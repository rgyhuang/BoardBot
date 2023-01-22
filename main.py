import math
import board_bot_motion_lib as motion
import pygame
import numpy as np
from matplotlib import pyplot as plt
import vision


def main():
    # Note to Self: each spool is 15.84 mm in diameter
    # This is the equivalent in the simulator coordinate system
    spool_actual_radius = 0.04525714285714285714285714285714
    spool_draw_radius = 10

    # Path Variables
    max_vel = 1
    accel = 2

    # Starting pointer position. x and y go from 0 to 1
    x = 0.5
    y = 0.5

    # Pygame Display Constants
    background_color = (255, 255, 255)
    screen_size = [500, 500]
    pointer_icon_radius = 5
    path_width = 3
    cable_width = 1
    quit_button = pygame.K_q
    mark_dist = spool_draw_radius / 2.0
    mark_radius = 3

    left_spool_center = (spool_draw_radius, spool_draw_radius)
    right_spool_center = (screen_size[0] - spool_draw_radius, spool_draw_radius)

    # Generate path x and y coordinates
    xs, ys = vision.scan_image("images/heart.png")

    # Plot the desired path
    plt.plot(xs, 1.0 - ys)
    plt.show()

    # Add the current pointer center to the start of the path
    xs = np.insert(xs, 0, x)
    ys = np.insert(ys, 0, y)

    # Generate the path states (the pen should be down half the time)
    pen_states = [motion.PEN_DOWN for _ in xs]
    # This state does not get used. We set it for illustrative purposes.
    pen_states[0] = motion.PEN_DOWN
    # We want the pen to be up on the way to the path.
    pen_states[1] = motion.PEN_UP

    # Generate the path
    path = motion.Path(xs, ys, pen_states, max_vel, accel)

    # Plot the velocity profile
    ts = np.linspace(0, path.velo_profile.duration, num=100)
    vs = [path.velo_profile.profile(t) for t in ts]
    plt.plot(ts, vs)
    plt.show()

    pygame.init()
    clock = pygame.time.Clock()

    # Set up the drawing window
    screen = pygame.display.set_mode(screen_size)
    path_overlay = pygame.Surface(screen_size)
    screen.fill(background_color)
    path_overlay.fill(background_color)
    path_overlay.set_colorkey(background_color)

    # Initialize simulation variables
    t = 0
    dt = 0.001
    s = 0
    left_mark_theta = 0
    right_mark_theta = math.pi

    pointer_center = (x * screen_size[0], y * screen_size[1])

    # Run until the user asks to quit
    running = True
    while running:
        clock.tick(200)

        # Check for quit events (window close or Q keypress)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == quit_button:
                    running = False
            elif event.type == pygame.QUIT:
                running = False

        # Clear the marker
        pygame.draw.circle(screen, (255, 255, 255), pointer_center, pointer_icon_radius)

        # Clear the pulley strings
        pygame.draw.line(screen, (255, 255, 255), left_spool_center, pointer_center, cable_width)
        pygame.draw.line(screen, (255, 255, 255), right_spool_center, pointer_center, cable_width)

        # Draw the marker
        pointer_center = (x * screen_size[0], y * screen_size[1])
        pygame.draw.circle(screen, (0, 255, 0), pointer_center, pointer_icon_radius)

        # Draw the two pulleys
        pygame.draw.circle(screen, (0, 0, 0), left_spool_center, spool_draw_radius)
        pygame.draw.circle(screen, (0, 0, 0), right_spool_center, spool_draw_radius)

        # Draw the pulley marks
        pygame.draw.circle(screen, (255, 0, 0), (left_spool_center[0] + mark_dist * math.cos(left_mark_theta),
                                                 left_spool_center[1] + mark_dist * math.sin(left_mark_theta)),
                           mark_radius)
        pygame.draw.circle(screen, (255, 0, 0), (right_spool_center[0] + mark_dist * math.cos(right_mark_theta),
                                                 right_spool_center[1] + mark_dist * math.sin(right_mark_theta)),
                           mark_radius)

        # Draw the pulley strings
        pygame.draw.line(screen, (0, 0, 0), left_spool_center, pointer_center, cable_width)
        pygame.draw.line(screen, (0, 0, 0), right_spool_center, pointer_center, cable_width)

        # Get the velocity and angle based on the current time since the path start
        # and the currently travelled arc length
        new_x, new_y, theta, v, pen = path.get_motion_data(s, t)

        # Theta != None iff we haven't finished the path
        if theta is not None:
            x += v * math.cos(theta) * dt
            y += v * math.sin(theta) * dt
            s += v * dt

            left_ang, right_ang = motion.point_vel_to_spool_vel(x, y, v*math.cos(theta), v*math.cos(theta),
                                                                spool_actual_radius, 1)
            left_mark_theta += left_ang*dt
            right_mark_theta += right_ang*dt

        t += dt

        # Draw the current location on the screen overlay (if pen is down)
        if pen == motion.PEN_DOWN:
            pygame.draw.circle(path_overlay, (0, 0, 0), pointer_center, path_width / 2.0)

        screen.blit(path_overlay, (0, 0))
        pygame.display.update()
    pygame.quit()


if __name__ == "__main__":
    main()
