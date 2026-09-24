# Ordering and rearrangement: which object to move first

Most of this area asks how to move the arm to one place. This document asks a
different question, and it comes up whenever there is more than one object on the
table. **In what order should the objects be dealt with?**

The question sounds like housekeeping and it is not. Removing an object changes
what the arm can reach, what the camera can see, and what is holding everything
else up. A task that is impossible in one order is straightforward in another,
and no improvement to perception or to motion planning repairs a bad order. The
order is a property of the scene rather than a preference, and it can be computed
before the arm moves.

This document is for someone who has a working pick-and-place and is now pointing
it at a crate, a tray or a cluttered table and finding that it gets three objects
out and then stops. It follows on from
[reaching and reachability](02_reaching-and-reachability.md), which answers
whether the arm can get to one pose, and from
[planning a path](03_planning-a-path.md), whose
[section 9](03_planning-a-path.md#9-planning-the-whole-task-as-one-thing) makes
the closely related argument that the steps of a single pick-and-place have to be
checked together rather than one at a time. That section is about one object and
several steps. This document is about several objects and one step each. The two
failures have the same shape and different cures, so the earlier section is
assumed here rather than repeated.

Every term is explained where it first appears. You do not need to know what a
graph or a topological sort is.

## Contents

1. [Why the order is a property of the scene](#1-why-the-order-is-a-property-of-the-scene)
2. [The blocking graph](#2-the-blocking-graph)
3. [The cheap heuristics, and where they stop](#3-the-cheap-heuristics-and-where-they-stop)
4. [Rearrangement, when the objects have to end up somewhere](#4-rearrangement-when-the-objects-have-to-end-up-somewhere)
5. [Buffer space](#5-buffer-space)
6. [Re-checking after every action](#6-re-checking-after-every-action)
7. [What runs on an Apple Silicon Mac, and under what licence](#7-what-runs-on-an-apple-silicon-mac-and-under-what-licence)
8. [The five failures worth remembering](#8-the-five-failures-worth-remembering)

---

## 1. Why the order is a property of the scene

Picking up an object changes three things about the objects that are left, and
each of the three can turn a possible task into an impossible one.

**It changes what is reachable.** The gripper needs room for its own body, not
only for the object. While a neighbour is in the way, the approach that would
work does not exist, and the inverse kinematics solver reports the same nothing
it reports for a pose outside the workspace. Once the neighbour is gone the
approach exists. Nothing about the arm changed.

**It changes what is visible.** A depth camera reports the surfaces it can see.
An object standing behind another is partly or wholly missing from the point
cloud, so its pose estimate is either absent or wrong. Remove the object in
front and the one behind is measured properly for the first time. This is why
[object perception](../06_object-perception/01_overview.md) and ordering are the
same subject seen from two sides.

**It changes what is stable.** An object resting on another falls when the other
is taken. A stack that was upright becomes a scatter, and every pose computed
before the collapse is now wrong.

Those three effects give the property that this whole document rests on. **The
set of objects the arm can deal with is a function of which objects are still
there.** It is not a fixed list computed once. It shrinks and grows as the scene
changes, and the sequence of choices therefore matters in its own right.

### 1.1 Why you cannot simply try orders until one works

The obvious response is to search: try an order, and if it fails try another.
The number of orders makes this unattractive very quickly, because it is the
factorial of the number of objects.

For 8 objects there are 8 × 7 × 6 × 5 × 4 × 3 × 2 × 1 = 40,320 orders. For 12
objects there are 479,001,600. For 20 there are 2,432,902,008,176,640,000, which
is more orders than there are microseconds in seventy thousand years.

The blocking graph in the next section replaces that search with a linear scan.
For 8 objects it inspects 8 × 7 = 56 ordered pairs of objects and then walks the
result once. The saving is not a constant factor; it is the difference between
an algorithm that scales and one that does not.

## 2. The blocking graph

A graph, here, is nothing more than a set of items with arrows between some pairs
of them. The items are the objects on the table. Each arrow records one fact:
*this object must be moved before that one*. Nothing else goes in.

The word for the arrows having a direction is **directed**. The word for the
arrows never leading in a loop back to where they started is **acyclic**. A
directed graph with no loops is a directed acyclic graph, which everybody
abbreviates to DAG, and the shape of the graph is the whole answer to the
ordering question.

### 2.1 Building it from footprints and reach

The arrows come from geometry, and you already have the geometry if you have a
segmented point cloud or a set of object poses. For each object, work out what
the arm has to occupy in order to pick it up, and then ask which other objects
are inside that volume.

What the arm has to occupy takes one of two shapes, and which one applies is
decided by how the object can be gripped.

For a **top-down grasp**, the gripper descends onto the object with its jaws
open. It therefore needs a clear column above the object, of the open gripper's
own outer width. A neighbour is in the way when its body intrudes into that
column.

For a **side grasp**, the gripper travels in horizontally from outside the scene.
It therefore needs a clear corridor from the edge of the workspace to the object,
of the gripper's width and along the direction of approach. A neighbour is in the
way when it stands anywhere in that corridor.

The arithmetic for the top-down case is worth doing once, because it produces a
single number that decides whether ordering matters at all. Take a parallel-jaw
gripper whose open outer width is 100 mm, so it occupies a disc of radius 50 mm
about the object it is picking. Take cylindrical objects of radius 30 mm. A
neighbour's body reaches to 30 mm from its own centre, so it intrudes into the
column when the two centres are closer than 50 + 30 = **80 mm**. Space the
objects further apart than that and there are no arrows at all, and every order
works. This is the honest reason so many demonstrations never meet the problem.

The construction in pseudo code:

```
for each object i:
    corridor[i] = the volume the gripper must sweep to reach i,
                  taken from i's chosen approach direction and the
                  gripper's own open dimensions
blockers = empty map
for each object i:
    for each other object j:
        if body(j) intersects corridor[i]:
            add j to blockers[i]        # j must be moved before i
```

Three practical notes about that loop.

The corridor depends on the **chosen** approach, so the graph depends on a
decision the grasp planner makes. Give an object two acceptable approaches and
it has two corridors, and it is blocked only when every one of them is blocked.
That is the single cheapest way to remove arrows from the graph, and
[choosing a grip](../07_gripping/03_choosing-a-grip.md) is where the clearance
those approaches need is worked out.

The corridor must include the gripper's fingers, its body, the wrist behind it
and anything bolted to the wrist, such as a camera bracket. The most common way
to build a graph that is too optimistic is to model the fingers and forget the
camera.

Support is a separate source of arrows and it is read from contact rather than
from swept volume. If object j rests on object i, then j must be taken before i,
or i's removal drops j. Support arrows are usually acyclic on their own, because
contact heights order them and every stack has a bottom object. They are not
always acyclic: two boards leaning against each other, or any arch, support each
other mutually, and then the support arrows do form a loop.

### 2.2 Topological sort, in plain terms

Given the graph, the order comes out of an algorithm called a **topological
sort**. Despite the name it is very simple, and it is easier to understand as a
procedure than as a definition.

Look at all the objects that have no blockers left. Any one of them can be taken
now. Take one, record it, and delete it from the scene, which removes it from
everybody else's blocker list. Some other object now has no blockers left.
Repeat.

One of two things happens. Either every object gets recorded, and the recorded
sequence is a valid order. Or the procedure reaches a point where every remaining
object still has at least one remaining blocker, and nothing can be taken. The
second outcome is not a failure of the algorithm. It is a proof that **no valid
order exists**, because every object left is waiting for another object that is
also waiting.

In pseudo code:

```
remaining = all objects
order = empty list
loop:
    ready = every object in remaining whose blockers are all gone
    if ready is empty and remaining is not empty:
        report "no order exists"; the objects in remaining form the deadlock
        stop
    if remaining is empty:
        report order
        stop
    pick one object from ready        # any one; see section 3 for which
    append it to order
    remove it from remaining
```

Two things about that procedure are worth stating plainly.

It runs in time proportional to the number of objects plus the number of arrows,
which is why it replaces the factorial search of section 1.1.

**The choice inside `pick one object from ready` never affects whether the
procedure succeeds.** If any valid order exists, this procedure finds one,
whatever rule you use to break the tie. The tie-break decides how far the arm
travels, not whether the task is possible. This is the single most useful fact in
the document, and section 3 is about what people do instead.

Python has this in its standard library, so there is nothing to install and
nothing to license.
[`graphlib.TopologicalSorter`](https://docs.python.org/3/library/graphlib.html)
takes exactly the blocker map built above and returns an order, and raises
`graphlib.CycleError` when none exists. The exception carries the loop it found,
which is the diagnostic you want.

### 2.3 A scene that has a valid order

Here is a concrete case, small enough to check by hand. Five cylindrical parts of
radius 30 mm sit in a shallow crate whose walls make a top-down grasp impossible,
so the gripper must come in horizontally through the crate's open front. The
corridor is 100 mm wide, so a part is in the way when it stands nearer the front
than the target and its centre is within 50 + 30 = 80 mm of the target's line of
approach. Positions in millimetres, measured from the front-left corner, with the
opening along the front:

| Part | Position (x, y) | Blocked by |
| --- | --- | --- |
| A | (100, 100) | nothing |
| B | (100, 220) | A |
| C | (260, 100) | nothing |
| D | (200, 340) | C, E |
| E | (240, 240) | C |

Read that table as the graph: the last column is the list of arrows pointing into
each part. Run the procedure. A and C have no blockers, so either can go first.
Take A; B is now free. Take C; E is now free. Take E; D is now free. The order
A, C, B, E, D empties the crate, and so does A, B, C, E, D. Feeding the same
blocker map to `graphlib.TopologicalSorter` returns `['A', 'C', 'B', 'E', 'D']`.

Now notice what a plausible wrong order does. Nearest-to-the-arm first would take
A and C — both at y = 100 — and then reach for D, the part furthest back. D is
blocked by E, so the approach has no inverse kinematics solution, and what the
software reports is a planning failure on D. The report names the object that
cannot be reached rather than the object that should have been moved, which is
why this is diagnosed slowly.

### 2.4 A scene that has no valid order

Three objects sit close together. Each one can be gripped from only one side,
because of how it is turned, and the three sides are different:

| Object | Position (x, y) | Must be entered from | Blocked by |
| --- | --- | --- | --- |
| P | (300, 200) | the left | Q, R |
| Q | (240, 260) | the front | P, R |
| R | (240, 140) | the right | P |

Read the last column the same way as before. P waits for R, and R waits for P.
The procedure in section 2.2 finds nothing ready on its first pass and stops.
`graphlib` raises `CycleError` and names the loop, `['P', 'Q', 'P']`.

This outcome is common enough that it deserves a name rather than a shrug, and it
deserves the right response. **A loop does not mean "try harder". It means the
set of actions you gave yourself is insufficient, and you must add an action of a
different kind.** Which action depends on which of two situations you are in, and
confusing the two wastes a great deal of time:

- **The loop is about picking things up**, as here. P cannot be lifted at all
  while R is there. Moving P to a temporary place does not help, because moving P
  requires picking P up, which is the thing that is impossible. The cure is a
  different action: push R aside with the closed gripper, tip the object over,
  approach with a second and less preferred grasp, or change the tool. This is
  the subject of
  [singulation and pre-grasp](../07_gripping/10_singulation-and-pre-grasp.md),
  and the mechanics of the push itself are in
  [pushing and sliding](../07_gripping/09_pushing-and-sliding.md). One of those
  two is the right document to read next when you meet this case.
- **The loop is about where things go.** Every object can be picked up without
  difficulty; the conflict is that each one's destination is occupied by another
  one. Here a temporary place is exactly the cure, and section 5 is about it.

### 2.5 What each outcome tells you to do

The table below is the three shapes a blocking graph can have, what each means,
and what to do. Read it as a decision to make once, immediately after the graph
is built and before the arm moves.

| Shape of the graph | What it means | What to do |
| --- | --- | --- |
| no arrows at all | the objects are far enough apart that the gripper never intrudes on a neighbour | take them in whatever order is shortest to travel; the ordering question does not arise |
| arrows, no loops | a valid order exists, and there may be many | topological sort; use the tie-break to shorten the travel |
| at least one loop | no order of plain picks empties the scene | add an action of a different kind, chosen by which of the two cases in section 2.4 you are in |

**Five jobs the blocking graph suits:**

- clearing a crate or a tray where the parts have to come out through one opening
- unpacking, where the item at the back is invisible and unreachable until the
  items in front are gone
- disassembling a kit or a stack, where support relations decide the order and
  getting it wrong drops something
- any task where a failure to reach an object is expensive to diagnose, because
  the graph explains failures in terms of the blocker rather than the victim
- deciding, before a cell is built, whether a proposed tray layout is workable at
  all, which costs nothing and is done on a laptop

**Five jobs it cannot do:**

- tell you what to do about a loop; it detects one and stops there
- cope with objects that move when touched, because every arrow was computed from
  a scene that the first action invalidates
- account for a grasp that fails for a reason other than blocking, such as the
  object being too heavy or too slippery
- handle deformable objects and granular material, where "footprint" and
  "support" are not well-defined
- replace collision checking. An arrow says "the gripper's corridor is occupied";
  it does not say the resulting path is collision-free, which is still
  [the planning scene's job](03_planning-a-path.md#7-the-planning-scene-and-what-collision-checking-really-checks)

## 3. The cheap heuristics, and where they stop

Most people do not build a graph. They sort the objects by something and work
down the list, and four rules account for nearly all of what is written:

- **Outermost first.** Take the object nearest the edge of the pile or the table,
  on the grounds that it has the fewest neighbours.
- **Topmost first.** Take the object whose highest point is highest, on the
  grounds that nothing can be resting on it. In a scene where the only
  interactions are support, this rule is correct rather than approximate, because
  support arrows point upwards and the top of a stack has no blockers.
- **Nearest first.** Take the object closest to the arm, which minimises travel.
- **Least-blocking first.** Take the object with the fewest blockers, which is
  the only one of the four that looks at the blocking relation at all.

These rules deserve more respect than a graph-based treatment usually gives them.
They are cheap, they need no graph, and in an uncluttered top-down scene they are
all correct, because there are no arrows to violate. The reason to know the graph
is not that the rules are bad. It is to recognise the scenes in which they will
fail, and to know that the failure is structural rather than a matter of tuning.

### 3.1 What a measurement says

The numbers below come from a simulation written for this document and run on an
Apple M4. It is a model, not a measurement of any real robot, and the model is
stated in full so you can judge how far it carries.

A table 600 mm by 400 mm holds 8 cylindrical objects of radius 30 mm, placed at
random with their centres at least 80 mm apart, which leaves at least 20 mm of
clear table between neighbouring surfaces. Each object is picked either from
above, needing a clear disc of radius 50 mm, or from one of the four sides,
needing a clear corridor of half-width 50 mm running to the table edge. The
column `side entry` is the fraction of objects that must be entered from the
side. Each row is 20,000 random scenes.

Read the table as follows. The second column counts the arrows. The third says
how often a valid order exists at all. The next three say, **of the scenes where
an order exists**, how often a list sorted once at the start by that rule and
then executed without re-checking happens to be a valid order.

| Side entry | Arrows per scene | An order exists | Outermost first | Nearest first | Least-blocking first |
| --- | --- | --- | --- | --- | --- |
| 0 % | 0.00 | 100.0 % | 100.0 % | 100.0 % | 100.0 % |
| 25 % | 1.98 | 93.9 % | 52.9 % | 53.3 % | 96.3 % |
| 50 % | 3.95 | 77.9 % | 28.9 % | 30.1 % | 86.4 % |
| 75 % | 5.91 | 57.0 % | 15.9 % | 17.3 % | 73.4 % |
| 100 % | 7.87 | 35.4 % | 9.1 % | 9.6 % | 56.9 % |

Four things come out of that table, and they are the honest answer to "are the
heuristics good enough".

**When every object can be taken from above and the spacing exceeds the
gripper's own radius, ordering is a non-question.** The first row has no arrows
because 50 mm of gripper plus 30 mm of object is 80 mm, and the centres are 80 mm
apart by construction. Every rule scores 100 % because every order is valid. Most
demonstrations live in this row, which is why the subject is under-treated.

**Side entry is what creates the problem.** Going from no side entry to all side
entry takes the fraction of scenes with a valid order from 100 % down to 35.4 %.
Crates with walls, shelves, machine fixtures and anything approached through an
opening all force side entry, and they are exactly the settings where clearing
tasks are hardest.

**The two popular geometric rules are weak as soon as there are arrows.** With
half the objects entered from the side, sorting once by distance from the table
edge gives a valid order in 28.9 % of the solvable scenes. That is not a rule
that needs tuning. It is a rule that is answering a different question from the
one being asked.

**Least-blocking first is much better, and the reason is that it is almost the
algorithm.** It scores 86.4 % where the geometric rules score 29 %. What stops it
reaching 100 % is that it is computed once from the initial scene. Recompute it
after every removal and it becomes exactly the procedure in section 2.2, and it
then succeeds in 100 % of the solvable scenes, because that is what a topological
sort is. **The good heuristic, done properly, is the algorithm.** There is no
trade-off here to manage, only a re-check to remember, and section 6 is about its
cost.

**Five jobs the cheap heuristics suit:**

- a well-spaced top-down scene, where they are correct and a graph is overhead
- a stack cleared from the top, where topmost-first is exactly the support order
- a first working version, to find out whether ordering is your problem before
  building machinery for it
- a scene too uncertain to model, where the arrows would be guesses and a guessed
  arrow is worse than no arrow
- choosing between the several objects a topological sort says are ready, where
  nearest-first is the right tie-break and costs nothing

**Five jobs they cannot do:**

- tell you when they have failed, as opposed to producing a reach that fails
- handle side entry, which is where the arrows come from
- detect that no order exists, so the arm attempts an impossible task and reports
  the wrong object
- account for support and reachability together, since each rule looks at one
  effect
- give a reason for their answer, which matters when somebody has to sign the
  cell off

## 4. Rearrangement, when the objects have to end up somewhere

Everything so far assumed the objects leave the scene. Much of the time they do
not. They have to end up in specified places: parts into a fixture, items into a
kit tray, tools back into their outlines. This is **rearrangement**, and it is
harder than clearing for a reason that is easy to state.

In clearing, the only constraint is the order of removal. In rearrangement there
are three more. Every object needs a place to go, and its place may be occupied
by another object. Putting an object down creates a new obstacle, so the act of
progressing also creates new arrows. And the same object may need to be moved
twice, once out of the way and once to its destination, so the sequence is no
longer a permutation of the objects at all.

### 4.1 What is hard about it

The hardness is combinatorial rather than geometric, and it has been proved
rather than observed.

The classical result is the **warehouseman's problem**: moving several rectangular
objects inside a rectangular room to specified goal positions. Hopcroft, Schwartz
and Sharir showed in 1984 that this is PSPACE-hard, which means that no algorithm
is known that solves it in time polynomial in the number of objects, and that the
problem is at least as hard as an entire class of problems for which none is
expected. This is a statement about the worst case and not about your table, and
the practical reading is that you should not expect a general solver to scale.

The table-top version a robot arm actually faces has been studied directly.
[Complexity Results and Fast Methods for Optimal Tabletop Rearrangement with
Overhand Grasps](https://arxiv.org/abs/1711.07369) considers exactly the case in
this document, similar objects on a flat surface approached from above, and shows
by reduction from well-understood hard combinatorial problems that minimising the
number of pick-and-place actions remains computationally hard both when the start
and goal poses overlap and when they do not. The same paper's second contribution
is the useful one: because the reductions run in both directions, existing
algorithms for those well-studied problems can be applied to rearrangement, and
they are fast in practice despite the hardness.

That pairing is the whole practical situation. The problem is hard in the worst
case and the scenes in front of you are not the worst case.

### 4.2 The decomposition people actually use

Nobody in a working cell solves rearrangement as one optimisation. The structure
that survives contact with real scenes has three parts and a loop around them.

**Choose a target order.** Decide the sequence in which objects will be moved to
their destinations. Build a graph as in section 2, but with an arrow from object
j to object i when j currently occupies the place i has to go, in addition to the
arrows for blocked approaches. Topologically sort it.

**Check feasibility of the whole chain before moving.** For each move in the
chosen order, verify that the pick pose has an inverse kinematics solution, that
the place pose has one **from the configuration the pick leaves the arm in**, and
that a path connects them. This is the same check that
[section 9 of planning a path](03_planning-a-path.md#9-planning-the-whole-task-as-one-thing)
prescribes for a single pick-and-place, applied to every move in the sequence.
The reason it matters more here is that a failure at move six is caused by a
choice at move two, and the further apart those are the more expensive the
diagnosis.

**Replan when it fails.** Something will fail: a grasp will slip, an object will
settle differently, perception will revise a pose. Do not treat this as an
exception. Treat it as the normal case, rebuild the graph from the scene as it
now is, and sort again. The cost of doing so is in section 6 and it is small.

In pseudo code:

```
loop until every object is at its goal:
    scene   = perceive()
    graph   = blocking_arrows(scene) + goal_occupancy_arrows(scene, goals)
    order   = topological_sort(graph)
    if order is none:
        pick an object on a loop, send it to a buffer (section 5), continue
    plan = []
    for each move in order:
        solve pick; solve place from the pick's configuration; solve the path
        if any of the three fails:
            drop this order, try the next-best tie-break, or buffer and continue
        append to plan
    execute only the first move of plan       # then re-perceive
```

The last line is the one people resist and it is the one that matters. The plan
is computed for the whole sequence, because that is how you find out that move
six is impossible. Only the first move is executed, because everything after it
was planned against a scene that the first move changes.

**Five jobs a full rearrangement formulation suits:**

- kitting, where every item has an assigned pocket and pockets get blocked
- restoring a fixture or a workspace to a known layout between runs
- any task where objects swap places, which is the case a clearing formulation
  cannot express at all
- dense scenes where the destination area is also the source area, so every
  placement creates an obstacle
- planning a tray or fixture layout offline, by asking whether the intended
  assignment has a feasible order before the tray is made

**Five jobs it cannot do:**

- run in a fixed time budget, because the worst case is provably bad and the
  solver cannot tell you in advance which case you handed it
- cope with objects whose pose changes when a neighbour is moved, unless it
  re-perceives, which invalidates the plan it just computed
- decide the grasp, which it takes as given and which usually decides whether a
  move is feasible at all
- deal with an object that has no feasible destination, which it will discover
  only after exploring the orders that depend on one
- justify itself on a small problem. Three objects and three destinations are
  solved correctly by a for-loop and a re-check

### 4.3 The software, and what each costs

Four things are worth naming, and the reason to name the alternative in each case
is that the obvious choice is often wrong for a reason that is not about
capability.

[`graphlib.TopologicalSorter`](https://docs.python.org/3/library/graphlib.html)
is in the Python standard library. It takes the blocker map, returns an order,
and raises `CycleError` naming the loop when there is none. **Why this rather
than a graph library?** Because it is already installed, has no licence to
review, and does the only thing most projects need. It costs you nothing and it
does not find loops for you beyond the first one it hits.

[NetworkX](https://github.com/networkx/networkx) is the general graph library.
Its LICENSE.txt states plainly that it is distributed with the 3-clause BSD
licence, which the GitHub metadata does not classify. It gives you cycle
enumeration, strongly connected components and feedback-set approximations, which
is what you want once you have a loop and need to know the cheapest way to break
it. It was last pushed in September 2026 and has 17,280 stars, so it is healthy.
**Why this rather than the standard library?** Only when you need to reason about
the loop rather than merely detect it. It costs a dependency and some
performance; it is pure Python.

[MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor)
(BSD-3-Clause, read from its licence file; last pushed September 2026, 287 stars)
plans a task as a sequence of stages and propagates solutions forwards and
backwards, so a stage that cannot be solved prunes the upstream choices that
caused it. **Why this rather than the loop in section 4.2?** Because it does the
feasibility check across the whole chain as a first-class structure rather than
as code you maintain, and it pays for itself when the number of candidate grasps
and places is large. It costs you a ROS 2 dependency, a C++ build, and a modelling
exercise, and at 287 stars it is not a widely-travelled road.

[PDDLStream](https://github.com/caelan/pddlstream) is the best-known open
implementation of task and motion planning, which searches the symbolic sequence
and the geometry together and is the genuinely general answer to rearrangement.
Two facts about it belong in any recommendation. Its licence, read from its
licence file, is **GPL-3.0**, not the permissive licence most robotics
repositories carry, which makes it unsuitable for a closed product. And it was
last pushed in October 2023, so it is research code that is no longer moving.
**Why this rather than the decomposition?** Because it solves the case the
decomposition cannot: when the symbolic choice and the geometric choice cannot be
separated. It costs a licence problem, a stale codebase and, as
[the one-arm training area](../10_one-arm-training/02_programmed-methods.md#5-task-and-motion-planning)
sets out, an honest reason why almost nobody uses it in production.

Two benchmarks exist if you want to evaluate rather than build.
[AI2-THOR Rearrangement](https://github.com/allenai/ai2thor-rearrangement)
(Apache-2.0, last pushed August 2023) and
[habitat-lab](https://github.com/facebookresearch/habitat-lab) (MIT, last pushed
May 2026) both define rearrangement tasks in simulated homes. Both come from the
embodied-agent literature summarised in
[Rearrangement: A Challenge for Embodied AI](https://arxiv.org/abs/2011.01975),
and both are about a mobile agent in a house rather than an arm over a table.
They are useful for reading about the problem and are the wrong shape for a
table-top arm.

## 5. Buffer space

A buffer is a place to put an object that is neither where it was nor where it
belongs. It exists to break a loop, and it is the part of this subject that gets
designed last and causes the most trouble.

Recall the distinction from section 2.4, because it decides whether a buffer is
any use. A buffer solves a loop about **destinations**. It does not solve a loop
about **picking up**, because an object you cannot pick up cannot be moved to a
buffer either.

### 5.1 The simplest case, worked through

Three objects sit at places 1, 2 and 3. Object A is at place 1 and belongs at 2.
B is at 2 and belongs at 3. C is at 3 and belongs at 1. Every destination is
occupied by an object whose own destination is occupied, so the graph is a loop of
length three and no order of three moves succeeds.

With one buffer it takes four moves. Move A to the buffer, which frees place 1.
Move C from 3 to 1, which is its destination and frees place 3. Move B from 2 to
3, which is its destination and frees place 2. Move A from the buffer to 2. Three
objects, four moves: the extra move is the price of the one buffer, and it is
exactly one extra move per loop broken.

### 5.2 How much buffer space you need

The question "how many temporary places do I need" has a precise answer in the
literature and a reassuring practical one.

[On Minimizing the Number of Running Buffers for Tabletop
Rearrangement](https://arxiv.org/abs/2105.06357) and its extended version,
[Minimizing Running Buffers for Tabletop Object Rearrangement](https://arxiv.org/abs/2304.01764),
work exactly on the dependency graph described in section 2. Three of their
results matter here. Finding the minimum number of running buffers is itself
NP-hard, so do not expect to compute the optimum. The number required can grow
without bound as the number of objects increases, even for identical cylinders,
so there is no constant that is always enough. And, in their own words, random
instances that more closely mimic real-world setups generally have fairly small
minimum buffer counts.

The simulation from section 3.1 gives the same shape of answer for the clearing
case. Taking the scenes in which no valid order exists, and counting the smallest
number of objects that would have to be dealt with by some exceptional means
before a valid order exists for the rest: when every object needs side entry,
71.3 % of unsolvable scenes need exactly one such object, 26.3 % need two, and
2.4 % need three or more. One temporary place covers most of it and two cover
97.6 %, and the small remainder is the reason not to hard-code one.

The practical rule that follows is to **design for two buffer places and detect
the case that needs three**, rather than designing for one and discovering the
second at three in the morning.

### 5.3 Where to put one, and the failure that follows from putting it anywhere

Here is the failure this section exists for. An object is set down in a place
that looks empty, and it is empty, and it is nonetheless the wrong place, because
it now stands in the approach corridor of an object that has to be picked up
later. The buffer placement created a new arrow, and the new arrow made the rest
of the order invalid. Nothing reported an error at the moment of the mistake. The
error appears several moves later as a failed reach on an unrelated object.

That is not a rare pathology, and the simulation puts a number on it. Lay a grid
of candidate buffer slots over the same 600 mm by 400 mm table at 80 mm pitch
with a 30 mm margin, giving 7 columns by 5 rows, which is 35 slots. With 8
objects on the table, an average of 15.05 of those 35 slots are far enough from
every object to hold another one. But when half the remaining objects need side
entry, only 8.63 of those free slots are also clear of every remaining object's
approach corridor: **57.4 % of the apparently free slots are safe.** When every
object needs side entry, only 4.69 are safe, which is **31.2 %**. Choosing a
buffer slot by "is it empty" is therefore wrong about two times in three in the
hardest case.

The test a buffer slot must pass is short, and it is the same test in every
case:

```
a slot is acceptable if:
    the object fits there without touching anything already placed
    the arm can reach the slot, both to place and to pick up again
    the slot lies outside the approach corridor of every object
        that has not yet been dealt with
    the slot lies outside the approach corridor of every goal placement
        that has not yet been made
    the object is stable there, which for a tall object means checking
        that it will not fall over rather than that it fits
```

Three further points decide whether that test can be satisfied at all.

**A buffer outside the working area is worth more than one inside it.** A slot on
a separate shelf, a second tray or a fixture beside the table satisfies the third
and fourth conditions automatically, because it is not in anybody's corridor. It
costs reach and cycle time. This is the single cheapest fix when loops are
frequent.

**Every buffered object is moved twice, so buffers cost cycle time in proportion
to how often you use them.** If a pick-and-place takes 4 seconds, one buffered
object in an eight-object task adds 4 seconds to roughly 32, which is 12.5 %.
That is a real cost and it is smaller than the cost of the task failing.

**Re-grasping is a hidden cost of buffering.** The object is put down and picked
up again, and the second grasp is not necessarily the first grasp. If the object
settles differently, the pose you place it from is not the pose you placed it at,
which is why the loop in section 4.2 re-perceives rather than remembering.

**Five jobs buffers suit:**

- swapping two objects between two places, which cannot be done without one
- kitting into a tray where a pocket is occupied by the wrong item
- breaking a destination loop of any length, which always costs exactly one extra
  move per loop
- staging: taking several objects out of a confined space into an open one where
  they can be dealt with comfortably
- re-grasping deliberately, when the grasp needed to pick an object up is not the
  grasp needed to place it

**Five jobs they cannot do:**

- rescue an object that cannot be picked up at all, which needs a push or a
  different tool
- work without free space, and the free space has to satisfy section 5.3's test
  rather than merely be empty
- preserve an object's orientation, unless the placement and the re-grasp are
  both controlled for it
- come free. Every buffered object is two moves instead of one
- handle an object that must not be set down, such as one that is open, full,
  hot, or sterile

## 6. Re-checking after every action

Every arrow in the graph was computed from a scene. The first action changes the
scene. From that moment the graph describes something that no longer exists.

This is the same error that
[section 7 of the overview](01_overview.md#7-why-a-plan-that-succeeds-can-still-fail)
identifies in a single pick-and-place, where an early choice makes a later step
impossible. The multi-object version is worse in one specific way: the invalidating
event is not a choice you made but a consequence you did not model. Objects
settle when a neighbour is removed. A leaning object falls upright. A pile
relaxes. The pose you measured for object five was measured through a gap that
object two used to make.

**The rule is short. Re-perceive and rebuild the graph after every action, plan
the whole remaining sequence, and execute only the next move.**

The cost is the obvious objection, so here it is in numbers.

The planning cost is negligible. Building the graph and running the topological
sort, in plain Python on an Apple M4 with no acceleration of any kind, takes
**18 microseconds for 8 objects**, 103 microseconds for 20 and 414 microseconds
for 40. Rebuilding it after every removal of an 8-object scene means doing it 8
times, which is 144 microseconds in total. This is not a cost. It is a rounding
error against a single camera frame.

The inverse kinematics cost is real but small. Checking the reachability of the
remaining objects after every removal means 8 + 7 + 6 + 5 + 4 + 3 + 2 + 1 = 36
checks rather than 8, using n(n+1)/2 for n = 8. MoveIt's default inverse
kinematics timeout is 0.05 seconds, as
[section 8.1 of reaching and reachability](02_reaching-and-reachability.md#8-finding-out-before-you-commit)
records, so in the worst case where every check runs to timeout that is 36 ×
0.05 = 1.8 seconds against 8 × 0.05 = 0.4 seconds, an increase of 1.4 seconds.
Spread across eight picks of perhaps 4 seconds each, which is 32 seconds, the
increase is 1.4 / 32 = 4.4 %. In practice most checks succeed in a few
milliseconds rather than timing out, so the real figure is lower.

The perception cost is the one that actually bites, because it is one extra
capture and one extra segmentation per pick rather than per task. Whether that
matters depends entirely on your pipeline, and it is the number to measure before
deciding anything. It is also the cost you were going to pay anyway the first
time an object settles and you pick at where it used to be.

Two refinements are worth knowing, and both are optimisations of a loop that
should be written the simple way first.

**Re-check only what could have changed.** Removing an object can only free the
objects it was blocking, and can only disturb the objects it was touching. Both
sets are in the graph you already built, so the update is local. This turns the
36 checks into something closer to the 8, and it is correct only if nothing
settles, which is why it is a refinement rather than the default.

**Distinguish a stale plan from a failed one.** If a reach fails and the rebuilt
graph shows a new arrow, the plan was stale and re-sorting fixes it. If a reach
fails and the graph is unchanged, the failure is about reachability or grasping,
and re-sorting will produce the same order and the same failure. Logging which of
the two happened turns an intermittent fault into a diagnosis.

## 7. What runs on an Apple Silicon Mac, and under what licence

The short answer is that the ordering machinery in this document is among the
very few parts of robotics that has no platform problem at all.

The table below lists each piece, its licence as read from the project's own
licence file, and whether it runs on an Apple Silicon Mac without an NVIDIA
graphics card. Read the last column as the practical answer for a laptop.

| Piece | Licence, from the licence file | On an Apple Silicon Mac |
| --- | --- | --- |
| `graphlib.TopologicalSorter` | Python Software Foundation licence, as part of the standard library | yes, it is already there |
| [NetworkX](https://github.com/networkx/networkx) | BSD-3-Clause, stated in LICENSE.txt | yes, pure Python |
| the blocking graph itself | your own code | yes; 18 microseconds for 8 objects, measured above |
| [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | BSD-3-Clause | only as far as ROS 2 does, which on macOS `arm64` means a community redistribution and no official support tier |
| [PDDLStream](https://github.com/caelan/pddlstream) | GPL-3.0 | yes in principle, and the licence is the reason to stop before the platform is |
| [OMPL](https://github.com/ompl/ompl) | 3-clause BSD, stated in LICENSE | yes; it is CPU code and builds natively |
| [cuRobo](https://github.com/NVlabs/curobo) | Apache-2.0 | no. It requires CUDA and has no CPU fallback |

Three conclusions from that table.

**The ordering layer is free of the usual platform trouble.** Building a blocking
graph, detecting a loop and sorting topologically are integer and geometric
arithmetic over tens of objects. They need no graphics card, no framework and no
licence review, and they run faster than the camera you are reading from.

**The licence trap here is PDDLStream rather than anything about hardware.**
GPL-3.0 on the most-cited open task-and-motion planner is the fact to check
before the architecture assumes it, and it is not visible from the papers that
cite it.

**Everything expensive is downstream.** The ordering decision is cheap; the
inverse kinematics, the motion planning and the perception it triggers are not.
That is the right way round, and it is the reason to make the ordering decision
explicitly rather than let it emerge from the order a segmentation routine
happened to return its clusters in.

## 8. The five failures worth remembering

**The arm reports a planning failure on the object you cannot reach, not on the
object you should have moved.** Section 2.3. The blocker is the cause and the
victim is what gets logged, which is why this is diagnosed slowly and why the
graph is worth building even when you intend to use a heuristic.

**A loop in the graph is a proof, not a hint.** Section 2.4. When no object has
an empty blocker list, no order of plain picks exists, and trying more orders,
tuning the planner or improving perception cannot change that. The only cure is
an action of a different kind.

**A buffer does not help an object you cannot pick up.** Section 2.4 again. This
is the distinction that wastes the most time, because "put it somewhere else for
now" is such a natural response to a loop and is useless in the case where you
cannot lift the thing.

**Free space is not the same as safe space.** Section 5.3. With every object
needing side entry, only 31.2 % of the empty slots on a table are outside every
remaining approach corridor. Putting an object down where it fits creates the
arrow that breaks the rest of the sequence, and the failure appears several moves
later on an unrelated object.

**The graph you sorted described the scene before you touched it.** Section 6.
Re-perceiving and re-sorting after every action costs 18 microseconds of graph
work and about 4 % of cycle time in inverse kinematics, and it is the difference
between a sequence that survives an object settling and one that does not.

Back to [the overview](01_overview.md), or on to
[licences and platforms](06_licences-and-platforms.md) for the whole area side by
side.
