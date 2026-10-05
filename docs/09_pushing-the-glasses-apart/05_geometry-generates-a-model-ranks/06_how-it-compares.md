# How it compares

This page is the judgement on this solution. It says where the solution is
strong and where it breaks, names the general ideas behind it, and places it
beside the other five.

## Contents

1. [Where it is strong and where it breaks](#1-where-it-is-strong-and-where-it-breaks)
2. [The general ideas behind this](#2-the-general-ideas-behind-this)
3. [Where it sits among the other five](#3-where-it-sits-among-the-other-five)

## 1. Where it is strong and where it breaks

The strengths are real, and they are the reason to understand this arrangement
even after deciding not to spend much on it here.

**The learned part cannot cause the failure that cannot be undone.** Toppling,
leaving the glass zone, leaving the arm's reach and striking the rack are all
settled before the model is consulted. In a cell whose one unrecoverable
failure is a toppled glass, that is the property worth designing around, and
the zero topples in the record of the geometry this solution extends is what it
looks like when it holds.

**It degrades to something that works.** Delete the model and the printed rule
runs the table. There is no state in which this solution is broken rather than
merely unimproved.

**It is checkable.** Every candidate can be printed with its score, every
refusal remains the geometry's and prints with a reason, and the model reports
which of its inputs mattered. When this solution is wrong, a person can find
out why by reading a list.

**It is cheap in every currency.** No accelerator, no licence condition, no
human labelling, minutes of examiner time, and a run-time cost that is arithmetic.

**And it is the teacher**, which is the contribution that survives even if its
own score is unremarkable.

Against that, three kinds of weakness.

**What the measurement said, and it is the finding of this solution.** The
job-finishing candidates are tied by construction, as the section on the
enumerator shows, so the ordering carries no information in exactly the part of
the candidate set where the task is actually being finished. That prediction
was then checked rather than left as an argument. `spread.py` made 4,511 real
pushes over 60 training tables and wrote `spread.json`: within one glass's
job-finishing candidates the room gained ranges **0.0 mm at the median** over
161 groups, which is an exact tie, while the pushes that only ease the crowding
range 11.9 mm. For one glass the printed rule already matches the best
candidate in **159 of 206 groups**, and the best possible choice beats it by
0.0 mm at the median.

**So the ranker was fitted, and it lost to the rule it was meant to improve.**
Both ran the same loop over the same fifty held-out tables with the same budget
and the same candidate set, the only difference being who picks: the ranker
racked **185 of 251 glasses in 229 pushes** and finished 31 tables, where the
printed rule racked **195 in 213 pushes** and finished 33. Neither toppled
anything. The gap is not an unlucky fit — three rankers fitted on resamples of
the same rows racked 180, 181 and 184 — and the reason is the label rather than
the trees. The model is fitted on **room gained** and the run is marked on
**glasses that end up grippable**, and a push that spreads room over three
glasses scores higher than one that finishes a glass outright. On the
validation tables in `training.json` the ranker's top pick takes a
job-finishing push in **47 of the 83 decisions that offer one**, where the rule
takes it every time; by its own label the ranker is the better chooser, giving
up 4.4 mm of room against the best candidate where the rule gives up 18.7 mm,
and it still clears fewer tables. What the fit says mattered points the same
way: the topple ratio (0.43) and the foot width (0.38) came first and the push
distance last (0.01), so the model mostly learned which glass is risky to push
rather than which push is good. **The verdict is to keep the simpler one.**

**What the design cannot do.** It cannot invent a candidate, so its quality is
the enumerator's quality rather than the model's. It cannot express a push that
is not a straight drag along one heading. It does not transfer across a change
in the number of glasses, because a model fitted on tables of five has never
seen the crowding that eight produce, and nothing errors when it is asked
anyway. And it says nothing at all about the commonest refusal in the record,
which is a glass with nowhere clear to go.

**What it cannot survive.** A log collected while the model is driving holds
outcomes only for the candidates the model already prefers, so retraining on it
without occasionally taking the second-ranked candidate locks in an early
mistake.
Change the sweep or change the way tables are drawn, and the fitted model is
out of date silently. And every label in the training set was decided by the
examiner's private friction, which was never measured against anything real.

**How it fails, when it fails, is quietly.** A badly fitted ranker orders the
candidates roughly at random. Nothing errors, nothing topples, and the run
simply spends more pushes and leaves more glasses behind than it needed to.
That is exactly how it failed here, and the only reason it was caught is that
the test was run: count pushes and glasses racked against the printed rule on
the held-out tables, with the model deleted and everything else held the same.

## 2. The general ideas behind this

Nothing in this solution was invented for glassware. Four ideas in it are worth
knowing separately from this cell, each with an honest note on where it is
normally right and where it is not.

### Generate, veto, then rank

Arithmetic writes down the candidates and holds an absolute veto, and the
fitted part is only allowed to reorder what survives. **Position in the
sequence is what limits the damage a wrong prediction can do**, and it limits
it by construction rather than by the model being accurate.

It is the standard answer wherever a fitted component is wanted in a system
that can cause physical harm, and it appears in motion planning, grasp
selection and flight control in the same form. It is the wrong shape when the
set of possible actions is too large or too awkward to write down, which is
exactly when a policy earns its place, and it is the wrong shape when the
enumerator can already tell which survivor is best — because then the model is
being asked a question that has already been answered. This cell is close to the
second of those two cases, which is the measured verdict this document keeps
returning to.

### Learning to rank

Nothing downstream uses the number the model predicts. Only the order matters.
That is called [learning to
rank](https://en.wikipedia.org/wiki/Learning_to_rank), and it is an easier
problem than predicting the number, because a model that is wrong by the same
amount everywhere still ranks perfectly.

There are three ways to fit it, and they are worth distinguishing because this
solution chooses the first. **Pointwise** fitting, which is what is used here,
shows the model one candidate at a time and asks it for that candidate's score
on its own. **Pairwise** fitting shows it two candidates from the same group and
asks which is better, so the thing being fitted is a comparison rather than a
value. **Listwise** fitting shows it the whole group and scores the order it
produces. Pairwise and listwise match the real objective more closely, because
the real objective is an order and not a set of values, and they are the usual
choice where the groups are large and the differences within them are subtle.
Pointwise is chosen here because it is the simplest thing that can work, because
the label it needs is exactly the label the examiner produces anyway, and because
nothing in the measured shape of these candidate sets suggests the extra
machinery would be repaid. If the within-group spread of the label turned out to
be large, pairwise fitting would be the next thing to try.

Learning to rank is used for search, recommendation and advertisement placement,
and in the same form for ordering candidate grasps, viewpoints and motions. It
is rarely right where the size of the number is used rather than the order, such
as deciding whether to act at all: **ranking tells you which candidate is best,
and never whether the best one is any good.** And it needs one condition this
cell largely fails, which is the lesson of this whole document: the candidates
within a group have to differ in the thing being ranked. When a group is a tie
the training signal is empty, and the fitted model's measured accuracy will look
perfect while telling you nothing. **Check the within-group spread of the label
before building the model.**

### Gradient boosting on tabular inputs

Fit a weak predictor, fit the next one to what the sum of the previous ones got
wrong, add them up, and repeat. With shallow decision trees as the weak
predictors this is **gradient boosting**, and it remains the first thing to
try when the input is a short table of quantities of different kinds rather
than a picture, a sound or a sentence. It needs no rescaling of the
inputs, it expresses a threshold in one question, it trains in seconds on a
processor, and it reports which inputs mattered.

It is normally right on tabular data of up to a few hundred thousand rows, which
covers the great majority of cases where somebody wants a number predicted from
a handful of measurements. It is normally wrong when the input has structure a
tree cannot see: neighbouring pixels of a picture, successive samples of a
sound, words in order. A tree asks about one input at a time, so it cannot
express "this region is crowded" over a grid without a great many questions,
which is precisely why the alternative input discussed above — an occupancy grid
of the zone — would mean changing the model as well.

### Learning a utility rather than a perception

The model here does not say what is on the table. It says how much a given
action would help. That is **utility** or **value** estimation, and what makes
it workable is that the answer is cheap to check: take the action in the
simulator and see what happened. The move has a well known ancestor in
grasping, where nobody could write down a rule saying whether a gripper pose
would hold an object, so attempts were collected and a function was fitted from
the pose to whether it worked — Pinto and Gupta's [*Supersizing
Self-supervision*](https://arxiv.org/abs/1509.06825) (ICRA 2016) is the clearest
example, with a robot making tens of thousands of attempts and labelling each by
whether the object came up. Applied to pushing rather than grasping, the same
move produced Agrawal and colleagues' [*Learning to Poke by
Poking*](https://arxiv.org/abs/1606.07419) (2016), which fits a model relating a
poke to the displacement it caused, and Zeng and colleagues' [*Learning
Synergies Between Pushing and Grasping*](https://arxiv.org/abs/1803.09956)
(2018), which learns where to push and where to grasp in a cluttered bin with
pushes scored by whether they make a later grasp possible.

It is worth noticing that this is not reinforcement learning, and the
distinction is why the pattern is cheap. There is no episode and no reward, only
an input, an attempt and a recorded outcome. The world produces the label.

Utility estimation is used for choosing among actions wherever the outcome can
be simulated or replayed, such as view planning, grasp ranking and move
ordering in games. It is rarely right where the outcome cannot be judged without
doing it for real, because then there is no free set of labels and the problem
becomes reinforcement learning with all of its cost in attempts. And it is
pointless where the utility is a closed-form function of quantities the planner
already holds — which is this cell's case, and the reason the two papers on
pushing above are worth reading against this document rather than as support
for it. Both are set in cluttered bins where the geometry genuinely cannot
write down the good actions: objects overlap, shapes are unknown, and one push
rearranges several things at once. A table with a few upright glasses on it,
each a circle of measured width, is not that case.

The mechanics underneath all of this is older and is not a rule of thumb.
Matthew Mason's *Mechanics and Planning of Manipulator Pushing Operations*
(International Journal of Robotics Research, 1986) is where planar pushing
became a subject with results in it, including which way an object turns when it
is pushed, and Kevin Lynch and Mason's *Stable Pushing: Mechanics,
Controllability, and Planning* (same journal, 1996) works out when a push keeps
an object under control rather than letting it slip away. The lesson those
papers carry into this document is the one the arrangement above keeps
confirming: where the mechanics has an answer, arithmetic gets it, and the
uncertainty that is left sits in the numbers the mechanics needs and nobody
measured — the friction, and the way the weight is distributed under the foot.

## 3. Where it sits among the other five

[The six solutions](../03_the-six-solutions/01_how-the-six-compare.md) form a ladder ordered by how much of each one
was fitted in this cell, and this one stands on the lowest rung that has
anything fitted at all.

Against [solution 1](../04_one-fixed-nudge/01_what-it-is.md), the comparison is whether choosing
is worth anything. Solution 1 pushes a glass a fixed fraction of the room it is
short of, straight away from the neighbour whose edge reaches furthest into that
room, and looks again, with no enumeration and nothing fitted. This solution
writes down every safe push and chooses among them. So the gap between the two
measures the value of the whole geometric apparatus, and the gap between this
solution's printed rule and this solution's model measures the value of the
ordering alone. Those are two separate questions and it is worth keeping them
apart.

Against [solution 3](../06_imitation-from-demonstrations/01_what-it-is.md), the comparison is
imitation against enumeration, and the two are connected rather than merely
opposed. Solution 3 fits a policy that emits the push directly, so it can
express motions this solution's candidate set cannot, and it pays for that by
having no structural guarantee of safety: a policy's output space is every push
there is. It also needs demonstrations, and this solution is where they come
from. So the pair measures something quite specific, which is whether a policy
fitted on this teacher's behaviour exceeds the teacher — and the section above
on inheriting a ceiling says why that is a harder thing to achieve than it
sounds.

Against [solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md), the comparison is
which question deserved a model, and it is the sharpest comparison among the
six. Both fit something, and the difference is what. This solution fits a model
of **how much a push would help**, which is a quantity the geometry already
computes exactly from the destination. Solution 4 fits a model of **what a push
will actually do**, which is the quantity the geometry gets wrong, because
predicting where a pushed glass ends up needs the friction and the weight
distribution that nobody here has. Both have now been run on the same tables,
and the result bears on that choice directly. Solution 4's first rung racked
202 of the 251 glasses in 114 pushes, repeating only 14 of them, where the
geometry racked 195 in 213 pushes and had to repeat 90. **The learning that
paid in this cell attacked the quantity the geometry gets wrong, not the
quantity it gets right.** That is the single most useful thing to take from
placing these two side by side.

It cost something, though, and the cost is the point of the comparison rather
than a footnote to it. The geometry toppled nothing at all, while the learned
approach toppled one glass and lost one table to it. That is what it means to
replace a rule that refuses whenever the arithmetic is unsure with a model that
predicts an outcome: the model is right more often and it is also occasionally
confidently wrong, and a toppled glass is the one failure this cell cannot take
back. So the two are not ordered on one number. The learned approach finishes
more glasses in half the attempts, and the geometry is the one that never
breaks anything.

Against [solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) and [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md), the comparison is scale and origin. Those two are
the same large vision-language-action model, one used exactly as it downloads
and one with its training continued here, and the only difference between them
is that training. Both read a picture rather than a list of measurements and
both emit waypoints rather than push parameters, and the one of them whose
training was continued here was expected to need a rented accelerator, though
in the event it trained on the same laptop as everything else. This solution
is the other end of the ladder in every one of those respects: a few
hundred shallow trees over eight numbers, trained on a processor, with the
safety held by arithmetic that was written rather than fitted. If a scorecard
ever shows this solution close to those two, the interesting reading is not that
the trees are clever. It is that the geometry was doing most of the work all
along.

← [What it needs](05_what-it-needs.md) · [Imitation from demonstrations — what it is](../06_imitation-from-demonstrations/01_what-it-is.md) →
