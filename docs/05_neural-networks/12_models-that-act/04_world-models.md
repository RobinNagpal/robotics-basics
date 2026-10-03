# World models

The page before this one, [vision-language-action
models](03_vision-language-action-models.md), ended with an arrangement where a large
slow model decides what the arm should aim for and a small fast one moves the joints
towards it. Every model in this chapter so far, including that one, works the same way
underneath: it looks at what is in front of it and says what to do next. None of them has
any idea what will happen afterwards.

This page is about the models that do have that idea. A **world model** is a model that
predicts what the world will look like after the robot acts, so that the robot can try
something out before doing it. The name is used for a whole family, from a few numbers
predicting a few numbers up to a model that generates video, and the family has one
shared job: given what is true now and what the robot is about to do, say what will be
true next.

This page is for a reader who has read the three pages before it in this chapter, so you
should already know what a policy is, what an action chunk is and why generative models
suit actions. You should also have read [reinforcement
learning](../11_learning-from-outcomes/01_reinforcement-learning.md), which is where the
words state, action and reward are explained, because this page uses them in the same way.

Everything here is measured on one small simulated system, a robot joint with a motor,
friction and a hard stop it cannot turn past. A learned model of it is fitted from recorded
movements and then pushed until it fails, and it fails in the three ways that carry over to
the much larger models used on real robots: the error piles up as the prediction runs on,
squeezing the pictures down throws away a detail a grasp depends on, and the one event the
recording almost never contains is the one the model gets most wrong. The script that works
it out is
[`docs/diagrams/models_that_act_2.py`](../../diagrams/models_that_act_2.py).

## Contents

