"""Generate the diagrams for docs/05_programming-techniques/07_control-and-motion/.

This covers 01_overview, 02_pid-control, 03_trajectory-generation and
04_impedance-and-force-control. Each document's pictures go to a folder named
after it, under docs/images/control-and-motion/.

Run with:  pixi run python ../docs/diagrams/control_and_motion.py
Add --png <dir> to also write PNG copies for checking.
Add --numbers to print the numbers the documents quote, without drawing.

Every curve here is simulated, not drawn by hand. The models are small on
purpose, so that a reader can check them:

- one joint: inertia J, viscous friction B and a constant gravity load, driven
  by a torque from a controller that runs at 1 kHz
- trajectories: trapezoidal and S-curve profiles built from piecewise-constant
  acceleration or jerk, and a clamped cubic spline solved with NumPy
- contact: a tool of mass M against a wall that pushes back like a stiff spring,
  under a position controller, an impedance controller, a guarded move or an
  admittance controller with a delay in its loop

Only NumPy and Matplotlib are needed.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'control-and-motion'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'

WALL: str = '#f3f3f3'
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _plot_axes(ax: Axes, xlabel: str, ylabel: str) -> None:
    """A plain chart: no top or right border, light grid, muted labels."""
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, color=INK, fontsize=10)
    ax.set_ylabel(ylabel, color=INK, fontsize=10)


def _label(ax: Axes, x: float, y: float, text: str, size: float = 9.5, color: str = INK,
           ha: str = 'center', va: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight, zorder=9,
            bbox={'boxstyle': 'square,pad=0.15', 'facecolor': 'white', 'edgecolor': 'none',
                  'alpha': 0.85})


def _panel_title(ax: Axes, text: str) -> None:
    ax.set_title(text, fontsize=11, color=INK, weight='bold', loc='left', pad=10)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.3) -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': '-|>', 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0},
                zorder=8)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# model 1: one joint under a controller
# --------------------------------------------------------------------------

J_INERTIA: float = 0.05     # kg m^2, the link and motor as the joint sees them
B_FRICTION: float = 0.5     # N m s / rad, viscous friction in the joint
LOAD: float = 1.0           # N m, gravity on the link, taken as constant for a small move
DT: float = 0.001           # s, the controller runs 1000 times a second
SUB: int = 10               # physics steps per controller step

KP: float = 20.0            # N m / rad
KI: float = 30.0            # N m / (rad s)
KD: float = 1.0             # N m s / rad

ENCODER_STEP: float = 2 * np.pi / 4096    # rad, one count of a 4096-count encoder


def joint_run(kp: float, ki: float, kd: float, target, seconds: float = 3.0,
              torque_limit: float | None = None, anti_windup: bool = False,
              encoder_step: float | None = None, d_filter_hz: float | None = None
              ) -> dict[str, np.ndarray]:
    """Simulate one joint under a PID controller.

    target is either a number (a step) or a function of time. The derivative
    acts on the measured angle, not on the error, so a step in the target does
    not produce a spike. Returns time, angle, target and the P, I, D and total
    torques, one row per controller tick.
    """
    tgt = target if callable(target) else (lambda _t, v=float(target): v)
    angle = 0.0
    speed = 0.0
    integral = 0.0
    previous: float | None = None
    d_state = 0.0
    rows: list[tuple[float, ...]] = []
    for k in range(int(round(seconds / DT))):
        t = k * DT
        measured = angle if encoder_step is None else np.round(angle / encoder_step) * encoder_step
        goal = tgt(t)
        error = goal - measured
        if previous is None:
            previous = measured
        rate = (measured - previous) / DT
        previous = measured
        if d_filter_hz is not None:
            alpha = DT / (DT + 1.0 / (2 * np.pi * d_filter_hz))
            d_state += alpha * (rate - d_state)
            rate = d_state
        p_term = kp * error
        d_term = -kd * rate
        new_integral = integral + error * DT
        torque = p_term + ki * new_integral + d_term
        if torque_limit is not None and abs(torque) > torque_limit:
            if not anti_windup:
                integral = new_integral
            torque = float(np.clip(torque, -torque_limit, torque_limit))
        else:
            integral = new_integral
        rows.append((t, angle, goal, p_term, ki * integral, d_term, torque))
        h = DT / SUB
        for _ in range(SUB):
            accel = (torque - B_FRICTION * speed - LOAD) / J_INERTIA
            speed += accel * h
            angle += speed * h
    a = np.array(rows)
    return {'t': a[:, 0], 'angle': a[:, 1], 'target': a[:, 2], 'P': a[:, 3], 'I': a[:, 4],
            'D': a[:, 5], 'torque': a[:, 6]}


def step_stats(run: dict[str, np.ndarray], goal: float) -> dict[str, float]:
    """Overshoot in per cent, 2 per cent settling time, and the error at the end."""
    angle = run['angle']
    over = max(0.0, (angle.max() - goal) / goal * 100)
    outside = np.where(np.abs(angle - goal) > 0.02 * goal)[0]
    if len(outside) == 0:
        settle = 0.0
    elif outside[-1] == len(angle) - 1:
        settle = float('nan')     # never settles inside the band
    else:
        settle = float(run['t'][outside[-1] + 1])
    return {'overshoot': over, 'settle': settle, 'end_error': goal - float(angle[-1])}


STEP: float = 0.5   # rad, the step every PID picture uses (about 29 degrees)


# --------------------------------------------------------------------------
# model 2: trajectories
# --------------------------------------------------------------------------

TR_DT: float = 1e-4


def _integrate(segments: list[tuple[float, float]], kind: str) -> dict[str, np.ndarray]:
    """Integrate piecewise-constant jerk (kind 'jerk') or acceleration (kind 'acc')."""
    t, p, v, a, j = [0.0], [0.0], [0.0], [0.0], [0.0]
    pos = vel = acc = time = 0.0
    for duration, value in segments:
        for _ in range(int(round(duration / TR_DT))):
            if kind == 'jerk':
                jerk = value
                pos += vel * TR_DT + acc * TR_DT ** 2 / 2 + jerk * TR_DT ** 3 / 6
                vel += acc * TR_DT + jerk * TR_DT ** 2 / 2
                acc += jerk * TR_DT
            else:
                acc, jerk = value, 0.0
                pos += vel * TR_DT + acc * TR_DT ** 2 / 2
                vel += acc * TR_DT
            time += TR_DT
            t.append(time)
            p.append(pos)
            v.append(vel)
            a.append(acc)
            j.append(jerk)
    return {'t': np.array(t), 'p': np.array(p), 'v': np.array(v), 'a': np.array(a),
            'j': np.array(j)}


def trapezoid(distance: float, v_max: float, a_max: float) -> dict[str, np.ndarray]:
    """Rest to rest with a speed and an acceleration limit. Falls back to a triangle."""
    t_acc = v_max / a_max
    if a_max * t_acc ** 2 >= distance:          # never reaches full speed
        t_acc = np.sqrt(distance / a_max)
        return _integrate([(t_acc, a_max), (t_acc, -a_max)], 'acc')
    t_cruise = (distance - a_max * t_acc ** 2) / v_max
    return _integrate([(t_acc, a_max), (t_cruise, 0.0), (t_acc, -a_max)], 'acc')


def s_curve(distance: float, v_max: float, a_max: float, j_max: float) -> dict[str, np.ndarray]:
    """Rest to rest with speed, acceleration and jerk limits (all three reached)."""
    t_j = a_max / j_max
    t_a = v_max / a_max - t_j
    t_ramp = 2 * t_j + t_a
    t_cruise = (distance - v_max * t_ramp) / v_max
    return _integrate([(t_j, j_max), (t_a, 0.0), (t_j, -j_max), (t_cruise, 0.0),
                       (t_j, -j_max), (t_a, 0.0), (t_j, j_max)], 'jerk')


MOVE: float = 1.2      # rad
V_MAX: float = 1.0     # rad/s
A_MAX: float = 2.0     # rad/s^2
J_MAX: float = 10.0    # rad/s^3


def residual_vibration(profile: dict[str, np.ndarray], freq: float, damping: float = 0.02,
                       reach: float = 0.5, tail: float = 1.0) -> tuple[np.ndarray, np.ndarray, float]:
    """The tool on a flexible link: a lightly damped spring between joint and tool.

    Returns time, the tool's deflection in millimetres at the given reach, and the
    largest deflection after the joint has stopped.
    """
    wn = 2 * np.pi * freq
    acc = np.concatenate([profile['a'], np.zeros(int(round(tail / TR_DT)))])
    x = 0.0
    xd = 0.0
    out = np.empty(len(acc))
    for i, a in enumerate(acc):
        xdd = -a - 2 * damping * wn * xd - wn ** 2 * x
        xd += xdd * TR_DT
        x += xd * TR_DT
        out[i] = x
    t = np.arange(len(acc)) * TR_DT
    mm = out * reach * 1000
    after = float(np.abs(mm[len(profile['a']):]).max())
    return t, mm, after


def clamped_spline(times: np.ndarray, values: np.ndarray, samples: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A cubic spline through the points, starting and ending at zero speed.

    Solves for the speed at each knot so that acceleration is continuous, then
    evaluates position, speed and acceleration at the sample times.
    """
    n = len(times)
    h = np.diff(times)
    A = np.zeros((n, n))
    rhs = np.zeros(n)
    A[0, 0] = 1.0
    A[-1, -1] = 1.0
    for i in range(1, n - 1):
        A[i, i - 1] = 1 / h[i - 1]
        A[i, i] = 2 / h[i - 1] + 2 / h[i]
        A[i, i + 1] = 1 / h[i]
        rhs[i] = 3 * ((values[i] - values[i - 1]) / h[i - 1] ** 2
                      + (values[i + 1] - values[i]) / h[i] ** 2)
    speeds = np.linalg.solve(A, rhs)
    pos = np.empty_like(samples)
    vel = np.empty_like(samples)
    acc = np.empty_like(samples)
    for k, s in enumerate(samples):
        i = min(max(np.searchsorted(times, s) - 1, 0), n - 2)
        dt = h[i]
        u = (s - times[i]) / dt
        p0, p1, m0, m1 = values[i], values[i + 1], speeds[i] * dt, speeds[i + 1] * dt
        h00, h10, h01, h11 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2, u**3 - u**2
        d00, d10, d01, d11 = 6*u**2 - 6*u, 3*u**2 - 4*u + 1, -6*u**2 + 6*u, 3*u**2 - 2*u
        e00, e10, e01, e11 = 12*u - 6, 6*u - 4, -12*u + 6, 6*u - 2
        pos[k] = h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1
        vel[k] = (d00 * p0 + d10 * m0 + d01 * p1 + d11 * m1) / dt
        acc[k] = (e00 * p0 + e10 * m0 + e01 * p1 + e11 * m1) / dt ** 2
    return pos, vel, acc


