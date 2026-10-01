"""The six-joint arm: forward and inverse kinematics of a Universal Robots UR5e.

This file prints the numbers quoted in
docs/01_robotics-intro/05_arm-types/03_the-six-joint-arm.md:

  1. the UR5e's published chain, one row per joint
  2. forward kinematics: every joint's position and the tool's position and
     pointing direction, at the zero pose and at a working pose
  3. what each joint's angle does on its own, joint by joint
  4. inverse kinematics: many different starting guesses, one target, and
     the different answers they settle on, with how high each puts the elbow
  5. the wrist singularity: with wrist 2 at 0, wrist 1 and wrist 3 turn about
     the same line

The chain comes from Universal Robots, "DH parameters for calculations of
kinematics and dynamics":
https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/

Run it with:  pixi run python src/arm_types/ur5e.py
"""

import math

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares  # type: ignore[import-untyped]

# One row per joint: (d, a, alpha), in metres and radians.
#   d     how far to move along the joint's own turning axis
#   a     how far to move sideways, out to the next joint's axis
#   alpha how much to tip the next joint's axis
UR5E_CHAIN: list[tuple[float, float, float]] = [
    (0.1625, 0.0, math.pi / 2),
    (0.0, -0.425, 0.0),
    (0.0, -0.3922, 0.0),
    (0.1333, 0.0, math.pi / 2),
    (0.0997, 0.0, -math.pi / 2),
    (0.0996, 0.0, 0.0),
]

JOINT_NAMES: list[str] = ['base', 'shoulder', 'elbow', 'wrist 1', 'wrist 2', 'wrist 3']

# A working pose: the arm reaching forward and down over a table, in degrees.
WORK_POSE_DEG: list[float] = [0.0, -60.0, 90.0, -120.0, -90.0, 0.0]


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def joint_transform(theta: float, d: float, a: float, alpha: float) -> NDArray[np.float64]:
    """Build the 4 x 4 transform from one joint's frame to the next.

    Read left to right it is four simple moves: turn by theta about z (this is
    the joint moving), slide d along z, slide a along the new x, tip by alpha
    about that x.
    """
    ct: float = math.cos(theta)
    st: float = math.sin(theta)
    ca: float = math.cos(alpha)
    sa: float = math.sin(alpha)
    return np.array([[ct, -st * ca, st * sa, a * ct],
                     [st, ct * ca, -ct * sa, a * st],
                     [0.0, sa, ca, d],
                     [0.0, 0.0, 0.0, 1.0]])


def forward(q: NDArray[np.float64] | list[float]) -> list[NDArray[np.float64]]:
    """Every frame along the chain, from the base (first) to the tool (last).

    Each one is the product of all the joint transforms before it.
    """
    frames: list[NDArray[np.float64]] = [np.eye(4)]
    for theta, (d, a, alpha) in zip(q, UR5E_CHAIN):
        frames.append(frames[-1] @ joint_transform(float(theta), d, a, alpha))
    return frames


def tool(q: NDArray[np.float64] | list[float]) -> NDArray[np.float64]:
    """Return the tool's frame: where it is, and which way it points."""
    return forward(q)[-1]


def fmt(v: NDArray[np.float64]) -> str:
    """Write a vector as signed numbers to a tenth of a millimetre."""
    return '(' + ', '.join(f'{round(float(x), 4) + 0.0:+.4f}' for x in v) + ')'


def pose_error(q: NDArray[np.float64], target: NDArray[np.float64]) -> NDArray[np.float64]:
    """Twelve numbers that are all zero only when the tool is on the target.

    Three for position, and nine for the difference between the two 3 x 3
    rotations. The rotation part is scaled by 0.1 m, so a small turn counts
    about as much as a small shift.
    """
    t: NDArray[np.float64] = tool(q)
    return np.concatenate([t[:3, 3] - target[:3, 3],
                           0.1 * (t[:3, :3] - target[:3, :3]).ravel()])


def wrap(q: NDArray[np.float64]) -> NDArray[np.float64]:
    """Bring every angle into the range -180 to +180 degrees."""
    return np.asarray((q + math.pi) % (2 * math.pi) - math.pi, dtype=np.float64)


def solve_many(target: NDArray[np.float64], tries: int,
               seed: int) -> list[NDArray[np.float64]]:
    """Start from many random guesses and keep every different answer found."""
    rng: np.random.Generator = np.random.default_rng(seed)
    found: list[NDArray[np.float64]] = []
    for _ in range(tries):
        guess: NDArray[np.float64] = rng.uniform(-math.pi, math.pi, 6)
        result = least_squares(pose_error, guess, args=(target,), xtol=1e-12, ftol=1e-12)
        if np.linalg.norm(pose_error(result.x, target)) > 1e-7:
            continue            # this guess got stuck and never reached the target
        q: NDArray[np.float64] = wrap(result.x)
        if not any(np.linalg.norm(wrap(q - other)) < 1e-4 for other in found):
            found.append(q)
    return found


