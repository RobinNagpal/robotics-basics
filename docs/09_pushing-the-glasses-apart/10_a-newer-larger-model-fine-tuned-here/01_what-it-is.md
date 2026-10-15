# What it is

This page explains the seventh solution. It is for a reader who has read the
chapter on [solution 6](../09_the-same-model-fine-tuned-here/01_what-it-is.md).
Solution 7 is solution 6 with one change: a newer and larger borrowed model.
**This solution is still being measured.** Its code is written and runs. Its
three fits and its scoring run are not finished. So this chapter has no score
yet, and it says so wherever a score would go.

The code is in the project's
[`07-evo1-fine-tuned/`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/README.md)
folder. It is not yet copied into this repository.

## Contents

1. [The model, Evo-1](#1-the-model-evo-1)
2. [Why add it](#2-why-add-it)
3. [What is fitted](#3-what-is-fitted)
4. [Two differences the model forces](#4-two-differences-the-model-forces)
5. [What it reuses](#5-what-it-reuses)

## 1. The model, Evo-1

This section says what the new model is, before we ask why it is here.

[Evo-1](https://arxiv.org/abs/2511.04555) is a vision-language-action model.
It reads a picture and a sentence, and it answers with a run of jaw waypoints.
This is the same kind of model as SmolVLA, which solutions 5 and 6 use.
[Solution 5's chapter](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#1-a-model-that-sees-is-told-and-acts)
explains this kind of model.

Evo-1 was published in November 2025. It has about 775 million numbers inside
it. SmolVLA has about 454 million. So Evo-1 is about 70% larger and about two
years newer. Its picture-and-text half is a general model called InternVL3-1B.

Like SmolVLA, Evo-1 draws its answer from random noise, by [flow
matching](../08_a-foundation-model-as-it-downloads/03_how-it-works.md#how-the-model-draws-its-answer-flow-matching).
So every score for this solution will need a spread.

The next section says why a second borrowed model is worth adding.

## 2. Why add it

The model is now known. This section says what question it answers.

Solutions 5 and 6 both racked about 50 glasses. Plain geometry racked 107. One
possible reason is that SmolVLA is too small or too old. Solution 7 tests that
reason.

It changes the model and **holds everything else still**. So the gap between
the scores of solutions 6 and 7 shows what the model is worth, and nothing
else. Solution 6's chapter planned this test with a different large model, in
[a second way](../09_the-same-model-fine-tuned-here/03_how-it-works.md#7-a-second-way--the-same-fine-tune-on-a-larger-model).

The next section says which part of Evo-1 is trained here.

## 3. What is fitted

The test holds everything still except the model. This section says how the
model is trained here.

[Solution 6's chapter](../09_the-same-model-fine-tuned-here/03_how-it-works.md#1-fine-tuning--continuing-somebody-elses-training)
explains fine-tuning. Solution 6 trains a small low-rank correction. Evo-1
does not need that trick. Its authors define two training stages:

1. In the first stage, the picture-and-text half is **frozen**. Frozen means
   its numbers are not changed. Only the action half learns.
2. In the second stage, every number learns.

Solution 7 uses the first stage. So 122.0 million of the 775.2 million numbers
are fitted. This is the model's own cheap path. It was not invented to fit a
laptop.

The training effort is solution 6's effort: 1000 steps, batch 4, learning rate
0.0001. More training for the newer model would measure the training too.

The next section names two ways the model is not the only difference.

## 4. Two differences the model forces

The fitting copies solution 6. This section lists two things that could not be
copied.

**The picture is larger.** The cell's top view is 384 pixels square. Evo-1
accepts only 448 pixels, because its checkpoint expects a fixed number of
picture pieces. So the view is scaled up. Scaling up adds no detail. It only
costs more work.

**The answer is wider.** Evo-1 always answers 24 numbers for each waypoint,
because it was built for many robots. This cell needs 6. The model's own
last step trims the other 18.

Both are recorded because they are real differences from solution 6. Neither
should help the score.

The next section lists what solution 7 shares with solutions 5 and 6.

## 5. What it reuses

The differences are short. This section lists what is shared, which is the
rest.

- **The demonstrations** are solution 6's own folder. They are read, not
  recorded again. So the two solutions share even the simulator's randomness.
- **The reading of an answer as jaw waypoints** is solution 5's own function.
  It is imported, not copied.
- **The loop over a table** is solution 5's own loop, also imported.
- **The test** is the same 50 held-out tables, with 251 glasses.

The model runs on this Mac with no change to its code. Three settings were
enough. [What it needs](02_what-it-needs.md) gives them, with the measured
costs.

← [The same model, fine-tuned here — questions and answers](../09_the-same-model-fine-tuned-here/07_questions-and-answers.md) · [What it needs](02_what-it-needs.md) →
