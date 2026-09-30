# The Kalman filter

This page explains the Kalman filter: a way to keep a running estimate of a
quantity that is measured again and again with noise, such as the distance to a
table or the position of a part on a moving belt. It answers four questions.
What do the two steps, predict and update, do? How much should each new reading
be trusted? Where does a robot arm use the filter? And what makes it go wrong?

It is for a reader who has read the page on
[least-squares fitting](02_least-squares-fitting.md), or who knows what an
average and a spread of readings are. The page starts with a single number and
moves to a position on a table. Every number on this page comes from a real run
of the diagram script, `docs/diagrams/fitting_and_estimation.py`.

The filter is named after Rudolf Kálmán, who published it in 1960. It is used in
nearly every machine that moves and senses: phones, drones, cars and robot arms.
On an arm it appears most often in tracking objects the camera sees, and in
smoothing sensor readings.

## Contents

1. [What this page answers](#1-what-this-page-answers)
2. [The idea in one sentence](#2-the-idea-in-one-sentence)
3. [How it works, step by step](#3-how-it-works-step-by-step)
   · [What the filter keeps](#what-the-filter-keeps)
   · [Predict](#predict)
   · [Update](#update)
   · [A worked example: a block on a belt](#a-worked-example-a-block-on-a-belt)
   · [The steps as pseudocode](#the-steps-as-pseudocode)
   · [The two settings: sensor noise and process noise](#the-two-settings-sensor-noise-and-process-noise)
   · [Tracking a position and a speed together](#tracking-a-position-and-a-speed-together)
4. [Where it is used on a robot arm](#4-where-it-is-used-on-a-robot-arm)
5. [Where it is useful, and where it is not](#5-where-it-is-useful-and-where-it-is-not)
6. [Libraries that provide it](#6-libraries-that-provide-it)
7. [Why a Kalman filter, and what it costs](#7-why-a-kalman-filter-and-what-it-costs)
8. [Where to read next](#8-where-to-read-next)

---

## 1. What this page answers

Many readings on a robot arm come in a stream. A camera gives a picture 30 times
a second. A force sensor gives a reading 1000 times a second. Each reading is a
little wrong, and sometimes a reading is missing, for example when the arm's own
body hides an object from the camera.

The arm wants one steady value at each moment, not a shaking one. It also wants
to know how far that value might be off. And when the quantity is changing, such
as a part moving on a belt, it wants a value for the part's position now and a
guess for its position a moment from now.

The Kalman filter gives all three. It keeps an estimate and a measure of how
sure it is, and improves both each time a reading arrives. It can also run
without a reading, which lets it carry on through a short gap.

---

## 2. The idea in one sentence

**Before each new reading, predict where the quantity should be from how it was
moving; then move the prediction towards the reading by an amount that depends
on which of the two you trust more.**

Here is an everyday example. You are walking to a friend's house in the dark,
and you know you walk about one metre per step. After ten steps you think you
are about ten metres along, but you are not quite sure: each step could have
been a little long or short. Then you see a lamp post you know is at eleven
metres, but it is dark and you cannot judge exactly how far away it is. You do
not throw away your step count, and you do not ignore the lamp post. You settle
on something in between, closer to whichever you trust more. Then you carry on
counting steps from that new position.

Counting steps is the **predict** step. Looking at the lamp post is the
**update** step. The Kalman filter does exactly this, with numbers for "how
sure".

---

## 3. How it works, step by step

### What the filter keeps

The filter keeps two things at all times.

- The **estimate**: its best value for the quantity. For a part on a belt this
  could be its position in millimetres.
- The **variance**: how unsure it is about the estimate. The variance is the
  square of the **spread**, also called the standard deviation. A spread of
  5 mm means the true value is usually within about 5 mm of the estimate, and
  gives a variance of 25 mm².

Variances are used inside the filter because they add up simply. When two
independent uncertainties combine, their variances add. Spreads do not.

The filter also needs two numbers from you, both as variances.

- The **sensor noise**, written `r`: how much a single reading scatters. A
  camera whose positions scatter by 4 mm has `r = 16`.
- The **process noise**, written `q`: how much the quantity can change between
  readings in ways the prediction does not know about. A belt that runs at a
  nearly steady speed has a small `q`.

### Predict

In the predict step the filter moves its estimate forward to the time of the
next reading, using what it knows about how the quantity moves. If a belt
carries the part 5 mm between pictures, the predicted position is the last
estimate plus 5 mm.

The prediction is less certain than the last estimate, because the belt might
have slipped or sped up a little. So the variance grows by the process noise:

```
predicted estimate = last estimate + known change
predicted variance = last variance + q
```

### Update

In the update step a reading arrives. The filter compares it with the
prediction. The difference, reading minus prediction, is called the
**innovation**: it is the part of the reading the prediction did not expect.

The filter then moves the prediction part of the way towards the reading. The
share it moves is called the **Kalman gain**, written `K`, and it is a number
between 0 and 1:

```
K = predicted variance / (predicted variance + r)
new estimate = predicted estimate + K × (reading − predicted estimate)
new variance = (1 − K) × predicted variance
```

Read the gain like this. If the prediction is very unsure compared with the
sensor, `K` is close to 1 and the new estimate is almost the reading. If the
sensor is very noisy compared with the prediction, `K` is close to 0 and the
reading barely moves the estimate. The new variance is always smaller than both
the predicted variance and the sensor noise: combining two pieces of evidence
gives a result more certain than either one alone.

### A worked example: a block on a belt

A block rides on a conveyor belt at 50 mm per second. A camera takes 10 pictures
a second, so the block moves 5 mm between pictures. The camera's position
readings scatter by 4 mm, so `r = 16`. The belt is steady but not perfect, so
`q = 1`. The filter starts with an estimate of 100 mm and a spread of 5 mm, a
variance of 25.

Step 1 goes like this.

1. Predict: the estimate becomes 100 + 5 = 105 mm. The variance becomes
   25 + 1 = 26, a spread of 5.1 mm.
2. The camera reads 107 mm. The innovation is 107 − 105 = 2 mm.
3. The gain is 26 / (26 + 16) = 0.619.
4. The new estimate is 105 + 0.619 × 2 = 106.24 mm.
5. The new variance is (1 − 0.619) × 26 = 9.90, a spread of 3.15 mm.

The picture below shows this step as bell-shaped curves. Each curve's peak is at
the value, and its width is the spread.

![The last estimate, the prediction 5 mm further on, the measurement and the narrower updated estimate between them, drawn as bell curves](../../images/fitting-and-estimation/kalman-filter/predict-and-update.svg)

The prediction (blue) is the last estimate (dotted) moved 5 mm to the right and
made a little wider. The measurement (red) is narrower than the prediction,
because the camera's 4 mm spread is smaller than the prediction's 5.1 mm. So the
updated estimate (orange) lands closer to the measurement, and it is narrower
than either.

The table below lists all four steps of the same run. Each row is one picture.

| Step | Predicted (mm) | Predicted variance | Reading (mm) | Gain K | Updated (mm) | Updated spread (mm) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 105.00 | 26.00 | 107 | 0.619 | 106.24 | 3.15 |
| 2 | 111.24 | 10.90 | 109 | 0.405 | 110.33 | 2.55 |
| 3 | 115.33 | 7.48 | 118 | 0.319 | 116.18 | 2.26 |
| 4 | 121.18 | 6.10 | 121 | 0.276 | 121.13 | 2.10 |

Notice the gain falls from 0.619 to 0.276. As the filter becomes surer, each new
reading moves it less. After four readings the spread is 2.1 mm, about half the
spread of a single camera reading.

### The steps as pseudocode

The pseudocode below is the one-number filter used above. The known change per
step can be 0 for a quantity that should stay still.

```
function kalman_1d(readings, start_estimate, start_variance, q, r, change_per_step):
    x = start_estimate
    p = start_variance
    for each reading z in readings:
        # predict
        x = x + change_per_step
        p = p + q
        # update, only if a reading arrived
        if z is present:
            k = p / (p + r)
            x = x + k * (z - x)
            p = (1 - k) * p
        output x and p
```

For several numbers at once, such as a position and a speed, the same steps
use matrices. `x` becomes a list of numbers called the **state**, and `p`
becomes a table called the **covariance**, which also says how the errors of the
numbers are linked. `F` is the table that moves the state forward one step. `H`
picks out the part of the state that the sensor measures. `Q` and `R` are the
process and sensor noise as tables.

```
    # predict
    x = F · x
    P = F · P · transpose(F) + Q
    # update
    S = H · P · transpose(H) + R            # expected spread of the innovation
    K = P · transpose(H) · inverse(S)
    x = x + K · (z − H · x)
    P = (identity − K · H) · P
```

Each line matches a line of the one-number version. `S` plays the part of
`p + r`, and the rest follows the same pattern.

### The two settings: sensor noise and process noise

The sensor noise `r` can be measured: hold the sensor still and record the
spread of its readings. The process noise `q` is harder. It says how much the
quantity can change in ways the prediction does not model, and it sets how
quickly the filter follows real changes.

The picture below shows the difference. A depth camera on the wrist reads the
distance to the table, 400 mm, with a 4 mm spread, 10 times a second. After
3.5 seconds the arm lowers the camera by 20 mm. Two filters run on the same
readings, one with `q = 0.01` and one with `q = 4`.

![Noisy depth readings, a smooth filter that lags badly after a 20 mm drop, and a quicker filter that is noisier but follows the drop](../../images/fitting-and-estimation/kalman-filter/smoothing-a-reading.svg)

While the distance is steady, the filter with the small `q` is the smoother of
the two. From the 11th to the 35th reading its average error is 0.77 mm, against
1.67 mm for the other filter and 2.76 mm for the raw readings. But when the
camera drops, the small-`q` filter believes the distance cannot change, so it
drifts down very slowly. At the end of the run, 2.4 seconds later, it still
reads 388.7 mm, 8.7 mm too far. The filter with `q = 4` is within 5 mm of the new distance by
the second reading after the drop.

The next picture shows why, by plotting the gain and the spread over time for
the steady part.

![The Kalman gain and the spread of the estimate over 60 steps for the two process noise settings](../../images/fitting-and-estimation/kalman-filter/gain-settles.svg)

With `q = 0.01` the gain keeps falling: 0.5 at the first step, 0.168 at the
fifth, 0.093 at the tenth and 0.027 at the sixtieth. The filter trusts its own
estimate more and more, and each reading counts less. That is what makes it
smooth, and also what makes it slow to follow a real change. With `q = 4` the
gain settles at 0.39 within a few steps, and the spread settles at 2.5 mm. That
filter always gives each reading a fair share.

There is no single right `q`. Choose it from how fast the real quantity can
change. If you know the arm is about to move the camera, you can also tell the
filter so: the move is a known change, just like the belt's 5 mm per step.

### Tracking a position and a speed together

A part on a belt has a position and a speed. The camera measures only the
position, but the filter can estimate the speed too, by putting both in its
state. This is called a **constant-velocity** model: the predict step assumes
the part keeps its speed, and adds the speed times the time step to the
position. The update step corrects the position from the reading, and the
covariance links position and speed, so the speed is corrected too.

The picture below tracks a part moving across a belt at about 60 mm/s, with the
camera's positions scattering by 4 mm. For 0.8 seconds the arm reaches in and
hides the part, so there are 8 pictures with no reading.

![A part's true path, camera detections, the Kalman estimate that carries on through a gap in the detections, and uncertainty ellipses that grow during the gap](../../images/fitting-and-estimation/kalman-filter/tracking-through-a-gap.svg)

Before the gap, the filter has learned a speed of 58.7 mm/s along the belt and
16.8 mm/s across it. During the gap it keeps predicting with that speed. The red
ellipses show where the filter thinks the part could be. They grow during the
gap, because there are no readings to shrink them: the spread along the belt
rises from 2.0 mm to 5.0 mm. At the end of the gap the estimate is 3.6 mm from
the true position, close enough to match the next detection to the same part.
When readings return, the ellipses shrink again.

The same growing ellipse tells a tracker how far from the prediction a new
detection may be and still count as the same part. Book 2 explains this idea,
called **gating**, in
[tracking and association](../../02_perception/02_object-perception/10_tracking-and-association.md#33-a-predictor-constant-velocity-then-the-kalman-filter).

The Kalman filter as described here assumes the motion and the measurement are
straight-line relationships, like "position plus speed times time". Many real
problems are not. An object turning on a turntable, or a camera measuring an
angle and a distance, bends the relationship. The **extended Kalman filter
(EKF)** handles this by treating the bend as straight over one small step. The
**unscented Kalman filter (UKF)** handles it by pushing a few sample points
through the bent relationship. Both keep the same predict and update loop.

---

## 4. Where it is used on a robot arm

The filter appears in perception, sensing and the arm's own state.

- **Tracking objects the camera sees.** A tracker runs one filter per object.
  Each picture, it predicts every object forward, matches detections to the
  predictions, and updates each filter with its match. The
  [assignment and matching](../03_searching-and-matching/04_assignment-and-matching.md)
  page shows the matching step.
- **Picking from a conveyor.** The filter's speed estimate lets the arm aim for
  where the part will be when the gripper arrives, not where it was when the
  picture was taken.
- **Coasting through a missed detection.** When the arm hides a part, or the
  detector misses it for a frame, the filter keeps predicting. The growing
  spread tells the program when to give up on the track.
- **Smoothing a depth or force reading.** A wrist camera's distance to the
  table, or a force sensor's reading during a gentle push, is filtered before a
  controller acts on it. A [PID controller](../07_control-and-motion/02_pid-control.md)
  that acts on raw readings passes the noise straight to the motors.
- **Estimating a slowly changing constant.** A robot that pushes objects can
  estimate the table's friction from push after push. The sibling repo's
  [contact-parameters page](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/docs/problem-3/solutions/09-identify-the-contact-parameters.md)
  shows that for a constant, the Kalman filter becomes recursive least squares:
  the least-squares fit updated one reading at a time.
- **Joining sensors.** A mobile base with an arm on it combines wheel counts, an
  inertial measurement unit (IMU) and sometimes a camera into one position.
  The ROS package `robot_localization` does this with an EKF or a UKF.
- **Estimating joint speed.** An arm's encoders measure joint angles. A small
  filter per joint estimates the speed more smoothly than subtracting two
  angles and dividing by the time.

---

## 5. Where it is useful, and where it is not

The filter works best when you can say how the quantity moves from one moment to
the next, the noise is roughly bell-shaped and does not depend on the last
reading, and the readings arrive regularly with known times.

The table below lists the ways it goes wrong. Each row gives the cause, the sign
you would see, and what people use instead.

| What goes wrong | The sign you would see | What to use instead |
| --- | --- | --- |
| Process noise `q` too small | smooth but late; after a real change the estimate trails for seconds | raise `q`, or tell the filter about known changes such as arm moves |
| Process noise `q` too large | the estimate is nearly as noisy as the raw readings | lower `q`; check with a recording of the sensor held still |
| The object stops following the motion model (a person picks it up, it hits a stop) | the estimate carries on past where the object is; innovations are suddenly large | detect large innovations and restart the track; use several motion models side by side |
| A wrong detection is fed in (the wrong object, a reflection) | a sudden jump that then decays slowly | a gate that refuses readings too far from the prediction; see [tracking and association](../../02_perception/02_object-perception/10_tracking-and-association.md#33-a-predictor-constant-velocity-then-the-kalman-filter) |
| Irregular timing (dropped frames, late messages) | speed estimate jumps; prediction off by one frame | use each reading's real timestamp for the time step, not a nominal rate |
| Strongly bent relationships (angles, rotations) | the filter becomes over-confident and then drifts | EKF or UKF; for orientation, a filter built for rotations |
| Readings with rare large errors, not bell-shaped | one bad reading drags the estimate | a gate, or a robust filter that limits the pull of one reading |
| Motion too complex to write down (a cloth, a rolling object bouncing) | large innovations all the time | a learned motion model, such as a [learned dynamics model](../../06_neural-network-models/07_world-models/02_learned-dynamics-models.md) |

---

## 6. Libraries that provide it

The one-number filter is ten lines of code, and many projects write it
themselves. For more, the libraries below are well known. Each row gives the
library, the languages it is used from, the class or package, and a note.

| Library | Languages | Class or package | Note |
| --- | --- | --- | --- |
| OpenCV | C++, Python | `cv::KalmanFilter` | linear filter with the standard predict and correct steps |
| filterpy | Python | `filterpy.kalman.KalmanFilter`, `ExtendedKalmanFilter`, `UnscentedKalmanFilter` | readable code written alongside a free textbook on the subject |
| robot_localization | ROS 2 (C++) | `ekf_node`, `ukf_node` | joins wheel, IMU, GPS and pose readings into one position |
| GTSAM | C++, Python | factor graphs | a smoother that corrects past estimates as well as the current one; used for camera and robot position |
| Eigen | C++ | matrix types | the matrices to write your own filter with, as most C++ robotics code does |

---

## 7. Why a Kalman filter, and what it costs

The Kalman filter is a loop that predicts a quantity forward and then corrects
it with each new reading, weighting the two by how much each is trusted. It
gives the arm a steady value, a measure of how sure that value is, and a
prediction for the next moment, even through short gaps.

The obvious alternative is a moving average: average the last ten readings. It
is simpler and needs no model. On the steady part of the depth example, a
10-reading average has an average error of 1.08 mm, close to the Kalman filters.
But it has three drawbacks. It always lags: after the 20 mm drop it took seven
readings to get within 5 mm, against two for the `q = 4` filter. It
cannot predict ahead, so it cannot help an arm meet a moving part. And it gives
no spread, so a tracker cannot tell how far to look for the next detection.

A second alternative is to fit a line through the last few positions with
[least squares](02_least-squares-fitting.md) and extend it forward. That gives a
speed and a prediction. But it forgets everything older than its window, and it
does not say how sure it is. The Kalman filter keeps all past readings in two
small numbers, the estimate and the covariance, and costs the same on every
step however long it runs.

The costs are these. You need a model of how the quantity moves, and the filter
is only as good as that model. You must choose the process noise, and a poor
choice gives either a laggy or a noisy result without any error message. The
filter's confidence is highest just before an object does something new, such as
change direction. And its state lives on from step to step, so a wrong reading
or a bug can affect many steps after it.

---

## 8. Where to read next

- [Least-squares fitting](02_least-squares-fitting.md) is the batch version of
  the same idea. For a quantity that does not change, the Kalman filter gives the
  least-squares answer one reading at a time.
- [RANSAC](03_ransac.md) handles bad points in a batch. A gate does the same job
  for a filter.
- [Assignment and matching](../03_searching-and-matching/04_assignment-and-matching.md)
  matches new detections to the filter's predictions.
- [PID control](../07_control-and-motion/02_pid-control.md) often acts on a
  filtered reading.
- [Tracking and motion](../../06_neural-network-models/02_seeing-models/08_tracking-and-motion.md)
  in Book 6 covers learned trackers, which follow objects by their appearance as
  well as their motion.
- [Force and slip models](../../06_neural-network-models/08_touch-and-body-models/03_force-and-slip-models.md)
  in Book 6 cover learned ways to read touch and force signals, which a filter
  alone cannot interpret.
- Book 2 goes deeper into tracking on a real arm in
  [tracking and association](../../02_perception/02_object-perception/10_tracking-and-association.md).