WAY_T: np.ndarray = np.array([0.0, 1.0, 2.0, 3.0])
WAY_Q: np.ndarray = np.array([0.0, 0.8, 0.5, 1.0])


# --------------------------------------------------------------------------
# model 3: a tool touching a wall
# --------------------------------------------------------------------------

TOOL_MASS: float = 2.0       # kg, the arm's apparent mass along the push
WALL_K: float = 50000.0      # N/m, a stiff surface: 50 N per millimetre
C_DT: float = 1e-5           # s, physics step for contact


def _wall_force(x: float, wall: float, k: float) -> float:
    return k * (x - wall) if x > wall else 0.0


def ramp_target(start: float, speed: float, stop: float):
    return lambda t: min(start + speed * t, stop)


def impedance_run(stiffness: float, damping: float, target, seconds: float = 2.0,
                  wall_k: float = WALL_K) -> dict[str, np.ndarray]:
    """Impedance control: force = K (target - x) - D v, sent straight to the tool."""
    x, v = -0.010, 0.0
    rows = []
    for k in range(int(round(seconds / C_DT))):
        t = k * C_DT
        push = stiffness * (target(t) - x) - damping * v
        wall = _wall_force(x, 0.0, wall_k)
        v += (push - wall) / TOOL_MASS * C_DT
        x += v * C_DT
        if k % 100 == 0:
            rows.append((t, x, wall, target(t)))
    a = np.array(rows)
    return {'t': a[:, 0], 'x': a[:, 1], 'F': a[:, 2], 'target': a[:, 3]}


