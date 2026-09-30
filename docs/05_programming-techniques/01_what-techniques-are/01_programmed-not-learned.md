# Programmed, not learned

This is the first page of Book 5. The book explains the programming techniques
that robot arm software is built from. A technique here means a fixed method,
written down step by step by a person. Examples are the pinhole camera model,
the Kalman filter, A* search and proportional-integral-derivative (PID)
control. Each of them has its own page
later in the book.

This page answers three questions. What is a technique? How is it different
from a learned model? And how is this book laid out?

It is for a reader who has never taken a course on algorithms. You should know
what a robot arm, a frame, a camera, a pixel and a point cloud are, from Books 1
and 2. You do not need to know any programming language well, and you do not
need any maths beyond adding, multiplying and square roots.

Book 5 has a partner. Book 6,
[neural network models](../../06_neural-network-models/01_what-models-are/01_what-a-model-is.md),
covers the other way of building robot software: models that are learned from
examples. This book covers the methods that people write by hand. A real robot
arm uses both, and this page says how they fit together.

## Contents

1. [What a technique is](#1-what-a-technique-is)
2. [A first technique: the closest mug](#2-a-first-technique-the-closest-mug)
3. [The same steps in any language](#3-the-same-steps-in-any-language)
4. [Written rules or a trained model](#4-written-rules-or-a-trained-model)
5. [Why learn techniques when models exist](#5-why-learn-techniques-when-models-exist)
6. [What this book covers](#6-what-this-book-covers)
7. [How to read this book](#7-how-to-read-this-book)
8. [Where to read next](#8-where-to-read-next)

---

## 1. What a technique is

A robot arm program has many small jobs to do. It must turn a pixel into a
position. It must pick which object to grab first. It must find a path that does
not hit the table. It must tell each motor how hard to push. Each of these jobs
is a question with an answer.

A **technique**, in this book, is a written method that finds the answer to one
such question. It is a list of steps. A person worked out the steps, wrote them
down, and checked that they give the right answer. The computer follows the steps
exactly, in order, every time.

Computer scientists call such a list of steps an **algorithm**. This book uses
"technique" and "algorithm" to mean nearly the same thing. "Technique" is a little
wider. It also covers a way of setting up a problem, such as the pinhole camera
model, which is a formula more than a list of steps.

Every technique has three parts:

- The **input** is what you give it. For example, the positions of four mugs.
- The **steps** are what it does with the input. For example, "work out the
  distance to each mug, and keep the smallest".
- The **output** is what it gives back. For example, "mug D".

A technique gives the same output every time you give it the same input. Nothing
in it changes from one day to the next unless a person changes it. This is the
main thing that makes it different from a learned model, as section 4 explains.

Many techniques also have **parameters**. A parameter is a number that you choose
before you run the technique, and that stays fixed while it runs. For example, a
rule that says "anything closer than 580 millimetres is an object" has one
parameter: the 580. Choosing parameters well is a large part of using a
technique, and [choosing a technique](03_choosing-a-technique.md) comes back to
it.

---

## 2. A first technique: the closest mug

This section walks through one small technique from start to finish, so that the
three parts are concrete.

A robot arm stands at a table. There are four mugs on the table. A camera has
already found where each mug is. The arm should pick up the mug closest to its
gripper first, because that is the shortest move. The question is: which mug is
closest?

All the positions are measured in millimetres, on the table, as seen from above.
The gripper tip is at x = 250, y = 100. The four mugs are called A, B, C and D.

![The gripper tip and four mugs seen from above, with the distance to each mug written on the line to it](../../images/what-techniques-are/programmed-not-learned/closest-mug.svg)

The picture shows the gripper tip in yellow and the four mugs, with a line from
the tip to each mug; the shortest line, 113.1 mm to mug D, is drawn in red.

The steps are these:

1. Start with no answer yet, and a "smallest distance so far" that is larger than
   any real distance.
2. Take the first mug. Work out its straight-line distance from the gripper tip.
3. If that distance is smaller than the smallest so far, remember this mug and
   this distance.
4. Repeat steps 2 and 3 for every other mug.
5. The mug you remember at the end is the answer.

The distance in step 2 comes from Pythagoras' rule. Take the difference in x,
and the difference in y. Square each one, add them, and take the square root.
For mug D, at x = 330 and y = 180, the differences are 80 and 80. The squares
are 6,400 and 6,400. They add up to 12,800. The square root of 12,800 is about
113.1. So mug D is 113.1 mm from the gripper tip.

The table below follows the steps one mug at a time. Read it from top to bottom.
The last column shows what the technique remembers after each mug.

| Mug | Position (x, y) in mm | Distance in mm | Smaller than the smallest so far? | Remembered after this mug |
| --- | --- | --- | --- | --- |
| A | (470, 210) | 246.0 | yes, it is the first | A, 246.0 |
| B | (180, 380) | 288.6 | no | A, 246.0 |
| C | (520, -60) | 313.8 | no | A, 246.0 |
| D | (330, 180) | 113.1 | yes | D, 113.1 |

The output is mug D. The picture agrees.

Here are the same steps written as **pseudocode**. Pseudocode is a way of
writing steps that looks a little like a program but belongs to no programming
language. It is meant for people to read. Every technique page in this book
gives its steps this way.

```
input:  tip, the gripper position (x, y)
        mugs, a list of mug positions (x, y)
output: the mug closest to tip

best     = none
smallest = infinity
for each mug in mugs:
    d = square root of ((mug.x - tip.x)^2 + (mug.y - tip.y)^2)
    if d < smallest:
        smallest = d
        best     = mug
return best
```

A few words in this pseudocode need explaining. The `=` sign means "store this
value under this name". It does not mean "is equal to". `infinity` stands for a
number larger than any real distance, so the first mug is always smaller.
`for each mug in mugs` means "do the indented lines once for every mug". `^2`
means "squared". `return` means "this is the output".

This technique has a name of its own. It is the simplest form of
**nearest-neighbour search**: finding the item closest to a given point. It works
the same for 4 mugs or for 40,000 points in a point cloud. With 40,000 points it
becomes slow, and the
[nearest-neighbour search](../03_searching-and-matching/02_nearest-neighbour-search.md)
page shows faster ways to do it.

---

## 3. The same steps in any language

The techniques in this book are **language independent**. That means the steps do
not depend on which programming language you use. The steps above work in Python,
in C++, in Rust, or on paper with a calculator. Only the spelling changes.

Here are the same steps in Python. `math.hypot` is Python's name for "the square
root of the sum of the squares".

```python
import math

def closest_mug(tip, mugs):
    best, smallest = None, math.inf
    for name, (x, y) in mugs.items():
        d = math.hypot(x - tip[0], y - tip[1])
        if d < smallest:
            best, smallest = name, d
    return best
```

Here they are in C++, the other language that robot software is most often
written in.

```cpp
std::string closest_mug(Point tip, const std::map<std::string, Point>& mugs) {
    std::string best;
    double smallest = std::numeric_limits<double>::infinity();
    for (const auto& [name, p] : mugs) {
        double d = std::hypot(p.x - tip.x, p.y - tip.y);
        if (d < smallest) { smallest = d; best = name; }
    }
    return best;
}
```

Both programs have a starting value, a loop over the mugs, a distance, a
comparison and a result. They are the pseudocode, spelled two ways. Called with
the four mugs from the picture, the Python version returns `'D'`.

This is why the book teaches techniques as steps, and not as code. Once you
understand the steps, you can read them in any language. You can also recognise
them inside a library. Most of the time you will not write a technique yourself.
You will call a library that already has it, such as OpenCV for pictures or Open3D
for point clouds. Each technique page ends with a table of the libraries that
provide it, and the name of the function to call.

---

## 4. Written rules or a trained model

There are two ways to build the software that answers a question for a robot. This
section compares them.

The first way is to write the steps yourself. That is a technique, and it is what
this book is about. People call software built this way **programmed**.

The second way is to let a computer find the steps. You collect many examples of
inputs, each with the right output written next to it. A program then adjusts
millions of numbers inside a **model** until the model gives the right outputs for
the examples. This adjusting is called **training**, and software built this way
is called **learned**. Book 6 explains it, starting with
[what a model is](../../06_neural-network-models/01_what-models-are/01_what-a-model-is.md).

Here is one job done by a written rule, to show where a rule is strong and where it
is weak. A depth camera looks straight down at a table. For each pixel, it
reports how far away the surface is, in millimetres. The table is 600 mm from the
camera. Anything standing on the table is closer than that. So a simple written
rule for finding objects is: "a pixel is part of an object if its depth reading is
more than 0 and less than 580 mm". The 580 is the rule's one parameter. It leaves
20 mm of room for the camera's small errors. The "more than 0" part is there
because the camera writes 0 when it gets no reading at all.

![Two bar charts of depth readings along one row of pixels: a mug is found by the rule, and a glass is missed](../../images/what-techniques-are/programmed-not-learned/depth-rule.svg)

On the left, five pixels on a mug read between 503 and 512 mm, below the dashed
580 mm line, so the rule marks them in red; on the right, the camera gets no
reading through a glass and writes 0, so the rule finds nothing.

On the mug, the rule works. It is fast: one comparison per pixel. It is exact: you
can point at any pixel and say why it was chosen. And it needed no examples at
all.

On the glass, the rule fails. Light passes through glass instead of bouncing back,
so the depth camera gets no reading there. The rule was never told about glass.
Book 2 describes this problem in
[the depth hole, for glass and chrome](../../02_perception/02_object-perception/03_programmed-methods.md#17-the-depth-hole-for-glass-and-chrome).
You could write a second rule for holes in the depth picture. But then a shadow
also makes holes, and you need a third rule. Each new rule fixes some cases and
breaks others.

A learned model would handle this differently. You would show it many colour
pictures of glasses, each with the glass outlined by a person. It would learn what
glasses look like, including their edges and reflections, without anyone writing
a rule about light.

The table below compares the two ways. Read each row across to see how they
differ on one point.

| | Programmed technique | Learned model |
| --- | --- | --- |
| Who writes the steps | a person | a program, from examples |
| What you need to start | an understanding of the problem | many examples with the right answers |
| How fast it runs | often under a millisecond | often tens of milliseconds, usually on a graphics card |
| Can you see why it gave an answer | yes, step by step | mostly no |
| Works on things you did not plan for | usually not | often, if they look like the examples |
| How you fix a mistake | change a step or a parameter | add examples and train again |

Most real robot arms use both. A common pattern is this. A learned model finds
the mugs in the colour picture. Then programmed techniques do everything after
that: they turn pixels into positions, fit the table plane, plan the path and
drive the motors. Books 2 and 3 show this pattern many times, for example in
[methods you write yourself](../../02_perception/02_object-perception/03_programmed-methods.md)
and [programmed methods for one arm](../../03_frameworks/04_one-arm-training/02_programmed-methods.md).

---

## 5. Why learn techniques when models exist

This section answers the question a beginner often asks in 2026. Learned models
can do so much. Why spend time on hand-written techniques?

The first reason is that a robot arm cannot run without them. Even a robot built
around a large learned model still needs a camera model to turn pixels into
positions. It still needs transforms to move between the camera's frame and the
arm's frame. It still needs a controller to turn joint targets into motor
currents, a thousand times a second. None of these is usually learned.

The second reason is that techniques are exact where exactness matters. A
transform from the camera to the base is plain arithmetic. It is either right or
wrong, and you can check it with a ruler. A learned model gives answers that are
usually close. For a gripper with 5 mm of room on each side of a mug, "usually
close" is not always good enough.

The third reason is cost. A technique needs no training data and no graphics card.
It often runs in well under a millisecond on an ordinary processor. It is also
easier to test, because you can reason about every step.

The fourth reason is understanding. A learned model is often described as
"replacing" a technique. A movement model replaces a planner and a controller. A
grasp model replaces a hand-written grasp search. You cannot judge whether the
replacement is better unless you know what it replaced.

Techniques cost you something too. They need a person who understands the
problem well enough to write the steps. They break when the world does something
the person did not plan for, as the glass did in section 4. And each parameter,
such as the 580 mm limit, has to be chosen and then checked again whenever the
scene changes.

So the advice in this book is the same as in Books 2, 3 and 6. If a written
technique does the job reliably, use it. Switch to a learned model where the world
is too varied for rules. [Choosing a technique](03_choosing-a-technique.md)
explains how to tell which case you are in.

---

## 6. What this book covers

This book sorts the techniques used on robot arms into seven categories. Each
category answers a different question for the arm. Each category has its own
chapter, and each chapter starts with an overview page.

The table below lists the seven categories. Read each row as one category: its
name, the question it answers, and the link to its overview.

| Category | What it does | Start here |
| --- | --- | --- |
| Geometry and cameras | turns pixels, frames and joint angles into positions you can trust | [overview](../02_geometry-and-cameras/01_overview.md) |
| Searching and matching | finds the closest thing, and decides which thing is which | [overview](../03_searching-and-matching/01_overview.md) |
| Fitting and estimation | gets a clean shape or a steady number out of noisy measurements | [overview](../04_fitting-and-estimation/01_overview.md) |
| Image and point cloud processing | cleans up and cuts up pictures and point clouds so objects stand out | [overview](../05_image-and-point-cloud-processing/01_overview.md) |
| Planning and search | finds a way for the arm to get from here to there without hitting anything | [overview](../06_planning-and-search/01_overview.md) |
| Control and motion | turns a planned path into smooth, safe motor commands | [overview](../07_control-and-motion/01_overview.md) |
| Decisions and task logic | decides what the robot does next, and in what order | [overview](../08_decisions-and-task-logic/01_overview.md) |

Before those seven chapters comes this first chapter. It explains the ideas that
every later page uses. It has four pages:

1. Programmed, not learned. This page.
2. [The building blocks](02_the-building-blocks.md). The six ingredients that
   almost every technique is made from: frames and transforms, arrays and grids,
   graphs, noise, cost functions, and loops that run at a fixed rate.
3. [Choosing a technique](03_choosing-a-technique.md). How to judge a technique
   by its speed, its accuracy, how well it copes with bad readings and how much
   tuning it needs, and when to use a learned model instead.
4. [The map of techniques](04_the-map-of-techniques.md). All seven categories
   and all 24 technique pages on one page, placed on one arm task.

---

## 7. How to read this book

Read this first chapter in order. Each page uses words that the page before it
explained.

After that, the seven category chapters can be read in any order. Each one starts
with an overview page that says what the category is for and lists its
techniques. Each later page in a chapter covers one technique. Those pages all
follow the same order:

1. what question the technique answers, in one sentence, with an everyday example;
2. how it works, step by step, with a small example worked out with real numbers,
   and the steps as pseudocode;
3. where it is used on a robot arm;
4. where it works well, where it fails, and what people use instead when it fails;
5. which libraries already provide it, and the name of the function to call;
6. why you would choose it over the obvious alternative, and what it costs you;
7. where to read next.

If you want the whole picture first, read [the map of techniques](04_the-map-of-techniques.md)
next, and then come back to [the building blocks](02_the-building-blocks.md).

The pseudocode in this book follows the same few rules as the example in
section 2. `=` stores a value under a name. Indented lines belong to the line
above them. `for each` repeats. `if` decides. `return` gives the output. Words in
plain English stand in for anything that would take many lines of code, such as
"square root of".

A real worked example of many of these techniques on one arm is the
[pick-glasses project](https://github.com/RobinNagpal/robot-arm-projects/tree/main/v5-pick-glasses)
in the robot-arm-projects repository. It uses nearest-neighbour search, the
distance transform, clustering and a greedy choice of camera views to find and
pick up drinking glasses. The technique pages mention it where it helps.

---

## 8. Where to read next

- [The building blocks](02_the-building-blocks.md) is the next page. It explains
  the ingredients that almost every technique uses.
- [What a model is](../../06_neural-network-models/01_what-models-are/01_what-a-model-is.md)
  is the first page of Book 6. It explains learned models, the other half of
  robot arm software.
- [Methods you write yourself](../../02_perception/02_object-perception/03_programmed-methods.md)
  in Book 2 shows many programmed perception techniques at work, with code.
- [Programmed methods for one arm](../../03_frameworks/04_one-arm-training/02_programmed-methods.md)
  in Book 3 shows how written methods drive a whole arm task.
