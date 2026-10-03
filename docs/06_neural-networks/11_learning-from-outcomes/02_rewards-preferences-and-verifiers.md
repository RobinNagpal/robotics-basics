# Rewards, preferences and verifiers

The page before this one, [reinforcement learning](01_reinforcement-learning.md),
showed a policy learned from nothing but a number that arrived after each
action. It took that number for granted. Every picture on it assumed somebody
had already decided that putting the block in the bin was worth 10, that a move
cost 0.10, and that dropping the block in the wrong place cost 1. This page is
about where those numbers come from, which turns out to be the hardest part of
the whole method and the part that goes wrong most often.

The difficulty is easy to state. A reward has to say what you want, and it has
to say it in a way that a learner can push on from the very first attempt. Those
two demands pull against each other. A reward that says exactly what you want,
such as one point when the block is in the bin and nothing otherwise, says
nothing at all until the first success happens by accident. A reward that says
something after every action, such as how close the gripper is to the block,
gives the learner something to push on immediately, but it is no longer a
statement of what you want, and the learner will do what it actually says.

So this page works through the ways of getting a reward, in the order people
usually try them: writing one by hand, shaping it, learning one from examples of
success and failure, learning one from a person's choices between two attempts,
and checking the outcome with a short program. For each one it says what it is,
what it buys you, why you would reach for it rather than the obvious
alternative, and what it costs. Then it covers the failure that all of them
share, which is called reward hacking, and what is actually done about it.

It assumes you have read the page before, so that state, action, reward, return,
policy, episode and discount factor are familiar. The world in every picture is
the same made-up table top, and the script
`docs/diagrams/learning_from_outcomes.py` works out every number. The learning
is real: tabular Q-learning, exact value iteration, a logistic reward model
fitted by gradient descent, and a reward fitted to simulated choices between
pairs of attempts, all in NumPy.

## Contents