1. [What a learned dynamics model is](#1-what-a-learned-dynamics-model-is)
2. [Why the prediction happens in a squeezed-down space](#2-why-the-prediction-happens-in-a-squeezed-down-space)
3. [Error that piles up over a rollout](#3-error-that-piles-up-over-a-rollout)
4. [Planning against a learned model](#4-planning-against-a-learned-model)
5. [Video prediction and neural simulators](#5-video-prediction-and-neural-simulators)
6. [When the model gets the physics wrong](#6-when-the-model-gets-the-physics-wrong)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. What a learned dynamics model is

The simplest member of the family is the one to start from, because everything else on
this page is a larger version of it. A **learned dynamics model** is a model that takes
what the robot can see now, together with the action it is about to take, and gives back
what it will see one step later. The word dynamics just means how the state changes over
time, and the word learned means the rule was fitted from recordings rather than written
out by a person.

![A layout showing a state box and a torque box feeding a learned model, which produces a predicted next state beside the real next state for comparison](../../images/models-that-act/world-models/one-step-job.svg)

From an angle of -25.78 degrees and a speed of +0.60 radians a second, with a torque of
+1.2 newton metres held for one step of 50 milliseconds, the real joint reaches -23.303
degrees while the learned model says -23.316 degrees.

The model is small on purpose, so nothing is hidden. It takes the angle, the speed and the
torque, works out ten simple combinations of them such as the angle times the speed, and
multiplies those by twenty learned numbers to get the change in angle and the change in
speed. Fitting it is one least-squares solve, and on a real robot the same job falls to a
network with millions of weights, but the shape of the task is identical. What it learns
from is a recording of the arm being driven about, of the kind a teleoperated demonstration
produces.

![A scatter of twelve thousand recorded transitions across angle and speed coloured by torque, with a red line marking the hard stop, beside a bar chart showing 11,522 transitions away from the stop and 478 touching it](../../images/models-that-act/world-models/training-transitions.svg)

The recording holds 12,000 transitions, and only 478 of them, which is 3.98 per cent,
ever touch the hard stop, so that is almost all the model gets to learn about what
happens when the arm runs into something.

Those 478 are left out of the fit, which sharpens the point without changing what really
happens, because a real recording contains very few collisions for the same reason: the
person driving the arm was avoiding them. One step at a time, the fitted model is very
good.

![A scatter of predicted against real next angle lying on the diagonal, beside a histogram of the one-step mistakes centred on zero and spanning about three hundredths of a degree](../../images/models-that-act/world-models/one-step-error.svg)

On data it never saw, the model predicts the next angle to within 0.0104 degrees and the
next speed to within 0.0033 radians a second.

That is the number that gets reported, and on its own it is misleading, which is what
section 3 is about. First it is worth seeing what the model actually learned, because the
shape of what it got right explains where it will go wrong.

![A chart of the pull on the joint against angle, with the real curve and the learned curve lying on top of each other inside a shaded band and parting outside it](../../images/models-that-act/world-models/learned-against-true-physics.svg)

Inside the angles the recording covered, which run from -51.0 to 25.8 degrees, the
learned pull on the joint is wrong by 0.0751 radians a second each second, and outside
them it is wrong by 1.0674, which is fourteen times worse.

Gravity pulls on the joint in proportion to the sine of the angle, and the model has no
sine in it, only squares and products. Inside the range it saw, a curve made of squares can
be bent to match a sine closely enough, and outside it nothing holds the two together, so
the model's version keeps going down while the real pull flattens off. That is the story of
this page in one picture: a learned model copies what it was shown and invents what it was
not.

---

## 2. Why the prediction happens in a squeezed-down space

The model in section 1 predicted two numbers from three, which is easy because the state
of that joint really is two numbers. A real robot does not get the state handed to it. It
gets camera pictures, and a camera picture is an enormous list of numbers, most of which
have nothing to do with what will happen next.

![Four small black and white pictures of a rod at different angles, each one a 32 by 32 grid](../../images/models-that-act/world-models/pixels-to-latent.svg)

Each of these simulated camera pictures is 32 by 32, so 1,024 numbers, while a modest
real camera frame of 256 by 256 pixels in colour is 196,608 numbers.

Predicting all 196,608 numbers of the next frame is an enormous job and almost all of it is
wasted, because what the robot needs to know is where the arm is and what it is holding. So
almost every world model used on a robot squeezes the picture down to a short list of
numbers and predicts the next short list. That list is called a **latent**, which means
hidden, since those numbers are not anything you can point at in the picture, and a model
that predicts the next latent rather than the next picture uses **latent dynamics**. How
short the list can be has a measurable answer.

![A curve of the share of the picture kept against the number of latent numbers, rising from 46.7 per cent at two numbers to 99.8 at sixty-four, beside a bar chart of the weights a one-layer predictor needs](../../images/models-that-act/world-models/variance-vs-latent-size.svg)

Eight numbers already hold 90.86 per cent of everything that changes between these
pictures, thirty-two hold 98.56 per cent, and a one-layer predictor over eight numbers
needs 64 weights where one over the raw pixels would need 1,048,576.

The squeezing here uses principal components, the simplest method, which keeps whatever
varies most across the pictures. Real systems use a trained encoder instead, but they do
the same thing and the sizes come out in the same range, and the saving is why nearly every
world model on a robot works this way. The cost is that what gets thrown away is chosen by
how much it varies, and nothing in that rule knows which parts the robot needs.

![Two rows of three pictures showing the same rod angle with the fingers open and shut, where the versions rebuilt from eight numbers are indistinguishable and the versions rebuilt from sixty-four are not](../../images/models-that-act/world-models/what-is-lost.svg)

The two real pictures sit at the same rod angle of 12.9 degrees and differ only in whether
the fingers are open, and rebuilding them from eight numbers gives the same picture twice.

The rod is large and it moves, so it dominates what varies and it survives the squeeze.
The fingers are a few pixels and they only open and shut, so they contribute almost
nothing to the variation and they are thrown away. The effect can be measured by asking
how often the open or shut state can be read back out of the short list.

![A bar chart of how often the fingers are read correctly, at about fifty per cent for two, four and eight numbers, eighty-one per cent for sixteen and a hundred per cent for thirty-two and sixty-four](../../images/models-that-act/world-models/reading-the-gripper.svg)

From eight numbers, which hold 90.86 per cent of the picture, whether the fingers are open
is read right 50.7 per cent of the time, which is guessing, and it takes thirty-two
numbers before it is read right every time.

That is the honest cost of latent dynamics, and it is not small. A squeeze that looks
excellent by the usual measure can be useless for the one decision that matters, because
grasping depends entirely on whether the fingers are open. The fix is to stop choosing the
latent by how much things vary and instead train it against the job, which is why world
models for robots are trained together with the policy rather than on their own.

---

## 3. Error that piles up over a rollout

Section 1 ended with a model that predicts one step to within 0.0104 degrees, and this
section is about what happens when you ask it for more than one step. A **rollout** is the
name for running a model forward repeatedly, feeding its own prediction back in as the
next input, and it is how any plan longer than one step gets made.

![Two charts, the left showing the real path and the model's path over three seconds of swinging, the right showing the gap between them rising and falling with each swing](../../images/models-that-act/world-models/rollout-vs-truth.svg)

Starting from the same state and given exactly the same torques, the two paths are 0.25
degrees apart after 6 steps, which is 0.30 seconds, and 0.74 degrees apart by step 60.

Nothing goes wrong in that picture, and that is the point. Each step is as accurate as the
one-step number says, but the second step starts from the model's own first answer rather
than from the truth, so an error in the first step is an error in the starting point of the
second. Averaged over many starts, the growth is easy to see.

![A chart of the average gap against steps predicted ahead, rising from 0.014 degrees at one step to 0.623 degrees at sixty, crossing a quarter of a degree at step nine](../../images/models-that-act/world-models/error-vs-horizon.svg)

Over the 233 of 600 test runs that never touch the hard stop, the gap grows from 0.014
degrees one step ahead to 0.623 degrees sixty steps ahead, and it passes a quarter of a
degree at step 9, which is 0.45 seconds.

A one-step error of a hundredth of a degree has become six tenths of a degree in three
seconds, forty-five times larger. Seen as a path through angle and speed together, the two
runs go round the same loop and separate only at the end.

![A phase chart of joint speed against joint angle showing the real and predicted paths spiralling inwards together with markers at steps 0, 10, 20, 40 and 60](../../images/models-that-act/world-models/phase-path.svg)

The two paths go twice round the same loop, and by step 60 they are 0.58 degrees apart.

The obvious reaction is to fit the model on more data, and the measurement says that this
does not work.

![Two charts against the number of recorded transitions, the left showing the one-step error falling steadily, the right showing the sixty-step gap bouncing around half a degree with no trend](../../images/models-that-act/world-models/more-data-does-not-fix-it.svg)

Going from 300 recorded transitions to 12,000 cuts the one-step error by four times over,
from 0.0454 to 0.0110 degrees, and changes the sixty-step gap by a factor of only 1.69,
with no direction to it.

The reason is in section 1's last picture. The model's error is not noise that averages away
with more examples, but a small bias left over from the fact that a curve made of squares is
not a sine, and a rollout adds that bias up step after step. No amount of data removes a
bias in the shape of the model, so the rule people draw from this is to trust a learned
model for a horizon measured in tenths of a second, and to find that limit by measuring it
rather than assuming it.

---

## 4. Planning against a learned model

Now that there is a model and a known limit on how far ahead it can be trusted, it can be
used to choose what to do. **Model-based planning** means trying several action sequences
inside the model, scoring what each leads to, and running the first action of whichever
scored best. Nothing touches the robot while this happens, which is the appeal, because a
bad idea costs a few milliseconds of arithmetic rather than a collision. The simplest
version, and still a common one, draws the candidate sequences at random.

![A fan of forty candidate futures drawn in pale blue inside the model, with the chosen one in green reaching the target line and the real outcome of the same torques in dashed black falling short](../../images/models-that-act/world-models/candidate-sequences.svg)

Forty random torque sequences of twenty steps each are run inside the model, which is 800
model steps for one decision, and the one the planner picks ends at 36.11 degrees inside
the model while those same torques on the real arm end at 12.49 degrees.

That gap is section 3's compounding error turning into a wrong decision, and section 6 comes
back to it. First comes the arithmetic of how many futures can be tried at all, because it
decides which kinds of world model are usable.

![Two charts, the left showing how many twenty-step candidates fit in fifty milliseconds for four model speeds, the right showing model steps rising with both the number of candidates and the horizon](../../images/models-that-act/world-models/arithmetic-of-planning.svg)

At 20 commands a second there are 50 milliseconds between commands, which holds 5,000
candidate futures of twenty steps if one model step costs half a microsecond, 500 if it
costs 5 microseconds, 50 if it costs 50 microseconds and 5 if it costs 500 microseconds.

The bill is always the candidates multiplied by the horizon, because every step of every
candidate is one call of the model. A model small enough to run in a few microseconds leaves
room to search properly, while one that takes half a millisecond a step leaves room for five
guesses, which is not a search at all. That line of arithmetic is why latent dynamics models
of a few dozen numbers are used for planning on robots and video models are not. Within
those limits, more candidates do give a better plan.

![A chart of the cost actually paid against the number of candidates, falling from 34.3 to 30.5 as the candidates go from four to 256, with the learned model and the real system almost on top of each other](../../images/models-that-act/world-models/more-candidates.svg)

Going from 4 candidates to 256 cuts the cost actually paid from 34.3 to 30.5, and
planning inside the learned model gives almost exactly the same result as planning inside
the real system.

That last part looks like it contradicts section 3, and it does not. The plan here is thrown
away and made again from a fresh measurement at every step, so the model is only ever
trusted for the length of one decision, and section 3 said the model is excellent over one
step. Remaking the plan is what makes a drifting model usable, and the price of not doing it
can be measured.

![A chart of how far the arm settles from the angle it was asked to hold, against the time between one plan and the next, rising from 9.9 degrees to 12.4 degrees](../../images/models-that-act/world-models/replanning-rate.svg)

When the real arm carries a steady pull of 0.45 newton metres that the model knows nothing
about, remaking the plan at every step leaves the arm 9.87 degrees from the angle it was
asked to hold, while remaking it once a second leaves 12.39 degrees.

So planning against a learned model works, it works because the plan is constantly
discarded, and the two things that decide whether it is possible at all are the cost of one
model step and the horizon the model can be trusted over. Both get much worse when the model
predicts pictures, which is the next section.

---

## 5. Video prediction and neural simulators

The world models above all predict a short list of numbers that somebody had to design. The
alternative that attracts the most attention skips that step and predicts the picture
itself, using the generative machinery from
[diffusion](../08_models-that-generate/01_diffusion.md). A **video prediction model** takes
a few frames and an action and generates the frames that come next, and people want one
because it can be trained on material nobody had to label.

![Two bar charts, the left comparing 540,000 frames with a recorded action against 1,080,000,000 frames of ordinary video, the right explaining what each kind of frame can teach](../../images/models-that-act/world-models/labelled-against-unlabelled.svg)

A full recording of 1,800 robot episodes is 540,000 frames with a recorded action beside
each one, and 10,000 hours of ordinary video at 30 frames a second is 1,080,000,000
frames, about 2,000 times as many.

That ratio is the whole argument, and it is a real one, because a video model can learn from
that pile what objects do when they are pushed, dropped or poured, which no amount of robot
recording would show. What it cannot teach is which action caused which change, since nobody
wrote the actions down, so such a model still has to be trained on recorded episodes before
it can be planned with, and the video stage is a head start rather than a replacement. The
second cost is time.

![Two bar charts on log scales, the left comparing 32 squeezed numbers with 196,608 for one frame and 3,932,160 for one frame through a twenty-step generator, the right comparing 40,960 numbers for one planning decision with 5,033,164,800](../../images/models-that-act/world-models/cost-of-predicting-pixels.svg)

One predicted frame at 256 by 256 in colour is 196,608 numbers, and a generator that takes
twenty denoising steps writes 3,932,160 of them, so one planning decision with 64
candidates twenty steps long writes 5,033,164,800 numbers in pixels against 40,960 in a
32-number squeezed space, which is 122,880 times the work.

Put beside section 4's budget of 50 milliseconds, that settles it: nobody plans at a robot's
control rate by generating video. Video world models are used three other ways instead. They
pretrain the squeezed-down space that a fast latent model then predicts in. They are run
slowly, a few times a second, to check whether a plan looks sensible while a fast policy
does the moving. And they are run offline, to generate training material for a policy rather
than to decide anything in the moment.

That last use is what people mean by a **neural simulator**, a learned model used in place
of a hand-written physics engine to produce the practice runs a policy learns from. The
attraction is real, because a hand-written simulator must be told the mass of every part,
the friction of every surface and the shape of every object, and getting those wrong is the
main reason policies trained in simulation fail on the real robot, while a learned simulator
gets all of it from recordings. The catch is that it only knows the parts of the world the
recordings covered.

![Two bar charts on log scales comparing the learned model's one-step error away from the stop with its error at the stop, 0.0176 against 8.59 degrees and 0.0059 against 1.067 radians a second](../../images/models-that-act/world-models/simulator-against-learned.svg)

The same learned model is wrong by 0.0176 degrees for a step that does not touch the hard
stop and by 8.59 degrees for one that does, which is 487 times worse, and in the speed it
is 181 times worse.

So a neural simulator is not a cheaper physics engine but a different thing with a different
failure. A hand-written engine is wrong everywhere by however much its numbers are wrong,
and that error is roughly the same whatever the robot does, while a learned one is nearly
perfect where it was shown and arbitrarily wrong where it was not, and contact is almost
always in the second group.

---

## 6. When the model gets the physics wrong

The last section said a learned model is arbitrarily wrong where it has not looked, and this
one shows what that looks like, because "it predicted the wrong physics" means something
very specific once you watch it happen.

![Two charts, the left showing the real arm stopping dead at the hard stop while the model's path carries straight on past it, the right comparing the average gap for runs that touch the stop with runs that do not](../../images/models-that-act/world-models/through-the-stop.svg)

The real arm reaches the hard stop after 2.75 seconds and goes no further, while the model
carries it 9.9 degrees past, up to 35.7 degrees, and averaged over all the runs that
touch the stop the gap reaches 15.7 degrees against 0.62 degrees for the runs that do not.

The model is not confused and not uncertain. It gives a clean, confident answer in which the
arm passes through solid metal, because nothing in the 11,522 transitions it was fitted on
ever showed it there was anything there. A model has no way of representing a thing it was
never shown, and that is the most important sentence on the page, because contact is exactly
what a robot arm spends its time doing and exactly what demonstrations avoid. The wrongness
is not confined to collisions, either, because even in open space the model quietly breaks a
rule the real world keeps.

![Two charts, the left showing the arm let go from rest swinging almost identically in the model and in reality, the right showing the model holding slightly more energy as the swings go on](../../images/models-that-act/world-models/energy-drift.svg)

Let go from rest with no torque at all, the real arm swings up to 20.2 degrees, which stays
clear of the stop, and its energy falls from 0.7744 to 0.3668 joules as friction takes it
away, while the model's version falls only to 0.4007 joules, which is 4.4 per cent of the
starting energy that came from nowhere.

Energy is not something the model was told about, so nothing stops it making a little. Four
per cent over three seconds sounds harmless, and on its own it is, but a planner searching
for the sequence that reaches a goal fastest is searching for exactly the sequences where
this kind of slip helps it, which is the last failure to show.

![Two charts, the left showing the cost the model expects, the cost the real system charges and the cost of the best candidate, all falling as candidates rise from four to 4,096, the right showing the two gaps between them staying open](../../images/models-that-act/world-models/plan-that-exploits-the-error.svg)

Planning forty steps ahead towards an angle that is past the hard stop, the model expects
to pay 0.8020 a step with four candidates and 0.6664 with 4,096, while the real system
charges 0.8641 and 0.7154, so the model flatters itself by between 0.0490 and 0.0621 a
step however hard the planner searches.

Two things there deserve naming. The first is that the model always expects to do better
than it does, and searching harder does not close that gap, because the planner chooses the
sequence the model scores best and the model scores a sequence best partly when it is most
wrong about it. The second is the gap between the red line and the green one, which is what
the planner loses by choosing with the model instead of with the truth, and it stays between
0.0073 and 0.0195 a step however many candidates are tried. Trying more futures buys a
better plan and not a more honest one.

What people do about all of this is short to list and hard to do. They keep the planning
horizon inside the range the model was measured to be trustworthy over, which section 3 put
at tenths of a second here. They remake the plan from a fresh measurement every step. They
add a penalty for plans that go where the recording was thin, so the planner stops being
rewarded for finding blind spots. And they go and record the situations the model is worst
at, which for an arm means deliberately recording contact rather than only success.

---

## 7. Where to read next

- [Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  is the next page, and it takes the latency and honesty arguments of sections 4 and 6
  and applies them to testing a model properly on a real robot.
- [Reinforcement learning](../11_learning-from-outcomes/01_reinforcement-learning.md)
  explains the learning-by-trying side of this, and a world model is what lets that trying
  happen inside a model instead of on the robot.
- [Diffusion](../08_models-that-generate/01_diffusion.md) explains the generative
  machinery that a video prediction model is built from, including why it takes many
  steps to produce one frame.
- [The map of models](../14_using-a-model-for-real/02_the-map-of-models.md) is the closing
  page of this book, and it puts world models beside every other family in one place.
- [World models](../../07_learned-models/08_world-models/01_overview.md) in the next book
  is the catalogue for this family, and
  [learned dynamics models](../../07_learned-models/08_world-models/02_most-used/01_learned-dynamics-models.md),
  [video prediction models](../../07_learned-models/08_world-models/03_also-used/01_video-prediction-models.md)
  and [learned simulators](../../07_learned-models/08_world-models/03_also-used/02_learned-simulators.md)
  give the named models of each kind and what each one costs.

---

## 8. Using it in Python

Section 1 fitted a dynamics model with one least-squares solve and section 3 rolled it
forward until it drifted, and both are short enough to write out in full. The code below
does what the pictures on this page do, on the same simulated joint, so you can change the
numbers and watch the horizon move.

```python
import numpy as np

G, L, M_ARM, DAMP, DT, STOP = 9.81, 1.0, 1.0, 0.25, 0.05, 0.45

def true_step(s, u):                       # section 1: the real system, with a hard stop
    th, om = s[..., 0], s[..., 1]
    om = om + DT * (-(G / L) * np.sin(th) - DAMP * om + u / (M_ARM * L ** 2))
    th = th + DT * om
    hit = th > STOP
    return np.stack([np.where(hit, STOP, th), np.where(hit, 0.0, om)], axis=-1)

def features(s, u):                        # section 1: ten simple combinations
    th, om = s[..., 0], s[..., 1]
    return np.stack([np.ones_like(th), th, om, u, th**2, om**2, u**2,
                     th*om, th*u, om*u], axis=-1)

rng = np.random.default_rng(2)             # collect a recording of the arm moving
s = np.stack([rng.uniform(-1.0, -0.15, 400), rng.uniform(-0.8, 0.8, 400)], axis=1)
rows, acts, nexts = [], [], []
for _ in range(30):
    u = rng.uniform(-1.1, 1.1, 400)
    s2 = true_step(s, u)
    rows.append(s); acts.append(u); nexts.append(s2); s = s2
X = features(np.concatenate(rows), np.concatenate(acts))
Y = np.concatenate(nexts) - np.concatenate(rows)
W = np.linalg.solve(X.T @ X + 1e-6 * np.eye(10), X.T @ Y)    # the whole fit

def learned_step(s, u):                    # section 3: the model, run on its own output
    return s + features(s, u) @ W

start, torques = np.array([-0.8, 0.0]), rng.uniform(-1.1, 1.1, 60)
a = b = start
for k, u in enumerate(torques):            # one rollout in each, same torques
    a, b = true_step(a, np.array(u)), learned_step(b, np.array(u))
    if k + 1 in (1, 10, 30, 60):
        print(f'after {k+1:2d} steps the gap is '
              f'{np.degrees(abs(a[0] - b[0])):.4f} degrees')
```

NumPy is doing one thing for you here, the least-squares solve on the line that makes `W`,
and that line is the entire training of this world model. On a real robot it becomes a
network trained by gradient descent over camera pictures, with PyTorch handling the
gradients, but the loop does not change: collect transitions, fit a one-step predictor, run
it forward.

What no library decides is everything the pictures measured. You choose how many numbers to
squeeze a picture down to, and section 2 showed eight numbers can hold 90.86 per cent of a
picture while reading the gripper no better than a coin. You choose how far ahead to plan,
and section 3 put the limit here at about nine steps, which you have to measure for your own
system rather than guess. You choose how often to remake the plan, and section 4 showed that
remaking it at every step is what makes a drifting model usable at all.

One thing to notice is that the gaps it prints are larger than section 3's. The snippet
keeps every recorded transition, including the few that touch the hard stop, and the single
rollout it runs reaches the stop once, so it is printing section 6's failure rather than
section 3's steady drift. Add a line counting how many steps of the real path sit at the
stop and the two kinds of error separate.

The last line of the loop is the one to take away. Print the gap at a few horizons, on your
own system, before you trust the model for anything. The one-step number will look excellent
and tell you almost nothing, and the number at thirty steps decides whether planning against
the model is going to work.
