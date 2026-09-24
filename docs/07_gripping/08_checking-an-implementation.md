# Checking an implementation

The other seven documents explain. This one is a list you run down.

Every line is a question, a one-line statement of what goes wrong if the answer
is no, and a link to the section that explains why. Nothing here is new: it is
the traps from the rest of the area, arranged so that you can audit code against
them in a sitting rather than by reading seven documents and remembering.

It is written for the case where the code already works. Most of these failures
do not stop a cell running. They make it fragile in a way that shows up on a
different object, a heavier one, a faster move, or a Tuesday.

## How to use it

Take one pick-and-place path through your code and answer each question about
it. A "no" is not necessarily a bug — several of these are reasonable
simplifications — but it should be a simplification you *chose*, and one written
down where the next person will find it. The difference between an assumption and
an oversight is whether it is in a comment.

---

## Before the fingers close

**Does a grip rule know the gripper's own body, and does that limit bound the
search rather than the answer?**
If the limit filters results instead of shaping the search, "hold it higher"
becomes "cannot be held". →
[choosing a grip, §7](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body)

**Do the checks report a margin, or a boolean?**
Five pass/fail checks mean the first acceptable grip wins even when a better one
exists two millimetres away. The margin inside the friction cone costs nothing
extra and turns a pass into a ranking. →
[choosing a grip, §9.1](03_choosing-a-grip.md#91-the-ones-worth-computing)

**Is the centre of mass assumed to be the centre of the outline, and is that
written down?**
True for a symmetric object, false for a mug, a part-full bottle, or anything
with an insert. The wrist reads torque as well as force, so the offset is torque
divided by weight. →
[choosing a grip, §5](03_choosing-a-grip.md#5-the-centre-of-mass-and-the-torque-nobody-budgets-for)

**Is the grasp above the centre of mass?**
Below it, the object is an inverted pendulum in the fingers and any disturbance
grows. →
[choosing a grip, §5](03_choosing-a-grip.md#5-the-centre-of-mass-and-the-torque-nobody-budgets-for)

**Is acceleration in the force formula, or hidden in the safety factor?**
`F = m(g + a)S / 2μ` with `a` from the planner leaves `S` covering only
uncertainty, which is what a safety factor is for. A factor chosen to absorb an
unmeasured acceleration is a factor nobody can defend. →
[choosing a grip, §4](03_choosing-a-grip.md#4-how-hard-to-squeeze-from-first-principles)

## While closing

**Is the commanded effort being treated as the applied force?**
It is a motor current limit. Robotiq publish 220 N on steel and 115 N on soft
rubber at one setting, with repeatability around ±10%, and OnRobot quote ±25%. →
[holding on, §2.1](05_holding-on.md#21-the-command-is-a-torque-request-not-a-force)

**Is the commanded position the gap, or one finger's travel?**
Usually the latter, so the gap is twice it. The failure looks like a perception
error. →
[the two-finger gripper, §4](06_two-finger-gripper.md#4-the-grasp-as-pseudo-code)

**Is the width at first contact compared against what perception predicted?**
The fingers stop where the object is. That is a free measurement and it catches a
misplaced grasp before any force is applied. →
[the two-finger gripper, §4](06_two-finger-gripper.md#4-the-grasp-as-pseudo-code)

**Is `allow_stalling` set?**
Closing on an object always stalls. Left at its default, the action reports
failure for every successful grasp. →
[the two-finger gripper, §2](06_two-finger-gripper.md#2-the-ros-2-interfaces-concretely)

## While holding

**Is the wrench rotated into the world frame before the weight is read?**
A force sensor reports in the tool's frame, so a side grasp reads zero and every
object weighs nothing, convincingly. →
[perception, sensors §2.1](../06_object-perception/02_sensors.md#21-what-you-can-actually-do-with-it)

**Is the weight a median of a few dozen samples with the arm still?**
Gripping and motion put transients through the sensor many times the payload. A
single sample is a plausible wrong number. →
[holding on, §1](05_holding-on.md#1-the-squeeze-sequence)

**Is there any check that the object is still held, other than the finger gap?**
The gap sees squashing. It cannot see the object sliding out or rotating. →
[holding on, §5.1](05_holding-on.md#51-every-signal-you-can-get-and-what-each-one-settles)

**Is there a response to slip other than refusing?**
There are five, in cost order: squeeze harder, slow down, regrasp, give up, and
the one to avoid — correcting the grasp point from measurements taken before the
object moved. A cell that only refuses is throwing away four of them. →
[holding on, §5.2](05_holding-on.md#52-the-five-responses-in-order-of-cost)

## Letting go

**Does the descent stop on the weight leaving the wrist, or on a contact sensor?**
Pad sensors cannot feel a held object's base touching down. The event is a
transfer of weight. →
[holding on, §8](05_holding-on.md#8-letting-go)

**Is support confirmed before the fingers open?**
A rim caught on a lip registers contact while still hanging from the gripper. →
[holding on, §8](05_holding-on.md#8-letting-go)

**Do the fingers open past the object's widest point, by construction?**
Opening to the gripper's maximum often clears it, and "often" is not a design. If
the maximum does not clear it, the retract direction has to avoid it instead. →
[holding on, §8](05_holding-on.md#8-letting-go)

**Is the placement confirmed?**
If the camera is pointed at the destination anyway, it costs one frame, and it is
the difference between reporting a failed placement and stacking onto a gap. →
[holding on, §8](05_holding-on.md#8-letting-go)

## Across the whole thing

**Does every refusal carry a sentence rather than a code?**
The reason has to survive into the report, or the thresholds can never be argued
with. →
[perception, making it work §6](../06_object-perception/07_making-it-work.md#6-declining-as-a-mechanism-rather-than-an-intention)

**Is the rule tested against a generated family, or against one object?**
A rule fails on proportions, and one test object has one set of proportions. →
[choosing a grip, §11](03_choosing-a-grip.md#11-testing-a-grip-rule)

**Are the simplifications written down where the next person will find them?**
This is the only question on the list with no wrong answer, and the one most
often skipped.

---

## What this list is not

It is not a specification, and passing every line does not mean a cell is safe.
It covers the failures this area documents, which are the ones that are quiet.
The loud ones — a gripper that does not open, a plan that does not solve — find
you on their own and need no checklist.

The same treatment would suit [object
perception](../06_object-perception/01_overview.md) and [arm
movement](../08_arm-movement/01_overview.md), which have comparable numbers of
quiet failures and no list of their own yet.
