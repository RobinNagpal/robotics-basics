"""Generate the diagrams for the arm dynamics page of Book 5, chapter 7.

The page is docs/06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md.
Its pictures go to docs/images/control-and-motion/arm-dynamics/.

Run with:  pixi run python ../docs/diagrams/control_and_motion_2.py
Add --png <dir> to also write PNG copies for checking.
Add --numbers to print the numbers the page quotes, without drawing.

Every curve here is simulated, not drawn by hand. The model is a two-joint arm
that swings in a vertical plane, so gravity pulls on both joints:

- link 1 is 0.30 m long and weighs 2.0 kg; link 2 is 0.25 m long and weighs
  1.0 kg; each link is a uniform rod, so its mass is centred at its middle
- an optional payload of 0.5 kg sits at the tip of link 2
- the "real" arm also has viscous friction of 0.02 N m s/rad in each joint;
  the controllers' model uses 0.016, a value 20 per cent too low, because a
  measured friction value is never exact
- angles are measured from the horizontal, anticlockwise positive; joint 2's
  angle is measured from link 1

The torques come from the closed-form equations of motion of a two-link arm,
and are checked against a small recursive Newton-Euler routine, which is the
method Pinocchio's rnea and KDL's ChainIdSolver_RNE use.

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
FOLDER: str = 'arm-dynamics'
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
PURPLE: str = '#8e5bb5'


# --------------------------------------------------------------------------
# small drawing helpers (the same look as control_and_motion.py)
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


def _save(fig: Figure, name: str) -> None:
    out: pathlib.Path = IMAGES / FOLDER
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{FOLDER}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# the arm
# --------------------------------------------------------------------------

G: float = 9.81             # m/s^2
L1: float = 0.30            # m
L2: float = 0.25            # m
M1: float = 2.0             # kg
M2: float = 1.0             # kg
PAYLOAD: float = 0.5        # kg, at the tip of link 2
FRICTION: float = 0.02       # N m s / rad, in the "real" arm
FRICTION_MODEL: float = 0.016   # N m s / rad, what the controllers' model believes
DT: float = 0.001           # s, the controller runs 1000 times a second
SUB: int = 10               # physics steps per controller step


def params(payload: float = 0.0) -> dict[str, float]:
    """Mass, centre-of-mass distance and inertia (about the centre of mass) of each link.

    A payload at the tip is folded into link 2: its mass is added, the centre of
    mass moves towards the tip, and the inertia grows.
    """
    lc1, lc2 = L1 / 2, L2 / 2
    i1, i2 = M1 * L1 ** 2 / 12, M2 * L2 ** 2 / 12
    m2 = M2 + payload
    lc2_new = (M2 * lc2 + payload * L2) / m2
    i2_new = i2 + M2 * (lc2 - lc2_new) ** 2 + payload * (L2 - lc2_new) ** 2
    return {'m1': M1, 'lc1': lc1, 'i1': i1, 'm2': m2, 'lc2': lc2_new, 'i2': i2_new}


def mass_matrix(q: np.ndarray, p: dict[str, float]) -> np.ndarray:
    c2 = np.cos(q[1])
    m11 = (p['i1'] + p['i2'] + p['m1'] * p['lc1'] ** 2
           + p['m2'] * (L1 ** 2 + p['lc2'] ** 2 + 2 * L1 * p['lc2'] * c2))
    m12 = p['i2'] + p['m2'] * (p['lc2'] ** 2 + L1 * p['lc2'] * c2)
    m22 = p['i2'] + p['m2'] * p['lc2'] ** 2
    return np.array([[m11, m12], [m12, m22]])


def speed_terms(q: np.ndarray, qd: np.ndarray, p: dict[str, float]) -> np.ndarray:
    """The Coriolis and centrifugal torques: the ones that depend on the joint speeds."""
    h = p['m2'] * L1 * p['lc2'] * np.sin(q[1])
    return np.array([-h * (2 * qd[0] * qd[1] + qd[1] ** 2), h * qd[0] ** 2])


def gravity(q: np.ndarray, p: dict[str, float]) -> np.ndarray:
    c1, c12 = np.cos(q[0]), np.cos(q[0] + q[1])
    g2 = p['m2'] * p['lc2'] * G * c12
    g1 = (p['m1'] * p['lc1'] + p['m2'] * L1) * G * c1 + g2
    return np.array([g1, g2])


def inverse_dynamics(q, qd, qdd, p) -> np.ndarray:
    """Motion in, torques out: tau = M(q) qdd + c(q, qd) + g(q)."""
    return mass_matrix(q, p) @ qdd + speed_terms(q, qd, p) + gravity(q, p)


def forward_dynamics(q, qd, tau, p, friction: float = 0.0) -> np.ndarray:
    """Torques in, motion out: qdd = M(q)^-1 (tau - c - g - friction)."""
    rhs = tau - speed_terms(q, qd, p) - gravity(q, p) - friction * qd
    return np.linalg.solve(mass_matrix(q, p), rhs)


def rnea(q, qd, qdd, p) -> np.ndarray:
    """Recursive Newton-Euler for a planar two-link arm, as a check on the closed form.

    Outward pass: the speed and acceleration of each link's centre of mass.
    Inward pass: the force and torque each joint must pass on to hold up and
    accelerate everything beyond it.
    """
    lengths = [L1, L2]
    masses = [p['m1'], p['m2']]
    lcs = [p['lc1'], p['lc2']]
    inert = [p['i1'], p['i2']]
    # outward pass, in the base frame; gravity is treated as an upward acceleration of the base
    th, w, al = 0.0, 0.0, 0.0
    a_joint = np.array([0.0, G])
    acc_com, angs, alphas, joints = [], [], [], [np.zeros(2)]
    for i in range(2):
        th += q[i]
        w += qd[i]
        al += qdd[i]
        u = np.array([np.cos(th), np.sin(th)])
        n = np.array([-u[1], u[0]])
        a_com = a_joint + al * lcs[i] * n - w ** 2 * lcs[i] * u
        a_joint = a_joint + al * lengths[i] * n - w ** 2 * lengths[i] * u
        acc_com.append(a_com)
        angs.append(u)
        alphas.append(al)
        joints.append(joints[-1] + lengths[i] * u)
    # inward pass
    f_next, n_next = np.zeros(2), 0.0
    tau = np.zeros(2)
    for i in (1, 0):
        u = angs[i]
        f = masses[i] * acc_com[i] + f_next
        r_com = lcs[i] * u              # from joint i to the centre of mass
        r_end = lengths[i] * u          # from joint i to joint i+1
        cross = lambda a, b: a[0] * b[1] - a[1] * b[0]   # noqa: E731
        n = inert[i] * alphas[i] + n_next + cross(r_com, masses[i] * acc_com[i]) \
            + cross(r_end, f_next)
        tau[i] = n
        f_next, n_next = f, n
    return tau


def tip(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    elbow = np.array([L1 * np.cos(q[0]), L1 * np.sin(q[0])])
    end = elbow + np.array([L2 * np.cos(q[0] + q[1]), L2 * np.sin(q[0] + q[1])])
    return elbow, end


# --------------------------------------------------------------------------
# a move, and a simulator
# --------------------------------------------------------------------------

Q_START: np.ndarray = np.radians([-45.0, 90.0])
Q_END: np.ndarray = np.radians([60.0, -30.0])
T_MOVE: float = 0.8         # s
T_HOLD: float = 0.7         # s of standing still after the move


def quintic(t: float, q0: np.ndarray, q1: np.ndarray, duration: float):
    """A smooth move that starts and ends at rest, as on the trajectory generation page."""
    s = np.clip(t / duration, 0.0, 1.0)
    d = q1 - q0
    pos = q0 + d * (10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5)
    if t <= 0 or t >= duration:
        return pos, np.zeros(2), np.zeros(2)
    vel = d * (30 * s ** 2 - 60 * s ** 3 + 30 * s ** 4) / duration
    acc = d * (60 * s - 180 * s ** 2 + 120 * s ** 3) / duration ** 2
    return pos, vel, acc


def move_parts(payload: float = 0.0) -> dict[str, np.ndarray]:
    """The torque parts along the planned move, from inverse dynamics."""
    p = params(payload)
    ts = np.arange(0.0, T_MOVE + 1e-9, DT)
    out = {k: np.zeros((len(ts), 2)) for k in ('inertia', 'speed', 'gravity', 'total', 'rnea')}
    for k, t in enumerate(ts):
        q, qd, qdd = quintic(t, Q_START, Q_END, T_MOVE)
        out['inertia'][k] = mass_matrix(q, p) @ qdd
        out['speed'][k] = speed_terms(q, qd, p)
        out['gravity'][k] = gravity(q, p)
        out['total'][k] = inverse_dynamics(q, qd, qdd, p)
        out['rnea'][k] = rnea(q, qd, qdd, p)
    out['t'] = ts
    return out


def simulate(controller, q0: np.ndarray, seconds: float, payload: float = 0.0,
             friction: float = FRICTION) -> dict[str, np.ndarray]:
    """Run the 'real' arm under a controller that is called 1000 times a second."""
    p_real = params(payload)
    n = int(round(seconds / DT))
    q, qd = q0.astype(float).copy(), np.zeros(2)
    state: dict = {}
    ts, qs, taus = np.zeros(n), np.zeros((n, 2)), np.zeros((n, 2))
    h = DT / SUB
    for k in range(n):
        t = k * DT
        tau = controller(t, q.copy(), qd.copy(), state)
        ts[k], qs[k], taus[k] = t, q, tau
        for _ in range(SUB):                    # semi-implicit Euler at 10 kHz
            qdd = forward_dynamics(q, qd, tau, p_real, friction)
            qd = qd + h * qdd
            q = q + h * qd
    return {'t': ts, 'q': qs, 'tau': taus}


# the controllers' gains
KP_PID: np.ndarray = np.array([60.0, 30.0])      # N m / rad
KI_PID: np.ndarray = np.array([60.0, 30.0])      # N m / (rad s)
KD_PID: np.ndarray = np.array([4.0, 1.5])        # N m s / rad
WN: float = 20.0                                  # rad/s, for computed torque
KP_CT: float = WN ** 2                            # 1/s^2
KD_CT: float = 2 * WN                             # 1/s


def make_pid(model: dict[str, float], feed_forward: str):
    """A PID per joint, with nothing, gravity, or the full model added as feed-forward.

    feed_forward is 'none', 'gravity' or 'full'. For 'none' the integral starts
    at the torque that held the arm at the start pose, as it would after the
    arm had been standing there for a while.
    """
    def controller(t, q, qd, state):
        qr, qdr, qddr = quintic(t, Q_START, Q_END, T_MOVE)
        e = qr - q
        ed = qdr - qd
        if 'integral' not in state:
            state['integral'] = gravity(Q_START, model) / KI_PID if feed_forward == 'none' \
                else np.zeros(2)
        state['integral'] = state['integral'] + e * DT
        tau = KP_PID * e + KI_PID * state['integral'] + KD_PID * ed
        if feed_forward == 'gravity':
            tau = tau + gravity(q, model)
        elif feed_forward == 'full':
            tau = tau + inverse_dynamics(qr, qdr, qddr, model) + FRICTION_MODEL * qdr
        return tau
    return controller


def make_computed_torque(model: dict[str, float]):
    """tau = M(q) (qdd_ref + Kp e + Kd ed) + c(q, qd) + g(q) + friction."""
    def controller(t, q, qd, state):
        qr, qdr, qddr = quintic(t, Q_START, Q_END, T_MOVE)
        e = qr - q
        ed = qdr - qd
        v = qddr + KP_CT * e + KD_CT * ed
        return (mass_matrix(q, model) @ v + speed_terms(q, qd, model) + gravity(q, model)
                + FRICTION_MODEL * qd)
    return controller


def tracking_runs() -> dict[str, dict[str, np.ndarray]]:
    model = params(0.0)
    secs = T_MOVE + T_HOLD
    return {
        'pid': simulate(make_pid(model, 'none'), Q_START, secs),
        'pid_g': simulate(make_pid(model, 'gravity'), Q_START, secs),
        'pid_ff': simulate(make_pid(model, 'full'), Q_START, secs),
        'ct': simulate(make_computed_torque(model), Q_START, secs),
    }


def payload_runs() -> dict[str, dict[str, np.ndarray]]:
    """Computed torque with a 0.5 kg payload that the model does or does not know about."""
    secs = T_MOVE + T_HOLD
    return {
        'unknown': simulate(make_computed_torque(params(0.0)), Q_START, secs, payload=PAYLOAD),
        'known': simulate(make_computed_torque(params(PAYLOAD)), Q_START, secs, payload=PAYLOAD),
    }


def errors_deg(run: dict[str, np.ndarray]) -> np.ndarray:
    ref = np.array([quintic(t, Q_START, Q_END, T_MOVE)[0] for t in run['t']])
    return np.degrees(ref - run['q'])


# --------------------------------------------------------------------------
# holding still, and falling
# --------------------------------------------------------------------------

Q_HOLD: np.ndarray = np.radians([30.0, 45.0])
KP_HOLD: np.ndarray = np.array([60.0, 30.0])
KD_HOLD: np.ndarray = np.array([4.0, 1.5])


def fall_run(seconds: float = 0.6) -> dict[str, np.ndarray]:
    """Forward dynamics with zero torque: the arm starts still at Q_HOLD and falls."""
    return simulate(lambda t, q, qd, s: np.zeros(2), Q_HOLD, seconds, friction=FRICTION)


def hold_run(with_gravity: bool, seconds: float = 3.0) -> dict[str, np.ndarray]:
    model = params(0.0)

    def controller(t, q, qd, state):
        tau = KP_HOLD * (Q_HOLD - q) - KD_HOLD * qd
        if with_gravity:
            tau = tau + gravity(q, model)
        return tau
    return simulate(controller, Q_HOLD, seconds)


# --------------------------------------------------------------------------
# finding the masses: hold still at many poses, fit the gravity torques
# --------------------------------------------------------------------------

def gravity_regressor(q: np.ndarray) -> np.ndarray:
    """Gravity torques are a (known matrix) times (two unknown numbers a and b).

    g1 = a cos(q1) + b cos(q1 + q2),  g2 = b cos(q1 + q2)
    with a = (m1 lc1 + m2 L1) g and b = m2 lc2 g.
    """
    c1, c12 = np.cos(q[0]), np.cos(q[0] + q[1])
    return np.array([[c1, c12], [0.0, c12]])


def identify(payload: float, poses: int = 20, noise: float = 0.05,
             seed: int = 7) -> dict[str, np.ndarray]:
    """Record the holding torque at random poses (with sensor noise) and fit a, b by least squares."""
    rng = np.random.default_rng(seed)
    p = params(payload)
    qs = np.column_stack([rng.uniform(-np.pi / 2, np.pi / 2, poses),
                          rng.uniform(-2.5, 2.5, poses)])
    rows, meas = [], []
    for q in qs:
        rows.append(gravity_regressor(q))
        meas.append(gravity(q, p) + rng.normal(0.0, noise, 2))
    y = np.concatenate(meas)
    a_mat = np.vstack(rows)
    theta, *_ = np.linalg.lstsq(a_mat, y, rcond=None)
    true = np.array([(p['m1'] * p['lc1'] + p['m2'] * L1) * G, p['m2'] * p['lc2'] * G])
    return {'qs': qs, 'meas': np.array(meas), 'theta': theta, 'true': true}


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------

def torque_parts() -> None:
    """Figure 1: the torque each joint needs along one fast move, split into its three parts."""
    r = move_parts()
    t = r['t']
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6),
                             gridspec_kw={'width_ratios': [0.85, 1.2, 1.2]})
    ax = axes[0]
    ax.set_aspect('equal')
    ax.axis('off')
    for k, s in enumerate(np.linspace(0, 1, 7)):
        q, _, _ = quintic(s * T_MOVE, Q_START, Q_END, T_MOVE)
        elbow, end = tip(q)
        first, last = k == 0, k == 6
        col = LINK if (first or last) else LINK_PALE
        ax.plot([0, elbow[0], end[0]], [0, elbow[1], end[1]], color=col, lw=4 if first or last else 3,
                solid_capstyle='round', zorder=3 if first or last else 2)
        ax.plot(*elbow, 'o', color=JOINT, ms=7 if first or last else 5, zorder=4)
    ax.plot(0, 0, 's', color=INK, ms=10, zorder=5)
    ax.plot([-0.12, 0.12], [-0.03, -0.03], color=INK, lw=2)
    e0, t0 = tip(Q_START)
    e1, t1 = tip(Q_END)
    _label(ax, e0[0] + 0.02, e0[1] - 0.07, 'start (−45°, 90°)', size=9)
    _label(ax, t1[0] + 0.02, t1[1] + 0.07, 'end\n(60°, −30°)', size=9)
    ax.annotate('', xy=(0.0, -0.2), xytext=(0.0, -0.08),
                arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.2})
    _label(ax, 0.07, -0.16, 'gravity', size=9, color=MUTED)
    ax.set_xlim(-0.2, 0.55)
    ax.set_ylim(-0.33, 0.55)
    _panel_title(ax, 'The move: 0.8 s')

    for j, ax in enumerate(axes[1:]):
        _plot_axes(ax, 'time (s)', 'torque (N m)')
        ax.plot(t, r['inertia'][:, j], color=LINK, lw=1.8, label='inertia × acceleration')
        ax.plot(t, r['speed'][:, j], color=PURPLE, lw=1.8, label='speed terms (Coriolis)')
        ax.plot(t, r['gravity'][:, j], color=SLIDE, lw=1.8, label='gravity')
        ax.plot(t, r['total'][:, j], color=INK, lw=2.2, ls='--', label='total torque needed')
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xlim(0, T_MOVE)
        _panel_title(ax, f'Joint {j + 1} ({"shoulder" if j == 0 else "elbow"})')
    axes[1].legend(loc='lower left', fontsize=8.5, frameon=False)
    fig.tight_layout()
    _save(fig, 'torque-parts.svg')


def _draw_arm(ax: Axes, q: np.ndarray, color: str, lw: float = 4.0, alpha: float = 1.0,
              z: int = 3) -> None:
    elbow, end = tip(q)
    ax.plot([0, elbow[0], end[0]], [0, elbow[1], end[1]], color=color, lw=lw, alpha=alpha,
            solid_capstyle='round', zorder=z)
    ax.plot(*elbow, 'o', color=JOINT, ms=6, alpha=alpha, zorder=z + 1)


def fall_and_hold() -> None:
    """Figure 2: forward dynamics with no torque (the arm falls), and PD holding with and without gravity."""
    fall = fall_run()
    no_g = hold_run(False)
    with_g = hold_run(True)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))

    ax = axes[0]
    ax.set_aspect('equal')
    ax.axis('off')
    marks = [0.0, 0.15, 0.25, 0.35]
    for k, tm in enumerate(marks):
        i = min(int(round(tm / DT)), len(fall['t']) - 1)
        q = fall['q'][i]
        alpha = 1.0 if k == 0 else 0.4 + 0.6 * k / (len(marks) - 1)
        _draw_arm(ax, q, LINK if k == 0 else GRIP, lw=3.5, alpha=alpha)
        _, end = tip(q)
        _label(ax, end[0] + 0.03, end[1], f'{tm:.2f} s', size=9, ha='left')
    ax.plot(0, 0, 's', color=INK, ms=10, zorder=6)
    ax.plot([-0.12, 0.12], [-0.03, -0.03], color=INK, lw=2)
    ax.set_xlim(-0.2, 0.55)
    ax.set_ylim(-0.55, 0.48)
    _panel_title(ax, 'Zero torque: forward dynamics lets it fall')

    ax = axes[1]
    ax.set_aspect('equal')
    ax.axis('off')
    _draw_arm(ax, Q_HOLD, LINK_PALE, lw=9, z=2)
    _draw_arm(ax, no_g['q'][-1], GRIP, lw=3.5, z=4)
    _draw_arm(ax, with_g['q'][-1], SLIDE, lw=3.5, z=5)
    ax.plot(0, 0, 's', color=INK, ms=10, zorder=6)
    ax.plot([-0.12, 0.12], [-0.03, -0.03], color=INK, lw=2)
    _, end_t = tip(Q_HOLD)
    _, end_s = tip(no_g['q'][-1])
    sag = np.degrees(Q_HOLD - no_g['q'][-1])
    _label(ax, end_t[0] + 0.04, end_t[1] + 0.05,
           'target, and PD + gravity\ncompensation (green): on it', size=9, color=SLIDE, ha='left')
    _label(ax, end_s[0] + 0.04, end_s[1] - 0.04,
           f'PD alone (red): sags\n{sag[0]:.1f}° at the shoulder,\n{sag[1]:.1f}° at the elbow',
           size=9, color=GRIP, ha='left')
    ax.set_xlim(-0.15, 0.75)
    ax.set_ylim(-0.1, 0.62)
    _panel_title(ax, 'Holding (30°, 45°) for 3 s')
    fig.tight_layout()
    _save(fig, 'fall-and-hold.svg')


def three_controllers() -> None:
    """Figure 3: tracking error on the same move under three controllers."""
    runs = tracking_runs()
    names = {'pid': ('PID only', GRIP), 'pid_g': ('PID + gravity compensation', WRIST),
             'pid_ff': ('PID + full inverse-dynamics feed-forward', PURPLE),
             'ct': ('computed torque', SLIDE)}
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.4))
    for j, ax in enumerate(axes):
        _plot_axes(ax, 'time (s)', 'error (degrees)')
        for key, (name, col) in names.items():
            e = errors_deg(runs[key])
            ax.plot(runs[key]['t'], e[:, j], color=col, lw=1.9, label=name)
        ax.axvspan(0, T_MOVE, color='#f3f3f3', zorder=0)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xlim(0, T_MOVE + T_HOLD)
        _label(ax, 0.02, ax.get_ylim()[1] * 0.95, 'moving', size=9, color=MUTED, ha='left')
        _label(ax, T_MOVE + 0.03, ax.get_ylim()[1] * 0.95, 'holding the end pose',
               size=9, color=MUTED, ha='left')
        _panel_title(ax, f'Joint {j + 1} ({"shoulder" if j == 0 else "elbow"})')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=4, fontsize=9.5, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, 'three-controllers.svg')


def payload_and_identification() -> None:
    """Figure 4: an unknown payload spoils computed torque; holding still at many poses finds it."""
    runs = payload_runs()
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6))
    ax = axes[0]
    _plot_axes(ax, 'time (s)', 'elbow error (degrees)')
    for key, name, col in (('unknown', 'model thinks the gripper is empty', GRIP),
                           ('known', 'model includes the 0.5 kg payload', SLIDE)):
        e = errors_deg(runs[key])
        ax.plot(runs[key]['t'], e[:, 1], color=col, lw=1.9, label=name)
    ax.axvspan(0, T_MOVE, color='#f3f3f3', zorder=0)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlim(0, T_MOVE + T_HOLD)
    ax.legend(loc='center right', fontsize=9, frameon=False)
    _panel_title(ax, 'Computed torque, carrying 0.5 kg')

    ax = axes[1]
    empty = identify(0.0)
    loaded = identify(PAYLOAD, seed=8)
    _plot_axes(ax, 'cos(q1 + q2)', 'elbow holding torque (N m)')
    xs = np.linspace(-1, 1, 50)
    for r, col, name in ((empty, LINK, 'empty'), (loaded, WRIST, 'with payload')):
        c12 = np.cos(r['qs'][:, 0] + r['qs'][:, 1])
        ax.plot(c12, r['meas'][:, 1], 'o', color=col, ms=5, alpha=0.8)
        ax.plot(xs, r['theta'][1] * xs, color=col, lw=1.8,
                label=f'{name}: fitted slope b = {r["theta"][1]:.3f} N m')
    ax.legend(loc='upper left', fontsize=9, frameon=False)
    mp = (loaded['theta'][1] - empty['theta'][1]) / (G * L2)
    _label(ax, 0.5, -1.9, f'payload = change in b ÷ (g × L2)\n= {mp:.2f} kg (true 0.50 kg)',
           size=9.5)
    _panel_title(ax, 'Finding the payload from 20 still poses')
    fig.tight_layout()
    _save(fig, 'payload-and-identification.svg')


# --------------------------------------------------------------------------
# numbers quoted on the page
# --------------------------------------------------------------------------

def print_numbers() -> None:
    np.set_printoptions(precision=4, suppress=True)
    p = params(0.0)
    print('link parameters:', {k: round(v, 5) for k, v in p.items()})
    print('with payload:', {k: round(v, 5) for k, v in params(PAYLOAD).items()})

    q = np.radians([30.0, 45.0])
    qd = np.array([1.0, 2.0])
    qdd = np.array([3.0, -2.0])
    mm = mass_matrix(q, p)
    print('\nworked example at q = (30, 45) deg, qd = (1, 2) rad/s, qdd = (3, -2) rad/s^2')
    print('  M =', mm)
    print('  M qdd =', mm @ qdd)
    print('  h = m2 L1 lc2 sin q2 =', p['m2'] * L1 * p['lc2'] * np.sin(q[1]))
    print('  speed terms =', speed_terms(q, qd, p))
    print('  gravity =', gravity(q, p))
    print('  total =', inverse_dynamics(q, qd, qdd, p))
    print('  rnea  =', rnea(q, qd, qdd, p))
    print('  forward dynamics of that total gives qdd =',
          forward_dynamics(q, qd, inverse_dynamics(q, qd, qdd, p), p))
    print('  gravity with payload =', gravity(q, params(PAYLOAD)))
    print('  still (qd=0,qdd=0) torque = gravity:', inverse_dynamics(q, np.zeros(2), np.zeros(2), p))

    r = move_parts()
    print('\nmove: largest |difference| closed form vs rnea:', np.abs(r['total'] - r['rnea']).max())
    for j in range(2):
        for key in ('inertia', 'speed', 'gravity', 'total'):
            col = r[key][:, j]
            print(f'  joint {j + 1} {key:8s}: min {col.min():7.3f}  max {col.max():7.3f}')
    rp = move_parts(PAYLOAD)
    print('  with payload, joint 1 total max |.|:', np.abs(rp['total'][:, 0]).max(),
          ' empty:', np.abs(r['total'][:, 0]).max())

    fall = fall_run()
    for tm in (0.15, 0.25, 0.35, 0.45, 0.6):
        i = min(int(round(tm / DT)), len(fall['t']) - 1)
        print(f'\nfall at {tm:.2f} s: q = {np.degrees(fall["q"][i])}' if tm == 0.15 else
              f'fall at {tm:.2f} s: q = {np.degrees(fall["q"][i])}')
    for wg in (False, True):
        h = hold_run(wg)
        print(f'hold with gravity={wg}: final error deg = {np.degrees(Q_HOLD - h["q"][-1])}, '
              f'final tau = {h["tau"][-1]}')
    print('  gravity at Q_HOLD =', gravity(Q_HOLD, p), ' / Kp =', gravity(Q_HOLD, p) / KP_HOLD)

    print()
    runs = tracking_runs()
    for key, run in runs.items():
        e = errors_deg(run)
        mov = run['t'] <= T_MOVE
        end = run['t'] >= T_MOVE + T_HOLD - 0.05
        print(f'{key:6s}: max |err| during move j1 {np.abs(e[mov, 0]).max():.3f} '
              f'j2 {np.abs(e[mov, 1]).max():.3f}; at end j1 {e[-1, 0]:.4f} j2 {e[-1, 1]:.4f}; '
              f'max |err| last 50 ms {np.abs(e[end]).max():.4f}')
    pr = payload_runs()
    for key, run in pr.items():
        e = errors_deg(run)
        mov = run['t'] <= T_MOVE
        print(f'payload {key:8s}: max |err| move j1 {np.abs(e[mov, 0]).max():.3f} '
              f'j2 {np.abs(e[mov, 1]).max():.3f}; at end j1 {e[-1, 0]:.4f} j2 {e[-1, 1]:.4f}')

    print()
    for pl, seed in ((0.0, 7), (PAYLOAD, 8)):
        r = identify(pl, seed=seed)
        print(f'identify payload={pl}: fitted a, b = {r["theta"]}, true = {r["true"]}')
    e0, e1 = identify(0.0), identify(PAYLOAD, seed=8)
    print('  payload estimate from b:', (e1['theta'][1] - e0['theta'][1]) / (G * L2))


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    torque_parts()
    fall_and_hold()
    three_controllers()
    payload_and_identification()
    print(f'wrote the diagrams under {IMAGES / FOLDER}')


if __name__ == '__main__':
    main()
