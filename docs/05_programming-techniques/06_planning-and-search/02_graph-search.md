# Graph search

This page explains graph search: finding the shortest or cheapest route through a
set of places that are joined by moves. It covers the three methods everyone uses:
breadth-first search, Dijkstra's algorithm and A* (said "A star"). It answers four
questions. How does each method work? When is each one the right choice? Where does
a robot arm use them? And when should you use something else?

It is for a reader who has read the [chapter overview](01_overview.md). You do not
need to have taken an algorithms course. Every term is explained where it first
appears, and every number on this page comes from a real run of the code in
[`planning_and_search_1.py`](../../diagrams/planning_and_search_1.py).

Graph search matters beyond this page. The
[probabilistic roadmap](03_sampling-based-planning.md#prm-build-a-map-once-then-ask-it-many-times)
on the next page uses it to answer every query, and a satellite navigation app uses
it every time it finds a route.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [Graphs and grids: the words](#2-graphs-and-grids-the-words)
3. [How it works](#3-how-it-works)
   · [Breadth-first search: fewest steps](#breadth-first-search-fewest-steps)
   · [Dijkstra's algorithm: lowest total cost](#dijkstras-algorithm-lowest-total-cost)
   · [A*: aim at the goal](#a-aim-at-the-goal)
   · [Costs that are not distance](#costs-that-are-not-distance)
   · [The pseudocode](#the-pseudocode)
4. [Where it is used on a robot arm](#4-where-it-is-used-on-a-robot-arm)
5. [Where it is useful, and where it is not](#5-where-it-is-useful-and-where-it-is-not)
6. [Libraries that provide it](#6-libraries-that-provide-it)
7. [Why graph search, and what it costs](#7-why-graph-search-and-what-it-costs)
8. [Where to read next](#8-where-to-read-next)

---

## 1. The idea in one sentence

Graph search grows outwards from the start, one place at a time, always taking next
the place that is cheapest to reach so far, until it reaches the goal.

Here is an everyday example. You are in a large building and want to reach a
meeting room. You do not know the way. So you try every corridor one door at a time
from where you stand. Each time you reach a door, you write on a sticky note which
door you came through. When you reach the meeting room, you follow the notes
backwards. That gives you the route. Breadth-first search does exactly this. The
other two methods add one rule each: Dijkstra's algorithm counts how long each
corridor is, and A* also looks at a sign that says roughly which way the meeting
room is.

---

## 2. Graphs and grids: the words

A **graph** is a set of places joined by moves. The places are called **nodes**.
A move between two nodes is called an **edge**. Each edge can have a **cost**, which
is a number that says how bad it is to take that move. The cost can be a distance,
a time, or anything else you want the route to keep low.

Two kinds of graph come up on a robot arm.

- A **grid** cuts a space into equal squares, called **cells**. Each free cell is a
  node. Each cell is joined by an edge to its neighbours. On this page a cell has
  four neighbours: up, down, left and right. A cell that holds an object is left
  out, so no route can pass through it.
- A **roadmap** is a small graph where each node is a pose the arm can be in, and
  each edge is a move between two poses that is known to be safe. A person can make
  a roadmap by teaching poses, or a program can make one by sampling, as the
  [next page](03_sampling-based-planning.md) shows.

A **route**, also called a **path**, is a list of nodes where each one is joined to
the next by an edge. Its cost is the sum of the costs of its edges. The search
wants the path with the lowest cost.

---

## 3. How it works

All three methods share one loop. They keep a list of nodes that they have reached
but not yet looked at. This list is called the **open list**. On each turn of the
loop, they take one node off the list, look at its neighbours, and add the new
ones. They differ only in which node they take off next.

The examples in this section use one grid. It is a table seen from above, cut into
5 cm squares, 16 across and 10 deep. The gripper moves at a fixed height. A square
is occupied when something on the table is taller than that height: a box, a tray
of parts, and a bottle and a jar. Of the 160 squares, 35 are occupied and 125 are
free. The gripper starts at S and must reach G.

### Breadth-first search: fewest steps

**Breadth-first search**, or BFS, takes nodes off the open list in the order they
were added. The first node added is the first taken off. A list that works this way
is called a **queue**, like a queue at a shop counter.

This makes the search spread out in rings. First it reaches every cell one step from
S. Then every cell two steps away. Then three, and so on. So the first time it
reaches a cell, it has found the fewest steps to that cell.

1. Put S on the queue. Write 0 steps next to it.
2. Take the first cell off the queue.
3. For each free neighbour that has no number yet, write the cell's number plus 1,
   remember which cell you came from, and add the neighbour to the back of the queue.
4. Repeat from step 2 until G comes off the queue.
5. Follow the "came from" notes backwards from G to S. That is the path.

The picture below is the real result on the grid.

![Each number is the fewest steps from S to that cell; the path follows the numbers down from G](../../images/planning-and-search/graph-search/breadth-first-waves.svg)

The number in each cell is its distance from S in steps. The colour gets darker as
the number grows, so you can see the rings spread around the box. The pale blue line
is the path. It is 20 steps long, and every number along it is one more than the one
before. The white cells at the right were never reached, because the search stopped
as soon as G came off the queue. By then it had taken 98 cells off the queue and
reached 106.

Breadth-first search finds the fewest steps. It does not know that some steps may
cost more than others. When every step costs the same, that is all you need.

### Dijkstra's algorithm: lowest total cost

**Dijkstra's algorithm**, named after Edsger Dijkstra, who published it in 1959,
handles edges with different costs. It always takes off the open list the node with
the lowest total cost found so far. A list that always gives back its smallest item
is called a **priority queue**.

When a node comes off the list, its cost is final. No later route can be cheaper,
because every other node on the list already costs at least as much, and costs can
only grow along a route. This is why Dijkstra's algorithm needs every edge cost to be
zero or more.

Here is a worked example on a roadmap. A person has taught an arm six poses. The
picture shows them, and the time in seconds for each move that is known to be safe.
The arm is at "home" and must get to "above chute" as fast as possible.

![Six taught poses joined by safe moves; the blue route is the fastest from home to above chute](../../images/planning-and-search/graph-search/roadmap-of-poses.svg)

Each pose is labelled with its best time from home. The blue route is the one
Dijkstra's algorithm returns.

The table below shows every turn of the loop. Read it from top to bottom. The
"finalised" column is the pose taken off the list on that turn. The "updates" column
says which neighbours got a new, lower time.

| Turn | Finalised | Its time | Updates to neighbours |
| --- | --- | --- | --- |
| 1 | home | 0.0 s | camera view 1.2 s, above bin 1.5 s |
| 2 | camera view | 1.2 s | above scale 1.2 + 1.1 = 2.3 s, above tray 1.2 + 2.6 = 3.8 s |
| 3 | above bin | 1.5 s | above chute 1.5 + 3.6 = 5.1 s; above scale via the bin would be 2.4 s, which is not better |
| 4 | above scale | 2.3 s | above tray 2.3 + 1.4 = 3.7 s, better than 3.8; above chute 2.3 + 1.8 = 4.1 s, better than 5.1 |
| 5 | above tray | 3.7 s | above chute via the tray would be 4.7 s, which is not better |
| 6 | above chute | 4.1 s | this is the goal, so stop |

The answer is home, camera view, above scale, above chute, in 4.1 seconds. The route
through the bin to the scale and on to the chute takes 4.2 seconds, so it came close.
Notice turn 4. The tray's time dropped from 3.8 to 3.7 seconds, because a longer
path in moves turned out to be a shorter path in time. Breadth-first search would
have missed that, because it counts moves, not seconds.

### A*: aim at the goal

Dijkstra's algorithm spreads out evenly in every direction. It has no idea where
the goal is, so it spends effort on cells behind the start. **A\*** fixes this with
a guess.

For each node, A\* adds two numbers: the cost from the start to the node, which it
knows, and a guess of the cost from the node to the goal. The guess is called the
**heuristic**. A\* takes off the open list the node with the smallest total.

On a grid with four neighbours, a good guess is the **Manhattan distance**: the
number of steps across plus the number of steps up or down, ignoring obstacles. From
S to G that is 13 across and 1 down, so the guess is 14 steps. The real path is 20,
because it has to go round the box.

The guess must never be more than the real cost. A guess with this property is
called **admissible**. With an admissible guess, A\* still finds the lowest-cost
path. The Manhattan distance is admissible here, because obstacles can only make the
real path longer.

The picture below runs both methods on the same grid, with every step costing 1.
The shaded cells are the ones each method took off its list.

![Dijkstra looked at 98 cells; A* looked at 42 and found a path of the same length](../../images/planning-and-search/graph-search/dijkstra-and-a-star.svg)

Both find a 20-step path. Dijkstra's algorithm took 98 cells off its list, the same
as breadth-first search, because with equal costs the two behave alike. A\* took off
42, because the guess kept it heading towards G. On a larger grid, the saving grows.

The count depends a little on how ties are broken, which is what the search does when
two cells have the same total. This code breaks ties by taking the cell with the
smaller guess first, which is a common choice.

### Costs that are not distance

The cost does not have to be distance. It can be anything the route should keep low.
A common choice on an arm is **clearance**: a route that passes right next to an
object is allowed, but worse than one that keeps away from it.

In the picture below, a move into a pink cell costs 5 instead of 1. A pink cell is a
free cell that touches an occupied one, even at a corner.

![The fewest-steps path hugs the obstacles; the lowest-cost path keeps clear of them](../../images/planning-and-search/graph-search/cost-keeps-clear.svg)

On the left is the breadth-first path. It is 20 steps long, but 15 of its cells are
pink, so its cost is 15 × 5 + 5 × 1 = 80. On the right is Dijkstra's path with the
clearance cost. It is 22 steps long, and its cost is 38, because only 4 of its cells
are pink. Those 4 are where it has to pass through the gap between the box and the
tray. A\* with the same costs found a path of the same cost, 38. It took 72
cells off its list, against 80 for Dijkstra's algorithm.

The two extra steps buy a path that keeps 5 cm from everything nearly all the way.
That is the same trade Book 3 describes as padding in
[the planning scene](../../03_frameworks/03_arm-movement/03_planning-a-path.md#71-the-default-clearance-is-zero),
done here as a cost instead of a hard rule.

### The pseudocode

One piece of pseudocode covers all three methods. The comments say what to change
for each one.

```
function search(start, goal):
    cost_so_far[start] = 0
    came_from[start]   = nothing
    open = a list holding start

    while open is not empty:
        # BFS:      take the node that was added first
        # Dijkstra: take the node with the smallest cost_so_far
        # A*:       take the node with the smallest cost_so_far + guess(node, goal)
        current = take the chosen node off open
        if current was already finished:
            skip it and go round again
        mark current as finished
        if current is goal:
            return follow_back(came_from, goal)

        for each neighbour of current that is free:
            new_cost = cost_so_far[current] + move_cost(current, neighbour)
            if neighbour has no cost_so_far yet, or new_cost < cost_so_far[neighbour]:
                cost_so_far[neighbour] = new_cost
                came_from[neighbour]   = current
                put neighbour on open

    return "no path"

function follow_back(came_from, goal):
    path = [goal]
    while came_from[last node of path] is not nothing:
        add came_from[last node of path] to the end of path
    return path reversed
```

The line "skip it" matters for Dijkstra's algorithm and A\*. A node can be put on
the open list more than once, each time with a lower cost. Only the first copy to
come off counts.

---

## 4. Where it is used on a robot arm

Graph search works best when the space has few dimensions, or when the graph is small.
Here are the places it turns up around an arm.

- **Choosing a sequence of taught moves.** A cell with a handful of taught poses,
  like the worked example, can hold them as a roadmap. Dijkstra's algorithm then
  finds the fastest sequence of known-safe moves between any two poses. The answer
  is the same every run, which matters in a cell that has to be signed off. The
  moves themselves are usually computed industrial motions, of the kind Book 3
  describes in
  [computed industrial motion](../../03_frameworks/03_arm-movement/03_planning-a-path.md#4-computed-industrial-motion-which-is-not-planning).
- **Answering a query on a probabilistic roadmap.** A PRM planner builds a graph of
  random free configurations. To plan a move, it joins the start and goal to the
  graph and runs Dijkstra's algorithm or A\*. The
  [sampling-based planning](03_sampling-based-planning.md#prm-build-a-map-once-then-ask-it-many-times)
  page shows this on the two-joint arm.
- **Moving a tool across a table.** When a tool moves at a fixed height, for example
  a gripper pushing objects into a row, the table from above is a two-dimensional
  grid. A depth camera gives the height of each cell. A cell is occupied when
  something in it is taller than the tool's height. A\* finds the push path.
- **Moving the gripper through a voxel grid.** A **voxel** is a cell in 3D: a small
  cube. A depth camera's points can fill a voxel grid of a bin or shelf. A\* can then
  plan a route for the gripper's position through the free voxels. Inverse
  kinematics must then find joint angles for each point, and a separate check must
  make sure the rest of the arm does not hit anything, because the search only
  looked at the gripper.
- **Moving a mobile base under an arm.** An arm on a wheeled base first needs the
  base to drive to the table. Base navigation plans on a flat grid of the floor, and
  Dijkstra's algorithm and A\* are the standard tools there.
- **Searching joint space for an arm with few joints.** For two or three joints, the
  whole configuration space fits in a grid, as the
  [overview](01_overview.md#2-where-the-search-happens-the-space-of-joint-angles)
  shows. A\* then gives the shortest path on that grid, and gives the same answer
  every time. Search-based planners also exist for more joints. They replace the grid
  with a small set of fixed joint moves and rely on a strong heuristic.
- **Planning the order of a task.** Each state of a task, such as which blocks are
  where, can be a node, and each action an edge. Breadth-first search then finds the
  fewest actions from the start state to the goal state. The
  [decisions and task logic](../08_decisions-and-task-logic/01_overview.md) chapter
  covers task-level choices.

---

## 5. Where it is useful, and where it is not

Graph search is exact on its own graph. If a path exists on the graph, it finds it.
If none exists, it says so, which a random planner cannot. Its weak points come from
the graph, not from the search.

The table below lists the common problems. Read each row as a problem, the sign you
would see, and what people use instead.

| Problem | The sign you would see | What people do instead |
| --- | --- | --- |
| Too many cells: a grid over six joints at 10° steps has over two billion cells | the search runs out of memory, or takes minutes | a [sampling-based planner](03_sampling-based-planning.md) |
| The grid is too coarse, so a narrow gap fills up | "no path", although the arm could clearly fit | a finer grid near the gap, or a sampler |
| Four-neighbour moves give a staircase path | the tool zig-zags where it should go diagonally | eight neighbours, "any-angle" search such as Theta\*, or a smoothing step |
| The map changes while the arm moves | the path runs through a place that is now blocked | search again each cycle, or an incremental method such as D\* Lite, which reuses the last search |
| The guess is poor, for example zero | A\* is no faster than Dijkstra's algorithm | a guess closer to the true cost |
| The guess is more than the true cost | A\* is fast but the path is not the shortest | keep the guess admissible, or accept the loss on purpose |
| The graph only checks the gripper | the gripper's route is free but the elbow hits the shelf | check the whole arm at each point, or plan in joint space |
| Negative costs | Dijkstra's algorithm returns a wrong answer | keep all costs zero or more; add a constant if needed |

The row about the guess being too large deserves one more sentence. Multiplying an
admissible guess by a number above 1 is called **weighted A\***. It trades a slightly
longer path for a much faster search, and it is often worth it. The point is to do it
knowingly.

---

## 6. Libraries that provide it

You rarely need to write graph search yourself, though it is a good exercise. The
table below lists well-known libraries. Read each row as one library, the languages
it serves, the names to look for, and a note.

| Library | Languages | Function or class | Note |
| --- | --- | --- | --- |
| NetworkX | Python | `networkx.shortest_path`, `networkx.dijkstra_path`, `networkx.astar_path`, `networkx.bfs_edges` | easiest to start with; slow on very large grids |
| SciPy | Python | `scipy.sparse.csgraph.dijkstra`, `scipy.sparse.csgraph.shortest_path`, `scipy.sparse.csgraph.breadth_first_order` | works on a sparse matrix of edge costs; fast |
| scikit-image | Python | `skimage.graph.route_through_array`, `skimage.graph.MCP` | cheapest path directly on an image or cost grid |
| Boost Graph Library | C++ | `boost::breadth_first_search`, `boost::dijkstra_shortest_paths`, `boost::astar_search` | the standard C++ choice |
| OMPL | C++, Python | the `PRM` planner family | runs a graph search on its roadmap for every query |
| Nav2 | C++ (ROS 2) | the NavFn and Smac planner plugins | grid planners for a mobile base, not for the arm's joints |

---

## 7. Why graph search, and what it costs

This section answers the four questions for graph search: what it is, what it does
for you, why it rather than the obvious alternative, and what it costs.

Graph search is a loop that grows out from the start, taking the cheapest node next,
until it reaches the goal. It gives you the best route on the graph you built, and
the same route every time. It also tells you for certain when there is no route on
that graph.

The obvious alternative for an arm is a
[sampling-based planner](03_sampling-based-planning.md), which is what MoveIt uses
by default. A sampler copes with six or seven joints, where a grid is hopeless. But
a sampler gives a different path each run, the path has detours, and when it fails
it cannot tell you whether no path exists or it simply ran out of time. Choose graph
search when the space is small enough to cut into cells, or when you already have a
small roadmap of safe moves, and you want the same best answer every time. Choose a
sampler when the arm has many joints and the space is too big to cover.

A second alternative is to teach every path by hand. That is deterministic too, but
it does not adapt when an object moves. Graph search on a roadmap of taught poses
keeps most of the determinism and still chooses the route at run time.

The costs are these. You must build the graph: choose the cell size, fill in which
cells are occupied, and decide what each move costs. A small cell size gives a better
path and uses more memory and time. The number of cells grows very fast with the
number of dimensions, which is the reason samplers exist. And the path on a grid is
only as smooth as the grid, so it usually needs a smoothing step before an arm
follows it.

---

## 8. Where to read next

- The next page is [sampling-based planning](03_sampling-based-planning.md). It
  covers the planners that take over when the grid becomes too large.
- [Trajectory optimisation](04_trajectory-optimisation.md) smooths a staircase grid
  path into one the arm can follow well.
- [Nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md)
  is the other search every planner leans on.
- [Greedy algorithms and set cover](../08_decisions-and-task-logic/04_greedy-algorithms-and-set-cover.md)
  shows the opposite approach: take the best-looking step and never look back.
- Book 6's [learned motion planners](../../06_neural-network-models/05_movement-models/06_learned-motion-planners.md)
  covers networks that guess a route directly, and why an ordinary search still
  checks the answer.
- Book 3's [planning a path](../../03_frameworks/03_arm-movement/03_planning-a-path.md)
  covers planning in practice with MoveIt.
