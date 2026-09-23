# Making it work: measuring, timing and debugging

The other six documents help you choose. This one is about what happens after
you have chosen: how to tell whether the thing is actually working, how fast it
has to be, and what to do when it is wrong.

It exists because the gap between "the model scores well" and "the robot picks
the glass up" is wider than it looks, and almost none of the published numbers in
this field are measured on the thing you care about.

## Contents

1. [How to tell whether it is working](#1-how-to-tell-whether-it-is-working)
2. [How fast does it actually have to be](#2-how-fast-does-it-actually-have-to-be)
3. [When it does not work: a diagnosis ladder](#3-when-it-does-not-work-a-diagnosis-ladder)
4. [Occlusion and clutter](#4-occlusion-and-clutter)
5. [What simulation will not tell you](#5-what-simulation-will-not-tell-you)

---

## 1. How to tell whether it is working

### 1.1 The standard metrics, in plain words

**IoU**, intersection over union, is how much two regions overlap: the area they
share divided by the area they cover between them. A perfect match is 1. Two
boxes overlapping half their area score about 0.33. It is the ruler every other
detection metric is built on.

**Precision and recall** are the two ways of being wrong. Precision is what
fraction of the things you found were real. Recall is what fraction of the real
things you found. You can always trade one for the other by moving a confidence
threshold, which is why quoting either alone means nothing.

**Average precision**, and **mAP** which is its mean over classes, sweeps that
threshold and takes the area under the resulting curve, counting a detection as
correct when its IoU beats some bar. COCO's headline number averages over IoU
bars from 0.5 to 0.95, which is why COCO mAP looks low compared with older papers
quoting IoU 0.5 alone. [The COCO evaluation
page](https://cocodataset.org/#detection-eval) defines it precisely, and
[torchmetrics](https://github.com/Lightning-AI/torchmetrics) (Apache-2.0)
implements it.

### 1.2 Why none of that is your metric

Here is the part that matters, and it is not in the papers.

**mAP is a ranking metric averaged over a dataset. A robot does one thing at a
time and either succeeds or does not.** The two are barely related, in both
directions:

- A mask can score 0.95 IoU and still be useless, if the missing 5% is all along
  one edge and that edge is where you measure the width from. IoU is blind to
  *where* the error is; your gripper is not.
- A box at 0.6 IoU can be perfectly good, if all the next step needs is somewhere
  to point a second camera.
- A model can improve its mAP by getting better at the classes you do not have,
  on objects at scales you never see.

So the number to track is **the task's own outcome**, and for anything where
being wrong is expensive it has two columns, not one:

| What to count | Why |
| --- | --- |
| attempts that succeeded | the obvious one |
| attempts that failed *after committing* | the expensive one — a dropped glass, a knocked-over part |
| times it declined, with the reason | the one that is easy to mistake for failure |
| measured value against true value | only available in simulation, and worth everything |

A run that completes four and declines one with a reason is working. A run that
completes five by pushing through a doubt is worse even when nothing breaks,
because the doubt is still there next time.

### 1.3 Use the simulator's ground truth — for scoring, never for acting

A simulator knows exactly what it spawned. That is a large advantage and it has
one rule attached: **the ground truth may be read by the report and never by the
robot.** Write what you spawned to a file, let the arm measure it independently,
and have the report compare the two afterwards. You then get an error
distribution over hundreds of objects, for free, which no amount of real-world
testing would give you cheaply.

The moment any code path the robot runs reads that file, every number you produce
afterwards is meaningless. Keep the boundary explicit and obvious in the
directory layout, not just in your intentions.

## 2. How fast does it actually have to be

The honest answer for most arm work is **much slower than you think**, and
knowing this saves a great deal of optimising.

**Look-then-move**, which is nearly every arm task: the arm stops, perception
runs once, the arm acts on the answer. Perception latency is dead time added to
the cycle. If the pick takes ten seconds and perception takes 500 ms, perception
is five per cent of the cycle. You can afford a model that takes half a second.
Most people building their first cell will not believe this and will spend a week
on a speed problem they did not have.

**Visual servoing**, where the picture steers the arm continuously, is the other
regime and it is a different world: you need 30 Hz or better, and the loop is
closed, so latency becomes phase lag and makes the controller unstable rather
than merely slow. This rules out almost everything learned, and it is why the
classical methods in [programmed methods](03_programmed-methods.md) still run
visual servoing in industry.

**The constraint that actually bites is not the mean, it is the variance.** A
model that takes 50 ms usually and 2 seconds occasionally is worse than one that
takes 200 ms every time, because the occasional case arrives when the arm is
already moving. Measure your ninety-ninth percentile, not your average, and be
suspicious of any figure quoted without one.

## 3. When it does not work: a diagnosis ladder

Perception failures nearly always present the same way — the arm goes to the
wrong place — and the cause can be at any of five levels. Test them in this
order, because each rung assumes the ones below it are sound.

**1. Is the mask right?** Save the mask as an overlay on the picture and look at
it. Not the numbers, the picture. Half of all "the model is bad" reports are
resolved here, usually as the mask being correct and the problem being further
up.

**2. Is the mask right but the 3D point wrong?** Project a known object — a
calibration board, a block of known size — and check the reported size in
millimetres against a ruler. If the size is wrong by a constant percentage, your
depth or your focal length is wrong. If it is wrong near the edges only, it is
distortion.

**3. Is the point right in the camera's frame but wrong in the world?** Put a
marker somewhere you can measure by hand, and compare what the arm reports
against a tape measure. A constant offset along one axis is the signature of
hand-eye calibration, and it is the single most common fault in a working cell —
see [the error budget](01_overview.md#8-where-the-millimetres-go), where one
degree of hand-eye error costs almost 6 mm at a 340 mm reach.

**4. Is the world point right but the arm still goes elsewhere?** Now it is the
tool offset, the controller, or the planner. Command the arm to the point with no
perception at all and see where it goes.

**5. Does it work standing still and fail in motion?** Timing. The picture and
the arm pose have to be from the same instant; if the pose is read after the
picture, an arm still settling gives a pose that is a few milliseconds and a few
millimetres stale. Use the timestamp on the frame, not the current pose.

The reason to follow the ladder rather than guess is that rungs 3 and 5 both look
exactly like rung 1 from the outside, and swapping the segmentation model — the
usual first move — fixes neither.

## 4. Occlusion and clutter

Everything in these documents assumes the object is visible. Two things happen
when it is not, and they need different answers.

**Partial occlusion**, where something covers part of the object, degrades a mask
model gracefully and a geometric method abruptly. A silhouette with a corner
missing is still mostly a silhouette; a
[solid-of-revolution measurement](03_programmed-methods.md#26-silhouettes-of-a-solid-of-revolution)
with a corner missing is simply wrong, and nothing in the arithmetic notices.
This is the main argument for checking the measurement against something else
before acting on it — a touch, a second view, a weight.

**Touching objects** defeat the cheap methods completely. Plane removal and
clustering return two touching objects as one clump, and a colour range returns
them as one blob. Instance segmentation exists precisely for this, and it is the
main reason to reach for it over semantic segmentation.

The cheapest fix for both is usually not a better model. It is a second
viewpoint, or separating the objects — which is why so many real cells have a
step that spreads things out before the step that looks at them.

## 5. What simulation will not tell you

Worth being explicit, since everything in this repo runs in a simulator.

- **Segmentation is easier in simulation than it has any right to be.** Clean
  lighting, no motion blur, no sensor noise, no dust. A model that works
  perfectly in Gazebo tells you your *logic* is right, not that your perception
  is.
- **Contact with curved, slippery or brittle surfaces is the weakest part of any
  physics engine.** Friction and softness numbers are plausible, not measured.
- **Depth sensors are modelled optimistically.** Real ones have holes at
  discontinuities, flying pixels, multipath error off shiny surfaces and
  temperature drift. Simulated ones mostly do not.
- **Nothing tells you what force breaks a real object.** Caps derived in
  simulation are guesses that need calibrating on hardware.

What simulation *does* tell you, and what makes it worth building in, is whether
the reasoning holds: whether a rule stated as a sentence about a shape survives
contact with a hundred objects nobody chose to suit it. That is a real result,
and it is the one this repo is set up to produce.