def position_run(target, seconds: float = 2.0, force_limit: float = 150.0
                 ) -> dict[str, np.ndarray]:
    """A stiff PID position loop at 1 kHz, with the motor's force limit."""
    kp, ki, kd = 2.0e5, 2.0e6, 1000.0
    x, v, integral, push = -0.010, 0.0, 0.0, 0.0
    every = int(round(DT / C_DT))
    rows = []
    for k in range(int(round(seconds / C_DT))):
        t = k * C_DT
        if k % every == 0:
            e = target(t) - x
            integral += e * DT
            push = float(np.clip(kp * e + ki * integral - kd * v, -force_limit, force_limit))
        wall = _wall_force(x, 0.0, WALL_K)
        v += (push - wall) / TOOL_MASS * C_DT
        x += v * C_DT
        if k % 100 == 0:
            rows.append((t, x, wall, target(t)))
    a = np.array(rows)
    return {'t': a[:, 0], 'x': a[:, 1], 'F': a[:, 2], 'target': a[:, 3]}


def guarded_run(speed: float, surface: float = 0.020, surface_k: float = 5000.0,
                threshold: float = 1.0, rate: float = 500.0, average: int = 5,
                noise: float = 0.1, latency_ticks: int = 1, stop_accel: float = 0.5,
                travel_limit: float = 0.050, seed: int = 1) -> dict:
    """A guarded move: creep at a steady speed until the filtered force passes a threshold.

    The arm follows its commanded position exactly. The force sensor is read at
    `rate`, with Gaussian noise, and averaged over the last `average` readings.
    After the trigger the arm waits `latency_ticks` and then brakes at `stop_accel`.
    It also stops at `travel_limit` if nothing fires.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / rate
    x, v = 0.0, speed
    readings: list[float] = []
    fired: dict | None = None
    brake_from: int | None = None
    rows = []
    k = 0
    while k < 100000:
        t = k * dt
        force = surface_k * max(0.0, x - surface)
        readings.append(force + rng.normal(0.0, noise))
        filtered = float(np.mean(readings[-average:]))
        rows.append((t, x, force, readings[-1], filtered))
        if fired is None and filtered > threshold:
            fired = {'why': 'force', 't': t, 'x': x}
            brake_from = k + latency_ticks
        if fired is None and x >= travel_limit:
            fired = {'why': 'travel limit', 't': t, 'x': x}
            brake_from = k
        if brake_from is not None and k >= brake_from:
            v = max(0.0, v - stop_accel * dt)
        x += v * dt
        k += 1
        if brake_from is not None and v == 0.0:
            rows.append((k * dt, x, surface_k * max(0.0, x - surface), np.nan, np.nan))
            break
    a = np.array(rows)
    return {'t': a[:, 0], 'x': a[:, 1], 'F': a[:, 2], 'raw': a[:, 3], 'filtered': a[:, 4],
            'fired': fired, 'surface': surface}


def admittance_run(surface_k: float, damping: float, virtual_mass: float = 10.0,
                   push: float = 10.0, inner_hz: float = 15.0, inner_zeta: float = 0.7,
                   delay_ticks: int = 4, rate: float = 500.0, seconds: float = 1.5,
                   surface: float = 0.001) -> dict[str, np.ndarray]:
    """Admittance control of a position-controlled arm pressing with a set force.

    The controller reads the wrist force (with a delay of delay_ticks), moves a
    virtual mass-damper under (push - measured force), and sends that position
    to the arm. The arm's own position loop follows it as a second-order lag.
    """
    wn = 2 * np.pi * inner_hz
    every = int(round(1.0 / rate / C_DT))
    x = v = xc = vc = 0.0
    queue = [0.0] * (delay_ticks + 1)
    rows = []
    for k in range(int(round(seconds / C_DT))):
        t = k * C_DT
        wall = _wall_force(x, surface, surface_k)
        if k % every == 0:
            queue.append(wall)
            measured = queue.pop(0)
            vc = (vc + (push - measured) / virtual_mass / rate) / (1 + damping / virtual_mass / rate)
            xc += vc / rate
        a = wn ** 2 * (xc - x) - 2 * inner_zeta * wn * v
        v += a * C_DT
        x += v * C_DT
        if k % 50 == 0:
            rows.append((t, x, wall))
    arr = np.array(rows)
    return {'t': arr[:, 0], 'x': arr[:, 1], 'F': arr[:, 2]}


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OV_WAYPOINTS: np.ndarray = np.array([[0.0, 0.0], [0.35, 0.55], [0.9, 0.7], [1.2, 0.3]])


def overview_move() -> dict:
    """One two-joint move through the three layers: path, timing, control."""
    seg = np.linalg.norm(np.diff(OV_WAYPOINTS, axis=0), axis=1)
    times = np.concatenate([[0.0], np.cumsum(seg / seg.sum() * 2.4)])
    samples = np.arange(0.0, 4.0 - DT / 2, DT)
    joints = []
    for j in range(2):
        pos, vel, _ = clamped_spline(times, OV_WAYPOINTS[:, j], np.minimum(samples, times[-1]))
        vel = np.where(samples > times[-1], 0.0, vel)

        def target(t: float, pos=pos) -> float:
            return float(pos[min(int(round(t / DT)), len(pos) - 1)])
        run = joint_run(KP, KI, KD, target, seconds=4.0)
        joints.append({'pos': pos, 'vel': vel, 'run': run})
    return {'times': times, 'samples': samples, 'joints': joints}


def one_move_three_layers() -> None:
    mv = overview_move()
    colours = (LINK, WRIST)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), facecolor='white')

    ax = axes[0]
    _plot_axes(ax, 'joint 1 angle (rad)', 'joint 2 angle (rad)')
    ax.plot(OV_WAYPOINTS[:, 0], OV_WAYPOINTS[:, 1], '--', color=MUTED, lw=1.2)
    ax.plot(mv['joints'][0]['pos'], mv['joints'][1]['pos'], color=PURPLE, lw=2.2)
    ax.plot(OV_WAYPOINTS[:, 0], OV_WAYPOINTS[:, 1], 'o', color=INK, ms=6, zorder=5)
    _label(ax, 0.0, -0.07, 'start', ha='left', color=MUTED)
    _label(ax, 1.2, 0.23, 'goal', ha='right', color=MUTED)
    _label(ax, 0.62, 0.22, 'planner: waypoints\n(no times yet)', color=MUTED)
    _label(ax, 0.72, 0.84, 'smooth curve through them', color=PURPLE)
    ax.set_xlim(-0.1, 1.35)
    ax.set_ylim(-0.15, 0.95)
    _panel_title(ax, '1. Planning: where to pass')

    ax = axes[1]
    _plot_axes(ax, 'time (s)', 'joint speed (rad/s)')
    for j, c in enumerate(colours):
        ax.plot(mv['samples'], mv['joints'][j]['vel'], color=c, lw=2)
    for tk in mv['times']:
        ax.axvline(tk, color=GRID, lw=1.0, ls=':')
    _label(ax, 1.45, 0.79, 'joint 1', color=LINK)
    _label(ax, 1.3, -0.6, 'joint 2', color=WRIST)
    _label(ax, 3.2, 0.35, 'both reach\nzero speed', color=MUTED)
    ax.set_xlim(0, 4.0)
    _panel_title(ax, '2. Trajectory: when to be there')

    ax = axes[2]
    _plot_axes(ax, 'time (s)', 'following error (degrees)')
    for j, c in enumerate(colours):
        run = mv['joints'][j]['run']
        ax.plot(run['t'], np.degrees(run['target'] - run['angle']), color=c, lw=2)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axvline(mv['times'][-1], color=GRID, lw=1.0, ls=':')
    _label(ax, 0.75, -2.7, 'PID lags behind\nwhile moving', color=MUTED)
    _label(ax, 3.3, 2.3, 'shrinks slowly\nafter the end', color=MUTED)
    ax.set_xlim(0, 4.0)
    _panel_title(ax, '3. Control: make the motor follow')

    fig.subplots_adjust(wspace=0.32)
    _save(fig, 'overview', 'one-move-three-layers.svg')


def slow_commands() -> dict:
    """A 10 Hz stream of targets, fed straight to a 1 kHz PID or first interpolated."""
    def wanted(t: float) -> float:
        return 0.4 * np.sin(2 * np.pi * 0.5 * t)

    def held(t: float) -> float:              # sample and hold at 10 Hz
        return wanted(np.floor(t * 10 + 1e-9) / 10)

    def ramped(t: float) -> float:            # go from the previous sample to the newest one
        k = np.floor(t * 10 + 1e-9)
        a, b = wanted((k - 1) / 10) if k > 0 else 0.0, wanted(k / 10)
        return a + (b - a) * (t * 10 - k)
    return {'held': joint_run(KP, KI, KD, held, seconds=2.0),
            'ramped': joint_run(KP, KI, KD, ramped, seconds=2.0)}


def slow_commands_figure() -> None:
    runs = slow_commands()
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), facecolor='white', sharex=True)
    ax = axes[0]
    _plot_axes(ax, '', 'joint angle (rad)')
    ax.plot(runs['held']['t'], runs['held']['target'], color=MUTED, lw=1.2, drawstyle='steps-post')
    ax.plot(runs['held']['t'], runs['held']['angle'], color=GRIP, lw=2)
    ax.plot(runs['ramped']['t'], runs['ramped']['angle'], color=SLIDE, lw=2)
    _label(ax, 0.33, 0.43, '10 Hz targets (grey steps)', color=MUTED)
    _label(ax, 1.3, 0.36, 'red: fed straight in', color=GRIP, ha='left')
    _label(ax, 1.3, 0.24, 'green: ramped between targets at 1 kHz', color=SLIDE, ha='left')
    ax.set_ylim(-0.5, 0.55)
    _panel_title(ax, 'The same 10 targets a second, two ways')
    ax = axes[1]
    _plot_axes(ax, 'time (s)', 'motor torque (N m)')
    ax.plot(runs['held']['t'], runs['held']['torque'], color=GRIP, lw=1.3)
    ax.plot(runs['ramped']['t'], runs['ramped']['torque'], color=SLIDE, lw=2)
    _label(ax, 0.55, 3.2, 'a torque kick at every new target', color=GRIP, ha='left')
    _label(ax, 1.62, -0.9, 'smooth torque', color=SLIDE)
    ax.set_xlim(0, 2.0)
    fig.subplots_adjust(hspace=0.12)
    _save(fig, 'overview', 'slow-commands.svg')


# --------------------------------------------------------------------------
# 02_pid-control
# --------------------------------------------------------------------------

def pid_runs() -> dict[str, dict[str, np.ndarray]]:
    return {'P': joint_run(KP, 0.0, 0.0, STEP),
            'PI': joint_run(KP, KI, 0.0, STEP),
            'PID': joint_run(KP, KI, KD, STEP)}


def step_responses() -> None:
    runs = pid_runs()
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), facecolor='white', sharey=True)
    specs = [('P', GRIP, f'P only (Kp = {KP:g})'),
             ('PI', WRIST, f'PI (Kp = {KP:g}, Ki = {KI:g})'),
             ('PID', SLIDE, f'PID (Kp = {KP:g}, Ki = {KI:g}, Kd = {KD:g})')]
    for ax, (key, colour, title) in zip(axes, specs):
        _plot_axes(ax, 'time (s)', 'joint angle (rad)' if key == 'P' else '')
        run = runs[key]
        ax.axhline(STEP, color=MUTED, lw=1.2, ls='--')
        ax.plot(run['t'], run['angle'], color=colour, lw=2.2)
        s = step_stats(run, STEP)
        ax.set_xlim(0, 2.0)
        ax.set_ylim(0, 0.75)
        _panel_title(ax, title)
        _label(ax, 1.97, STEP + 0.03, 'target 0.5', color=MUTED, ha='right', va='bottom')
        lines = [f'overshoot {s["overshoot"]:.0f}%']
        if np.isnan(s['settle']):
            lines.append(f'stops {np.degrees(s["end_error"]):.1f}° short')
        else:
            lines.append(f'settled by {s["settle"]:.2f} s')
        _label(ax, 1.97, 0.12, '\n'.join(lines), color=colour, ha='right', size=10)
    fig.subplots_adjust(wspace=0.1)
    _save(fig, 'pid-control', 'step-responses.svg')


def three_terms() -> None:
    run = pid_runs()['PID']
    fig, ax = plt.subplots(figsize=(10, 4.6), facecolor='white')
    _plot_axes(ax, 'time (s)', 'torque (N m)')
    ax.plot(run['t'], run['P'], color=LINK, lw=2)
    ax.plot(run['t'], run['I'], color=WRIST, lw=2)
    ax.plot(run['t'], run['D'], color=PURPLE, lw=2)
    ax.plot(run['t'], run['torque'], color=INK, lw=1.2, ls='--')
    ax.axhline(LOAD, color=MUTED, lw=0.9, ls=':')
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-5, 10.5)
    _label(ax, 0.02, 10.0, 'P: pushes in proportion to the error', color=LINK, ha='left')
    _label(ax, 0.55, 1.6, 'I: grows until it holds the 1 N m of gravity', color=WRIST, ha='left')
    _label(ax, 0.17, -3.7, 'D: brakes while the joint is moving fast', color=PURPLE, ha='left')
    _label(ax, 0.3, 3.3, 'total torque (dashed)', color=INK, ha='left')
    i = int(round(0.07 / DT))
    _arrow(ax, (0.29, 3.2), (0.07, float(run['torque'][i])), color=INK, lw=1.0)
    _panel_title(ax, 'The three terms of the PID run, tick by tick')
    _save(fig, 'pid-control', 'three-terms.svg')


def windup_runs() -> dict[str, dict[str, np.ndarray]]:
    return {'plain': joint_run(KP, KI, KD, 1.5, seconds=4.0, torque_limit=3.0),
            'guarded': joint_run(KP, KI, KD, 1.5, seconds=4.0, torque_limit=3.0,
                                 anti_windup=True)}


def windup() -> None:
    runs = windup_runs()
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), facecolor='white', sharex=True)
    ax = axes[0]
    _plot_axes(ax, '', 'joint angle (rad)')
    ax.axhline(1.5, color=MUTED, lw=1.2, ls='--')
    ax.plot(runs['plain']['t'], runs['plain']['angle'], color=GRIP, lw=2)
    ax.plot(runs['guarded']['t'], runs['guarded']['angle'], color=SLIDE, lw=2)
    sp, sg = step_stats(runs['plain'], 1.5), step_stats(runs['guarded'], 1.5)
    _label(ax, 1.25, 2.12, f'integral keeps growing: {sp["overshoot"]:.0f}% overshoot', color=GRIP,
           ha='left')
    _label(ax, 1.6, 1.22, f'integral paused while saturated: settled by {sg["settle"]:.2f} s',
           color=SLIDE, ha='left')
    _label(ax, 3.95, 1.55, 'target 1.5 rad', color=MUTED, ha='right', va='bottom')
    ax.set_ylim(0, 2.3)
    _panel_title(ax, 'A big step with the motor limited to 3 N m')
    ax = axes[1]
    _plot_axes(ax, 'time (s)', 'integral term (N m)')
    ax.plot(runs['plain']['t'], runs['plain']['I'], color=GRIP, lw=2)
    ax.plot(runs['guarded']['t'], runs['guarded']['I'], color=SLIDE, lw=2)
    ax.axhline(LOAD, color=MUTED, lw=0.9, ls=':')
    _label(ax, 0.8, runs['plain']['I'].max() * 0.97, f'winds up to {runs["plain"]["I"].max():.0f} N m',
           color=GRIP, ha='left')
    _label(ax, 2.2, 3.0, 'stays near the 1 N m it needs', color=SLIDE, ha='left')
    ax.set_xlim(0, 4.0)
    fig.subplots_adjust(hspace=0.14)
    _save(fig, 'pid-control', 'integral-windup.svg')


def derivative_runs() -> dict[str, dict[str, np.ndarray]]:
    return {'raw': joint_run(KP, KI, KD, STEP, encoder_step=ENCODER_STEP),
            'filtered': joint_run(KP, KI, KD, STEP, encoder_step=ENCODER_STEP, d_filter_hz=30.0)}


def derivative_noise() -> None:
    runs = derivative_runs()
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.3), facecolor='white', sharey=True)
    for ax, key, colour, title in ((axes[0], 'raw', GRIP, 'D term from the raw encoder'),
                                   (axes[1], 'filtered', SLIDE, 'D term after a 30 Hz low-pass filter')):
        run = runs[key]
        _plot_axes(ax, 'time (s)', 'D torque (N m)' if key == 'raw' else '')
        ax.plot(run['t'], run['D'], color=colour, lw=0.9)
        jump = np.abs(np.diff(run['D'])).max()
        ax.set_xlim(0, 1.0)
        ax.set_ylim(-5, 3.6)
        _panel_title(ax, title)
        _label(ax, 0.98, 2.9, f'largest jump in one tick: {jump:.1f} N m', color=colour, ha='right')
    _label(axes[0], 0.5, -4.2, 'each spike is one encoder count (0.0015 rad) in 1 ms',
           color=MUTED)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'pid-control', 'derivative-noise.svg')


# --------------------------------------------------------------------------
# 03_trajectory-generation
# --------------------------------------------------------------------------

def profiles() -> None:
    tr = trapezoid(MOVE, V_MAX, A_MAX)
    sc = s_curve(MOVE, V_MAX, A_MAX, J_MAX)
    fig, axes = plt.subplots(4, 1, figsize=(10, 9.2), facecolor='white', sharex=True)
    rows = [('p', 'position (rad)'), ('v', 'speed (rad/s)'), ('a', 'acceleration\n(rad/s²)'),
            ('j', 'jerk (rad/s³)')]
    for ax, (key, name) in zip(axes, rows):
        _plot_axes(ax, 'time (s)' if key == 'j' else '', name)
        if key == 'j':
            # the trapezoid's jerk is infinite at each corner; mark where it happens
            for tc in (0.0, 0.5, 1.2, 1.7):
                ax.axvline(tc, color=GRIP, lw=2.2, alpha=0.8)
            ax.plot(sc['t'], sc['j'], color=LINK, lw=2)
            _label(ax, 0.26, 7.0, 'trapezoid: a jump at each red line', color=GRIP, ha='left')
            ax.set_ylim(-13, 13)
        else:
            ax.plot(tr['t'], tr[key], color=GRIP, lw=2)
            ax.plot(sc['t'], sc[key], color=LINK, lw=2)
    _label(axes[0], 0.05, 1.0, 'trapezoid, done at 1.7 s', color=GRIP, ha='left')
    _label(axes[0], 0.05, 0.75, 'S-curve, done at 1.9 s', color=LINK, ha='left')
    _label(axes[2], 0.52, 1.0, 'acceleration jumps', color=GRIP, ha='left')
    _label(axes[2], 1.3, 1.2, 'acceleration ramps', color=LINK, ha='left')
    axes[0].set_title(f'The same {MOVE} rad move: speed ≤ {V_MAX:g}, acceleration ≤ {A_MAX:g}, '
                      f'jerk ≤ {J_MAX:g} (S-curve)', fontsize=11, color=INK, weight='bold',
                      loc='left', pad=10)
    axes[-1].set_xlim(0, 2.0)
    fig.subplots_adjust(hspace=0.16)
    _save(fig, 'trajectory-generation', 'trapezoid-and-s-curve.svg')


VIB_HZ: float = 4.0


def vibration() -> None:
    tr = trapezoid(MOVE, V_MAX, A_MAX)
    sc = s_curve(MOVE, V_MAX, A_MAX, J_MAX)
    t1, m1, r1 = residual_vibration(tr, VIB_HZ)
    t2, m2, r2 = residual_vibration(sc, VIB_HZ)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.3), facecolor='white', sharey=True)
    for ax, t, mm, r, end, colour, title in (
            (axes[0], t1, m1, r1, tr['t'][-1], GRIP, 'Trapezoid'),
            (axes[1], t2, m2, r2, sc['t'][-1], LINK, 'S-curve')):
        _plot_axes(ax, 'time (s)', 'tool wobble at 0.5 m (mm)' if title == 'Trapezoid' else '')
        ax.axvspan(end, t[-1], color=WALL)
        ax.plot(t, mm, color=colour, lw=1.6)
        ax.axvline(end, color=MUTED, lw=1, ls='--')
        _label(ax, end + 0.05, 2.7, f'joint stopped\nwobble left: ±{r:.2f} mm', color=colour,
               ha='left')
        _panel_title(ax, title)
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-3.4, 3.4)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'trajectory-generation', 'residual-vibration.svg')


def spline_vs_linear() -> None:
    samples = np.linspace(0.0, 3.0, 3001)
    lin_p = np.interp(samples, WAY_T, WAY_Q)
    lin_v = np.gradient(lin_p, samples)
    sp_p, sp_v, _ = clamped_spline(WAY_T, WAY_Q, samples)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), facecolor='white', sharex=True)
    ax = axes[0]
    _plot_axes(ax, '', 'joint angle (rad)')
    ax.plot(samples, lin_p, color=GRIP, lw=2)
    ax.plot(samples, sp_p, color=LINK, lw=2)
    ax.plot(WAY_T, WAY_Q, 'o', color=INK, ms=7, zorder=5)
    _label(ax, 0.25, 0.75, 'cubic spline', color=LINK, ha='left')
    _label(ax, 2.2, 0.33, 'straight lines', color=GRIP)
    ax.set_ylim(-0.1, 1.15)
    _panel_title(ax, 'Four waypoints, joined two ways')
    ax = axes[1]
    _plot_axes(ax, 'time (s)', 'joint speed (rad/s)')
    ax.plot(samples, lin_v, color=GRIP, lw=2)
    ax.plot(samples, sp_v, color=LINK, lw=2)
    ax.axhline(0, color=MUTED, lw=0.8)
    _label(ax, 1.05, 1.0, 'straight lines: speed jumps\nat every waypoint', color=GRIP, ha='left')
    _label(ax, 2.5, -0.33, 'spline: speed changes smoothly\nand is zero at both ends', color=LINK)
    ax.set_xlim(0, 3.0)
    fig.subplots_adjust(hspace=0.12)
    _save(fig, 'trajectory-generation', 'spline-vs-straight-lines.svg')


SYNC_MOVES: tuple[float, ...] = (1.2, 0.6, 0.2)


def sync_profiles() -> tuple[list[dict], list[dict]]:
    """Each joint alone at full limits, and all joints stretched to finish together."""
    alone = [trapezoid(d, V_MAX, A_MAX) for d in SYNC_MOVES]
    slowest = max(p['t'][-1] for p in alone)
    together = []
    for d in SYNC_MOVES:
        # keep the same acceleration time share as the slowest joint, scale speed down
        t_acc = V_MAX / A_MAX
        v = d / (slowest - t_acc)
        together.append(_integrate([(t_acc, v / t_acc), (slowest - 2 * t_acc, 0.0),
                                    (t_acc, -v / t_acc)], 'acc'))
    return alone, together


def synchronised_joints() -> None:
    alone, together = sync_profiles()
    colours = (LINK, WRIST, PURPLE)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.3), facecolor='white', sharey=True)
    for ax, profs, title in ((axes[0], alone, 'Each joint as fast as it can'),
                             (axes[1], together, 'Stretched so all finish together')):
        _plot_axes(ax, 'time (s)', 'joint speed (rad/s)' if profs is alone else '')
        for p, c in zip(profs, colours):
            ax.plot(p['t'], p['v'], color=c, lw=2)
            ax.plot([p['t'][-1]], [0], 'o', color=c, ms=7, zorder=5)
        _panel_title(ax, title)
        ax.set_xlim(0, 1.85)
        ax.set_ylim(-0.08, 1.15)
    _label(axes[0], 0.85, 1.05, 'joint 1: 1.2 rad, ends 1.70 s', color=LINK)
    _label(axes[0], 1.13, 0.13, f'joint 2: 0.6 rad,\nends {alone[1]["t"][-1]:.2f} s', color=WRIST,
           ha='left')
    _label(axes[0], 0.02, 0.95, f'joint 3: 0.2 rad,\nends {alone[2]["t"][-1]:.2f} s', color=PURPLE,
           ha='left')
    _label(axes[1], 0.85, 1.05, 'all three end at 1.70 s', color=INK)
    _label(axes[1], 0.85, together[1]['v'].max() + 0.07, f'{together[1]["v"].max():.2f} rad/s',
           color=WRIST)
    _label(axes[1], 0.85, together[2]['v'].max() + 0.07, f'{together[2]["v"].max():.2f} rad/s',
           color=PURPLE)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'trajectory-generation', 'synchronised-joints.svg')


# --------------------------------------------------------------------------
# 04_impedance-and-force-control
# --------------------------------------------------------------------------

def wall_runs() -> dict[str, dict[str, np.ndarray]]:
    target = ramp_target(-0.010, 0.020, 0.005)
    return {'position': position_run(target),
            'K2000': impedance_run(2000.0, 2 * 0.7 * np.sqrt(2000.0 * TOOL_MASS), target),
            'K500': impedance_run(500.0, 2 * 0.7 * np.sqrt(500.0 * TOOL_MASS), target)}


def into_the_wall() -> None:
    runs = wall_runs()
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), facecolor='white')
    ax = axes[0]
    _plot_axes(ax, 'time (s)', 'contact force (N)')
    ax.plot(runs['position']['t'], runs['position']['F'], color=GRIP, lw=2)
    ax.axhline(150, color=GRIP, lw=0.9, ls=':')
    ax.axvline(0.5, color=MUTED, lw=1, ls='--')
    _label(ax, 0.47, 120, 'touches\nthe wall', color=MUTED, ha='right')
    _label(ax, 1.95, 160, 'the motor\'s limit, 150 N', color=GRIP, ha='right')
    _label(ax, 1.4, 60, 'position control:\nthe force climbs\nto the limit', color=GRIP)
    ax.set_xlim(0, 2.0)
    ax.set_ylim(-5, 175)
    _panel_title(ax, 'Target 5 mm inside a stiff wall')
    ax = axes[1]
    _plot_axes(ax, 'time (s)', 'contact force (N)')
    for key, colour, k in (('K2000', LINK, 2000), ('K500', SLIDE, 500)):
        run = runs[key]
        ax.plot(run['t'], run['F'], color=colour, lw=2)
        _label(ax, 1.97, run['F'][-1] + 0.7,
               f'impedance K = {k} N/m: settles at {run["F"][-1]:.1f} N', color=colour,
               ha='right', va='bottom')
    ax.axvline(0.5, color=MUTED, lw=1, ls='--')
    ax.set_xlim(0, 2.0)
    ax.set_ylim(-0.5, 14)
    _label(ax, 0.47, 12.5, 'target passes\nthe wall surface', color=MUTED, ha='right')
    _panel_title(ax, 'The same target with a spring (note the scale)')
    fig.subplots_adjust(wspace=0.2)
    _save(fig, 'impedance-and-force-control', 'into-the-wall.svg')


BOUNCE_ZETAS: tuple[float, ...] = (0.1, 0.7, 1.5)


def bounce_runs() -> list[dict[str, np.ndarray]]:
    target = ramp_target(-0.010, 0.050, 0.005)
    k = 1000.0
    return [impedance_run(k, 2 * z * np.sqrt(k * TOOL_MASS), target, seconds=1.0)
            for z in BOUNCE_ZETAS]


def bounce() -> None:
    runs = bounce_runs()
    colours = (GRIP, WRIST, LINK)
    fig, axes = plt.subplots(3, 1, figsize=(10, 7.6), facecolor='white', sharex=True,
                             sharey=True)
    for ax, run, z, c in zip(axes, runs, BOUNCE_ZETAS, colours):
        _plot_axes(ax, 'time (s)' if ax is axes[-1] else '', 'force (N)')
        ax.plot(run['t'], run['F'], color=c, lw=1.6)
        d = 2 * z * np.sqrt(1000.0 * TOOL_MASS)
        first = np.argmax(run['F'] > 0)
        leaves = int((np.diff((run['F'][first:] > 0).astype(int)) == -1).sum())
        words = 'never leaves the wall' if leaves == 0 else f'leaves the wall {leaves} times'
        _label(ax, 0.98, 25, f'damping D = {d:.0f} N s/m: {words}', color=c, ha='right')
        ax.set_ylim(-1, 33)
    axes[-1].set_xlim(0.15, 1.0)
    axes[0].set_title('K = 1000 N/m, hitting a stiff wall at 50 mm/s', fontsize=11, color=INK,
                      weight='bold', loc='left', pad=10)
    fig.subplots_adjust(hspace=0.14)
    _save(fig, 'impedance-and-force-control', 'damping-and-bounce.svg')


def guarded_runs() -> dict[str, dict]:
    return {'slow': guarded_run(0.010), 'fast': guarded_run(0.050)}


def guarded_move() -> None:
    runs = guarded_runs()
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), facecolor='white', sharey=True)
    for ax, key, colour, title in ((axes[0], 'slow', SLIDE, 'Creeping at 10 mm/s'),
                                   (axes[1], 'fast', GRIP, 'Creeping at 50 mm/s')):
        run = runs[key]
        mm = run['x'] * 1000
        _plot_axes(ax, 'tool travel (mm)', 'force (N)' if key == 'slow' else '')
        ax.plot(mm, run['raw'], color=GRID, lw=1.0)
        ax.plot(mm, run['filtered'], color=MUTED, lw=1.4)
        ax.plot(mm, run['F'], color=colour, lw=2.2)
        ax.axhline(1.0, color=INK, lw=0.9, ls=':')
        ax.axvline(20.0, color=MUTED, lw=1, ls='--')
        fx = run['fired']['x'] * 1000
        ax.plot([fx], [1.0], 'o', color=INK, ms=6, zorder=6)
        end = mm[-1]
        peak = run['F'].max()
        _label(ax, 19.2, 13.0, 'surface\nat 20 mm', color=MUTED, ha='right')
        _label(ax, 15.5, 1.9, 'threshold 1 N', color=INK)
        _label(ax, 14.3, 8.0, f'fired at {fx:.2f} mm\nstopped at {end:.2f} mm\npeak force {peak:.1f} N',
               color=colour, ha='left')
        _panel_title(ax, title)
        ax.set_xlim(14, 24)
        ax.set_ylim(-0.6, 16)
    _label(axes[0], 16.5, 0.45, 'noisy readings (light grey) and their average', color=MUTED,
           size=8.5)
    fig.subplots_adjust(wspace=0.08)
    _save(fig, 'impedance-and-force-control', 'guarded-move.svg')


ADM_CASES: tuple[tuple[str, float, float], ...] = (
    ('foam, D = 200', 2000.0, 200.0),
    ('metal, D = 200', 200000.0, 200.0),
    ('metal, D = 1000', 200000.0, 1000.0),
    ('metal, D = 5000', 200000.0, 5000.0),
)


def admittance_runs() -> list[dict[str, np.ndarray]]:
    return [admittance_run(k, d) for _, k, d in ADM_CASES]


def admittance_buzz() -> None:
    runs = admittance_runs()
    colours = (SLIDE, GRIP, WRIST, LINK)
    fig, axes = plt.subplots(2, 2, figsize=(14, 6.6), facecolor='white', sharex=True)
    for ax, run, (name, k, d), c in zip(axes.flat, runs, ADM_CASES, colours):
        _plot_axes(ax, 'time (s)' if ax in axes[1] else '', 'force (N)')
        ax.plot(run['t'], run['F'], color=c, lw=1.4)
        ax.axhline(10.0, color=MUTED, lw=0.9, ls='--')
        tail = run['F'][run['t'] > 1.0]
        ax.set_title(f'{name} N s/m', fontsize=11, color=INK, weight='bold', loc='left', pad=22)
        top = max(14.0, run['F'].max() * 1.08)
        ax.set_ylim(-0.03 * top, top)
        ax.set_xlim(0, 1.5)
        txt = (f'last half second: {tail.min():.1f} to {tail.max():.1f} N')
        ax.text(0.0, 1.03, txt, transform=ax.transAxes, fontsize=9.5, color=c, ha='left',
                va='bottom')
    _label(axes[0, 0], 1.0, 8.3, 'wanted: press with 10 N', color=MUTED)
    fig.subplots_adjust(hspace=0.42, wspace=0.18)
    _save(fig, 'impedance-and-force-control', 'admittance-buzz.svg')


# --------------------------------------------------------------------------
# the numbers the documents quote
# --------------------------------------------------------------------------

def print_numbers() -> None:
    print('== PID step, 0.5 rad, J=0.05 B=0.5 load=1.0')
    for key, run in pid_runs().items():
        s = step_stats(run, STEP)
        print(f'  {key}: overshoot {s["overshoot"]:.1f}%  settle {s["settle"]:.3f} s  '
              f'end error {s["end_error"]:.4f} rad ({np.degrees(s["end_error"]):.2f} deg)  '
              f'peak torque {run["torque"].max():.2f}')
    run = pid_runs()['PID']
    for tick in (0, 1, 2, 100):
        print(f'  PID tick {tick}: t={run["t"][tick]:.3f} angle={run["angle"][tick]:.5f} '
              f'P={run["P"][tick]:.4f} I={run["I"][tick]:.5f} D={run["D"][tick]:.4f} '
              f'torque={run["torque"][tick]:.4f}')
    print(f'  PID final I term {run["I"][-1]:.4f}')
    for key, r in windup_runs().items():
        s = step_stats(r, 1.5)
        print(f'  windup {key}: overshoot {s["overshoot"]:.1f}% settle {s["settle"]:.3f} '
              f'max I {r["I"].max():.2f}')
    for key, r in derivative_runs().items():
        steady = r['D'][r['t'] > 1.0]
        print(f'  D noise {key}: largest one-tick jump {np.abs(np.diff(r["D"])).max():.3f}  '
              f'std after 1 s {steady.std():.3f}  overshoot {step_stats(r, STEP)["overshoot"]:.1f}')
    print('== trajectories')
    tr, sc = trapezoid(MOVE, V_MAX, A_MAX), s_curve(MOVE, V_MAX, A_MAX, J_MAX)
    print(f'  trapezoid ends {tr["t"][-1]:.3f} s at {tr["p"][-1]:.4f}; s-curve ends '
          f'{sc["t"][-1]:.3f} s at {sc["p"][-1]:.4f}')
    tri = trapezoid(0.3, V_MAX, A_MAX)
    print(f'  short 0.3 rad move: triangle ends {tri["t"][-1]:.3f} s, peak speed {tri["v"].max():.3f}')
    for f in (2.0, 3.0, 4.0, 5.0, 6.0, 8.0):
        print(f'  residual at {f:g} Hz: trapezoid {residual_vibration(tr, f)[2]:.2f} mm, '
              f's-curve {residual_vibration(sc, f)[2]:.2f} mm')
    samples = np.linspace(0.0, 3.0, 3001)
    _, sv, sa = clamped_spline(WAY_T, WAY_Q, samples)
    lin = np.diff(WAY_Q) / np.diff(WAY_T)
    print(f'  linear segment speeds {lin}; spline max speed {np.abs(sv).max():.3f}, '
          f'max accel {np.abs(sa).max():.3f}')
    alone, together = sync_profiles()
    print('  alone ends', [round(p['t'][-1], 3) for p in alone], ' together peak speeds',
          [round(p['v'].max(), 3) for p in together], ' ends', [round(p['t'][-1], 3) for p in together])
    mv = overview_move()
    print('== overview move: waypoint times', np.round(mv['times'], 3))
    for j in range(2):
        r = mv['joints'][j]['run']
        err = np.degrees(r['target'] - r['angle'])
        i_end = int(round(mv['times'][-1] / DT))
        print(f'  joint {j + 1}: max following error {np.abs(err).max():.2f} deg, at the end '
              f'{err[i_end]:.2f} deg, 0.5 s later {err[min(i_end + 500, len(err) - 1)]:.3f} deg')
    sl = slow_commands()
    for key, r in sl.items():
        print(f'  slow commands {key}: peak |torque| {np.abs(r["torque"]).max():.2f}, largest '
              f'one-tick torque change {np.abs(np.diff(r["torque"])).max():.2f}')
    print('== contact')
    for key, r in wall_runs().items():
        first = r['t'][np.argmax(r['F'] > 0)]
        print(f'  {key}: contact at {first:.3f} s, final force {r["F"][-1]:.2f} N, peak '
              f'{r["F"].max():.2f}, final x {r["x"][-1] * 1000:.3f} mm')
        if key == 'position':
            reach = r['t'][np.argmax(r['F'] > 140)]
            print(f'    passes 140 N at {reach:.3f} s')
    for z, r in zip(BOUNCE_ZETAS, bounce_runs()):
        first = np.argmax(r['F'] > 0)
        leaves = int((np.diff((r['F'][first:] > 0).astype(int)) == -1).sum())
        print(f'  bounce zeta {z}: D {2 * z * np.sqrt(1000 * TOOL_MASS):.1f} peak {r["F"].max():.2f} '
              f'leaves {leaves} final {r["F"][-1]:.2f}')
    for key, r in guarded_runs().items():
        print(f'  guarded {key}: fired {r["fired"]}, stopped {r["x"][-1] * 1000:.3f} mm, '
              f'peak {r["F"].max():.2f} N')
    miss = guarded_run(0.010, surface=1.0)
    print(f'  guarded, nothing there: fired {miss["fired"]}, stopped {miss["x"][-1] * 1000:.2f} mm')
    for (name, _, _), r in zip(ADM_CASES, admittance_runs()):
        tail = r['F'][r['t'] > 1.0]
        print(f'  admittance {name}: peak {r["F"].max():.1f}, last 0.5 s {tail.min():.2f} to '
              f'{tail.max():.2f}, mean {tail.mean():.2f}')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    one_move_three_layers()
    slow_commands_figure()
    step_responses()
    three_terms()
    windup()
    derivative_noise()
    profiles()
    vibration()
    spline_vs_linear()
    synchronised_joints()
    into_the_wall()
    bounce()
    guarded_move()
    admittance_buzz()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
