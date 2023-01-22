import math
import numpy as np
import scipy.integrate
from scipy.interpolate import CubicSpline

PEN_UP = 0
PEN_DOWN = 1

class VeloProfile:
    def __init__(self, init_v: float, v_max: float, final_v: float, accel: float, total_dist: float):
        ascent_dt = (v_max - init_v) / accel
        descent_dt = (v_max - final_v) / accel

        ascent_dt = max(0.0, ascent_dt)
        descent_dt = max(0.0, descent_dt)

        ascent_d = 0.5 * (init_v + v_max) * ascent_dt
        descent_d = 0.5 * (v_max + final_v) * descent_dt

        const_d = total_dist - ascent_d - descent_d
        const_dt = const_d / v_max

        if const_dt <= 0:
            const_dt = 0
            const_d = 0
            v_max = math.sqrt(total_dist * accel + 0.5 * (init_v * init_v + final_v * final_v))
            ascent_dt = (v_max - init_v) / accel
            descent_dt = (v_max - final_v) / accel
            ascent_d = 0.5 * (init_v + v_max) * ascent_dt
            descent_d = 0.5 * (v_max + final_v) * descent_dt

        self.duration = ascent_dt + const_dt + descent_dt
        self.dist = ascent_d + const_d + descent_d
        self.v_max = v_max

        def ascent(t): return init_v + accel * t

        def const(_): return v_max

        def descent(t): return v_max - accel * t

        self.profile = lambda t: (
            0 if (t < 0) else (
                ascent(t) if (t <= ascent_dt) else (
                    const(t - ascent_dt) if (ascent_dt < t <= ascent_dt + const_dt) else (
                        descent(t - ascent_dt - const_dt) if (t <= ascent_dt + const_dt + descent_dt) else (
                            final_v
                        )
                    )
                )
            )
        )


class Path:
    def __init__(self, xs, ys, pen_states, max_v, accel):
        xs_len = len(xs)
        ys_len = len(ys)
        if xs_len != ys_len:
            raise Exception("lengths of x and y list do not match.")
        if xs_len < 3:
            raise Exception("Must have at least 3 points to form a path.")
        for state in pen_states:
            if state != PEN_UP and state != PEN_DOWN:
                raise Exception("Invalid Pen State Detected")

        ts = np.linspace(0, 1, num=xs_len)
        points = [(xs[i], ys[i]) for i in range(xs_len)]

        self.time_spline = CubicSpline(ts, points, bc_type='natural')

        def arc(t):
            dx, dy = self.time_spline(t, nu=1)
            return math.hypot(dx, dy)

        # This is an awful way to re-parameterize the curve, but it works
        arc_pieces = [arc(t) for t in ts]

        s = [scipy.integrate.trapezoid(arc_pieces[:i], ts[:i]) for i in range(1, xs_len)]
        print(s[207:])
        for i in range(len(s) - 1):
            diff = s[i+1] - s[i]
            if diff < 0:
                z=1
                #print(i)
                #print(str((s[i], s[i+1])))

        self.dist = scipy.integrate.simpson(arc_pieces, ts)
        s.append(self.dist)

        self.arc_time_spline = CubicSpline(s, ts, bc_type='natural')
        self.spline = CubicSpline(s, points, bc_type='natural')
        self.derivative = self.spline.derivative()

        self.pen_states = CubicSpline(s, pen_states, bc_type='natural')

        self.velo_profile = VeloProfile(0, max_v, 0, accel, self.dist)

    def get_motion_data(self, s: float, t: float):

        if t > self.velo_profile.duration:
            return None, None, None, None, None

        velocity = self.velo_profile.profile(t)

        x, y = self.spline(s)
        dx, dy = self.derivative(s)
        theta = math.atan2(dy, dx)

        return x, y, theta, velocity, round(self.pen_states(s).item())
    

def to_line_lens(x: float, y: float, spool_dist: float):
    return math.hypot(x, y), math.hypot(spool_dist - x, y)


def point_vel_to_spool_vel(x: float, y: float, x_vel: float, y_vel: float, spool_radius: float, spool_dist: float):
    l1, l2 = to_line_lens(x, y, spool_dist)
    l1_vel, l2_vel = (x * x_vel + y * y_vel) / l1, (-x * x_vel + y * y_vel) / l2
    return l1_vel / spool_radius, l2_vel / spool_radius

