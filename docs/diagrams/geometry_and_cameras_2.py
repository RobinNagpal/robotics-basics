"""Generate the diagrams for the two newer pages of
docs/06_programming-techniques/02_geometry-and-cameras/.

This covers 02_most-used/04_pose-from-points and 03_also-used/01_multi-view-geometry.
Each document's pictures go to a folder named after it, under
docs/images/geometry-and-cameras/.

Run with:  pixi run python ../docs/diagrams/geometry_and_cameras_2.py
Add --png <dir> to also write PNG copies for checking.
Add --numbers to print the numbers the two pages quote, without drawing.

It shares the palette, the drawing helpers and Book 2's camera with
geometry_and_cameras.py: 320 x 240 pixels, fx = fy = 277.1, cx = 160, cy = 120.
Every pose, triangulation, epipolar line and disparity drawn here is computed
with NumPy when the picture is drawn. The pose solver is written out below
(a direct linear first guess, then Gauss-Newton with a damping term, which is the
Levenberg-Marquardt method), so no OpenCV is needed.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geometry_and_cameras as gc  # noqa: E402
from geometry_and_cameras import (  # noqa: E402
    CX, CY, FX, GRID, GRIP, H_PX, INK, JOINT, LINK, LINK_PALE, MUTED, PURPLE, SLIDE, TABLE,
    W_PX, _arrow, _axes, _boxed, _camera_body, _label, _save, rot_x, rot_y, rot_z,
)

K: np.ndarray = np.array([[FX, 0.0, CX], [0.0, FX, CY], [0.0, 0.0, 1.0]])


# --------------------------------------------------------------------------
# the arithmetic: rotations, projection, and a small PnP solver
# --------------------------------------------------------------------------

def rodrigues(r: np.ndarray) -> np.ndarray:
    """A rotation vector (axis times angle in radians) to a 3 x 3 rotation matrix."""
    angle = float(np.linalg.norm(r))
    if angle < 1e-12:
        return np.eye(3)
    k = r / angle
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(angle) * kx + (1 - math.cos(angle)) * kx @ kx


def rot_to_vec(r: np.ndarray) -> np.ndarray:
    """A rotation matrix back to a rotation vector."""
    c = max(-1.0, min(1.0, (np.trace(r) - 1) / 2))
    angle = math.acos(c)
    if angle < 1e-12:
        return np.zeros(3)
    w = np.array([r[2, 1] - r[1, 2], r[0, 2] - r[2, 0], r[1, 0] - r[0, 1]])
    return w / (2 * math.sin(angle)) * angle


def angle_between(r1: np.ndarray, r2: np.ndarray) -> float:
    """The angle, in degrees, of the turn that takes r1 to r2."""
    c = max(-1.0, min(1.0, (np.trace(r1.T @ r2) - 1) / 2))
    return math.degrees(math.acos(c))


def project_all(pts: np.ndarray, r: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Object points (N x 3) placed at pose (r, t) in the camera's frame, to pixels (N x 2)."""
    pc = pts @ r.T + t
    return np.column_stack([FX * pc[:, 0] / pc[:, 2] + CX, FX * pc[:, 1] / pc[:, 2] + CY])


def rms(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))))


def normalised(px: np.ndarray) -> np.ndarray:
    """Pixels to ray directions with z = 1 (the lens numbers removed)."""
    return np.column_stack([(px[:, 0] - CX) / FX, (px[:, 1] - CY) / FX])


def nearest_rotation(m: np.ndarray) -> np.ndarray:
    u, _s, vt = np.linalg.svd(m)
    r = u @ vt
    if np.linalg.det(r) < 0:
        r = u @ np.diag([1, 1, -1]) @ vt
    return r