1. [A reward written by hand, and how it fails](#1-a-reward-written-by-hand-and-how-it-fails)
2. [Sparse rewards, dense rewards and shaping](#2-sparse-rewards-dense-rewards-and-shaping)
3. [A reward model learned from success and failure](#3-a-reward-model-learned-from-success-and-failure)
4. [Asking a person which of two attempts was better](#4-asking-a-person-which-of-two-attempts-was-better)
5. [Verifiers: a program that checks the outcome](#5-verifiers-a-program-that-checks-the-outcome)
6. [Reward hacking, and what is done about it](#6-reward-hacking-and-what-is-done-about-it)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. A reward written by hand, and how it fails

The first thing anybody does, having read the page before this one, is sit down
and write a reward. On this world the obvious one is to pay the arm for being
near the block, because the arm has to get to the block before it can do
anything, and because a number that changes every step gives the learner
something to work with straight away. So the reward is 1.00 at the block's
square and 0.30 less for every square between the gripper and the block, with
the 10 for a block landing in the bin still on top of it.

![A five by five grid with a reward number in every square, highest at the block and falling away, beside a line showing the reward falling by 0.30 a square](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-written-reward.svg)

The reward is 1.00 on the block's own square, 0.70 one square away and minus 0.50 in the far corners, and the bin's square pays minus 0.50 because it is five squares from the block.

Nothing about that is unreasonable, and it is close to what real reward
functions for arms actually look like. Working out exactly what it asks for is
another matter, and the answer is not what the person who wrote it wanted.

![Three panels: the route the best policy takes, and the best action in every square with an empty gripper and while holding the block, nearly all of them pointing towards the block](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-hovering-policy.svg)

The best policy under this reward walks to the block in three moves and then waits beside it for the remaining 77 actions, collecting 78.20 and never once closing the gripper.

The arithmetic is simple once you see it. Standing beside the block pays 1.00
every step for as long as the attempt lasts, which over 77 remaining steps comes
to 77. Carrying the block to the bin pays 10 once and ends the attempt, which
stops the payments. So the written reward, read exactly, says that hovering by
the object is worth about eight times as much as doing the job, and a learner
that maximises it is behaving correctly.

![A chart with two lines over 4,000 attempts, one showing the written reward rising from 22.56 to 77.20 and one showing the share of attempts reaching the bin staying flat at zero](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/reward-up-task-flat.svg)

Over four runs of 4,000 attempts the written reward it collects rises from 22.56 to 77.20, while the share of attempts that put the block in the bin stays at 0.001.

That pair of lines is the thing to remember from this section, because it is
what a reward failure looks like from the outside. The training curve climbs
beautifully, the loss falls, every chart on the dashboard is green, and the
robot never once does the job. Nothing in the numbers the learner sees is wrong,
and the only way to notice is to measure the job separately.

![Two bar charts comparing three behaviours, one scored by the written reward where waiting wins with 78.2, and one scored by whether the block reached the bin where only one of them succeeds](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/three-behaviours-scored.svg)

Waiting by the block scores 78.2 on the written reward and never finishes the job, while the policy that puts the block in the bin scores 13.6 and finishes every time.

---

## 2. Sparse rewards, dense rewards and shaping

Section 1 failed because the written reward paid for something other than the
job, so the obvious repair is to pay only for the job, and this section is about
what that costs and what the middle ground looks like.

A **sparse reward** pays nothing until the job is done and then pays once. It is
exactly right, because the only thing it rewards is the thing you want. A
**dense reward** pays something after every action. It is easier to learn from,
because the learner gets a signal before its first success, and it is harder to
get right, because every one of those payments is a claim about what is good.

![Two bar charts of the ten rewards of the same attempt, one sparse with nine small costs and a single 9.85, and one dense where every step pays something](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/sparse-against-dense.svg)

The same ten actions collect 8.90 under the sparse reward, with everything arriving at the last step, and 2.60 under a dense reward that charges 0.30 for every square between the gripper and whatever it is meant to reach next.

Changing a reward to make it easier to learn from is called **reward shaping**,
and the important thing about it is that a shaping term is not a hint. It is
part of the reward, so it changes which behaviour scores highest, and the
learner optimises the reward it is given rather than the one you meant.

![A line chart of the share of attempts reaching the bin over 6,000 attempts for three rewards, where the potential-based one rises almost immediately and the other two take a few hundred attempts](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/how-fast-each-one-learns.svg)

Averaged over four runs each, the potential-based reward passes half of attempts reaching the bin at attempt 6, the sparse reward at attempt 171, and the plain dense reward at attempt 262.

That picture carries a warning. The plain dense reward is not faster than the
sparse one here, and is slightly slower, because making every step pay does not
by itself point the learner anywhere useful. What is dramatically faster is the
third line, and the difference between the two dense rewards is how they were
built, which the rest of this section explains.

![Three panels: the route the best policy takes under a holding bonus, the best action while holding the block, and a chart comparing 0.50 a step for ever against 10 once](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/shaping-that-changes-the-answer.svg)

Adding 1.00 a step for having the block in the gripper makes carrying it about for ever worth 67.95 against 14.90 for putting it in the bin, so the best policy picks the block up and never puts it down, and the learner trained on it reaches the bin on none of its attempts.

That is shaping changing the answer rather than the speed, and it is the normal
case rather than a trick. There is, though, one way of writing a shaping term
that provably cannot do this. Attach a number to every state, and make the
shaping payment the difference between the number at the state you arrive in and
the number at the state you left. Along any route the differences cancel out
except at the two ends, so no loop can be made profitable and the ranking of
whole behaviours is unchanged.

![Two grids showing the number attached to each square, rising towards the block with an empty gripper and towards the bin while holding, beside a bar chart of how many states keep the same best action](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/shaping-that-keeps-the-answer.svg)

The potential-based reward leaves the best action unchanged in all 50 states, while the plain dense reward changes it in one of them.

So shaping of that one shape is free, in the sense that it can only change how
fast the answer is found and never which answer it is. It is still not free in
effort, because somebody has to invent the number attached to each state, and
that is nearly as hard as writing the reward. Everything that follows is about
not having to.

---

## 3. A reward model learned from success and failure

Sections 1 and 2 both ended at the same place, which is that writing the reward
by hand is the problem. So the next idea is to stop writing it and to learn it,
in exactly the way everything else in this book is learned, from examples.

A **reward model** is an ordinary trained model whose input is a state, or a
whole attempt, and whose output is a number saying how good it is. The training
examples are attempts somebody has labelled, and the simplest labelling is to
mark every state in a successful attempt as good and every state in a failed one
as bad. The model here is a logistic fit over six measurements of the state,
small enough to print, and the examples are 400 attempts made by policies of
several standards.

![Two grids showing how many times each square was visited during attempts that worked and during attempts that failed](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-examples-it-learns-from.svg)

Of 400 example attempts, 293 ended with the block in the bin, giving 6,354 states from attempts that worked and 8,560 from attempts that failed.

![Two grids of the model's score for every square, with and without the block held, beside a bar chart of the six fitted weights](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/what-the-reward-model-scores.svg)

The biggest weight by far is 1.70 for holding the block, and the score is 0.71 on the bin's square while holding it, 0.31 on the same square with an empty gripper, and 0.29 at the start.

What it buys you is a number for every state, learned rather than invented, and
one that nobody had to make consistent by hand. Why reach for this rather than
writing a dense reward yourself? Because labelling an attempt as a success or a
failure is something an operator can do by watching, in a second, without
knowing anything about the arm, while writing a dense reward needs somebody to
decide what every intermediate state is worth. Collecting a thousand labels is
easier than getting one formula right.

![A histogram of the model's score for states from successful and failed attempts, beside a line showing the score climbing along one good attempt](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/how-well-it-tells-them-apart.svg)

The model scores 0.56 on average for states from attempts that worked against 0.35 for states from attempts that failed, puts 0.77 of them on the right side of 0.5, and climbs from 0.29 to 0.77 along a good attempt.

What it costs is that the model is only right where it has seen examples, and a
policy trained against it will go looking for the places where it is wrong. That
is not a worry about the future but something that happens immediately, and the
next picture is what happened here.

![A chart of the model's score and the share of attempts really reaching the bin against the number of training attempts, with the score flat at 0.75 and the share flat at zero](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/training-against-the-model.svg)

A policy trained on this model's score alone reaches 0.753 on the score at every checkpoint from 250 attempts to 6,000, and puts the block in the bin on none of its attempts, because the highest-scoring thing it can do is pick the block up and hold it.

---

## 4. Asking a person which of two attempts was better

Section 3 asked a person for a label, meaning a judgement about one attempt
against an absolute standard, and this section asks for something easier, which
is a judgement about one attempt against another.

**Preference learning** means showing a person two attempts at the same job and
asking only which they prefer, then fitting a reward so that the preferred one
scores higher. People are far better at comparing two things than at scoring one
thing, because a score needs a scale and a comparison does not, and two people
scoring the same attempt will disagree about the number while usually agreeing
about the order.

![Two grids showing the paths of two attempts side by side, one reaching the bin and one wandering until the time runs out, with the fitted score of each](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/a-pair-to-judge.svg)

The person is shown one attempt worth 8.90 and one worth minus 14.80, says which they prefer, and the fitted model ends up scoring them minus 9.57 and minus 75.81, which puts them in the same order.

The fitting works by giving each attempt a score, which is the total of the
fitted per-state reward over the states it passed through, and then adjusting
the reward so that the preferred attempt's score comes out higher. Nobody writes
a number anywhere. The judge here is simulated: it picks the attempt with the
higher true return, but only most of the time, so that the effect of mistakes
can be measured.

![Two grids of the fitted per-state reward and a bar chart of the fitted weights, with the reward least negative near the bin](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/what-the-preferences-taught.svg)

From choices alone the fit gives minus 1.08 at the start, minus 1.00 on the block's square and minus 0.86 on the bin's square while holding, so the score rises along the route the job takes.

![A line chart of the share of held-out pairs ordered the same way as the truth, against the number of judged pairs on a log scale](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/how-many-pairs.svg)

Ten judged pairs already order 0.69 of held-out pairs correctly, a hundred manage 0.91, and after about 250 more pairs stop helping, because the limit is the shape of the model rather than the number of choices.

![The same curve drawn for three judges, one right 85% of the time, one 76%, one 67%](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/people-make-mistakes.svg)

A careless judge costs accuracy rather than ruining the fit, because the mistakes are spread evenly and more pairs average them out.

Why reach for preferences rather than the labels of section 3? Because the
question is easier to answer, so answers are cheaper and more consistent, and
because a preference carries information about degree that a yes or no does not:
two failures can still be ranked. What it costs is that the reward is only
defined up to an ordering, so it says which attempt is better and not by how
much, and the person is still in the loop, which means the whole method runs at
human speed.

---

## 5. Verifiers: a program that checks the outcome

Sections 3 and 4 both learned the reward, and a learned reward can be wrong.
This section is about the case where you do not have to learn it at all.

A **verifier** is a short program that looks at the finished attempt and decides
whether it met the goal. It is not a model, it has no weights, and it cannot be
argued with. Here it is three lines: the attempt passes when the record says the
block ended in the bin. In language work the same idea is a unit test that runs
the generated code, or a checker that works out whether an answer to a sum is
right, and training against rewards of that kind is a large part of why recent
reasoning models improved.

![Two charts along the steps of two attempts, showing the reward model's score changing every step while the verifier's answer stays at zero until the final step of the successful attempt](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-verifier-along-an-attempt.svg)

Along an attempt that works the reward model's score climbs from 0.29 to 0.77 while the verifier says nothing until the last step, and along an attempt that waits by the block the model settles at 0.39 and the verifier answers 0.

![A histogram of the reward model's score for attempts the verifier passed and failed, beside a bar chart counting the attempts the two measurements disagree about](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/where-they-disagree.svg)

Out of 400 attempts the verifier passes 300, and taking a middling passing attempt's score of 0.58 as a bar, no failing attempt scores above it while 147 passing attempts score below it.

What the verifier buys you is a reward that cannot be gamed, because there is
nothing in it to find a hole in: the only way to raise it is to do the job. Why
reach for it rather than a learned reward model? Because it is exactly right,
costs nothing to run, needs no labelled data, and never drifts. What it costs is
that it can only ask about things the record actually holds, and that it says
nothing until the very end.

![Two panels, one listing the four things the record of an attempt holds, and one listing five questions with whether a short program can decide each from them](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/what-a-program-can-check.svg)

A program can decide whether the block reached the bin, where the gripper finished and whether it was empty, because those are in the record, and it cannot decide whether the block was set down gently or finished the right way up, because nothing in the record measures force or turning.

![A line chart of the share of attempts reaching the bin, for a learner trained on the verifier alone and one trained on the dense written reward](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/learning-from-the-verifier-alone.svg)

The verifier alone gets there in the end, reaching the bin on 1.00 of the last 200 attempts, but it takes about twice as many attempts to pass half as the dense written reward does.

In practice the three sources are combined rather than chosen between. A
verifier settles whether the job was done, a learned reward model or a set of
preferences fills in the long stretch where the verifier is silent, and the
verifier is kept as the thing that is actually optimised at the end. The next
section is about why that combination is needed.

---

## 6. Reward hacking, and what is done about it

Every section above has shown the same failure in a different costume, and this
section names it and says what is done.

**Reward hacking** means finding a behaviour that scores highly on the reward
and does not do the job. It is not the learner cheating, because the learner has
no idea what the job is: the reward is the entire statement of what is wanted,
and the learner is doing exactly what it was asked. The clearest example in this
world comes from a reward that pays for putting the block down anywhere tidy
rather than only in the bin.

![Two panels: the gripper looping between the block and the tray, and a chart of the reward collected over the attempt rising to 222.10 against 8.90 for the policy that does the job](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-tray-loop.svg)

Paying for a block put down on the near tray, and letting the attempt carry on, makes the best policy a loop that puts the block there 78 times in one attempt for 222.10, while the policy that does the job scores 8.90.

![A bar chart of three written rewards, each showing the score of the policy that squeezes it against the score of the policy that does the job](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/high-score-failed-task.svg)

Under all three written rewards the squeezing policy scores far higher than the policy that does the job, 78.2 against 13.6, 68.0 against 14.9, and 222.1 against 8.9, and never once puts the block in the bin.

The same thing happens to a learned reward, and it happens faster, because a
learned reward has places where it is wrong and a search finds them. The way to
see it is to measure many policies twice, once by the reward they were trained
on and once by the job.

![A scatter plot of the learned reward model's score against the share of attempts really reaching the bin, for policies trained on four different rewards](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/the-two-scores-come-apart.svg)

Of 48 policies, the quarter with the highest learned-reward score put the block in the bin on none of their attempts, while the rest managed 0.67, because the highest-scoring behaviour the model knows about is holding the block.

Four things are done about this, and none of them is a cure. The first is to keep
a **hold-out check on the real goal**, measured separately from the reward and
never optimised, which is the only reason anybody notices the problem at all.
The second is to use more than one reward at once, so that a hole in one is
covered by another.

![A bar chart comparing the share of attempts reaching the bin for a learner trained on the learned reward alone and one trained on the learned reward with the verifier added](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/two-rewards-together.svg)

Adding the verifier's payment to the learned reward model's score turns a policy that never finishes the job into one that does.

The third is to have a person watch recordings of what the policy actually does,
because every failure on this page is obvious in two seconds of video and
invisible in the numbers. The fourth is to keep the policy close to one that is
already trusted, by charging it for every action that differs from what the
trusted policy would have done, which stops the search wandering into the part
of the reward where the model is least reliable.

![A line chart of the share of attempts reaching the bin and the learned-reward score against the strength of the charge for differing from a trusted policy](../../images/learning-from-outcomes/rewards-preferences-and-verifiers/staying-near-a-trusted-policy.svg)

With no charge the policy chases the learned reward and never reaches the bin, and once the charge is large enough it is pulled back onto the trusted policy and finishes the job every time.

The honest summary is that none of these finds the hole, and all of them only
catch it after it has been found by the learner. That is why every serious piece
of work in this area reports a measurement of the real job, taken on attempts
nobody trained on, and treats the reward number as a tool rather than a result.

---

## 7. Where to read next

- [Behaviour cloning and action chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md)
  is the next page, and it shows the approach that avoids this whole problem by
  copying what a person did instead of scoring what the robot did.
- [Reinforcement learning](01_reinforcement-learning.md) is the page before this
  one, and it is where the policy, the return and the discount factor are
  explained if any of them went past too quickly.
- [Post-training a language model](../10_language-and-multimodal-models/02_post-training-a-language-model.md)
  shows preferences and verifiers used on text, which is where most of the work
  on them has happened.
- [Running and evaluating a model](../13_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  explains how to measure the real job honestly, which is the hold-out check
  this page leaned on.
- [Reward and progress models](../../07_learned-models/06_movement-models/03_also-used/03_reward-and-progress-models.md)
  is the catalogue page for learned rewards on arms, and it names the real
  models.
- [Evaluation and failure](../../07_learned-models/10_making-models-work-on-an-arm/02_most-used/03_evaluation-and-failure.md)
  covers what failure looks like on a real arm and how often it is measured
  wrongly.

---

## 8. Using it in Python

Sections 3 and 4 fitted two small models: one that predicts whether an attempt
will succeed from the state, and one fitted to a person's choices between pairs.
This section shows both in PyTorch, because the shapes are the part worth
seeing.

```python
import torch
from torch import nn

reward_model = nn.Sequential(nn.Linear(6, 32), nn.ReLU(), nn.Linear(32, 1))

# section 3: states from attempts that worked are 1, from attempts that failed are 0
states = torch.randn(14914, 6)                      # six measurements per state
labels = torch.randint(0, 2, (14914, 1)).float()
loss = nn.BCEWithLogitsLoss()(reward_model(states), labels)
print(round(loss.item(), 3))                        # about 0.7 before any training

# section 4: a pair of attempts, and which one the person preferred
better = torch.randn(256, 20, 6)                    # 256 pairs, 20 states each
worse = torch.randn(256, 20, 6)
score_better = reward_model(better).sum(dim=1)      # an attempt's score is the total
score_worse = reward_model(worse).sum(dim=1)
pref_loss = -torch.nn.functional.logsigmoid(score_better - score_worse).mean()
print(round(pref_loss.item(), 3))                   # about 0.7 before any training
```

Both printed numbers are about 0.693, which is what a model that has learned
nothing gives, because an untrained model says the two sides are equally likely
and the natural logarithm of a half is minus 0.693. Seeing that number is how
you check the loss is wired up correctly before training anything.

The library gives you the fitting and nothing else. TRL and similar packages
wrap both of these as ready-made trainers, so a reward model is a few lines, and
the preference loss above is exactly what direct preference optimisation and the
reward-model stage of learning from human feedback use. The verifier of section
5 has no library at all, because it is your own program.

What you still have to decide is everything this page was about. You decide what
the reward measures, and section 1 showed that paying for being near the object
buys an arm that stands near the object. You decide whether to shape it, and
section 2 showed that only one shape of shaping leaves the answer alone. You
decide where the labels or the preferences come from and how many you can
afford. Above all you decide what the hold-out measurement is, and section 6
showed that it is the only thing standing between you and a very high score on a
robot that does nothing useful.
