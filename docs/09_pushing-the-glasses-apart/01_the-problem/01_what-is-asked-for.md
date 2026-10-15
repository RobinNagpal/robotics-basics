# Push the glasses apart — what is asked for

## 1. Introduction

The camera work is finished. [Telling the glasses apart in a
picture](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md)
tells the arm where each glass stands. But some glasses stand too close together.
The gripper cannot get round one of them without hitting its neighbour.

So the arm has to **move them apart by dragging them across the table**. It does
not lift them. Dragging is the whole point of this problem.

This page states the question that all seven answers in this book get. The same
question lets us compare seven very different methods. The page is for anyone
who wants to read those answers. It covers these things:

- why the arm drags instead of lifting;
- what each answer gets and what it gives back;
- how much room the gripper needs, and how to measure it;
- why the hand is turned on its side, and what that costs;
- what counts as done, as correct but incomplete, and as wrong.

## Contents

1. [Introduction](#1-introduction)
2. [A film of the job](#2-a-film-of-the-job)
3. [Why dragging and not lifting](#3-why-dragging-and-not-lifting)
4. [What is on the table](#4-what-is-on-the-table)
5. [What goes in and what comes out](#5-what-goes-in-and-what-comes-out)
6. [The gap that matters is not the gap between the glasses](#6-the-gap-that-matters-is-not-the-gap-between-the-glasses)
7. [How low the push has to be, and why it is a property of the glass](#7-how-low-the-push-has-to-be-and-why-it-is-a-property-of-the-glass)
8. [What else makes this hard](#8-what-else-makes-this-hard)
9. [What is deliberately not in this problem](#9-what-is-deliberately-not-in-this-problem)
10. [What "done" means](#10-what-done-means)
11. [Where to go next](#11-where-to-go-next)

## 2. A film of the job

Words are easier to follow after you have seen the job once. This film shows
one of the solutions clearing one crowded table in the simulator. It plays
at one and a half times real speed.

[The job done once: a learned world model clears one table, 44 seconds and no sound](https://docs.dodao.io/videos/pushing-the-glasses-apart/04-a-world-model.mp4 "video")

Watch for three things, because the rest of this page is about them.

- Every glass is **dragged across the table**. No glass is lifted.
- The arm **pushes, looks again, and pushes again**. It looks again because a
  push does not end exactly where it was aimed.
- A glass is carried away only once it has room around it. The table is
  finished when every glass has been taken. This is [what this page means by
  done](#10-what-done-means).

Two things in the film are easy to misread. Both are about the hand.

First, **the hand never opens while it pushes.** The gripper stays shut for the
whole problem. The closed hand is the pusher. Nothing is gripped during a push.

Second, **the pick-up at the end is drawn, not simulated.** The examiner removes
a glass from the table in one instant. So the film draws a pick-up instead. The
wrist rolls back level, the fingers open, the hand reaches in, the fingers
close, and the glass is carried off. A line on the screen says "problem 1 does
the real pick". Problem 1 is the job of picking up one glass. This library has
no book about that job yet. The drawing does not show that this cell can lift a
glass.

A drawn hand cannot hit anything. So the film first checks which side is clear,
and it comes in from that side. [What the examiner
measures](03_the-examiner.md#5-what-the-examiner-measures) explains this check.
It also explains that the cell's grip rule finds a hold on only 97 of the 251
glasses.

The hand is drawn twice. The solid pieces are its real parts: two fingertips,
two fingers and the gripper's body. A faint shell around them is the shape the
simulator uses for collisions. The shell fills the 82 mm gap between the two
fingers, because a glass in that gap would be pushed along too. So every
solution has to plan its pushes around the shell.

Six of the solutions have been filmed. This is the only film in which the
table is finished. So it shows success, not an average attempt. [The
results](../11_the-results.md) shows all six films.

The film shows the arm dragging. The next section says why it cannot lift.

## 3. Why dragging and not lifting

Lifting is not possible yet, and the reason goes round in a circle.

- To lift a glass, the fingers must close on it in a chosen place.
- To choose that place, the arm needs the glass's side shape, its profile.
- To measure the profile, the arm needs a photograph from the side, taken from
  300 mm away.
- To take that photograph, the arm needs a clear view. The crowding has taken
  that view away.

![Four needs in a ring, each one waiting on the next: lifting needs a chosen grip place, which needs the glass's profile, which needs a side-on photograph, which needs a viewpoint the crowding has taken away.](../../images/pushing-the-glasses-apart/what-is-asked-for/asked-the-circle-lifting-cannot-break.png)

Dragging breaks the circle because it needs very little. A push needs a contact
point and a direction. It does not need the glass's height, shape or weight. It
needs only where the glass stands and how wide its foot is. The camera work
already [hands over both of
these](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md#4-what-must-come-out).

Dragging needs to know what is on the table, so the next section says that.

## 4. What is on the table

The glasses are the same as in [the camera
work](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md#2-what-is-on-the-table).
There are four to six of them. They are all one known kind, upright and opaque.
The difference is that some of them stand close together.

The next section says what an answer gets about these glasses.

## 5. What goes in and what comes out

This section gives a short summary. [What goes in and what comes
out](02_what-goes-in-and-what-comes-out.md) gives the full detail.

**What goes in** is one reading for each standing glass. It says where the
glass stands, how tall it is, and how wide it is. Answers that read pictures
also get a picture of the table from above. After each push, the answer also
gets the force that the hand felt. Nothing else goes in.

**What comes out** is a path for the hand, then another path, until the table
is done or the pushes run out. An answer may also refuse a glass that it cannot
move safely. It must give the reason.

The same input and output go to every answer. This is what makes the
answers comparable. [The examiner](03_the-examiner.md) makes sure of it.

The input includes each glass's width. The next section explains why that width
matters for the gripper.

## 6. The gap that matters is not the gap between the glasses

![The open jaw needs about 76 mm from a glass's middle outwards before it fits round it, so the gap that decides whether a glass can be gripped is the one between a middle and a neighbour's edge rather than the one between two glasses.](../../images/pushing-the-glasses-apart/what-is-asked-for/the-room-a-gripper-needs.png)

Two glasses with a centimetre of space between them are not touching. A person
would call them separate. But the gripper cannot pick up either one. This is
because the gripper is not a point.

The gripper on this arm is a **Robotiq 2F-85**. It is a real product. The cell
uses the shape its maker publishes. So where a number below is awkward, the
real cell would have the same problem.

To close on a glass, the open hand must go **around** it, with one finger on
each side. How much room does that need? It is **not half the opening**. That
is an easy mistake. It is how far the widest part of the open hand reaches from
its middle. On a 2F-85 the fingers stand further out than the pads. Measured
this way, the hand needs **76 mm of clear room in every direction**.

That room is measured to the **neighbour's edge**, not to its middle. This
means the test is **not symmetric**. Here is an example. A narrow glass stands
beside a wide glass. The wide glass's rim reaches further into the gap. So the
narrow glass runs out of room first. A method that only compares distances
between middles will get this wrong.

So there are three different distances, and they are easy to mix up. Each row
of the table below is one of them. The middle column says what it means, and
the last column gives its rough size.

| | What it is | Roughly |
| --- | --- | --- |
| glasses touching | the failure the [camera work never faces](../../08_seeing-the-glasses/02_the-problem/01_what-is-asked-for.md#2-what-is-on-the-table) | the two rims meet |
| glasses grippable | the hand fits round one of them | 76 mm clear of the neighbour's **edge** |
| glasses measurable | a clear line of sight from 300 mm back | depends on the angle |

This book's job is to make every glass grippable. The third distance belongs to
[looking again at what was
hidden](../../08_seeing-the-glasses/02_the-problem/02_looking-again-at-what-was-hidden.md).
Moving a glass changes it too.

The hand needs room around a glass. The next section shows that the hand's
shape also limits how low it can push.

## 7. How low the push has to be, and why it is a property of the glass

![A push above a certain height on the glass tips it instead of sliding it, and how low that height is follows from the width of the foot the glass stands on and from a friction nothing in the cell can measure.](../../images/pushing-the-glasses-apart/what-is-asked-for/push-low-or-it-topples.png)

A pushed glass either slides or tips over. Where you push it decides which. A
push near the foot slides it. A push near the rim tips it.

The height where sliding turns into tipping depends on two things. One is how
wide the glass's foot is. The other is the friction between the glass and the
table. A wide foot gives more room. High friction gives less.
[Pushing without toppling](05_pushing-without-toppling.md#3-the-limit-slide-or-tip)
works out this limit in full. It also explains which height on the hand to use.
That height is the top edge of the jaw, at 107 mm, not the 75 mm the arm aims at.

The hand's shape decides how low it can push. Held the normal way, with its
fingers side by side, the 2F-85 is 139 mm across. The closest glasses stand
150 mm apart, so the hand has almost no space. So the cell turns the hand a
quarter turn onto its side. On its side it is only 27 mm across, and it fits
between the glasses.

**Turning the hand costs height.** On its side the hand reaches 69 mm below its
own middle. So its middle cannot go lower than 75 mm, or the fingers hit the
table. A higher push is closer to the tipping limit.

Turning the hand has a second cost, which you can see in [the
film](#2-a-film-of-the-job). To grip a glass, the fingers must open across it,
one on each side. They cannot do that while the hand lies on its side. So the
wrist must roll back level before each pick-up. Pushing and gripping are two
different poses of the same hand. This is why each drawn pick-up starts by
rolling the wrist.

Three things follow from this.

- **The push height must be worked out for each glass**, from its measured foot
  width. It is not one setting chosen for all glasses.
- **Some glasses cannot be pushed.** A tall glass on a narrow foot tips before
  it slides. The answer must refuse that glass and not try.
- **The friction is not known.** Nothing in the cell measures it. [What a
  solution is never
  told](02_what-goes-in-and-what-comes-out.md#4-what-a-solution-is-never-told)
  explains why this makes the problem hard.

The tipping limit is one hard part. The next section lists the others.

## 8. What else makes this hard

These are the other reasons the job is hard.

**Choosing where to push a glass to.** The new place must be clear of other
glasses and clear of the rack. It must be inside the arm's reach and inside the
part of the table the glasses may use. A glass pushed out of one crowd can end
up in another crowd.

**A push does not go exactly where you aim it.** The friction under a glass is
not the same everywhere. The contact is not a single point. The glass turns as
well as slides. Predicting the result exactly needs numbers that nobody here
has. So the arm must look again after each push.

![A finger that meets a round glass anywhere but on the line through its middle turns the glass as well as moving it, so only a push aimed through the middle slides it roughly straight.](../../images/pushing-the-glasses-apart/what-is-asked-for/an-off-centre-push-spins.png)

**Choosing which glass to move.** Moving the wrong glass of a pair can make
things worse. It can push that glass into a third glass, or out of reach. So
the choice needs the whole table, not just the crowded pair.

**Pushing means touching, and touching can break things.** The arm does not
know how heavy a glass is. A push that is too fast becomes a knock. A knock on a
tall glass can tip it over.

Those are the hard parts that are in the problem. The next section lists what
is left out on purpose.

## 9. What is deliberately not in this problem

Some things are left out on purpose, to keep the problem small.

- **Lifting.** There is no grasp, no weighing and no rack in this problem.
- **Measuring a profile.** This book works only from a foot width and a position.
- **Deciding the kind of glass.** All glasses on a table are one known kind.
- **Tidying.** The glasses do not have to end up in any set place. They only
  have to end up far enough apart.

With the scope clear, the next section says how a run ends.

## 10. What "done" means

A run can end in three ways.

A run is **done** when three things are true. Every glass has at least 76 mm of
clear room around it. Every glass has at least one clear view for a side
photograph. And no glass has been knocked over.

A run is **correct but incomplete** when a glass could not be moved safely, and
the answer reports it with the reason. The usual reasons are that the glass
tips before it slides, or that there is no clear place to push it to. This
still counts as a correct answer.

A run is **wrong** if a glass is tipped over, pushed out of reach, pushed off
the table, or pushed into the rack. Tipping over is the failure to watch most.
Nothing else in this project can recover a glass that has fallen over.

![The three endings side by side: done, correct but incomplete where a glass was refused with its reason, and wrong where a glass was toppled or pushed somewhere it cannot be recovered from.](../../images/pushing-the-glasses-apart/what-is-asked-for/asked-three-ways-a-run-ends.png)

Four numbers are worth watching. They are how many glasses ended up grippable
and how many pushes it took. They are also how far each glass ended from its
aim, and how many glasses were refused.

That is the whole question. The next section says where to read on.

## 11. Where to go next

Five pages describe what every answer shares. Read them before any of the seven
answers.

- [What goes in and what comes out](02_what-goes-in-and-what-comes-out.md) —
  the three calls, what a push reports, how its force is measured, and what an
  answer gives back.
- [The examiner](03_the-examiner.md) — the crowded tables, the physics, and how
  a run is marked.
- [The target layout](04_the-target-layout.md) — where the glasses should end
  up, and the least movement the task needs.
- [Pushing without toppling](05_pushing-without-toppling.md) — the height limit
  that decides whether a glass slides or tips, and the loop of plan, feel and
  look again.
- [Questions and answers](06_questions-and-answers.md) — short answers to the
  common questions about this problem, each with a link to the full
  explanation.

Then read the seven answers themselves:

→ [The seven solutions](../03_the-seven-solutions/01_how-the-six-compare.md)

[What goes in and what comes out](02_what-goes-in-and-what-comes-out.md) →
