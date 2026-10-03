"""Generate the diagrams for two pages in Book 5.

- docs/06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md
  writes to docs/images/fitting-and-estimation/sensor-streams/
- docs/06_programming-techniques/07_control-and-motion/02_most-used/04_safety-monitoring.md
  writes to docs/images/control-and-motion/safety-monitoring/

Run with:  pixi run python ../docs/diagrams/sensor_streams_and_safety.py
Add --png <dir> to also write PNG copies for checking.

Every curve here is computed, not drawn by hand. The force traces come from a
seeded random generator, the filters, slopes, thresholds, limiters, watchdog and
speed-and-separation rule really run on them, and the script prints the numbers
the two pages quote.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

DOCS: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
STREAMS: pathlib.Path = DOCS / 'images' / 'fitting-and-estimation' / 'sensor-streams'
SAFETY: pathlib.Path = DOCS / 'images' / 'control-and-motion' / 'safety-monitoring'
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

TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'
RAW: str = '#b5b5b5'

Arr = NDArray[np.float64]


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


def _save(fig: Figure, root: pathlib.Path, name: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    fig.savefig(root / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{root.name}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# page 1: sensor streams
# --------------------------------------------------------------------------

FT_RATE: float = 500.0                  # force-torque readings per second
FT_DT: float = 1.0 / FT_RATE
FT_NOISE: float = 0.25                  # N, standard deviation of the sensor noise


def tool_x(t: Arr | float) -> Arr | float:
    """The tool's position along one axis, in mm, during a smooth 100 mm move.

    The move runs from t = 0 to t = 0.6 s with a cosine speed profile, so the
    speed is zero at both ends and largest in the middle.
    """
    t = np.clip(t, 0.0, 0.6)
    return 50.0 * (1.0 - np.cos(np.pi * t / 0.6))


def tool_speed(t: float) -> float:
    """The tool's speed in mm/s, the derivative of tool_x."""
    return 50.0 * np.pi / 0.6 * np.sin(np.pi * t / 0.6)


def pairing_numbers() -> dict[str, float]:
    """The joint stream at 100 Hz, the camera at 30 Hz, and three ways to get a pose."""
    joint_t = np.arange(0.0, 0.6001, 0.01)
    joint_x = tool_x(joint_t)
    stamp = 0.2833                                  # the picture's own time stamp
    latency = 0.045                                 # it arrives 45 ms later
    arrival = stamp + latency
    true = float(tool_x(stamp))
    nearest_i = int(np.argmin(np.abs(joint_t - stamp)))
    nearest = float(joint_x[nearest_i])
    interp = float(np.interp(stamp, joint_t, joint_x))
    at_arrival = float(np.interp(arrival, joint_t, joint_x))
    offset = 0.012                                  # a camera clock 12 ms ahead
    with_offset = float(np.interp(stamp - offset, joint_t, joint_x))
    return {'stamp': stamp, 'arrival': arrival, 'latency': latency, 'true': true,
            'nearest_t': float(joint_t[nearest_i]), 'nearest': nearest, 'interp': interp,
            'at_arrival': at_arrival, 'speed': tool_speed(stamp), 'offset': offset,
            'with_offset': with_offset}


