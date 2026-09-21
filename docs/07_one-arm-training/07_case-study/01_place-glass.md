# Case study: standing a glass upside down on a drying rack

This document takes one small household job and follows it all the way down to the
parts you would actually have to build. The job is this: a drinking glass is
standing on a table, and the robot has to pick it up, turn it over, and stand it
mouth-down on a drying rack.

A drying rack, in this document, means the ordinary kitchen kind sold across
Pakistan and India: a flat base with a set of vertical pegs standing up from it. You
push a washed glass down over a peg, upside down, so the water runs out and the air
gets in. Six pegs is a common size, and that is the rack assumed here.

It is worth being clear about why this job is worth a whole document. It sounds
trivial, and the pick-and-place part of it is trivial. Everything that is hard about
it comes from the object: the glass is transparent, so the usual camera cannot see
it; it has to be turned completely over, which most arms cannot do in one motion;
and if you squeeze it too hard it breaks, which is not a failure you can retry.

This is for somebody who has read [the overview](../01_overview.md) and wants to see
the method choices in it applied to one real problem, with the reasons attached. It
is a design document, not code. Where a term is new,
[the glossary](../06_glossary.md) has the longer explanation.

## Contents

1. [The task, said precisely](#1-the-task-said-precisely)
2. [Why it is harder than it looks](#2-why-it-is-harder-than-it-looks)
3. [The first version, where everything is known in advance](#3-the-first-version-where-everything-is-known-in-advance)
4. [What each step up buys you](#4-what-each-step-up-buys-you)
5. [Finding the glass](#5-finding-the-glass)
6. [The gripper](#6-the-gripper)
7. [Force](#7-force)
8. [When a new kind of glass arrives](#8-when-a-new-kind-of-glass-arrives)
9. [The frameworks, and why each one](#9-the-frameworks-and-why-each-one)
10. [What will bite you](#10-what-will-bite-you)
11. [What to measure](#11-what-to-measure)
12. [Where to go next](#12-where-to-go-next)

---

## 1. The task, said precisely

The robot starts with a glass standing upright on a table, mouth up. It has to end
with that glass standing on the rack, mouth down, over one of the free pegs, resting
on the rack base, touching none of the glasses already there, and still in one
piece.

Said as a sequence, in the order it happens:

1. Find the glass on the table, and find the rack.
2. Choose a free peg.
3. Grasp the glass.
4. Lift it clear of the table.
5. Turn it through 180 degrees, so the mouth points down.
6. Move it above the chosen peg.
7. Lower it until the rim reaches the rack base.
8. Let go.
9. Check that it is standing, and that nothing else fell over.

Every number in this document comes from one example setup, which is also what the
pictures are drawn to. Measure your own rack and your own glasses before you use any
of these; they are here so that the reasoning has something concrete to work on.

| Thing | Number |
| --- | --- |
| Glass outside diameter at the rim | 70 mm |
| Glass inside diameter at the rim | 64 mm |
| Glass height | 120 mm |
| Glass wall thickness | 3 mm |
| Glass mass, empty | 220 g |
| Peg diameter | 12 mm |
| Peg height | 100 mm |
| Pegs on the rack | 6, in two rows of three |
| Distance between neighbouring pegs | 90 mm |

The arm is a six-axis arm bolted to the table, of the ordinary sort whose
repeatability is around a tenth of a millimetre. That precision is not the problem
here, and saying so early saves a lot of wasted effort: nothing in this task fails
because the arm cannot hit a position accurately enough.

One attempt counts as a success when the glass is mouth-down on a peg, the rim is on
the base, the glass is still there ten seconds later, no neighbouring glass moved,
and the glass is undamaged. Nothing short of all five counts, and in particular a
glass that the arm released in the right place and which then fell over is a
failure, not a partial success.

---

## 2. Why it is harder than it looks

Four things make this harder than the box-picking in
[the camera area](../../05_camera/03_one-box-intro.md), and they are worth
separating, because each one is solved by a different part of the system.

### The camera cannot see the glass

A depth camera, meaning a camera that reports a distance for every pixel rather than
a colour, works by sending light out and measuring what comes back. On an opaque mug
that works. On a glass it does not, because most of the light goes straight through,
and the part that does not goes off sideways because the curved wall bends it. What
comes back is either the table behind the glass or nothing at all, so the depth
picture has a hole in exactly the place you were most interested in.

![Why a depth camera returns a hole where the glass is](../../images/one-arm-training/case-study/place-glass/why-depth-fails.svg)

The useful half of that picture is on the left of the two panels. The ordinary
colour camera still sees the glass perfectly well. So the shape has to be worked out
from colour, and depth is demoted to confirming things that colour already claimed.
[Section 5](#5-finding-the-glass) is about how.

### The turn has to be planned backwards

Turning the glass over is a rotation of 180 degrees about a horizontal line. The
rotation itself is easy. What is not easy is that the last joint of most arms has a
limited range — a range of plus or minus 175 degrees is common, and some arms give
you a full turn or more, so check the one you have — and 180 degrees of turning does
not fit into 175 degrees of range if you start in the middle of it.

![Where in the wrist's range the turn starts decides whether it finishes](../../images/one-arm-training/case-study/place-glass/wrist-budget.svg)

The fix is not clever, but it has to be done in the right place. You turn the wrist
back before closing the fingers, so that the turn you are about to make ends inside
the range. That means the grasp step has to already know about the release
orientation, which is the single most common thing people get wrong when they write
this task for the first time. They write a grasp, then a turn, and discover that the
turn is impossible from the grasp they chose.

### The tolerance is not where you would guess

The obvious worry is getting the glass onto a 12 mm peg. That worry is misplaced.
The glass is 64 mm across inside, so you can be 26 mm out sideways and it still
drops over.

![The peg is easy to hit; the glasses already on the rack are not](../../images/one-arm-training/case-study/place-glass/rack-clearance.svg)

The real constraint is the rack filling up. With pegs 90 mm apart and glasses 70 mm
across, the gap between two rims is 20 mm, so there are 10 mm to spare on each side.
And because the glass is tall, orientation eats that budget faster than position
does: tilting a 120 mm glass by 5 degrees, measured from where the fingers hold it,
swings the far end sideways by 10.5 mm, which is all of it. So the thing to control
carefully is not where the arm puts the glass but how vertical it holds it, and the
descent onto the peg has to be a straight vertical line rather than an arc.

### Squeezing it wrong breaks it, once

There is a range of grip force that works. Below it the glass slides out of the
fingers. Above it the glass cracks. The upper edge is a property of the glass and
you cannot move it. The lower edge you can move, by choosing fingers with more
friction, and that is the only lever you have.

![The grip force window, and what widens it](../../images/one-arm-training/case-study/place-glass/grip-window.svg)

A wet glass, which is what comes out of a sink, moves the lower edge up and narrows
the window further. [Section 7](#7-force) is about what to do about that.

### And you cannot tell from the plan whether it worked

The last point is the one that shapes the whole design. Nothing in the commanded
positions tells you whether the glass is standing. The arm will happily report that
it reached every waypoint while the glass lies on its side. The only way to know is
to let go, look, and be willing to say the attempt failed.

---

## 3. The first version, where everything is known in advance

Build this one first. It assumes away every hard part of
[section 2](#2-why-it-is-harder-than-it-looks) except the turn, and what it gives you
in return is a working system in a few days, plus a test rig for everything that
comes after.

The assumptions are: the glass always starts in the same place, because there is a
marked spot or a simple jig on the table; the rack does not move, and its position
was measured once; every glass is the same glass; and a person loads the table and
takes the rack away.

The programme is then a fixed sequence, and it reads roughly like this:

```
pegs = [p1, p2, p3, p4, p5, p6]          # measured once, in fill order

for peg in pegs:
    move_to(above_pickup, wrist = -90°)   # pre-turned, so the flip will fit
    move_down_to(grasp_height)
    close_gripper(to_width = 64 mm, force_limit = grip_force)
    if gripper_width_now > 68 mm:         # the fingers closed on nothing
        stop("no glass")
    move_up_to(clear_height)
    turn_wrist(to = +90°)                 # the glass is now mouth down
    move_to(above(peg) + 130 mm)          # above the peg top, with margin
    move_down_until(vertical_force > 2 N) # the rim has reached the base
    open_gripper(slowly)
    move_up_to(clear_height)
    photograph(peg) and check_standing()
```

Two lines in that sketch are doing the real work, and they are the two that are not
about motion. `move_down_until(vertical_force ...)` is the descent stopping on
contact rather than on a commanded position, which is what keeps the rim from being
driven into the base. And `check_standing()` is the admission that the plan
succeeding is not the same as the task succeeding.

What this version gives you is a complete loop, a cycle time you can measure, and
somewhere to put every improvement that follows. What it cannot do is cope with the
glass being anywhere other than the marked spot, or with a second kind of glass, or
with somebody nudging the rack.

---

## 4. What each step up buys you

The same four layers as [the learning path](../04_learning-path.md) apply here, and
they are worth reading as a ladder where each rung removes one assumption. Read the
table as: this is what changes, this is what it buys, and this is what it costs.

| Layer | What changes | What it buys | What it costs |
| --- | --- | --- | --- |
| 1. Written by hand | nothing is learned | a working cell in days | the glass must always be in the same place |
| 2. Learned perception | a network finds the glass and the rack | the glass can be anywhere on the table | training data, and a part you cannot read |
| 3. A learned skill | the approach and release come from demonstrations | it tolerates a rack that moved and a glass it has not seen | a few hundred demonstrations, and a rig to collect them |
| 4. A pretrained policy | one model drives the whole task from an instruction | new glassware without new demonstrations | you can predict its behaviour least, so the checks matter most |

The rule that matters more than the table is this: do not climb a rung until the rung
below fails for a reason you can name out loud. "The colour segmenter cannot separate
two glasses that are touching" is a reason. "Layer 3 is more modern" is not.

For this particular task, layer 2 is where most of the value is, because the one
assumption that really hurts in layer 1 is the marked spot. Layer 3 earns its keep
only if the glassware varies a lot. Layer 4 is worth trying as an experiment, and
worth wrapping in the same `check_standing()` either way.

---

## 5. Finding the glass

There are two things to find, and they are not equally hard. The rack is opaque,
rigid and stays put, so it is the easy one. The glass is the problem.

These are the approaches worth considering. Read the table as a shortlist, with the
recommendation explained underneath it.

| Approach | What it does | Why you might not |
| --- | --- | --- |
| Plain RGB-D | red, green, blue and depth from one camera | returns a hole where the glass is |
| Colour segmentation, then fit a cylinder | outlines the glass in the colour picture, then fits a known shape to it | only works because a tumbler *is* a cylinder |
| Learned depth completion | a network fills the hole in the depth picture | one more model to train, host and debug |
| Polarisation camera | measures how light is polarised, which glass changes strongly | costly, and rare enough that help is hard to find |
| A patterned mat under the glass | the glass distorts the pattern, which outlines it | only works in a cell you control |
| Feeling for it | close slowly and find the glass by contact | slow, and it does not tell you where to start |

**Use colour segmentation and a cylinder fit.** Outline the glass in the ordinary
colour picture, then fit a vertical cylinder to that outline using the table plane —
which depth *can* measure reliably — as the ground it stands on. What you get out is
five numbers: where it stands on the table, how wide it is, and how tall.

The reason to prefer this over the learned depth completion that the literature
mostly discusses is that the problem here is much smaller than the one those methods
solve. They reconstruct arbitrary transparent shapes. You are fitting a cylinder to
a glass, and you already know it is a cylinder standing on a table. Five numbers is
a far easier thing to get right, and far easier to check, than a mesh.

What it costs you is generality, and the bill arrives the day somebody puts a wine
glass on the table. The cylinder fit will produce an answer, and the answer will be
wrong. [Section 8](#8-when-a-new-kind-of-glass-arrives) is about making that
situation safe.

Two more practical points. Use **two cameras**: one overhead for the table and the
rack, and one on the wrist for the last stretch of the approach. The wrist camera is
not about resolution, it is about calibration — looking from the hand removes the
error between where the camera thinks things are and where the arm does, which is
the error that actually sinks this task. And find the **rack** with a printed
fiducial marker, a flat printed pattern the camera can locate exactly, glued to its
base. The rack is a known rigid object, so there is nothing to learn, and a marker
turns finding it into arithmetic.

---

## 6. The gripper

The gripper is the one hardware choice in this task that you cannot recover from in
software, so it is worth taking slowly. The options are these.

| Gripper | Why it might suit | Why it probably does not |
| --- | --- | --- |
| Two-finger parallel, soft pads | simple, controllable, wide grip window | needs room on two sides of the glass |
| Suction cup | one contact point, no room needed | a 70 mm cylinder is curved, and the seal carries the full weight once inverted |
| Three-finger adaptive | centres itself on round things | more to buy, more to tune, more to go wrong |
| Soft pneumatic fingers | very forgiving of shape and force | poor at knowing where the object is, needs an air supply |

**Use a two-finger parallel gripper with soft silicone pads.** The pads are the
important half of that sentence. They raise the friction, which moves the lower edge
of the grip window down; they spread the contact over an area instead of a line,
which keeps the upper edge where it is; and they forgive a millimetre or two of
misalignment. A shallow V-shaped or curved pad profile also makes the glass centre
itself as the fingers close, which is free accuracy.

The obvious alternative is suction, and it is genuinely the right answer for sheet
glass and flat lids. It is the wrong answer here for three separate reasons, any one
of which would be enough: the side of the glass is curved in one direction, so a
flat cup does not seal; the glass comes out of water, and a wet surface leaks; and
the moment you turn it upside down the cup is holding 220 g against gravity with
nothing to fall back on.

What the two-finger gripper costs you is space. The fingers need room on both sides
of the glass, which means you cannot pick a glass that is pressed against another
one, and it means the fingers themselves are part of the clearance problem on the
rack.

That last point decides **where** on the glass to hold it. Grip the end that will be
on *top* after the turn — that is, the base end of the glass as it stands on the
table. After the flip, the fingers are then up at the top, well clear of the rack
base, the pegs and the rims of the neighbouring glasses while the glass goes down
into the gap. Gripping near the rim would put the fingers into exactly the 10 mm
corridor from [section 2](#2-why-it-is-harder-than-it-looks), and it would also put
them on the thinnest and most breakable part of the glass.

---

## 7. Force

Force matters at two separate moments in this task, and they need different things.

### Holding the glass

A gripper commanded to a width is a position-controlled device, and driving a
position into something rigid is the failure described in
[the programmed methods document](../02_programmed-methods.md#6-feedback-control):
the controller sees an error it cannot remove, so it pushes harder. On a 3 mm glass
wall that ends one way.

So command a force, or at least a current limit, not just a width. Then find the two
edges of the window by measuring rather than guessing:

- **The lower edge.** Hold the glass, turn it over, and increase the load until it
  slips. Do it dry and again wet, because wet is the case that matters.
- **The upper edge.** Take a glass you are willing to lose, and squeeze it until it
  cracks. Do this once, deliberately, on purpose. It is far better than discovering
  the number by accident in the middle of a demonstration.

Work at a force comfortably above the wet slipping point, and record both numbers
against that type of glass.

The most useful thing to monitor while holding is the gripper's own width. If a
force-controlled gripper is slowly closing while it holds, the glass is sliding
through the fingers, and you have a second or two to react. That signal costs
nothing, needs no extra sensor, and catches most of the drops.

### Putting it down

The descent onto the rack should be controlled by force, not by position. Command
the arm downwards with a low stiffness on the vertical axis and a cap on the
downward force, so that when the rim reaches the base the motion stops because of
the contact rather than because a number was reached. This is admittance control,
and it is the same idea as the compliant connector insertion in
[the overview's worked examples](../01_overview.md#6-three-worked-examples), just
with a much easier target.

Releasing is the delicate moment. Open slowly, and only after the vertical force has
confirmed that the rack is now carrying the glass. If that force never appears, the
glass is hung up — caught on a peg, or resting on a neighbour — and the correct
response is to lift away and try again, not to open the fingers and hope.

---

## 8. When a new kind of glass arrives

This is the question that decides whether the system is a demonstration or a
product, so it deserves a direct answer. The answer has two halves: noticing, and
adapting.

### Noticing is the safety-relevant half

The dangerous case is not a new glass. It is a new glass that the system treats as
an old one. The cylinder fit from [section 5](#5-finding-the-glass) will return an
answer for a wine glass, and the answer will be confident and wrong.

So make the fit report how well it fitted, and make the measured dimensions get
compared against what is known. If the shape does not fit a cylinder well, or the
dimensions fall outside every glass on file, the system stops and asks. Refusing to
act is a perfectly good outcome, and it is much better than the alternative.

### Adapting should be data, not code

Keep everything that is specific to a type of glass in one small file, one record
per type, and keep it out of the programme entirely. A record holds:

| Field | What it is for |
| --- | --- |
| Outside and inside rim diameter | whether it fits over a peg, and past its neighbours |
| Height | how high to lift, and how much a tilt costs |
| Mass | the grip force it needs, and the arm's payload check |
| Grasp height above the table | where on the body to hold it |
| Grip force, dry and wet | the window from [section 7](#7-force) |
| Shape family | cylinder, tapered, stemmed — this decides the strategy |

Adding a glass is then a new record and a test run, not a code change. Somebody with
a ruler and a kitchen scale can produce one in five minutes.

How much that buys you depends on which layer you are on. The table below says what
a genuinely new glass actually requires at each one.

| Layer | A wider or taller tumbler | A different shape, such as a stemmed glass |
| --- | --- | --- |
| 1. Written by hand | one new record, then re-test | a new grasp and a new descent, written by hand |
| 2. Learned perception | free: a cylinder fit does not care about size | the segmenter still finds it, but the cylinder fit must be refused |
| 3. A learned skill | usually free, but you must check rather than assume | new demonstrations, and you should measure how many rather than trust a published number |
| 4. A pretrained policy | expected to be free | the case these models are actually for, and the case where the check matters most |

The pattern across that table is worth stating plainly, because it is the real
answer to the question. **A new size is nearly free at every layer. A new shape is
never free at any layer.** Changing size changes numbers; changing shape changes
which surfaces can be held and which way up the thing can stand, and no amount of
training data turns that into the same problem.

---

## 9. The frameworks, and why each one

This is the shortlist for building the system described above. Read the table as one
row per job, with the alternative you would otherwise have reached for and the
reason not to; the three choices that actually shape the design are explained
underneath.

| Job | Use | Rather than |
| --- | --- | --- |
| Simulate it first | [Gazebo](https://github.com/gazebosim/gz-sim) | MuJoCo — better contact, but you need simulated cameras and ROS in the loop more |
| Describe the robot | URDF, the Unified Robot Description Format | a bespoke model, which nothing else can read |
| Plan the motion | [MoveIt 2](https://github.com/moveit/moveit2) | hand-written waypoints, which stop working the day the rack moves |
| Sequence pick, turn and place | [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | planning each stage separately and discovering the grasp forbids the release |
| Drive the joints | [ros2_control](https://github.com/ros-controls/ros2_control) | your own control loop, where the hard part is the timing, not the maths |
| Control the descent by force | the admittance controller in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), or [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | commanding a position into the rack base |
| Sequence and recover | [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | a state machine, which turns illegible once recovery branches multiply |
| Outline the glass | [SAM 2](https://github.com/facebookresearch/sam2) to prototype, a small trained segmenter to ship | colour thresholding, because a glass has no colour of its own |
| Fit the cylinder and the table plane | [Open3D](https://github.com/isl-org/Open3D) | PCL, the Point Cloud Library — capable, but heavier than this needs |
| Fill the depth hole, if you go that way | [ClearGrasp](https://github.com/Shreeyak/cleargrasp), [TransCG](https://github.com/Galaxies99/TransCG) | assuming the depth camera will improve |
| Find the rack without a marker | [FoundationPose](https://github.com/NVlabs/FoundationPose) | a marker, which is simpler and which you should prefer if you can glue one on |
| Learn the skill, at layer 3 | [LeRobot](https://github.com/huggingface/lerobot) | the original [ACT](https://github.com/tonyzhaozh/act) and [diffusion policy](https://github.com/real-stanford/diffusion_policy) repositories, which are quiet now |
| Try a pretrained policy, at layer 4 | [openpi](https://github.com/Physical-Intelligence/openpi) | training your own from nothing |
| Record what happened | rosbag2, which ships with ROS 2 | log lines, which cannot show you the frame before the drop |

Three of those deserve the longer answer.

**MoveIt Task Constructor** is an add-on to MoveIt 2 that lets you describe a task as
a series of stages — approach, grasp, lift, turn, place, retreat — and then plans
them together rather than one after another. What it does for you here is precisely
the problem from [section 2](#2-why-it-is-harder-than-it-looks): it can reject a
grasp because the release it would force is unreachable, which a stage-by-stage
planner discovers only when it is too late to change anything. The obvious
alternative is to plan each move as it comes, and for the fixed-position first
version that is genuinely fine. What it costs you is a heavier dependency and a
noticeably steeper learning curve than plain MoveIt.

**BehaviorTree.CPP** is a library for writing the decision logic as a tree of small
actions and conditions. What it does for you is keep the recovery paths readable,
and this task has a lot of them: no glass in the gripper, the glass slipping, the
descent finding contact early, the rack being full, the glass not standing after
release. The obvious alternative is a state machine, and a state machine is fine for
five states; it becomes unreadable at twenty, because every new recovery has to be
wired to every state it can happen in. What a behaviour tree costs you is a second
representation in the system, described in XML, that a newcomer has to learn before
they can read your logic at all.

**An admittance controller** makes the arm behave as though it were soft: you tell it
how much force to accept, and it moves in response to what it feels rather than
holding a commanded position. What it does for you here is let the descent end on
contact. The obvious alternative — command a height and trust it — fails because the
rack base is rigid and the glass rim is thin, so being 2 mm too low is not a small
error. The cost is real and worth knowing in advance: you need a force reading good
enough to trust, either a wrist force sensor or an arm that estimates it from joint
currents, and you have to tune the stiffness, which takes an afternoon of patient
work with nothing much to show for it.

---

## 10. What will bite you

These are the things that go wrong in practice, ordered by how much of your time
they will take.

**Broken glass is not a retry.** Most robot failures leave you free to try again.
This one leaves shards on the table and possibly on the floor, and an arm that
happily carries on moving through them. So the response to a drop is to stop the
cell and call a person, not to reach for the next glass. Decide this before you
build the recovery logic, because it changes its shape.

**Calibration drift eats your margin.** You have 10 mm of clearance between rims. A
3 mm error between where the camera thinks the rack is and where it really is has
taken a third of it before the arm has moved. Re-check the camera-to-arm calibration
on a schedule, not when something breaks.

**Wet glass is a different object.** It slips at a force that a dry one holds at, and
water on silicone pads is worse than water on glass. If the glasses come from a sink
or a dishwasher, every grip number has to be measured wet.

**The rack moves.** It is a light plastic thing on a table, and the arm will nudge
it. Either fix it down or find it again every cycle. Assuming it stayed put is the
cheapest possible bug to create and one of the more annoying to diagnose.

**The corridor narrows as the rack fills.** The first glass has the whole rack. The
sixth has neighbours on two or three sides. Fill in an order that keeps the occupied
pegs away from the next one for as long as possible, and treat the last two pegs as
the hard cases they are.

**Simulation will not tell you about the grip.** Contact between rigid fingers and a
thin rigid shell is close to the worst case for a physics engine. Use the simulator
for the reaching, the planning, the turn and the clearances, which it does well, and
get the grip numbers from a real glass.

**People are nearby.** A kitchen is not a cage. Speed limits, force limits and a way
to stop the arm by hand are not optional extras here, and they constrain the cycle
time you can honestly promise.

---

## 11. What to measure

Robot demonstrations are easy to make look good, so decide what you are counting
before you start. These five numbers are enough:

| Number | How to count it |
| --- | --- |
| Success rate | glasses standing ten seconds after release, over attempts |
| Breakages per thousand attempts | the number that decides whether this can ever ship |
| Attempts per glass | how often it has to let go and try again |
| Cycle time | from reaching for the glass to the arm clear of the rack |
| Failures caught before release | as a share of all failures — the measure of whether the checks work |

That last row is the one people leave out and the one worth watching most closely. A
system that notices it has the glass wrong and puts it back down is in a completely
different class from one that finds out by hearing it break, even when the two have
the same success rate.

Log every attempt: the camera frames, the force trace, the gripper width, and the
planned and actual poses. Without those, a failure two weeks from now is a story
rather than a bug.

---

## 12. Where to go next

- [The overview](../01_overview.md) puts this task in the wider map of methods, and
  its [grid of which method suits which task](../01_overview.md#5-which-method-for-which-task)
  is where the choices here came from.
- [Programmed methods](../02_programmed-methods.md) covers the planning, the
  behaviour trees and the force control used above, properly rather than in passing.
- [Learned methods](../03_learned-methods.md) covers what layers 2, 3 and 4 involve.
- [The learning path](../04_learning-path.md) has five projects to build in
  simulation; project 1 and project 2 between them cover most of what this task
  needs.
- [Tools and libraries](../../06_tools-and-libraries.md) is the fuller version of
  [section 9](#9-the-frameworks-and-why-each-one).
