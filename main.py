import math

import matplotlib

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
    max_vel = 2
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
    xs, ys = vision.scan_image("images/circle.jpg")

    # Plot the desired path
    plt.axes().set_aspect('equal')
    plt.xlim(left=0.0, right=1.0)
    plt.ylim(bottom=0.0, top=1.0)
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
            print(str((t, path.velo_profile.duration)))
            k1x = v * math.cos(theta)
            k1y = v * math.sin(theta)

            dt1 = dt/2.0

            _, _, theta2, v2, _ = path.get_motion_data(s + math.hypot(k1x * dt1, k1y * dt1), t + dt1)

            if theta2 is None:
                x += k1x * dt
                y += k1y * dt
                s += v * dt
            else:
                k2x = v2 * math.cos(theta2)
                k2y = v2 * math.sin(theta2)

                _, _, theta3, v3, _ = path.get_motion_data(s + math.hypot(k2x * dt1, k2y * dt1), t + dt1)

                if theta3 is None:
                    x += k1x * dt
                    y += k1y * dt
                    s += v * dt
                else:
                    k3x = v3 * math.cos(theta3)
                    k3y = v3 * math.sin(theta3)

                    _, _, theta4, v4, _ = path.get_motion_data(s + math.hypot(k3x * dt, k2y * dt), t + dt)

                    if theta4 is None:
                        x += k1x * dt
                        y += k1y * dt
                        s += v * dt
                    else:
                        k4x = v4 * math.cos(theta4)
                        k4y = v4 * math.sin(theta4)

                        kx = (1.0 / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
                        ky = (1.0 / 6.0) * (k1y + 2 * k2y + 2 * k3y + k4y)
                        ks = (1.0 / 6.0) * (v + 2 * v2 + 2 * v3 + v4)

                        x += kx * dt
                        y += ky * dt
                        s += ks * dt

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
