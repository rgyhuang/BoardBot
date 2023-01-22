import math
import board_bot_motion_lib as motion
import time
import numpy as np
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


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

    # Generate path x and y coordinates
    ts = np.linspace(0, 1, num=100)
    s = [t * 2 * math.pi * circle_radius for t in ts]
    xs = [circle_x - circle_radius * math.cos(2 * math.pi * t) for t in ts]
    ys = [circle_y - circle_radius * math.sin(2 * math.pi * t) for t in ts]

    # Generate the path
    path = motion.Path(xs, ys, max_vel, accel)

    # Initialize simulation variables
    t = 0
    dt = 0.001
    s = 0

    # Run until the user asks to quit
    running = True
    while running:
        new_x, new_y, theta, v = path.get_motion_data(s, t)

        # Theta != None iff we haven't finished the path
        if theta is not None:
            x += v*math.cos(theta)*dt
            y += v*math.sin(theta)*dt
            s += v*dt
        
        # get the radians/sec 
        l1_vel, l2_vel = motion.point_vel_to_spool_vel(new_x, new_y, x, y, spool_radius)

        # radians/sec to rotations/min
        # = 2pi/60 = pi/30
        # I don't think there is a setspeed function in raspberry pi??

        # Need radians / degree2rad(1.8) steps == cannot change the waiting time
        # Total time is 0.1 seconds, calculate how many steps required
        # total radians required move in 0.1 sec

        l1_rad = l1_vel/10
        l2_rad = l2_vel/10
        steps_req_l1, steps_req_l2 = abs(l1_rad/math.radians(1.8)), abs(l2_rad/math.radians(1.8))
        
        count_l1 = 0
        count_l2 = 0
        # this is such a stupid method of changing the speeds
 
        for _ in range(10):
            if (steps_req_l1 < count_l1):
                if (steps_req_l1 <= 10): steps_l1 = stepper.SINGLE
                else: steps_l1 = stepper.DOUBLE

                if (l1_rad >= 0): dir_l1 = stepper.FORWARD
                else: dir_l1 = stepper.BACKWARD

                kit.stepper1.onestep(direction=dir_l1, style=steps_l1)

                if (steps_l1 == stepper.SINGLE): count_l1 += 1
                else: count_l1 += 2

            if (steps_req_l2 < count_l2):
                if (steps_req_l2 <= 10): steps_l2 = stepper.SINGLE
                else: steps_l2 = stepper.DOUBLE

                if (l2_rad >= 0): dir_l2 = stepper.FORWARD
                else: dir_l2 = stepper.BACKWARD

                kit.stepper2.onestep(direction=dir_l2, style=steps_l2)

                if (steps_l2 == stepper.SINGLE): count_l2 += 1
                else: count_l2 += 2

            time.sleep(0.01)

        t += dt


if __name__ == "__main__":
    main()
