# System identification: measuring the numbers a model needs

This page explains system identification: finding the numbers inside a physical
model of the arm from measurements of the arm itself. Examples are a joint's
friction, the mass of the part in the gripper, and the stiffness of a springy
finger. It answers five questions. How do you move the arm so that the data can
tell the numbers apart? How do you fit them? How do you follow a number that
drifts over time? How sure can you be of each number? And which end of that
range should the arm act on?

It is for a reader who has read the page on
[least-squares fitting](../02_most-used/01_least-squares-fitting.md). That page
explains parameters, residuals and the least-squares solve, and this page uses
all three. The part on drifting numbers also uses one idea from the
[Kalman filter](../02_most-used/03_kalman-filter.md) page. Every number on this
page comes from a real run of the diagram script,
`docs/diagrams/fitting_and_estimation_2.py`.

## Contents

1. [What this page answers](#1-what-this-page-answers)
2. [The idea in one sentence](#2-the-idea-in-one-sentence)
3. [How it works, step by step](#3-how-it-works-step-by-step)
   · [Write the model so the numbers sit on their own](#write-the-model-so-the-numbers-sit-on-their-own)
   · [Design the probe move](#design-the-probe-move)
   · [Fit by least squares](#fit-by-least-squares)
   · [How sure you are: error bars](#how-sure-you-are-error-bars)
   · [Carrying error bars through a formula, and a Monte Carlo check](#carrying-error-bars-through-a-formula-and-a-monte-carlo-check)
   · [Act on the cautious end](#act-on-the-cautious-end)
   · [Numbers that drift: recursive least squares with forgetting](#numbers-that-drift-recursive-least-squares-with-forgetting)
   · [The steps as pseudocode](#the-steps-as-pseudocode)
4. [Where it is used on a robot arm](#4-where-it-is-used-on-a-robot-arm)
5. [Where it is useful, and where it is not](#5-where-it-is-useful-and-where-it-is-not)
6. [Libraries that provide it](#6-libraries-that-provide-it)
7. [Why system identification, and what it costs](#7-why-system-identification-and-what-it-costs)
8. [Where to read next](#8-where-to-read-next)

---

## 1. What this page answers

A controller, a planner or a simulator uses a model of the arm. A **model** here
means a set of equations, such as "the torque a joint needs is its friction plus
the weight it lifts". The equations have numbers in them: a friction value, a
mass, a distance, a stiffness. The equations come from physics and are usually
right. The numbers are usually not known well.

A datasheet gives a typical value, not the value for your arm. Friction changes
from one gearbox to the next, and it falls as the gearbox warms up. The mass of
the part in the gripper changes with every pick. A rubber finger pad gets softer
with wear.

System identification means measuring these numbers on the real arm. You move
the arm in a planned way, record what happens, and fit the numbers so that the
model's equations match the recording. The result is a model that describes
your arm today, plus an error bar that says how far each number might be off.

---

## 2. The idea in one sentence

**Move the arm so that each unknown number has a visible effect, record the
result, fit the numbers by least squares, and state how sure you are of each
one.**

Here is an everyday example. You want to know how much a suitcase weighs and
how much the wheels drag, but you have only a luggage scale that measures how
hard you pull. If you pull it at one steady walking speed, you learn only the
total pull. You cannot say how much of it is drag that grows with speed, and how
much is a fixed amount of rubbing. So you pull it slowly, then quickly, then
slowly the other way. Now the two effects show up differently, and you can
separate them. Choosing those different speeds is the probe move. Working out
the two numbers from the pulls is the fit.

---

## 3. How it works, step by step

The worked example follows one joint of a small arm. The joint needs torque to
overcome friction. Torque is the turning force a motor gives, measured in
newton-metres (N m). Most arm motors report their torque, or a current that is
proportional to it.

### Write the model so the numbers sit on their own

A common model of joint friction has two parts.

- **Viscous friction** grows in step with speed, like stirring honey. Its
  number is `b`, in newton-metres per radian per second.
- **Coulomb friction** is a fixed amount of rubbing that always opposes the
  motion, whatever the speed. Its number is `c`, in newton-metres. It is named
  after Charles-Augustin de Coulomb, who studied rubbing surfaces.

Written out, the torque at a steady speed `w` (in radians per second) is:

```
torque = b × w + c × sign(w)
```

Here `sign(w)` is +1 when the joint turns one way and −1 when it turns the
other way.

The important point is that the unknowns `b` and `c` are each multiplied by
something you know. So each reading gives one row of a **linear** equation: a
known row `[w, sign(w)]` times the unknown pair `[b, c]` gives the measured
torque. Least squares solves exactly this kind of equation. Many physical models
can be written this way, even when the physics is bent. A payload's weight
enters an arm's torque as the mass times a known function of the joint angles.
The page on [arm dynamics](../../07_control-and-motion/02_most-used/03_arm-dynamics.md)
shows the full equations for a whole arm. The rows that multiply the unknowns
are often called the **regressor**.

### Design the probe move

The probe move is the motion you run to collect the data. People call the
quality of a probe move its **excitation**: how strongly it makes each unknown
number show up in the data.

The simulated joint has true values `b = 0.25` and `c = 0.40`. Its torque
readings scatter by 0.05 N m, which is the sensor noise. The picture below
compares two probe moves of 40 readings each.

![A rich probe that holds eight speeds in both directions, a poor probe that holds speeds near 1 rad/s in one direction, and the fitted friction values from 300 repeats of each](../../../images/fitting-and-estimation/system-identification/probe-moves.svg)

The rich probe (left) holds eight speeds, from −2 to +2 rad/s, five readings at
each. The poor probe (middle) holds speeds between 0.9 and 1.1 rad/s, all in one
direction. On the right, each probe was repeated 300 times with fresh noise, and
each repeat gave one fitted pair `(b, c)`.

The rich probe's answers sit in a small cloud around the true values. Its fitted
`b` ranged from 0.204 to 0.294 over the 300 repeats. The poor probe's answers
lie along a long thin line. Its fitted `b` ranged from −0.025 to 0.589, and one
answer even had negative friction, which is not possible.

The reason is simple. At a speed of about 1 rad/s, the torque is about `b + c`.
The poor probe measures that sum very well, but it cannot tell how the sum
splits between `b` and `c`. Every point along the line gives nearly the same
sum. The rich probe includes slow and fast speeds, so a change in `b` and a
change in `c` change the torques in different ways.

A number called the **condition number** measures this. It compares how well
the best-measured and the worst-measured combination of the unknowns are pinned
down. A value near 1 is ideal. The rich probe's rows have a condition number of
4.9. The poor probe's have 28.3. If the poor probe held exactly one speed, the
condition number would be infinite and the fit would have no single answer.

The rules for a good probe follow from this.

- Make each unknown change the readings in its own way. For friction, use slow
  and fast speeds, in both directions.
- Cover the range the arm will use. A number fitted from slow moves may be wrong
  for fast ones.
- Keep the probe safe: stay inside the joint limits, the speed limits and the
  workspace, and start gently.
- Check the condition number of the rows before running the probe on the arm.
  It needs only the planned speeds, not the readings.

### Fit by least squares

With the rows and the readings in hand, the fit is one least-squares solve, as
the [least-squares page](../02_most-used/01_least-squares-fitting.md) explains.
One real run of the rich probe gave readings such as −0.940 N m at −2 rad/s,
0.489 N m at 0.5 rad/s and 0.880 N m at 2 rad/s. The fit gave:

- `b = 0.2285` N m per rad/s (true value 0.25)
- `c = 0.4205` N m (true value 0.40)

The residuals, the gaps between each reading and the fitted curve, have a spread
of 0.043 N m. That is close to the sensor's true noise of 0.05 N m. It is a sign
that the model has the right shape: nothing is left over except noise.

The picture below shows the 40 readings and the fitted curve.

![Forty torque readings at eight speeds, the fitted friction curve with a jump at zero speed, and a narrow band showing how sure the fit is](../../../images/fitting-and-estimation/system-identification/friction-fit.svg)

The slope of each half of the curve is `b`. The jump where the speed crosses
zero is `2 × c`, because the rubbing flips direction. The pale band around the
curve shows two spreads of the fit's uncertainty. The next part explains where
that band comes from.

### How sure you are: error bars

An **error bar** is the spread of a fitted number: how far it would move if you
ran the same probe again with fresh noise. It comes almost free with a
least-squares fit, in three steps.

1. Estimate the sensor's noise from the residuals. Square them, add them up, and
   divide by the number of readings minus the number of unknowns. Here that is
   40 − 2 = 38. The square root is the 0.043 N m above.
2. Multiply that squared noise by the inverse of `AᵀA`, where `A` is the table
   of rows. The result is the **covariance** of the fitted numbers: a small table
   that gives each number's squared spread and how the numbers' errors are
   linked.
3. The square root of each number on the diagonal of the covariance is that
   number's error bar.

For the run above this gives `b = 0.229 ± 0.012` and `c = 0.421 ± 0.017`. Both
true values lie within two error bars of the fit. That is what an error bar of
one spread should do most of the time.

You can check the formula against the repeats in the probe picture. There, the
300 fitted values of `b` had a spread of 0.0148, and the formula predicts
0.0141. For the poor probe the repeats gave 0.1100 and the formula 0.1118. So the
formula is trustworthy, and it also tells you in advance that the poor probe is
eight times less sure.

The covariance also shows a link. The errors of `b` and `c` have a correlation of
−0.91: when `b` comes out too high, `c` usually comes out too low. This matters
when you use both numbers together. The torque the joint needs at 1.5 rad/s is
`1.5 × b + c` = 0.763 N m. Its error bar, worked out with the link, is only
0.0075 N m. If you ignore the link and treat the two errors as separate, you get
0.025 N m, more than three times too cautious. The fit knows the total torque at
the speeds it measured far better than it knows either number alone.

### Carrying error bars through a formula, and a Monte Carlo check

Often the number you need is not the fitted number itself, but something worked
out from it. Carrying an error bar through a formula is called **error
propagation**.

Here is an example. The arm holds a part still with its forearm level. The elbow
motor reports an extra torque of 1.20 N m, with a spread of 0.04 N m. The part's
centre sits 0.150 m from the elbow axis, with a spread of 0.006 m, because the
grasp is never in exactly the same place. The part's mass is:

```
mass = torque / (g × distance) = 1.20 / (9.81 × 0.150) = 0.815 kg
```

For a formula made only of multiplying and dividing, there is a simple rule: the
**relative** spreads (spread divided by value) add in squares.

```
torque:   0.04 / 1.20  = 0.033
distance: 0.006 / 0.150 = 0.040
mass:     square root of (0.033² + 0.040²) = 0.052
```

So the mass is 0.815 kg with a spread of 5.2%, which is 0.043 kg. Notice that
the distance, not the torque, is the larger source of doubt. To improve the
answer, measure the grasp position better, not the torque.

The rule is exact only for a straight-line formula, and a division is not
straight. A **Monte Carlo check** tests it by brute force. You draw many random
torques and distances, each from its own bell curve, work out the mass for every
pair, and look at the spread of the results. The name comes from the casino in
Monaco, because the method runs on random numbers.

![A histogram of 20000 Monte Carlo masses, the bell curve the formula predicts on top of it, the best value 0.815 kg and the cautious end 0.900 kg](../../../images/fitting-and-estimation/system-identification/error-bars-and-cautious-end.svg)

The picture above shows 20 000 such samples. They have an average of 0.817 kg and
a spread of 0.0427 kg, against 0.815 kg and 0.0425 kg from the rule. The bell
curve from the rule sits on top of the histogram. So the rule is good enough
here. If the two had disagreed, for example because a spread was large compared
with its value, you would trust the Monte Carlo result.

### Act on the cautious end

A fitted number with an error bar is a range, not a point. The arm still has to
make one decision. The safe habit is to act on the end of the range that fails
gently if you are wrong. That is called the **cautious end**.

For the payload, a heavier part is the dangerous case. It needs more torque to
stop, takes longer to brake and puts more load on the gripper. So the planner
should use the upper end. With two spreads, that is 0.815 + 2 × 0.043 = 0.900 kg.
In the Monte Carlo run, only 3.1% of the samples lay above 0.900 kg.

Which end is cautious depends on the decision, not on the number.

- **Payload mass for a speed limit or a lift check:** use the upper end.
- **Friction for feed-forward.** Feed-forward means adding the torque the
  model says friction will take, so the controller does not have to wait for an
  error to build up. Too much added torque makes the joint push itself when it
  should stop, or shake around the target. So use the lower end of `c`.
- **Stiffness of a springy finger, to limit squeezing force:** the force is the
  stiffness times the squeeze distance. To stay under a force limit, work out
  the distance from the upper end of the stiffness.

When the cautious end is too costly, for example when the upper-end payload is
over the arm's limit but the best value is not, the answer is to measure better.
Run a longer probe or measure the grasp position, rather than hoping.

### Numbers that drift: recursive least squares with forgetting

Some numbers change while the arm works. A gearbox's friction falls as it warms
up over the first twenty minutes. Running the probe again and again stops the
arm's real work. Instead, the arm can refine the numbers from its normal moves,
one reading at a time.

**Recursive least squares (RLS)** does this. It keeps the current fitted
numbers and a covariance table `P`, like a Kalman filter. Each new reading
nudges the numbers towards it, by an amount that depends on `P`. With no
forgetting, the answer after all the readings is the same as a batch
least-squares fit over all of them. The
[Kalman filter](../02_most-used/03_kalman-filter.md) page explains the same
predict-and-correct idea; RLS is that filter for numbers that are meant to
stay constant.

A number that stays constant is the wrong assumption for friction that drifts.
Plain RLS weighs a reading from twenty minutes ago as much as the latest one.
A **forgetting factor**, written `λ` (the Greek letter lambda), fixes this. It
is a number just below 1. At each step, all older readings count `λ` times as
much as before. The filter then remembers roughly the last `1 / (1 − λ)`
readings. A factor of 0.98 remembers about 50 readings.

The picture below runs RLS on 600 readings, one every 2 seconds, taken during
normal moves at speeds between 0.3 and 2 rad/s in both directions. The true `b`
is 0.30 for the first 150 readings, falls steadily to 0.20 by reading 450, and
then stays there.

![Recursive least squares estimates of viscous friction over 600 readings for forgetting factors 1, 0.98 and 0.90, against a true value that falls from 0.30 to 0.20](../../../images/fitting-and-estimation/system-identification/forgetting-factor.svg)

Three settings behave very differently.

- **Factor 1, never forgets (red).** It is smooth, but it trails far behind. At
  reading 600 it says 0.258, while the true value is 0.200. Over the last 150
  readings it is 0.063 too high on average.
- **Factor 0.98 (orange).** It follows the fall with a short lag. At reading 600
  it says 0.207. Over the last 150 readings it is 0.017 too high on average, with
  a shake of 0.010.
- **Factor 0.90 (pale blue).** It remembers only about 10 readings. It follows
  fastest, but it shakes: a spread of 0.022 over the last 150 readings, more than
  twice that of 0.98.

This is the same trade as the process noise `q` in a Kalman filter. Forgetting
fast follows changes but passes on more noise. Choose `λ` from how quickly the
real number can change compared with how often readings arrive.

### The steps as pseudocode

The first function is the batch fit with error bars. The second is one step of
recursive least squares. Here `row` is the known row for one reading, such as
`[w, sign(w)]`, and `·` is a dot product or matrix product.

```
function fit_with_error_bars(rows A, readings y):
    numbers   = solve (transpose(A) · A) · numbers = transpose(A) · y
    residuals = y − A · numbers
    noise²    = sum(residuals²) / (count(y) − count(numbers))
    covariance = noise² · inverse(transpose(A) · A)
    error_bars = square root of each diagonal entry of covariance
    return numbers, covariance, error_bars

function rls_step(numbers, P, row, reading, lam):
    predicted = row · numbers
    gain      = P · row / (lam + row · P · row)
    numbers   = numbers + gain × (reading − predicted)
    P         = (P − gain · transpose(row) · P) / lam
    return numbers, P

function monte_carlo_spread(formula, inputs with spreads, count):
    results = empty list
    repeat count times:
        draw each input from its own bell curve
        add formula(drawn inputs) to results
    return average(results), spread(results)
```

Start RLS with `numbers` at a rough guess and `P` large, such as 100 times the
identity table, which says "I know almost nothing yet".

---

## 4. Where it is used on a robot arm

System identification appears wherever a model's numbers decide how the arm
moves or what it believes.

- **Joint friction for feed-forward.** Friction numbers let a
  [PID controller](../../07_control-and-motion/02_most-used/01_pid-control.md)
  add the torque friction will take, so a slow move does not stick and then jump.
- **Payload identification after a grasp.** The arm holds the part still in two
  or three poses and fits its mass and the position of its centre from the joint
  torques. A mass that is far from the expected one means the wrong part, or two
  parts, or a slipping grasp.
- **The full arm's masses for a model-based controller.** Each link's mass,
  centre and inertia enter the equations of
  [arm dynamics](../../07_control-and-motion/02_most-used/03_arm-dynamics.md)
  linearly, so a rich probe that moves all joints together can fit them all at
  once.
- **Collision detection.** A monitor compares the torque the model expects with
  the torque the motors report, and stops the arm when the gap is too large. A
  poorly identified model needs a wide margin, which makes the monitor slow to
  notice a real collision. The page on
  [safety monitoring](../../07_control-and-motion/02_most-used/04_safety-monitoring.md)
  covers the monitor.
- **Stiffness of a springy finger or a force-controlled contact.** Pressing a
  finger or a tool on a known surface at a few depths and fitting force against
  depth gives the stiffness that
  [impedance and force control](../../07_control-and-motion/03_also-used/01_impedance-and-force-control.md)
  needs.
- **Contact and friction with the table.** A robot that pushes objects can fit
  the table's friction from push after push. The sibling repo's
  [contact-parameters page](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/docs/problem-3/solutions/09-identify-the-contact-parameters.md)
  does this, and moves on to recursive least squares.
- **Making a simulator match the real arm.** Fitting a simulator's masses,
  friction and motor delays to recordings from the real arm narrows the gap
  between simulation and reality. Book 3's page on
  [simulation and evaluation](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md)
  describes MuJoCo's system identification toolbox for this.
- **Camera placement.** Finding where a camera sits on the arm is also
  identification: a geometric model with unknown numbers, fitted from a probe of
  many arm poses. The [calibration](../../02_geometry-and-cameras/02_most-used/03_calibration.md)
  page covers it, and the same rule applies: vary the poses so every unknown
  shows up.

---

## 5. Where it is useful, and where it is not

System identification works best when the physics is known and only the numbers
are not, the numbers can be written so they multiply known quantities, and the
arm can be moved safely through a probe.

The table below lists the ways it goes wrong. Each row gives the cause, the sign
you would see, and what people use instead.

| What goes wrong | The sign you would see | What to use instead |
| --- | --- | --- |
| The probe does not excite every number | huge error bars; numbers that change a lot between runs; impossible values such as negative friction | a richer probe; check the condition number before running it |
| The model is missing an effect (sticking at very low speed, gear play, a cable that pulls) | the residuals show a pattern, not random scatter; their spread is larger than the sensor's noise | add the missing term; or fit only the speed range the model describes; or add a learned correction |
| Speed and torque readings are out of step in time | the fit changes when the probe changes speed quickly; hysteresis loops in a torque-speed plot | line the readings up in time first; see [sensor streams](../02_most-used/04_sensor-streams.md) |
| Forgetting while the arm stands still | the covariance `P` grows every step; the numbers jump on the first move after a pause | update only while the arm moves enough; put a ceiling on `P` |
| Forgetting factor too small | the numbers shake from reading to reading | raise `λ`; or run a slower filter on the numbers |
| Rare large readings (a bump, a missed sample) | one reading moves the fit a long way | throw away readings with a large residual, as [RANSAC](../02_most-used/02_ransac.md) does for points |
| The number depends on something you did not vary (temperature, load, pose) | a model that fits the probe well and the real task badly | probe under the task's conditions; or track the number with RLS |
| Physics too complex to write down (cloth, a soft object, a tangled cable) | no small set of numbers fits | a learned model; see [learned arm models](../../../06_neural-network-models/08_touch-and-body-models/03_also-used/02_learned-arm-models.md) |

---

## 6. Libraries that provide it

For a model written as rows times unknowns, the fit is one call to a
least-squares routine. The libraries below cover the fit, the full-arm rows, the
error bars and the drift. Each row gives the library, the languages it is used
from, the function, class or feature, and a note.

| Library | Languages | Function, class or feature | Note |
| --- | --- | --- | --- |
| NumPy | Python | `numpy.linalg.lstsq`, `numpy.linalg.inv`, `numpy.linalg.cond` | the fit, the covariance and the condition number, as in this page's script |
| SciPy | Python | `scipy.optimize.curve_fit`, `scipy.optimize.least_squares` | `curve_fit` returns the covariance with the fit; both handle models that are not rows times unknowns |
| Pinocchio | C++, Python | `computeJointTorqueRegressor` | builds the rows for a whole arm's masses and inertias from its description file |
| MuJoCo | Python | system identification toolbox (from version 3.5.0) | fits a simulator's parameters to recorded trajectories; see Book 3's [simulation page](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md) |
| MATLAB System Identification Toolbox | MATLAB | a whole toolbox | a long-standing commercial tool, strong on probe design and model checking |
| uncertainties | Python | `ufloat` | carries error bars through a formula automatically, using the straight-line rule |
| padasip | Python | `FilterRLS` | recursive least squares with a forgetting factor |

Recursive least squares itself is about ten lines, and many projects write it
themselves, as in the pseudocode above.

---

## 7. Why system identification, and what it costs

System identification measures the numbers in a physical model of the arm by
running a planned probe, fitting the numbers by least squares, and stating an
error bar for each. It gives the arm a model that matches this arm today, and a
range that says how far to trust it.

The obvious alternative is to **use the datasheet or the design files**. It
costs nothing and needs no arm time. But a datasheet gives a typical value, and
friction in particular varies from unit to unit and with temperature by tens of
percent. A payload's mass and grasp position are not in any datasheet at all.
And a datasheet value comes with no error bar, so the arm cannot tell whether it
is safe to act on.

A second alternative is to **learn the whole model with a neural network**, as
Book 6's [learned arm models](../../../06_neural-network-models/08_touch-and-body-models/03_also-used/02_learned-arm-models.md)
page describes. It can capture effects no textbook equation has. But it needs
far more data, its internal numbers have no physical meaning you can check, and
it can behave oddly in poses it has not seen. That page itself recommends
identifying the physics model first and learning only what is left over.

A third alternative, used for simulators, is **domain randomisation**: training
across many random guesses of the numbers so that the real arm falls somewhere
inside. It avoids measuring, but wide random ranges make the result more
cautious than it needs to be. Identifying the numbers first lets you randomise
only over the real error bars.

The costs are these. You need a model with the right terms, and the fit cannot
find an effect the model leaves out. The probe takes time on the real arm, and
it must be designed to be safe as well as rich. The numbers go stale as the arm
wears, warms or picks up a new tool, so you must re-run the probe or track the
numbers with RLS. And a tracker with forgetting must be guarded, because it can
drift or jump when the arm stands still.

---

## 8. Where to read next

- [Least-squares fitting](../02_most-used/01_least-squares-fitting.md) explains
  the solve that every fit on this page uses.
- The [Kalman filter](../02_most-used/03_kalman-filter.md) is the same
  predict-and-correct loop as recursive least squares, for quantities that move.
- [Sensor streams](../02_most-used/04_sensor-streams.md) covers lining readings
  up in time and filtering them, which a fit needs before it starts.
- [Arm dynamics](../../07_control-and-motion/02_most-used/03_arm-dynamics.md)
  gives the full equations whose masses and friction this page measures.
- [Impedance and force control](../../07_control-and-motion/03_also-used/01_impedance-and-force-control.md)
  uses identified stiffness and payload values.
- [Uncertainty and confidence](../../../06_neural-network-models/01_what-models-are/06_uncertainty-and-confidence.md)
  in Book 6 covers error bars for learned models.
- The [chapter overview](../01_overview.md) shows how this page fits with the
  others in the chapter.
