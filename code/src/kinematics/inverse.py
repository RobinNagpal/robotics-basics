"""Inverse kinematics: gripper position in, joint angles out.

This file prints every number quoted in the inverse kinematics doc, in the
order the doc uses them:

  1. the two-joint arm solved by hand, with the law of cosines and atan2
  2. both answers, elbow up and elbow down, checked with forward kinematics
  3. targets with no answer, and targets with exactly one
  4. the three-joint arm: one answer for each gripper angle you choose
  5. numerical inverse kinematics: guess, correct, repeat
  6. how long each way takes

Run it with:  pixi run python src/kinematics/inverse.py
"""

import math
import timeit

from planar_arm import (forward, numerical_ik, points, three_joint_ik, THREE_LINKS,
                        two_joint_ik, TWO_LINKS)

L1: float = TWO_LINKS[0]
L2: float = TWO_LINKS[1]
#: Where the two-joint arm's gripper is at q1 = 30, q2 = 60.
TARGET: tuple[float, float] = (L1 * math.cos(math.radians(30.0)), 3.5)


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the doc."""
    print(f'\n--- {text} ---')


def elbow_side(q1: float, q2: float, x: float, y: float) -> str:
    """Say whether the elbow sits above or below the line from the base to the target."""
    ex, ey = points([q1, q2], TWO_LINKS)[1]
    cross: float = x * ey - y * ex        # > 0: the elbow is to the left of the line
    return 'elbow up' if cross > 0 else 'elbow down'


def by_hand() -> None:
    """Every step of the two-joint solution, printed as it happens."""
    heading('1. Solving the two-joint arm by hand')
    x, y = TARGET
    print(f'target: ({x:.3f}, {y:.3f})')
    d_squared: float = x * x + y * y
    print(f'distance squared: {x:.3f}^2 + {y:.3f}^2 = {d_squared:.3f}')
    print(f'distance: {math.sqrt(d_squared):.3f} m')
    cos_q2: float = (d_squared - L1 * L1 - L2 * L2) / (2.0 * L1 * L2)
    print(f'cos(q2) = ({d_squared:.3f} - 9 - 4) / 12 = {cos_q2:.3f}')
    q2: float = math.acos(cos_q2)
    print(f'q2 = +{math.degrees(q2):.2f} or -{math.degrees(q2):.2f} degrees')
    alpha: float = math.atan2(y, x)
    print(f'angle from the base to the target: atan2({y:.3f}, {x:.3f}) = '
          f'{math.degrees(alpha):.2f} degrees')
    for sign in (1.0, -1.0):
        b: float = math.atan2(L2 * math.sin(sign * q2), L1 + L2 * math.cos(sign * q2))
        print(f'for q2 = {math.degrees(sign * q2):+.2f}: the correction is '
              f'atan2({L2 * math.sin(sign * q2):.3f}, {L1 + L2 * math.cos(sign * q2):.3f}) = '
              f'{math.degrees(b):+.2f}, so q1 = {math.degrees(alpha - b):.2f}')


def both_answers() -> None:
    """Both answers, put back through forward kinematics to check them."""
    heading('2. Two answers, checked with forward kinematics')
    x, y = TARGET
    for q1, q2 in two_joint_ik(x, y, L1, L2):
        gx, gy, _ = forward([q1, q2], TWO_LINKS)
        ex, ey = points([q1, q2], TWO_LINKS)[1]
        print(f'q1 = {math.degrees(q1):6.2f}, q2 = {math.degrees(q2):+6.2f}: '
              f'elbow at ({ex:.3f}, {ey:.3f}), gripper at ({gx:.3f}, {gy:.3f}), '
              f'{elbow_side(q1, q2, x, y)}')


def reach_cases() -> None:
    """Targets too far, too close, on the edge, and inside."""
    heading('3. How many answers each target has')
    targets: dict[str, tuple[float, float]] = {
        'too far': (6.0, 0.0),
        'too close': (0.5, 0.0),
        'full stretch': (5.0, 0.0),
        'folded back': (1.0, 0.0),
        'inside the ring': (4.0, 0.0),
    }
    for name, (x, y) in targets.items():
        d: float = math.hypot(x, y)
        cos_q2: float = (d * d - L1 * L1 - L2 * L2) / (2.0 * L1 * L2)
        answers: list[tuple[float, float]] = two_joint_ik(x, y, L1, L2)
        found: str = ', '.join(f'({round(math.degrees(a), 2) + 0.0:.2f}, '
                               f'{round(math.degrees(b), 2) + 0.0:.2f})'
                               for a, b in answers) or '-'
        print(f'{name:16s} ({x}, {y}): distance {d:.2f}, cos(q2) = {cos_q2:+.3f}, '
              f'{len(answers)} answer(s): {found}')


def three_joints() -> None:
    """Reach the same point with the gripper at different angles."""
    heading('4. The three-joint arm: pick the gripper angle, then solve')
    x, y, _ = forward([math.radians(a) for a in (30.0, 60.0, -60.0)], THREE_LINKS)
    print(f'target: ({x:.3f}, {y:.3f})')
    for phi_deg in (0.0, 30.0, 60.0, 90.0, 180.0):
        answers = three_joint_ik(x, y, math.radians(phi_deg), THREE_LINKS)
        if not answers:
            print(f'gripper angle {phi_deg:5.1f}: no answer, the wrist is out of reach')
            continue
        text: str = '   or   '.join(
            '(' + ', '.join(f'{math.degrees(a):7.2f}' for a in q) + ')' for q in answers)
        print(f'gripper angle {phi_deg:5.1f}: {text}')


def numerically() -> None:
    """Guess, correct, repeat, from two different guesses."""
    heading('5. Numerical inverse kinematics')
    x, y = TARGET
    for guess_deg in ((0.0, 30.0), (90.0, -30.0)):
        guess: list[float] = [math.radians(a) for a in guess_deg]
        history = numerical_ik(x, y, guess, TWO_LINKS)
        print(f'starting guess {guess_deg}:')
        for i, (joints, miss) in enumerate(history):
            print(f'  step {i}: q1 = {math.degrees(joints[0]):7.2f}, '
                  f'q2 = {math.degrees(joints[1]):7.2f}, miss = {miss:.6f} m')


def timing() -> None:
    """How long one solution takes each way, on this computer."""
    heading('6. How long each way takes')
    x, y = TARGET
    runs: int = 2000
    analytic: float = timeit.timeit(lambda: two_joint_ik(x, y, L1, L2), number=runs) / runs
    guess: list[float] = [0.0, math.radians(30.0)]
    numeric: float = timeit.timeit(lambda: numerical_ik(x, y, guess, TWO_LINKS),
                                   number=runs) / runs
    print(f'by hand (law of cosines): {analytic * 1e6:.1f} microseconds')
    print(f'numerical:                {numeric * 1e6:.1f} microseconds')
    print(f'numerical is about {numeric / analytic:.0f} times slower')


def main() -> None:
    """Print every section, in the order the doc uses them."""
    by_hand()
    both_answers()
    reach_cases()
    three_joints()
    numerically()
    timing()


if __name__ == '__main__':
    main()
