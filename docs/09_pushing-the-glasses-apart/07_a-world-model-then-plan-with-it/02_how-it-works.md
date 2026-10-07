# How it works

This page explains what happens inside this solution, part by part. It
follows [what it is](01_what-it-is.md), which states the question the
solution answers and the single idea it rests on.

## Contents

1. [What exists in code, and what is a design](#1-what-exists-in-code-and-what-is-a-design)
2. [What a forward model is](#2-what-a-forward-model-is)
3. [What this model is shown, and what it answers](#3-what-this-model-is-shown-and-what-it-answers)
4. [The push's own frame, and why direction carries no information](#4-the-pushs-own-frame-and-why-direction-carries-no-information)
5. [Ensembles as a measure of ignorance](#5-ensembles-as-a-measure-of-ignorance)
6. [Planning by sampling: the cross-entropy method](#6-planning-by-sampling-the-cross-entropy-method)
7. [Receding horizon: plan several, make one](#7-receding-horizon-plan-several-make-one)
8. [Compounding error over a rollout](#8-compounding-error-over-a-rollout)
9. [Planning a sequence, which only this solution could do](#9-planning-a-sequence-which-only-this-solution-could-do)
10. [A second way — TD-MPC2 off the shelf](#10-a-second-way--td-mpc2-off-the-shelf)

## 1. What exists in code, and what is a design

Before any of the concepts, it is worth saying which parts of this solution are
running code in this repository and which parts are described here and not
written, because this solution is unusual among the six in how much of it
exists.

**The first way is built.** It lives in
`code/src/09_pushing-the-glasses-apart/04-a-world-model/`, it trains on data it
collects itself, and it has been run by the examiner's held-out tables with its
results recorded in that folder's own `results.json`, and set beside the other
five in `code/src/09_pushing-the-glasses-apart/results/README.md`. The model is
`model.py`, what it is shown is `features.py`, and the search and the loop
around it are `plan.py`. Everything this document says about those three files
is a description of code.

**The sequence capability is a design.** The planner that exists chooses one
push at a time: it scores each candidate by the table one push later, makes the
best push, and then looks again. It never asks the model about a push that
follows another push. The *model* is what makes planning a sequence possible,
because its answer is a table and a table is a legal question. But the horizon
in the built planner is one push, and the reason it is one push is given below
under compounding error.

**The second way is a design, and it claims nothing.** It is not wired to this examiner
and it has not been trained or run here, so every number in this document
belongs to the first way. One thing about it is worth settling before anybody
starts: the library this project uses elsewhere ships **TD-MPC**, the earlier
method, and not TD-MPC2. So the second way means fetching TD-MPC2 from its own
project, and the convenience of everything living in one library, which
[imitation from demonstrations](../06_imitation-from-demonstrations/01_what-it-is.md) and the
two SmolVLA solutions enjoy, does not apply here. The two examiner pieces an
off-the-shelf policy needs are no longer the obstacle: the straight-down
rendered view and the path that accepts waypoints were built for [imitation
from demonstrations](../06_imitation-from-demonstrations/01_what-it-is.md), as
`bench/top_view.py` and `Bench.follow`. What is still missing is the wiring and
the training.

## 2. What a forward model is

Start with the object everything else here rests on.

A **forward model** is a function from a situation and an action to the
situation afterwards. Written as a signature it is `(state, action) -> state`.
Nothing more. It does not know what the action was for, it has no preference
between the states it returns, and it cannot be asked what to do. It can only
be asked what happens.

The programming comparison is exact and it is worth taking seriously, because
it explains both the power and the danger. A forward model is a **pure
function**: given the same arguments it returns the same value, it has no side
effects, and — this is the important part — **you may call it as often as you
like without consequences**. That is what makes it a thing you can search
against. Calling the real world is not free: every push risks a glass. Calling
the model is arithmetic. So the model is a cheap, repeatable, consequence-free
copy of an expensive, irreversible world, and a search that would be reckless
against the table is ordinary against the model.

The second half of the comparison is that a pure function returns a value of
the same type it took. `(state, action) -> state` can be composed with itself.
Feed the returned state back in with a second action and you have the state two
actions later. **That composability is the whole of the sequence capability**,
and it is a property of the type rather than of the quality of the fit.

It is worth naming what a forward model is *not*, because the contrast is the
cleanest way to see the six apart. A **policy** is a function from a situation
to an action, `state -> action`. It answers *what should I do*, which is the
question you actually want answered, and it answers it in one pass with no
search. [Imitation from demonstrations](../06_imitation-from-demonstrations/01_what-it-is.md) and
the two SmolVLA solutions are policies. The trade between the two kinds is
discussed at the end of this document, but the short form is that a policy is
fast and narrow, and a forward model is slow and general.

## 3. What this model is shown, and what it answers

Given that shape, the only real design question for the first way is what to put in
the two states and the action, and the answer is: exactly what the arm has, and
nothing else.

**In go thirty-four numbers.** The table's one known kind, as four yes-or-no
columns, one per kind. The pushed glass's height, its width at its widest and
its width at its foot — the three measurements `look()` reports, carrying the
measured error of [telling the glasses
apart](../../08_seeing-the-glasses/11_the-results.md).
The push itself as two numbers: how far across the glass the jaw meets it, and
how far it pushes. And then five slots for other glasses, nearest first, five
numbers each: where it stands relative to the pushed glass, which is two
numbers, how wide it is, how tall it is, and whether there is a glass in that
slot at all. Six glasses on a table is the most the examiner ever draws, so five
others is everyone, and a table with fewer leaves the spare slots empty.

**Out come fourteen numbers.** A displacement for the pushed glass. A
displacement for each of the five other glasses, because a push moves
neighbours as well as its target and a model that only predicted its target
would be blind to the way one glass shoves another. And two yes-or-no answers:
did anything topple, and was the jaw blocked on the way down before it ever
pushed.

Three things about that list are worth dwelling on.

**It is only what the arm has.** No friction, no mass, no tipping rule, no
record from the simulator. Whether a push slides a glass or tips it over is not
given to the model in any form; it is a regularity in the data that the model
either finds or does not.

**The two yes-or-no answers carry most of the value.** A displacement that is a
few millimetres out costs a repeated push. A topple that was not predicted costs
a glass, and nothing in this project can stand a glass back up. So the model is
not really a predictor of displacements with two extras attached; it is a safety
check with a displacement predictor attached, and the training reflects that.
Toppling is rare, and a model trained on rare events will quietly learn to
answer "no" to all of them and be right almost always. The fit therefore weighs
the toppling examples up until the two sides count the same, so that answering
"no" to everything is no longer a cheap way to score well.

**The labels come from two looks, not from the truth.** An example is made by
looking at the table, pushing, and looking again, and the answer recorded is the
difference between the two looks. So the model learns to predict what the
*camera will report*, error and all, rather than what the world will do. This
is the right choice, because what the camera will report is what the planner
will see next, and a model that predicted a truth the arm can never observe
would be predicting the wrong thing.

## 4. The push's own frame, and why direction carries no information

One decision inside those thirty-four numbers deserves a section of its own,
because it is the clearest example in this project of making a problem smaller
by choosing coordinates well.

Every position in the inputs, and every displacement in the outputs, is measured
**in the push's own frame**: one number along the way the jaw moves, and one
number across to its left. Nothing is measured in the table's north and east.

The consequence is that **a push to the north and the same push to the east are
one example rather than two**. A neighbour 30 mm ahead of the pushed glass and
92 mm to its left is the same input row whichever way round the table the jaw
happens to be pointing, so the model sees the two situations as what they are,
which is one situation.

![The same glass and the same neighbour, pushed on two different headings: in the table's north and east the neighbour sits at two different pairs of numbers, and in the push's own frame it sits at one pair, so the two pushes reach the model as a single row.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-pages-the-pushs-own-frame.png)

The justification is a fact about the cell rather than a trick: **the table's
friction is the same everywhere and the same in every direction**. There is no
grain, no slope and no patch that is stickier than the rest. So the direction a
push points in carries no information about what the push will do, and encoding
it would mean asking the model to learn, separately for every heading, a
relationship that does not vary with heading. That is a waste of data in the
most expensive currency this solution has, which is recorded pushes.

The physics comparison is a conserved symmetry. When a system behaves the same
way under a rotation, its description should not change under that rotation
either. Writing the inputs in the table's frame would be writing a description
that changes when the thing being described does not.

There is a second, smaller gift in the same idea. Since the physics has no
preferred direction, it also has no preferred handedness in any way that
matters here: a push and its mirror image, left and right swapped, are both
true pushes. So every recorded push can be used twice, once as it happened and
once reflected, which doubles a small training set with examples that are not
invented but real.

The honest limit is worth stating with it. **The frame only removes the
information it was right to remove.** The reach of the arm and the edges of the
glass zone are emphatically not the same in every direction, and the model knows
nothing about either. That is why the map — where a glass may stand and where
the arm can reach — stays as written-down arithmetic outside the model, and is
checked against the model's predicted table rather than learned.

## 5. Ensembles as a measure of ignorance

The hardest thing to get from a trained model is not an answer. It is an honest
statement that it does not know, and this section is the most transferable idea
in the document.

A plain network always answers. Shown a push unlike anything in its training
data it does not hesitate, decline or warn; it returns numbers in exactly the
same format and with exactly the same confidence as for a push it has seen a
thousand times. That is a serious problem for a planner, because **a search is
an adversary against its own model**. It tries hundreds of candidates and keeps
the one the model likes best, so it systematically finds the places where the
model is wrong in a favourable direction. A model that is right on average and
badly wrong in a few places will have those few places chosen for it.

The fix used here is simple to describe and hard to improve on. **Train the
same network several times from different starting weights on the same data,
and keep all the copies.** The first way keeps five. Where the five agree, the
training data pinned the answer down, which means the model has seen pushes like
this one. Where they disagree, the data did not pin it down, and each copy
filled the gap with whatever its own starting weights happened to lead to. So
**the spread between the copies is a measurement of what the data did not
say**, and it costs nothing but the training of four more small networks.

The planner then uses that spread in a specific and deliberately asymmetric
way. For the displacements it takes the copies' average, because there the
spread is only accuracy and the loop will correct it. For toppling it takes
**the worst copy's chance, not the average**. If any one of the five thinks a
push might tip something over, the push carries that copy's number. A push the
model is unsure about therefore counts as a risky push, and a push gets through
only when all five agree it is safe. The limit is one in a hundred: any copy
giving a push more than a 1% chance of toppling something takes it out of
consideration.

That asymmetry is the right one because the two errors it trades are not
comparable. Refusing a push that would have been fine costs a refusal, which
[the problem](../01_the-problem/01_what-is-asked-for.md) counts as a result rather than a failure. Making a
push that tips a glass costs the glass, permanently, and the arm carries on
working beside it.

The search's adversarial pressure is answered a second time, in a way worth
knowing because it generalises as well as the ensemble does. A search over
thousands of candidates will find a push that looks safe because of a
millimetre of luck in the measurements. So every candidate is also checked
against four copies of the table with every reading moved by about the camera's
error — a millimetre on each position and three on each width — and the worst
topple chance over all five readings is the one that counts. **A hole in the
model narrow enough to be found by luck does not survive being shifted by a
millimetre.** A genuinely safe push does.

![The worst copy's topple chance for one candidate push as the reading of the table is shifted: a genuinely safe push stays under the one-in-a-hundred limit however the reading moves, while a hole in the model is a narrow dip that the measured reading happens to land in and that none of the four shifted readings does, so the push is dropped.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-pages-the-jitter-check.png)

## 6. Planning by sampling: the cross-entropy method

With a model that answers and an honest signal for where it does not know, the
remaining question is how to find a good push, and the answer is the plainest
one available: try a lot of them.

A candidate push here is three numbers: which way the jaw points, where across
the glass it meets it, and how far it travels. **Sampling** means drawing many
candidates at random from the allowed range, asking the model what each one
leads to, scoring every predicted table, and keeping the best. That alone is
called random shooting and it is already a working planner, but it spends most
of its draws in parts of the range that were ruled out by the first round.

The **cross-entropy method** is random shooting with one addition: use the good
draws to decide where to draw next. It runs in rounds. Draw a batch spread over
the whole allowed range. Score them all. Keep the best few — call them the
elite. Work out the average and the spread of the elite, and draw the next
batch from around that average with that spread. Repeat. Each round the cloud
of candidates contracts onto whatever region keeps scoring well, so the method
spends its later draws where the answer is rather than where it started.

The first way runs this with six hundred draws in the first round and three
hundred in each of three more, keeping the best thirty each time, which is
fifteen hundred candidate pushes examined per crowded glass. That sounds
extravagant and costs little, because a candidate push is one row of thirty-four
numbers and each network takes the whole round's rows in a single call. The
measured price for the whole of it is 0.41 seconds of thinking per push the arm
makes.

![An early round spreads its candidates over the whole range and most are struck out by the filters, on the table the model predicts for them; by round four the draws have collapsed onto one small region, and the score is the room still missing on the table plus a small penalty per millimetre pushed.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/10-planning-against-the-model.png)

Two properties make this search the right one here, and both are worth
remembering for other problems.

**It needs no gradients.** It never asks how the score changes when a push
changes by a hair. It only ever asks which of these candidates scored better,
so it does not care whether the score can be differentiated, whether the model
is differentiable, or whether the arithmetic wrapped around the model is. The
map test, the reach test and the ensemble veto are all plain conditions, and a
gradient method would have to be contorted to accept them.

**It copes with a cost that is not smooth.** This matters more. The cost here
has a cliff in it: a push that topples a glass is not slightly worse than one
that does not, it is unacceptable, and a push that lands a glass a hair outside
the zone is not slightly worse than one a hair inside. A method that follows a
slope downhill needs the landscape to have slopes. This one needs only a
comparison, so a cost of infinity for an unacceptable candidate is an ordinary
value it handles without any special arrangement. Given how many of the rules
in this problem are hard limits rather than preferences, that is not a
convenience but the deciding property.

The score itself is deliberately plain arithmetic over the predicted table, and
it is short enough to state in full. Add up, over every glass, how much clear
room is still missing at the end — how far each neighbour's edge reaches inside
the 70 mm that glass needs. Charge a tenth of a millimetre of that missing room
for every millimetre the jaw travels, so that the shortest push which does the
job wins. One more term keeps the arithmetic honest: the model also returns how
likely the jaw is to be blocked on the way down, and a push that is blocked
moves nothing, so the two outcomes are mixed in that proportion — the table as
it already stands, weighted by the chance of a block, against the predicted
table, weighted by the rest.

Three conditions throw a candidate away before it is scored at all. Any copy of
the model giving it more than the topple limit. A predicted table that puts a
moved glass outside the glass zone or outside the arm's reach. And a predicted
movement more than two centimetres longer than the push that caused it, which
is the model answering about something well outside anything it has seen. What
survives is scored, and the best push over all the crowded glasses on the table
is the one that gets made.

## 7. Receding horizon: plan several, make one

The search above returns a push, and the natural next thought is to let it
return several and carry them out in order. That thought is wrong in a specific
way, and the correction is a named idea worth having.

**Receding horizon** means: plan several steps ahead, execute only the first,
then throw the rest of the plan away and plan again from a fresh measurement.
The plan reaches further than the arm ever acts, and its far end keeps moving
away as the arm advances — which is where the name comes from.

The reason it is the right answer to a model that is wrong in small ways is a
matter of where the errors land. A plan several steps deep is built on the
model's prediction of a table the arm has never seen. If the arm carried out all
of those steps, each one would be acting on a table a little further from the
truth than the one before, and nothing would ever notice. If instead the arm
makes only the first step and then **looks**, the model's prediction is replaced
by a measurement, and whatever the model got wrong is deleted rather than
inherited. The plan was still useful: it is what made the first push a push
worth making rather than merely a good push in isolation. But only the part of
it that was acted on could possibly have been wrong, and that part is one push
long.

The programming comparison is given in [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) and applies exactly here. A plan
carried out in full is a loop unrolled into a fixed sequence because you believe
you know how many times it will run. A receding horizon is a loop that re-reads
its state every pass. The state here is the arrangement of the table, the
re-reading is `look()`, and the loop continues while the state says there is
still work to do.

This is also why the solution is forgiving of a mediocre model. The thing a
model has to be good at is **ranking the pushes available right now**, not
describing the future. It can be several millimetres out about where a glass
lands and still reliably pick the better of two pushes, and being several
millimetres out is corrected for free by the next look. That is a much easier
standard than accuracy, and it is the standard this arrangement actually
imposes.

## 8. Compounding error over a rollout

Receding horizon limits the damage a wrong plan can do. It does not make the
plan right, and this section is about why a plan gets less right the further it
reaches.

A **rollout** is what you get by composing the model with itself: feed its
predicted table back in with a second push to get the table two pushes later,
and again for a third. Each call adds its own error, and — this is the part that
surprises people — **each call also starts from a situation its predecessor got
slightly wrong**. So the errors do not merely add. They compound, because a
model asked about a table slightly unlike anything in its training data answers
slightly worse, which produces a table a little further from anything in its
training data, which it answers worse again.

The size of this is easy to feel with the numbers recorded for the first way. Its
README reports a median error of about four and a half millimetres for where a
pushed glass lands, on tables it never trained on. That is a perfectly useful
one-step model. If that error simply accumulated, a plan rolled three pushes
deep would judge the table it ends on to be where it is not by some thirteen
millimetres — and the clearances this whole problem turns on are tens of
millimetres.
Compounding makes it worse than that straight sum, not better. **So a model
that is good at one step can be useless at five**, and the quality of the
one-step fit says almost nothing about it.

This is why the built planner's horizon is one push. It is the honest horizon
for a model trained the way the first way's is: every training example is a single
push, so the model was never asked to be right about a table that one of its own
predictions produced.

**What is done about it is to train against multi-step rollouts rather than
only single steps.** Instead of scoring the model on how well it predicts the
next table from a measured table, roll it forward several pushes from a measured
table and score it on how well the whole sequence matches what really happened
over those pushes. The error then has somewhere to go: the fit is penalised for
predictions that are plausible one step out and drift two steps out, so it
learns to produce tables that it can itself handle as input. This is the
standard remedy in the learned-world-model literature and it is exactly what
the second way does by construction, which is one of the clearest reasons to want
the second way at all.

Two cheaper habits help as well, and the first way uses both. **Keep the horizon as
short as the task allows**, because the compounding is a function of depth.
And **collect training data from the planner itself**, not only from random
pushes, so that the tables the model sees during training are tables a planner
would really reach. The first way's second round of data collection does precisely
that: the first model plans, the planner finds the pushes where that model is
wrong in its own favour, those pushes are really made, and what really happened
goes into the training set. That fills exactly the holes the search is going to
exploit. A quarter of that round is still drawn at random, so the model keeps
seeing pushes the planner would never choose and does not forget what they do.

## 9. Planning a sequence, which only this solution could do

Everything so far has been machinery. This section is the reason the machinery
is worth having, and it is the one capability that is this solution's alone.

Consider a table where glass A is crowded and there is nowhere to push it. Every
direction either runs into glass B, leaves the glass zone, or puts A outside the
arm's reach. Every solution that chooses one push at a time, judged by the table
one push later, will correctly report that no push helps and refuse. And every
one of them is wrong, because the answer is to push B first — not because B
needed moving, and not because moving B makes any glass grippable, but because
moving B opens the route A needed.

**A push whose only value is what it allows the next push to do** is invisible
to a method that scores pushes one at a time. It scores badly on its own terms:
it clears no room and it spends a push. Only a method that can ask *and then
what* can see its value, and asking *and then what* requires a function that
returns a table.

![Pushing one glass at a time, where each push has to leave the glass it moved with full room by itself, takes four pushes on a real four-glass layout; choosing the best pair together takes two, and choosing the second of that pair needs to know where the first one lands.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/10-when-a-sequence-beats-one-at-a-time.png)

The extension to the built planner is small, and it is worth describing
precisely so that it is clear how little the model has to change. The search
currently draws three numbers per candidate. A two-push search draws six — a
first push and a second — rolls both through the model in turn, and scores the
table at the end of the pair. The ensemble veto applies at every step rather
than only the last, so a sequence that topples something halfway through is
thrown away whatever it achieves afterwards. Only the first push of the winning
pair is made, and then the arm looks again, which is the receding horizon doing
exactly its job. Nothing about the model changes at all. What changes is how
many times it is called, and the cost of the search grows quickly with depth,
which is the real reason to want the shortest horizon that can see the answer.

Two honest qualifications belong here, and they matter.

**The depth that is useful is small.** Compounding error sets an upper limit on
how far a rollout can be trusted, and for the first way's model that limit is low.
Two pushes is defensible, three is optimistic, and anything deeper is planning
against a story rather than a prediction.

**On this examiner a sequence saves pushes rather than rescuing runs.** The cases
where a sequence wins outright — where a one-at-a-time planner has to refuse and
a two-deep planner succeeds — are real but uncommon on four to six glasses, and
the more usual gain is finishing the same table in fewer pushes. That is worth
something here for a precise reason rather than a general one: **touching a
glass is the only step in this problem that can topple one**, so a run that
spends four pushes instead of six has taken two fewer chances of the single
failure that cannot be undone. It is not worth something because the arm is
short of time.

## 10. A second way — TD-MPC2 off the shelf

There is a second way to build this solution: take a model somebody else
maintains instead of writing one. **TD-MPC2** has the same shape — learn what
happens, search over actions against what was learned, act on only the first —
and differs in what the model predicts.

The model written here predicts the next table directly, in the quantities the
arm measures, so every number in it has a name and a unit a person can check.
TD-MPC2 encodes the situation into a vector of its own choosing, whose entries
mean nothing to anybody, learns how that vector changes under an action, and
plans there without ever converting back into positions and widths. The
hand-built one is inspectable and trains in minutes on an ordinary processor;
the off-the-shelf one is stronger, is trained against multi-step rollouts by
construction, and is maintained by people who do this for a living, but it
cannot be read and it wants an accelerator.

**It is not built, so it has no scorecard.** Comparing the two would measure
whether building the model by hand was worth it, which is the only reason to
carry both: if a maintained implementation clears tables no better than five
small networks trained in half an hour on a laptop, the cell is narrow enough
that the hand-built model was the right call.

← [What it is](01_what-it-is.md) · [The code](03_the-code.md) →
