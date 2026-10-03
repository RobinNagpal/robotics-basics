# When it does not work

The page before this one,
[recipes for models that act and predict](05_recipes-for-models-that-act-and-predict.md),
gave a starting recipe for each family of model that makes a robot move, and
every one of those recipes ends in the same place, which is you typing a
training command and waiting. This page is about what you do when the waiting is
over and the thing does not work. That is not a rare accident, it is the normal
first outcome, and saying so plainly is part of this page's job, because a person
who believes that a recipe followed properly produces a working model will take
their first failure as proof that they are not clever enough, when what they have
actually reached is the ordinary place from which everybody starts the real work.

The page is organised by symptom rather than by cause, because a symptom is what
you actually have in front of you. You have a curve that did not fall, or two
curves that parted company, or an arm that knocked a mug over. Each section below
takes one symptom and answers three questions about it in the same order: what
the symptom means, what the cheapest test is that confirms the cause or rules it
out, and what to change once you know. The tests are ordered by what they cost,
so the first thing suggested is always the one you can do in an hour, and
collecting more data, which is the expensive answer everybody reaches for first,
is suggested only where it is really the answer.

It is written for somebody who has read the earlier pages of this chapter, and
in particular [the order of the work](02_the-order-of-the-work.md), which sets
out the milestones this page assumes you were working through when the trouble
started. Two pages elsewhere in the book own the machinery that this page only
diagnoses against, and it links to them rather than explaining them again.
[Overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
owns what a held-out set is, why it has to be split along the right seam, and
what dropout, weight decay and early stopping do.
[Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
owns how a model is judged on a real arm, and in particular why a
**success rate**, which is the fraction of whole attempts that worked, needs
many trials before it means anything.

Every number quoted below is worked out and printed by
`docs/diagrams/starting_your_own_model_6.py`. All the data in it is simulated, and
there are three simulated jobs. In the first, an arm's gripper has to be driven
to an object lying on a table, a written controller plays the demonstrator, its
commands are recorded with noise, a network is trained to copy them, and the same
weights are then run in closed loop so that there is a task success rate as well
as a loss. In the second, two demonstrators go round one obstacle on opposite
sides. In the third, a model has to say how wide to open a gripper for each kind
of object. The jobs are made up, but the networks, the training steps, the
roll-outs and the counted trials are all real, written in NumPy.

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

The first symptom is the one you meet soonest, usually within a minute of
starting the run that the recipe told you to start, and it is the flat line. The
loss wobbles about near the value it had at the beginning and never goes
anywhere. What this means is simple and worth saying clearly, because it saves
people from a week of collecting data: a flat loss is never a sign that you have
too few examples. A network with enough weights can memorise whatever you give
it, so if it is not even able to drive the error down on the examples it is being
trained on, then something is wrong with the arrangement rather than with the
data, and more data will not touch it.

![Four loss curves against training step on a log scale, three of them flat near 0.02 and one falling to 0.001](../../images/starting-your-own-model/when-it-does-not-work/loss-does-not-fall.svg)

The same network and the same 8,000 recorded commands give a falling curve at a learning rate of 0.003 and a flat one at 1.0, at 0.000001, and when the labels are shuffled.

The **learning rate** is the number that says how big a step the training takes
down the slope of the loss, and the page on
[gradient descent](../03_how-training-works/02_gradient-descent.md) explains what
it is a step of. Set it to 1.0 and the run ends at 0.02468 on held-out data, set
it to 0.000001 and it ends at 1.60748, and set it to 0.003 and it ends at
0.00105. The fourth curve is the interesting one, because its learning rate is
the good one and it is still flat: its labels were shuffled, so that each set of
readings is paired with some other attempt's command, and there is nothing to
learn. It settles at 0.02568, which is no better than answering zero every time,
and the number to compare against is 0.024181, the plain spread of the recorded
commands.

That comparison is the first thing to put in place, because a loss number by
itself tells you nothing at all. Work out what the loss would be if the model
answered with the average of the training labels every time, and write that
number down before you start. A run that cannot beat it has learned nothing,
whatever the curve looks like.

![Three loss curves on eight examples, two falling below a thousandth of a millionth and one flattening at 0.00036](../../images/starting-your-own-model/when-it-does-not-work/single-batch-test.svg)

Eight examples and 2,000 steps: the network as written reaches 8.8 at the eighth decimal place, the same network with its first two layers frozen by accident stops at 0.00036.

That picture is the cheapest test there is, and it is worth an hour of anybody's
time. Take eight examples, throw the rest away, and train on those eight over and
over until the loss on them reaches nothing. A network that is wired up properly
will do this every time, because eight examples is a thing any network can
memorise, and the loss falling to 8.8 at the eighth decimal place in the picture
is what success looks like. A network that cannot do it has a fault you can find
without any data at all. The red curve is a network whose first two layers were
frozen by accident, which happens whenever somebody loads a published starting
point with its layers locked and forgets to unlock them, and it is invisible in
an ordinary run because the model still trains, just badly.

The shuffled-label curve passing this test is the other half of the lesson,
since it reaches nothing as well. Memorising eight examples does not need the
labels to mean anything, so the single-batch test proves that your code can
learn and proves nothing whatever about your data. That is exactly why it is
useful, because it splits the possible faults into two piles, and you then only
have to search one of them.

![Held-out loss against learning rate across ten powers of ten, flat and high at both ends with a dip in the middle](../../images/starting-your-own-model/when-it-does-not-work/learning-rate-band.svg)

Across learning rates from a ten-millionth to three, only the band from 0.00032 to 0.032 beats answering with zero, and the best value in this short run of 1,200 steps is 0.032 at a held-out loss of 0.00167.

If the single-batch test passes, the usual cause is that the learning rate is
outside its band. The band in the picture is about a hundred times wide from end
to end, which sounds generous until you notice that the rates being tried span
ten powers of ten, so picking one at random leaves you outside it far more often
than inside. Below the band the loss falls so slowly that a run of a few thousand
steps looks flat, and above it the steps overshoot so badly that the model never
settles anywhere, and those two very different faults produce the same flat line.
The way to tell them apart is to try a rate ten times smaller and a rate ten
times larger and see which direction helps.

![Two loss curves beside a bar chart of the spread of each input column, one set of bars reaching 138 and the other all at 1](../../images/starting-your-own-model/when-it-does-not-work/input-scale.svg)

Four of the eight inputs written in millimetres instead of metres leave the run at a held-out loss of 0.89920, and subtracting each column's average and dividing by its spread brings the same run to 0.00105.

The last common cause is that the inputs were never put on one scale. In the
picture the four position readings arrive in millimetres while the other four
readings are around one, so their spreads are 138, 148, 125 and 134 against
0.289, 0.0494, 0.586 and 0.997. The network is not able to use a learning rate
that suits both, so it ends at 0.89920 instead of 0.00105, a difference of nearly
a thousand times from a units mistake that produces no error message anywhere.
Subtracting each column's average and dividing by its spread fixes it in one
line, and the page on
[normalisation and stability](../04_making-training-work/02_normalisation-and-stability.md)
explains why the arithmetic inside the network needs this. Once the loss is
falling, the next question is how far down it goes.

---

## 2. The loss falls to a floor well above zero and stops

The second symptom is the one that follows a fixed version of the first. The loss
falls for a while, flattens out at some value that is clearly not zero, and stays
there however long you leave the run going. What this means is quite different
from a flat loss, because the model is learning, and the question is only whether
the floor it has reached is a fault or the right answer. Most people assume it is
a fault and reach for a bigger model, and most of the time they are wrong, so
this section is mostly about finding the floor before trying to beat it.

![Training and held-out loss falling together over 6,000 steps and flattening just above a dashed line marking the noise](../../images/starting-your-own-model/when-it-does-not-work/a-floor-not-a-bug.svg)

Both curves flatten at about 0.00098 against a dashed line at 0.00061, which is the variance of the noise in the recorded commands themselves.

The demonstrator in this simulated job is sloppy when the gripper is far from the
object and careful when it is close, so the command recorded at each step is the
right command plus noise whose spread grows with the distance still to go. The
variance of that noise is 0.00061, and no model can ever go below it, because the
part of the label that is noise is different in every recording and nothing in
the readings predicts it. The run ends at 0.000824 on training data and 0.000978
on held-out data, which is 1.6 times the noise, so almost everything left in the
loss is noise rather than error, and the remaining 0.4 is all that any amount of
work could win back.

The cheapest way to find that floor on real data is to record the same situation
twice. Set the scene up, take a demonstration, set the same scene up again as
exactly as you can, take another demonstration, and measure how much the two
differ. Half the variance of that difference is a lower limit on the loss, and it
is nearly always much larger than people expect, because two human demonstrations
of the same pick are not the same at all.

![Training and held-out loss against hidden width from 1 to 128 on a log scale, dropping steeply to width 4 and then flat](../../images/starting-your-own-model/when-it-does-not-work/floor-and-model-size.svg)

Making the hidden layers wider moves the held-out loss from 0.024602 at width 1 to 0.000896 at width 4, and then from 0.000896 to 0.000879 across the whole range from width 4 to width 128.

Once you have a floor you can ask whether the model is the thing holding you
above it, and the test is to make the model bigger and look. Width 1 is far too
small to represent the job and scores 0.024602, which is the answering-with-zero
number from section 1, and width 2 scores 0.008368. By width 4 the model is at
0.000896, and the thirty-two-fold increase from there to width 128 buys 0.000017,
which is nothing. This is worth doing before anything else because it is one
number to change and one run to wait for, and because the answer is so often that
the model was never the problem.

![Sixty demonstrated paths past a round obstacle, half going above and half below, with a single black line passing through the obstacle, beside two bars of loss](../../images/starting-your-own-model/when-it-does-not-work/two-ways-round.svg)

Thirty-six demonstrations go above the obstacle and twenty-four below, every one of them clearing its edge by at least 53.3 mm, while the single path that least squares gives passes 31.4 mm inside that edge.

The floor that no model size will move is the one that is in the data, and the
commonest form of it on a robot is in that picture. Two demonstrators were asked
to move past an obstacle and one went above it while the other went below, so for
the same readings the recorded answer is sometimes one thing and sometimes the
opposite. A model trained to make its squared error small cannot pick a side,
because the sum of the squared distances to both sides is smallest in the middle,
so it answers with the average, and the average is a path straight through the
obstacle. The loss confirms it, since the best single answer scores 0.006573
against 0.000133 for a model fitted to one side alone, which is 49.3 times worse,
and the model has done exactly what it was asked to do.

The way to tell this cause from the others is to look at the examples where the
error is largest and ask whether two different answers appear for nearly the same
readings. If they do, the fixes are to narrow the job until one answer is right,
to add something to the readings that says which way this attempt goes, or to use
a kind of model that can hold more than one answer at once, which is what
[diffusion and flow policies](../12_models-that-act/02_diffusion-and-flow-policies.md)
are for.

![Two held-out loss curves that lie on top of each other until step 3,000, where one drops below the other and stays there](../../images/starting-your-own-model/when-it-does-not-work/lr-too-high-to-settle.svg)

The same run with the learning rate held at 0.01 ends at 0.001213, and with the rate cut to 0.001 at the half-way point it ends at 0.000788.

The last cause of a floor is the cheapest of all to remove. A learning rate large
enough to make early progress is too large to settle at the end, because each
step jumps further than the distance left to go, so the loss bounces about above
the place it is trying to reach. Cutting the rate by a factor of ten part way
through takes this run from 0.001213 to 0.000788, which is a third of the loss
removed by one line of code, and it costs nothing but the decision of when to cut.
Try that before you conclude anything about your data or your model size. A floor
is at least an honest number though, and the next symptom is the one where the
number itself has stopped being honest.

---

## 3. The training loss falls and the held-out loss does not follow

The third symptom is the one everybody has been warned about and few people
recognise in time. The training loss keeps going down, run after run, while the
loss measured on examples that were kept back stops going down or turns and
climbs. What this means is that the model is learning the particular examples
rather than the pattern in them, which is called **overfitting**, and
[overfitting and generalisation](../04_making-training-work/01_overfitting-and-generalisation.md)
explains the mechanism, why it happens and what early stopping, dropout and
weight decay do about it. This section is about what to do when you see it in
your own run, and in particular about telling it apart from the thing that looks
exactly like it and is not it.

![Two loss curves over 20,000 steps, the training one falling steadily while the held-out one bottoms out and turns upwards](../../images/starting-your-own-model/when-it-does-not-work/train-and-held-out-part.svg)

Six demonstrated attempts and a network of width 128: the held-out loss reaches its best value of 0.00458 at step 11,000 and climbs to 0.00870 by step 20,000, while the training loss falls to 0.000009.

In that run the two numbers finish a factor of 971 apart, and the held-out loss
ends at 1.90 times its own best value, so a person who had watched only the
training curve would have stopped at step 20,000 with a model that was almost
twice as bad as the one they had at step 11,000 and thrown the good one away. The
first thing to do, therefore, costs nothing: score the held-back examples every
few hundred steps, keep a copy of the weights whenever that score reaches a new
low, and finish with the copy rather than with the last weights. This is early
stopping, the other page explains it, and it converts this symptom from a
disaster into a mild waste of electricity.

![Training and held-out loss against the number of demonstrated attempts, from 3 to 200, with the gap between them shaded and closing](../../images/starting-your-own-model/when-it-does-not-work/would-more-data-fix-it.svg)

The same network trained on more attempts closes the gap between the two losses from 23,509 times at 3 attempts, to 7.2 times at 12, to 2.4 times at 50, to 1.2 times at 200.

The second thing to do is to find out whether more data would fix it, and you can
find that out from the data you already have. Train the same model on a quarter of
your attempts, on a half, and on all of them, and plot the held-out loss against
the number of attempts. A curve still falling steeply at the right-hand end, as
this one is between 3 and 50 attempts, says that collecting more is worth the
effort. A curve that has flattened says it is not, and that something else is
the limit. This is the one measurement that honestly answers the question
everybody asks first, which is whether to go back and record more demonstrations,
and it costs three short training runs rather than three weeks of recording.

![Four loss curves over one run, scored against the training set and three different held-out sets, each flattening at a different height](../../images/starting-your-own-model/when-it-does-not-work/which-held-out-set.svg)

One run scored four ways: on its own training rows it reaches 0.00074, on rows taken out of the training attempts 0.00074 as well, on whole attempts it never saw 0.00205, and on attempts where the object lies further out than any it trained on 0.01154.

Now for the thing that looks like overfitting and is not. The purple curve is a
held-out set made by taking rows out of the training attempts at random, which
leaves nearly identical moments of the same recording on both sides of the split,
and it sits exactly on top of the training curve. Anybody using it would report a
score of 0.00074 and believe their model generalised, and the other page explains
at length why this kind of split lies. The red curve is the opposite mistake. Its
held-out attempts have the object further out on the table than anything in the
training set, so that loss is high from the very first step, best at 0.01100 and
ending at 0.01154, and it never comes down.

Read the shape of the held-out curve rather than its final height, because the
shape is what names the cause. A curve that falls with the training curve and
then turns upwards is overfitting, and early stopping plus more attempts is the
answer. A curve that was never low, that starts high and stays high and barely
responds to training at all, is not overfitting but a held-out set that asks a
different question from the training set, and no amount of regularisation will
help, because the model is being asked about a situation nobody showed it. The
fix there is either to record the missing situation or to change what you claim
the model does. All of this, though, is still about a number, and the next
symptom is the one where all the numbers are good.

---

## 4. Both losses look fine and the robot still fails the task

The fourth symptom is the one that confuses people most, and unlike the three
above it it belongs to robots rather than to machine learning in general. The
training loss fell, the held-out loss followed it down, the two curves agree, the
flattening happened near the noise floor that section 2 told you to work out, and
by every number on your screen the model is finished. Then you run it on the arm
and it misses the object half the time. What this means is not that something has
gone wrong since you measured, but that the loss and the task were never the same
question, and the rest of this section measures how far apart those two questions
are.

![A scatter of sixty policies, held-out loss against success rate, with a tight cluster at the left whose successes run from 40% to 98%](../../images/starting-your-own-model/when-it-does-not-work/loss-is-not-the-job.svg)

Sixty policies trained on the same recorded commands and scored twice: two of them have held-out losses of 0.00103 and 0.00107, four parts in a hundred apart, and succeed 81% and 50% of the time.

The script trains those sixty policies on the same 8,000 recorded commands,
changing only the width of the network, the starting seed and how long it trains,
and then scores each one twice. The first score is the held-out loss on recorded
commands. The second is a success rate from 300 attempts in which the policy
drives the arm itself and the attempt counts as a success if the gripper finishes
within 15 mm of the object. Across all sixty the two scores agree well, with a
rank correlation of -0.950, and a **rank correlation** is a number between -1 and
+1 saying how closely one ordering matches another, so -0.950 means that sorting
by loss very nearly reverses the sorting by success. That agreement is exactly
why people trust the loss.

The agreement comes entirely from the bad policies. Eighteen of the sixty trained
all the way down to the floor, and their held-out losses lie between 0.00079 and
0.00140, a spread of less than a factor of two, while their success rates run
from 40.3% to 98.3%. Within that group the rank correlation falls to -0.806, and
the policy with the lowest loss of all succeeds 93.3% while the best policy of the
sixty succeeds 98.3% with a slightly worse loss of 0.00089. So once every
candidate has trained properly, which is the only situation in which you are
actually choosing between them, the loss has almost stopped telling you which one
to ship.

![Two bands of gap-to-target against step with a dashed tolerance line, beside two histograms of the gap at the last step](../../images/starting-your-own-model/when-it-does-not-work/what-the-arm-does.svg)

The two circled policies finish a median of 7.4 mm and 14.9 mm from the object, and since the tolerance is 15 mm, the second one's attempts land astride the line that decides the attempt.

The first reason for the gap is in the shape of those two measurements. The loss
is an average, taken over all forty steps of every attempt and over every
attempt in the held-out set, so a small error at a step where the gripper is a
quarter of a metre away counts exactly as much as the same error at the last
step. The task is not an average at all. It is a threshold, applied once, at the
end of each attempt, and the two policies in the picture differ almost entirely
in the last ten steps, where one settles at 7.4 mm and the other wanders back out
to 14.9 mm. Ninety per cent of the attempts of the better policy finish inside
22.0 mm against 26.8 mm for the worse one, and the whole difference in success
rate comes out of a few millimetres on one side of one line.

![Two scatter plots of success rate against error, the left against error on the demonstrator's states and the right against error on the policy's own states](../../images/starting-your-own-model/when-it-does-not-work/states-it-reaches-itself.svg)

Measured on the situations the demonstrator reached, these eighteen policies have errors within a factor of four of each other, and measured on the situations they drive themselves into, the errors spread over a factor of ten and track the success rate more closely.

The second reason is deeper, and it is the one worth carrying away from this
page. The held-out loss asks a question about the demonstrator's situations: given
a moment the demonstrator was in, would the model have sent the demonstrator's
command? The task asks a different question: with the model driving from the very
first step, does the arm end up in the right place? Those differ because the
model's own small errors move the arm into situations slightly away from the ones
the demonstrator ever reached, where the model has seen nothing and so errs a
little more, which moves it further still. In this simulation the error measured
on the policy's own situations is between 2.29 and 12.3 times the error measured
on the demonstrator's, and it ranks the policies by success better, at -0.942
against -0.862. The page on
[behaviour cloning and action chunks](../12_models-that-act/01_behaviour-cloning-and-action-chunks.md)
explains why copying a demonstrator has this property built into it, and what
chunking the actions does about it.

So the cheapest test for this symptom is simply to run the thing, because no
measurement made on recorded data will show it. Twenty closed-loop attempts take
an afternoon and are worth more than any number of held-out losses. What to
change, once you have confirmed it, is not the training settings, since section
1's work is already done. It is either to record demonstrations that start from
the situations the policy drives itself into, so that it learns how to come back,
or to move to a model that commits to a chunk of future commands at once, both of
which that page covers.

![Measured success rates with their 95% ranges at 10, 20, 50, 100, 200 and 400 trials, for two policies, the ranges overlapping at the left and separating at the right](../../images/starting-your-own-model/when-it-does-not-work/how-many-trials.svg)

Ten trials give 80.0% and 70.0% for two policies that really differ by about 28 points, with ranges of 44.4% to 97.5% and 34.8% to 93.3% that overlap almost completely, while 400 trials give 84.2% and 56.2% with ranges that do not touch.

One warning belongs with this, because the measurement that replaces the loss is
far noisier than the loss was. A success rate is a count of whole attempts, so a
handful of attempts says almost nothing, and the picture shows the two policies
of this section measured at six different numbers of trials. At ten trials the
better policy scores 80.0% and the worse one 70.0%, in the wrong order by nearly
nothing, and their 95% ranges overlap over almost their whole width.
[Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
works through why that is, how such a range is worked out, and how many trials
different comparisons need, and this page simply takes the result: do not report
a success rate from twenty trials and do not believe one.

---

## 5. It works on the objects it was trained on and on nothing else

The fifth symptom usually arrives on the day you show somebody the robot. It
picks up all six of the objects it was trained on, every time, and then somebody
puts a seventh object on the table and it fails completely. What this means is
that the model found an easier way to answer than the one you had in mind. It did
not learn the property you cared about, it learned which of your six objects it
was looking at, and since that is enough to answer every question in your training
set and in your held-out set, nothing you measured could have told you.

The simulated job here makes that concrete. Each kind of object has a shape and a
colour, and the right gripper opening, between 23.5 and 78.5 mm, depends on the
shape alone. The readings a picture gives are four noisy measurements of the
shape and three crisp measurements of the colour, and an answer counts as right
if it is within 4 mm. Because the colour readings are the crisp ones, reading the
colour and looking up a remembered answer is the more accurate strategy, and the
model finds it.

![A bar chart of twelve objects, the first six all at 100% in blue and the last six at nearly zero in red](../../images/starting-your-own-model/when-it-does-not-work/per-kind-of-object.svg)

The same weights get 99.9% of the openings right on the six kinds of object they trained on and 0.7% right on six kinds they never saw, even though every opening is decided by a shape the readings describe perfectly well.

Those two numbers, 99.9% and 0.7%, are what a learned lookup table looks like
from outside. Nothing is broken, the model is answering confidently, and on the
training objects it is better than you had any right to expect. The failure is
total rather than gradual, which is itself a clue, because a model that had
learned the shape and merely learned it imperfectly would be somewhat right on a
new object rather than entirely wrong.

![Three bars: 100% for rows held back from the same kinds, 49.8% for two kinds held back, and 0.4% for kinds nobody collected](../../images/starting-your-own-model/when-it-does-not-work/split-by-kind.svg)

Holding back rows from the same six kinds gives 100.0%, holding back two whole kinds gives 49.8%, and the truth on six kinds nobody ever collected is 0.4%.

The cheapest test is in the middle bar, and it costs one extra training run. Do
not hold back rows, hold back kinds: train on four of your six objects and score
on the two you kept out. The left-hand bar is what an ordinary random split
reports, and it reports perfection, because rows of the same object sit on both
sides of it. The middle bar reports 49.8% and is the warning. Note also that it
is still far too kind, since the real answer on objects nobody collected is 0.4%,
and the reason is that two held-back kinds that happen to resemble the four
trained ones still flatter the model. So treat a held-out-kind score as an upper
limit on what will happen, never as a prediction, and hold back as many kinds as
you can spare.

![A line chart of success on new kinds against how many kinds the same 1,800 pictures are spread over, rising from 4% to 39%](../../images/starting-your-own-model/when-it-does-not-work/variety-not-volume.svg)

The same 1,800 pictures spread over more kinds of object: one kind gives 4% on objects it never saw, four kinds give 14%, nine give 20% and twelve give 39%, while the score on the kinds it did train on stays at about 100% throughout.

That picture is the answer to the question everybody asks next, which is whether
to collect more pictures. The total number of pictures is held at 1,800 in every
run, and only the number of distinct objects they are spread over changes, so any
difference between the points is bought with variety alone and costs nothing in
recording time. Going from one kind to twelve takes the score on new objects from
4% to 39% with no extra data at all, and the four runs drawn as faint dots behind
each point show how much it still depends on which objects you happen to have.
Collecting more pictures of the objects you already own does nothing here, which
is why this measurement is worth making before any recording session.

![Three bars showing the score falling when the colour readings or the shape readings are scrambled, beside four bars comparing a model trained with and without the colour readings](../../images/starting-your-own-model/when-it-does-not-work/which-reading-did-it-use.svg)

Scrambling the colour readings on objects the model trained on drops it from 99.7% to 53.7%, which proves it was using them, and training again with those readings left out gives 98.5% on the trained kinds and 59.7% on kinds it never saw.

The left-hand panel is the test that names the shortcut, and it needs no
retraining at all. Take your held-out examples, shuffle one group of readings
between them so that each example keeps its own shape readings and gets somebody
else's colour readings, and score the model again. The opening cannot possibly
depend on the colour, since the job was built so that it does not, and yet
hiding the colour costs 46 points, which is proof that the model was leaning on
it. The right-hand panel is the repair, and it is the one that makes this section
worth reading: the same model trained with the colour readings left out of the
input entirely gives up 1.2 points on the objects it knows and goes from 1.2% to
59.7% on objects it has never seen. Taking a shortcut away is often worth more
than any amount of extra data, and the page on
[where the data comes from](../../07_learned-models/01_what-models-are/05_where-the-data-comes-from.md)
describes how robot datasets come to contain such shortcuts in the first place.
