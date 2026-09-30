# Decisions and task logic

This chapter is about the part of a robot program that decides what the robot
does next, and in what order. The other chapters of this book find the mug, plan a
path to it and move the joints. This chapter answers the questions above those
steps. Which step comes now? What happens when a step fails? Which mug goes first,
and where does each one go?

This page is the overview of the chapter. It says what the four techniques in it
are for, gives each one in a line, compares them in a table, and shows how they
connect to the rest of the book and to learned models. It is for a reader who knows
what an arm, a camera and a gripper are, but has not met these techniques before.

## Contents

1. [What this family of techniques is for](#1-what-this-family-of-techniques-is-for)
2. [The question it answers for an arm](#2-the-question-it-answers-for-an-arm)
3. [The four techniques](#3-the-four-techniques)
4. [How they compare](#4-how-they-compare)
5. [When each one runs](#5-when-each-one-runs)
6. [How this chapter connects to the others](#6-how-this-chapter-connects-to-the-others)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What this family of techniques is for

The seventh category of this book is **decisions and task logic**: deciding what
the robot does next, and in what order.

A real task is never one motion. Picking up a mug and putting it in a bin is at
least eight steps. The camera looks for the mug. The arm moves above it. The
gripper opens, lowers and closes. A check makes sure the mug is really in the
gripper. The arm lifts, carries the mug to the bin, and lets go. Then it goes home
and looks for the next mug.

Any of those steps can fail. The gripper can close on nothing, because the mug
moved a little. The planner can find no path, because a box is in the way. The mug
can slip out on the way to the bin. Most of the code in a working robot is not the
steps themselves. It is the code that decides what to do when a step fails.

The techniques in this chapter are the standard ways to write that code so that it
stays correct and readable as the task grows. They are all programmed rules. None
of them is trained from data. They are the same in every programming language.

---

## 2. The question it answers for an arm

The chapter answers two kinds of question. They sound alike, but they need
different tools.

The first kind is "what now?". The robot must react to events as they happen: the
grasp worked, the grasp failed, a person pressed stop. The answer changes from one
moment to the next. A **finite state machine** and a **behaviour tree** answer this
kind of question. They run all the time the robot works, and check what to do many
times a second.

The second kind is "which ones, and in what order?". The robot has a list of
choices and wants the best set or the best order. Which camera views see every mug?
Which mug should go in which slot of a tray? These questions are asked once, before
the work starts, or once per batch. **Greedy algorithms** and **optimisation
solvers** answer this kind of question.

The picture below shows all four questions on one table.

![One table with five mugs and a tray, marked with the question each technique answers](../../images/decisions-and-task-logic/overview/four-questions-one-table.svg)

The red mug is the one whose grasp just failed; a state machine or a behaviour tree
decides to try again. The blue circles are the four camera views that a greedy rule
chose, out of six, so that every mug is seen. The purple lines pair each mug with a
tray slot so that the total distance is the shortest of all 120 pairings, which the
script found by trying every one.

---

## 3. The four techniques

Each technique has its own page. The first two react to events. The last two choose
the best set or order.

- [Finite state machines](02_finite-state-machines.md) describe the task as a small
  set of named situations, such as "grasp" or "carry", with arrows that say which
  event moves the robot from one to the next.
- [Behaviour trees](03_behaviour-trees.md) describe the task as a tree of steps and
  checks. The tree is re-checked many times a second, and each part answers
  "success", "failure" or "still running". Retries and fallbacks are part of its
  shape.
- [Greedy algorithms and set cover](04_greedy-algorithms-and-set-cover.md) build an
  answer one choice at a time, always taking the choice that looks best right now.
  A common use is choosing the fewest camera views that together see every object.
- [Optimisation solvers](05_optimisation-solvers.md) search for the best answer to a
  problem written as numbers, a goal and rules. They order picks, assign objects to
  places and pack boxes, using libraries such as Google's OR-Tools.

---

## 4. How they compare

The table below compares the four techniques. Read each row as one technique. The
columns say what question it answers, how often it runs, what it needs as input, and
what it gives back.

| Technique | Question it answers | How often it runs | What goes in | What comes out |
|---|---|---|---|---|
| [Finite state machine](02_finite-state-machines.md) | What do I do now, given what just happened? | All the time, on every event | The current state and the latest event | The next state, and the action it starts |
| [Behaviour tree](03_behaviour-trees.md) | What do I do now, and what if it fails? | All the time, often 10 to 100 times a second | The world as the checks see it | The step to run now, and success, failure or running |
| [Greedy algorithm](04_greedy-algorithms-and-set-cover.md) | Which small set of choices covers everything? | Once per task or batch | A list of choices and what each one covers | A set of choices, usually close to the smallest |
| [Optimisation solver](05_optimisation-solvers.md) | What is the best order or assignment? | Once per task or batch | Numbers, a goal and rules | The best answer it can prove, or the best it found in time |

The first two rows are about control flow. They decide which step runs. The last two
rows are about choice. They decide what the steps work on. A real robot program uses
both kinds together: a behaviour tree runs the task, and one of its steps calls a
greedy rule or a solver.

---

## 5. When each one runs

The difference in timing is easy to see on one real run. The picture below comes
from the state machine on the [finite state machines](02_finite-state-machines.md)
page. It moves two mugs to a bin, and its first grasp closes on nothing.

![A timeline of one run: the task logic is busy all the time, the two choosers run once at the start](../../images/decisions-and-task-logic/overview/when-each-one-runs.svg)

The coloured bar is the state the task logic was in at each moment. The small ticks
above it show that it is checked every tenth of a second. The two diamonds on the
lower rows are single calls, made once at the start: one chooses the camera views and
one pairs mugs with tray slots.

This timing decides how fast each technique must be. Task logic runs thousands of
times in a task, so each check must take well under a millisecond. A chooser runs
once, so it can take a few hundred milliseconds, or even seconds, if the answer is
better.

---

## 6. How this chapter connects to the others

The techniques here sit on top of every other chapter of this book. Each step in a
state machine or a behaviour tree calls something from another chapter.

- The "detect mug" step uses the
  [image and point cloud processing](../05_image-and-point-cloud-processing/01_overview.md)
  chapter to cut the mug out of the picture, and the
  [geometry and cameras](../02_geometry-and-cameras/01_overview.md) chapter to turn
  its pixels into a position.
- The "is it the same mug as before?" check uses the
  [searching and matching](../03_searching-and-matching/01_overview.md) chapter.
- The "move above mug" step calls the
  [planning and search](../06_planning-and-search/01_overview.md) chapter to find a
  path, and the [control and motion](../07_control-and-motion/01_overview.md) chapter
  to follow it.
- A "holding mug?" check often reads a steady gripper width or force from the
  [fitting and estimation](../04_fitting-and-estimation/01_overview.md) chapter.

Learned models also meet this chapter in two places. First, a learned model can
be one step inside the tree. A detector from Book 6's
[object detection](../../06_neural-network-models/02_seeing-models/03_object-detection.md)
page can be the "detect mug" step, and a model from
[collision and failure detection](../../06_neural-network-models/08_touch-and-body-models/04_collision-and-failure-detection.md)
can be the "did the grasp fail?" check. The tree around them stays the same.

Second, a language model can sit above the tree. The page
[language models as planners](../../06_neural-network-models/06_language-models/02_language-models-as-planners.md)
shows a model that turns a spoken request into a list of steps. Even then, the
steps usually run inside a state machine or a behaviour tree, because that part must
be fast and must always do the same thing.

The map of the whole book is on
[the map of techniques](../01_what-techniques-are/04_the-map-of-techniques.md).

---

## 7. Where to read next

- Start with [finite state machines](02_finite-state-machines.md). They are the
  simplest way to write task logic, and the next page builds on them.
- Then read [behaviour trees](03_behaviour-trees.md), which most robot arm programs
  use today for the same job.
- [Greedy algorithms and set cover](04_greedy-algorithms-and-set-cover.md) and
  [optimisation solvers](05_optimisation-solvers.md) cover the "which ones, and in
  what order" questions.
- Book 3 shows behaviour trees in real code in
  [behaviour trees: putting a task in order](../../03_frameworks/01_tools-and-libraries.md#11-behaviour-trees-putting-a-task-in-order),
  and compares state machines and behaviour trees in
  [scripted logic](../../03_frameworks/04_one-arm-training/02_programmed-methods.md#3-scripted-logic-state-machines-and-behaviour-trees).
