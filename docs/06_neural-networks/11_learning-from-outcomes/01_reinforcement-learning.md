# Reinforcement learning: learning by trying

The page before this one, [reasoning and tool use](../10_language-and-multimodal-models/04_reasoning-and-tool-use.md),
finished a long run of pages about models that are trained by being shown the
right answer. Every one of those training methods needed somebody to write the
answer down first, because training compared what the model said with what it
should have said and pushed the weights towards the second one. This page is
about what to do when nobody knows the right answer in advance, but anybody can
look at what happened afterwards and say whether it went well.

That situation is very common on a robot arm. Nobody can write down the exact
joint angles that pick up a particular mug, because the right angles depend on
where the mug is, which way its handle points and how the fingers happen to
land on it. But it is easy to say afterwards whether the mug is in the gripper,
and that is enough to learn from. **Reinforcement learning** is the name for
learning from that kind of after-the-fact judgement: the learner tries
something, a number comes back saying how good the result was, and over many
tries the learner changes what it does so that the number gets bigger.

This page explains the pieces of that idea one at a time, on one small example
that is worked all the way through, and then it explains the three things that
make the idea hard in practice: that the learner has to try things it does not
yet believe in, that each improvement has to be small enough not to wreck what
already works, and that the number of tries needed is far larger than a real arm
can survive. The page assumes you have read
[gradient descent](../03_how-training-works/02_gradient-descent.md), so that you
know what it means to nudge numbers in the direction that improves a score, and
[the words everyone uses](../01_what-learning-means/02_the-words-everyone-uses.md),
so that the words model, training and parameter are already familiar.

The example in every picture is a made-up world rather than a measurement of a
real arm, and the script that draws the pictures,
`docs/diagrams/learning_from_outcomes.py`, works out every number in them. The
learning in it is real: the policies are learned from nothing by tabular
Q-learning and by a clipped policy-gradient step, both written in NumPy, and the
exact answers it is checked against come from value iteration.

## Contents

