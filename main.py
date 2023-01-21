import math
import board_bot_motion_lib as motion
import pygame
import numpy as np
from matplotlib import pyplot as plt


def main():
    # Note to Self: each spool is 15.84 mm in diameter
    spool_radius = 10

    # Circle Path Variables
    circle_radius = 0.1
    circle_x = 0.5
    circle_y = 0.5
    max_vel = 1
    accel = 2

    # Starting pointer position. x and y go from 0 to 1
    x = 0.4
    y = 0.5

    # Pygame Display Constants
    background_color = (255, 255, 255)
    screen_size = [500, 500]
    pointer_icon_radius = 5
    path_width = 3
    cable_width = 1
    quit_button = pygame.K_q

    left_spool_center = (spool_radius, spool_radius)
    right_spool_center = (screen_size[0] - spool_radius, spool_radius)

    # Generate path x and y coordinates
    ts = np.linspace(0, 1, num=100)
    xs = [circle_x - circle_radius * math.cos(2 * math.pi * t) for t in ts]
    ys = [circle_y - circle_radius * math.sin(2 * math.pi * t) for t in ts]

    # Generate the path states (the pen should be down half the time)
    pen_states = [motion.PEN_DOWN if t <= 0.5 else motion.PEN_UP for t in ts]

    # Generate the path
    path = motion.Path(xs, ys, pen_states, max_vel, accel)

    # Plot the path using matplotlib
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.set_aspect('equal', adjustable='box')
    s = [t * 2 * math.pi * circle_radius for t in ts]
    plt.plot(path.spline(s)[:, 0], path.spline(s)[:, 1], label='spline')
    plt.show()

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

        # Fill the background with white
        # screen.fill(background_color)

        # Clear the marker
        pygame.draw.circle(screen, (255, 255, 255), pointer_center, pointer_icon_radius)

        # Clear the pulley strings
        pygame.draw.line(screen, (255, 255, 255), left_spool_center, pointer_center, cable_width)
        pygame.draw.line(screen, (255, 255, 255), right_spool_center, pointer_center, cable_width)

        # Draw the marker
        pointer_center = (x * screen_size[0], y * screen_size[1])
        pygame.draw.circle(screen, (0, 255, 0), pointer_center, pointer_icon_radius)

        # Draw the two pulleys
        pygame.draw.circle(screen, (0, 0, 0), left_spool_center, spool_radius)
        pygame.draw.circle(screen, (0, 0, 0), right_spool_center, spool_radius)

        # Draw the circular path
        pygame.draw.circle(screen, (255, 0, 0),
                           (0.5*screen_size[0], 0.5*screen_size[1]), 0.1*screen_size[0], width=1)

        # Draw the pulley strings
        pygame.draw.line(screen, (0, 0, 0), left_spool_center, pointer_center, cable_width)
        pygame.draw.line(screen, (0, 0, 0), right_spool_center, pointer_center, cable_width)

        # Get the velocity and angle based on the current time since the path start
        # and the currently travelled arc length
        new_x, new_y, theta, v, pen = path.get_motion_data(s, t)

        # Theta != None iff we haven't finished the path
        if theta is not None:
            x += v*math.cos(theta)*dt
            y += v*math.sin(theta)*dt
            s += v*dt

        t += dt

        # Draw the current location on the screen overlay (if pen is down)
        if pen == motion.PEN_DOWN:
            pygame.draw.circle(path_overlay, (0, 0, 0), pointer_center, path_width/2.0)

        screen.blit(path_overlay, (0, 0))
        pygame.display.update()
    pygame.quit()


if __name__ == "__main__":
    main()