def pnp_dlt(pts: np.ndarray, px: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The direct linear first guess: solve for the 3 x 4 matrix [R | t] as 12 unknowns.

    It needs six or more points that are not all on one plane.
    """
    xy = normalised(px)
    rows = []
    for (x, y, z), (u, v) in zip(pts, xy):
        rows.append([x, y, z, 1, 0, 0, 0, 0, -u * x, -u * y, -u * z, -u])
        rows.append([0, 0, 0, 0, x, y, z, 1, -v * x, -v * y, -v * z, -v])
    _u, _s, vt = np.linalg.svd(np.array(rows))
    p = vt[-1].reshape(3, 4)
    scale = np.cbrt(np.linalg.det(p[:, :3]))
    p = p / scale
    return nearest_rotation(p[:, :3]), p[:, 3]


def pnp_planar(pts: np.ndarray, px: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The first guess for a flat target (all z = 0): fit the homography, then split it."""
    xy = normalised(px)
    rows = []
    for (x, y, _z), (u, v) in zip(pts, xy):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _u, _s, vt = np.linalg.svd(np.array(rows))
    h = vt[-1].reshape(3, 3)
    h = h / np.linalg.norm(h[:, 0])
    if h[2, 2] < 0:
        h = -h
    r = nearest_rotation(np.column_stack([h[:, 0], h[:, 1], np.cross(h[:, 0], h[:, 1])]))
    return r, h[:, 2]


def residuals(params: np.ndarray, pts: np.ndarray, px: np.ndarray) -> np.ndarray:
    return (project_all(pts, rodrigues(params[:3]), params[3:]) - px).ravel()


def refine(pts: np.ndarray, px: np.ndarray, r: np.ndarray, t: np.ndarray,
           iters: int = 30) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Levenberg-Marquardt on the six pose numbers. Returns the pose and the RMS after each step."""
    p = np.concatenate([rot_to_vec(r), t])
    lam = 1e-3
    history = [float(np.sqrt(np.mean(residuals(p, pts, px).reshape(-1, 2) ** 2) * 2))]
    for _ in range(iters):
        e = residuals(p, pts, px)
        jac = np.empty((e.size, 6))
        for i in range(6):
            d = np.zeros(6)
            d[i] = 1e-7
            jac[:, i] = (residuals(p + d, pts, px) - e) / 1e-7
        a = jac.T @ jac
        step = np.linalg.solve(a + lam * np.diag(np.diag(a)), -jac.T @ e)
        e_new = residuals(p + step, pts, px)
        if e_new @ e_new < e @ e:
            p = p + step
            lam *= 0.3
        else:
            lam *= 10
        history.append(float(np.sqrt(np.mean(residuals(p, pts, px).reshape(-1, 2) ** 2) * 2)))
        if np.linalg.norm(step) < 1e-12:
            break
    return rodrigues(p[:3]), p[3:], history


# ---- the scene for the pose page: Book 2's 6 cm red cube, seen by a tilted camera

def tilted_camera() -> tuple[np.ndarray, np.ndarray]:
    """The same tilted camera as the pinhole page: 0.40 m up, 0.20 m back, 60 degrees down.

    Returns the camera's rotation and position in the table's frame.
    """
    return gc.tilted_camera()


CUBE: float = 0.06
# the six corners the tilted camera sees: the top four, and the two bottom corners of the near face
CUBE_POINTS: np.ndarray = np.array([
    [-0.03, -0.03, 0.06], [0.03, -0.03, 0.06], [0.03, 0.03, 0.06], [-0.03, 0.03, 0.06],
    [-0.03, -0.03, 0.0], [0.03, -0.03, 0.0],
])
CUBE_YAW_DEG: float = 20.0
CUBE_CENTRE: np.ndarray = np.array([0.064, 0.041, 0.0])


def cube_truth() -> tuple[np.ndarray, np.ndarray]:
    """The cube's true pose in the camera's frame: T_camera_cube = inv(T_table_camera) T_table_cube."""
    r_cam, c_cam = tilted_camera()
    r_obj = rot_z(math.radians(CUBE_YAW_DEG))
    r = r_cam.T @ r_obj
    t = r_cam.T @ (CUBE_CENTRE - c_cam)
    return r, t


def cube_run(noise: float = 0.3, seed: int = 4) -> dict:
    """PnP on the cube's six corners: first guess, then refinement."""
    rng = np.random.default_rng(seed)
    r_true, t_true = cube_truth()
    px_true = project_all(CUBE_POINTS, r_true, t_true)
    px = px_true + rng.normal(0, noise, px_true.shape)
    # a deliberately rough starting guess: the cube in the middle of the table, not turned
    r_cam, c_cam = tilted_camera()
    r0 = r_cam.T
    t0 = r_cam.T @ (np.zeros(3) - c_cam)
    r1, t1, hist = refine(CUBE_POINTS, px, r0, t0)
    r_dlt, t_dlt = pnp_dlt(CUBE_POINTS, px)
    return {
        'px': px, 'px_true': px_true, 'r_true': r_true, 't_true': t_true,
        'r0': r0, 't0': t0, 'r1': r1, 't1': t1, 'history': hist,
        'r_dlt': r_dlt, 't_dlt': t_dlt,
        'pos_err_mm': float(np.linalg.norm(t1 - t_true) * 1000),
        'rot_err_deg': angle_between(r1, r_true),
        'start_rms': rms(project_all(CUBE_POINTS, r0, t0), px),
        'final_rms': rms(project_all(CUBE_POINTS, r1, t1), px),
        'dlt_rms': rms(project_all(CUBE_POINTS, r_dlt, t_dlt), px),
        'dlt_pos_err_mm': float(np.linalg.norm(t_dlt - t_true) * 1000),
    }


# ---- PnP inside RANSAC: a printed box with 40 matched features, 12 of them wrong

BOX_SIZE: np.ndarray = np.array([0.12, 0.08, 0.10])


def box_features(rng: np.random.Generator, n: int = 40) -> np.ndarray:
    """Points on the top face and on the near face (y = -0.04) of a box standing on the table."""
    sx, sy, sz = BOX_SIZE
    pts = []
    for i in range(n):
        if i % 2 == 0:
            pts.append([rng.uniform(-sx / 2, sx / 2), rng.uniform(-sy / 2, sy / 2), sz])
        else:
            pts.append([rng.uniform(-sx / 2, sx / 2), -sy / 2, rng.uniform(0.0, sz)])
    return np.array(pts)


def box_truth() -> tuple[np.ndarray, np.ndarray]:
    r_cam, c_cam = tilted_camera()
    r_obj = rot_z(math.radians(-15))
    return r_cam.T @ r_obj, r_cam.T @ (np.array([0.02, 0.06, 0.0]) - c_cam)


def ransac_run(n: int = 40, n_bad: int = 12, noise: float = 0.5, limit: float = 3.0,
               tries: int = 200, seed: int = 12) -> dict:
    rng = np.random.default_rng(seed)
    pts = box_features(rng, n)
    r_true, t_true = box_truth()
    px_true = project_all(pts, r_true, t_true)
    px = px_true + rng.normal(0, noise, px_true.shape)
    bad = rng.choice(n, n_bad, replace=False)
    px[bad] = np.column_stack([rng.uniform(20, W_PX - 20, n_bad), rng.uniform(20, H_PX - 20, n_bad)])
    is_bad = np.zeros(n, bool)
    is_bad[bad] = True

    # plain least squares on every match
    r_ls, t_ls = pnp_dlt(pts, px)
    r_ls, t_ls, _ = refine(pts, px, r_ls, t_ls)

    # RANSAC: six matches per try (the smallest set the direct linear guess can use)
    best = None
    for _ in range(tries):
        pick = rng.choice(n, 6, replace=False)
        try:
            r, t = pnp_dlt(pts[pick], px[pick])
        except np.linalg.LinAlgError:
            continue
        if t[2] <= 0:
            continue
        err = np.linalg.norm(project_all(pts, r, t) - px, axis=1)
        inl = err < limit
        if best is None or inl.sum() > best[0].sum():
            best = (inl, r, t)
    inl, r, t = best
    r_r, t_r, _ = refine(pts[inl], px[inl], r, t)
    err = np.linalg.norm(project_all(pts, r_r, t_r) - px, axis=1)
    inl = err < limit
    r_r, t_r, _ = refine(pts[inl], px[inl], r_r, t_r)
    return {
        'pts': pts, 'px': px, 'is_bad': is_bad, 'r_true': r_true, 't_true': t_true,
        'r_ls': r_ls, 't_ls': t_ls, 'r_r': r_r, 't_r': t_r, 'inliers': inl,
        'ls_pos_mm': float(np.linalg.norm(t_ls - t_true) * 1000),
        'ls_rot_deg': angle_between(r_ls, r_true),
        'r_pos_mm': float(np.linalg.norm(t_r - t_true) * 1000),
        'r_rot_deg': angle_between(r_r, r_true),
        'n_inliers': int(inl.sum()),
        'caught': int((~inl & is_bad).sum()),
        'wrongly_dropped': int((~inl & ~is_bad).sum()),
    }


# ---- a flat square marker, and why face-on is unstable

MARKER: float = 0.040
MARKER_PTS: np.ndarray = np.array([[-0.02, -0.02, 0.0], [0.02, -0.02, 0.0],
                                   [0.02, 0.02, 0.0], [-0.02, 0.02, 0.0]])
MARKER_DIST: float = 0.34


def marker_truth(tilt_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """A marker 0.34 m in front of the camera, a little off-centre, tilted about its x axis.

    The marker's z axis points back towards the camera when tilt is 0.
    """
    r = rot_x(math.radians(180 + tilt_deg))
    return r, np.array([0.03, 0.02, MARKER_DIST])


def flipped_start(r: np.ndarray, t: np.ndarray) -> np.ndarray:
    """The other pose a flat target nearly allows: its face mirrored across the line of sight."""
    v = t / np.linalg.norm(t)
    n = r[:, 2]
    n2 = 2 * (n @ v) * v - n
    axis = np.cross(n, n2)
    s = np.linalg.norm(axis)
    if s < 1e-12:
        return r
    ang = math.atan2(s, n @ n2)
    return rodrigues(axis / s * ang) @ r


def marker_solve(px: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Solve a square marker both ways and keep the one with the smaller reprojection error.

    Returns the chosen pose, its RMS, and the RMS of the other one.
    """
    r0, t0 = pnp_planar(MARKER_PTS, px)
    ra, ta, _ = refine(MARKER_PTS, px, r0, t0, iters=40)
    rb, tb, _ = refine(MARKER_PTS, px, flipped_start(ra, ta), ta, iters=40)
    ea = rms(project_all(MARKER_PTS, ra, ta), px)
    eb = rms(project_all(MARKER_PTS, rb, tb), px)
    if ea <= eb:
        return ra, ta, ea, eb
    return rb, tb, eb, ea


def marker_study(tilts: list[float], noise: float = 0.3, runs: int = 300,
                 seed: int = 7) -> list[dict]:
    """For each tilt: how far off the marker's facing direction comes out, over many noisy runs."""
    rng = np.random.default_rng(seed)
    out = []
    for tilt in tilts:
        r_true, t_true = marker_truth(tilt)
        n_flip = flipped_start(r_true, t_true)[:, 2]
        px_true = project_all(MARKER_PTS, r_true, t_true)
        errs = []
        flips = 0
        depth = []
        for _ in range(runs):
            px = px_true + rng.normal(0, noise, px_true.shape)
            r, t, _e, _e2 = marker_solve(px)
            ang = math.degrees(math.acos(max(-1.0, min(1.0, r[:, 2] @ r_true[:, 2]))))
            errs.append(ang)
            if tilt > 0 and r[:, 2] @ n_flip > r[:, 2] @ r_true[:, 2]:
                flips += 1
            depth.append(abs(t[2] - t_true[2]) * 1000)
        errs_a = np.array(errs)
        out.append({'tilt': tilt, 'median': float(np.median(errs_a)),
                    'p90': float(np.percentile(errs_a, 90)), 'flips': flips / runs,
                    'depth_median_mm': float(np.median(depth))})
    return out


# ---- two views: triangulation, epipolar lines, stereo, parallax

# Book 2's spot on top of the red box, in the table's frame (camera 0.40 m straight above).
SPOT_WORLD: np.ndarray = np.array([0.0644, 0.0411, 0.06])
TABLE_H: float = 0.40


def down_camera(x: float, y: float = 0.0, turn_deg: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """A camera at (x, y, 0.40) looking straight down, then turned about the table's y axis.

    Returns T_camera_table as (R, t): a table point p lands at R p + t in the camera's frame.
    """
    r_tc = rot_y(math.radians(turn_deg)) @ np.diag([1.0, -1.0, -1.0])
    c = np.array([x, y, TABLE_H])
    r = r_tc.T
    return r, -r @ c


def to_px(p: np.ndarray, cam: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    r, t = cam
    q = r @ p + t
    return np.array([FX * q[0] / q[2] + CX, FX * q[1] / q[2] + CY])


def triangulate(px1: np.ndarray, px2: np.ndarray, cam1: tuple, cam2: tuple) -> np.ndarray:
    """Linear triangulation: each view gives two equations; solve for the point by SVD."""
    rows = []
    for (u, v), (r, t) in ((px1, cam1), (px2, cam2)):
        p = K @ np.column_stack([r, t])
        rows.append(u * p[2] - p[0])
        rows.append(v * p[2] - p[1])
    _u, _s, vt = np.linalg.svd(np.array(rows))
    x = vt[-1]
    return x[:3] / x[3]


def triangulation_study(baselines: list[float], noise: float = 0.5, runs: int = 2000,
                        seed: int = 3) -> list[dict]:
    """Two wrist-camera views, the second slid by the baseline and turned to face the spot."""
    rng = np.random.default_rng(seed)
    cam1 = down_camera(0.0)
    out = []
    for b in baselines:
        turn = math.degrees(math.atan2(b, TABLE_H - SPOT_WORLD[2]))
        cam2 = down_camera(b, turn_deg=turn)
        p1, p2 = to_px(SPOT_WORLD, cam1), to_px(SPOT_WORLD, cam2)
        errs = []
        for _ in range(runs):
            est = triangulate(p1 + rng.normal(0, noise, 2), p2 + rng.normal(0, noise, 2), cam1, cam2)
            errs.append(np.linalg.norm(est - SPOT_WORLD) * 1000)
        out.append({'b': b, 'turn': turn, 'median_mm': float(np.median(errs)),
                    'p90_mm': float(np.percentile(errs, 90))})
    return out


def skew(v: np.ndarray) -> np.ndarray:
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def essential(cam1: tuple, cam2: tuple) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """E for the move from camera 1 to camera 2, and F for pixels. x2' E x1 = 0."""
    r1, t1 = cam1
    r2, t2 = cam2
    r = r2 @ r1.T
    t = t2 - r @ t1
    e = skew(t) @ r
    kinv = np.linalg.inv(K)
    f = kinv.T @ e @ kinv
    return e, f, t


def epipolar_line(f: np.ndarray, px1: np.ndarray) -> np.ndarray:
    """The line a * u + b * v + c = 0 in picture 2, scaled so that (a, b) has length 1."""
    ln = f @ np.array([px1[0], px1[1], 1.0])
    return ln / np.linalg.norm(ln[:2])


def line_distance(ln: np.ndarray, px: np.ndarray) -> float:
    return float(abs(ln @ np.array([px[0], px[1], 1.0])))


STEREO_B: float = 0.050


def stereo_depth(disparity: float, b: float = STEREO_B) -> float:
    return FX * b / disparity


def parallax_height(shift_px: float, slide: float) -> float:
    """A straight-down camera 0.40 m up slides sideways: the shift gives the depth, then the height."""
    return TABLE_H - FX * slide / shift_px


def ground_plane_point(u: float, v: float) -> np.ndarray:
    """Book 2's straight-down camera: assume the pixel shows the table (depth 0.40 m)."""
    x = (u - CX) * TABLE_H / FX
    y = (v - CY) * TABLE_H / FX
    return np.array([x, -y, 0.0])


# ==========================================================================
# 04_pose-from-points
# ==========================================================================

FOLDER_PNP = 'pose-from-points'
FOLDER_MV = 'multi-view-geometry'


def _picture(ax: Axes, title: str) -> None:
    ax.set_facecolor('white')
    ax.add_patch(Rectangle((0, 0), W_PX, H_PX, facecolor='#fafafa', edgecolor=MUTED, lw=1.2, zorder=0))
    ax.set_xlim(-6, W_PX + 6)
    ax.set_ylim(H_PX + 6, -22)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.text(W_PX / 2, -12, title, ha='center', va='center', fontsize=11, weight='bold', color=INK)


CUBE_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 5), (4, 5)]


def _draw_cube(ax: Axes, px: np.ndarray, color: str, lw: float = 1.6, ls: str = '-') -> None:
    for a, b in CUBE_EDGES:
        ax.plot([px[a, 0], px[b, 0]], [px[a, 1], px[b, 1]], color=color, lw=lw, ls=ls, zorder=3)


def pnp_guess_and_fit() -> None:
    """The six known corners: where a rough guess puts them, and where the fitted pose puts them."""
    run = cube_run()
    px = run['px']
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9), facecolor='white')
    for ax, (r, t, name, rms_val, col) in zip(axes, (
            (run['r0'], run['t0'], 'the first guess', run['start_rms'], JOINT),
            (run['r1'], run['t1'], 'after 30 refinement steps', run['final_rms'], LINK))):
        _picture(ax, name)
        guess = project_all(CUBE_POINTS, r, t)
        _draw_cube(ax, guess, col, lw=2.0)
        for g, o in zip(guess, px):
            ax.plot([g[0], o[0]], [g[1], o[1]], color=GRIP, lw=1.3, zorder=4)
        ax.plot(guess[:, 0], guess[:, 1], 'o', color=col, mec=INK, ms=6, zorder=5)
        ax.plot(px[:, 0], px[:, 1], 'x', color=INK, ms=8, mew=2, zorder=6)
        _boxed(ax, W_PX / 2, H_PX - 18, f'reprojection error (RMS): {rms_val:.2f} pixels',
               edge=col, size=9.5)
    axes[0].plot([], [], 'x', color=INK, ms=8, mew=2, label='where the corners were found')
    axes[0].plot([], [], 'o', color=JOINT, mec=INK, ms=6, label='where a pose puts them')
    axes[0].plot([], [], color=GRIP, lw=1.3, label='the reprojection error')
    fig.legend(loc='lower center', ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
    err = (f'fitted pose vs the truth: {run["pos_err_mm"]:.1f} mm, {run["rot_err_deg"]:.2f}°')
    _label(axes[1], W_PX / 2, 18, err, size=9, color=MUTED)
    _save(fig, FOLDER_PNP, 'guess-then-fit.svg')


def pnp_ransac() -> None:
    """Forty matched features, twelve wrong: least squares on all of them, and RANSAC."""
    run = ransac_run()
    pts, px, bad = run['pts'], run['px'], run['is_bad']
    corners = np.array([[x, y, z] for x in (-0.06, 0.06) for y in (-0.04, 0.04) for z in (0.0, 0.10)])
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9), facecolor='white')
    for ax, (r, t, name, pos, rot, col) in zip(axes, (
            (run['r_ls'], run['t_ls'], 'least squares on all 40 matches', run['ls_pos_mm'], run['ls_rot_deg'], JOINT),
            (run['r_r'], run['t_r'], 'RANSAC, then least squares on the agreeing ones', run['r_pos_mm'],
             run['r_rot_deg'], LINK))):
        _picture(ax, name)
        truth = project_all(corners, run['r_true'], run['t_true'])
        fit = project_all(corners, r, t)
        for a, b in edges:
            ax.plot([truth[a, 0], truth[b, 0]], [truth[a, 1], truth[b, 1]], color=GRID, lw=3.0, zorder=2)
            ax.plot([fit[a, 0], fit[b, 0]], [fit[a, 1], fit[b, 1]], color=col, lw=1.6, zorder=3)
        ax.plot(px[~bad, 0], px[~bad, 1], 'o', color=SLIDE, ms=4.5, zorder=5)
        ax.plot(px[bad, 0], px[bad, 1], 'x', color=GRIP, ms=7, mew=2, zorder=5)
        _boxed(ax, W_PX / 2, H_PX - 16, f'box pose off by {pos:.1f} mm and {rot:.1f}°', edge=col, size=9.5)
    axes[0].plot([], [], 'o', color=SLIDE, ms=4.5, label='28 right matches')
    axes[0].plot([], [], 'x', color=GRIP, ms=7, mew=2, label='12 wrong matches')
    axes[0].plot([], [], color=GRID, lw=3, label='the true box')
    axes[0].plot([], [], color=JOINT, lw=1.6, label='the box at the fitted pose')
    fig.legend(loc='lower center', ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
    _save(fig, FOLDER_PNP, 'ransac-ignores-wrong-matches.svg')


def pnp_marker_two_poses() -> None:
    """A flat marker tilted +t and -t about an axis across the line of sight: nearly the same pixels."""
    tilt = 12.0
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.25, 1]})
    # left: a close side view of the marker (camera z to the right, camera -y up); the camera is off to the left
    _axes(ax1, (0.285, 0.385), (-0.045, 0.05))
    tc = np.array([0.0, 0.0, MARKER_DIST])
    for sign, col, ly in ((1, LINK, 0.027), (-1, JOINT, -0.027)):
        r = rot_x(math.radians(180 + sign * tilt))
        ends = np.array([r @ np.array([0, -0.02, 0]) + tc, r @ np.array([0, 0.02, 0]) + tc])
        ax1.plot(ends[:, 2], -ends[:, 1], color=col, lw=4, solid_capstyle='butt', zorder=5)
        for e in ends:
            k = 0.285 / e[2]
            ax1.plot([0.285, e[2]], [-e[1] * k, -e[1]], color=col, lw=0.9, ls=':', zorder=3)
        tip = tc + r[:, 2] * 0.03
        ax1.annotate('', xy=(tip[2], -tip[1]), xytext=(tc[2], -tc[1]),
                     arrowprops={'arrowstyle': '-|>', 'color': col, 'lw': 1.6}, zorder=6)
        _label(ax1, 0.343, ly, f'tilted {"+" if sign > 0 else "−"}{tilt:.0f}°', size=9.5, color=col)
    _arrow(ax1, (0.31, -0.04), (0.288, -0.04), color=MUTED, lw=1.2)
    _label(ax1, 0.313, -0.04, 'to the camera, 0.34 m away', size=9, color=MUTED, ha='left')
    _label(ax1, 0.335, 0.046, 'a 40 mm marker seen from the side', size=10, color=INK)
    _label(ax1, 0.352, 0.0, 'arrows: the way\nthe marker faces', size=8.5, color=MUTED, ha='left')
    # right: the four corners in the picture, zoomed
    rp, tp = marker_truth(tilt)
    rm, tm = marker_truth(-tilt)
    a = project_all(MARKER_PTS, rp, tp)
    b = project_all(MARKER_PTS, rm, tm)
    gap = float(np.max(np.linalg.norm(a - b, axis=1)))
    ax2.set_facecolor('white')
    for q, col, ls in ((a, LINK, '-'), (b, JOINT, '--')):
        loop = np.vstack([q, q[:1]])
        ax2.plot(loop[:, 0], loop[:, 1], color=col, lw=2, ls=ls, zorder=4)
        ax2.plot(q[:, 0], q[:, 1], 'o', color=col, mec=INK, ms=6, zorder=5)
    mid = a.mean(axis=0)
    ax2.set_xlim(mid[0] - 26, mid[0] + 26)
    ax2.set_ylim(mid[1] + 26, mid[1] - 26)
    ax2.set_aspect('equal')
    ax2.grid(color=GRID, lw=0.6)
    ax2.set_xlabel('u (pixels)', fontsize=9, color=MUTED)
    ax2.set_ylabel('v (pixels)', fontsize=9, color=MUTED)
    ax2.tick_params(labelsize=8, colors=MUTED)
    ax2.set_title(f'the corners in the picture: at most {gap:.2f} pixels apart', fontsize=10.5, color=INK)
    _save(fig, FOLDER_PNP, 'flat-marker-two-poses.svg')


