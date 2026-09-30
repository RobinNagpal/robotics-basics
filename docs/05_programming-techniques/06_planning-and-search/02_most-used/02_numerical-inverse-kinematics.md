# Numerical inverse kinematics

This page explains how a program finds the joint angles that put a gripper at a
chosen place, when there is no neat formula to do it. It answers five questions.
How does the guess-and-correct loop work? What is the Jacobian, and why does the
loop need it? Why does the plain loop go wild when the arm is nearly straight?
How does **damped least squares**, the method most solvers use, fix that? And
what happens when the target cannot be reached at all?

It is for a reader who has read
[inverse kinematics](../../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md)
in Book 1. That page solves the same small arm with a triangle formula, and then
introduces the guess-and-correct loop in
[its section 6](../../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md#6-numerical-inverse-kinematics-guess-and-correct).
This page picks up where that one stops. It uses the same arm, the same target
and the same first guess, so you can compare the numbers.

The arm has two links lying flat: link 1 is 3 m and link 2 is 2 m. The target is
`(2.598, 3.5)`, which is where the gripper sits when `q1 = 30°` and `q2 = 60°`.
Every number on this page is printed by the diagram script
`docs/diagrams/planning_and_search_2.py`.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [How it works](#2-how-it-works)
   · [Step 1: measure the miss](#step-1-measure-the-miss)
   · [Step 2: the Jacobian](#step-2-the-jacobian)
   · [Step 3: turning the Jacobian round](#step-3-turning-the-jacobian-round)
   · [Step 4: why the plain answer goes wild near a straight arm](#step-4-why-the-plain-answer-goes-wild-near-a-straight-arm)
   · [Step 5: damped least squares](#step-5-damped-least-squares)
   · [Step 6: a worked run](#step-6-a-worked-run)
   · [Step 7: a target out of reach, and choosing the damping](#step-7-a-target-out-of-reach-and-choosing-the-damping)
   · [Step 8: more joints than the task needs](#step-8-more-joints-than-the-task-needs)
   · [Pseudocode](#pseudocode)
3. [Where it is used on a robot arm](#3-where-it-is-used-on-a-robot-arm)
4. [Where it works, and where it does not](#4-where-it-works-and-where-it-does-not)
5. [Libraries that provide it](#5-libraries-that-provide-it)
6. [Why numerical inverse kinematics, and what it costs](#6-why-numerical-inverse-kinematics-and-what-it-costs)
7. [The learned alternative](#7-the-learned-alternative)
8. [Where to read next](#8-where-to-read-next)

---

## 1. The idea in one sentence

Guess the joint angles, see how far the gripper misses the target, work out which
small turn of each joint shrinks that miss, make the turn, and repeat until the
miss is tiny.

Here is an everyday example. Think of parking a car close to a kerb with the
help of a mirror. You do not work out the steering angle in advance. You look in
the mirror, see that you are 40 cm out, turn the wheel a little, roll back, and
look again. Each look tells you the miss. You know from experience which way to
turn the wheel to shrink it. You keep going until you are close enough.

A program does the same. Forward kinematics is its mirror: it says where the
gripper is for any set of joint angles. The **Jacobian** is its experience: it
says which way the gripper moves when each joint turns. Inverse kinematics is
often shortened to **IK**, and this page uses that short form from here on.

---

## 2. How it works

The steps below go in the order the program runs them.

### Step 1: measure the miss

The program starts from a guess for the joint angles. On a real robot the guess
is usually the arm's current angles. Here it is `q1 = 0°`, `q2 = 30°`, the same
guess Book 1 uses.

It runs forward kinematics on the guess to find where the gripper is. Then it
subtracts that from the target. The result is the **miss**: an arrow from the
gripper to the target, with an `x` part and a `y` part. Its length is how far off
the gripper is. For the first guess the length is 3.287 m.

### Step 2: the Jacobian

The Jacobian is a small table with one column per joint. Each column says how
far the gripper moves, in `x` and in `y`, when that joint turns by one radian. It
only holds for small turns, and it changes as the arm moves, so the program
works it out again at every step.

Book 1 finds each column by turning one joint a millionth of a radian and seeing
where the gripper goes. For this arm there is also a short formula. At
`(30°, 60°)` the table is:

```
                 joint 1    joint 2
gripper x:       -3.500     -2.000
gripper y:        2.598      0.000
```

Read the first column as: turning joint 1 by a small amount `a` radians moves the
gripper `-3.5 a` in `x` and `2.598 a` in `y`. Joint 1 swings the whole arm, so the
gripper moves at right angles to the line from the base. Joint 2 only swings the
last link, so the gripper moves at right angles to that link.

![The two columns of the Jacobian drawn at the gripper, for a bent arm and a nearly straight one](../../../images/planning-and-search/numerical-inverse-kinematics/jacobian-columns.svg)

On the left, with the elbow at 60°, the two columns point in clearly different
directions, so together they can move the gripper any way; on the right, with the
elbow at 5°, both point almost the same way, and neither moves the gripper along
the arm.

### Step 3: turning the Jacobian round

The Jacobian answers "if I turn the joints this much, where does the gripper
go?". IK needs the opposite: "to move the gripper along the miss, how much
should I turn the joints?". So the program solves this for the joint step
`dq`:

```
J · dq = miss
```

With two joints and two numbers in the miss, this is two equations with two
unknowns, and it has one answer as long as the columns point different ways.
Book 1 does this with `np.linalg.pinv`, the **pseudo-inverse**, which also works
when the table is not square. The
[NumPy page](../../../01_robotics-intro/01_python-and-numpy/02_numpy-intro.md#66-moving-an-arm-a-little-the-jacobian-and-pinv)
explains it.

One number tells you how easy the table is to turn round: its **determinant**.
For this arm it is `L1 · L2 · sin(q2) = 6 · sin(q2)`, as
[the arm movement overview](../../../03_frameworks/03_arm-movement/01_overview.md#5-the-one-calculation-underneath-everything)
shows. At `(30°, 60°)` it is 5.196. It is zero when the elbow is straight or
folded back. That pose is a **singularity**: a pose where the arm cannot move
its gripper in some direction, however fast the joints turn.

### Step 4: why the plain answer goes wild near a straight arm

The trouble starts before the singularity. As the elbow straightens, both columns
of the Jacobian point almost the same way, as the right-hand picture above shows.
Neither of them moves the gripper along the arm, towards or away from the base.
Asked to move that way, the plain answer asks for a huge turn.

The program tests this directly. It puts joint 1 at 0° and asks each method for
the step that moves the gripper 10 cm towards the base, for smaller and smaller
elbow angles.

![The joint step each method asks for as the arm straightens](../../../images/planning-and-search/numerical-inverse-kinematics/step-near-singularity.svg)

The red line is the plain inverse: its step grows as the elbow straightens, to
29.4° at an elbow of 10° and to 2946° at 0.1°, while the two damped lines shrink.

The table below gives some of the same numbers. Read each row as one elbow angle
and the size of the joint step, in degrees, that each method asks for.

| Elbow angle | Plain inverse | Damped, 0.5 | Damped, 1.0 |
| --- | --- | --- | --- |
| 30° | 9.6° | 5.50° | 2.42° |
| 10° | 29.4° | 3.85° | 1.07° |
| 2° | 147.3° | 0.89° | 0.22° |
| 0.1° | 2946.4° | 0.04° | 0.01° |

To pull the gripper in by 10 cm from a nearly straight arm, the true answer bends
the elbow to 23.44°. The plain inverse asks for eight full turns of the joints in
one step. Book 1 avoids this by capping every step at 30° per joint. A cap works,
but it is a blunt tool: it cuts the step to the same size whether the arm is near
a singularity or far from it.

### Step 5: damped least squares

Damped least squares asks a slightly different question. Instead of "which step
removes the whole miss?", it asks:

> Which step makes (the miss left over)² + λ² × (the size of the step)² as small as possible?

The first part wants the miss gone. The second part charges a price for every
bit of joint turn. The number `λ` (lambda) is the **damping**, and it sets the
price. Here it is measured in metres, because the miss is in metres.

When the arm is well bent, a small turn removes a lot of miss, so the price
hardly matters and the step is close to the plain answer. When the arm is nearly
straight, removing the miss along the arm would need a huge turn, so the price
wins and the step stays small. The method gives up, for now, on the direction
the arm cannot move in, and moves in the directions it can.

The answer has a short formula. `Jᵀ` is the Jacobian with rows and columns
swapped, and `I` is the table with 1 on the diagonal and 0 elsewhere:

```
dq = Jᵀ · (J · Jᵀ + λ² · I)⁻¹ · miss
```

With `λ = 0` this is the plain answer again. With a large `λ` it becomes a small
step along `Jᵀ · miss`, which is plain gradient descent on the squared miss,
called the **Jacobian transpose** method. Damped least squares sits between the
two. The same idea, a least-squares fit with a price on large answers, appears
in [least-squares fitting](../../04_fitting-and-estimation/02_most-used/01_least-squares-fitting.md).
The name **Levenberg–Marquardt** is used when the program also changes `λ` as it
goes, which step 7 shows.

### Step 6: a worked run

Here is damped least squares with `λ = 1.0`, from the guess `(0°, 30°)`. The
program has no step cap.

```
step  0: q1 =    0.00, q2 =   30.00, miss = 3.286921 m
step  1: q1 =   15.90, q2 =   74.83, miss = 0.727079 m
step  2: q1 =   26.98, q2 =   68.29, miss = 0.182858 m
step  3: q1 =   28.62, q2 =   63.47, miss = 0.074530 m
step  4: q1 =   29.40, q2 =   61.51, miss = 0.031999 m
step  5: q1 =   29.74, q2 =   60.67, miss = 0.014036 m
  ...
step 10: q1 =   30.00, q2 =   60.01, miss = 0.000245 m
  ...
step 17: q1 =   30.00, q2 =   60.00, miss = 0.000001 m
```

![The arm at every step of damped least squares, from the first guess to the target](../../../images/planning-and-search/numerical-inverse-kinematics/dls-steps.svg)

The palest arm is the first guess, each darker arm is one step later, and the
purple dots trace the gripper; the first two steps do most of the work.

It finds `(30°, 60°)`, the elbow-down answer, in 17 steps. From the guess
`(90°, -30°)` it would find the elbow-up answer instead, as Book 1 shows: the
loop finds the answer nearest its guess.

For comparison, here is the plain pseudo-inverse from the same guess, with no
step cap:

```
step  0: q1 =    0.00, q2 =   30.00, miss = 3.286921 m
step  1: q1 =  -22.84, q2 =  175.11, miss = 4.063828 m
step  2: q1 =   48.47, q2 =   94.32, miss = 2.202467 m
step  3: q1 =   15.40, q2 =   84.49, miss = 0.734723 m
step  4: q1 =   29.09, q2 =   63.83, miss = 0.089897 m
step  5: q1 =   29.94, q2 =   60.11, miss = 0.002675 m
step  6: q1 =   30.00, q2 =   60.00, miss = 0.000002 m
```

Its first step folds the elbow to 175°, almost flat against link 1, and the miss
gets *bigger*. It recovers, and it finishes sooner, in 7 steps. Near the answer,
the plain method is the fastest there is, because it removes the whole miss at
every step. Damped least squares gives up some of that speed to keep every step
safe.

![The miss at every step for three methods, on a reachable target and on one out of reach](../../../images/planning-and-search/numerical-inverse-kinematics/miss-per-step.svg)

On the left, the pseudo-inverse and damped least squares both reach a miss below
a micrometre, while the Jacobian transpose is still 3.2 cm off after 40 steps;
on the right, the target is out of reach, the damped method settles at the best
pose, and the pseudo-inverse jumps about.

### Step 7: a target out of reach, and choosing the damping

The target `(6, 0)` is 6 m from the base, and the arm is 5 m long. No answer
exists. The best the arm can do is point straight at it, with a miss of 1 m.

From the guess `(10°, 20°)`, damped least squares with `λ = 1.0` gets there in a
few steps and stays there: the arm straight, the miss 1.000 m. The plain
pseudo-inverse never settles. After 100 steps its miss is 7.171 m, and its joint
angles have wound up to hundreds of degrees.

The right damping is a trade. The table below shows what five values do. Read
each row as one value of `λ`: how many steps it takes to reach `(2.598, 3.5)`
from `(0°, 30°)`, and what it does when asked for the out-of-reach `(6, 0)`.

| Damping λ | Steps to reach the target | Out of reach, after 100 steps |
| --- | --- | --- |
| 0.05 | 7 | jumps about, miss near 7 m |
| 0.2 | 7 | jumps about, miss between 1.0 and 3.6 m |
| 0.5 | 10 | flips between two mirror poses, miss 1.175 m |
| 1.0 | 17 | settles straight, miss 1.000 m |
| 2.0 | 44 | settles straight, miss 1.000 m |

Small damping is fast when the target is easy and wild when it is not. Large
damping is safe and slow. The `λ = 0.5` row is worth a second look: it swaps
every step between `(11.56°, -30.9°)` and `(-11.56°, 30.9°)`, two poses with the
same miss. A program that only checks whether the miss is small would see a
steady 1.175 m and not notice that the arm is being told to swing back and forth.

The usual answer is to change the damping as the loop runs, which is the
**Levenberg–Marquardt** method. After a step that makes the miss smaller, the
program keeps the step and halves `λ`. After a step that makes the miss larger,
it throws the step away, doubles `λ` and tries again. Starting from `λ = 1.0`, it
reaches `(2.598, 3.5)` in 5 kept steps, and settles on the straight pose for
`(6, 0)` in 9.

The nearly-straight case shows the difference most clearly. Start the arm at
`(0°, 0.1°)`, almost straight, and ask for `(4.9, 0)`, 10 cm towards the base.
The answer is `(-9.34°, 23.44°)`.

- The plain pseudo-inverse gets there in 16 steps, but one step turns a joint by
  8634.9°. It ends at `(3230.66°, -5376.56°)`, which is the right pose after many
  full turns. A real joint with limits would have hit them on the first step.
- Damped least squares with `λ = 1.0` never turns a joint more than 0.9° in one
  step, but it needs 119 steps, because near the singularity it moves very
  cautiously.
- With `λ = 0.5` it needs 36 steps, with no step over 3.0°.
- Levenberg–Marquardt needs 8 kept steps.

### Step 8: more joints than the task needs

Add a third link, 1 m long, and ask only for the gripper's position, not its
angle. Now three joints meet two numbers, so the arm is **redundant**: it has
endless answers, as
[Book 1's section 5](../../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md#5-three-joints-endless-answers-and-how-to-pick-one)
explains. The Jacobian is now 2 rows by 3 columns, and the same formula still
works, because `J · Jᵀ` is still a 2 by 2 table.

Damped least squares with `λ = 0.5`, asked for `(3.464, 4)`:

```
from (0, 30, 0):   (21.01, 54.98,  3.66) in 9 steps, gripper angle 79.65
from (90, -30, 0): (77.16, -54.31, -5.51) in 8 steps, gripper angle 17.35
```

Both reach the point. They choose very different poses and gripper angles. The
loop does not pick "the best" answer. It picks one near the guess, with small
joint turns. When the gripper angle matters, you must add it to the miss as a
third number, and then the arm is no longer redundant.

A real six-joint arm works the same way with bigger tables. The miss has six
numbers: three for position and three for rotation. The Jacobian has six rows and
one column per joint. The page on
[rigid transforms](../../02_geometry-and-cameras/02_most-used/02_rigid-transforms.md) explains how
a rotation miss is written as three numbers.

### Pseudocode

The pseudocode below is the full loop, with Levenberg–Marquardt damping and joint
limits, written without any particular language.

```
function solve_ik(target, guess, damping, tolerance, max_steps, time_limit):
    q = guess
    miss = target - forward_kinematics(q)
    repeat until length(miss) < tolerance
                 or max_steps are used or time_limit has passed:
        J = jacobian(q)                                  # one column per joint
        step = J^T * inverse(J * J^T + damping^2 * I) * miss
        q_new = clamp(q + step, lower_limits, upper_limits)
        miss_new = target - forward_kinematics(q_new)
        if length(miss_new) < length(miss):
            q = q_new
            miss = miss_new
            damping = damping / 2                        # things are going well
        else:
            damping = damping * 2                        # too bold: be more careful
            if damping is very large: stop               # no step helps any more
    if length(miss) < tolerance: return q
    else: return "not found", q, length(miss)
```

Two things in the last lines matter. The loop must say when it failed, and how
far off it was. And "not found" is not the same as "no answer exists", which
section 4 comes back to.

---

## 3. Where it is used on a robot arm

**Turning a grasp into joint angles.** A grasp model or a detector gives a
gripper pose in the camera frame. The program moves it into the arm's frame and
calls IK. The result is the goal a planner then plans to. This is the most common
IK call in a pick-and-place program.

**Checking many grasps before moving.** A grasp model may offer 50 candidate
grasps. The program runs IK on each one, throws away the ones with no answer,
and scores the rest by how far the answer is from joint limits and from a
singularity. Book 3 describes this check in
[reaching and reachability](../../../03_frameworks/03_arm-movement/02_reaching-and-reachability.md#8-finding-out-before-you-commit).

**Straight-line moves.** To move the gripper straight down onto a part, the
program splits the line into small steps and calls IK at each one, seeded with
the answer from the step before. MoveIt's Cartesian path function works this way.
Near a singularity the IK step fails, and the line stops short, as
[planning a path](../../../03_frameworks/03_arm-movement/03_planning-a-path.md#5-cartesian-paths-and-what-they-are-not)
warns.

**Jogging and following.** When an operator jogs the gripper with a joystick, or
the arm follows a moving target seen by the wrist camera, the program runs one
step of this loop every control cycle, for example 500 times a second. The miss
is replaced by the wanted gripper velocity, and damped least squares keeps the
joints from spinning up when the arm passes near a singularity. In ROS 2,
MoveIt Servo does this job; it slows the motion down as the arm nears a
singularity.

**Pointing a camera.** To look at a point on the table with a wrist camera, the
miss is "how far the camera's centre line is from the point". That is only two
numbers, so a six-joint arm has spare joints, and the loop picks a pose near the
current one.

**Finishing a learned guess.** A learned IK model gives an answer that is close
but not exact. The numerical loop, seeded with that answer, finishes the job in
a step or two. Book 6 describes this in
[learned motion planners](../../../06_neural-network-models/05_movement-models/03_also-used/02_learned-motion-planners.md#5-learned-inverse-kinematics).

**Inside other planners.** Trajectory optimisation turns an obstacle push on a
point of the arm into joint turns with the same Jacobian, as
[trajectory optimisation](03_trajectory-optimisation.md#step-6-the-same-thing-for-a-real-arm)
explains.

---

## 4. Where it works, and where it does not

The table below lists the common failures. Read each row as one failure: what
causes it, the sign you would see, and what people do about it.

| Failure | The sign you would see | What people do |
| --- | --- | --- |
| Near a singularity, with no damping | a joint jumps hundreds of degrees in one step, or the arm lurches | damped least squares, or Levenberg–Marquardt |
| Target out of reach | the loop uses all its steps and the miss stays the same | check reach first; report the final miss, not just "failed" |
| Damping too low for a hard target | the miss jumps up and down, or two poses swap every step | raise the damping, or change it as you go |
| Damping too high | many steps, and the solver times out on targets it should reach | lower the damping, or change it as you go |
| A joint limit in the way | the answer is clamped at a limit and the miss stops shrinking | restart from other guesses |
| The guess is on the wrong side | an answer is found, but with the elbow or wrist the other way | seed with the current angles; try several seeds and pick the nearest |
| A time limit that is too short | "no solution" for a pose that does have one | raise the limit when surveying; try several seeds |
| Only one answer returned | the planner fails later, because that pose leads nowhere | an analytic solver, or several seeds, to list the choices |

The time limit row deserves a sentence of its own. MoveIt's default solver, KDL,
stops after 0.05 seconds. As
[reaching and reachability](../../../03_frameworks/03_arm-movement/02_reaching-and-reachability.md#81-the-solvers-answer-is-weaker-than-it-looks)
explains, "unreachable" from such a solver means "not found in 50 ms from these
guesses". That is why TRAC-IK runs two solvers at once and takes whichever
answers first, and why many programs try several random guesses.

---

## 5. Libraries that provide it

The table below lists well-known libraries. Read each row as one library: the
languages you can call it from, the function or class, and a note.

| Library | Languages | Function or class | Note |
| --- | --- | --- | --- |
| KDL (Orocos Kinematics and Dynamics Library) | C++, Python | `ChainIkSolverPos_NR`, `ChainIkSolverPos_LMA`, `ChainIkSolverVel_pinv`, `ChainIkSolverVel_wdls` | Newton steps, Levenberg–Marquardt, pseudo-inverse and weighted damped least squares |
| MoveIt 2 | C++, Python | `kdl_kinematics_plugin/KDLKinematicsPlugin` | the default IK plugin, set in `kinematics.yaml` |
| TRAC-IK | C++ | `TRAC_IK::TRAC_IK` | runs a Newton solver and an optimisation solver together; a drop-in MoveIt plugin |
| pick_ik | C++ | a MoveIt kinematics plugin | the maintained modern alternative inside MoveIt |
| Pinocchio | C++, Python | `computeFrameJacobian`, `integrate` | gives you the pieces; you write the damped loop, as in the pseudocode |
| Drake | C++, Python | `InverseKinematics` | IK as an optimisation, with extra constraints such as collision distance |
| Robotics Toolbox for Python | Python | `ik_LM` on a robot model | Levenberg–Marquardt; good for learning and teaching |
| ikpy | Python | `Chain.inverse_kinematics` | reads a URDF; small and easy to try |
| cuRobo | Python | `IKSolver` | thousands of IK problems at once on an NVIDIA graphics card |
| NumPy, Eigen | Python, C++ | `np.linalg.solve`, `np.linalg.pinv`; Eigen's matrix decompositions | enough to write the loop yourself, as the diagram script does |

For a ROS 2 arm, start with the solver MoveIt already uses, and switch to TRAC-IK
or pick_ik if it fails on poses you know are reachable. Write your own loop when
you need it inside a control cycle, or when the miss is not a pose at all, as in
the camera-pointing example.

---

## 6. Why numerical inverse kinematics, and what it costs

This section answers the four questions: what it is, what it does for you, why
it rather than the obvious alternative, and what it costs.

It is a loop that finds joint angles for a target by repeatedly measuring the
miss and correcting it with the Jacobian. Damped least squares is the version
that stays calm near singularities and when the target is out of reach. It gives
you joint angles for any arm that has forward kinematics, whatever its shape, and
for any kind of target you can write as a miss.

The obvious alternative is an analytic solver: a formula worked out for one arm
design, like the triangle formula in Book 1. Tools such as IKFast generate such
formulas automatically for many six-joint arms. A formula is faster, it lists
every answer, and it says for certain when there is none. Book 1 measured it at
about 332 times faster on this arm. So why use a loop? Because many arms have no
formula: arms with seven joints, arms whose wrist axes do not meet at one point,
and any arm whose task is not a plain pose. The loop needs only forward
kinematics, so the same code serves every arm.

The costs are these. The loop finds one answer, the one nearest its guess, and
does not tell you others exist. It needs a sensible guess. It is slower than a
formula, and its time is not fixed: easy targets take a few steps, hard ones may
run out of time. It cannot tell "no answer exists" from "not found yet". And it
has settings, the damping and the time limit, whose right values depend on the
arm and the task. Damped least squares removes the worst failure, the wild jump
near a singularity, at the price of slower progress near one.

---

## 7. The learned alternative

A learned IK solver, described in Book 6's
[learned motion planners](../../../06_neural-network-models/05_movement-models/03_also-used/02_learned-motion-planners.md#5-learned-inverse-kinematics),
is a network trained on many pairs of joint angles and the gripper poses forward
kinematics gives for them. It answers in one pass, and some, such as IKFlow, give
many different answers at once, which helps when a seven-joint arm needs a choice
of poses. But its answer is close, not exact, so it is used as the starting guess
for this loop, which finishes the job in a step or two, as section 3 showed. For
one target at a time, the loop alone is still the usual choice, because it is
exact, needs no training, and works on a new arm without retraining. A
[learned arm model](../../../06_neural-network-models/08_touch-and-body-models/03_also-used/02_learned-arm-models.md#34-calibration)
does a different job: it learns the small bends and gear play that make the real
tool miss the pose that forward kinematics predicts.

---

## 8. Where to read next

- [Trajectory optimisation](03_trajectory-optimisation.md) uses the same step-by-step
  lowering of a cost for a whole path instead of one pose.
- The [planning and search overview](../01_overview.md) places this technique among
  the others in the chapter.
- [Least-squares fitting](../../04_fitting-and-estimation/02_most-used/01_least-squares-fitting.md)
  explains the least-squares idea that damped least squares is built on.
- [Rigid transforms](../../02_geometry-and-cameras/02_most-used/02_rigid-transforms.md) explains
  the poses and rotations that a full six-number miss is made from.
- [PID control](../../07_control-and-motion/02_most-used/01_pid-control.md) is what turns the joint
  angles this page finds into motor commands.
- Book 1 has the formula method and the first version of this loop in
  [inverse kinematics](../../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md).
- Book 3 covers singularities in
  [reaching and reachability](../../../03_frameworks/03_arm-movement/02_reaching-and-reachability.md#3-singularities-and-what-the-controller-does-at-one),
  and the libraries in
  [tools and libraries](../../../03_frameworks/01_tools-and-libraries.md#8-kinematics-and-maths-kdl-pinocchio-and-scipy).
