# What goes in and what comes out

## 1. Introduction

Every solution in this book gets the same things. Every solution must give back
the same kind of thing. This page says exactly what those are:

- what a solution may read;
- what it is never told;
- what a push does and what it reports;
- what a solution gives back.

The page comes after [what is asked for](01_what-is-asked-for.md), which says
why the arm drags the glasses. It comes before [the
examiner](03_the-examiner.md), which draws the tables and marks the result.

The examiner's code carries out everything on this page. That code is in
`code/src/09_pushing-the-glasses-apart/bench/`. So all of it is the same for
all six solutions.

## Contents

1. [Introduction](#1-introduction)
2. [Three calls, in a loop](#2-three-calls-in-a-loop)
3. [What `look()` hands over](#3-what-look-hands-over)
4. [What a solution is never told](#4-what-a-solution-is-never-told)
5. [What `push()` does, and what it reports back](#5-what-push-does-and-what-it-reports-back)
6. [What must come out](#6-what-must-come-out)
7. [Where to go next](#7-where-to-go-next)

## 2. Three calls, in a loop

A solution can touch the table only through the examiner. So we start with how
it does that.

The examiner offers three calls and nothing else: `look()`, `push()` and
`take()`. A call is a function the solution can run. The three calls form a
loop. A solution looks, decides, pushes, and looks again. The loop ends when
the solution runs out of pushes, not when it decides to stop.

![look, decide, push, and look again until the budget runs out, at which point take ends the run and the examiner marks it.](../../images/pushing-the-glasses-apart/what-goes-in-and-what-comes-out/examiner-flow-the-three-calls.png)

The loop starts with a look, so the next section says what a look returns.

## 3. What `look()` hands over

The loop begins by reading the table. This section says what that reading
contains.

**`look()` returns one reading for each glass still on the table.** Each
reading says five things about the glass:

- where it stands;
- how tall it is;
- how wide it is at its widest;
- how wide it is at its foot;
- whether it is still standing.

These are the same facts the camera work for [telling the glasses
apart](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
produces. So this problem can start where that one ended. Here is the start of
a look at table 10025. There is one row for each standing glass. Every length
is in metres.

```json
[
  {"id": 0, "x": 0.4570, "y": -0.4170, "height": 0.1554, "widest": 0.0740, "foot": 0.0419, "standing": true},
  {"id": 1, "x": 0.5489, "y": -0.2464, "height": 0.1360, "widest": 0.0871, "foot": 0.0462, "standing": true}
]
```

**Each reading has the camera work's measured error.** The numbers are not the
true ones. The examiner adds a small random error to the position, the two
widths and the height. The size of each error comes from what the camera
solution really scored, as [its own
results](../../08_seeing-the-glasses/11_the-results.md) record. The width error
is the largest. The position error is the smallest.

The error is new on every look, so looking twice tells you more. The error is
drawn from the table's number and the number of the look. This means the first
look at a table is the same for all six solutions. No solution gets an easier
first reading.

**Solutions that read pictures also get a picture of the table from above.**
Three of the six read pictures, not numbers. They are an imitation policy
trained on images and the two vision-language models. A list of numbers is no
use to them. So the examiner draws a picture of the same table at the same
moment. The information is the same. Only its form is different.

The picture comes from `bench/top_view.py`. A camera is fixed 750 mm above the
middle of the glass zone, looking straight down. It returns a colour picture,
384 by 384 pixels, that shows the whole zone. This camera is not the one that
`film.py` uses. The film camera looks down from the arm's side, and it exists
only so that people can watch a run.

Keeping the two cameras apart matters. A solution that reads a picture decides
from that picture. If filming a table changed anything in the simulated world,
a filmed table could differ from the table that was scored. Then the six would
no longer be compared fairly. So the films are drawn in a second, separate
world that is never simulated. The scored world is the same whether a table is
filmed or not. A test checks this. It runs one table both ways and requires
every glass to end in the same place.

What a look leaves out matters too. The next section lists it.

## 4. What a solution is never told

The readings above are all a solution sees. This section says what the
examiner knows but keeps back.

![The readings a solution may have in one column, and the truth the examiner keeps in the other, with the friction picked out because nothing in the cell could measure it anyway.](../../images/pushing-the-glasses-apart/what-goes-in-and-what-comes-out/examiner-flow-given-and-kept.png)

**A solution never gets the simulator's record.** The examiner knows each
glass's true position, true shape and mass. It keeps all of them. Only the
scoring code reads them, and only after a run ends. A learned solution may use
them as training labels on the training tables. But nothing reads them while a
solution is answering. A solution that read the truth would not be answering
this problem.

**A solution is also never given the friction.** Friction is how strongly two
surfaces resist sliding over each other. Its size is a number called the
friction coefficient, written μ. The examiner keeps three of these numbers
private: glass on table, glass on glass, and the hand's pads on glass. Every
table uses the same three.

They are hidden because the real cell could not know them either. **Nothing in
the cell measures friction.** There is no sensor for it, and there is no other
way to find it. This one missing number is what makes the problem hard. The
tipping limit depends on it, as [pushing without
toppling](05_pushing-without-toppling.md#3-the-limit-slide-or-tip) shows. So a
solution must guess the very number that decides whether a glass is safe to
push.

Friction cannot be read directly. The only evidence of it comes from pushing,
so the next section says what a push reports.

## 5. What `push()` does, and what it reports back

`look()` tells a solution where things are. `push()` is the only way to change
them. It is also the only call that brings back anything about friction.

One push runs as a fixed series of steps.

1. The closed hand is held level, pointing the way it will move.
2. It comes down at the start point the solution chose, to the lowest height
   the gripper can reach.
3. It moves forward very slowly until it feels a small force. This means it has
   touched something.
4. It pushes the asked-for distance at a steady speed.
5. It backs off a couple of centimetres.
6. It lifts up above the tallest glass.

Three things can stop this early. The hand can touch something on the way down.
Then it goes straight back up without pushing. The hand can reach the end of
its slow forward move without touching anything. Or the force can pass a much
higher limit during the push. This means something is stuck, and the push stops
where it is.

**The push then reports what it felt.** This report is the only thing that
comes back. It says five things:

- whether the hand was blocked on the way down;
- how far forward it moved before it touched, or that it never touched;
- whether it got stuck;
- the largest force it felt at any moment;
- how far it really moved after it touched.

Both the request and the report are short enough to show in full. The first
object below is the push that solution 1 asks for on table 10025. The second is
the report the examiner gives after doing it. Lengths are in metres. The
heading is in radians. The force is in newtons.

```json
{"glass": 4, "start": [0.3726, -0.4500], "heading": 1.5708, "reach": 0.0881, "travel": 0.0660,
 "aim": [0.3726, -0.3259]}
```

```json
{"blocked": false, "touched": 0.0146, "jammed": false, "peak": 1.73, "pushed": 0.0660}
```

The arm never uses the `aim` field. The examiner keeps it. Once the glass stops
moving, the examiner measures how far the glass ended from where the solution
expected it.

### How the jaw's force is measured

The force reading is the only input that comes from touch and not from the
camera. So this part says which sensor makes it and how.

**The sensor is a six-axis force-torque sensor between the arm and the
gripper.** The arm ends in a flat plate called the flange. The gripper is not
fixed straight to it. A force sensor sits between them. So anything that pushes
on the hand also pushes on the sensor. "Six-axis" means the sensor reports six
numbers. Three are forces along three directions. Three are twists about those
directions. The cell names this sensor `wrist_force` in
[`arm/gripper.urdf.xacro`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/src/work_cell/work_cell/arm/gripper.urdf.xacro).
In the Gazebo cell it reports 100 times a second.

The camera cannot measure force. The cell's two other sensors are in the
finger pads. They only report whether a pad is touching something.

**A real sensor of this kind measures how much a piece of metal bends.** Inside
it is a stiff metal part. Under load it bends a tiny amount, too little to see.
Strain gauges are glued to that part. A strain gauge is a thin wire pattern.
When it stretches, its electrical resistance changes. So the bending becomes a
change in voltage. The maker's calibration turns these voltages into the three
forces and three twists.

The sensor feels every load below it, including the gripper's own weight. So
that weight is measured once, with nothing touching, and then subtracted. What
is left is the force from contact. [Force and torque at the
wrist](../../03_frameworks/02_gripping/02_grippers-and-hardware.md#81-force-and-torque-at-the-wrist)
gives the published figures of one such sensor.

**In the examiner, the force is added up from the physics.** The pushing is
tested in MuJoCo, not Gazebo. [The
examiner](03_the-examiner.md#3-what-the-examiner-draws) gives the reasons.
MuJoCo has no sensor model to read. So the examiner in
[`bench.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/bench/bench.py)
does the work itself. Every 2 milliseconds, it finds every contact that
involves the hand. It adds up their forces and reports the total in newtons.
This is what the wrist sensor would read after the gripper's weight is
subtracted. It has no noise and no drift. A real sensor has both.

**The push uses that number at three moments.**

- The hand comes down at 200 mm per second. Any force above 0.1 newton means it
  has hit something, and it goes back up.
- The hand moves forward at 10 mm per second. The first force above 0.1 newton
  is the touch, and the push starts there. The limit is this low because the
  lightest glass starts to slide under about a quarter of a newton. A higher
  limit would push that glass along without noticing.
- The hand pushes at 20 mm per second. A force above 20 newtons means something
  is stuck, and the push stops.

The whole time, the largest force seen is kept. That is the peak force the push
reports.

**The distances in the report come from the hand's position, not from the
sensor.** The sensor only says *when* the force crossed a limit. Where the hand
was at that moment comes from where the arm put it. On the real arm, the joint
encoders give this. An encoder is a sensor that measures a joint's angle.
[Measuring by
touch](../../02_perception/02_object-perception/02_sensors.md#2-measuring-by-touch)
explains this split of work.

There is one warning for the real cell. The 0.1 newton touch limit is about the
noise level of a typical wrist sensor. Its maker suggests ten times that for
finding contact. So a real arm would need a higher limit or a slower approach.
The examiner's clean reading is one way it is easier than the real world.

### Why the force reading matters

The force reading is how a solution learns anything about friction. This part
explains why.

The rule for whether a glass slides or tips uses three things: the push height,
the foot width and the friction. A solution knows the push height, because it
is the gripper's own number. It can measure the foot width, because `look()`
gives it. It cannot have the friction. So the rule gives a limit that is only
as good as a guess.

**So the force reading is the only way to observe friction at all.** Two things
depend on the friction: how much force it took to start the glass moving, and
how far the glass went. So they are indirect evidence about it. A glass that
leaned and fell back also feels different from a glass that slid.

Every solution that does better than a blind nudge does so by using this
reading. It either reasons about the reading or learns from it. If the examiner
reported only success or failure, the interesting half of this problem would
be hidden.

A solution has now read the table and felt its pushes. The last question is
what it gives back.

## 6. What must come out

The inputs are the same for every solution. This section fixes the output.
This is harder, because the six do not naturally give back the same kind of
thing.

**The shared output is a path for the hand.** The hand follows one path, then
another, until the table is done or the pushes run out.

Some solutions do not think in paths at all. A geometric solution thinks in a
**parameterised push**. This is a few numbers that describe one push: which
glass to move, where to put the hand down, which way to point, how far to feel
forward, and how far to push. `push()` accepts exactly these numbers. `push()`
then turns them into the steps described above: come down, feel, push, back
off and lift.

So **turning a push into a path is a fixed routine that the examiner owns**. A
solution does not write it. Every parameterised push is turned into a path in
the same way, by the same code. So no solution gains or loses anything at this
step.

Other solutions think in paths directly. A modern imitation policy does not
give one target at a time. It gives an **action chunk**. An action chunk is a
short run of waypoints that the network predicts together in one step. These
solutions call `follow()` instead of `push()`. `follow()` takes a `Chunk` of
waypoints for the hand and carries them out in the same physics. It reports the
same `Felt` into the same record. So the scores cannot tell which call an
action came through.

The examiner also records the path the hand really followed on every action.
It samples the path at a fixed rate. This turns a parameterised push into a
demonstration. A policy that gives waypoints can be trained on these
demonstrations.

**The obvious alternative would be worse.** The examiner could make every
solution give the same few push numbers. That sounds fair, but it would be
unfair. It would break the action chunks that make those policies work. A chunk
keeps a policy steady over a whole motion. Without chunks, the policy wobbles
from one step to the next. If you force such a policy into three numbers, you
measure a damaged version of it. Two kinds of output work because the examiner
[marks the outcome, not the
action](03_the-examiner.md#4-the-score-is-the-outcome-not-the-action).

**A solution may also refuse a glass, with a reason.** For example, a glass may
tip before it slides, or have no clear place to go. [The
examiner](03_the-examiner.md#5-what-the-examiner-measures) explains why a
refusal counts as a result and how it is scored.

**`take()` ends a glass's part in the run.** It lifts a glass off the table and
puts it in the rack. That is the earlier job of carrying one glass to the rack,
done for free here. The examiner also records whether the glass really had room
when it was taken. This record shows later whether the arm was right to think
the glass had room.

Those are the inputs and outputs every solution shares. The next page describes
the examiner that draws the tables and marks what comes back.

## 7. Where to go next

- [The examiner](03_the-examiner.md) draws the crowded tables, runs the
  physics, and marks every run the same way.
- [The target layout](04_the-target-layout.md) works out where the glasses
  should end up.
- [Pushing without toppling](05_pushing-without-toppling.md) gives the height
  limit and the loop of plan, feel and look again.

← [Push the glasses apart — what is asked for](01_what-is-asked-for.md) · [The examiner](03_the-examiner.md) →