MARKER_TILTS: list[float] = [0, 5, 10, 15, 20, 30, 40, 50, 60]


def pnp_marker_study_chart() -> None:
    """How wrong the marker's facing direction comes out, against how far it is tilted."""
    study = marker_study(MARKER_TILTS)
    tilts = [s['tilt'] for s in study]
    med = [s['median'] for s in study]
    p90 = [s['p90'] for s in study]
    fig, ax = plt.subplots(figsize=(8.6, 4.6), facecolor='white')
    ax.fill_between(tilts, med, p90, color=LINK_PALE, zorder=1, label='from the median to the worst tenth')
    ax.plot(tilts, med, 'o-', color=LINK, lw=2, zorder=3, label='median error')
    ax.plot(tilts, p90, 's--', color=PURPLE, lw=1.5, ms=5, zorder=3, label='the worst tenth of runs start here')
    for s in study:
        if s['tilt'] in (0, 20, 50):
            ax.annotate(f'{s["median"]:.1f}°', (s['tilt'], s['median']), textcoords='offset points',
                        xytext=(6, 8), fontsize=9, color=LINK)
    ax.set_xlabel('how far the marker is tilted away from facing the camera (degrees)', fontsize=10)
    ax.set_ylabel('error in the marker\'s facing direction (degrees)', fontsize=10)
    ax.set_xlim(-2, 62)
    ax.set_ylim(0, max(p90) * 1.12)
    ax.grid(color=GRID, lw=0.6)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(fontsize=9, frameon=False)
    ax.set_title('a 40 mm marker at 0.34 m, 0.3 pixels of corner noise, 300 runs per tilt',
                 fontsize=10.5, color=INK)
    _save(fig, FOLDER_PNP, 'face-on-is-unstable.svg')


