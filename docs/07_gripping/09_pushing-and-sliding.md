# Pushing and sliding: moving an object without gripping it

Everything before this document closes fingers on things. The arm arrives, the
fingers shut, the object is held, and the rest is a question of whether the grip
survives. That is one way to move an object and it is not the only way. A robot
can also push it, drag it, sweep it aside or knock it over, and in each of those
cases nothing ever grips anything.

The word for this is **non-prehensile manipulation**. *Prehensile* means "able to
grasp", so non-prehensile manipulation is any way of moving an object that does
not involve holding it. Pushing is the main one. Pulling, dragging, sweeping and
deliberate toppling are the others.

This matters more than its absence from tutorials suggests, for a reason that is
easy to state and easy to miss. **A push does not need a grasp to exist.** Every
method in [choosing a grip](03_choosing-a-grip.md) begins by assuming that a
valid grasp is available somewhere on the object and that the arm can reach it.
When no such grasp exists — the object is flat on a table, or flush against a
wall, or wedged among its neighbours — the grasping pipeline has nothing to
return. A push has no such precondition. It needs one reachable point on the
object and a direction to move it in, and it very often produces the grasp that
did not exist a moment earlier.

The authors of the largest experimental study of pushing open their paper with
the same claim: "Pushing is a motion primitive useful to handle objects that are
too large, too heavy, or too cluttered to be grasped." That paper is
[More than a Million Ways to Be Pushed](https://arxiv.org/abs/1604.04038), and
most of the measured numbers in this document come from it.

## Who this is for

Someone who has read [the gripping overview](01_overview.md) and
[choosing a grip](03_choosing-a-grip.md), has a robot arm that can be commanded
to a Cartesian pose, and now has an object that cannot be picked up — or one that
could be picked up more reliably if something moved it first. You need to know
what friction is. You do not need to know what a limit surface, a motion cone or
a centre of friction is; each is explained where it first appears.

Two boundaries. **Deciding where to grip is not here**; that is
[choosing a grip](03_choosing-a-grip.md), and section 3 of this document extends
its friction-cone arithmetic from squeezing to pushing rather than repeating it.
**Planning the arm's path is not here either**; that belongs to
[arm movement](../08_arm-movement/01_overview.md). What is here is the physics
that decides what the object does when the arm touches it without closing on it.

## Contents

1. [Why you would push rather than grasp](#1-why-you-would-push-rather-than-grasp)
2. [The slide-or-tip condition](#2-the-slide-or-tip-condition)
3. [Quasi-static planar pushing](#3-quasi-static-planar-pushing)
4. [Pulling, dragging and deliberate toppling](#4-pulling-dragging-and-deliberate-toppling)
5. [The tools, the libraries and how thin they are](#5-the-tools-the-libraries-and-how-thin-they-are)

---

## 1. Why you would push rather than grasp

### 1.1 The five ordinary reasons

Each of these is a case where a grasp is either impossible or unnecessary, and in
each case a push is available.

**The object is too large for the gripper.** A two-finger gripper has a stroke,
and [the 2F-85's is 85 mm](06_two-finger-gripper.md#1-what-this-gripper-actually-is).
Anything wider than the stroke cannot be gripped at all, however good the grasp
planner is. It can still be pushed.

**The object is too heavy to lift.** Lifting a mass `m` requires the wrist to
carry `m * g`. Pushing it along a table requires only enough force to overcome
friction, which is `mu * m * g`, where `mu` is the coefficient of friction between
the object's base and the table. The saving is the factor `mu`, and on the four
surfaces measured in the Massachusetts Institute of Technology (MIT) push study
that factor runs from 0.12 to 0.29. For a 10 kg object on plywood at
`mu = 0.28`, lifting needs 98.1 N at the wrist and pushing needs 27.5 N. The
arithmetic is `10 * 9.81 = 98.1` and `0.28 * 10 * 9.81 = 27.5`.

That comparison has a limit worth stating, because it is the kind of thing that
gets quoted without its ceiling. Pushing only saves force while `mu` is below 1.
At `mu = 1` the two are equal, and above 1 pushing is the harder job. An arm that
can apply about 49 N sideways can push 17.8 kg on plywood at `mu = 0.28`
(`49 / (0.28 * 9.81) = 17.8`), 38.4 kg on ABS at `mu = 0.13`, and exactly 5 kg on a
rubbery surface where `mu` has reached 1.0. Treat those as order-of-magnitude
figures: an arm's rated payload is a mass at the wrist, not a horizontal force
capability, and the real limit is the joint torque in the specific configuration
you push from.

**The object is too flat to get under.** A sheet of metal, a card, a phone lying
face-down on a table. There is no pair of opposed faces a finger can reach,
because the only two faces are the top and the table. Suction solves this when
the surface will seal. A push solves it when suction will not, by sliding the
object to an edge where a finger can get underneath.

**The object is against a wall or among its neighbours.** A grasp needs room for
the gripper body as well as the fingers, and
[section 7 of choosing a grip](03_choosing-a-grip.md#7-bounding-the-search-by-the-grippers-own-body)
is about exactly the grasps that fail this test. An object flush against the side
of a tote has no antipodal pair the gripper can physically straddle. Pushing it
15 mm away from the wall creates one.

**The object does not need lifting.** Closing a drawer, sliding a tray along a
conveyor, moving a box from one end of a table to the other, nudging a part into
a fixture. In all of these the destination is on the same surface as the origin,
and a pick followed by a place is two extra vertical moves that buy nothing.

### 1.2 The reason underneath those five

The five reasons above are circumstantial. The structural reason is about what
each operation requires before it can be attempted at all.

A grasp requires a great deal to be true simultaneously. There must be two
surface regions whose normals point at each other within the friction cone, both
must be reachable, the gripper body must fit around the object, the object must
survive the squeeze, and the grip must hold through the acceleration of the move.
[Choosing a grip](03_choosing-a-grip.md) is a long document because each of those
is a separate condition that can fail.

A push requires two things. There must be one reachable point on the object, and
there must be a direction in which the object is free to move. That is a strictly
smaller set of conditions, and it is smaller in a way that matters: it is
satisfied for objects that fail every grasp test.

This is why pushing is usually best understood as the step **before** grasping
rather than as a rival to it. The sequence that makes most cells work is: look,
find no valid grasp, push once, look again, grasp. Systems that treat pushing as
an alternative pipeline end up maintaining two planners. Systems that treat it as
a pre-grasp move add one primitive to the one they already have.

### 1.3 What pushing suits and what it does not

Five jobs pushing suits:

- separating an object from a wall, a bin side or a neighbour so that a grasp
  becomes geometrically possible
- moving an object that is wider than the gripper stroke or heavier than the
  rated payload
- getting a flat object to a table edge, where a finger can reach under it
- breaking up a pile so that individual items can be seen and then picked, which
  is usually called singulation
- any move whose start and finish are on the same surface, where the two vertical
  moves of a pick and place are pure cost

Five jobs pushing cannot do:

- move an object to anywhere that is not a continuous surface reachable from where
  it is now, since the object never leaves the table
- place an object with orientation accuracy, because the rotation of a pushed
  object depends on a pressure distribution you do not know, which is
  [section 3.7](#37-the-pressure-distribution-nobody-measures)
- handle anything that must not be dragged across a surface, because sliding
  scratches the object and the table
- move an object whose base friction is high enough that it tips instead, which is
  [section 2](#2-the-slide-or-tip-condition)
- work at all against an object that is fixed, jammed or heavier than the arm can
  push, where the arm will instead push itself and trip a collision stop

## 2. The slide-or-tip condition

This is the single most useful piece of arithmetic in non-prehensile
manipulation, it is one line long, and it decides whether a push is attempted at
all. Push an object low down and it slides across the table. Push the same object
higher up and it topples over. There is a height at which the behaviour changes,
that height can be computed before the arm moves, and it depends on almost
nothing.

### 2.1 The derivation

Set up the problem. A rigid object of mass `m` stands on a flat horizontal table.
The coefficient of friction between the object's base and the table is `mu`. The
robot applies a horizontal force `P` to the object at a height `h` above the
table. Call `d` the horizontal distance from the vertical line through the
object's centre of mass to the bottom edge the object would pivot about — for a
push, that is the leading edge, the one furthest from the robot. For an object
with a symmetric base of width `w` measured along the push direction, `d` is
simply `w / 2`.

Now raise `P` from zero and ask which of two things happens first.

**Sliding** happens when the push exceeds the friction holding the base in place.
The base carries the whole weight, so the normal force is `m * g` and the largest
friction it can supply is `mu * m * g`. So the object begins to slide when

    P > mu * m * g

**Tipping** happens when the push produces more moment about the leading bottom
edge than the weight produces in the other direction. A moment is a force
multiplied by its perpendicular distance from the point you are turning about.
Taking moments about that leading edge is the trick that makes this simple,
because it removes two forces from the sum. As the object begins to tip, the
whole of the normal force has migrated forward to that edge, so its moment arm is
zero. The friction at the base acts in the plane of the table, which passes
through the edge, so its moment arm is zero too. Only two moments remain: the push
`P` acting at height `h` above the edge, which drives the tip, and the weight
`m * g` acting at horizontal distance `d` from the edge, which resists it. So the
object begins to tip when

    P * h > m * g * d

**Which one wins.** Sliding needs `P_slide = mu * m * g`. Tipping needs
`P_tip = m * g * d / h`. The object slides rather than tips when `P_slide` is the
smaller of the two:

    mu * m * g  <  m * g * d / h

The mass and gravity appear on both sides and cancel, leaving `mu * h < d`.

### 2.2 The formula

    h* = d / mu

    and for an object with a symmetric base of width w,   h* = w / (2 * mu)

Push below `h*` and the object slides. Push above `h*` and it topples. `h*` is
the critical push height, and `mu` here is the coefficient between the **object
and the table**, not between the pusher and the object.

Three things are not in that formula, and each one is worth noticing.

**The mass is not in it.** A heavy object and a light one of the same shape tip at
exactly the same push height. This surprises people, and it is the reason that
"push gently" is not a fix for toppling.

**The push force is not in it.** How hard you push changes how fast the object
moves and does not change whether it tips. Pushing more slowly does not help
either; the derivation above is a statement about forces at the moment motion
begins, and during steady sliding the push force stays at `mu * m * g`, so the
comparison is unchanged.

**The object's own height is not in it.** Only the height at which you make
contact matters. A tall object pushed near its base slides. A short object pushed
near its top may tip, if its base is narrow enough.

The one remedy that works is the one the formula points at: **lower the contact**.

### 2.3 A worked table

The numbers below are for one object with an 80 mm base, pushed on each of the
four surfaces measured in the MIT push study. That study slid bead-blasted
stainless steel objects across four named surfaces and recorded the dynamic
coefficient of friction for each pairing, so every coefficient here is a property
of a *pair* of materials, as it must be. Read each row as: on this table, this
object tips if you touch it above the height in the last column.

| Surface, against bead-blasted stainless steel | Measured `mu` | `h* = 0.080 / (2 * mu)` |
| --- | --- | --- |
| Delrin acetal sheet, after wear | 0.12 | 333 mm |
| ABS sheet, after wear | 0.13 | 308 mm |
| ABS sheet, when new | 0.15 | 267 mm |
| Delrin acetal sheet, when new | 0.16 | 250 mm |
| marine-grade plywood, after wear | 0.24 | 167 mm |
| marine-grade plywood, when new | 0.28 | 143 mm |
| polyurethane rubber, 80A durometer, which is a hardness grade roughly that of a shoe sole | 0.29 | 138 mm |
| the same polyurethane, at high sliding speed | 1.0 | 40 mm |

The arithmetic for one row, so the rest can be checked: on new plywood,
`0.080 / (2 * 0.28) = 0.080 / 0.56 = 0.1429 m`, which is 143 mm.

The important reading of that table is the spread. **The same object, pushed at
the same height by the same robot, slides on two of these tables and topples on
the other two.** Push it at 200 mm and it slides on ABS and Delrin and tips on
plywood and polyurethane. Nothing about the object changed. The table changed.

The last row is worse than it looks. Polyurethane's coefficient is about 0.29 at
low sliding speed and rises to about 1.0 at high speed, which the MIT authors
observed directly and attribute to a known property of rubbers. On that surface
the safe push height falls from 138 mm to 40 mm purely because the robot moved
faster.

### 2.4 The band where the answer is undecided

You never know `mu` exactly. You know a range. That range turns the single
threshold `h*` into two thresholds with a gap between them, and the gap is where
you cannot predict the outcome.

A larger `mu` gives a smaller `h*`, so tipping is easier on a grippier table.
That gives two rules with opposite ends of the range in them:

    to be sure it slides:  h  <  d / mu_max
    to be sure it tips:    h  >  d / mu_min

Between those two heights the outcome depends on where in the range `mu` actually
falls, which you do not know. Read the table below as the width of that gap: the
first two rows use a friction range that was genuinely measured, and the last two
use the kind of range you get when you look a coefficient up rather than measure
it.

| Object and surface | `mu` range | Slides for sure below | Tips for sure above | Undecided band |
| --- | --- | --- | --- | --- |
| 80 mm base, plywood, measured | 0.24 to 0.28 | 143 mm | 167 mm | 24 mm |
| 300 mm carton, plywood or rubber, measured | 0.24 to 0.29 | 517 mm | 625 mm | 108 mm |
| 70 mm bottle, friction looked up | 0.2 to 0.6 | 58 mm | 175 mm | 117 mm |
| 80 mm base, friction looked up | 0.2 to 0.6 | 67 mm | 200 mm | 133 mm |

The lesson is in the difference between the measured rows and the looked-up ones.
Measuring `mu` for your own object on your own table narrows the undecided band
from over 100 mm to about 25 mm, and the measurement is an afternoon with a
tilting board. This is the same argument
[the friction cone section makes for grasping](03_choosing-a-grip.md#31-the-cone),
where two Robotiq figures for the same fingertip differ by a factor of two purely
because of cutting oil. If there is one number to measure rather than assume in
this whole area, it is a coefficient of friction.

### 2.5 As pseudo code

```
function safe_push_height(object, surface, safety_factor):
    # d: horizontal distance from the centre of mass to the leading bottom edge.
    # Use the measured base width when the object is symmetric, and the
    # measured centre of mass when it is not.
    d = distance_from_com_to_leading_edge(object)

    # mu_max is the top of the measured range for this pair of materials,
    # because a higher mu makes tipping easier and we want the pessimistic case.
    mu_max = friction_range(object.base_material, surface.material).high

    h_critical = d / mu_max
    return h_critical / safety_factor

function plan_push(object, surface):
    h = safe_push_height(object, surface, safety_factor = 1.5)
    if h < minimum_reachable_contact_height(robot, object):
        # The gripper body cannot get low enough to push safely.
        decline("cannot push this object without tipping it")
    return contact_at_height(object, h)
```

A safety factor of 1.5 on top of the pessimistic `mu` is a judgement, exactly as
the squeeze-force safety factor in
[choosing a grip](03_choosing-a-grip.md#41-the-safety-factor-is-where-the-physics-stops-and-the-judgement-starts)
is a judgement. The reason to keep the two separate — the pessimistic `mu` and
then a factor — is that they cover different unknowns. The range covers
variation you measured. The factor covers the ones you did not, and section 2.6
lists them.

The `decline` branch is not decoration. When the lowest point the gripper can
reach on the object is above the safe push height, pushing that object will topple
it, and the honest response is to say so rather than to try. This is the same
mechanism
[the perception area argues for](../06_object-perception/07_making-it-work.md#6-declining-as-a-mechanism-rather-than-an-intention).

### 2.6 What breaks the derivation

The formula is exact for the situation it describes. Five things change that
situation, and each makes the real critical height lower than `d / mu`.

**The centre of mass is not in the middle.** `d` is the distance from the centre
of mass to the pivot edge, and for a bottle with a heavy base or a tool with a
heavy head it is not half the base width. An object whose mass sits towards the
leading edge has a smaller `d` and tips sooner. When the object's contents vary —
a part-full container is the standard example — `d` varies with the contents.

**The push is not horizontal.** A pusher that presses downward as well as forward
increases the normal force, which increases the friction that must be overcome,
which increases the push force, which increases the tipping moment at the same
contact height. Pressing down makes tipping more likely, not less. A pusher with
a slight upward component does the reverse.

**The push is not quasi-static.** The derivation assumes motion begins gently. A
pusher that arrives with speed delivers an impulse, and the object can be tipped
by an impact well below `h*`. Section 3.1 gives the acceleration below which this
does not apply.

**The base is not flat and rigid.** An object resting on three feet, or with a
warped bottom, pivots about the line joining two of its contact points, which is
generally not the geometric edge and is usually further inboard. That reduces `d`.

**The object is not rigid.** A carton with a soft wall deforms where the pusher
touches it, the contact spreads and moves, and the effective contact height is not
the height you commanded.

### 2.7 What this calculation suits and does not

Five jobs the slide-or-tip condition suits:

- deciding, before any motion, whether a given object can be pushed at all
- choosing the height at which to touch it, which is usually the only free
  parameter in a push
- explaining a failure afterwards, since a toppled object is either a contact that
  was too high or a friction value that was wrong
- deciding deliberately to topple something, by aiming above `d / mu_min` instead
  of below `d / mu_max`, which is [section 4.2](#42-toppling-on-purpose)
- setting a requirement on the perception system, since it must report the base
  width and the contact height and nothing else

Five jobs it cannot do:

- predict anything about a dynamic push, an impact or a fast pusher
- tell you where the object ends up, which is section 3's problem entirely
- handle a deformable object, whose contact height is not what you commanded
- work without a friction estimate, since the whole formula is a division by `mu`
- say anything about an object on a sloped, moving or compliant surface

## 3. Quasi-static planar pushing

Section 2 answers whether the object slides. This section is about what happens
when it does: which way it goes, which way it turns, and how much of that you can
predict in advance. The honest summary is at the end of it, and it is that the
theory is good, the theory needs a number nobody measures, and the correct
response is feedback rather than a better model.

### 3.1 What quasi-static means

A push is **quasi-static** when friction dominates inertia, so the object stops
the instant the pusher stops. There is no coasting, no momentum to account for,
and the object's motion at each moment depends only on where the pusher is
touching it and in which direction — not on how it got there.

The condition for this is a comparison of two accelerations. The object's inertial
force is `m * a`. The friction available to stop it is `mu * m * g`. So the motion
is quasi-static when `a` is much smaller than `mu * g`. For `mu = 0.13`, that
boundary is `0.13 * 9.81 = 1.28 m/s^2`. For `mu = 0.28` it is
`0.28 * 9.81 = 2.75 m/s^2`. To be an order of magnitude inside the assumption you
want accelerations around 0.1 m/s², which is slow — about 100 mm/s reached over a
full second.

This is why the MIT push dataset was recorded with the pusher moving at 20 mm/s,
and why the same dataset deliberately includes accelerations from 0.1 up to
2.5 m/s²: that range straddles the boundary, so the data shows where the
assumption stops being safe.

The practical reading is that quasi-static pushing is a slow primitive. If your
cycle time cannot afford a slow push, the models in this section do not describe
what your robot is doing.

### 3.2 The friction cone at the pusher, which is not the one from grasping

[Section 3.1 of choosing a grip](03_choosing-a-grip.md#31-the-cone) introduces the
friction cone: at any contact, the total force that can be transmitted without
slipping lies within a cone about the surface normal whose half-angle is
`arctan(mu)`. That is used there to decide whether two fingers can squeeze an
object without it sliding out. The same cone does a different job in pushing.

Here the relevant coefficient is between the **pusher tip and the object's face**,
which is a different pairing from the object-to-table coefficient in section 2.
Both appear in the same problem and they are not interchangeable. The MIT setup
measured the pusher-to-object coefficient as approximately 0.25, determined with a
variable-slope experiment, for a steel pusher against a bead-blasted stainless
steel object. That gives a cone half-angle of `arctan(0.25) = 14.0 degrees`.

The consequence is direct. If the direction you move the pusher in lies inside
that cone about the object's face normal, the pusher **sticks** to the object and
the two move together. If it lies outside, the pusher **slides** across the
object's face, the object goes somewhere other than where you aimed it, and the
pusher may come off the object's edge entirely. A 14-degree half-angle is a
28-degree window, which is narrower than most people assume when they command a
push direction from a camera measurement.

The half-angles for the coefficients that appear in this document, computed from
`arctan(mu)`:

| `mu` | Half-angle | The pairing this came from |
| --- | --- | --- |
| 0.13 | 7.4 degrees | steel object on worn ABS sheet |
| 0.16 | 9.1 degrees | steel object on new Delrin sheet |
| 0.25 | 14.0 degrees | steel pusher against bead-blasted steel object |
| 0.28 | 15.6 degrees | steel object on new marine plywood |
| 1.0 | 45.0 degrees | the same 80A polyurethane at high sliding speed |

Read that table as the width of the window in which a push behaves predictably.
The first practical move in any pushing system is to widen it, by putting a
rubber pad on the pusher.

### 3.3 The centre of friction, and which way the object turns

The **centre of friction** is the point in the object's support area about which
the table's friction forces produce no net moment while the object is purely
translating. For an object with a flat base and evenly distributed weight it is
the centroid of the base, which coincides with the vertical projection of the
centre of mass. It is not the same concept, and the two separate whenever the
object stands on three feet, has a warped bottom, or carries its weight unevenly.

Which way a pushed object rotates is decided by where the push line falls relative
to that point, and the reason is a single cross product. Put the centre of
friction at the origin, push in the `+y` direction, and make contact at
`(-a, 0)`, which is a distance `a` to the left of the centre of friction. The
moment about the centre of friction is the `z` component of the cross product of
position and force, which is `x * Fy - y * Fx`, and that evaluates to
`(-a) * F - 0 = -a * F`. It is negative, which is a clockwise rotation seen from
above.

In words: **the side you push advances faster than the side you do not, so the
object rotates about a point between them, and the unpushed side lags behind.**
Push through the centre of friction and `a` is zero, the moment vanishes, and the
object translates without turning. That is the single most useful sentence in
planar pushing, because it says what to aim at.

### 3.4 Mason's voting theorem

The result in 3.3 assumed the force acts along the push direction. It does not,
in general, because the pusher's own friction cone lets the contact force tilt
anywhere within `arctan(mu_contact)` of the face normal. Matt Mason settled this
in 1986, in a paper called "Mechanics and planning of manipulator pushing
operations", and his result is the one piece of planar pushing theory that
survives not knowing the pressure distribution.

The rule uses three lines drawn in the plane of the table, all passing through the
contact point: the line of pushing, which is along the pusher's velocity, and the
two edges of the friction cone at the contact. Each of those three lines divides
the plane into a left side and a right side, and each therefore votes on which
side the centre of friction lies. **The majority of those three votes gives the
direction the object rotates.**

The value of this is what it does not require. It does not need the pressure
distribution, the mass, the moment of inertia, or the object-to-table coefficient.
When all three lines agree — which happens whenever the centre of friction is
comfortably to one side of the whole friction cone — the rotation sense is certain
no matter how the weight is distributed under the object. That certainty is rare
in this field and worth using.

When the votes are split, the sense still resolves by majority, but it is close,
and small errors in the contact position or the friction estimate will flip it in
practice. A push planner that wants a predictable result should aim for the
unanimous case.

### 3.5 The limit surface

The limit surface is how the theory gets from "the object is sliding" to "here is
the motion it makes". It needs one new idea first.

While the object slides, every small patch of its base contributes a friction
force. Add all of them up and you get one force in the plane and one moment about
the vertical, and a force together with a moment is called a **wrench**. So the
table's whole effect on the sliding object is a single wrench with three numbers
in it: a force along `x`, a force along `y`, and a moment about `z`.

Now collect the wrench for every possible way the object could be sliding — every
combination of translating and spinning. Plot each of those wrenches as a point in
the three-dimensional space whose axes are those three numbers. The points form a
closed surface around the origin, and **that surface is the limit surface**.

Two properties make it useful.

**Inside means stuck, on means sliding.** If the wrench applied to the object lies
strictly inside the limit surface, the base friction can balance it and the object
does not move. If the object is sliding, its friction wrench lies exactly on the
surface. So the limit surface is the boundary between an object that stays put and
one that moves.

**The motion is perpendicular to the surface.** At the point where the wrench
sits, the object's motion — its velocity and its spin, taken together, which is
called a **twist** — points along the outward normal to the limit surface. This
follows from the principle of maximum dissipation, and the MIT study tested it
directly against measured data: it holds well for ABS, Delrin and plywood, and
fails in two regions for polyurethane, corresponding to abrupt transitions in that
material's limit curve.

Nobody computes the exact limit surface. It is approximated by an ellipsoid, and
the approximation has two parameters that can be worked out.

The first is the largest force the base friction can produce, which is the pure
translation case: `f_max = mu * m * g`.

The second is the largest moment it can produce, which is the pure rotation case,
and for a uniform circular support of radius `R` it can be integrated directly.
The pressure is `m * g / (pi * R^2)`. The friction force on an annulus at radius
`r` of width `dr` is `mu * pressure * 2 * pi * r * dr`, and its moment arm is `r`.
Integrating `mu * (m*g/(pi*R^2)) * 2 * pi * r^2 dr` from 0 to `R` gives

    m_max = (2/3) * mu * m * g * R

The ellipsoid is then

    (fx / f_max)^2 + (fy / f_max)^2 + (mz / m_max)^2  =  1

and the single number that characterises it is the ratio
`m_max / f_max = (2/3) * R`.

That ratio has a physical meaning worth holding on to: it is the moment arm at
which a force is exactly as good at rotating the object as at translating it. For
a 1 kg object on a 50 mm support radius with `mu = 0.25`, the numbers are
`f_max = 0.25 * 1 * 9.81 = 2.45 N`,
`m_max = (2/3) * 0.25 * 1 * 9.81 * 0.05 = 0.0818 N m`, and the ratio is
`0.0818 / 2.45 = 0.0333 m`, which is `(2/3) * 50 mm = 33.3 mm` as expected.

So for that object, pushing more than about 33 mm away from the centre of friction
produces more rotation than translation, and pushing closer than that produces
more translation than rotation. That is a number you can act on.

### 3.6 The motion cone

The friction cone in 3.2 is a set of forces. The motion cone is the corresponding
set of motions, and it is what tells you whether the pusher will stay put on the
object's face.

Fix a contact point. Sweep the contact force over every direction inside the
friction cone there. Each force is a wrench, each wrench sits somewhere on the
limit surface, and each point on the limit surface gives a twist. The set of
twists you get from sweeping the whole friction cone is the **motion cone** at
that contact.

The rule it gives you is this. If the twist you are commanding — that is, the
motion of the pusher itself — lies inside the motion cone, the contact **sticks**,
and the object moves exactly as the pusher does. If it lies outside, the contact
**slides**, the object moves along the nearest edge of the motion cone instead,
and the pusher skates across the object's face while it does.

Sticking is what you want, because it is the only case in which the object goes
where you told it. Three things widen the motion cone and therefore make sticking
more likely: a higher-friction pusher tip, a push direction closer to the face
normal, and a contact closer to the centre of friction. All three are free.

### 3.7 The pressure distribution nobody measures

Everything in 3.3 to 3.6 depends on where the object's weight sits on its base.
The centre of friction is defined by it. The limit surface is computed from it.
The 33.3 mm number in 3.5 assumed a uniform circular support, and real objects do
not have one.

**No robot measures it.** There is no sensor on a normal cell that reports the
pressure distribution under an object on a table. You can infer it if you know the
object's geometry and assume it is homogeneous and its base is perfectly flat, and
those three assumptions fail routinely. A box with its contents to one side, a
tray with three feet touching and a fourth not quite, a moulded part with a
slightly convex bottom — each of these moves the centre of friction somewhere you
did not predict, and the predicted rotation goes with it.

Even the coefficient underneath it all is not the constant the model wants. The
MIT study measured this directly and the numbers are worth quoting, because they
are what separates a model that looks right from one that is right.

Read the table below as four separate ways in which a single coefficient of
friction fails to be a single number, each measured on the same apparatus.

| How it varies | What was measured | Size of the effect |
| --- | --- | --- |
| across the table | standard deviation of the coefficient over a 20 cm by 40 cm plate | 0.016 on Delrin, 0.017 on ABS, 0.024 on plywood, 0.064 on polyurethane |
| over time, from wear | change over 100 successive scans | Delrin fell from 0.16 to 0.12, which the paper puts at a 22.2 per cent drop |
| with sliding speed | coefficient at low speed against high speed | polyurethane rose from about 0.29 to about 1.0 |
| with sliding direction | ratio of largest to smallest friction over all directions | about 3 to 2 on polyurethane; ABS, Delrin and plywood close to isotropic |

The spatial figure is the one that is easiest to underestimate. A standard
deviation of 0.064 against a mean of 0.29 is 22 per cent of the value, varying
from place to place on one sheet of one material. The paper's own conclusion is
blunt: the coefficient of friction "is not necessarily constant, and the ratio
changes in space, with orientation, with velocity, and with time."

Two things follow, and both are practical.

**Do not plan a long push open-loop.** The error in the object's predicted pose
grows with the push distance, because the model's error is in the rate of rotation
rather than in the final position. A 200 mm push planned from a model will not end
where the model said.

**Push in short segments and look again between them.** This is the same shape as
the feedback argument in
[holding on](05_holding-on.md#5-feedback-and-what-to-do-with-it): the model gives
you the direction to correct in, and the sensor tells you how much correction is
needed. The model is not wasted — it is what makes the correction converge instead
of oscillating — but it is not sufficient on its own.

It is worth saying where this meets simulation.
[Section 5 of making it work](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you)
says that contact with curved, slippery or brittle surfaces is the weakest part of
any physics engine, and that friction and softness numbers there are plausible
rather than measured. Pushing is the manipulation primitive that depends on those
numbers most directly. A push that works perfectly in a simulator tells you your
control logic is right. It tells you nothing about whether the object will end up
in the same place on a real table, because the simulator invented the pressure
distribution and the friction map that the real table has and you do not know.

### 3.8 As pseudo code

```
function push_to_pose(object, target_pose):
    while distance(observe(object).pose, target_pose) > tolerance:
        current = observe(object).pose          # a fresh perception cycle

        # Decide what correction is wanted: mostly translation, or a turn.
        error = target_pose - current
        cof   = estimated_centre_of_friction(object)

        if error.rotation is small:
            # Push through the centre of friction: no moment, so no rotation.
            contact = point_on_face_aligned_with(cof, direction = error.translation)
        else:
            # Offset the contact to one side of the centre of friction.
            # 3.5 gives the arm at which rotation and translation are equal;
            # beyond it, rotation dominates.
            offset  = sign(error.rotation) * (2.0 / 3.0) * support_radius(object)
            contact = point_on_face_offset_from(cof, offset)

        # Keep the pusher inside the contact friction cone (3.2) so it sticks.
        direction = clamp_to_cone(error.translation,
                                  normal    = face_normal_at(contact),
                                  half_angle = atan(mu_pusher_object))

        # Keep the contact below the tipping height (2.2).
        if contact.height > safe_push_height(object, surface, 1.5):
            decline("cannot reach a safe contact on this face")

        # Short segment, then look again. 3.7 is why.
        move_pusher(contact, direction, distance = 20 mm, speed = 20 mm/s)
```

Two details in that sketch are the whole point. The push distance is 20 mm rather
than the full error, because section 3.7 says the model's accuracy degrades with
distance. And the speed is 20 mm/s, which is the speed the MIT dataset used, and
which keeps the acceleration comfortably inside the quasi-static condition from
3.1.

### 3.9 What the quasi-static model suits and does not

Five jobs the quasi-static pushing model suits:

- choosing where on an object's face to touch it in order to turn it a particular
  way, which is the question nothing else answers
- deciding a push direction that will stick rather than skate, from the contact
  friction cone
- knowing when a push is hopeless before attempting it, because the required
  rotation is larger than the pusher can produce from any reachable contact
- providing the correction direction in a feedback loop, where the magnitude comes
  from the camera rather than the model
- explaining a failure, since a push that rotated the wrong way usually means the
  centre of friction was not where you assumed

Five jobs it cannot do:

- predict a final pose accurately over a long push, which is section 3.7
- work above roughly a tenth of `mu * g` in acceleration, where inertia takes over
- handle an object whose pressure distribution is unknown, which is all of them
- describe a push against a non-flat contact, a rolling object or an object on
  another object
- be calibrated from any sensor a normal robot cell has, since the quantity it
  needs is the pressure distribution under the base

## 4. Pulling, dragging and deliberate toppling

Pushing is the primitive with the theory. The other three non-prehensile moves
have less theory and are no less useful, and toppling in particular is the one
that is most often the right answer and least often considered.

### 4.1 Pulling and dragging

Pulling means moving an object towards the robot. The difficulty is that a bare
pusher cannot pull: pushing needs only contact, and pulling needs the object to be
attached to the tool somehow. Four attachments are available, in increasing order
of cost.

A **hook** catches on a lip, a handle, a hole or an edge. The cheapest hook on a
robot arm is one finger of a two-finger gripper, closed and extended past the
other. It needs a feature to catch on, and most objects do not have one.

A **high-friction pad pressed downward** drags by friction alone. The tool presses
onto the top of the object with force `F_down` and moves sideways; the object
comes with it as long as the friction at the pad, `mu_pad * F_down`, exceeds the
friction at the base, `mu_base * m * g`. This works and it has a real limit: it
needs `mu_pad * F_down > mu_base * m * g`, and the downward force is bounded by
what the object can take without crushing.

**Suction** pulls anything it can seal against, which is
[the same condition as gripping by suction](01_overview.md#2-the-six-ways-to-hold-something),
and it does not care about the direction afterwards.

**A shaped tool** — a scraper, a squeegee, a rake — pulls a whole region rather
than one object and is what most sweeping is actually done with.

The slide-or-tip condition applies to pulling with one change: **the pivot edge is
the trailing edge, the one nearest the robot.** So `d` is now the distance from
the centre of mass to the near edge, and the object tips *towards* the robot. The
formula and the derivation are otherwise identical. The asymmetry this produces is
useful: an object whose mass sits towards its far side is harder to topple by
pulling than by pushing, and vice versa, so when only one of the two is safe it is
worth working out which.

Dragging has one advantage over pushing that has nothing to do with physics. It
brings the object **into** the workspace rather than out of it. An object at the
back of a shelf, or at the far side of a bin, may be reachable for a touch and not
for a grasp; dragging it 100 mm closer converts it into an ordinary pick.

Five jobs pulling and dragging suit:

- retrieving an object from the far edge of a workspace, where a grasp is out of
  reach but a touch is not
- moving an object away from a wall it is flush against, when pushing would drive
  it further into the wall
- dragging a flat object to a table edge so that a finger can get under it
- moving several objects at once with a shaped tool, which pushing also does
- any move where the destination is nearer the robot than the origin, which is
  most of them in a shelf or a deep bin

Five jobs they cannot do:

- work on an object with no lip, hole, handle or sealable face, unless a
  high-friction pad can press on it
- work on anything the downward press would crush, since the press is what makes
  friction dragging work
- be done with a bare pusher or a flat fingertip, which is the common disappointment
- be planned with the models in section 3, which are written for a pushing contact
  and assume the contact can only push
- avoid tipping an object backwards onto the robot, which is a real failure mode
  and the reason the trailing-edge version of section 2 matters

### 4.2 Toppling on purpose

Knocking an object over sounds like a failure. It is frequently the correct move,
and it is the clearest example in this document of a non-prehensile action that
creates a grasp rather than replacing one.

Four situations call for it.

**The face you need is not the face that is up.** A suction cup needs one flat,
smooth, sealable patch. An object whose only such patch is a vertical side offers
nothing to a suction gripper standing over it. Tip it over and the patch faces
upward. This is exactly what the Berkeley toppling work was built for; its
repository is titled "Robust Toppling for Vacuum Suction Grasping".

**The object is too tall to grasp stably standing and fine lying down.** A tall
bottle gripped near its top has its centre of mass far below the grasp, which is
[the torque problem in choosing a grip](03_choosing-a-grip.md#5-the-centre-of-mass-and-the-torque-nobody-budgets-for).
The same bottle lying down can be gripped across its body at its middle.

**The object is standing in the way.** An upright item in a bin hides its
neighbours from the camera and blocks the gripper from reaching them. Knocking it
flat clears both.

**The grasp you want is underneath.** Some objects have exactly one good grasp
region and it is on the bottom face. Toppling is the only way to expose it without
a grasp you do not have.

The arithmetic of toppling is different from section 2's, because section 2 asks
whether an object *begins* to tip and toppling asks whether it goes all the way
over. An object pivoting about an edge lifts its centre of mass until the centre
of mass is directly above the pivot, and falls the rest of the way on its own. So
there are two numbers: the angle you must tilt it through, and the energy you must
put in.

For a box of base width `w` and height `H` with its centre of mass in the middle,
the centre of mass sits at a distance `r = sqrt((w/2)^2 + (H/2)^2)` from the pivot
edge, and it starts at height `H/2`. The tipping angle and the lift are

    tilt angle  =  arctan(w / H)
    lift        =  r - H/2
    energy      =  m * g * (r - H/2)

Read the table below as the effort required to knock each shape over, for a 1 kg
object. The last column is the energy in joules, which is small in every case and
still tells you which shapes are easy.

| Object | Base `w` | Height `H` | `r` | Tilt needed | Centre of mass lift | Energy for 1 kg |
| --- | --- | --- | --- | --- | --- | --- |
| bottle | 70 mm | 250 mm | 129.8 mm | 15.6 degrees | 4.8 mm | 0.047 J |
| tall box | 150 mm | 300 mm | 167.7 mm | 26.6 degrees | 17.7 mm | 0.174 J |
| cube | 150 mm | 150 mm | 106.1 mm | 45.0 degrees | 31.1 mm | 0.305 J |
| flat plate | 200 mm | 5 mm | 100.0 mm | 88.6 degrees | 97.5 mm | 0.957 J |

The arithmetic for the tall box, so the rest can be checked:
`r = sqrt(0.075^2 + 0.150^2) = sqrt(0.028125) = 0.16771 m`, the lift is
`0.16771 - 0.150 = 0.01771 m`, and the energy is `1 * 9.81 * 0.01771 = 0.174 J`.

The ordering in that table is the useful result, and it runs against the
intuition. **The taller and narrower the object, the easier it is to topple** —
less tilt and less energy both. The flat plate is the hardest thing on the list to
knock over, needing an 88.6-degree rotation and twenty times the energy of the
bottle, which is another way of saying what section 2 already said: a flat object
cannot be toppled by a push, only slid.

Toppling has one problem that it does not share with pushing, and it is the reason
it is used less than it should be. **You do not know which way up it lands.** An
object released mid-tumble settles into whichever of its stable poses it happened
to be nearest, and predicting that requires the centre of mass and the friction,
which is the same obstacle
[regrasping runs into](05_holding-on.md#6-regrasping). The practical answer is
also the same: look again afterwards rather than predicting. Toppling followed by
a fresh perception cycle is reliable. Toppling followed by an assumption is not.

Five jobs deliberate toppling suits:

- exposing a flat face so that a suction cup has something to seal against
- laying a tall object down so that it can be gripped near its centre of mass
- clearing an upright object that is occluding its neighbours from the camera
- exposing a grasp region that is currently on the bottom face
- any object tall and narrow enough that the tilt needed is small, which the table
  above quantifies

Five jobs it cannot do:

- work on flat or wide objects, where the required tilt approaches 90 degrees
- tell you which stable pose the object lands in, which needs a fresh look
- be undone, since an object on its side cannot be stood up again by pushing
- be used on anything fragile, since the object falls the last part of the way
  under gravity and lands with whatever energy that gives it
- be done safely near neighbours, because a toppling object sweeps a region much
  wider than its base and knocks other things over

### 4.3 Sweeping and singulation

Sweeping is pushing several objects at once with a broad tool, and its usual
purpose is **singulation**: separating a pile into items that can be seen and
grasped individually. It is the one non-prehensile action with a clean place in a
standard pipeline, because its success criterion is not a pose but a much weaker
question — did the perception system, after the sweep, find at least one object it
can now grasp. That is a question the existing pipeline already answers.

The pattern is worth stating as a loop, because it is short and it works:

```
while no graspable object found:
    pile   = observe()
    if sweep_attempts > limit: decline("cannot singulate this pile")
    sweep across the densest region of the pile
    sweep_attempts = sweep_attempts + 1
grasp the object that perception found
```

The reason this is more robust than it looks is that it does not need the sweep to
be predictable. It needs the sweep to change the scene, and then it re-asks a
question it already knows how to answer. A push planner that had to predict where
each item ended up would be defeated by section 3.7. This one is not.

## 5. The tools, the libraries and how thin they are

Everywhere else in this area, the honest answer about open-source support is that
there is too much of it to choose from. Here the honest answer is the opposite,
and it is worth putting a number on before listing anything.

### 5.1 How thin, with numbers

The grasping repositories that this area's other documents discuss have, at the
time of writing in September 2026, these star counts on GitHub: GraspNet baseline
1030, AnyGrasp 1008, GPD 767, Contact-GraspNet 533, Dex-Net 364.

A GitHub repository search for "nonprehensile manipulation" returns nine
repositories. The most starred has 51. A search for "planar pushing robot" returns
four, the most starred of which has 14.

There is one prominent exception, and its state is instructive.
[Visual Pushing for Grasping](https://github.com/andyzeng/visual-pushing-grasping)
has 1111 stars, which puts it above every grasping repository in the list above.
Its LICENSE file is BSD 2-Clause. Its last commit was in May 2021, its README
documents Ubuntu 16.04, Python 2.7 or 3, and PyTorch 0.3, and the simulator it
targets is V-REP, which has since been renamed and rewritten. It is an excellent
paper with a well-cited implementation and it is five years unmaintained.

The research code from the group that produced most of the pushing literature is
in worse shape still. The MIT MCube lab's public repositories include
[pdproc](https://github.com/mcubelab/pdproc), the processing scripts for the push
dataset, and [cpush](https://github.com/mcubelab/cpush) and
[fompush](https://github.com/mcubelab/fompush), which are pushing controllers.
None of the three has a LICENSE file. That is not an oversight you can work
around: with no licence, default copyright applies and you have no permission to
use, copy or modify the code at all, which is
[the first trap in this area's licence document](07_licences-and-platforms.md#11-no-licence-at-all).
The same is true of
[BerkeleyAutomation/toppling](https://github.com/BerkeleyAutomation/toppling),
which has one star, no LICENSE file, and a README that specifies Python 2.7.

**There is no ROS 2 package for any of this.** There is no push primitive, no
slide-or-tip check, no limit surface implementation and no motion cone in the ROS
ecosystem. What ROS 2 gives you is
[MoveIt 2](https://github.com/moveit/moveit2), whose LICENSE file is BSD
3-Clause, and a Cartesian path is what you build a push out of. Everything in
sections 2, 3 and 4 of this document is arithmetic you write yourself, and the
good news in that is that all of it fits in a few hundred lines.

### 5.2 The libraries that do exist

Every licence below was read from the repository's own LICENSE file rather than
from the badge. Read the table as: what it is, what its licence file actually
says, and how alive it is.

| Project | What it is | Licence, from its LICENSE file | State |
| --- | --- | --- | --- |
| [planning-through-contact](https://github.com/bernhardpg/planning-through-contact) | a planar pushing planner built on Drake, solving the contact mode sequence | MIT | active |
| [quasistatic_simulator](https://github.com/pangtao22/quasistatic_simulator) | a quasi-static contact simulator, which is the regime section 3 describes | MIT | research code |
| [force_push](https://github.com/learnsyslab/force_push) | single-contact quasi-static pushing with force feedback, from a 2024 paper | MIT | 14 stars, last touched 2025 |
| [ActivePusher](https://github.com/elpis-lab/ActivePusher) | active learning of a residual pushing model on top of an analytic one | MIT | 18 stars, 2026 |
| [CORN](https://github.com/iMSquared/corn) | a learned contact representation for non-prehensile manipulation, from a 2024 paper | MIT | 51 stars |
| [visual-pushing-grasping](https://github.com/andyzeng/visual-pushing-grasping) | learns when to push and when to grasp, jointly | BSD 2-Clause | unmaintained since 2021 |
| [ravens](https://github.com/google-research/ravens) | simulated manipulation benchmark including a [sweeping task](https://github.com/google-research/ravens/blob/master/ravens/tasks/sweeping_piles.py) | Apache 2.0 | archived research code |
| [pdproc](https://github.com/mcubelab/pdproc) | processing for the MIT push dataset | **no LICENSE file** | last touched 2019 |
| [toppling](https://github.com/BerkeleyAutomation/toppling) | toppling policies for suction grasping | **no LICENSE file** | Python 2.7 |

The dataset itself is the most valuable artefact in that list, and it is separate
from the code. The
[MIT push dataset](https://mcube.mit.edu/push-dataset/) records over a million
timestamped samples of a circular pusher and a pushed object, with the interaction
force at the contact, varying six things: surface material, object shape, contact
position, push direction, push speed and push acceleration. Every measured number
in sections 2 and 3 of this document came from it or from
[its paper](https://arxiv.org/abs/1604.04038). It is the reason you can put a real
range on a friction coefficient rather than a guess.

### 5.3 The simulators

None of the pushing-specific packages is a simulator. If you want to try a push
before building one, you use a general physics engine, and four are relevant.
Their licence files say something slightly different from their GitHub badges in
three of the four cases, which is why the middle column is worth reading.

| Simulator | What its LICENSE file says | Runs on an Apple Silicon Mac with no NVIDIA graphics card |
| --- | --- | --- |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | Apache 2.0 | yes: release 3.14.0 ships a macOS universal2 build |
| [Drake](https://github.com/RobotLocomotion/drake) | [BSD 3-Clause for all components](https://github.com/RobotLocomotion/drake/blob/master/LICENSE.TXT), with some portions under other permissive non-viral licences; GitHub reports this as "Other" | yes: release 1.57.0 ships `drake-1.57.0-cp313-cp313-macosx_15_0_arm64.whl` |
| [Bullet and PyBullet](https://github.com/bulletphysics/bullet3) | [zlib, except `Extras` and `examples/ThirdPartyLibs`](https://github.com/bulletphysics/bullet3/blob/master/LICENSE.txt); GitHub reports this as "Other" because of the carve-out | **with difficulty**: PyPI publishes only `manylinux` x86_64 wheels for PyBullet 3.2.7, and the newest Python it builds a wheel for is 3.10, so on an Apple Silicon Mac you compile from the source tarball |
| [Isaac Lab](https://github.com/isaac-sim/IsaacLab) | BSD 3-Clause | no: it requires Isaac Sim and an NVIDIA GPU |

Two of those entries are worth a sentence each.

Drake is the outlier in a useful direction. It has a real quasi-static contact
solver, it is the platform the best-licensed pushing planner in section 5.2 is
built on, and it publishes an Apple Silicon wheel for current Python. If you want
to experiment with the physics in section 3 on a Mac, that is the shortest path.

PyBullet is the one most tutorials assume and the one most awkward on this
hardware. It works once compiled, and compiling it is a step that every tutorial
you read will have skipped.

### 5.4 What to actually do

The state of the software leads to a fairly short recommendation.

**Write sections 2 and 4 yourself.** The slide-or-tip condition, the safe push
height, the toppling angle and the toppling energy are four formulas and perhaps
fifty lines. There is no library to find and nothing to licence, and they cover
the decisions that matter most.

**Write section 3's feedback loop yourself too, and keep the model small.** The
useful parts of the quasi-static theory are: push through the centre of friction
to translate, offset by about two-thirds of the support radius to rotate, stay
inside the contact friction cone, and push 20 mm at a time. That is a page of
code, and section 3.7 is the reason a larger model would not pay for itself.

**Reach for a library only for simulation.** MuJoCo and Drake both run natively on
Apple Silicon and both will let you watch a pushed object rotate the wrong way,
which is instructive. Neither will tell you what the real object does, for the
reasons in
[section 5 of making it work](../06_object-perception/07_making-it-work.md#5-what-simulation-will-not-tell-you).

**Check every licence before you copy anything.** This area has more unlicensed
research code than any other in the repository, and the checks in
[checking an implementation](08_checking-an-implementation.md) apply here
unchanged.
