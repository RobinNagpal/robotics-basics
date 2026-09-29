"""Moving between two poses: joint-space moves, straight-line moves, and smooth timing.

This file prints every number quoted in the moving between poses doc, in the
order the doc uses them:

  1. a joint-space move: every joint turns evenly, and the gripper curves
  2. a straight-line move: inverse kinematics at every point along the line
  3. a straight line that fails partway, through the hole near the base
  4. a straight line towards full stretch, where joint 2 has to turn faster and faster
  5. timing: jumping to full speed at once, against a smooth start and stop

Run it with:  pixi run python src/kinematics/motion.py
"""

import math

from planar_arm import forward, two_joint_ik, TWO_LINKS

L1: float = TWO_LINKS[0]
L2: float = TWO_LINKS[1]

Point = tuple[float, float]
Joints = tuple[float, float]

#: The move used in sections 1 and 2: from low on the right to high on the left.
START: Point = (4.5, 0.5)
END: Point = (0.5, 4.0)

#: The move used in section 3. The straight line between these passes the base
#: closer than 1 m, and the arm cannot reach closer than 1 m.
FAIL_START: Point = (3.0, -1.0)
FAIL_END: Point = (-2.0, 1.5)

#: How many equal steps each move is cut into.
STEPS: int = 8


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the doc."""
    print(f'\n--- {text} ---')


def elbow_down(x: float, y: float) -> Joints:
    """Return the elbow-down answer for a target: the one with q2 positive, as in the IK doc."""
    answers: list[Joints] = two_joint_ik(x, y, L1, L2)
    return max(answers, key=lambda a: a[1])


def closest_answer(x: float, y: float, previous: Joints) -> Joints | None:
    """Return the IK answer nearest the joints the arm already has, or None if there is none.

    Taking the nearest answer stops the arm from flipping its elbow halfway
    along a line.
    """
    answers: list[Joints] = two_joint_ik(x, y, L1, L2)
    if not answers:
        return None
    return min(answers, key=lambda a: abs(a[0] - previous[0]) + abs(a[1] - previous[1]))


def along(a: Point, b: Point, s: float) -> Point:
    """Return the point a fraction s of the way from a to b, on the line between them."""
    return a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])


def off_line(p: Point, a: Point, b: Point) -> float:
    """Measure how far point p is from the straight line through a and b, in metres."""
    dx: float = b[0] - a[0]
    dy: float = b[1] - a[1]
    return abs(dx * (p[1] - a[1]) - dy * (p[0] - a[0])) / math.hypot(dx, dy)


def joint_space_path(a: Joints, b: Joints, steps: int) -> list[Joints]:
    """Turn every joint evenly from a to b. All joints start and finish together."""
    return [(a[0] + i / steps * (b[0] - a[0]), a[1] + i / steps * (b[1] - a[1]))
            for i in range(steps + 1)]


def cartesian_path(a: Point, b: Point, steps: int) -> list[Joints | None]:
    """Run inverse kinematics at equal steps along the straight line from a to b.

    An entry is None where the point on the line has no answer.
    """
    q: Joints = elbow_down(*a)
    path: list[Joints | None] = []
    for i in range(steps + 1):
        found: Joints | None = closest_answer(*along(a, b, i / steps), q)
        path.append(found)
        if found is not None:
            q = found
    return path


def deg(q: Joints) -> str:
    """Format both joint angles in degrees, lined up."""
    return f'q1 = {math.degrees(q[0]):7.2f}, q2 = {math.degrees(q[1]):7.2f}'


def joint_move() -> None:
    """Section 1: turn both joints evenly, and see where the gripper goes."""
    heading('1. Joint-space move: every joint turns evenly')
    q_start: Joints = elbow_down(*START)
    q_end: Joints = elbow_down(*END)
    print(f'start gripper ({START[0]}, {START[1]}): {deg(q_start)}')
    print(f'end gripper   ({END[0]}, {END[1]}): {deg(q_end)}')
    print('step   joints                         gripper            off the straight line')
    worst: float = 0.0
    for i, q in enumerate(joint_space_path(q_start, q_end, STEPS)):
        x, y, _ = forward(list(q), TWO_LINKS)
        gap: float = off_line((x, y), START, END)
        worst = max(worst, gap)
        print(f'{i:>4}   {deg(q)}   ({x:6.3f}, {y:6.3f})   {gap:.3f} m')
    print(f'the gripper strays up to {worst:.3f} m from the straight line')


def straight_move() -> None:
    """Section 2: put the gripper on the line at every step, with inverse kinematics."""
    heading('2. Straight-line move: inverse kinematics at every step')
    print('step   gripper on the line   joints')
    for i, q in enumerate(cartesian_path(START, END, STEPS)):
        p: Point = along(START, END, i / STEPS)
        print(f'{i:>4}   ({p[0]:6.3f}, {p[1]:6.3f})      {deg(q) if q else "no answer"}')


def failing_move() -> None:
    """Section 3: a straight line that passes too close to the base."""
    heading('3. A straight line through the hole near the base')
    dx: float = FAIL_END[0] - FAIL_START[0]
    dy: float = FAIL_END[1] - FAIL_START[1]
    closest: float = abs(FAIL_START[0] * dy - FAIL_START[1] * dx) / math.hypot(dx, dy)
    print(f'from ({FAIL_START[0]}, {FAIL_START[1]}) to ({FAIL_END[0]}, {FAIL_END[1]})')
    print(f'the line passes {closest:.3f} m from the base; '
          f'the arm cannot reach closer than {L1 - L2:.0f} m')
    print('step   gripper on the line   distance from base   joints')
    for i, q in enumerate(cartesian_path(FAIL_START, FAIL_END, STEPS)):
        p: Point = along(FAIL_START, FAIL_END, i / STEPS)
        print(f'{i:>4}   ({p[0]:6.3f}, {p[1]:6.3f})      {math.hypot(*p):5.3f} m'
              f'              {deg(q) if q else "no answer"}')
    q_start: Joints = elbow_down(*FAIL_START)
    q_end: Joints = elbow_down(*FAIL_END)
    nearest: float = min(math.hypot(*forward(list(q), TWO_LINKS)[:2])
                         for q in joint_space_path(q_start, q_end, 100))
    print(f'joint-space move between the same two ends: closest to the base '
          f'{nearest:.3f} m, every step has an answer')


def towards_stretch() -> None:
    """Section 4: equal gripper steps towards full stretch need ever bigger joint turns."""
    heading('4. A straight line towards full stretch')
    print('the gripper moves out along the x axis in equal 0.1 m steps')
    print('gripper x   q2         how far q2 turned in this 0.1 m step')
    previous: float | None = None
    for x10 in range(44, 51):
        x: float = x10 / 10.0
        q2: float = elbow_down(x, 0.0)[1]
        change: str = '' if previous is None else f'{math.degrees(previous - q2):6.2f} degrees'
        print(f'{x:9.1f}   {math.degrees(q2):6.2f}     {change}')
        previous = q2


def smooth(s: float) -> float:
    """Give a smooth start and stop: position goes 0 to 1 with zero speed at both ends."""
    return 3.0 * s * s - 2.0 * s ** 3


def smooth_speed(s: float) -> float:
    """Give how fast smooth() is changing at s, as a multiple of the average speed."""
    return 6.0 * s - 6.0 * s * s


def timing() -> None:
    """Section 5: position and speed over a 1-second move, both ways."""
    heading('5. Timing: jump to full speed, or start and stop smoothly')
    print('both moves go from 0 % to 100 % of the way in 1 second')
    print('time      even speed              smooth start and stop')
    print('          position   speed        position   speed')
    for i in range(9):
        t: float = i / 8.0
        even_speed: str = '1.00' if 0.0 < t < 1.0 else '0 -> 1.00' if t == 0.0 else '1.00 -> 0'
        print(f'{t:4.3f} s   {100 * t:5.1f} %    {even_speed:<11}  '
              f'{100 * smooth(t):5.1f} %    {smooth_speed(t):.2f}')
    print('speed is a multiple of the average speed, which is 100 % per second')


if __name__ == '__main__':
    joint_move()
    straight_move()
    failing_move()
    towards_stretch()
    timing()
