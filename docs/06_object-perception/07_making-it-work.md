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
6. [Declining, as a mechanism rather than an intention](#6-declining-as-a-mechanism-rather-than-an-intention)

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

### 1.4 Testing a rule is not testing a model

Everything above assumes what you are evaluating is a model, scored against a
dataset. If what you have written is a **rule** — hold the narrowest part below
the widest, take the flattest band in the lower third — then dataset metrics are
the wrong instrument entirely, and there is a better one.

**Generate a family and test the rule against all of it.** Not one example.
Forty, drawn across the whole plausible range of proportions, with the generator
seeded so a failure can be reproduced exactly. Then assert a property that must
hold for every one of them: *every object gets a grip the gripper can actually
make*, say, or *no measurement is more than 2 mm from the truth the generator
knows*.

This is property testing, and it fits geometric rules the way mAP fits
classifiers. The difference in what it catches is large, because a rule fails on
*proportions* rather than on appearance, and a single test object has exactly one
set of proportions. Real examples of faults that only a family finds:

- a search that returns the first index of a plateau rather than its middle,
  which is correct on a tapered object and wrong on one with a parallel section
- a generated dimension drawn independently of another it should depend on, so
  that one object in forty comes out with a base wider than its body and breaks
  an assumption three functions away
- a tolerance set from geometry rather than from the hardware, which quietly
  refuses a whole class of shape

None of those is a bug in the sense of a crash. Each is a rule that is true of
the object the author had in mind, and the family is what reveals which object
that was.

**Assert the property, not the label.** A tempting test is that each generated
object is classified as the kind it was generated as. That test is wrong, and it
fails for a good reason: a very shallow cone is, physically, a nearly straight
object, and the straight-object rule holds it perfectly well. Insisting on the
generated label forces the classifier to preserve a distinction the gripper does
not care about. Ask instead whether the object ends up with a rule that can hold
it — harder to satisfy, impossible to satisfy by cheating, and the thing you
actually want.

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

**4a. Is a check passing or failing for the wrong reason?** Two failures look
identical from outside and neither is perception. A check on a sensor that cannot
observe the event always reports nothing — see [the guarded
move](02_sensors.md#21-what-you-can-actually-do-with-it), where pad sensors
cannot feel a held object's base touching down. And a quality check applied after
a smoothing step never fires, because smoothing is what it was going to complain
about. Both are silent, and both are reassuring, which is worse than an error.

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
[solid-of-revolution measurement](03_programmed-methods.md#27-silhouettes-of-a-solid-of-revolution)
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

Two traps are specific enough to be worth naming, because both have cost real
days and neither announces itself.

**Transparency may be applied to colour and not to depth.** In Gazebo, a material
with an alpha value renders see-through in the camera image while the depth
sensor returns the surface as though it were solid. That matters here more than
it sounds, because it means **the depth-hole signal that
[section 1.7 of programmed methods](03_programmed-methods.md#17-the-depth-hole-for-glass-and-chrome)
recommends for glass does not exist in simulation.** The one honest way to
develop against it is to manufacture the hole deliberately — mask out the depth
where the glass is — and to be explicit in the code that you are simulating the
sensor's failure rather than observing it. A pipeline that is never given the
hole will not be ready for it.

**Colour comes out gamma-encoded.** A material set to 2% reflectance does not
arrive as 5 of 255. It arrives near 41, because the renderer writes sRGB. Any
threshold picked by reasoning about the material rather than by looking at the
pixels will be wrong, and wrong in the direction that makes a dark background
read as an object. The whole horizon can come back as one enormous blob and the
threshold looks perfectly sensible in the source. Pick thresholds from a
histogram of the actual image, never from the number you typed into the world
file.

What simulation *does* tell you, and what makes it worth building in, is whether
the reasoning holds: whether a rule stated as a sentence about a shape survives
contact with a hundred objects nobody chose to suit it. That is a real result,
and it is the one this repo is set up to produce.

## 6. Declining, as a mechanism rather than an intention

Several documents here say that a system handling anything fragile needs to be
able to decline. That is easy to agree with and easy to leave as good intentions,
so this is what it looks like as code.

**Every check raises rather than returns a flag.** A rule that cannot find a grip
raises; a measurement too ragged to trust raises; a mass beyond the cap raises. A
boolean that the caller may forget to look at is not a refusal mechanism.

**The exception carries the sentence, not a code.** `NoGrip("the rule wants the
fingers 61 mm apart, outside the 4 to 40 mm a stemmed glass should ever need")`
is worth more than `ERR_GRIP_INVALID`, because it survives into the report and
tells you which threshold to argue with.

**One place catches them all.** The module that knows the sequence catches each
kind, writes down which object and which reason, marks that object as not to be
retried, and moves to the next. Nothing below that layer decides whether to give
up — they only state what is wrong.

**And the report prints both columns with equal weight.** Completed and declined,
side by side, with the reason beside each declined one. If the summary line
counts only successes, every future change will be judged by a number that
rewards pushing through doubt, and the mechanism above will slowly be tuned away.

The test that this is working is that a declined object is boring: it produces a
line in a report, not a traceback, not a stuck arm, and not a retry loop.
