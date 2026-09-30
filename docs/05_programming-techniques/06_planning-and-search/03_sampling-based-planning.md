# Sampling-based planning

This page explains sampling-based planning: finding a route for the arm by trying
random joint angles, keeping the ones that hit nothing, and joining them up. It
covers the three methods you will meet most: the rapidly-exploring random tree
(RRT), RRT-Connect and the probabilistic roadmap (PRM). It also explains the two
ideas they rest on: the configuration space and collision checking.

It is for a reader who has read the [chapter overview](01_overview.md) and
[graph search](02_graph-search.md). This page uses graph search's words, such as
node, edge and path, without explaining them again.

Sampling-based planning is what most arm software uses to find a route. MoveIt 2
calls the Open Motion Planning Library (OMPL), and when no other planner is set, it
uses RRT-Connect. Book 3's
[planning a path](../../03_frameworks/03_arm-movement/03_planning-a-path.md#2-sampling-based-planners)
covers that in practice. This page explains how the methods work inside. Every
number and picture on this page comes from a real run of the planners in
[`planning_and_search_1.py`](../../diagrams/planning_and_search_1.py), on the book's
two-joint arm.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [Configuration space, drawn for a real arm](#2-configuration-space-drawn-for-a-real-arm)
3. [Collision checking: the only question a sampler asks](#3-collision-checking-the-only-question-a-sampler-asks)
4. [How it works](#4-how-it-works)
   · [RRT: grow a tree from the start](#rrt-grow-a-tree-from-the-start)
   · [A worked example: the first three tries](#a-worked-example-the-first-three-tries)
   · [RRT-Connect: grow two trees and join them](#rrt-connect-grow-two-trees-and-join-them)
   · [PRM: build a map once, then ask it many times](#prm-build-a-map-once-then-ask-it-many-times)
   · [The pseudocode](#the-pseudocode)
   · [Random means different every run](#random-means-different-every-run)
   · [Cleaning up the path](#cleaning-up-the-path)
5. [Where it is used on a robot arm](#5-where-it-is-used-on-a-robot-arm)
6. [Where it is useful, and where it is not](#6-where-it-is-useful-and-where-it-is-not)
7. [Libraries that provide it](#7-libraries-that-provide-it)
8. [Why sampling, and what it costs](#8-why-sampling-and-what-it-costs)
9. [Where to read next](#9-where-to-read-next)

---

## 1. The idea in one sentence

A sampling-based planner picks random sets of joint angles, throws away the ones
where the arm would hit something, and joins the rest into a tree or a network
until one of its routes links the start to the goal.

Here is an everyday example. You are in a dark, cluttered garage with a torch that
only lights a small spot. You want to reach the door on the far side. You cannot see
the whole garage, so you point the torch at a random spot, and if it is clear floor,
you step a little way towards it. Then you pick another random spot and step towards
it from wherever on your trail is closest. Your trail spreads out across the clear
floor. Sooner or later a step lands next to the door. A sampling planner does the
same, with joint angles in place of floor, and a collision checker in place of the
torch.

---

## 2. Configuration space, drawn for a real arm

A planner does not search the room. It searches the space of joint angles, called
the **configuration space**. One set of joint angles is one point in it, called a
**configuration**. The [overview](01_overview.md#2-where-the-search-happens-the-space-of-joint-angles)
introduced this. Here it is for a real arm.

The arm is the book's two-joint arm from
[Book 1](../../01_robotics-intro/02_maths/01_angles-and-trigonometry.md#1-the-arm-used-in-this-doc).
Link 1 is 3 m long and link 2 is 2 m long. Joint 1, the shoulder, can turn from
−180° to 180°. Joint 2, the elbow, can turn from −160° to 160°. Three objects stand
on the table: a box, a post and a jar. All three are more than 3 m from the base,
so only link 2 and the gripper can touch them.

The start is (10°, 20°), which puts the gripper at (4.686, 1.521) m. The goal is
(130°, 20°), which puts it at (−3.660, 3.298) m.

![The table from above, and the same scene as joint angles](../../images/planning-and-search/sampling-based-planning/workspace-and-configuration-space.svg)

The left panel is the table. The right panel is the configuration space. The
horizontal axis is joint 1's angle and the vertical axis is joint 2's angle. Each
coloured band is the set of configurations where the arm touches the object of the
same colour.

The script made the right panel by checking every configuration at 1° steps. That
is 361 × 321 = 115,881 checks. The bands cover 9.2% of the space: 3.8% for the box,
2.6% for the post and 2.8% for the jar.

Three things in the picture are worth noticing.

- A square box on the table becomes a curved band. There is no simple formula for
  the band's shape. Book 3 makes the same point: planners do not describe the free
  space, they probe it.
- The dashed straight line from start to goal crosses two bands. Turning both joints
  at a steady rate would hit the post between q1 = 23° and 38°, and then the box
  between q1 = 63° and 83°.
- The bands stop at about q2 = 95° and q2 = −95°. With the elbow bent more than
  that, link 2 folds back towards the base and passes inside the objects. So a free
  route exists: bend the elbow sharply, swing round, and straighten it again.

For a six-joint arm, the configuration space has six axes. Nobody can draw it, and
checking every cell would take billions of checks. A sampler checks a few thousand.

---

## 3. Collision checking: the only question a sampler asks

A **collision checker** is a program that takes one configuration and answers "yes,
the arm hits something" or "no, it is clear". It places the arm's shapes where the
joint angles put them, and tests them against the shapes of the obstacles. In this
script the test is simple: points every 5 cm along each link, each tested against
the box and two circles. Real checkers, such as the Flexible Collision Library
(FCL), test meshes and simple shapes for overlap, and they are much faster than the
planner around them.

A sampler asks the checker two kinds of question.

1. Is this one configuration clear? This is used for each random sample.
2. Is this whole straight move between two configurations clear? This is used for
   each new edge. The checker cannot test every point on a line, so it tests points
   along it at a fixed spacing.

The spacing in the second question is a real risk. The picture below checks one
move of the arm: joint 1 turns from 0° to 60° with joint 2 held at 30°. A rod 12 cm
across stands on the gripper's path.

![Checking every 10 degrees misses a thin rod; checking every degree catches it](../../images/planning-and-search/sampling-based-planning/checking-an-edge.svg)

On the left, the move is checked every 10°. That is 7 checks. The gripper is 4.84 m
from the base, so it moves 0.84 m between checks. The rod sits between the 40° check
and the 50° check, and no check touches it. The edge passes, and the arm would hit
the rod. On the right, the move is checked every 1°. That is 61 checks, and the one
at 45° hits the rod, so the edge is rejected.

This is the problem Book 3 describes in
[collisions are checked at sampled points](../../03_frameworks/03_arm-movement/03_planning-a-path.md#72-collisions-are-checked-at-sampled-points-not-continuously).
OMPL sets the spacing as a fraction of the size of the whole joint space, and on an
arm with wide joint limits the default comes to the order of ten degrees. The planners
on this page check every 1°, which is safe here but costs time: most of the checks
counted below are edge checks.

---

## 4. How it works

### RRT: grow a tree from the start

The **rapidly-exploring random tree**, or RRT, grows a tree of free configurations
out from the start. A **tree** here is a graph where each node has exactly one
parent, except the first node. So from any node, you can follow parents back to the
start.

1. Put the start in the tree.
2. Pick a random configuration inside the joint limits. Now and then, instead, pick
   the goal itself. This script picks the goal 5% of the time. This is called
   **goal bias**, and it pulls the tree towards the goal.
3. Find the node in the tree that is closest to the random configuration. This is a
   [nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md).
4. Take one short step from that node towards the random configuration. This script
   uses steps of 8°.
5. Ask the checker whether the new configuration is clear, and whether the move to
   it is clear. If both are, add it to the tree, with the nearest node as its parent.
   If not, throw it away.
6. If the new node is within one step of the goal, and the move to the goal is
   clear, add the goal and stop. Follow parents back from the goal. That is the path.
7. Otherwise go back to step 2.

Step 3 is where the name comes from. A random configuration in a large empty region
is most likely to be closest to a node on the edge of the tree. So the tree grows
fastest into the space it has not yet covered.

The picture below shows a real run, and RRT-Connect's run on the same problem.

![RRT after 40 tries, RRT at success, and RRT-Connect at success](../../images/planning-and-search/sampling-based-planning/rrt-and-rrt-connect.svg)

The left panel is RRT after 40 tries. The tree has 28 points: the start and 27 new
ones. The other 13 tries landed in a band or crossed one. The middle panel is the same run when it found the
goal: 504 tries, 393 points in the tree and 3,505 collision checks. Its path, in
black, goes over the top of the bands. It is 305° long in total joint movement, with
40 waypoints. The right panel is RRT-Connect, which the next section explains.

### A worked example: the first three tries

Here are the first three tries of that RRT run, with the real numbers.

1. The random number is 0.625, which is not below 0.05, so the planner picks a random
   configuration: (143.0°, 88.2°). The tree only holds the start, (10°, 20°), at a
   distance of 149.5°. One 8° step towards the random point reaches
   (17.12°, 23.65°). It is clear, and so is the move, so it joins the tree.
2. The random configuration is (−71.9°, 119.5°). The closest node is still the
   start, 128.9° away. One step reaches (4.92°, 26.18°). It is clear, so it joins
   the tree.
3. The random number is 0.005, which is below 0.05, so the planner aims at the goal,
   (130°, 20°). The closest node is (17.12°, 23.65°), 112.9° away. One step reaches
   (25.1°, 23.4°). That configuration lies in the post's band, where link 2 touches
   the post. The checker says no, and the point is thrown away.

The third try shows why a planner that only heads for the goal gets stuck. From
here, heading straight for the goal runs into the post's band. The random tries are what carry the
tree up and over the bands.

### RRT-Connect: grow two trees and join them

**RRT-Connect** grows two trees: one from the start and one from the goal. It takes
turns between them.

1. Grow one tree by one step towards a random configuration, as in RRT.
2. If that worked, take the new node and try to reach it from the other tree. Keep
   stepping from the other tree's nearest node towards it until you reach it or
   hit something. This greedy stepping is the "connect" in the name.
3. If the other tree reached the new node, the two trees are joined. The path is
   start tree's branch plus goal tree's branch.
4. Otherwise swap the roles of the two trees and go back to step 1.

In the right panel of the picture, blue is the start tree and orange is the goal
tree. On this run it needed 459 tries, 242 points and 2,612 collision checks.

Over 100 runs, RRT-Connect needed a median of 1,922 collision checks against 2,805 for
RRT, about a third fewer. This is a small, open problem with two joints. In larger
spaces with more joints the gap is usually much wider, which is why MoveIt uses
RRT-Connect by default. Book 3 says the same.

### PRM: build a map once, then ask it many times

The **probabilistic roadmap**, or PRM, splits the work in two.

The first part builds a roadmap, once.

1. Pick many random configurations. Throw away the ones in collision.
2. For each one that is left, find its nearest few neighbours, and add an edge to
   each neighbour where the straight move is clear.

The second part answers a query, as many times as you like.

1. Join the start and the goal to their nearest roadmap nodes, the same way.
2. Run [Dijkstra's algorithm or A\*](02_graph-search.md#dijkstras-algorithm-lowest-total-cost)
   on the roadmap from the start to the goal.

![A PRM on the two-joint arm: free samples, the edges between them, and the path found by Dijkstra's algorithm](../../images/planning-and-search/sampling-based-planning/probabilistic-roadmap.svg)

This run picked 150 random configurations. Ten fell inside a band and were rejected;
they are the crosses. The other 140 each tried to join their 10 nearest neighbours
within 45°, and 446 edges were clear. Building the roadmap took 15,151 collision
checks. Answering the query took only 369 more, to join the start and the goal. The
path, in black, goes under the bands this time, with the elbow bent the other way.
It is 337° long.

The build cost is high, but it is paid once. When the scene does not change, every
later query is cheap. When the scene does change, edges that pass through the new
object are wrong, and the roadmap must be checked again. That is why RRT-Connect,
which builds nothing in advance, is the usual choice for an arm whose scene changes
every time.

### The pseudocode

Here is RRT. RRT-Connect and PRM use the same pieces: a sampler, a nearest-neighbour
search, a step, and the two collision questions.

```
function rrt(start, goal, step, goal_bias, max_tries):
    tree = a tree holding start, with no parent
    repeat max_tries times:
        if random number < goal_bias:
            target = goal
        else:
            target = a random configuration inside the joint limits

        near = the node in tree closest to target
        new  = move from near towards target, at most step far

        if configuration_is_clear(new) and move_is_clear(near, new):
            add new to tree, with parent near
            if distance(new, goal) <= step and move_is_clear(new, goal):
                add goal to tree, with parent new
                return follow parents back from goal

    return "no path found in time"

function move_is_clear(a, b):
    for each point from a to b, spaced at the check spacing:
        if not configuration_is_clear(point):
            return false
    return true
```

Notice the last line of `rrt`. It does not say "no path exists". It says none was
found in the time allowed. A sampler cannot tell the two apart.

### Random means different every run

The planners are random on purpose. So the same problem gives a different answer
each run. The script ran RRT and RRT-Connect 100 times each on the problem above,
with 100 different random seeds. A **seed** is the number that starts a random
number generator, so the same seed gives the same run.

The table below shows the spread. Read each row as one planner. The "tries" columns
count trips round the loop. The "path" columns give the total joint movement along
the path found.

| Planner | Tries, fewest | Tries, median | Tries, 90th percentile | Tries, most | Checks, median | Checks, most | Path, shortest | Path, median | Path, longest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RRT | 170 | 408 | 617 | 964 | 2,805 | 5,385 | 277° | 347° | 479° |
| RRT-Connect | 168 | 306.5 | 421 | 578 | 1,922 | 3,130 | 295° | 393° | 692° |

The 90th percentile means 90 runs out of 100 needed that many tries or fewer. So
RRT's slowest run took nearly six times as many tries as its fastest. The paths
vary too. The longest RRT-Connect path, 692°, is more than twice the shortest. Book 3
lists this as the main reason samplers do not suit a cell that must do the same
thing every time.

RRT-Connect found paths with fewer checks, but its paths were longer on the median.
Joining two trees greedily finds a path fast, not a short path. That is the reason
for the next step.

### Cleaning up the path

A sampler's path has detours, because each step went towards a random point. Two
fixes are common.

The first is **shortcutting**. Pick two points on the path at random. If the
straight move between them is clear, cut out everything between them. Repeat a few
hundred times. The [overview](01_overview.md#5-how-they-work-together-on-one-move)
shows this on an RRT-Connect path: it drops from 384° to 250°. On the seed-7 run
above, the same step took the RRT-Connect path from 353° to 290°, with 4 waypoints
left.

The second is to hand the path to a
[trajectory optimiser](04_trajectory-optimisation.md), which makes it smooth and
pushes it away from obstacles as well as shortening it.

There are also planners that keep improving their own path. **RRT\*** and **PRM\***
reconnect nodes whenever a shorter route through them appears. Given more and more
time, their paths approach the shortest possible. This property is called
**asymptotic optimality**. The cost is more time per try.

---

## 5. Where it is used on a robot arm

Sampling-based planners are the default way to move an arm through free space when
the scene is not fixed. Here are concrete places.

- **Moving from the camera pose to above a detected object.** The goal comes from
  perception, so it is different every time. The planner finds a route that clears
  the other objects on the table.
- **Reaching into a bin or shelf.** The arm has to pass the bin's rim or the shelf's
  edge. The free space is awkward, and a sampler will find its way in where a simple
  straight move would hit.
- **Carrying a held object.** Once the gripper holds something, the object is part
  of the arm. The planner checks it too. Book 3's
  [the object in the gripper is part of the arm](../../03_frameworks/03_arm-movement/03_planning-a-path.md#73-the-object-in-the-gripper-is-part-of-the-arm)
  explains what happens if nobody tells the planner.
- **Recovering after a fault.** When the arm stopped somewhere unexpected, any
  valid path back to a safe pose is the whole requirement.
- **Planning many queries in a fixed cell.** A PRM built once for the cell answers
  every later query cheaply, as long as nothing in the cell moves.
- **Feeding an optimiser.** A sampler finds a route through the awkward part of the
  space, and a [trajectory optimiser](04_trajectory-optimisation.md) makes it smooth.
  This pairing uses each method for what it is good at.
- **Checking whether a grasp is usable at all.** Before the arm commits to a grasp,
  a program can ask a planner for the whole chain: reach, grasp, lift and place.
  Book 3's
  [planning the whole task as one thing](../../03_frameworks/03_arm-movement/03_planning-a-path.md#9-planning-the-whole-task-as-one-thing)
  explains why.

---

## 6. Where it is useful, and where it is not

A sampling planner is **probabilistically complete**. That means if a free path
exists, the chance that it finds one grows towards certainty as it runs longer. It
does not mean it will find one in the time you give it.

The table below lists the common problems. Read each row as a problem, the sign you
would see, and what people use instead.

| Problem | The sign you would see | What people do instead |
| --- | --- | --- |
| A narrow gap: few random samples land inside it | planning times out, or takes much longer, in one part of the cell | samplers that aim near obstacles, a learned sampler, or a longer time limit |
| The same move must be identical every run | the arm takes a different route each cycle | [graph search](02_graph-search.md) on a roadmap of taught poses, an optimiser, or computed industrial motion |
| A straight-line tool motion is needed | the tool wanders instead of going straight | a Cartesian path, as Book 3 explains |
| The planning time must have a hard limit | usually 50 ms, sometimes a second | an optimiser warm-started from the last answer, or a planner on a graphics card |
| Collision checks too far apart | a path through a thin rod or plate | a smaller check spacing, or padding around thin objects |
| The goal cannot be reached at all | a timeout, which looks like any other failure | check reachability first, before planning |
| The path is ugly | long detours, sharp corners | shortcutting, then a [trajectory optimiser](04_trajectory-optimisation.md) |
| The scene changes after the roadmap is built | a PRM path through a newly placed object | rebuild or re-check the roadmap, or use RRT-Connect |

The narrow gap problem deserves a sentence more. The chance that a random sample
lands in a gap is the gap's share of the whole space. A gap that is 1% as wide as
the space, in each of six joints, holds a tiny fraction of the samples. This is the
case where Book 6's learned samplers help, as the
[learned motion planners](../../06_neural-network-models/05_movement-models/06_learned-motion-planners.md#3-how-a-learned-route-planner-works)
page explains.

---

## 7. Libraries that provide it

Almost nobody writes a production sampler from scratch. The table below lists the
well-known libraries. Read each row as one library, the languages it serves, the
names to look for, and a note.

| Library | Languages | Function or class | Note |
| --- | --- | --- | --- |
| OMPL | C++, Python bindings | `ompl::geometric::RRT`, `RRTConnect`, `PRM`, `RRTstar`, `PRMstar`, `LazyPRM` | the reference collection of samplers; brings no collision checker of its own |
| MoveIt 2 | C++, Python (MoveItPy) | the OMPL planning plugin, with planner settings such as `RRTConnectkConfigDefault` | connects OMPL to the arm model, the planning scene and the collision checker |
| FCL | C++ (python-fcl for Python) | `fcl::collide`, `fcl::distance` | the Flexible Collision Library; MoveIt's usual collision checker |
| Coal (formerly HPP-FCL) | C++, Python | collision and distance queries | used by Pinocchio |
| Pinocchio | C++, Python | `computeCollisions` | arm kinematics plus collision checks in one library |
| PyBullet | Python | `getContactPoints`, `getClosestPoints` | a simulator whose collision queries are handy for quick experiments |

To try the ideas in Python, OMPL's Python bindings are the most direct. You give it
the joint limits and a function that says whether a configuration is clear. It gives
back a path.

---

## 8. Why sampling, and what it costs

This section answers the four questions for sampling-based planning: what it is,
what it does for you, why it rather than the obvious alternative, and what it costs.

It is a family of planners that probe the configuration space with random samples
and join the clear ones into a tree or a roadmap. It finds a collision-free route for
an arm with any number of joints, without anyone describing the free space.

The obvious alternative is [graph search](02_graph-search.md) on a grid of the
joint space. A grid gives the shortest path and the same answer every time. But the
number of cells grows 36 times with every joint at 10° steps, so a six-joint arm
would need over two billion cells. A sampler needs only a few thousand collision
checks on this page's problem, and still a manageable number for six joints. Choose
a sampler when the arm has more than about three joints and the scene changes. Choose
graph search when the space is small, or when you have a fixed roadmap.

The second alternative is a [trajectory optimiser](04_trajectory-optimisation.md).
It gives a smooth path and the same answer every time. But it starts from a guess
and improves it locally, so it can get stuck on the wrong side of an obstacle. A
sampler does not get stuck that way, because it keeps exploring. That is why the two
are so often used together.

The costs are these. The answer differs every run, and cannot be certified as the
same. The path has detours and needs cleaning. The time to find a path has no fixed
limit. A failure tells you nothing about why it failed. And the planner is only as
good as its collision checker and its planning scene: it cannot avoid what it was
not told about, and it can miss what falls between two checks.

---

## 9. Where to read next

- [Trajectory optimisation](04_trajectory-optimisation.md) takes a sampler's path
  and makes it smooth and clear of obstacles.
- [Numerical inverse kinematics](05_numerical-inverse-kinematics.md) turns a target
  pose into the goal configuration a sampler plans to.
- [Graph search](02_graph-search.md) explains the search a PRM runs on its roadmap.
- [Nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md)
  is the step that every RRT try uses to find the closest node.
- Book 6's [learned motion planners](../../06_neural-network-models/05_movement-models/06_learned-motion-planners.md)
  covers learned samplers and learned collision checkers, which speed up exactly the
  two expensive steps on this page.
- Book 3's [planning a path](../../03_frameworks/03_arm-movement/03_planning-a-path.md)
  covers MoveIt's defaults, the planning scene, and when planning is the wrong tool.