def describe(q: NDArray[np.float64], target: NDArray[np.float64]) -> str:
    """Name the three choices that tell the answers apart, from where the parts are.

    shoulder: does the base face the target, or face away so the arm reaches
              back over the top of itself?
    elbow:    is the elbow above or below the straight line from shoulder to wrist?
    wrist:    which way round is wrist 2 turned? Normal is the sign the
              working pose uses (negative); flipped is the other sign.
    """
    frames = forward(q)
    shoulder_pt: NDArray[np.float64] = frames[1][:3, 3]
    elbow_pt: NDArray[np.float64] = frames[2][:3, 3]
    wrist_pt: NDArray[np.float64] = frames[3][:3, 3]
    # With the shoulder and elbow straight, a UR arm reaches along -x of frame 1.
    reach_dir: NDArray[np.float64] = -frames[1][:3, 0]
    facing: bool = float(reach_dir[:2] @ target[:2, 3]) > 0
    along: float = float((elbow_pt - shoulder_pt) @ (wrist_pt - shoulder_pt)
                         / ((wrist_pt - shoulder_pt) @ (wrist_pt - shoulder_pt)))
    on_line: NDArray[np.float64] = shoulder_pt + along * (wrist_pt - shoulder_pt)
    up: bool = float(elbow_pt[2] - on_line[2]) > 0
    return (f'base {"faces the target" if facing else "faces away      "}  '
            f'elbow {"up  " if up else "down"}  '
            f'wrist {"normal " if q[4] < 0 else "flipped"}')


def main() -> None:
    """Print each numbered section in turn."""
    heading('1. the UR5e chain (from Universal Robots)')
    print('  joint      d (m)     a (m)    alpha (deg)')
    for name, (d, a, alpha) in zip(JOINT_NAMES, UR5E_CHAIN):
        print(f'  {name:9s} {d:7.4f}  {a:8.4f}   {math.degrees(alpha):6.0f}')

    for label, pose_deg in (('zero pose, every joint at 0', [0.0] * 6),
                            ('working pose ' + str(WORK_POSE_DEG), WORK_POSE_DEG)):
        heading(f'2. forward kinematics: {label}')
        frames = forward(np.radians(pose_deg))
        for name, frame in zip(['base'] + [f'after {n}' for n in JOINT_NAMES], frames):
            print(f'  {name:15s} at {fmt(frame[:3, 3])}')
        print(f'  tool points along {fmt(frames[-1][:3, 2])}')

    heading('3. one joint at a time: add 30 degrees to each joint of the working pose')
    base_q: NDArray[np.float64] = np.radians(WORK_POSE_DEG)
    base_tool: NDArray[np.float64] = tool(base_q)
    for i, name in enumerate(JOINT_NAMES):
        q = base_q.copy()
        q[i] += math.radians(30.0)
        t = tool(q)
        shift: float = float(np.linalg.norm(t[:3, 3] - base_tool[:3, 3]))
        cos_turn: float = float(np.clip(t[:3, 2] @ base_tool[:3, 2], -1, 1))
        print(f'  {name:9s} tool moves {shift * 1000:6.1f} mm, '
              f'tool direction turns {math.degrees(math.acos(cos_turn)):5.1f} deg')

    heading('4. inverse kinematics: one target, 200 random starting guesses')
    target: NDArray[np.float64] = tool(np.radians(WORK_POSE_DEG))
    print(f'  target position {fmt(target[:3, 3])}, pointing {fmt(target[:3, 2])}')
    answers = solve_many(target, tries=200, seed=1)
    # The answers that face the target first, then in order of the shoulder angle.
    answers.sort(key=lambda a: (-round(float(a[0]), 3), round(float(a[1]), 3)))
    print(f'  different answers found: {len(answers)}')
    for q in answers:
        err: float = float(np.linalg.norm(tool(q)[:3, 3] - target[:3, 3]))
        degs: str = ', '.join(f'{round(float(v), 1) + 0.0:7.1f}' for v in np.degrees(q))
        print(f'  q = ({degs})  miss {err * 1000:.1e} mm  {describe(q, target)}')
    print('  elbow height above the base plate, per answer (mm):',
          ', '.join(f'{forward(q)[2][2, 3] * 1000:.1f}' for q in answers))

    heading('5. the wrist singularity: the axes of wrist 1 and wrist 3')
    for wrist2_deg in (0.0, 30.0):
        q = np.radians(WORK_POSE_DEG)
        q[4] = math.radians(wrist2_deg)
        frames = forward(q)
        print(f'  wrist 2 at {wrist2_deg:4.0f} deg: wrist 1 turns about {fmt(frames[3][:3, 2])},'
              f' wrist 3 about {fmt(frames[5][:3, 2])}')


if __name__ == '__main__':
    main()
