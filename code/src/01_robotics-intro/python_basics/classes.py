"""Classes: keeping a joint's angle and its limits together, and checking them.

A real joint cannot turn forever. It has a smallest and a largest angle, set by
the motor and by the parts around it. A class keeps the angle and its limits in
one object, and gives that object the methods that use them:

  1. a Joint class with a name, limits and an angle
  2. a method that refuses an angle outside the limits
  3. a method that clamps an angle into the limits instead
  4. a list of Joint objects: a whole arm

Run it with:  pixi run python src/python_basics/classes.py
"""


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


class Joint:
    """One turning joint: a name, the range it can turn through, and where it is now."""

    def __init__(self, name: str, lower_deg: float, upper_deg: float) -> None:
        """Make a joint that starts at 0 degrees."""
        self.name: str = name
        self.lower_deg: float = lower_deg
        self.upper_deg: float = upper_deg
        self.angle_deg: float = 0.0

    def set_angle(self, angle_deg: float) -> None:
        """Move to angle_deg, or raise ValueError if the joint cannot turn that far."""
        if not self.lower_deg <= angle_deg <= self.upper_deg:
            raise ValueError(f'{self.name}: {angle_deg} deg is outside '
                             f'[{self.lower_deg}, {self.upper_deg}]')
        self.angle_deg = angle_deg

    def set_angle_clamped(self, angle_deg: float) -> None:
        """Move as close to angle_deg as the limits allow."""
        self.angle_deg = min(max(angle_deg, self.lower_deg), self.upper_deg)

    def __repr__(self) -> str:
        """Describe the joint when it is printed."""
        limits: str = f'{self.lower_deg}..{self.upper_deg}'
        return f'Joint({self.name}, {self.angle_deg} deg, limits {limits})'


def one_joint() -> None:
    """Make one joint and move it."""
    heading('1. A Joint object')
    elbow: Joint = Joint('elbow', -150.0, 150.0)
    print(elbow)
    elbow.set_angle(60.0)
    print('after set_angle(60.0):', elbow)


def refusing() -> None:
    """Ask for an angle the joint cannot reach."""
    heading('2. Refusing an angle outside the limits')
    elbow: Joint = Joint('elbow', -150.0, 150.0)
    try:
        elbow.set_angle(170.0)
    except ValueError as error:
        print('ValueError:', error)
    print('the joint did not move:', elbow)


def clamping() -> None:
    """Ask for the same angle, and let the joint stop at its limit."""
    heading('3. Clamping instead')
    elbow: Joint = Joint('elbow', -150.0, 150.0)
    elbow.set_angle_clamped(170.0)
    print('after set_angle_clamped(170.0):', elbow)


def an_arm() -> None:
    """Build an arm as a list of joints."""
    heading('4. A list of joints: a whole arm')
    arm: list[Joint] = [Joint('shoulder', -90.0, 90.0), Joint('elbow', -150.0, 150.0)]
    for joint, target in zip(arm, [30.0, 60.0]):
        joint.set_angle(target)
    for joint in arm:
        print(joint)
    print('angles as a list:', [joint.angle_deg for joint in arm])


if __name__ == '__main__':
    one_joint()
    refusing()
    clamping()
    an_arm()