1. [The pieces: state, action, reward, episode and return](#1-the-pieces-state-action-reward-episode-and-return)
2. [The policy and the value function](#2-the-policy-and-the-value-function)
3. [Learning the whole thing from nothing](#3-learning-the-whole-thing-from-nothing)
4. [Exploring against taking the best answer you know](#4-exploring-against-taking-the-best-answer-you-know)
5. [Whose attempts you learn from, and how big a step to take](#5-whose-attempts-you-learn-from-and-how-big-a-step-to-take)
6. [Why this happens in a simulator, and what the crossing costs](#6-why-this-happens-in-a-simulator-and-what-the-crossing-costs)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. The pieces: state, action, reward, episode and return

Because reinforcement learning has no right answers to copy, it needs a
different set of words from the rest of this book, and this section introduces
all of them on one example small enough to draw in full.

The example is a table top divided into five squares across and five squares
deep, with a gripper that can move one square at a time, one block sitting on
the table, a bin in the far corner that the block is supposed to end up in, and
a small tray near the block that somebody also counts as a place to put things.

![A five by five grid seen from above, with the gripper on the bottom left square, the block in the middle, a tray just below the block and a bin in the top right corner, beside a list of the seven actions and the reward each one pays](../../images/learning-from-outcomes/reinforcement-learning/the-little-world.svg)

The world is five squares across and five squares deep, the gripper starts in the bottom left corner, and the seven actions each cost a small amount except for putting the block down in the bin, which pays 10.

Everything in this world is deliberately small, because the whole point of the
example is that you can see all of it at once. There are 25 squares, the gripper
is either holding the block or not, so there are 50 different situations the
learner can be in, and there are seven things it can do in each of them.

The first word is the state. The **state** is everything the learner can see at
one moment, and it is what the learner's decision is based on. In this world the
state is the square the gripper is on together with whether it is holding the
block, which makes 50 states in all. On a real arm the state would be the joint
angles, the gripper opening and a camera picture, and it is much bigger, but it
plays exactly the same part: it is the input.

The second word is the action. An **action** is one of the things the learner can
choose to do, and it is the output. Here there are seven of them, four moves,
closing the gripper, opening it, and waiting.

![Two five by five grids with the state number written in every square, one for an empty gripper and one for holding the block, and a third grid showing where each of the seven actions from state 34 leads](../../images/learning-from-outcomes/reinforcement-learning/state-and-action.svg)

Every square and holding flag together make one numbered state, and each action from state 34 leads to a named next state, so closing the gripper on the block moves the learner from state 34 to state 35.

Taking an action moves the learner from one state to another. From state 34, the
square the block sits on with an empty gripper, moving up leads to state 24,
moving left leads to state 32, and closing the gripper leads to state 35, which
is the same square with the block now held.

The third word is the reward. A **reward** is a single number that arrives after
each action and says how good that action's result was. It is not advice and it
does not say what should have been done instead, which is exactly what makes
reinforcement learning different from the training in the earlier chapters. In
this world every action costs 0.10 because time matters, a gripper command costs
another 0.05, and putting the block down in the bin pays 10, so the action that
finishes the job returns 9.85.

![A five by five grid showing the ten-step route from the start to the block to the bin, beside a bar chart of the ten rewards, nine of them small and negative and the last one 9.85](../../images/learning-from-outcomes/reinforcement-learning/reward-sequence.svg)

The best attempt takes ten actions, nine of which cost a little and one of which pays 9.85, so the whole attempt collects 8.90.

The fourth word is the episode. An **episode** is one whole attempt, from the
start to the moment the attempt is over, and it is over here when the block is
put down somewhere or when 80 actions have been used up. The fifth word follows
straight from it, because the **return** of an episode is the total of all the
rewards collected during it. The best attempt collects 8.90, and the picture
above shows where that total comes from.

![Three five by five grids showing three different attempts, one finishing at the bin with return 8.90, one finishing at the tray with return 1.30, and one wandering for 80 actions with return minus 10.35](../../images/learning-from-outcomes/reinforcement-learning/episodes-and-returns.svg)

Three real attempts drawn as the path the gripper took: a good one worth 8.90, a lazy one that drops the block on the near tray and is worth 1.30, and an untrained one that uses all 80 actions and is worth minus 10.35.

There is one more piece, and it is the only one that is not obvious. Rewards
that arrive later are usually counted for less than rewards that arrive now, and
the amount they are counted for is set by a number called the **discount
factor**, written as gamma. A reward that is one step away is multiplied by
gamma, a reward two steps away by gamma times gamma, and so on, and the total
worked out that way is called the discounted return. The reason for doing this
is partly that a robot that finishes sooner is worth more than one that finishes
eventually, and partly that without it the sums in section 2 can run away to
infinity in a task that never ends.

![Three panels: the weight gamma to the power of the step for four values of gamma, the bin route's ten rewards before and after weighting at gamma 0.9, and a bar chart comparing the discounted return of the bin route and the tray route at four values of gamma](../../images/learning-from-outcomes/reinforcement-learning/discounted-return.svg)

At gamma 0.9 the bin route is worth 3.17 and the near tray only 0.65, but at gamma 0.5 the bin is worth minus 0.19 and the tray minus 0.14, so the discount factor decides which route counts as better.

The right-hand panel is worth looking at twice, because it shows that the
discount factor is not a harmless detail. The bin pays five times what the tray
pays, but it is four actions further away, and below a gamma of about 0.68 those
four extra actions cost more than the extra payment is worth, so the best
behaviour flips from carrying the block to the bin to dumping it on the nearest
tray. Choosing gamma is therefore part of saying what you want, and a value
between 0.95 and 0.99 is usual because it keeps rewards a few dozen steps away
worth having. Everything from here on uses 0.95.

---

## 2. The policy and the value function

The five words in section 1 describe the problem, and the two words in this
section describe the two things a reinforcement learner actually builds and
stores.

The first is the policy. A **policy** is the thing that chooses the action, and
it is a rule that takes a state and gives back a chance for each action. A
policy that always picks the same action in the same state is called a
deterministic one, and a policy that spreads its chances over several actions is
a random one. On a real robot the policy is a neural network whose input is the
camera picture and the joint angles and whose output is the next movement. In
this small world it is a table of 50 rows and seven columns, one chance per
state and action, which is why everything on this page can be drawn.

![Three bar charts, one for each of three states, each comparing a flat set of seven equal chances before training with a set after training where one action has a chance of 0.91](../../images/learning-from-outcomes/reinforcement-learning/policy-as-a-table.svg)

Before training the policy gives all seven actions the same chance of about 0.14, and after training it gives 0.91 to one action in each state and shares the rest out for exploring.

The second is the value function. A **value function** takes a state and gives
back one number, which is the discounted return the learner expects to collect
from that state onwards if it keeps following its policy. It is a prediction
rather than a reward: it says what the future is worth from here, while a reward
says what just happened.

![Two five by five grids with a number written in every square, one for an empty gripper where the numbers rise towards the block, and one for holding the block where the numbers rise towards the bin](../../images/learning-from-outcomes/reinforcement-learning/value-on-the-grid.svg)

With an empty gripper the start square is worth 5.43 and the block's own square is worth 6.66, and once the block is held the bin's square is worth 9.85, because opening the gripper there pays 10 straight away.

The two are closely tied together, because once you know what every state is
worth, choosing an action is easy: look at the states each action leads to, and
take the action that leads to the best one. That is why the arrows in the
picture below all point uphill through the numbers.

![The same two grids with the numbers shown and an arrow or letter drawn in every square showing which action the policy takes there](../../images/learning-from-outcomes/reinforcement-learning/policy-and-value-together.svg)

With an empty gripper the arrows all lead towards the block and the block's square holds a C for closing the gripper, and while holding the block the arrows all lead towards the bin and the bin's square holds an O for opening it.

The difference between the two is worth stating plainly, because it is easy to
blur. The policy answers "what do I do now", and it is the thing that actually
runs on the robot. The value function answers "how well is this going to go from
here", and it exists to make the policy better, because the difference between
what the value function predicted and what actually happened is the signal that
training uses. Many methods learn both, some learn only a policy, and some learn
only a value function and read the policy off it, which is what the next section
does.

![Two scatter plots of the value the learner predicts for each state against the discounted return the policy really collects from that state, one early in training where the points scatter and one at the end where they lie on the line](../../images/learning-from-outcomes/reinforcement-learning/value-vs-return.svg)

Early in training the predicted value is out by 0.16 on average over the 50 states, and by the end it is out by 0.00, because the learner has seen enough attempts for the prediction to match what really happens.

---

## 3. Learning the whole thing from nothing

Sections 1 and 2 described what gets learned, and this section shows it actually
being learned, starting from a table of zeros and using nothing but the rewards
that come back.

The method used here is called Q-learning, and it keeps one number for every
state and action pair, which is the value of taking that action in that state
and behaving well afterwards. The learner starts with all 350 of those numbers
set to zero, runs an attempt, and after every action moves the number for the
action it took a little way towards the reward it got plus the value of the best
action available in the state it landed in. That one rule, applied over and
over, is enough.

![Two line charts, one showing the reward collected per attempt rising from minus nine to 8.90 over 6,000 attempts, and one showing the share of attempts that reach the bin rising from zero to 1.00](../../images/learning-from-outcomes/reinforcement-learning/learning-curve.svg)

Over 6,000 attempts the average reward rises from minus 9.09 in the first hundred to 8.78 in the last hundred, and the share of attempts that put the block in the bin rises from zero to 1.00.

The shape of that curve is worth understanding, because it is the shape nearly
every reinforcement learning run has. Nothing happens at all for a long time,
and in this run the first attempt that reached the bin was attempt number 658,
so 657 attempts were paid for and taught the learner nothing except that
wandering is not worth much. Then the curve climbs quickly once the first few
successes have been found, because each success tells the learner that a whole
chain of earlier states was worth more than it thought. Then it flattens as the
remaining improvements get smaller.

![Four five by five grids showing the action the policy takes in every square, before training and after training, with an empty gripper and while holding the block](../../images/learning-from-outcomes/reinforcement-learning/policy-before-after.svg)

Before training every value is zero so the policy takes whichever action comes first in the list, and after training the arrows lead to the block with an empty gripper and to the bin while holding it.

![Three five by five grids of value numbers for an empty gripper, all zero at the start, around 1 after 600 attempts, and between 4.70 and 6.66 after 6,000 attempts](../../images/learning-from-outcomes/reinforcement-learning/value-before-after.svg)

The learned value of the start square goes from 0 to 0.94 after 600 attempts and to 5.43 at the end, which is exactly the value that working the answer out directly gives.

What is happening underneath is that the value spreads backwards from the bin.
The square beside the bin learns its value first, because the reward lands there
in one step, then the square beside that one learns from it, and so on until the
start square knows what it is worth. This is why the middle grid above has small
numbers everywhere rather than large numbers near the bin and nothing elsewhere:
the information has reached everywhere but is still too small.

![A bar chart of the seven action values in state 35, comparing the values after 120 attempts with the values after 6,000 attempts and with the exact answers drawn as black marks](../../images/learning-from-outcomes/reinforcement-learning/q-values-one-state.svg)

In state 35, holding the block on its own square, the learner ends up valuing "up" and "right" at 7.17, "wait" at 6.71 and "open" at 5.18, and each of those agrees with the exact answer to two decimal places.

The last picture is the proof that the learner has really learned and not just
got lucky. Up and right are worth exactly the same, which is correct, because
the bin is three squares up and two squares right, so either one starts the
journey equally well. Opening the gripper is worth the least, which is also
correct, because the block would land on an ordinary square, cost 1 and have to
be picked up again. Nobody told the learner any of that.

---

## 4. Exploring against taking the best answer you know

Section 3 glossed over one setting, and this section is about it, because it is
the setting that decides whether the whole thing works.

A learner that always takes the action it currently believes is best will never
find out about anything better, because it never tries anything else. A learner
that always acts at random will find out about everything and collect almost
nothing while it does so. Choosing between those two is called the trade-off
between **exploring**, which means taking an action to find out what it does,
and **exploiting**, which means taking the action you already believe is best.
The usual way of settling it is simple: with some small chance the learner takes
a random action, and the rest of the time it takes its best one.

![Two panels, one showing the reward per attempt for a learner that never explores flattening at 1.30 while a learner that explores 70% of the time stays around minus 3, and one bar chart comparing the reward collected while training with the reward of the finished policy](../../images/learning-from-outcomes/reinforcement-learning/explore-or-not.svg)

The learner that never explores collects more reward while training, 1.15 against minus 3.07, and ends up with a policy worth 1.30 against 8.90.

That is the whole trade-off in one picture, and it is worth reading carefully
because the two bars measure different things. The grey bars are the reward
collected during training, which is what you actually get while the learning is
going on, and the learner that never explores wins there. The purple bars are
the reward the finished policy collects, and the learner that explores wins
there by a factor of nearly seven. Exploring costs you reward now and buys you a
better answer later.

![Two five by five grids showing the route each finished policy takes, one going from the start to the block and dropping it on the tray in six actions for 1.30, and one carrying it to the bin in ten actions for 8.90](../../images/learning-from-outcomes/reinforcement-learning/where-each-one-ends-up.svg)

The learner that never explores finds the tray one square below the block, settles on it and never discovers that the bin pays five times as much.

The failure is not that the greedy learner learned badly. It learned perfectly
well, and its policy is the best route to the tray. The failure is that it never
saw the bin, so the bin was never part of the problem it was solving. This is
the single most common way a reinforcement learning run fails on a real task,
and it is why so much work goes into making the learner try unlikely things.

![Two panels, one bar chart showing that none of eight runs that never explore end up going to the bin while all eight exploring runs do, and one line chart showing when each exploring run first reached the bin](../../images/learning-from-outcomes/reinforcement-learning/first-time-at-the-bin.svg)

Across eight runs of each kind, no run that never explores ever reaches the bin at all, while the exploring runs find it at attempt 26 in the luckiest case and attempt 4,468 in the unluckiest.

![A line chart of the reward collected while training and the reward of the finished policy against the exploring rate, from 0.00 to 0.80](../../images/learning-from-outcomes/reinforcement-learning/the-price-of-exploring.svg)

Raising the exploring rate from 0.00 to 0.80 raises the finished policy's reward from 1.30 to 8.90 and drops the reward collected while training from 1.01 to minus 7.30.

In this world more exploring is always better for the finished policy, because
the world is tiny and random wandering eventually stumbles on the bin. That is
not generally true, because in a world with a thousand states random wandering
finds nothing at all, and the answer is to explore in a cleverer way than at
random, or to give the learner a few demonstrations to start from. What is
generally true is the shape of the grey line: every unit of exploring is paid
for out of the reward collected while training, which on a real arm is paid for
in broken parts and operator time.

---

## 5. Whose attempts you learn from, and how big a step to take

Section 4 was about which attempts get made, and this section is about two
questions that follow from it: whether the learner may use attempts that some
other policy made, and how far it is allowed to change its policy after reading
them.

A method is called **off-policy** when it can learn from attempts made by any
policy at all, including old versions of itself and including a human driving
the arm by hand. Q-learning is off-policy, because its update rule asks what the
best action in the next state is worth, not what the policy that collected the
data actually did there. That makes it possible to store every attempt ever made
and keep learning from the pile.

![Two panels, one line chart showing the reward of the policy read off the table rising to 8.90 over 40 passes through stored attempts, and one grid showing the route it ends up taking](../../images/learning-from-outcomes/reinforcement-learning/learning-from-old-attempts.svg)

From 1,500 attempts made by a policy acting completely at random, only two of which reached the bin, Q-learning works out the best route in the world after about five passes through the stored data and reaches 8.90 without ever acting itself.

A method is called **on-policy** when it can only learn from attempts made by
the policy it is currently improving. Policy-gradient methods, which change the
policy's numbers directly in the direction that makes good actions more likely,
are on-policy, because the size of the change they want depends on how likely
the policy was to take that action at the time. Once the policy has moved, the
stored attempts describe a policy that no longer exists, and the advice they
give stops being right.

![A line chart of the reward a policy really collects against the number of gradient passes made over one fixed batch of 60 attempts, rising at first and then falling away](../../images/learning-from-outcomes/reinforcement-learning/on-policy-goes-stale.svg)

Reusing one batch of 60 attempts helps for the first few passes and then makes the policy worse, because the batch no longer describes what the policy does.

Why use an on-policy method at all, given that cost? Because policy-gradient
methods work directly on the thing you want, which is the policy, so they handle
actions that are real-valued rather than a short list, which is what a robot arm
needs, and they do not need a value table with one entry per action. The price is
that every improvement needs fresh attempts, which on a robot means fresh time.

That price is what **proximal policy optimisation (PPO)** is designed to reduce.
It is the most widely used policy-gradient method, and its idea is simple to say.
Collect a batch of attempts, then improve the policy on that batch several times
over rather than once, but refuse to let any single action's chance move more
than a fixed fraction away from what it was when the batch was collected. The
refusal is done by paying the update nothing for a change beyond that band.

![Two line charts of what an update is paid for a change, one for an action that turned out better than expected and one for an action that turned out worse, both flat outside a band from 0.8 to 1.2](../../images/learning-from-outcomes/reinforcement-learning/the-clip.svg)

Raising the chance of a good action beyond 1.2 times what it was earns nothing extra, so the update has no reason to push further, and lowering the chance of a bad action below 0.8 times earns nothing extra either.

What happens when the limit is taken away is not a slow decline but a collapse,
because one large step can push an action's chance all the way to certainty, and
once the policy only ever takes one action it collects no information about any
other and cannot recover.

![Two line charts, one of the reward per round for runs with and without the limit, and one of the biggest change in a single action's chance per round](../../images/learning-from-outcomes/reinforcement-learning/with-and-without-the-limit.svg)

With the limit the policy holds at about 1.01 and never moves any action's chance by more than 0.21 in a round, and without it the policy reaches 1.20 at its best, moves one action's chance by the full 1.00 in a single round, and ends at minus 7.66.

The learner in that picture settles on the near tray rather than the bin, for
exactly the reason section 4 gave, so the useful comparison is between the two
lines rather than against the best possible 8.90. What the right-hand panel
shows is the mechanism: without the limit, one round of improvement is enough to
make an action certain, and the collapse in the left-hand panel follows from it.

---

## 6. Why this happens in a simulator, and what the crossing costs

Every number on this page so far came from a world that costs nothing to run,
and this section is about what happens when the world is a real arm on a real
bench.

The worked example in section 3 used 6,000 attempts and 239,361 separate
actions, in a world with 50 states and seven actions. A real pick-and-place task
has a state made of a camera picture and a dozen joint angles, and a continuous
set of actions, so it needs far more attempts than this, not fewer. Even taking
this example's figures as they stand, and allowing three seconds for a real arm
to carry out one action and be reset when it drops something, the same learning
would take just under 200 hours of running.

![Two panels, one showing the actions used per attempt falling from 80 to about 10 over the run, and one bar chart on a log scale comparing the hours of running needed in a simulator and on a real arm](../../images/learning-from-outcomes/reinforcement-learning/how-many-attempts.svg)

The same 239,361 actions take about eight minutes in this script and 199 hours, or 8.3 days of continuous running, on an arm that needs three seconds an action.

That is why reinforcement learning for arms almost always happens in a
simulator, which is a program that pretends to be the robot and the table and
the objects, and which can run many copies of the task at once and faster than
real time. The policy is then moved onto the real arm, and the move is called
**sim-to-real** transfer. The trouble is that the simulator is never right. The
friction is wrong, the camera is in a slightly different place, the object is
heavier than the model says, and the bench has a fixture bolted to it that
nobody put in the simulator. The difference between the two, and the drop in
performance it causes, is called the **reality gap**.

![Three panels: the route the policy takes in the simulator, the same policy in a cell with a fixture on one square where it pushes against the fixture until the time runs out, and a bar chart showing the share of attempts reaching the bin falling from 1.00 to 0.00](../../images/learning-from-outcomes/reinforcement-learning/the-reality-gap.svg)

All six policies trained in the perfect simulator learn the same route, and in a cell with a fixture standing on one square of that route they push against it until the time runs out, so the share of attempts that reach the bin falls from 1.00 to 0.00.

That failure has the shape real sim-to-real failures have. The policy is not
confused and it does not wander: it carries out confidently a plan that was
correct in the simulator and is impossible in the cell, and because its state
never changes it takes the same impossible action again and again. A policy that
has only ever seen one version of the world has no reason to be careful about
anything the simulator got right by accident.

The usual answer is **domain randomisation**, which means changing the
simulator's settings at random for every attempt, so that the policy has to work
across a whole range of worlds rather than one. If the friction, the lighting,
the object's weight and the position of the fixture are all drawn fresh each
time, then the policy cannot lean on any particular value of them, and the real
cell has a good chance of being one more member of the range it already handles.

![Two panels, one bar chart of the share of attempts reaching the bin for each of eight possible fixture positions comparing the two kinds of training, and one grid showing the route the randomised learner picks with the possible fixture squares outlined](../../images/learning-from-outcomes/reinforcement-learning/domain-randomisation.svg)

Averaged over the eight squares the fixture could stand on, policies trained in one perfect simulator reach the bin on 0.62 of attempts and policies trained with the fixture moved every attempt reach it on 0.83, because the randomised ones learn a route along the edge of the table where no fixture ever stands.

What it costs is worth saying, because domain randomisation is often described
as free and it is not. The randomised learner is solving a harder problem, so it
needs more attempts to get anywhere, and if the range of worlds is drawn too
wide then no single policy does well on any of them and the learning stops
working altogether.

![Two panels, one showing the share of training attempts reaching the bin rising more slowly for the randomised learner, and one bar chart showing both policies collect 8.90 back in the perfect simulator](../../images/learning-from-outcomes/reinforcement-learning/what-randomising-costs.svg)

Randomising slows the learning down, and in this world it costs nothing at all in the easy case, because both kinds of policy collect 8.90 when there is no fixture in the way.

In this small world the randomised policy happens to lose nothing in the easy
case, because there are several routes of exactly the same length and it simply
picks a safer one. In a harder world there is usually a real price to pay, and
the policy that handles every friction setting is a little worse at the friction
setting the real bench turns out to have. Deciding how wide to draw the range is
therefore a judgement, and the honest way to make it is to measure on the real
arm rather than to argue about it.

---

## 7. Where to read next

- [Rewards, preferences and verifiers](02_rewards-preferences-and-verifiers.md)
  is the next page, and it answers the question this page left open, which is
  where the reward number actually comes from when nobody can write one.
- [Behaviour cloning and action chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md)
  shows the other way to get a policy for an arm, by copying demonstrations
  instead of trying things, and explains why that is the usual first choice.
- [World models](../12_models-that-act/04_world-models.md) explains how a
  learned model of what happens next can stand in for the simulator this page
  relied on, so that attempts can be made inside a network.
- [Post-training a language model](../10_language-and-multimodal-models/02_post-training-a-language-model.md)
  shows the same machinery used on text rather than movement, where the episode
  is one answer and the reward comes from a judge.
- [Reinforcement learning policies](../../07_learned-models/06_movement-models/03_also-used/01_reinforcement-learning-policies.md)
  is the catalogue page for arms, and it says which jobs are actually done this
  way today and which are not.
- [Learned dynamics models](../../07_learned-models/08_world-models/02_most-used/01_learned-dynamics-models.md)
  lists the real models that predict what the world does next, which is what a
  simulator provides by hand.

---

## 8. Using it in Python

Sections 1 to 3 built a state, an action, a reward, a policy and a value table by
hand. This section shows the same loop in about twenty-five lines of NumPy, on
exactly the little world the pictures use, cut down to the part that matters. In
practice nobody writes the learning rule themselves for a real robot, and the
libraries are named after this section, but a table this small makes the rule
visible.

```python
import numpy as np

n_states, n_actions, gamma, alpha = 50, 7, 0.95, 0.3   # section 1's world
Q = np.zeros((n_states, n_actions))                     # section 2's value table
rng = np.random.default_rng(7)

for attempt in range(6000):
    eps = 1.0 - 0.95 * attempt / 5999      # section 4: explore a lot, then less
    state, done = 40, False                # state 40 is the start square
    while not done:
        if rng.random() < eps:
            action = int(rng.integers(n_actions))       # explore
        else:
            action = int(np.argmax(Q[state]))           # exploit
        nxt, reward, done = step(state, action)         # the world answers
        target = reward if done else reward + gamma * Q[nxt].max()
        Q[state, action] += alpha * (target - Q[state, action])   # section 3's rule
        state = nxt

print(Q[40].max())        # 5.43, the value of the start square
print(np.argmax(Q[40]))   # 0, which is "up"
```

The two printed numbers are the ones section 2 and section 3 quoted, and you can
check the first one by hand: the best attempt pays 9.85 ten steps away and costs
about 0.1 a step before that, which at a gamma of 0.95 comes to 5.43.

What a library does for you is everything except that update rule. For a real
arm the value table becomes a neural network, so `Q[state]` becomes a forward
pass, the update becomes a loss and a gradient step, and the attempts are run in
many copies of the simulator at once. Stable-Baselines3 and CleanRL both provide
proximal policy optimisation ready built, Gymnasium provides the `step` function
above as a standard interface that simulators implement, and physics simulators
such as MuJoCo, Isaac Lab and Genesis provide the arm and the table. What you
write is the environment: the state, the action and the reward.

What you still have to decide is everything this page argued about. You choose
the discount factor, and section 1 showed that it changes which behaviour counts
as best. You choose how much exploring to do, and section 4 showed that too
little means never finding the good answer. You choose how far the policy may
move in one step, and section 5 showed what happens when that limit is removed.
Above all you choose the reward, and the next page is about how often that
choice is the thing that goes wrong.