# ==========================================================================
# 01_multi-view-geometry
# ==========================================================================

def _ray_2d(cam: tuple, px: np.ndarray, du: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """A pixel's ray in the side view: start (x, z) and the point where it meets the table."""
    r, t = cam
    d = r.T @ np.array([(px[0] + du - CX) / FX, (px[1] - CY) / FX, 1.0])
    c = -r.T @ t
    end = c + d * (-c[2] / d[2])
    return np.array([c[0], c[2]]), np.array([end[0], end[2]])


def mv_triangulation() -> None:
    """Side view: two wrist-camera poses, the two rays, and where they cross; then a close-up."""
    b = 0.08
    turn = math.degrees(math.atan2(b, TABLE_H - SPOT_WORLD[2]))
    cam1 = down_camera(0.0)
    cam2 = down_camera(b, turn_deg=turn)
    p1, p2 = to_px(SPOT_WORLD, cam1), to_px(SPOT_WORLD, cam2)
    est = triangulate(p1 + np.array([0.5, 0.0]), p2 - np.array([0.5, 0.0]), cam1, cam2)
    fig, (ax, az) = plt.subplots(1, 2, figsize=(11.8, 5.8), facecolor='white',
                                 gridspec_kw={'width_ratios': [1.15, 1]})
    _axes(ax, (-0.12, 0.20), (-0.05, 0.49))
    sx, sz = SPOT_WORLD[0], SPOT_WORLD[2]
    for axis in (ax, az):
        axis.add_patch(Rectangle((-0.12, -0.03), 0.32, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
        axis.plot([-0.12, 0.20], [0, 0], color='#b9a888', lw=1.5, zorder=2)
        axis.add_patch(Rectangle((sx - 0.03, 0), 0.06, 0.06, facecolor=GRIP, edgecolor='#a83232',
                                 lw=1.2, alpha=0.85, zorder=3))
    for cam, cx_, name, col, pp, dx, ha in ((cam1, 0.0, 'view 1', LINK, p1, -0.03, 'right'),
                                            (cam2, b, 'view 2', JOINT, p2, 0.03, 'left')):
        ang = -90 - (turn if cam is cam2 else 0.0)
        _camera_body(ax, cx_, TABLE_H, ang, size=0.018)
        _label(ax, cx_ + dx, TABLE_H, f'{name}\npixel u = {pp[0]:.1f}', size=9, color=col, ha=ha)
        for axis in (ax, az):
            s0, e0 = _ray_2d(cam, pp)
            axis.plot([s0[0], e0[0]], [s0[1], e0[1]], color=col, lw=2.0, zorder=4)
        for du in (-1.5, 1.5):
            s0, e0 = _ray_2d(cam, pp, du)
            az.plot([s0[0], e0[0]], [s0[1], e0[1]], color=col, lw=1.0, ls='--', zorder=4)
    for axis in (ax, az):
        axis.plot([sx], [sz], 'o', color=INK, ms=7, zorder=8)
    _arrow(ax, (0.0, TABLE_H + 0.05), (b, TABLE_H + 0.05), color=MUTED, lw=1.2, style='<|-|>')
    _label(ax, b / 2, TABLE_H + 0.068, f'the arm moves the camera {b * 1000:.0f} mm', size=9, color=MUTED)
    ax.add_patch(Rectangle((sx - 0.014, sz - 0.03), 0.028, 0.06, facecolor='none', edgecolor=MUTED,
                           lw=1, ls=':', zorder=9))
    _label(ax, sx + 0.018, sz + 0.04, 'close-up on the right', size=8.5, color=MUTED, ha='left')
    _label(ax, 0.04, -0.04, 'side view: table x runs left to right, height up', size=9, color=MUTED)
    # the close-up
    _axes(az, (sx - 0.014, sx + 0.014), (sz - 0.03, sz + 0.03))
    az.plot([est[0]], [est[2]], 'o', mfc='white', mec=INK, mew=1.6, ms=8, zorder=8)
    _label(az, sx, sz + 0.034, 'close-up: 28 mm wide, 60 mm tall', size=10, color=INK)
    _boxed(az, sx, sz - 0.037,
           f'true spot: x = {sx * 1000:.1f} mm, height {sz * 1000:.1f} mm\n'
           f'pixels moved 0.5 apart: x = {est[0] * 1000:.1f} mm, height {est[2] * 1000:.1f} mm',
           edge=INK, ha='center', size=8.5)
    _label(az, sx, sz - 0.049, 'dashed: each ray moved by 1.5 pixels.\nThe crossing can be anywhere in the diamond.',
           size=8.5, color=MUTED)
    az.add_patch(Rectangle((sx - 0.014, sz - 0.03), 0.028, 0.06, facecolor='none', edgecolor=MUTED,
                           lw=1, ls=':', zorder=9))
    _save(fig, FOLDER_MV, 'two-rays-cross.svg')


def mv_epipolar() -> None:
    """A pixel in view 1 becomes a line in view 2. The true match is on it; a look-alike is not."""
    b = 0.08
    turn = math.degrees(math.atan2(b, TABLE_H - SPOT_WORLD[2]))
    cam1 = down_camera(0.0)
    cam2 = down_camera(b, 0.03, turn_deg=turn)
    _e, f, _t = essential(cam1, cam2)
    other = np.array([0.020, -0.050, 0.06])      # a second red box's top, somewhere else
    p1 = to_px(SPOT_WORLD, cam1)
    p2 = to_px(SPOT_WORLD, cam2)
    o1 = to_px(other, cam1)
    o2 = to_px(other, cam2)
    ln = epipolar_line(f, p1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.9), facecolor='white')
    _picture(ax1, 'view 1')
    _picture(ax2, 'view 2')
    for ax, a, o in ((ax1, p1, o1), (ax2, p2, o2)):
        ax.plot([a[0]], [a[1]], 's', color=GRIP, mec=INK, ms=10, zorder=5)
        ax.plot([o[0]], [o[1]], 's', color=GRIP, mec=INK, ms=10, alpha=0.55, zorder=5)
    _label(ax1, p1[0], p1[1] - 13, f'the spot ({p1[0]:.1f}, {p1[1]:.1f})', size=9)
    _label(ax1, o1[0], o1[1] + 14, 'a look-alike box', size=9, color=MUTED)
    us = np.array([0.0, W_PX])
    vs = -(ln[0] * us + ln[2]) / ln[1]
    ax2.plot(us, vs, color=PURPLE, lw=2, zorder=3)
    d_true = line_distance(ln, p2)
    d_other = line_distance(ln, o2)
    _boxed(ax2, p2[0] - 10, p2[1] - 30, f'true match: {d_true:.2f} pixels from the line', edge=PURPLE, size=9)
    _boxed(ax2, o2[0] + 5, o2[1] + 26, f'look-alike: {d_other:.1f} pixels from the line', edge=GRID, size=9)
    _label(ax2, 60, vs[0] + (vs[1] - vs[0]) * 60 / W_PX - 16, 'epipolar line', size=9.5, color=PURPLE)
    _save(fig, FOLDER_MV, 'epipolar-line.svg')


def mv_stereo() -> None:
    """Rectified stereo: the same row in both pictures, and depth from the disparity."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.7), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.05, 1]})
    # left: the spot on the box top in the left and right pictures of a rectified pair
    q = np.array([0.0644, -0.0411, 0.34])         # the spot in the left camera's frame
    ul = FX * q[0] / q[2] + CX
    ur = FX * (q[0] - STEREO_B) / q[2] + CX
    v = FX * q[1] / q[2] + CY
    _picture(ax1, 'the spot in the left and right pictures')
    for u_, col, name, off, ha in ((ul, LINK, 'left', 8, 'left'), (ur, JOINT, 'right', -8, 'right')):
        ax1.plot([u_], [v], 'o', color=col, mec=INK, ms=10, zorder=5)
        _label(ax1, u_ + off, v - 14, f'{name} picture: u = {u_:.1f}', size=9, color=col, ha=ha)
    ax1.axhline(v, color=PURPLE, lw=1, ls='--', zorder=2)
    _arrow(ax1, (ur, v + 18), (ul, v + 18), color=INK, lw=1.2, style='<|-|>')
    _label(ax1, (ul + ur) / 2, v + 32, f'disparity = {ul - ur:.2f} pixels', size=9.5)
    _label(ax1, W_PX / 2, v + 62,
           f'depth = fx × b / disparity\n= 277.1 × 0.050 / {ul - ur:.2f} = {stereo_depth(ul - ur):.3f} m',
           size=9.5)
    _label(ax1, 8, v + 4, f'row v = {v:.1f} in both', size=8.5, color=PURPLE, ha='left', va='top')
    # right: depth against disparity, and the size of one disparity step
    d = np.linspace(5, 80, 300)
    ax2.plot(d, stereo_depth(d), color=LINK, lw=2, zorder=3)
    for z in (0.2, 0.34, 0.6, 1.0):
        dd = FX * STEREO_B / z
        step = z - stereo_depth(dd + 1)
        ax2.plot([dd], [z], 'o', color=JOINT, mec=INK, ms=6, zorder=5)
        ax2.annotate(f'{z:.2f} m: 1 pixel = {step * 1000:.0f} mm', (dd, z), textcoords='offset points',
                     xytext=(8, 4), fontsize=9, color=INK)
    ax2.set_xlabel('disparity (pixels)', fontsize=10)
    ax2.set_ylabel('depth (m)', fontsize=10)
    ax2.set_xlim(0, 82)
    ax2.set_ylim(0, 2.9)
    ax2.grid(color=GRID, lw=0.6)
    ax2.spines[['top', 'right']].set_visible(False)
    ax2.set_title('fx = 277.1, baseline 50 mm', fontsize=10.5, color=INK)
    _save(fig, FOLDER_MV, 'disparity-to-depth.svg')


def mv_parallax() -> None:
    """A camera slides 40 mm: the table shifts 27.7 pixels, the box top shifts more."""
    slide = 0.040
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.9), facecolor='white',
                                   gridspec_kw={'width_ratios': [1.1, 1]})
    _axes(ax1, (-0.10, 0.20), (-0.05, 0.47))
    ax1.add_patch(Rectangle((-0.10, -0.03), 0.30, 0.03, facecolor=TABLE, edgecolor='none', zorder=1))
    ax1.plot([-0.10, 0.20], [0, 0], color='#b9a888', lw=1.5, zorder=2)
    ax1.add_patch(Rectangle((SPOT_WORLD[0] - 0.03, 0), 0.06, 0.06, facecolor=GRIP, edgecolor='#a83232',
                            lw=1.2, alpha=0.85, zorder=3))
    table_pt = np.array([-0.02, 0.0])
    top_pt = np.array([SPOT_WORLD[0], SPOT_WORLD[2]])
    for cx_, col in ((0.0, LINK), (slide, JOINT)):
        _camera_body(ax1, cx_, TABLE_H, -90, size=0.018)
        for p in (table_pt, top_pt):
            ax1.plot([cx_, p[0]], [TABLE_H, p[1]], color=col, lw=1.3, zorder=4)
    ax1.plot(*table_pt, 'o', color=SLIDE, mec=INK, ms=7, zorder=6)
    ax1.plot(*top_pt, 'o', color=INK, ms=7, zorder=6)
    _arrow(ax1, (0.0, TABLE_H + 0.04), (slide, TABLE_H + 0.04), color=MUTED, lw=1.2, style='<|-|>')
    _label(ax1, slide / 2, TABLE_H + 0.058, 'slide 40 mm', size=9, color=MUTED)
    _label(ax1, -0.022, TABLE_H, 'before', size=9, color=LINK, ha='right')
    _label(ax1, slide + 0.022, TABLE_H, 'after', size=9, color=JOINT, ha='left')
    _label(ax1, table_pt[0] - 0.01, -0.035, 'a mark on the table', size=9, color=SLIDE, ha='right')
    _label(ax1, top_pt[0] + 0.035, top_pt[1] + 0.02, 'the box top, 60 mm up', size=9, ha='left')
    _label(ax1, -0.085, 0.2, '0.40 m', size=9, color=MUTED)
    ax1.plot([-0.07, -0.07], [0, TABLE_H], color=GRID, lw=1, ls=':')
    # right: the shifts in pixels
    ax2.set_facecolor('white')
    shift_table = FX * slide / TABLE_H
    shift_top = FX * slide / (TABLE_H - SPOT_WORLD[2])
    bars = ax2.barh([1, 0], [shift_table, shift_top], color=[SLIDE, INK], height=0.5, zorder=3)
    for bar, s in zip(bars, (shift_table, shift_top)):
        ax2.text(s + 0.6, bar.get_y() + bar.get_height() / 2, f'{s:.2f} pixels', va='center', fontsize=9.5)
    ax2.set_yticks([1, 0], ['table mark', 'box top'])
    ax2.set_xlim(0, 44)
    ax2.set_xlabel('how far it moves in the picture (pixels)', fontsize=10)
    ax2.grid(axis='x', color=GRID, lw=0.6)
    ax2.spines[['top', 'right']].set_visible(False)
    h = parallax_height(shift_top, slide)
    ax2.set_title(f'depth = 277.1 × 0.040 / {shift_top:.2f} = {TABLE_H - h:.3f} m;  height = {h * 1000:.1f} mm',
                  fontsize=10, color=INK)
    _save(fig, FOLDER_MV, 'parallax-gives-height.svg')


# --------------------------------------------------------------------------

def print_numbers() -> None:
    np.set_printoptions(precision=4, suppress=True)
    run = cube_run()
    print('CUBE true t (m):', run['t_true'])
    print('CUBE pixels:', run['px_true'])
    print('CUBE rms history:', [round(h, 3) for h in run['history'][:12]], '... final', run['final_rms'])
    print('CUBE start rms', run['start_rms'], 'final', run['final_rms'])
    print('CUBE pos err mm', run['pos_err_mm'], 'rot err deg', run['rot_err_deg'])
    print('CUBE DLT alone: rms', run['dlt_rms'], 'pos err mm', run['dlt_pos_err_mm'],
          'rot', angle_between(run['r_dlt'], run['r_true']))
    rr = ransac_run()
    print('RANSAC', {k: v for k, v in rr.items() if isinstance(v, (int, float))})
    for s in marker_study(MARKER_TILTS):
        print('MARKER', s)
    for tilt in (0, 5, 12, 30):
        rp, tp = marker_truth(tilt)
        rm, tm = marker_truth(-tilt)
        a = project_all(MARKER_PTS, rp, tp)
        b = project_all(MARKER_PTS, rm, tm)
        print('MARKER gap', tilt, float(np.max(np.linalg.norm(a - b, axis=1))))
    print('marker side in pixels', FX * MARKER / MARKER_DIST)
    for s in triangulation_study([0.018, 0.04, 0.08, 0.2]):
        print('TRI', s, 'formula 0.5px:', (0.34 ** 2) * 0.5 / (FX * s['b']) * 1000)
    b = 0.08
    turn = math.degrees(math.atan2(b, TABLE_H - SPOT_WORLD[2]))
    cam1 = down_camera(0.0)
    cam2 = down_camera(b, turn_deg=turn)
    p1, p2 = to_px(SPOT_WORLD, cam1), to_px(SPOT_WORLD, cam2)
    print('TRI pixels', p1, p2, 'turn', turn)
    print('TRI exact', triangulate(p1, p2, cam1, cam2))
    print('TRI noisy', triangulate(p1 + np.array([0.5, 0.0]), p2 - np.array([0.5, 0.0]), cam1, cam2))
    cam2e = down_camera(b, 0.03, turn_deg=turn)
    e, f, t = essential(cam1, cam2e)
    print('E', e, 't', t)
    q1 = np.linalg.inv(K) @ np.append(to_px(SPOT_WORLD, cam1), 1)
    q2 = np.linalg.inv(K) @ np.append(to_px(SPOT_WORLD, cam2e), 1)
    print('x2 E x1', q2 @ e @ q1)
    other = np.array([0.020, -0.050, 0.06])
    ln = epipolar_line(f, to_px(SPOT_WORLD, cam1))
    print('EPI pixels', to_px(SPOT_WORLD, cam1), to_px(SPOT_WORLD, cam2e), 'other', to_px(other, cam1),
          to_px(other, cam2e))
    print('EPI line', ln, 'dist true', line_distance(ln, to_px(SPOT_WORLD, cam2e)), 'other',
          line_distance(ln, to_px(other, cam2e)))
    for z in (0.2, 0.34, 0.5, 1.0, 2.0):
        d = FX * STEREO_B / z
        print('STEREO z', z, 'disp', d, 'step 1px mm', (z - stereo_depth(d + 1)) * 1000,
              'step 0.25px mm', (z - stereo_depth(d + 0.25)) * 1000)
    slide = 0.04
    st = FX * slide / TABLE_H
    sb = FX * slide / 0.34
    print('PARALLAX table shift', st, 'top shift', sb, 'h', parallax_height(sb, slide),
          'h with +0.5px', parallax_height(sb + 0.5, slide), 'h with -0.5', parallax_height(sb - 0.5, slide))
    g = ground_plane_point(212.5, 86.5)
    print('GROUND point', g, 'truth', SPOT_WORLD, 'horizontal error mm',
          np.linalg.norm(g[:2] - SPOT_WORLD[:2]) * 1000)
    # the tilted camera: a box top 60 mm up read as if on the table
    r_cam, c_cam = tilted_camera()
    top = np.array([0.0, 0.05, 0.06])
    d = top - c_cam
    s = -c_cam[2] / d[2]
    wrong = c_cam + d * s
    print('GROUND tilted: truth', top, 'assumed on table', wrong, 'error mm',
          np.linalg.norm(wrong[:2] - top[:2]) * 1000)


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    if len(sys.argv) >= 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        gc.PNG_DIR = pathlib.Path(sys.argv[2])
        gc.PNG_DIR.mkdir(parents=True, exist_ok=True)
    pnp_guess_and_fit()
    pnp_ransac()
    pnp_marker_two_poses()
    pnp_marker_study_chart()
    mv_triangulation()
    mv_epipolar()
    mv_stereo()
    mv_parallax()
    print(f'wrote the diagrams under {gc.IMAGES}')


if __name__ == '__main__':
    main()