def pairing_picture_and_pose() -> None:
    n = pairing_numbers()
    fig, (top, bot) = plt.subplots(2, 1, figsize=(10.5, 7.2),
                                   gridspec_kw={'height_ratios': [1.0, 2.2], 'hspace': 0.55})
    # top: the two streams on one time line
    t0, t1 = 0.20, 0.36
    jt = np.arange(0.0, 0.6001, 0.01)
    jt = jt[(jt >= t0 - 1e-9) & (jt <= t1 + 1e-9)]
    ct = np.array([0.2167, 0.2500, 0.2833, 0.3167, 0.3500])
    top.set_xlim(t0 - 0.005, t1 + 0.005)
    top.set_ylim(-0.6, 2.0)
    top.set_yticks([0, 1])
    top.set_yticklabels(['joint angles\n100 per second', 'wrist camera\n30 per second'],
                        fontsize=9, color=INK)
    for side in ('top', 'right', 'left'):
        top.spines[side].set_visible(False)
    top.spines['bottom'].set_color(MUTED)
    top.tick_params(colors=MUTED, labelsize=9)
    top.set_xlabel('time stamp (s)', color=INK, fontsize=10)
    top.vlines(jt, -0.25, 0.25, color=LINK, lw=1.6)
    top.vlines(ct, 0.75, 1.25, color=WRIST, lw=2.4)
    s = n['stamp']
    top.vlines([s], 0.75, 1.25, color=GRIP, lw=3.0)
    top.plot([s, s], [0.72, 0.28], color=GRIP, lw=1.2, ls='--')
    top.annotate('', xy=(n['arrival'], 1.55), xytext=(s, 1.55),
                 arrowprops={'arrowstyle': '-|>', 'color': MUTED, 'lw': 1.2})
    _label(top, (s + n['arrival']) / 2, 1.8, 'picture arrives 45 ms later', size=9,
           color=MUTED)
    _panel_title(top, 'Two streams, two rates: the picture falls between two joint readings')

    # bottom: the tool's position and the three answers
    t = np.linspace(0.18, 0.38, 400)
    _plot_axes(bot, 'time (s)', 'tool position (mm)')
    bot.plot(t, tool_x(t), color=MUTED, lw=1.6, label='where the tool really was')
    bot.plot(jt, tool_x(jt), 'o', color=LINK, ms=5, label='joint readings (100 per second)')
    bot.axvline(s, color=GRIP, lw=1.0, ls='--')
    bot.axvline(n['arrival'], color=MUTED, lw=1.0, ls=':')
    bot.plot([s], [n['interp']], 'o', color=SLIDE, ms=11, mfc='none', mew=2.4,
             label=f'interpolated at the stamp: {n["interp"]:.1f} mm')
    bot.plot([n['nearest_t']], [n['nearest']], 's', color=JOINT, ms=10, mfc='none', mew=2.2,
             label=f'nearest reading: {n["nearest"]:.1f} mm')
    bot.plot([n['arrival']], [n['at_arrival']], 'D', color=GRIP, ms=10, mfc='none', mew=2.2,
             label=f'pose "now", on arrival: {n["at_arrival"]:.1f} mm')
    _label(bot, s - 0.002, 25, 'picture\ntaken', size=9, color=GRIP, ha='right')
    _label(bot, n['arrival'] + 0.002, 25, 'picture\narrives', size=9, color=MUTED, ha='left')
    bot.annotate('', xy=(n['arrival'] + 0.004, n['at_arrival']),
                 xytext=(n['arrival'] + 0.004, n['true']),
                 arrowprops={'arrowstyle': '<->', 'color': GRIP, 'lw': 1.3})
    _label(bot, n['arrival'] + 0.007, (n['at_arrival'] + n['true']) / 2,
           f'{n["at_arrival"] - n["true"]:.1f} mm wrong', size=9.5, color=GRIP, ha='left')
    bot.set_xlim(0.18, 0.38)
    bot.set_ylim(15, 95)
    bot.legend(loc='upper left', fontsize=9, frameon=False)
    _panel_title(bot, 'Reading the arm\'s pose at the picture\'s time, not when it arrives')
    _save(fig, STREAMS, 'pairing-picture-and-pose.svg')


