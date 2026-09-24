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
7. [Report the margin, not the verdict](#7-report-the-margin-not-the-verdict)
8. [Making a run traceable](#8-making-a-run-traceable)

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

### 1.5 Merge and split are two failures, and only one of them announces itself

Everything above treats a detection failure as one kind of event. It is two kinds,
and they behave so differently once the arm starts moving that averaging them
together discards the distinction you most need.

A **split** is one object reported as two. A **merge** is two objects reported as
one. Both are boundary errors, both come out of the same segmentation step, and it
is natural to file them under one heading. The reason not to is that a split
announces itself and a merge does not.

A split announces itself because the arm tries to pick up half a thing. The width
it was given is too small, the fingers meet the object before they reach the
commanded opening, and the attempt fails visibly on the first try. Nobody has to
be told. A merge is the dangerous one because it produces a plausible object: a
region with a sensible outline, a sensible width and a centroid that the rest of
the pipeline has no reason to doubt. That centroid is in a place where nothing is.

Work it through on the repo's camera, which has a focal length `fx` of 277.1
pixels on a 320 by 240 image. At 340 mm one pixel covers `0.340 / 277.1` =
1.227 mm. Put two objects 40 mm wide on the table with a 10 mm gap between them.
Each is `40 / 1.227` = 32.6 pixels wide and the gap is 8.2 pixels.

If the segmenter merges them, the reported region is 40 + 10 + 40 = 90 mm wide and
its centroid sits at the middle of the pair. That centroid is 25 mm from the centre
of either real object. Compare that with [the error
budget](01_overview.md#8-where-the-millimetres-go), where one degree of hand-eye
error costs 5.9 mm at this reach and a 20 mm depth error costs 4.3 mm. A single
merge is more than four times the largest term in that budget, and unlike every
term in it the merge arrives with no symptom at all.

Now split the 73.6 mm object that budget is worked for, down the middle. Each
fragment is reported as 36.8 mm wide with its centroid 18.4 mm from the true
centre. The arm is told to close to 36.8 mm on an object 73.6 mm across. It cannot,
so it fails where you can see it.

**A single detection accuracy hides the difference completely.** Take two runs of a
hundred objects that both report ninety-six correct detections. The first made four
splits and wasted four attempts. The second made four merges and sent the arm into
four places where there was nothing, each time with a grip width that belonged to no
object present. Those are different systems and the headline number is the same.

**Count them by matching in both directions.** Match predicted regions against the
objects the simulator spawned, and then count the matches from each side rather than
from one.

1. For each spawned object, find every predicted region that covers at least a third
   of it.
2. For each predicted region, find every spawned object of which it covers at least a
   third.
3. A spawned object covered by two or more predictions is one split. Record how many
   pieces it came back in.
4. A prediction covering two or more spawned objects is one merge. Record how many
   objects it swallowed.
5. What is left over is the ordinary bookkeeping: a prediction that covers nothing is
   a false positive, and an object covered by nothing is a miss.

Use coverage — how much of the object lies inside the prediction — rather than IoU
for steps 1 and 2. This is the part that is easy to get wrong, and getting it wrong
is exactly how a merge disappears. The merged region above has an IoU of `40 / 90` =
0.44 against each of the two objects it contains, because the union includes the
other object. At the usual 0.5 bar it matches neither, so standard scoring records
one false positive and two misses — the same score as a detector that saw nothing
there at all. The one outcome you were trying to separate has been filed as its
opposite.

Set the coverage bar low, at a third rather than a half, because an object split
three ways gives fragments covering a third each, and a bar of a half would record
that as three false positives and a miss.

**The two failures have different causes, and the causes overlap in a revealing
way.** Merges are caused by:

- objects touching or nearly touching, so there is no background between them to
  draw a boundary through
- a morphological closing step, which fills small gaps by design; on this camera at
  340 mm a 3 by 3 closing bridges about two pixels, which is 2.5 mm of table
- a clustering tolerance larger than the gap, since point-cloud clustering joins
  points closer together than a distance you set, and a 10 mm tolerance joins the
  10 mm gap above
- a colour threshold that also accepts the shadow lying between the two objects
- non-maximum suppression, the step that deletes duplicate boxes, set to a loose
  overlap so that two genuine boxes collapse into one

Splits are caused by:

- something crossing the object, such as a wire, a handle or the shadow of the
  gripper
- a specular highlight, meaning a bright mirror-like reflection, which leaves the
  colour range the rest of the object sits in
- a hole in the depth image across the middle of the object, which is what a shiny
  or a very dark surface gives you
- an erosion or opening step aggressive enough to cut through a thin waist
- non-maximum suppression set too tight, so two boxes on one object both survive

The same two steps appear in both lists with their settings turned in opposite
directions. That is the whole argument for counting the two failures separately:
every knob you have trades one against the other, and a single accuracy number
tells you nothing about which way to turn it.

Five jobs that counting merges and splits apart suits:

- deciding whether to buy a better segmenter or to add a step that separates the
  objects before anything looks at them
- tuning a morphological kernel or a clustering tolerance, where the two errors move
  in opposite directions and one number cannot show it
- setting a policy for when to decline, because a merge is a good reason to decline
  and a split usually is not
- choosing between two models that score the same overall
- writing the acceptance test for a cell where a wrong centroid is expensive

Five jobs it cannot do:

- work without ground truth, which means it works in simulation and not on a real
  run; the substitute on hardware is a plausibility check on the size, since a
  90 mm region where 40 mm was expected is a fact you have without knowing the truth
- tell a merge from a genuinely single object of that size
- notice a merge of two objects when only one of them is in the frame
- say anything about the millimetres, since a merge with a clean boundary and a
  merge with a ragged one score identically
- replace looking at the mask overlay, which is still where the cause becomes
  visible

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

### 5.1 Contact, and which of its numbers you can measure

The second bullet above says contact is the weakest part of any physics engine. It
deserves more than a bullet, for two reasons. It is the part manipulation depends on
most, since every pick ends in contact. And it is the one place where the simulator
is not merely approximate but is answering a different question from the one you
asked.

The examples below are MuJoCo's, because MuJoCo documents its contact model in
public and the [repository](https://github.com/google-deepmind/mujoco) is
Apache-2.0, so the behaviour can be checked rather than assumed. The shape of the
problem is the same in every engine.

**A friction coefficient is a property of a pair of surfaces, not of a material.**
There is no such thing as the friction of steel. There is the friction of this steel
against that rubber, at this normal load, at this sliding speed, with this much dust
on it, after being pressed together for this long. Textbook tables give one number
per material pair and omit the rest of that list, which is why the grip document
warns that [textbook friction coefficients are the largest single source of confident
wrong answers](../07_gripping/03_choosing-a-grip.md) in the subject.

Simulators store friction per object rather than per pair, because the pairs
multiply: ten objects and three fingertip materials is thirty pairs, and every one
needs its own measurement. In MuJoCo a geom carries three friction numbers, with
defaults `1 0.005 0.0001` for sliding, torsional and rolling friction. When two
geoms touch and neither has been given priority, the contact takes the **element-wise
maximum** of the two geoms' coefficients. So the pad-against-object pair you care
about most gets whichever of the two numbers happens to be larger, which is a rule
about bookkeeping and not about physics. The fix is to declare the pair explicitly,
with its own measured coefficients, for the handful of pairs that matter.

The cost of leaving the default in place is easy to put a number on. The squeeze a
two-pad grip needs to hold a mass `m` against gravity is `F = m * g * S / (2 * mu)`,
for a safety factor `S` you choose. For 500 g at a safety factor of 2, the default
sliding friction of 1.0 asks for `0.5 * 9.81 * 2 / (2 * 1.0)` = 4.9 N per pad. A
coefficient of 0.3, which is the order of the measured figure a gripper manufacturer
publishes for its own pads and the value [the grip
document](../07_gripping/03_choosing-a-grip.md) works its examples at, asks for
`0.5 * 9.81 * 2 / (2 * 0.3)` = 16.4 N. The simulation holds the object with a third of the force the bench needs,
and the grip that looked comfortable slips.

**Pressure distribution across the contact patch is essentially never modelled.** A
real pad on a flat face presses over an area, and the pressure is not even across
that area. How it is distributed is what decides the torque the contact can resist,
and therefore whether a pushed or held object rotates instead of translating. A
physics engine resolves the contact at a small number of points instead. MuJoCo's
concession to the patch is one number: raise `condim` to 4 and you get a torsional
friction coefficient whose units are length, which the documentation says can be
interpreted as the diameter of the contact patch. One scalar stands in for the whole
distribution. The default `condim` is 3, which has no torsional term at all, so
unless you changed it the simulated object is free to spin about the contact normal
with nothing resisting it.

**Compliance is a solver parameter wearing the clothes of a material property.** A
pad deforms under load, and the newtons per millimetre of that deformation is a real
quantity you could in principle measure. What the model gives you instead is
`solref`, whose two numbers are a time constant and a damping ratio — how quickly the
solver pushes penetration back out, not how stiff the rubber is. Tuning it until the
simulation looks right is tuning the solver. Nobody measures the pad, because
measuring it needs a load cell and a displacement gauge, and the datasheet offers a
durometer rating instead, which is a hardness reading from a spring-loaded indenter
and does not convert into a stiffness for your pad's geometry.

**Restitution, the bounciness of an impact, is not a parameter you can set.** MuJoCo
has no coefficient of restitution. You obtain a bounce by writing `solref` in its
negative form, as a stiffness and a damping, and setting the damping to zero; the
documentation is explicit that even then energy is not exactly preserved, because the
contact is soft and lasts several timesteps. A bounce you see in simulation is
therefore something you tuned, not something the material did.

The table below says, for each of those four, whether you can settle the number on
your own hardware. Read the middle column as the answer and the right-hand column as
the method, or the reason there is none.

| Contact property | Measurable on your hardware | How, or why not |
| --- | --- | --- |
| friction for one pad-and-object pair | yes | a tilt test: raise a plate until the object slides, and `mu` is the tangent of that angle. A coefficient of 0.3 is a slide at 16.7 degrees |
| friction across the whole object set | not in practice | one measurement per pair, repeated for scatter. Ten objects and three fingertips is thirty of them, and they change as the pads wear |
| pressure distribution across the patch | no | it needs pressure-sensitive film or a tactile array at the pad, and even then you get the real patch rather than a parameter the engine can accept |
| pad compliance | yes, with effort | press the pad a measured distance into a scale and read the force, which gives newtons per millimetre directly |
| restitution | yes, for one pair of surfaces | drop from a known height onto a fixed surface and measure the rebound height |

The pattern in that table is the useful part. The two properties you can measure
cheaply, friction for one pair and restitution, are also the two the engine has a
parameter for. Pressure distribution is the one that decides rotation under a push
or a squeeze, and it is both unmeasurable in a form the engine accepts and absent
from the model. That is the contact gap, stated concretely.

Five things about contact you can settle by measuring on hardware:

- the sliding friction of the two or three pairs your cell actually uses
- whether a given squeeze holds a given object, which is one pull test
- the pad's stiffness, if you care enough to build the rig
- how much the friction falls when the object is wet, oily or dusty, by repeating the
  tilt test in that state
- how much the friction falls as a pad wears, by repeating the tilt test monthly

Five things you cannot:

- the pressure distribution in a form you can put back into the model
- the friction of every pair in an open-ended object set
- how an object rotates under a push, which follows from the distribution you could
  not measure
- the contact stiffness the solver is actually using, which is not the pad's
- what happens at a contact you have no sensor at, which for most cells is all of
  them, and [sensors](02_sensors.md) is about the instruments that would change
  that

The practical consequence is narrow and worth stating plainly. Use simulation to
check that the reasoning about shape and geometry holds. Do not use it to choose a
squeeze force, a friction margin or a push. Those are the numbers to calibrate on
hardware, and the cheapest of them is a plate and a protractor.

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

## 7. Report the margin, not the verdict

Section 6 is about a check that can stop the arm. This section is about what that
check should hand back when it does not stop the arm, and the answer is: how close
it came.

A check that returns `true` has thrown away everything except the answer. A check
passed by half a millimetre and a check passed by five millimetres are the same
`true`, and they are not the same result. The first is a warning and the second is
comfortable, and by the time the value reaches the caller there is no way to tell
which one happened.

**The general form is one line. Return the margin, and threshold it at the call
site.** Instead of

    def fits(width_mm):
        return 4.0 <= width_mm <= 40.0

write

    def fit_margin_mm(width_mm):
        """How many millimetres of room the gripper has. Negative means it does
        not fit."""
        return min(width_mm - 4.0, 40.0 - width_mm)

and let whoever calls it decide what margin is enough. The check keeps the
arithmetic, which is the part it knows about. The caller keeps the threshold, which
is the part it knows about, and different callers want different thresholds: the bar
before a fragile grasp and the bar before a shove are not the same bar. When the
threshold lives inside the check, the second caller writes a second copy of the
function.

**The reason this matters here rather than in general is that a margin can be
compared with the error budget.** Take an object measured at 38.4 mm against the 4
to 40 mm range a stemmed glass should ever need. The margin is 1.6 mm. Now look at
what the measurement is worth. One pixel covers 1.227 mm at 340 mm on this camera, so
one pixel of segmentation error on each edge is `2 * 1.227` = 2.45 mm, and one degree
of hand-eye error is 5.9 mm at the same reach. Added in quadrature, which is how
independent errors combine, `sqrt(2.45^2 + 5.9^2)` = 6.4 mm. The check passed by
1.6 mm on a number that is uncertain by 6.4 mm. It did not pass. A boolean cannot
show you that, and no amount of staring at `true` will.

Four checks from this area, and what each should return instead of a verdict.

**A detection score.** Return the score itself, and return the runner-up's score
beside it. The gap between the best and the second best is a different quantity from
the best, and it is the one that says whether the decision was close. Remember that
the score's scale is the model's own, so it is comparable between runs of the same
model and with nothing else.

**A plane fit.** Fitting a plane to a patch of point cloud — the step underneath
table removal and underneath most flatness checks — has a natural margin already:
the root mean square residual, meaning the typical distance from a point to the
fitted plane, in millimetres. A fit at 0.4 mm and a fit at 2.9 mm both clear a 3 mm
bar, and only one of them is a plane. Return the residual.

**A size-range check.** The example above. Return the signed distance to the nearer
end of the range, in millimetres, so the sign carries the pass or fail and the
magnitude carries the confidence.

**An association gate.** When a detection has to be matched to a track, or to the
object you expected to be there, the match is accepted if the distance is below a
gate. Return two numbers: the distance to the accepted match and the distance to the
nearest rejected one. A match at 3 mm with the runner-up at 40 mm and a match at
3 mm with the runner-up at 4 mm are the same boolean and completely different
events, and the second is where an object swap comes from.

This is already stated in one place in this repository, for one case. The section on
grasp quality metrics in [choosing a grip](../07_gripping/03_choosing-a-grip.md) says
that reporting the margin inside the friction cone rather than the boolean is nearly
free and turns a pass into a ranking. The generalisation is that this is true
of every check with a threshold in it, not only that one, and the grasp case is
simply where it was noticed first.

It also joins up with section 6. The sentence carried by an exception — the fingers
want to be 61 mm apart, outside the 4 to 40 mm range — is the margin written out in
words. A check that already computes its margin can raise that sentence for free,
and one that computes only a boolean has to reconstruct the numbers to say anything
useful.

Five jobs that returning a margin suits:

- ranking several candidates that all passed, which a boolean cannot order at all
- deciding which object to attempt first when the arm can only do one at a time
- triaging a report after a run, by reading the margins of the calls that were nearly
  wrong rather than only the ones that failed
- choosing a threshold from data, by running once and looking at the distribution of
  margins for the attempts that worked against the ones that did not
- comparing the margin against the error budget, which is the only way to notice that
  a check is finer than the measurement feeding it

Five jobs it cannot do:

- make a badly chosen check meaningful, since a precise margin on the wrong quantity
  is a precise number about nothing
- be compared between two checks measured in different units, so every margin needs
  its unit printed beside it
- rescue a check applied to the wrong input; rung 4a of [the diagnosis
  ladder](#3-when-it-does-not-work-a-diagnosis-ladder) describes a check downstream of
  a smoothing step, and it never fires whatever it returns
- carry a confidence the model did not have, since a detector's score is a number the
  model chose for itself
- remove the need to choose a threshold, which it moves to the call site rather than
  abolishing

## 8. Making a run traceable

Section 1.3 says to score against the simulator's ground truth. This section is about
the step that makes such a score usable: being able to take any number in the report
and get back to the picture and the arm pose that produced it.

The test is a single question. Given a line in the report, can you reach the inputs
that produced it without re-running anything? If not, every surprising number becomes
a re-run, and a re-run of a pipeline with any randomness in it is not the same run.
Put a number on what that costs: with the ten-second pick cycle from section 2, a
five-hundred attempt run takes about 5000 seconds, which is 83 minutes. That is the
price of finding out what one attempt saw.

**Give every attempt an identifier, and write the inputs and the outputs of each step
under it.** One directory per attempt, named by the identifier, and the identifier
printed in the report line. A report that says `object 7: declined, NoGrip` and a
directory called `attempt_0031` with nothing connecting them is not traceable, and
the missing piece is one string.

**The rule for what to log is that you log what you cannot recompute.** The camera
frame, the depth frame, the arm pose with its own timestamp, the random seed, the
version of the code, and the thresholds that were in force are all inputs. None of
them can be reconstructed afterwards and all of them change the answer. The mask, the
measured width, the chosen grasp and the margins are outputs of those inputs, so in
principle you do not need to store them. In practice store the numbers, which are
tiny, and do not store the intermediate arrays, which are not.

**The one output worth storing as a picture is the mask overlay.** Rung 1 of [the
diagnosis ladder](#3-when-it-does-not-work-a-diagnosis-ladder) is looking at the mask
drawn on top of the image, and it resolves about half of all reports. A picture you
have to regenerate before you can look at it is a picture you do not look at. Write
it during the run, when the mask is already in memory and the cost is one file.

The sizes make this argument concrete rather than theoretical. A 320 by 240 colour
frame at three bytes a pixel is 230,400 bytes. The depth frame at four bytes a pixel
is 307,200 bytes, so an attempt that keeps both raw costs 537,600 bytes. Five hundred
attempts is 269 MB. Store depth as 16-bit millimetres instead, which is lossless at
any range a table-top arm works over, and the frame is 153,600 bytes and the run is
192 MB. Neither figure is a reason to throw the frames away, which is worth knowing
because "it would be too much data" is the usual reason given and it is usually
false.

**What not to log is anything that grows with the loop rather than with the
attempt.** A line per attempt is five hundred lines. A line per solver iteration, per
candidate grasp or per point in the cloud is however many the run happened to need,
which is the log that fills the disk and, worse, the log nobody reads because it
cannot be read. If you want per-iteration detail, write it for the attempts that
failed and discard it for the ones that did not.

Keep the ground truth in the run record as well, on the report side of the boundary
that [section 1.3](#13-use-the-simulators-ground-truth--for-scoring-never-for-acting)
insists on. It is an input to the score and not to the robot, and writing it into the
same directory as the frames is how the comparison becomes a two-line script later.

Two pieces of existing software do the recording part if you are already on ROS.
[rosbag2](https://github.com/ros2/rosbag2) records and replays message streams and is
Apache-2.0. Its default storage format is [MCAP](https://github.com/foxglove/mcap),
MIT-licensed, which is a container that keeps heterogeneous timestamped messages in
one file with an index. Both save you writing the part that is about files rather
than about robots. If you are not on ROS, a directory per attempt and plain files are
enough, and the discipline matters more than the format.

Five jobs a run record like this suits:

- answering which picture produced a number that looks wrong
- reproducing one attempt without re-running the batch
- showing that a change helped, by comparing two runs attempt by attempt rather than
  summary against summary
- building a regression set out of the attempts that failed, since their inputs are
  already saved in a form the pipeline can be pointed at
- letting somebody who was not in the room read the report

Five jobs it cannot do:

- record what you did not think to record, since the frame you skipped is gone
- make a stochastic pipeline reproducible unless the seed is in the record too
- help at all if the identifier is missing from the report line
- explain a cause that is not among the recorded inputs, such as an arm that reported
  a pose it had not yet reached
- outlive a change in the pipeline's shape, since a record of a step that no longer
  exists only explains old failures

The test that this is working is the same shape as the test in section 6. When a
number in the report looks wrong, the next action is opening a file, not starting the
run again.
