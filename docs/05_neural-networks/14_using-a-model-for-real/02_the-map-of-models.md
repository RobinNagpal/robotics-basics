# The map of models

The page before this one,
[running and evaluating a model](01_running-and-evaluating-a-model.md), took a trained
file and made it drive an arm, and then measured whether it worked. This page is the
last of the book, so it teaches nothing new. It gathers what the other thirty-nine
pages explained into one map, and then answers the question a reader is left with,
which is what to reach for given a job.

It is for somebody who has read most of the book and wants the shape of it in one
place, and it is also for somebody coming back later with a problem in hand. Every
family named here was explained from scratch earlier, and every mention links to the
page that did the explaining, so this page is a set of signposts rather than an
account.

It has one more duty, which is to be honest about the parts that do not work yet.
Section 5 is the list of what is not solved, written plainly, because a book that
spent forty pages explaining how this machinery works owes its reader a clear account
of where the machinery stops.

Every number in the pictures is worked out and printed by
`docs/diagrams/using_a_model_for_real.py`. The arithmetic costs come from stated
example configurations of each family, and the machine that runs them is the same
example machine as the page before, which gets through 3.6 million million
multiply-adds a second at two bytes a number. The training-data figures are rough
orders of magnitude rather than measurements of any named dataset, and the page says
so where they appear.

## Contents

