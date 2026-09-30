# Greedy algorithms and set cover

This page explains greedy algorithms, and the most useful problem they solve on a
robot arm: set cover. It answers four questions. What does "greedy" mean for a
program? How does greedy set cover choose the fewest camera views that see every
object? How close to the best answer does it get? And when should you use
something else?

It is for a reader who has met the arm, the camera on its wrist and the idea of a
viewpoint, as in Books 1 and 2, but who has not taken an algorithms course. No
knowledge of complexity theory is needed. Where the page uses a term such as
"NP-hard", it explains it in plain words first.

The page sits in the chapter on
[decisions and task logic](../01_overview.md). The two pages before it,
[finite state machines](../02_most-used/01_finite-state-machines.md) and
[behaviour trees](../02_most-used/02_behaviour-trees.md), decide which step the robot does next.
This page and the next one,
[optimisation solvers](02_optimisation-solvers.md), decide which choice to make
when there are many possible choices and some are better than others.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [Set cover: the problem greedy is best known for](#2-set-cover-the-problem-greedy-is-best-known-for)
3. [How greedy set cover works, step by step](#3-how-greedy-set-cover-works-step-by-step)
   · [A worked example with eight glasses](#a-worked-example-with-eight-glasses)
   · [Checking the answer by trying every group](#checking-the-answer-by-trying-every-group)
   · [The pseudocode](#the-pseudocode)
4. [How far from the best greedy can be](#4-how-far-from-the-best-greedy-can-be)
5. [Where greedy choices are used on a robot arm](#5-where-greedy-choices-are-used-on-a-robot-arm)
6. [Where greedy is good enough, and where it is not](#6-where-greedy-is-good-enough-and-where-it-is-not)
7. [Libraries that provide it](#7-libraries-that-provide-it)
8. [Why greedy, and what it costs](#8-why-greedy-and-what-it-costs)
9. [The learned alternative](#9-the-learned-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. The idea in one sentence

A **greedy algorithm** builds an answer one piece at a time, and at each step it
takes the piece that looks best right now, without ever going back to change an
earlier piece.

Here is an everyday example. You have a shopping list of eight items, and there
are four shops in town. Each shop sells some of the items. You want to visit as
few shops as possible. The greedy way is simple. Go first to the shop that sells
the most items on your list. Cross those items off. Then go to the shop that sells
the most of the items that are left. Repeat until the list is empty.

That plan is quick to work out, and it is usually good. It is not always the best
plan. Section 3 shows a case where it visits three shops when two would have been
enough.

The word "greedy" describes two properties together:

- the choice at each step uses only what is known at that step. It does not look
  ahead to see how this choice affects the later ones.
- a choice, once made, is never undone.

Both properties make a greedy algorithm fast and short. Both are also the reason
it can miss the best answer.

---

## 2. Set cover: the problem greedy is best known for

The shopping example has a name. It is called **set cover**. The general form is
this. You have a list of things that must all be covered, called the
**universe**. You also have a collection of groups, called **sets**. Each set
covers some of the things. The task is to choose as few sets as possible so that
every thing is covered by at least one chosen set.

On a robot arm, set cover appears whenever one action serves several needs at
once. The most common case is choosing camera views.

Think of a camera on the arm's wrist, looking straight down at a table. From each
pose the arm can reach, the camera sees one rectangle of the table. That rectangle
is called the camera's **footprint**. An object is seen from a pose if it lies
inside that footprint. So each candidate pose is a set: the set of objects it
sees. The universe is the list of objects the robot must look at. Choosing the
fewest poses that together see every object is set cover.

Book 2 treats this choice in depth in
[choosing where to look](../../../02_perception/02_object-perception/09_choosing-where-to-look.md),
including how to test whether one object hides another from a view. This page
takes the sets as given and looks only at how to choose among them.

Set cover is **NP-hard**. In plain words, this means that no method is known
that always finds the smallest group of sets quickly. Every known exact method
takes, in the worst case, a time that grows faster than any fixed power of the
number of sets. For a handful of views that does not matter. For hundreds it does.
That is why the greedy method is the usual choice.

---

## 3. How greedy set cover works, step by step

The greedy method for set cover has three steps.

1. Start with every object marked as "not yet seen".
2. Look at every candidate view that is not chosen yet. For each one, count how
   many not-yet-seen objects it would see. Take the view with the highest count.
   Mark its objects as seen.
3. Repeat step 2 until every object is seen. If no view can add a new object while
   some objects are still unseen, stop and report those objects as not coverable.

When two views have the same count, take either one. A real program takes the
first one in its list, which is what the example below does.

### A worked example with eight glasses

Eight glasses, named A to H, stand on a table 600 mm wide and 400 mm deep. The arm
can place its wrist camera over four candidate points, looking straight down. The
camera is the same one used across this repository: a 320 by 240 pixel picture
with a focal length of 277.1 pixels. At a height `h` above the table, its
footprint is `h × 320 / 277.1` wide and `h × 240 / 277.1` deep. At 277 mm up that
is 320 by 240 mm. At 180 mm up it is 208 by 156 mm.

The picture below shows the four footprints, one per panel, and the glasses each
one contains.

![Each candidate view sees the glasses inside its footprint](../../../images/decisions-and-task-logic/greedy-algorithms-and-set-cover/views-and-footprints.svg)

The dashed rectangle is the footprint, and the red glasses are the ones inside it.
These sets were computed by the diagram script from the positions of the glasses
and the footprints, not typed in by hand.

The table below lists the same four sets. Read each row as one view: where the
camera is, and which glasses it sees.

| View | Point under the camera | Height | Footprint | Sees |
| --- | --- | --- | --- | --- |
| L | (150, 200) mm | 277 mm | 320 × 240 mm | A, B, C, D (4) |
| M | (300, 200) mm | 277 mm | 320 × 240 mm | B, C, D, E, F, G (6) |
| R | (450, 200) mm | 277 mm | 320 × 240 mm | E, F, G, H (4) |
| S | (500, 220) mm | 180 mm | 208 × 156 mm | G, H (2) |

Now run the greedy method.

1. All eight glasses are unseen. The counts are L 4, M 6, R 4 and S 2. View M has
   the highest count, so greedy takes M. Glasses B, C, D, E, F and G are now seen.
   Only A and H are left.
2. The counts for the views that are left are L 1 (it adds A), R 1 (it adds H) and
   S 1 (it adds H). They tie. Greedy takes the first, which is L. Now only H is
   left.
3. The counts are R 1 and S 1. Greedy takes R. Every glass is now seen.

The picture below shows the three steps.

![Greedy takes M first, then needs L and R for the two glasses M missed](../../../images/decisions-and-task-logic/greedy-algorithms-and-set-cover/greedy-steps.svg)

In each panel, red glasses are the ones this step adds, and grey glasses were
already seen. The line of numbers under each title is the count greedy compared at
that step.

So greedy uses three views: M, L and R.

### Checking the answer by trying every group

With only four views, a program can simply try every group of views. This is
called **brute force** or **exhaustive search**: try every possibility and keep
the best. It starts with groups of one view, then groups of two, and stops at the
first group that sees all eight glasses.

- No single view sees all eight. The largest, M, sees six.
- Of the six possible pairs, L with R sees all eight. L sees A to D and R sees E
  to H.

So the smallest answer is two views, L and R. Greedy used three. The picture below
puts the two answers side by side.

![Greedy uses three views; the best choice uses two](../../../images/decisions-and-task-logic/greedy-algorithms-and-set-cover/greedy-against-best.svg)

The left panel shows greedy's three footprints overlapping. The right panel shows
that L and R alone already cover the whole row of glasses.

The reason greedy lost is visible in the picture. View M is the biggest single
set, so it looks like the best first choice. But M sees the middle six glasses,
and it leaves one glass at each end. Each of those two glasses then needs its own
view. Views L and R each see fewer glasses than M, but they fit together without
overlap. Greedy never asks "how well does this view fit with the others?", only
"how many new glasses does this view see right now?". That is the whole
weakness of a greedy choice, in one example.

This kind of trap is not rare in a real cell. A camera held high sees the most, so
it wins the first round, and the objects near the edges then need extra views.

### The pseudocode

The pseudocode below is written in plain steps, not in any programming language.

```
greedy_set_cover(objects, views):
    # views: for each candidate view, the set of objects it sees
    unseen = copy of objects
    chosen = empty list
    while unseen is not empty:
        best_view = none
        best_count = 0
        for each view in views, not already in chosen:
            count = number of objects in (view.sees AND unseen)
            if count > best_count:
                best_view = view
                best_count = count
        if best_view is none:
            return chosen, unseen          # these objects no view can see
        add best_view to chosen
        remove best_view.sees from unseen
    return chosen, empty
```

The exact check used above is just as short, but its running time is very
different.

```
smallest_set_cover(objects, views):
    for k = 1, 2, ..., number of views:
        for each group of k views:
            if the union of what the group sees contains every object:
                return the group
    return none                            # no group covers everything
```

With `m` candidate views, the exact check can try up to `2^m` groups. Four views
means 16 groups. Sixteen views means 65,536 groups, which a computer tries in well
under a second. Thirty views means 1,073,741,824 groups, and forty views means more
than a million million. Greedy, in contrast, looks at each view at most once per
step, so it does at most `m × m` counts.

---

## 4. How far from the best greedy can be

Two questions matter in practice. How often does greedy miss the smallest answer,
and by how much?

To find out, the diagram script built 1,000 random scenes of each of three sizes.
In each scene, the glasses and the candidate views were placed at random on the
600 by 400 mm table, and each view's camera height was drawn between 150 and
350 mm. Scenes that no group of views could cover were thrown away and drawn
again. For each scene, the script ran greedy and also found the smallest answer by
trying every group. The chart below shows the result.

![Greedy matches the smallest answer in most random scenes, and rarely uses more than one extra view](../../../images/decisions-and-task-logic/greedy-algorithms-and-set-cover/random-trials.svg)

Each group of bars is one scene size. The green bar is the share of scenes where
greedy found a smallest answer, and the orange and red bars are the shares where
it used one or two views more.

The table below gives the same numbers, with the average number of views. Read
each row as one scene size.

| Scene | Greedy found the smallest | One view more | Two views more | Average, smallest | Average, greedy |
| --- | --- | --- | --- | --- | --- |
| 8 glasses, 8 views | 95.6% | 4.4% | 0% | 3.27 | 3.32 |
| 12 glasses, 12 views | 89.8% | 10.1% | 0.1% | 3.94 | 4.04 |
| 20 glasses, 16 views | 78.1% | 21.0% | 0.9% | 4.57 | 4.79 |

Three things stand out.

- Greedy is right most of the time, and never used more than two extra views in
  these trials.
- It gets worse as the scene grows. With 20 glasses it missed the smallest answer
  in about one scene in five.
- On average the extra cost is small: a fifth of a view with 20 glasses.

There is also a proven limit. If the largest set holds `d` objects, greedy never
uses more than `1 + 1/2 + 1/3 + ... + 1/d` times as many sets as the smallest
answer. That sum grows very slowly, roughly as the natural logarithm of `d`. In the
example, the largest view sees six glasses, so the limit is
`1 + 1/2 + 1/3 + 1/4 + 1/5 + 1/6 = 2.45`. Greedy used 3 views where 2 were
enough, which is 1.5 times, well inside that limit. Researchers have also shown
that, unless a famous open question in computer science has a surprising answer,
no fast method can promise a much better limit than this one. In short: greedy is
about as good as any fast method can promise to be.

A related question often matters more on a robot. Suppose the arm has time for only
two views. Which two should it take to see the most glasses? This is called
**maximum coverage**. Greedy is again the usual method: take the view that adds
the most, twice. It is proven to see at least about 63 per cent of what the best
pair would see. In the example, greedy's first two picks, M and L, see seven of the
eight glasses. The best pair, L and R, sees all eight.

---

## 5. Where greedy choices are used on a robot arm

Greedy set cover is one greedy algorithm among many. The same "take the best-looking
choice now" rule appears all over robot-arm software.

- **Choosing a fixed set of camera views offline.** Book 2 describes this in
  [how to pick them](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#52-how-to-pick-them):
  take the candidate that sees the most target points, remove those points, and
  repeat. It runs once at a desk. Then the chosen poses are tested on the arm.
- **Covering patches that could not be seen.** The
  [glasses-picking project](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/docs/problem-2/solutions/03-move-the-camera.md)
  in the sibling repository uses greedy set cover when some patches of the table
  were hidden behind glasses. Each candidate camera position sees some of the
  hidden patches. It takes the one that sees the most, and repeats until every
  patch is seen or the budget of extra looks runs out.
- **Deciding the order to visit places.** Nearest-neighbour ordering is greedy: go
  next to the closest place not yet visited. Book 2 measured it in
  [the order to visit them in](../../../02_perception/02_object-perception/09_choosing-where-to-look.md#6-the-order-to-visit-them-in):
  on average it costs four to ten per cent more travel than the best order, and in
  the worst trial 48 per cent more.
- **Removing duplicate detections.** An object detector gives several boxes for
  one mug. The clean-up step, called non-maximum suppression, is greedy. It keeps
  the box with the highest confidence, removes the boxes that overlap it, and
  repeats. Book 6 explains it in
  [cleaning up the extra boxes](../../../06_learned-models/03_seeing-models/02_most-used/01_object-detection.md#cleaning-up-the-extra-boxes).
- **Matching detections to tracked objects.** Greedy matching pairs the closest
  detection and track first, then the next closest, and so on. It is fast. It can
  make a wrong pair when two objects pass close to each other.
  [Assignment and matching](../../03_searching-and-matching/02_most-used/03_assignment-and-matching.md)
  compares it with the exact Hungarian method.
- **Picking from clutter.** A bin-picking cell often picks the object with the
  highest grasp score first, or the object on top of the pile first. That is a
  greedy order. It works well because the scene changes after each pick, so a
  long plan would be out of date anyway.
- **Online next-best view.** When the robot looks, thinks, and then chooses the
  next pose, it usually takes the pose that would reveal the most unknown space.
  That is maximum coverage, one view at a time.

---

## 6. Where greedy is good enough, and where it is not

Greedy is a good choice when a small loss does not matter, when the problem is too
big to solve exactly, or when the scene changes so often that a perfect long plan
would be wasted. It is a poor choice when each extra action is expensive and the
problem is small enough to solve exactly.

The table below lists the common ways greedy goes wrong on an arm. Read each row
as: the situation, the sign you would see, and what to use instead.

| Situation | What you would see | What to use instead |
| --- | --- | --- |
| One large set overlaps many small ones, as with view M above | Greedy's views overlap a lot, and each extra view adds only one or two objects | Try every group if there are fewer than about 20 candidates; otherwise an integer program ([optimisation solvers](02_optimisation-solvers.md)) |
| Each view has a different cost, such as a long arm move | Greedy picks a view that sees many objects but is far away | Weighted greedy: choose by new objects per second of arm travel, not by new objects alone |
| Ties between views | Different runs pick different views for the same scene | Break ties by a fixed rule, such as the shortest arm move |
| The order must obey rules, such as "C before B" | Nearest-neighbour ordering visits a blocked object first | A [blocking graph](../../../03_frameworks/03_arm-movement/07_ordering-and-rearrangement.md#2-the-blocking-graph), or a solver with constraints |
| Two tracks and two detections are close together | Tracked identities swap when objects pass each other | The Hungarian method in [assignment and matching](../../03_searching-and-matching/02_most-used/03_assignment-and-matching.md) |
| No candidate sees some object at all | The loop finds no view that adds anything | Report the object as unseen; add candidate poses; do not loop forever |

The weighted form in the second row deserves one more sentence. If moving to a view
costs time, divide each view's count of new objects by its cost, and take the view
with the highest ratio. This is the standard greedy method for **weighted set
cover**, and it keeps the same proven limit.

Two signs tell you greedy is probably good enough. First, the number of chosen
views is small compared with the number of candidates, and removing any one chosen
view leaves an object unseen. Second, when you run the exact search on a few saved
scenes, it agrees with greedy or finds one view fewer. If the exact search often
finds a smaller answer on your real scenes, that is the sign to switch.

---

## 7. Libraries that provide it

Greedy set cover is about fifteen lines of code in any language, and most
projects write it themselves. Libraries matter more for the exact alternative, and
for the other greedy steps listed in section 5. The table below lists well-known
libraries. Read each row as: the library, the languages it can be used from, the
part that is relevant, and what it gives you.

| Library | Languages | Function or module | Note |
| --- | --- | --- | --- |
| Your own code | any | a loop, as in section 3 | The usual choice for greedy set cover; there is nothing to install |
| Google OR-Tools | C++, Python, Java, C# | `ortools.sat.python.cp_model` (CP-SAT), `ortools.linear_solver.pywraplp` | Solves set cover exactly as an integer program; see [optimisation solvers](02_optimisation-solvers.md) |
| SciPy | Python | `scipy.optimize.milp` | Solves set cover exactly as a mixed-integer linear program |
| OR-Tools routing | C++, Python, Java, C# | `pywrapcp.RoutingModel` with `FirstSolutionStrategy.PATH_CHEAPEST_ARC` | Builds a first route greedily, then improves it |
| NetworkX | Python | `networkx.algorithms.approximation` | Greedy approximations for graph problems, including `greedy_tsp` for a visiting order |
| OpenCV | C++, Python | `cv2.dnn.NMSBoxes` | Greedy non-maximum suppression of detection boxes |
| torchvision | Python | `torchvision.ops.nms` | The same greedy clean-up, on the graphics processor |
| SciPy | Python | `scipy.optimize.linear_sum_assignment` | The exact alternative to greedy matching |

---

## 8. Why greedy, and what it costs

### What it is

A greedy algorithm makes the best-looking choice at each step and
never goes back. Greedy set cover repeatedly takes the set that covers the most
things not yet covered.

### What it does for you

It turns a problem that has no known fast exact method
into a loop that finishes in a fraction of a millisecond for any cell-sized
problem. It gives an answer that is usually the smallest, and is never far from
it: in the random trials above it used at most two views more than needed, and
usually none.

### Why greedy rather than the obvious alternative

The obvious alternative is to
compute the best answer exactly, either by trying every group or with an integer
programming solver. Choose greedy when the exact answer is not worth what it costs.
Trying every group becomes slow at about 25 to 30 candidate views, because the
number of groups doubles with each candidate. A solver has no such wall at cell
sizes, but it is a dependency to install, to learn and to run on the robot
computer. On many arms, the scene also changes after every move, so the robot
re-plans anyway, and one extra view now and then costs less than any of that. The
reverse also holds. When there are fewer than about 20 candidates, trying every
group is short, exact and fast, and there is no reason to accept greedy's loss.

### What it costs you

It costs a guarantee. Greedy can use more views than
needed, as it did in the example, and it does not tell you when it has done so.
It also costs predictability when views tie, unless you fix the tie-break rule.
And a greedy order cannot respect a rule such as "C before B" unless you add that
rule to the loop by hand.

---

## 9. The learned alternative

There is no learned model in Book 6 that replaces greedy set cover, because the
problem is only counting which views see which objects, greedy already solves it
in a fraction of a millisecond with a proven limit, and an exact solver is there
when greedy is not good enough. Where learning appears around greedy choices, it
supplies the scores that greedy ranks. A
[grasp quality model](../../../06_learned-models/05_grasp-models/03_also-used/02_grasp-quality-models.md)
scores each candidate grasp, and a bin-picking cell then takes the highest score
first, as section 5 described; a detector's confidences decide in the same way
which box non-maximum suppression keeps. A
[language model as planner](../../../06_learned-models/07_language-models/03_also-used/01_language-models-as-planners.md)
also chooses one step at a time, but it chooses which task step to do next from a
request in words, not which set of views covers every object.

---

## 10. Where to read next

- [Optimisation solvers](02_optimisation-solvers.md), the next page, solves
  ordering, assignment and packing problems exactly, and shows where greedy loses
  by 39 to 57 per cent on small tasks.
- [Assignment and matching](../../03_searching-and-matching/02_most-used/03_assignment-and-matching.md)
  compares greedy matching with the Hungarian method.
- [Graph search](../../06_planning-and-search/03_also-used/01_graph-search.md) explains A*,
  which also looks at the most promising place first, but, unlike a greedy
  choice, still finds the best path.
- [Choosing a technique](../../01_what-techniques-are/03_choosing-a-technique.md)
  sets out how to weigh speed against accuracy in general.
- Book 2's
  [choosing where to look](../../../02_perception/02_object-perception/09_choosing-where-to-look.md)
  covers the geometry of views: distance, angle, reach and occlusion.
- Book 3's
  [ordering and rearrangement](../../../03_frameworks/03_arm-movement/07_ordering-and-rearrangement.md)
  covers the order in which to move objects.
