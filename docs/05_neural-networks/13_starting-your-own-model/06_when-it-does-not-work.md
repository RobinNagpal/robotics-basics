# When it does not work

The page before this one,
[recipes for models that act and predict](05_recipes-for-models-that-act-and-predict.md),
gave a starting recipe for each family of model that makes a robot move, and
every one of those recipes ends in the same place, which is you typing a training
command and waiting. This page is about what to do when the waiting is over and
the thing does not work. That is not a rare accident but the normal first
outcome, and saying so plainly is part of this page's job, because somebody who
believes that a recipe followed properly gives a working model will take their
first failure as proof that they are not clever enough, when what they have
reached is the ordinary place from which everybody starts the real work.

The page is organised by symptom rather than by cause, because a symptom is what
you actually have in front of you: a curve that did not fall, two curves that
parted company, or an arm that knocked a mug over. Each section takes one symptom
and answers three questions about it in the same order, which are what the
symptom means, what the cheapest test is that confirms the cause or rules it out,
and what to change once you know. The tests are ordered by what they cost, so
collecting more data, which is the expensive answer everybody reaches for first,
is suggested only where it really is the answer.

It assumes you have read the earlier pages of this chapter, and in particular
[the order of the work](02_the-order-of-the-work.md), which sets out the
milestones you were working through when the trouble started. Two pages elsewhere
own the machinery that this page only diagnoses against.
[Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
owns what a held-out set is, why it has to be split along the right seam, and what
early stopping, dropout and weight decay do.
[Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
owns how a model is judged on a real arm, and in particular why a **success
rate**, which is the fraction of whole attempts that worked, needs many trials
before it means anything.

Every number below is worked out and printed by
`docs/diagrams/starting_your_own_model_6.py`, and all of its data is simulated.
There are three simulated jobs. In the first, an arm's gripper has to be driven
to an object on a table, a written controller plays the demonstrator, its commands
are recorded with noise, a network is trained to copy them, and the same weights
are then run in closed loop, which gives a task success rate as well as a loss.
In the second, two demonstrators go round one obstacle on opposite sides. In the
third, a model says how wide to open a gripper for each kind of object. The jobs
are invented, but the networks, the training steps, the roll-outs and the counted
trials are real, written in NumPy.

## Contents

1. [The loss does not fall at all](#1-the-loss-does-not-fall-at-all)
2. [The loss falls to a floor well above zero and stops](#2-the-loss-falls-to-a-floor-well-above-zero-and-stops)
3. [The training loss falls and the held-out loss does not follow](#3-the-training-loss-falls-and-the-held-out-loss-does-not-follow)
4. [Both losses look fine and the robot still fails the task](#4-both-losses-look-fine-and-the-robot-still-fails-the-task)
5. [It works on the objects it was trained on and on nothing else](#5-it-works-on-the-objects-it-was-trained-on-and-on-nothing-else)
6. [It works in the simulator and not on the arm](#6-it-works-in-the-simulator-and-not-on-the-arm)
7. [It worked last week and does not now](#7-it-worked-last-week-and-does-not-now)
8. [Where to read next](#8-where-to-read-next)
9. [Using it in Python](#9-using-it-in-python)

---

## 1. The loss does not fall at all

The first symptom arrives within a minute of starting the run the recipe told you
to start, and it is a flat line. What it means is worth saying clearly, because it
saves a week of collecting data: a flat loss is never a sign that you have too few
examples, since a network with enough weights can memorise whatever you give it,
so a model that cannot even drive the error down on its own training examples has
something wrong with its arrangement rather than its data.

![Four loss curves against training step on a log scale, three of them flat near 0.02 and one falling to 0.001](../../images/starting-your-own-model/when-it-does-not-work/loss-does-not-fall.svg)

The same network and the same 8,000 recorded commands give a falling curve at a learning rate of 0.003 and a flat one at 1.0, at 0.000001, and when the labels are shuffled.

The **learning rate** is the number saying how big a step the training takes down
the slope of the loss, and
[gradient descent](../03_how-training-works/02_gradient-descent.md) explains what
it is a step of. At 1.0 this run ends at 0.02468 on held-out data, at 0.000001 it
ends at 1.60748, and at 0.003 it ends at 0.00105. The fourth curve has the good
rate and is still flat because its labels were shuffled, so each set of readings
is paired with another attempt's command and there is nothing to learn. It settles
at 0.02568, which is no better than answering zero every time, and that comparison
is the first thing to put in place: work out what the loss would be if the model
answered with the average of your labels, which here is 0.024181, and write it
down before you start, because a loss number on its own tells you nothing.

![Three loss curves on eight examples, two falling below a thousandth of a millionth and one flattening at 0.00036](../../images/starting-your-own-model/when-it-does-not-work/single-batch-test.svg)

Eight examples and 2,000 steps: the network as written reaches 8.8 at the eighth decimal place, while the same network with its first two layers frozen by accident stops at 0.00036.

That is the cheapest test there is. Take eight examples, throw the rest away, and
train on those eight until the loss on them reaches nothing, which any correctly
wired network will do because eight examples is a thing any network can memorise.
The red curve is a network whose first two layers were frozen by accident, which
happens whenever somebody loads a published starting point with its layers locked
and forgets to unlock them, and in an ordinary run it is invisible because the
model still trains, just badly. Notice that the shuffled labels also pass this
test, so it proves your code can learn and proves nothing whatever about your
data, and that is exactly why it is useful, because it splits the possible faults
into two piles and you then search only one.

![Held-out loss against learning rate across ten powers of ten, flat and high at both ends with a dip in the middle](../../images/starting-your-own-model/when-it-does-not-work/learning-rate-band.svg)

Across learning rates from a ten-millionth to three, only the band from 0.00032 to 0.032 beats answering with zero, and the best value in this short run of 1,200 steps is 0.032, at a held-out loss of 0.00167.

If the single-batch test passes, the usual cause is a learning rate outside its
band. That band is about a hundred times wide from end to end, which sounds
generous until you notice that the rates being tried span ten powers of ten, so a
rate picked without thought lands outside it far more often than inside. Below the
band the loss falls so slowly that a few thousand steps look flat, and above it
the steps overshoot so badly that the model never settles, and those two very
different faults draw the same flat line, so the way to tell them apart is to try
a rate ten times smaller and one ten times larger and see which direction helps.

![Two loss curves beside a bar chart of the spread of each input column, one set of bars reaching 138 and the other all at 1](../../images/starting-your-own-model/when-it-does-not-work/input-scale.svg)

Four of the eight inputs written in millimetres instead of metres leave the run at a held-out loss of 0.89920, and subtracting each column's average and dividing by its spread brings the same run to 0.00105.

The last common cause is inputs that were never put on one scale. Here the four
position readings arrive in millimetres while the other four are around one, so
the column spreads are 138, 148, 125 and 134 against 0.289, 0.0494, 0.586 and
0.997, no single learning rate suits both groups, and the run ends nearly a
thousand times worse from a units mistake that produces no error message anywhere.
Subtracting each column's average and dividing by its spread repairs it in one
line, and
[normalisation and stability](../04_making-training-work/02_normalisation-and-stability.md)
explains why the arithmetic inside the network needs this. Once the loss is
falling, the next question is how far down it goes.

---

## 2. The loss falls to a floor well above zero and stops

The second symptom follows a fixed version of the first. The loss falls for a
while, flattens at a value that is clearly not zero, and stays there however long
the run goes on. This means something quite different from a flat line, because
the model is learning and the only question is whether the floor it reached is a
fault or the right answer. Most people assume it is a fault and reach for a bigger
model, and most of the time they are wrong, so this section is about finding the
floor before trying to beat it.

![Training and held-out loss falling together over 6,000 steps and flattening just above a dashed line marking the noise](../../images/starting-your-own-model/when-it-does-not-work/a-floor-not-a-bug.svg)

Both curves flatten at about 0.00098 against a dashed line at 0.00061, which is the variance of the noise in the recorded commands themselves.

The demonstrator in this job is sloppy when the gripper is far from the object and
careful when it is close, so every recorded command is the right command plus
noise whose spread grows with the distance still to go. The variance of that noise
is 0.00061 and no model can go below it, because that part of each label is
different in every recording and nothing in the readings predicts it. The run ends
at 0.000824 on training data and 0.000978 on held-out data, which is 1.6 times the
noise, so nearly everything left in the loss is noise rather than error. On real
data you find this floor by recording the same situation twice and measuring how
much the two recordings differ, since half the variance of that difference is a
lower limit, and it is nearly always larger than people expect.

![Training and held-out loss against hidden width from 1 to 128 on a log scale, dropping steeply to width 4 and then flat](../../images/starting-your-own-model/when-it-does-not-work/floor-and-model-size.svg)

Making the hidden layers wider moves the held-out loss from 0.024602 at width 1 to 0.000896 at width 4, and then from 0.000896 to 0.000879 across the whole range from width 4 to width 128.

With a floor in hand you can ask whether the model is what holds you above it, and
the test is one number to change and one run to wait for. Width 1 is far too small
and scores 0.024602, which is the answering-with-zero number from section 1, while
width 2 scores 0.008368. By width 4 the model is at 0.000896, and the thirty-two
fold increase from there to width 128 buys 0.000017, which is nothing. Do this
before anything else, because the answer is so often that the model was never the
problem.

![Sixty demonstrated paths past a round obstacle, half going above and half below, with a single black line passing through the obstacle, beside two bars of loss](../../images/starting-your-own-model/when-it-does-not-work/two-ways-round.svg)

Thirty-six demonstrations go above the obstacle and twenty-four below, every one clearing its edge by at least 53.3 mm, while the single path that least squares gives passes 31.4 mm inside that edge.

The floor that no model size will move is the one in the data, and on a robot its
commonest form is in that picture. Two demonstrators were asked to move past an
obstacle and one went above while the other went below, so for the same readings
the recorded answer is sometimes one thing and sometimes the opposite. A model
trained to make its squared error small cannot pick a side, since the sum of the
squared distances to both sides is smallest in the middle, so it answers with the
average and the average goes straight through the obstacle. The loss confirms it,
because the best single answer scores 0.006573 against 0.000133 for a model fitted
to one side alone, which is 49.3 times worse, and the model has done exactly what
it was asked. Look at your largest errors and ask whether two different answers
appear for nearly the same readings; if they do, narrow the job until one answer
is right, add something to the readings that says which way this attempt goes, or
move to a model that can hold several answers at once, which is what
[diffusion and flow policies](../12_models-that-act/02_diffusion-and-flow-policies.md)
are for.

![Two held-out loss curves that lie on top of each other until step 3,000, where one drops below the other and stays there](../../images/starting-your-own-model/when-it-does-not-work/lr-too-high-to-settle.svg)

The same run with the learning rate held at 0.01 ends at 0.001213, and with the rate cut to 0.001 at the half-way point it ends at 0.000788.

The last cause of a floor is the cheapest to remove. A rate large enough to make
early progress is too large to settle at the end, because each step jumps further
than the distance left to go, so the loss bounces about above the place it is
trying to reach. Cutting the rate by ten part way through takes this run from
0.001213 to 0.000788, which is a third of the remaining loss removed by one line
of code, so try that before concluding anything about your data or your model
size. A floor is at least an honest number, though, and the next symptom is where
the number itself stops being honest.

---

## 3. The training loss falls and the held-out loss does not follow

The third symptom is the one everybody has been warned about and few people
recognise in time. The training loss keeps going down while the loss on examples
kept back stops falling or turns and climbs, which means the model is learning
the particular examples rather than the pattern in them, and that is called
**overfitting**.
[Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
explains the mechanism and the cures, so this section is only about recognising it
in your own run and telling it apart from the thing that looks exactly like it and
is not it.

![Two loss curves over 20,000 steps, the training one falling steadily while the held-out one bottoms out and turns upwards](../../images/starting-your-own-model/when-it-does-not-work/train-and-held-out-part.svg)

Six demonstrated attempts and a network of width 128: the held-out loss reaches its best value of 0.00458 at step 11,000 and climbs to 0.00870 by step 20,000, while the training loss falls to 0.000009.

Those two numbers finish a factor of 971 apart, and the held-out loss ends at 1.90
times its own best value, so somebody watching only the training curve would stop
at step 20,000 holding a model almost twice as bad as the one they had at step
11,000, and would have thrown the good one away. The first thing to do therefore
costs nothing: score the held-back examples every few hundred steps, keep a copy
of the weights whenever that score reaches a new low, and finish with the copy
rather than the last weights. That is early stopping, and it turns this symptom
from a disaster into a mild waste of electricity.

![Training and held-out loss against the number of demonstrated attempts, from 3 to 200, with the gap between them shaded and closing](../../images/starting-your-own-model/when-it-does-not-work/would-more-data-fix-it.svg)

The same network trained on more attempts closes the gap between the two losses from 23,509 times at 3 attempts, to 7.2 times at 12, to 2.4 times at 50, to 1.2 times at 200.

The second thing to do is find out whether more data would fix it, which you can
do from the data you already have. Train the same model on a quarter of your
attempts, on a half and on all of them, and plot the held-out loss against the
number of attempts. A curve still falling steeply at the right-hand end, as this
one is between 3 and 50 attempts, says that collecting more is worth the effort,
and a curve that has flattened says it is not and that something else is the
limit. This is the one measurement that honestly answers the question everybody
asks first, and it costs three short training runs rather than three weeks of
recording.

![Four loss curves over one run, scored against the training set and three different held-out sets, each flattening at a different height](../../images/starting-your-own-model/when-it-does-not-work/which-held-out-set.svg)

One run scored four ways: on its own training rows it reaches 0.00074, on rows taken out of the training attempts 0.00074 as well, on whole attempts it never saw 0.00205, and on attempts where the object lies further out than any it trained on 0.01154.

Now for the thing that looks like overfitting and is not. The dashed purple curve
is a held-out set made by taking rows out of the training attempts at random,
which leaves nearly identical moments of one recording on both sides of the split,
and it sits exactly on top of the training curve, so anybody using it would report
0.00074 and believe their model generalised. The red curve is the opposite
mistake, because its attempts have the object further out on the table than
anything in training, so it is high from the very first step, best at 0.01100 and
ending at 0.01154. Read the shape rather than the height: a curve that falls with
the training curve and then turns upwards is overfitting, and early stopping plus
more attempts is the answer, while a curve that was never low is not overfitting
at all but a held-out set asking a different question from the training set, for
which the only repairs are to record the missing situation or to change what you
claim the model does.

---

## 4. Both losses look fine and the robot still fails the task

The fourth symptom confuses people most, and unlike the three above it belongs to
robots rather than to machine learning in general. The training loss fell, the
held-out loss followed it down, the flattening happened near the floor section 2
told you to work out, and by every number on your screen the model is finished.
Then you run it on the arm and it misses the object half the time. This does not
mean something has gone wrong since you measured; it means the loss and the task
were never the same question.

![A scatter of sixty policies, held-out loss against success rate, with a tight cluster at the left whose successes run from 40% to 98%](../../images/starting-your-own-model/when-it-does-not-work/loss-is-not-the-job.svg)

Sixty policies trained on the same recorded commands and scored twice: two of them have held-out losses of 0.00103 and 0.00107, four parts in a hundred apart, and succeed 81% and 50% of the time.

The script trains those sixty policies on the same 8,000 recorded commands,
changing only the width, the starting seed and the number of steps, then scores
each one on held-out commands and again by 300 attempts in which the policy drives
the arm itself and succeeds if the gripper finishes within 15 mm of the object.
Across all sixty the two scores agree, with a rank correlation of -0.950, where a
**rank correlation** is a number between -1 and +1 saying how closely one ordering
matches another, and that agreement is why people trust the loss. It comes
entirely from the bad policies. The eighteen that trained down to the floor have
losses between 0.00079 and 0.00140, a spread of less than a factor of two, and
success rates from 40.3% to 98.3%, their rank correlation falls to -0.806, and the
policy with the lowest loss of all succeeds 93.3% while the best of the sixty
succeeds 98.3% with a worse loss of 0.00089. So once every candidate has trained
properly, which is the only time you are really choosing between them, the loss
has stopped telling you which to ship.

![Two bands of gap-to-target against step with a dashed tolerance line, beside two histograms of the gap at the last step](../../images/starting-your-own-model/when-it-does-not-work/what-the-arm-does.svg)

The two circled policies finish a median of 7.4 mm and 14.9 mm from the object, and since the tolerance is 15 mm, the second one's attempts land astride the line that decides the attempt.

The first reason is the shape of the two measurements. The loss is an average over
all forty steps of every attempt, so a small error while the gripper is a quarter
of a metre away counts exactly as much as the same error at the last step, whereas
the task is a threshold applied once, at the end. These two policies differ almost
entirely in their last ten steps, where one settles at 7.4 mm and the other
wanders back out to 14.9 mm, and nine attempts in ten finish inside 22.0 mm for
the better one against 26.8 mm for the worse, so the whole gap in success comes
from a few millimetres on one side of one line.

![Two scatter plots of success rate against error, the left against error on the demonstrator's states and the right against error on the policy's own states](../../images/starting-your-own-model/when-it-does-not-work/states-it-reaches-itself.svg)

Measured on the situations the demonstrator reached, these eighteen policies have errors within a factor of four of each other, and measured on the situations they drive themselves into, the errors spread over a factor of ten and track the success rate more closely.

The second reason is deeper and is the one to carry away. The held-out loss asks a
question about the demonstrator's situations, which is whether the model would
have sent the demonstrator's command from a moment the demonstrator was in, while
the task asks whether the arm ends up in the right place with the model driving
from the first step. They differ because the model's own small errors move the arm
slightly away from anywhere the demonstrator went, where the model has seen
nothing and errs a little more, which moves it further still. Here the error
measured on the policy's own situations is between 2.29 and 12.3 times the error
on the demonstrator's, and it ranks the policies by success better, at -0.942
against -0.862.
[Behaviour cloning and action chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md)
explains why copying a demonstrator has this built in, and what chunking the
commands does about it.

![Measured success rates with their 95% ranges at 10, 20, 50, 100, 200 and 400 trials, for two policies, the ranges overlapping at the left and separating at the right](../../images/starting-your-own-model/when-it-does-not-work/how-many-trials.svg)

Ten trials give 80.0% and 70.0% for two policies that really differ by about 28 points, with ranges of 44.4% to 97.5% and 34.8% to 93.3% that overlap almost completely, while 400 trials give 84.2% and 56.2% with ranges that do not touch.

So the cheapest test for this symptom is to run the thing, because no measurement
on recorded data will show it, and twenty closed-loop attempts take an afternoon
and are worth more than any number of held-out losses. What to change is not the
training settings, since section 1's work is already done, but either the data,
by recording demonstrations that start from the situations the policy drives
itself into so that it learns to come back, or the model, by moving to one that
commits to a chunk of future commands at once. The warning that goes with all of
this is that the new measurement is far noisier than the loss it replaces, since a
success rate is a count of whole attempts, and the picture above shows ten trials
putting these two policies in almost the same place.
[Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
works through how such a range is built and how many trials different comparisons
need, and this page takes only the result, which is not to report a success rate
from twenty trials and not to believe one.

---

## 5. It works on the objects it was trained on and on nothing else

The fifth symptom arrives on the day you show somebody the robot. It picks up all
six of the objects it was trained on, every time, and then somebody puts a seventh
on the table and it fails completely. This means the model found an easier way to
answer than the one you had in mind: it did not learn the property you cared
about, it learned which of your six objects it was looking at, and since that
answers every question in your training set and in your held-out set, nothing you
measured could have told you. In this simulated job each kind of object has a
shape and a colour, the right gripper opening of between 23.5 and 78.5 mm depends
on the shape alone, an answer counts as right within 4 mm, and the colour readings
are the crisp ones while the shape readings are noisy, so reading the colour and
looking up a remembered answer is the more accurate strategy.

![A bar chart of twelve objects, the first six all at 100% in blue and the last six at nearly zero in red](../../images/starting-your-own-model/when-it-does-not-work/per-kind-of-object.svg)

The same weights get 99.9% of the openings right on the six kinds of object they trained on and 0.7% right on six kinds they never saw, although every opening is decided by a shape the readings describe perfectly well.

Those two numbers are what a learned lookup table looks like from outside. Nothing
is broken, the model answers confidently, and on the training objects it is better
than you had any right to expect. The failure being total rather than gradual is
itself the clue, because a model that had learned the shape and merely learned it
imperfectly would be somewhat right on a new object rather than entirely wrong.

![Three bars: 100% for rows held back from the same kinds, 49.8% for two kinds held back, and 0.4% for kinds nobody collected](../../images/starting-your-own-model/when-it-does-not-work/split-by-kind.svg)

Holding back rows from the same six kinds gives 100.0%, holding back two whole kinds gives 49.8%, and the truth on six kinds nobody ever collected is 0.4%.

The cheapest test is the middle bar and it costs one extra training run. Do not
hold back rows, hold back kinds, which means training on four of your six objects
and scoring on the two you kept out. The left-hand bar is what an ordinary random
split reports, and it reports perfection because rows of the same object sit on
both sides of it. The middle bar is the warning. Notice that it is still far too
kind, since the real answer on objects nobody collected is 0.4%, and the reason is
that two held-back kinds which happen to resemble the four trained ones still
flatter the model, so treat a held-out-kind score as an upper limit rather than a
prediction and hold back as many kinds as you can spare.

![A line chart of success on new kinds against how many kinds the same 1,800 pictures are spread over, rising from 4% to 39%](../../images/starting-your-own-model/when-it-does-not-work/variety-not-volume.svg)

The same 1,800 pictures spread over more kinds of object: one kind gives 4% on objects it never saw, four kinds give 14%, nine give 20% and twelve give 39%, while the score on the kinds it did train on stays near 100% throughout.

That answers the question everybody asks next, which is whether to collect more
pictures. The total is held at 1,800 in every run and only the number of distinct
objects changes, so every difference between the points is bought with variety
alone and costs nothing in recording time. Going from one kind to twelve takes the
score on new objects from 4% to 39% with no extra data at all, and the four runs
drawn as faint dots behind each point show how much it still depends on which
objects you happen to own. More pictures of the objects you already have does
nothing here, which is why this measurement is worth making before any recording
session.

![Three bars showing the score falling when the colour readings or the shape readings are scrambled, beside four bars comparing a model trained with and without the colour readings](../../images/starting-your-own-model/when-it-does-not-work/which-reading-did-it-use.svg)

Scrambling the colour readings on objects the model trained on drops it from 99.7% to 53.7%, which proves it was using them, and training again with those readings left out gives 98.5% on the trained kinds and 59.7% on kinds it never saw.

The left-hand panel names the shortcut and needs no retraining. Take your held-out
examples, shuffle one group of readings between them so that each example keeps
its own shape readings and gets somebody else's colour readings, and score the
model again. The opening cannot possibly depend on the colour, because the job was
built so that it does not, and yet hiding the colour costs 46 points, which is
proof that the model was leaning on it. The right-hand panel is the repair and it
is what makes this section worth the trouble, since the same model trained with
the colour readings left out of the input entirely gives up 1.2 points on the
objects it knows and goes from 1.2% to 59.7% on objects it has never seen. Taking
a shortcut away is often worth more than any amount of extra data, and
[where the data comes from](../../07_learned-models/01_what-models-are/05_where-the-data-comes-from.md)
describes how robot datasets come to contain such shortcuts.

---

## 6. It works in the simulator and not on the arm

The sixth symptom is section 5's problem with the whole world as the object. The
policy succeeds in the simulator it was trained in and fails on the real arm, and
what this means is that the simulator and the arm differ in several ways at once,
each of which the model has never seen. The useless response is to call this the
reality gap and conclude that simulators do not work. The useful response is that
the gap is a list of named differences, every one of which can be put into the
simulator and measured.

![A bar chart of six success rates, the simulator at 71.8% and five variations between 23.3% and 80.5%](../../images/starting-your-own-model/when-it-does-not-work/one-difference-at-a-time.svg)

The policy succeeds 71.8% of the time in the simulator it trained in, 71.3% with noisier sensors, 23.3% with the object reported 12 mm from where it is, 37.8% with two periods of delay, 78.2% with 15% weaker drive, and 27.5% with all four at once.

That is the cheapest test, and it is cheap because every one of those bars is a
run of the simulator rather than an hour on the arm. Read it as a ranking of
suspects. The sensor noise costs nothing at all, the weaker drive actually helps,
because this policy overshoots and a weaker arm overshoots less, and almost the
whole gap is the calibration error and the delay. Notice also that the four
separate costs do not add up to the cost of having all four, which is why you have
to measure the combination as well as the parts, and why a list of single
measurements is a list of suspects rather than an explanation.

![A line of success rate against added delay, falling from 72.6% at no delay to 13.9% at six periods, with the median final gap rising behind it](../../images/starting-your-own-model/when-it-does-not-work/delay-costs-success.svg)

Adding delay one control period at a time, at twenty commands a second, takes the success rate from 72.6% to 61.5% after one period, 40.0% after two and 23.9% after three, while the median gap at the last step grows from 11.9 mm to 25.1 mm.

Delay deserves its own picture because it is the difference people forget. A
simulator usually hands the policy a picture of the world as it is now and applies
the answer at once, while a real cell spends time exposing the camera, moving the
picture, working out the answer and putting the command on the arm's bus, so the
policy is always acting on a world that has moved on. One period of 50
milliseconds costs 11 points here and two cost 33, and the budget page of
[running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
shows how to add that time up for a real cell. The repair is partly to make the
loop faster and partly to put the measured delay into the simulator, so that
whatever you train next is trained against it.

![Four bars of success on the arm, comparing training at one setting with training across a range, each with the calibration error left in and taken out](../../images/starting-your-own-model/when-it-does-not-work/randomise-what-you-do-not-know.svg)

Training across a range of delay, drive and sensor noise, and then measuring the 12 mm calibration error and taking it out, lifts the arm from 27.5% to 88.2%, while the same randomised training with that error left in place gives 5.3%, which is worse than doing nothing.

The repair has two halves and the picture is about getting them the right way
round. Recording the demonstrations in simulators whose delay, drive strength and
sensor noise are each drawn from a range, rather than fixed at one guess, is
called domain randomisation, and it works because a policy that has seen every
value in the range cannot rely on any one of them. It is the right answer for a
quantity you cannot measure. A fixed calibration error is not such a quantity,
because you can measure it in an afternoon with a ruler, and the picture shows the
price of treating it as though you could not: with that error left in, the
randomised policy reaches 5.3%, well below the 27.5% of the policy that was never
randomised, because training against a wide range of conditions makes a policy act
more decisively and a steady 12 mm lie then carries it confidently to the wrong
place. Measure what you can measure, randomise only what is left, and the same
pair of changes reaches 88.2%, which is better than the policy ever scored in its
own simulator.

---

## 7. It worked last week and does not now

The last symptom destroys mornings. The same cell, the same model file, and a task
that went ten times out of twelve on Thursday is now failing more often than not.
The reflex is to go looking for what changed, and sometimes something did, but
before spending a day on that it is worth knowing how often the answer is that
nothing changed and the difference is in the measurement.

![Eight measured success rates from eight runs of 25 trials each, ranging from 52% to 80%, against a shaded band for all 200 trials together](../../images/starting-your-own-model/when-it-does-not-work/same-weights-different-answer.svg)

One unchanged policy measured eight times with 25 trials each gives 68%, 52%, 64%, 80%, 64%, 76%, 68% and 72%, while all 200 trials together give 68.0%.

Nothing whatever changed between those eight measurements. The weights are the
same file, the arm is the same arm, and only the particular places the object was
put differ, which is what varies between any two evaluations anybody has ever run.
The spread is 28 points, so the week that measured 52% and the week that measured
80% would both be reported to a meeting as a real change and neither is one, while
pooling all 200 trials gives 68.0% with a range of 61.1% to 74.4%, which is the
honest description of this policy. So the cheapest test is also the most
convincing: take last week's file, the one that worked, and run it again today
beside today's. If the old one now scores what the new one scores, the model did
not change and you are looking at the noise in your own trials or at something in
the cell, and if it still scores what it scored, the change is real and in the
model, and you have halved the search for an hour of trials.

![Two bar charts over eight starting seeds, held-out losses nearly identical and success rates between 36% and 82%](../../images/starting-your-own-model/when-it-does-not-work/the-spread-between-seeds.svg)

Eight runs of exactly the same training, differing only in the random number that sets the starting weights, end with held-out losses from 0.00081 to 0.00109 and success rates from 35.5% to 82.5%.

That picture is the other half of the answer. Training is not a function that
gives the same result twice, because the starting weights are drawn at random and
the examples are visited in a random order, and those two things alone move the
success rate of this recipe across 47 points while the held-out loss varies by
only 34% from end to end. A difference of ten points between your model of last
week and your model of this week, both trained by the same recipe with different
seeds, is therefore not evidence of anything. A change is worth reporting only
when it is larger than the spread between seeds, and the only way to know that
spread is to train the same thing three or four times and look.

![Two bar charts, one showing a four-point gain from making both changes at once, the other showing the same four conditions measured separately](../../images/starting-your-own-model/when-it-does-not-work/two-changes-at-once.svg)

Making two changes together takes the success rate from 51.5% to 55.7%, which looks like a modest win from two good ideas, while measuring them separately shows that more attempts was worth 24.9 points on its own and the weight decay cost 8.2.

That leads to the discipline the whole page depends on, which is to change one
thing at a time. It sounds obvious and it is the first thing everybody drops,
because a failed run leaves four promising things to try and one night to try them
in. Here is what dropping it costs, measured. The starting point is a policy
trained on 25 attempts which succeeds 51.5% of the time over four seeds. Two
changes are made together, the training set growing to 200 attempts and a little
weight decay being turned on, and the result is 55.7%, so the person who made both
writes down that both helped a little and carries both forward. They are wrong
about one of them, because more attempts on its own gives 76.4% while the weight
decay on its own gives 43.3%, and paired seed by seed at 200 attempts the decay
made things worse in all four runs. The two-change experiment did not merely fail
to say which change helped, it hid five sixths of the gain the good change was
offering and carried the bad one into every run that followed.

The habit that prevents this is three lines of work per run. Write down before the
run what the one difference is and what you expect. Write down afterwards what
happened, with the seed, the number of trials and the range around the success
rate. And re-run the thing you changed from, in the same session, rather than
comparing against a number in a notebook from three weeks ago, because the cell
has moved since then even if your code has not. That last point is the one people
skip and the one that makes every other number comparable. The table below gathers
the seven symptoms, and each row reads as: if you see the thing in the first
column, do the thing in the second column next, before anything else.

| Symptom | The cheapest test | What it usually means |
| --- | --- | --- |
| The loss does not fall at all | Train on eight examples until the loss reaches nothing | The learning rate is outside its band, the inputs are not on one scale, or something is frozen |
| The loss stops at a floor | Work out the noise in the labels, then try a wider model and a cut learning rate | The floor is in the data, or the rate is too large to settle |
| The held-out loss does not follow | Read the held-out curve from step one, and retrain on a quarter of the data | Overfitting if the curve turned upwards, a split across a gap if it was never low |
| The losses are fine and the arm fails | Run twenty closed-loop attempts | The loss averages over steps, the task is a threshold, and the policy visits its own situations |
| It works only on the trained objects | Hold back whole kinds rather than rows, and scramble a group of readings | The model learned which object it was looking at rather than the property |
| It works in the simulator only | Put each real-world difference into the simulator one at a time | Delay and calibration, usually, rather than anything about the model |
| It worked last week | Run last week's file again today, beside today's | The trials, or the seed, rather than any change you made |

---

## 8. Where to read next

- [Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  is what to read next, because a model that now works has to be run on a real
  machine and judged honestly, and it covers the trials, the ranges and the safety
  layer that sections 4, 6 and 7 lean on.
- [Recipes for models that act and predict](05_recipes-for-models-that-act-and-predict.md)
  is the page this one follows, and the place to go back to once a symptom has
  told you which recipe decision to revisit.
- [Recipes for models that see and understand](04_recipes-for-models-that-see-and-understand.md)
  holds the same for classifiers, detectors and vision-language jobs, where
  section 5's object problem bites hardest.
- [The order of the work](02_the-order-of-the-work.md) arranges the milestones so
  that each of these symptoms appears as early and as cheaply as it can.
- [Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
  is the full treatment of section 3, including how to split robot data along the
  right seam.
- [Evaluation and failure](../../07_learned-models/10_making-models-work-on-an-arm/02_most-used/03_evaluation-and-failure.md)
  is the catalogue page for testing a model on a real arm, with a worked
  evaluation of a real picking job.

---

## 9. Using it in Python

The four most useful checks on this page are short, and this block is all of them,
with comments naming the section each one comes from. It runs as it stands, and
the numbers in the comments are what it printed.

```python
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import torch
from torch import nn
from scipy.stats import beta

torch.manual_seed(0)
policy = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(),
                       nn.Linear(32, 2))

# Section 1. The single-batch test. Eight examples, 2,000 steps, and the loss
# has to reach nothing. If it does not, the fault is in the code, not the data.
x = torch.randn(8, 8)
y = torch.randn(8, 2)
opt = torch.optim.Adam(policy.parameters(), lr=3e-3)
for step in range(2000):
    loss = ((policy(x) - y) ** 2).mean()
    opt.zero_grad()
    loss.backward()
    opt.step()
print(f"single batch: {loss.item():.2e}")          # single batch: 3.49e-15

# Section 1. Nothing reaches a weight whose gradient is missing or all zero,
# so this names every layer the training is not actually changing.
blocked = [name for name, p in policy.named_parameters()
           if p.grad is None or float(p.grad.abs().max()) == 0.0]
print("weights nothing reaches:", blocked)         # weights nothing reaches: []

# The same two lines catch a layer that somebody froze and forgot about.
opt.zero_grad(set_to_none=True)
policy[0].weight.requires_grad_(False)
((policy(x) - y) ** 2).mean().backward()
print("after freezing one layer:",
      [name for name, p in policy.named_parameters()
       if p.grad is None or float(p.grad.abs().max()) == 0.0])   # ['0.weight']

# Section 2. The floor. Record the same situation twice, and the spread between
# the two recordings is the part of the loss no model can remove.
rng = np.random.default_rng(0)
truth = rng.normal(0.0, 0.25, size=4000)
first = truth + rng.normal(0.0, 0.11, size=4000)
second = truth + rng.normal(0.0, 0.11, size=4000)
print(f"floor at least {0.5 * float(np.mean((first - second) ** 2)):.4f}")
                                                   # floor at least 0.0120

# Section 4. A success rate is a count of whole attempts, and this is its exact
# 95% range, which is what says whether two policies really differ.
for successes, trials in ((17, 20), (170, 200)):
    lo = beta.ppf(0.025, successes, trials - successes + 1)
    hi = beta.ppf(0.975, successes + 1, trials - successes)
    print(f"{successes}/{trials} = {100 * successes / trials:.0f}%"
          f" from {100 * lo:.1f}% to {100 * hi:.1f}%")
          # 17/20 = 85% from 62.1% to 96.8%
          # 170/200 = 85% from 79.3% to 89.6%

# Section 7. One change is worth reporting only if it beats the spread between
# seeds, so train the same thing several times before believing anything.
big_x, big_y = torch.randn(256, 8), torch.randn(256, 2)
scores = []
for seed in range(5):
    torch.manual_seed(seed)
    net = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 2))
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    for step in range(300):
        loss = ((net(big_x) - big_y) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    scores.append(loss.item())
print(f"five seeds: {min(scores):.4f} to {max(scores):.4f}")
                                                   # five seeds: 0.6171 to 0.6975
```

The library does two of these four for you and will not do the other two at all.
PyTorch keeps a gradient on every parameter it was asked to track, so the check
for a layer nothing reaches is two lines and catches the commonest invisible fault
on this page, which is a published starting point loaded with its layers locked.
The `scipy.stats.beta` call gives the exact range around a count of successes in
two lines, and the range it gives for 17 successes out of 20 runs from 62.1% to
96.8%, which is most of the space a success rate can occupy, so there is no excuse
for reporting a bare percentage.

What no library will do is the single-batch test or the floor, because neither
produces an error message, neither is part of any training recipe, and both answer
a question the training framework does not know you are asking. The floor in
particular has to come from your own data, since only you can set the same scene
up twice, and the 0.0120 printed above comes from an invented pair of recordings
standing in for that measurement. What you also still have to decide is everything
in section 7, since no library keeps your experiment log, none will stop you
changing two things at once, and nothing in PyTorch knows that the number you are
comparing against was measured three weeks ago in different light.