1. [The whole book in one map](#1-the-whole-book-in-one-map)
2. [The families, side by side](#2-the-families-side-by-side)
3. [What to reach for, given a job](#3-what-to-reach-for-given-a-job)
4. [When the answer is not a neural network](#4-when-the-answer-is-not-a-neural-network)
5. [What is not solved](#5-what-is-not-solved)
6. [What this book left out, and which book holds it](#6-what-this-book-left-out-and-which-book-holds-it)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. The whole book in one map

The book was written to be read in order, and the order was not arbitrary, because
each chapter needs particular earlier chapters and no others. Drawing those needs as
arrows gives the map of the whole book.

![Thirteen chapter boxes arranged in nine columns by how deep they sit, with pale blue arrows from each chapter to the chapters that need it](../../images/using-a-model-for-real/the-map-of-models/book-map.svg)

The book is thirteen chapters and forty pages, and the arrows say which chapters have to be read before which.

Read it from the left. Chapter 1 asks why some jobs cannot be written as rules, and
chapter 2 opens a network up. Chapter 3 trains one and chapter 5 turns pictures, sounds
and joint readings into numbers, and the transformer in chapter 6 needs both of those.
After the transformer the map widens, because models that see, models that generate,
models that use words and models that act all stand on the same machinery and can be
read in almost any order. Chapter 13, where this page sits, needs everything.

![A bar chart of pages per chapter, mostly 2 or 4, with a black line showing the running total reaching 40](../../images/using-a-model-for-real/the-map-of-models/pages-per-chapter.svg)

Twelve of the forty pages are the four chapters on how the machinery works, and sixteen are the five chapters on the families built from it.

The running total is the more useful line. After chapter 4 you have read 12 pages and
you know what a network is and how one is trained, after chapter 7 you have read 22 and
you know how a model is pretrained and adapted, and the remaining 18 pages are the
families themselves. So the first half of the book is machinery and the second half is
what the machinery is used for.

![A horizontal bar chart of the thirteen chapters, sorted by how deep each sits in the reading order, from level 1 for chapter 1 to level 9 for chapter 13](../../images/using-a-model-for-real/the-map-of-models/dependency-depth.svg)

Following the longest chain of arrows, chapter 13 sits nine levels deep, which is why it is the last.

The script works this depth out from the arrows rather than from the chapter numbers,
and the two mostly agree. The exceptions are worth noticing. Chapter 11, on learning
from outcomes, sits only four levels deep because it needs training and a loss and
nothing else, so it can be read straight after chapter 3. Chapter 8, on models that
generate, is the same. Chapter 10 sits seven levels deep because it needs both the
transformer and the chapter on models that see.

---

## 2. The families, side by side

Section 1 said which chapters stand on which, and this section puts the families those
chapters explain next to each other. The simplest way to compare them is by what goes
in and what comes out, counted in plain numbers, because a family is in the end a
shape of input turned into a shape of output.

![A horizontal bar chart on a log scale showing numbers going in and numbers coming out for nine families, from 320 in for a vision-language model to 3,145,728 in for a segmenter](../../images/using-a-model-for-real/the-map-of-models/inputs-and-outputs.svg)

A picture classifier turns 150,528 numbers into 1,000, a promptable segmenter turns 3,145,728 into 1,048,576, and a behaviour-cloning policy turns 301,063 into 112.

Three shapes stand out. The seeing models of
[detection and segmentation](../09_models-that-see/02_detection-and-segmentation.md)
and [depth and 3D](../09_models-that-see/04_depth-and-3d.md) give back almost as many
numbers as they take, because they answer something about every pixel. The models that
use words give back 32,000 numbers, which is one score for each word piece they could
say next, as
[large language models](../10_language-and-multimodal-models/01_large-language-models.md)
explains. And the policies of
[behaviour cloning and action chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md)
give back 112 numbers, which is sixteen future commands for seven joints, from an input
of two pictures. A policy throws almost everything away, which is exactly what makes it
hard to train.

![A scatter of nine families with training examples on the x axis and multiply-adds per decision on the y axis, both on log scales, with a dashed line at the 180 thousand million a 20 Hz loop allows](../../images/using-a-model-for-real/the-map-of-models/data-and-run-cost.svg)

The nine families spread over ten powers of ten in training data and two in arithmetic per decision, and only the segmenter is above what one 20 hertz loop allows.

The two axes are nearly independent, which is the point of this picture. A language
model is the most expensive thing in the book to train and one of the cheapest to run
once, because each new word costs only one pass through the weights with the earlier
words cached. A policy is the opposite, because a few hundred demonstrations are enough
to train it and every decision pays for two whole picture encoders. The training-data
figures are rough orders of magnitude, not measurements.

![Two log-scale bar charts: calls in a 6 second pick-and-place, from 1 for the language model to 3,000 for the safety checks, and the arithmetic each one costs over the episode](../../images/using-a-model-for-real/the-map-of-models/calls-per-episode.svg)

In one six-second pick-and-place the language model is asked once and the written safety checks run 3,000 times, while the detector and the depth model together cost 2,573 of the episode's 3,108 thousand million multiply-adds.

This is how the families actually sit together on a working arm. Each one runs at the
rate its job needs rather than at the rate of the control loop: the language model
plans once, the vision-language model checks the scene twice a second, the detector and
depth model run five times a second, the policy writes a chunk 2.5 times a second, and
the written safety layer of the page before runs 500 times a second. The whole episode
is 3,079 calls and 3,108 thousand million multiply-adds.

---

## 3. What to reach for, given a job

Section 2 compared the families against each other, and this section compares them
against jobs. The first question is not which model to use, because for a good number
of jobs the answer is no model at all.

![A four-question decision picture, each question leading down to a family and right to the next question, ending at a vision-language-action model](../../images/using-a-model-for-real/the-map-of-models/choosing-a-family.svg)

Four questions, asked in this order, pick the family, and the first of them sends three of the ten jobs below away from machine learning entirely.

Ask whether a person can write the rule down, because if they can then writing it is
cheaper, faster and inspectable. If they cannot, ask what shape the answer is, because
a name, a box, a mask or a depth reading is a job the seeing models already do and
their weights can be downloaded. If the job needs words, or an object nobody listed in
advance, ask for a vision-language model or the open-vocabulary detectors of
[open-vocabulary vision](../09_models-that-see/03_open-vocabulary-vision.md). Only when
the answer is a stream of movement does a policy become the right tool, and only when
the instruction varies freely does a
[vision-language-action model](../12_models-that-act/03_vision-language-action-models.md)
earn its cost.

![A horizontal log-scale bar chart of ten jobs, each with a red marker showing all the arithmetic its control rate allows, three of them green for written methods](../../images/using-a-model-for-real/the-map-of-models/cost-against-budget.svg)

A written force controller uses one part in 180,000,000 of what its 500 hertz loop allows, while a vision-language-action model at 10 hertz uses 38.1% of it.

The red marker on each row is everything the example machine can do inside one period
at that job's rate, and the bar is what the chosen method costs. The four written
methods are so far to the left of their markers that the comparison is hard to draw at
all, and the learned methods crowd up against theirs. The diffusion policy at 20 hertz
takes 24.6% of its budget and the vision-language-action model at 10 hertz takes 38.1%,
and neither leaves room for a second large model in the same loop.

![Left: a log-scale bar chart of training examples for six learned answers. Right: hours of a person driving the arm, from 1.1 hours for 200 demonstrations to 27.8 for 5,000](../../images/using-a-model-for-real/the-map-of-models/data-needed.svg)

Most of these have been trained already by somebody else, and the only one you usually pay for yourself is the demonstrations, at 1.1 hours for 200 of them and 27.8 hours for 5,000.

The table below puts all of it in one place. Read each row from left to right: the job,
what to reach for, what that costs in data, what it costs in arithmetic for one
decision, and the page of this book that explains it.

| The job | Reach for | Data it needs | Arithmetic for one decision | Page to re-read |
| --- | --- | --- | --- | --- |
| Find a bright part on a plain belt | A written colour threshold | none | 921,600 operations | [thresholds and colour masks](../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md) |
| Hold 5 newtons against a surface | A written force controller | none | 40 operations | [proportional-integral-derivative (PID) control](../../06_programming-techniques/07_control-and-motion/02_most-used/01_pid-control.md) |
| Move from A to B without hitting anything | A written planner | none | about 2 million operations | [sampling-based planning](../../06_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md) |
| Stop the arm when something is wrong | Written limits and a watchdog | none | 12 operations | [running and evaluating a model](01_running-and-evaluating-a-model.md) |
| Name which of twenty known parts is in the bin | A picture classifier | about 20,000 labelled pictures, or a fine-tune of a few hundred | 4.6 thousand million | [what a network can learn](../02_inside-a-network/04_what-a-network-can-learn.md) |
| Find an object nobody labelled | An open-vocabulary detector | already trained; you write a text prompt | 39.1 thousand million | [open-vocabulary vision](../09_models-that-see/03_open-vocabulary-vision.md) |
| Measure how far away each pixel is | A depth model | already trained | 46.7 thousand million | [depth and 3D](../09_models-that-see/04_depth-and-3d.md) |
| Pick a cloth out of a pile | A diffusion policy | 200 to 2,000 demonstrations you record | 44.2 thousand million | [diffusion and flow policies](../12_models-that-act/02_diffusion-and-flow-policies.md) |
| Follow a spoken instruction on a new table | A vision-language-action model | demonstrations on top of web pretraining | 137.1 thousand million | [vision-language-action models](../12_models-that-act/03_vision-language-action-models.md) |
| Work out the order of the steps | A language model, once a task | already trained | 785.6 thousand million for 300 words | [large language models](../10_language-and-multimodal-models/01_large-language-models.md) |

Two things in that table are worth saying out loud. Six of the ten learned answers need
no training data from you at all, because somebody else trained them and you download
the weights or write a prompt, which is what
[fine-tuning and adapters](../07_pretraining-and-adapting/03_fine-tuning-and-adapters.md)
and the pretraining chapter made possible. And the four written answers cost so little
arithmetic that they can run inside every control cycle, which the learned ones cannot.

---

## 4. When the answer is not a neural network

Section 3's table had four rows with no model in them, and this section says why,
because a book about neural networks should be clear about where they are the wrong
tool. The clearest case is when you have very little data. The script trains the colour
classifier from the page before on a growing number of examples and compares it with a
rule a person wrote, which is to pick whichever nominal colour is nearest.

![A log-scale curve of the learned classifier's accuracy rising from 33% at 2 examples to 95.6% at 2,048, crossing a flat green line at 85.4% near 16 examples](../../images/using-a-model-for-real/the-map-of-models/rule-vs-learned.svg)

The written rule scores 85.4% with no training data at all, and the learned classifier needs about 16 examples before it draws level and 64 before it reaches 94.0%.

Below sixteen examples the learned method is not merely worse, it is unstable, because
its accuracy over nine runs spreads by 11.0 points at eight examples and still by 4.8
points at sixteen, depending on which examples it happened to get. The written rule has
no such spread, because it has nothing to fit. This is the real shape of the trade:
learning buys accuracy with data, and if you have no data it buys nothing.

![Two log-scale bars: 150,564 operations for the written rule against 4,573,642,752 for the classifier, and 0.04 microseconds against 1.27 milliseconds with a dashed 2 ms line](../../images/using-a-model-for-real/the-map-of-models/cost-comparison.svg)

The classifier does 30,377 times the arithmetic of the written rule, which on the example machine is 1.27 milliseconds against 0.04 microseconds.

The second case is speed. A 500 hertz force loop has 2 milliseconds for everything, and
the classifier alone would take most of that, so no network goes inside a loop that
fast. This is why the layer that keeps the arm safe is written rather than learned, and
why [calibration](../../06_programming-techniques/02_geometry-and-cameras/02_most-used/03_calibration.md)
and [inverse kinematics](../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md)
stay written even on robots whose perception is entirely learned.

![A grouped bar chart of the written rule and the learned classifier under four conditions, 85 against 96 as expected, 60 against 88 brighter, 74 against 77 on a warmer tablecloth and 71 against 72 with a noisier camera](../../images/using-a-model-for-real/the-map-of-models/where-each-breaks.svg)

Neither method survives a change it was not built for: brighter light takes the written rule from 85.4% to 60.5% and the learned one from 95.5% to 87.8%, and a warmer tablecloth takes them to 73.9% and 76.6%.

The third case is honesty about failure, and this picture is the one that should stop
anybody from thinking the choice is between a fragile rule and a robust network. Both
fall over, in different places, and neither says so. A written rule fails in a way you
can read and repair, because you can see the threshold that was crossed. A network
fails in a way you can only measure, by running the trials of the page before. That
difference, rather than accuracy, is usually what should decide. The
[map of techniques](../../06_programming-techniques/01_what-techniques-are/04_the-map-of-techniques.md)
lists the written methods in full, and
[classical machine learning](../../07_learned-models/02_classical-machine-learning/01_overview.md)
covers the fitted methods that are not neural networks and often win on a few hundred
examples.

---

## 5. What is not solved

Section 4 said where a neural network is the wrong tool, and this section says where it
is the right tool and still does not work. None of what follows is a reason not to use
these models, and all of it is a reason to be careful about what you promise.

The first unsolved thing is the cost of robot data. Pictures and text come by the
billion from the internet, and demonstrations of an arm come one at a time from a
person driving it, which is why
[scale, data and compute](../07_pretraining-and-adapting/02_scale-data-and-compute.md)
calls robot data the scarce ingredient.

![A log-scale curve of success rate against hours of demonstration, reaching 80% at 99 hours, 90% at 559, 95% at 3,162 and 99% at 176,777](../../images/using-a-model-for-real/the-map-of-models/data-cost-curve.svg)

On this example curve, which is an illustration rather than a measurement, 80% costs 99 hours of demonstration, 95% costs 3,162 hours, and 99% costs 176,777 hours.

The shape matters more than the numbers. Every curve of this kind that anybody has
measured bends over, so each step up costs several times the last one, and at 20
seconds a demonstration those 3,162 hours are 569,210 demonstrations and about two
years of one person working six hours a day. Simulation, shared datasets across many
robot types and generated data all push the curve down, and none of them has flattened
it.

The second unsolved thing is reliability, and it is the one that keeps learned policies
out of unattended production.

![Left: four curves of whole-task success against the number of steps, for per-step rates of 95%, 98%, 99% and 99.9%. Right: a log-scale bar chart of hours between call-outs, 7 minutes at 90% up to 11.1 hours at 99.9%](../../images/using-a-model-for-real/the-map-of-models/reliability-compounding.svg)

A policy that gets 99% of its steps right finishes a 20-step task 81.8% of the time, and a cell that must run one unattended eight-hour shift needs a whole-task success of 99.86%.

Read the left panel as a warning about per-step numbers. Steps multiply, so 99% a step
is 81.8% over twenty steps and 95% a step is 35.8%. The right panel turns whole-task
rates into the number a factory actually cares about, which is how long before somebody
has to walk over: at one task every 40 seconds, a 95% policy calls for help every 13
minutes and a 99.9% policy every 11.1 hours. Today's best arm policies on varied
everyday tasks are far below that, which is why they appear in demonstrations and in
cells with a person nearby rather than in lights-out factories.

The third unsolved thing is that nothing in training says anything about inputs the
training did not cover.

![A curve of measured success against distance from the nearest training example, falling from 94% within 1 cm to 6% beyond 8 cm, with 95% intervals](../../images/using-a-model-for-real/the-map-of-models/outside-the-training-set.svg)

In this simulation the policy scores 94% within 1 cm of a training example, 61% at 3 to 4 cm and 6% beyond 8 cm, and nothing in the training predicted any of that.

A written method has a domain you can state: a colour threshold works while the colour
is in range, and you can say what that range is. A network has no such statement. It
will answer any input, confidently, and the only way to find out whether that answer is
any good is to measure it, which brings us to the fourth unsolved thing.

![A log-scale curve of trials needed on each policy against the improvement being proved, from 6,039 each for 2 points to 199 each for 10 points](../../images/using-a-model-for-real/the-map-of-models/evaluation-cost.svg)

Proving that a policy has gone from 80% to 85% needs 906 trials of each version, which is 1,812 trials and 45.3 hours of arm time at 90 seconds a trial.

Evaluation is expensive in exactly the place it is needed most, because the
improvements people make are usually a few points and a few points is what costs
thousands of trials. Worse, those trials are run on one lab's arm, objects and lighting,
so two labs' numbers cannot be compared, which
[simulation and evaluation](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md)
covers in detail.

The fifth unsolved thing has no picture because it is not a number. A model that can
describe a task correctly in words is not thereby able to do it. A vision-language model
can look at a cluttered table and say, correctly, that the fork should be picked up by
its handle and laid to the left of the plate, and the same system can then fail to close
its fingers on the handle at all. Describing and doing are different problems, the
second has far less data behind it, and joining them is what the whole
vision-language-action line of work is about.

---

## 6. What this book left out, and which book holds it

Section 5 was the honest list of what the field cannot do, and this section is the
honest list of what this book did not cover. The book explains the machinery of neural
networks, and a working robot arm needs a great deal besides.

![Eight book boxes on a shelf, with chapter counts from 2 to 13, and this book highlighted in red in the middle](../../images/using-a-model-for-real/the-map-of-models/library-shelf.svg)

The library is eight books and 50 chapters, and this one is the thirteen chapters in the middle that explain how the machinery works.

Its two neighbours matter most. On one side, Programming Techniques holds the methods
nobody had to train, which section 4 said are the right answer more often than people
expect. On the other, Learned Models is the catalogue: for each family of model an arm
uses, it names the real models, what they cost, how they are licensed and where they
fail. This book explains how a diffusion policy works, and that book tells you which
ones exist.

![Eight rows pairing a topic this book leaves out with the book that covers it, from camera calibration to Perception through to one problem solved ten ways in Robotics by Example](../../images/using-a-model-for-real/the-map-of-models/handoff-map.svg)

Eight things this book deliberately does not cover, and the book that does.

Each row is a real gap. This book never says what a camera actually measures or how to
calibrate one, and [Perception](../../02_perception/01_camera/01_basics.md) does. It
never explains frames, transforms or
[inverse kinematics](../../01_robotics-intro/04_kinematics/02_inverse-kinematics.md),
without which a joint command means nothing. It says nothing about planning a path, PID control
or force control, which are in Programming Techniques. It says nothing about
simulators or how an arm is trained in one, which is in Frameworks and Manipulation,
and nothing about [ROS](../../04_ros-and-rviz/01_ros/01_ros-intro.md), which is how the
parts of a robot talk to each other.

![Six boxes in a row showing a suggested reading order after this book, starting at Neural Networks and ending at Robotics by Example, covering 43 chapters](../../images/using-a-model-for-real/the-map-of-models/reading-order.svg)

One suggested path onwards covers 43 chapters in six books, starting with the catalogue of real models and ending with one problem solved ten ways.

The order is a suggestion rather than a rule. Learned Models comes first because it is
the direct continuation of this book, and Programming Techniques second because section
4's argument only lands once you can see the written methods in full. Perception and
Frameworks fill in the camera and the simulator. Robotics by Example comes last because
it is the one book that takes a single real problem and solves it ten ways, three of
them written and seven of them with something trained inside, which is this book's
closing question asked once more with an answer attached.

---

## 7. Where to read next

This is the last page of the book, so these links point outwards rather than onwards.

- [The map of models](../../07_learned-models/01_what-models-are/06_the-map-of-models.md)
  in Learned Models is the catalogue's own map, and it sorts the real models an arm uses
  into seven kinds, which is the next thing to read after this page.
- [Making models work on an arm](../../07_learned-models/10_making-models-work-on-an-arm/01_overview.md)
  is that book's chapter on fine-tuning, running, testing and trusting a model, with
  named tools.
- [The map of techniques](../../06_programming-techniques/01_what-techniques-are/04_the-map-of-techniques.md)
  lists every written method a robot arm uses, which is section 4's half of the answer.
- [Cameras](../../02_perception/01_camera/01_basics.md) explains what a camera measures,
  which this book assumed throughout and never said.
- [Simulation and evaluation](../../03_frameworks/08_frontier/04_simulation-and-evaluation.md)
  covers the benchmark problem of section 5 as the research field sees it.
- [Many glasses of one kind](../../08_robotics-by-example/02_many-glasses-of-one-kind/01_overview.md)
  takes one problem and solves it ten ways, written and learned side by side.

---

## 8. Using it in Python

The whole page comes down to two sums you can do before writing any code: does the
model fit in the time you have, and how good does it have to be. This is both of them,
in plain Python, with the numbers section 3 and section 5 printed.

```python
# Section 3. The example machine at two bytes a number, and what one period allows.
machine = 3.6e12                       # multiply-adds a second
hertz = 20
budget = machine / hertz               # 180,000,000,000 per decision

families = {                           # section 2's stated example configurations
    "picture classifier":          4_573_642_752,
    "behaviour-cloning policy":   15_422_650_368,
    "diffusion policy, 10 steps": 44_243_202_048,
    "promptable segmenter":      659_545_915_392,
}
for name, work in families.items():
    share = 100 * work / budget
    print(f"{name:28s} {share:7.1f}% of a {hertz} Hz budget "
          f"{'fits' if share < 100 else 'does not fit'}")
# picture classifier               2.5% of a 20 Hz budget fits
# behaviour-cloning policy         8.6% of a 20 Hz budget fits
# diffusion policy, 10 steps      24.6% of a 20 Hz budget fits
# promptable segmenter           366.4% of a 20 Hz budget does not fit

# Section 5. Steps multiply, so a good step rate is not a good task rate.
for step_rate in (0.95, 0.98, 0.99, 0.999):
    print(f"{100 * step_rate:5.1f}% a step -> {100 * step_rate ** 20:5.1f}% over 20 steps")
# 95.0% a step ->  35.8% over 20 steps
# 98.0% a step ->  66.8% over 20 steps
# 99.0% a step ->  81.8% over 20 steps
# 99.9% a step ->  98.0% over 20 steps

# Section 5. One task every 40 seconds: how long before somebody is called over.
tasks_per_hour = 3600 / 40
for task_rate in (0.90, 0.95, 0.99, 0.999):
    gap = 1 / ((1 - task_rate) * tasks_per_hour)
    print(f"{100 * task_rate:5.1f}% a task -> a call-out every {gap:5.2f} hours")
# 90.0% a task -> a call-out every  0.11 hours
# 99.9% a task -> a call-out every 11.11 hours
```

Those printed numbers are the same ones the pictures in sections 3 and 5 draw. The
budget line is the single most useful thing in this file, because it is quick, it needs
no model and no robot, and it rules out a great many plans before anybody downloads
anything. The compounding line is the second, because it turns the per-step number that
papers report into the whole-task number a user cares about.

What the libraries give you after that is almost everything else. Hugging Face's
`transformers` and `timm` hold pretrained weights for most of the seeing and language
families in section 2, `lerobot` holds policies and the recording tools for the
demonstrations section 3 priced, and PyTorch holds the layers and the training loop the
first half of this book explained.

What you still have to decide is the part no library has a view on. You decide whether
the job needs a model at all, which section 4 says is the question people skip. You
decide which family the shape of your answer calls for, and whether its arithmetic fits
your control rate. You decide how many demonstrations you are willing to record, knowing
from section 5 what the next ten points of success rate will cost. And you decide what
you are prepared to promise, which should be no more than your trials can support.