def force_trace(seed: int = 3) -> tuple[Arr, Arr, Arr]:
    """A wrist force trace: free motion, contact that builds up, then a steady press.

    Contact starts at 0.50 s and the force rises at 20 N/s to 6 N at 0.80 s.
    Three spikes of +4 N stand for electrical glitches.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, 1.2, FT_DT)
    true = np.clip((t - 0.5) * 20.0, 0.0, 6.0)
    raw = true + rng.normal(0.0, FT_NOISE, t.size)
    for ts in (0.20, 0.35, 1.00):
        raw[int(round(ts / FT_DT))] += 4.0
    return t, true, raw


def moving_average(x: Arr, n: int) -> Arr:
    """Average of the last n samples (a causal filter, as on a robot)."""
    out = np.empty_like(x)
    c = np.cumsum(np.insert(x, 0, 0.0))
    for i in range(x.size):
        lo = max(0, i - n + 1)
        out[i] = (c[i + 1] - c[lo]) / (i + 1 - lo)
    return out


def exponential(x: Arr, alpha: float) -> Arr:
    """y = y + alpha (x - y): each new reading pulls the estimate part of the way."""
    out = np.empty_like(x)
    y = x[0]
    for i, v in enumerate(x):
        y = y + alpha * (v - y)
        out[i] = y
    return out


def running_median(x: Arr, n: int) -> Arr:
    """Median of the last n samples."""
    return np.array([np.median(x[max(0, i - n + 1):i + 1]) for i in range(x.size)])


def first_crossing(t: Arr, x: Arr, level: float, after: float = 0.4) -> float:
    idx = np.nonzero((x > level) & (t > after))[0]
    return float(t[idx[0]]) if idx.size else float('nan')


def filter_numbers() -> dict:
    t, true, raw = force_trace()
    n = 25
    alpha = 2.0 / (n + 1)         # the usual match between an exponential and an n-sample mean
    ma, ex, md = moving_average(raw, n), exponential(raw, alpha), running_median(raw, n)
    quiet = (t > 0.05) & (t < 0.48) & (np.abs(t - 0.20) > 0.06) & (np.abs(t - 0.35) > 0.06)
    steady = (t > 0.9) & (t < 1.2)
    spike_i = int(round(0.35 / FT_DT))
    out = {'t': t, 'true': true, 'raw': raw, 'ma': ma, 'ex': ex, 'md': md, 'n': n,
           'alpha': alpha}
    for k in ('raw', 'ma', 'ex', 'md'):
        x = out[k]
        out[k + '_sd'] = float(np.std(x[quiet]))
        out[k + '_spike'] = float(np.max(x[spike_i:spike_i + 30]))
        out[k + '_cross'] = first_crossing(t, x, 3.0)
        out[k + '_steady_sd'] = float(np.std(x[steady & (np.abs(t - 1.0) > 0.07)]))
    out['true_cross'] = first_crossing(t, true, 3.0)
    return out


def filters_on_force() -> None:
    f = filter_numbers()
    t = f['t']
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={'wspace': 0.25,
                                                                       'width_ratios': [1.5, 1]})
    for ax in (a, b):
        _plot_axes(ax, 'time (s)', 'force along the tool (N)')
        ax.plot(t, f['raw'], color=RAW, lw=0.8, label='raw, 500 per second')
        ax.plot(t, f['true'], color=INK, lw=1.2, ls=':', label='true force')
        ax.plot(t, f['ma'], color=LINK, lw=2.0, label=f'moving average, {f["n"]} samples')
        ax.plot(t, f['ex'], color=SLIDE, lw=2.0, label=f'exponential, alpha = {f["alpha"]:.3f}')
        ax.plot(t, f['md'], color=PURPLE, lw=2.0, label=f'median, {f["n"]} samples')
    a.set_xlim(0, 1.2)
    a.set_ylim(-1.2, 10.8)
    _label(a, 0.20, 5.3, 'spike', size=9, color=MUTED)
    _label(a, 0.35, 5.3, 'spike', size=9, color=MUTED)
    _label(a, 1.00, 10.2, 'spike', size=9, color=MUTED)
    a.legend(loc='upper left', fontsize=8.5, frameon=False)
    _panel_title(a, 'One force trace, three filters')
    b.axhline(3.0, color=GRIP, lw=1.0, ls='--')
    _label(b, 0.515, 3.25, 'a 3 N contact threshold', size=9, color=GRIP, ha='left')
    for k, c in (('true', INK), ('ma', LINK), ('ex', SLIDE), ('md', PURPLE)):
        b.plot([f[k + '_cross']], [3.0], 'o', color=c, ms=6, zorder=6)
    b.set_xlim(0.5, 0.75)
    b.set_ylim(-0.8, 6.5)
    _panel_title(b, 'Close up: every filter crosses late')
    _save(fig, STREAMS, 'filters-on-a-force-trace.svg')


def slope_numbers() -> dict:
    t, true, raw = force_trace(seed=5)
    # a clean segment with no spikes, entirely inside the rising part
    rng = np.random.default_rng(11)
    t = np.arange(0.50, 0.80, FT_DT)
    true = (t - 0.5) * 20.0
    raw = true + rng.normal(0.0, FT_NOISE, t.size)
    d1 = np.diff(raw) / FT_DT
    k = 25
    dk = (raw[k:] - raw[:-k]) / (k * FT_DT)
    ls = []
    for i in range(k - 1, raw.size):
        tt = t[i - k + 1:i + 1]
        yy = raw[i - k + 1:i + 1]
        ls.append(np.polyfit(tt, yy, 1)[0])
    ls = np.array(ls)
    return {'t': t, 'raw': raw, 'd1': d1, 'dk': dk, 'ls': ls, 'k': k,
            'd1_sd': float(np.std(d1)), 'dk_sd': float(np.std(dk)), 'ls_sd': float(np.std(ls)),
            'd1_mean': float(np.mean(d1)), 'ls_mean': float(np.mean(ls))}


def slope_from_noisy_data() -> None:
    s = slope_numbers()
    t = s['t']
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.0, 4.6), gridspec_kw={'wspace': 0.28})
    _plot_axes(a, 'time (s)', 'slope estimate (N/s)')
    a.plot(t[1:], s['d1'], color=RAW, lw=0.9, label='difference of neighbouring readings')
    a.axhline(20.0, color=INK, lw=1.4, ls=':', label='true slope, 20 N/s')
    a.set_ylim(-450, 500)
    a.legend(loc='upper right', fontsize=9, frameon=False)
    _panel_title(a, f'Neighbour differences: spread {s["d1_sd"]:.0f} N/s')
    _plot_axes(b, 'time (s)', 'slope estimate (N/s)')
    k = s['k']
    b.plot(t[k:], s['dk'], color=JOINT, lw=1.6,
           label=f'difference across {k} readings: spread {s["dk_sd"]:.1f} N/s')
    b.plot(t[k - 1:], s['ls'], color=LINK, lw=2.0,
           label=f'least-squares line over {k} readings: spread {s["ls_sd"]:.1f} N/s')
    b.axhline(20.0, color=INK, lw=1.4, ls=':', label='true slope, 20 N/s')
    b.set_ylim(0, 42)
    b.legend(loc='upper right', fontsize=9, frameon=False)
    _panel_title(b, 'Over a 50 ms window (note the scale)')
    _save(fig, STREAMS, 'slope-from-noisy-data.svg')


def hysteresis_trace(seed: int = 7) -> tuple[Arr, Arr]:
    """A force that climbs to the 10 N limit, hovers there, rises, then falls back."""
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, 2.0, FT_DT)
    knots_t = [0.0, 0.4, 1.0, 1.2, 1.5, 1.7, 2.0]
    knots_f = [0.0, 9.8, 10.0, 11.5, 11.5, 7.0, 6.5]
    true = np.interp(t, knots_t, knots_f)
    return t, true + rng.normal(0.0, 0.3, t.size)


def single_threshold(x: Arr, on: float) -> Arr:
    return (x > on).astype(float)


def with_hysteresis(x: Arr, on: float, off: float) -> Arr:
    state = False
    out = np.zeros_like(x)
    for i, v in enumerate(x):
        if not state and v > on:
            state = True
        elif state and v < off:
            state = False
        out[i] = state
    return out


def debounced(x: Arr, on: float, count: int) -> Arr:
    """Change state only after `count` readings in a row agree with the new state."""
    state = False
    run = 0
    out = np.zeros_like(x)
    for i, v in enumerate(x):
        wants = v > on
        run = run + 1 if wants != state else 0
        if run >= count:
            state = wants
            run = 0
        out[i] = state
    return out


def hysteresis_numbers() -> dict:
    t, f = hysteresis_trace()
    a = single_threshold(f, 10.0)
    h = with_hysteresis(f, 10.0, 9.0)
    d = debounced(f, 10.0, 10)
    flips = {k: int(np.sum(np.abs(np.diff(v)))) for k, v in (('single', a), ('hyst', h),
                                                               ('debounce', d))}

    def first_on(v: Arr) -> float:
        return float(t[np.nonzero(v)[0][0]])

    def last_off(v: Arr) -> float:
        on = np.nonzero(v)[0]
        return float(t[on[-1] + 1]) if on[-1] + 1 < t.size else float('nan')

    return {'t': t, 'f': f, 'single': a, 'hyst': h, 'debounce': d, 'flips': flips,
            'first_on': {k: first_on(v) for k, v in (('single', a), ('hyst', h),
                                                      ('debounce', d))},
            'last_off': {k: last_off(v) for k, v in (('single', a), ('hyst', h),
                                                      ('debounce', d))}}


def hysteresis_and_debounce() -> None:
    h = hysteresis_numbers()
    t = h['t']
    fig, axes = plt.subplots(4, 1, figsize=(10.5, 7.6), sharex=True,
                             gridspec_kw={'height_ratios': [2.4, 0.7, 0.7, 0.7], 'hspace': 0.5})
    ax = axes[0]
    _plot_axes(ax, '', 'force (N)')
    ax.plot(t, h['f'], color=RAW, lw=0.8)
    ax.axhline(10.0, color=GRIP, lw=1.3, ls='--')
    ax.axhline(9.0, color=SLIDE, lw=1.3, ls='--')
    _label(ax, 0.05, 10.55, 'limit: on above 10 N', size=9, color=GRIP, ha='left')
    _label(ax, 0.05, 8.45, 'hysteresis: off below 9 N', size=9, color=SLIDE, ha='left')
    ax.set_ylim(4, 13)
    ax.set_xlim(0, 2.0)
    _panel_title(ax, 'A force that hovers at the limit, and three ways to raise a flag')
    rows = (('single', 'one threshold', GRIP), ('hyst', 'with hysteresis', SLIDE),
            ('debounce', 'debounced, 10 readings', LINK))
    for ax, (k, name, c) in zip(axes[1:], rows):
        ax.fill_between(t, 0, h[k], step='post', color=c, alpha=0.8, lw=0)
        ax.set_ylim(-0.1, 1.25)
        ax.set_yticks([])
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(MUTED)
        ax.tick_params(colors=MUTED, labelsize=9)
        ax.set_title(f'{name}: the flag changes {h["flips"][k]} times', fontsize=10,
                     color=INK, loc='left', pad=3)
    axes[-1].set_xlabel('time (s)', color=INK, fontsize=10)
    _save(fig, STREAMS, 'hysteresis-and-debounce.svg')


# --------------------------------------------------------------------------
# page 2: safety monitoring
# --------------------------------------------------------------------------

CTRL_DT: float = 0.01          # the safety layer runs 100 times a second
POS_LO, POS_HI = -1.6, 1.6     # rad, the software limits for this joint
V_MAX: float = 2.5             # rad/s
JUMP_LIMIT: float = 0.3        # rad: a target further than this from the last one is a fault


def policy_targets() -> tuple[Arr, Arr]:
    """Joint targets from a learned policy at 10 per second, held for 10 control ticks.

    The path is smooth, except that it drifts past the upper software limit
    around 1.0 s, and one output at 2.0 s jumps 0.9 rad away from its neighbours.
    """
    tp = np.arange(0.0, 3.0, 0.1)
    q = 0.4 + 1.3 * np.sin(2 * np.pi * tp / 4.0)
    q[20] += 0.9
    t = np.arange(0.0, 3.0, CTRL_DT)
    raw = q[np.minimum((t / 0.1 + 1e-9).astype(int), q.size - 1)]
    return t, raw


def clamp_and_rate_limit(raw: Arr, q0: float) -> Arr:
    out = np.empty_like(raw)
    q = q0
    for i, target in enumerate(raw):
        target = min(max(target, POS_LO), POS_HI)
        step = np.clip(target - q, -V_MAX * CTRL_DT, V_MAX * CTRL_DT)
        q = q + step
        out[i] = q
    return out


def reject_and_hold(raw: Arr, q0: float) -> tuple[Arr, list[float]]:
    """Refuse a policy output that jumps too far from the last good one; hold and report it.

    The check runs once per policy output (every 0.1 s). A jump of up to
    JUMP_LIMIT is allowed for each policy step since the last good output.
    """
    out = np.empty_like(raw)
    q = q0
    last_good = raw[0]
    steps_since = 0
    held = raw[0]
    faults: list[float] = []
    per_output = int(round(0.1 / CTRL_DT))
    for i, target in enumerate(raw):
        if i % per_output == 0:
            steps_since += 1
            if abs(target - last_good) > JUMP_LIMIT * steps_since:
                faults.append(round(i * CTRL_DT, 3))
            else:
                last_good = target
                steps_since = 0
            held = last_good
        target = min(max(held, POS_LO), POS_HI)
        step = np.clip(target - q, -V_MAX * CTRL_DT, V_MAX * CTRL_DT)
        q = q + step
        out[i] = q
    return out, faults


def limits_numbers() -> dict:
    t, raw = policy_targets()
    lim = clamp_and_rate_limit(raw, raw[0])
    rej, faults = reject_and_hold(raw, raw[0])
    after = (t >= 2.0) & (t < 2.4)
    return {'t': t, 'raw': raw, 'lim': lim, 'rej': rej, 'faults': faults,
            'raw_max': float(raw.max()), 'lim_max': float(lim.max()),
            'raw_step': float(np.max(np.abs(np.diff(raw)))),
            'lim_step': float(np.max(np.abs(np.diff(lim)))),
            'jump_moved': float(np.max(lim[after] - rej[after]))}


def limits_and_clamping() -> None:
    n = limits_numbers()
    t = n['t']
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    _plot_axes(ax, 'time (s)', 'elbow joint angle (rad)')
    ax.axhspan(POS_HI, 2.4, color=GRIP, alpha=0.08, lw=0)
    ax.axhline(POS_HI, color=GRIP, lw=1.2, ls='--')
    _label(ax, 0.05, POS_HI + 0.1, 'software position limit, 1.6 rad', size=9, color=GRIP,
           ha='left')
    ax.step(t, n['raw'], where='post', color=RAW, lw=2.2, label='targets from the policy')
    ax.plot(t, n['lim'], color=JOINT, lw=2.0,
            label='clamped to the limit, speed limited to 2.5 rad/s')
    ax.plot(t, n['rej'], color=LINK, lw=2.0, ls='--',
            label='same, and a jump over 0.3 rad per output refused')
    _label(ax, 2.16, 1.5, 'one bad output:\n+0.9 rad for 0.1 s', size=9, color=MUTED,
           ha='left')
    _label(ax, 1.0, 2.15, 'policy asks for\nmore than the limit', size=9, color=MUTED)
    ax.set_xlim(0, 3.0)
    ax.set_ylim(-1.1, 2.4)
    ax.legend(loc='lower left', fontsize=9, frameon=False)
    _panel_title(ax, 'Checking a learned policy\'s joint targets before they reach the arm')
    _save(fig, SAFETY, 'limits-and-clamping.svg')


# the workspace, seen from above, in mm; the arm's base is at the origin
BOX = (150.0, 700.0, -450.0, 450.0)            # x_lo, x_hi, y_lo, y_hi
KEEP_OUT = (380.0, 560.0, 180.0, 320.0)        # a camera stand on the table
TOOL_R: float = 40.0                           # mm, a sphere around the gripper


def _dist_to_box(p: Arr, box: tuple[float, float, float, float]) -> float:
    x_lo, x_hi, y_lo, y_hi = box
    dx = max(x_lo - p[0], 0.0, p[0] - x_hi)
    dy = max(y_lo - p[1], 0.0, p[1] - y_hi)
    return float(np.hypot(dx, dy))


def _inside(p: Arr, box: tuple[float, float, float, float], margin: float) -> bool:
    x_lo, x_hi, y_lo, y_hi = box
    return (x_lo + margin <= p[0] <= x_hi - margin) and (y_lo + margin <= p[1] <= y_hi - margin)


def workspace_numbers() -> dict:
    a = np.array([300.0, -200.0])
    b = np.array([600.0, 380.0])
    length = float(np.linalg.norm(b - a))
    steps = int(length // 5.0) + 1
    stop = None
    reason = ''
    for i in range(steps + 1):
        p = a + (b - a) * min(i * 5.0 / length, 1.0)
        if _dist_to_box(p, KEEP_OUT) < TOOL_R:
            reason = 'keep-out'
            break
        if not _inside(p, BOX, TOOL_R):
            reason = 'box'
            break
        stop = p
    travelled = float(np.linalg.norm(stop - a))
    c = np.array([260.0, 530.0])       # a second target, outside the allowed box
    return {'a': a, 'b': b, 'stop': stop, 'reason': reason, 'travelled': travelled,
            'length': length, 'c': c, 'c_inside': _inside(c, BOX, TOOL_R),
            'b_inside': _inside(b, BOX, TOOL_R)}


def workspace_and_keep_out() -> None:
    w = workspace_numbers()
    fig, ax = plt.subplots(figsize=(8.6, 8.2))
    ax.set_aspect('equal')
    ax.add_patch(Rectangle((0, -600), 820, 1200, color=TABLE, zorder=0))
    x_lo, x_hi, y_lo, y_hi = BOX
    ax.add_patch(Rectangle((x_lo, y_lo), x_hi - x_lo, y_hi - y_lo, fill=False,
                           ec=SLIDE, lw=2.2, zorder=2))
    ax.add_patch(Rectangle((x_lo + TOOL_R, y_lo + TOOL_R), x_hi - x_lo - 2 * TOOL_R,
                           y_hi - y_lo - 2 * TOOL_R, fill=False, ec=SLIDE, lw=1.0, ls='--',
                           zorder=2))
    k_lo, k_hi, ky_lo, ky_hi = KEEP_OUT
    ax.add_patch(Rectangle((k_lo, ky_lo), k_hi - k_lo, ky_hi - ky_lo, color=GRIP, alpha=0.35,
                           lw=0, zorder=2))
    ax.add_patch(Rectangle((k_lo - TOOL_R, ky_lo - TOOL_R), k_hi - k_lo + 2 * TOOL_R,
                           ky_hi - ky_lo + 2 * TOOL_R, fill=False, ec=GRIP, lw=1.0, ls='--',
                           zorder=2))
    ax.add_patch(Circle((0, 0), 60, color=LINK, zorder=3))
    _label(ax, 0, -95, 'arm base', size=9.5)
    a, b, s = w['a'], w['b'], w['stop']
    ax.plot([a[0], b[0]], [a[1], b[1]], color=MUTED, lw=1.4, ls=':', zorder=4)
    ax.plot([a[0], s[0]], [a[1], s[1]], color=LINK, lw=2.6, zorder=5)
    ax.plot(*a, 'o', color=LINK, ms=8, zorder=6)
    ax.plot(*b, 'x', color=GRIP, ms=12, mew=2.6, zorder=6)
    ax.add_patch(Circle(tuple(s), TOOL_R, fill=False, ec=LINK, lw=1.8, zorder=6))
    _label(ax, a[0] + 15, a[1] - 35, 'start', size=9.5, ha='left')
    _label(ax, b[0] + 18, b[1] + 38, 'commanded goal', size=9.5, color=GRIP, ha='left')
    _label(ax, s[0] - 55, s[1] + 10, f'stopped here\nafter {w["travelled"]:.0f} mm', size=9.5,
           color=LINK, ha='right')
    _label(ax, (k_lo + k_hi) / 2, (ky_lo + ky_hi) / 2, 'keep-out:\ncamera stand', size=9.5,
           color=GRIP)
    _label(ax, x_hi - 10, y_lo + 18, 'allowed box', size=9.5, color=SLIDE, ha='right')
    _label(ax, 410, -560, 'dashed lines: the limits moved in by the\n40 mm radius of the gripper',
           size=9, color=MUTED)
    c = w['c']
    ax.plot(*c, 'x', color=GRIP, ms=12, mew=2.6, zorder=6)
    _label(ax, c[0] - 18, c[1] + 42, 'a goal outside the box:\nrefused before moving', size=9,
           color=GRIP, ha='left')
    ax.set_xlim(-120, 840)
    ax.set_ylim(-620, 620)
    ax.set_xlabel('x, away from the base (mm)', color=INK, fontsize=10)
    ax.set_ylabel('y, across the table (mm)', color=INK, fontsize=10)
    ax.tick_params(colors=MUTED, labelsize=9)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    _panel_title(ax, 'A workspace box and a keep-out zone, seen from above')
    _save(fig, SAFETY, 'workspace-and-keep-out.svg')


def watchdog_run(timeout: float | None, decel: float = 2.0) -> dict[str, Arr]:
    """Velocity commands at 100 per second stop arriving at 1.0 s."""
    dt = 0.001
    t = np.arange(0.0, 2.0, dt)
    v_cmd = 200.0      # mm/s
    last_msg = 0.0
    v = 0.0
    x = 0.0
    vs, xs = [], []
    for ti in t:
        if ti < 1.0 and abs(ti / 0.01 - round(ti / 0.01)) < 1e-6:
            last_msg = ti
        target = v_cmd
        if timeout is not None and ti - last_msg > timeout:
            target = 0.0
        if target < v:
            v = max(target, v - decel * 1000.0 * dt)
        else:
            v = min(target, v + decel * 1000.0 * dt)
        x += v * dt
        vs.append(v)
        xs.append(x)
    return {'t': t, 'v': np.array(vs), 'x': np.array(xs)}


def watchdog_numbers() -> dict:
    no = watchdog_run(None)
    yes = watchdog_run(0.1)
    i1 = int(round(1.0 / 0.001))
    stop_i = int(np.nonzero((yes['t'] > 1.0) & (yes['v'] <= 1e-9))[0][0])
    return {'no': no, 'yes': yes,
            'no_after': float(no['x'][-1] - no['x'][i1]),
            'yes_after': float(yes['x'][-1] - yes['x'][i1]),
            'stop_t': float(yes['t'][stop_i])}


def watchdog() -> None:
    w = watchdog_numbers()
    fig, (top, bot) = plt.subplots(2, 1, figsize=(10.5, 6.6), sharex=True,
                                   gridspec_kw={'height_ratios': [0.55, 2.0], 'hspace': 0.35})
    msgs = np.arange(0.0, 1.0, 0.01)
    top.vlines(msgs, 0, 1, color=LINK, lw=0.8)
    top.set_ylim(0, 1.6)
    top.set_yticks([])
    for side in ('top', 'right', 'left'):
        top.spines[side].set_visible(False)
    top.spines['bottom'].set_color(MUTED)
    top.tick_params(colors=MUTED, labelsize=9)
    _label(top, 1.03, 0.5, 'the sender freezes: no more commands', size=9.5, color=GRIP,
           ha='left')
    _panel_title(top, 'Speed commands, 100 per second')
    _plot_axes(bot, 'time (s)', 'tool speed (mm/s)')
    bot.plot(w['no']['t'], w['no']['v'], color=GRIP, lw=2.2,
             label=f'no watchdog: keeps going, {w["no_after"]:.0f} mm more by 2 s')
    bot.plot(w['yes']['t'], w['yes']['v'], color=SLIDE, lw=2.2, ls='--',
             label=f'watchdog, 0.1 s timeout: stops at {w["stop_t"]:.2f} s, '
                   f'{w["yes_after"]:.0f} mm more')
    bot.axvline(1.0, color=MUTED, lw=1.0, ls=':')
    bot.axvspan(1.0, 1.1, color=JOINT, alpha=0.15, lw=0)
    _label(bot, 1.05, 228, 'timeout', size=9, color=MUTED)
    _label(bot, 1.12, 40, 'braking at\n2 m/s²', size=9, color=SLIDE, ha='left')
    bot.set_ylim(0, 260)
    bot.set_xlim(0, 2.0)
    bot.legend(loc='upper left', fontsize=9, frameon=False)
    _save(fig, SAFETY, 'watchdog.svg')


# speed and separation: illustrative numbers, not taken from any standard
V_HUMAN: float = 1.6       # m/s, a brisk walk (assumed)
T_REACT: float = 0.1       # s, sensor plus software reaction (assumed)
ARM_DECEL: float = 2.0     # m/s^2, how hard the arm can brake (assumed)
MARGIN: float = 0.1        # m, allowance for sensor error and body size (assumed)
V_ARM_MAX: float = 0.5     # m/s


def needed_gap(v: float) -> float:
    """The separation needed at arm speed v so the arm can stop before contact."""
    t_stop = v / ARM_DECEL
    return (V_HUMAN * (T_REACT + t_stop) + v * T_REACT + v * v / (2 * ARM_DECEL) + MARGIN)


def allowed_speed(gap: float) -> float:
    vs = np.linspace(0.0, V_ARM_MAX, 5001)
    ok = vs[np.array([needed_gap(v) <= gap for v in vs])]
    return float(ok.max()) if ok.size else 0.0


def ssm_numbers() -> dict:
    d = np.linspace(0.0, 1.6, 321)
    v = np.array([allowed_speed(x) for x in d])
    dt = 0.01
    t = np.arange(0.0, 6.0, dt)
    person = np.interp(t, [0.0, 1.0, 2.25, 3.5, 4.0, 5.2, 6.0],
                       [2.6, 2.6, 0.25, 0.25, 0.25, 2.5, 2.5])
    v_arm = np.array([allowed_speed(g) for g in person])
    return {'d': d, 'v': v, 'gap0': needed_gap(0.0), 'gap_full': needed_gap(V_ARM_MAX),
            't': t, 'person': person, 'v_arm': v_arm,
            'first_slow': float(t[np.nonzero(v_arm < V_ARM_MAX - 1e-9)[0][0]]),
            'first_stop': float(t[np.nonzero(v_arm <= 1e-9)[0][0]])}


def speed_and_separation() -> None:
    s = ssm_numbers()
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={'wspace': 0.3})
    _plot_axes(a, 'distance between person and arm (m)', 'allowed arm speed (m/s)')
    a.plot(s['d'], s['v'], color=LINK, lw=2.4)
    a.axvspan(0, s['gap0'], color=GRIP, alpha=0.15, lw=0)
    a.axvspan(s['gap_full'], 1.6, color=SLIDE, alpha=0.12, lw=0)
    _label(a, s['gap0'] / 2, 0.3, 'stop', size=9.5, color=GRIP)
    _label(a, (s['gap0'] + s['gap_full']) / 2, 0.56, 'slow down', size=9.5, color=INK)
    _label(a, (s['gap_full'] + 1.6) / 2, 0.3, 'full\nspeed', size=9.5, color=SLIDE)
    _label(a, s['gap0'] + 0.02, -0.035, f'{s["gap0"]:.2f} m', size=9, color=GRIP, ha='left')
    _label(a, s['gap_full'] + 0.02, -0.035, f'{s["gap_full"]:.2f} m', size=9, color=SLIDE,
           ha='left')
    a.set_xlim(0, 1.6)
    a.set_ylim(-0.07, 0.62)
    _panel_title(a, 'The rule: speed allowed at each distance')
    _plot_axes(b, 'time (s)', 'distance (m)')
    b.plot(s['t'], s['person'], color=MUTED, lw=2.0, label='distance to the person')
    b.set_ylim(0, 2.9)
    b2 = b.twinx()
    b2.plot(s['t'], s['v_arm'], color=LINK, lw=2.2, label='arm speed')
    b2.set_ylim(0, 0.58)
    b2.set_ylabel('arm speed (m/s)', color=LINK, fontsize=10)
    b2.tick_params(colors=LINK, labelsize=9)
    for side in ('top',):
        b2.spines[side].set_visible(False)
    _label(b, 3.2, 0.75, 'person stands close:\narm stopped', size=9, color=GRIP)
    _label(b, 0.5, 2.3, 'person\napproaches', size=9, color=MUTED)
    _label(b, 5.4, 2.0, 'walks\naway', size=9, color=MUTED)
    lines = b.get_lines() + b2.get_lines()
    b.legend(lines, [ln.get_label() for ln in lines], loc='upper center', fontsize=9,
             frameon=False, bbox_to_anchor=(0.5, 1.0))
    b.set_xlim(0, 6.0)
    _panel_title(b, 'The rule running as a person walks up and away')
    _save(fig, SAFETY, 'speed-and-separation.svg')


# --------------------------------------------------------------------------
# the numbers the pages quote
# --------------------------------------------------------------------------

def print_numbers() -> None:
    p = pairing_numbers()
    print(f"pairing: stamp {p['stamp']}, true {p['true']:.2f} mm, interp {p['interp']:.2f}, "
          f"nearest {p['nearest']:.2f} (t {p['nearest_t']}), at arrival {p['at_arrival']:.2f}, "
          f"speed {p['speed']:.1f} mm/s, 12 ms clock offset gives {p['with_offset']:.2f}")
    f = filter_numbers()
    for k in ('raw', 'ma', 'ex', 'md'):
        print(f"filter {k}: quiet sd {f[k + '_sd']:.3f}, steady sd {f[k + '_steady_sd']:.3f}, "
              f"spike peak {f[k + '_spike']:.2f}, 3 N crossing {f[k + '_cross']:.3f}")
    print(f"true crossing {f['true_cross']:.3f}; alpha {f['alpha']:.4f}")
    s = slope_numbers()
    print(f"slope: neighbour sd {s['d1_sd']:.1f} mean {s['d1_mean']:.1f}; across {s['k']} "
          f"sd {s['dk_sd']:.2f}; least squares sd {s['ls_sd']:.2f} mean {s['ls_mean']:.2f}")
    h = hysteresis_numbers()
    print(f"hysteresis flips {h['flips']}; first on {h['first_on']}; last off {h['last_off']}")
    n = limits_numbers()
    print(f"limits: raw max {n['raw_max']:.3f}, limited max {n['lim_max']:.3f}, raw biggest "
          f"step {n['raw_step']:.3f}, limited step {n['lim_step']:.3f}, jump moved joint "
          f"{n['jump_moved']:.3f} rad further than the refusing version, faults at "
          f"{n['faults']}")
    w = workspace_numbers()
    print(f"workspace: path length {w['length']:.1f}, stopped at {np.round(w['stop'], 1)} "
          f"after {w['travelled']:.1f} mm because {w['reason']}; goal b inside "
          f"{w['b_inside']}; goal c inside {w['c_inside']}")
    wd = watchdog_numbers()
    print(f"watchdog: without {wd['no_after']:.1f} mm after 1 s; with {wd['yes_after']:.1f} mm,"
          f" stopped at {wd['stop_t']:.3f} s")
    ss = ssm_numbers()
    print(f"ssm: gap for stop {ss['gap0']:.3f} m, gap for full speed {ss['gap_full']:.3f} m; "
          f"allowed at 0.6 m {allowed_speed(0.6):.3f}; first slow {ss['first_slow']:.2f} s, "
          f"first stop {ss['first_stop']:.2f} s")
    for v in (0.25, 1.0):
        print(f"kinetic energy of 2 kg at {v} m/s: {0.5 * 2.0 * v * v:.4f} J")


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    pairing_picture_and_pose()
    filters_on_force()
    slope_from_noisy_data()
    hysteresis_and_debounce()
    limits_and_clamping()
    workspace_and_keep_out()
    watchdog()
    speed_and_separation()
    print_numbers()
    print(f'wrote the diagrams under {STREAMS} and {SAFETY}')


if __name__ == '__main__':
    main()
