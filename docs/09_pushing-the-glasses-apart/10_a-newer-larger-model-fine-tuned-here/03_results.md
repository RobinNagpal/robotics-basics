# Results

This page holds what is known about solution 7. **The fits did not learn the
task, and the scoring run was stopped.** So this solution has no score. The
page gives what the three fits reached. It then says why this does not show
that the newer model is worse.

## Contents

1. [What is being measured](#1-what-is-being-measured)
2. [Where the results will appear](#2-where-the-results-will-appear)

## 1. What is being measured

[What it needs](02_what-it-needs.md) gave the costs. This section gives what
the fitting measured, and why the scoring stopped there.

Solution 7 was fitted three times, once for each of three seeds. Each fit ran
1,000 steps and took about 100 minutes. During each fit the model was asked
for chunks on tuning tables. A tuning table is one nothing was fitted on. The
fit measures how far the model's waypoints land from the teacher's.

The table gives that distance, as the median over the tuning tables. Each row
is one fit. The last three rows are solution 6, fitted on the same 6,935
demonstrations with the same budget. The numbers come from each fit's training
record:
Evo-1 seeds [0](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/fitted-0/training.json),
[1](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/fitted-1/training.json) and
[2](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/fitted-2/training.json),
and SmolVLA seeds [0](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/06-smolvla-fine-tuned/correction-aligned-0/training.json),
[1](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/06-smolvla-fine-tuned/correction-aligned-1/training.json) and
[2](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/06-smolvla-fine-tuned/correction-aligned-2/training.json).

| fit | step 0 | step 500 | step 1,000 |
|---|---|---|---|
| 7 Evo-1, seed 0 | 299.9 mm | 283.4 mm | **287.4 mm** |
| 7 Evo-1, seed 1 | 297.4 mm | 298.5 mm | **288.6 mm** |
| 7 Evo-1, seed 2 | 308.7 mm | 297.7 mm | **287.4 mm** |
| 6 SmolVLA, seed 0 | 310.2 mm | 92.6 mm | 101.5 mm |
| 6 SmolVLA, seed 1 | 297.8 mm | 115.3 mm | 106.1 mm |
| 6 SmolVLA, seed 2 | 298.5 mm | 77.0 mm | 90.0 mm |

Both models start about 300 mm from the teacher. Solution 6 ends between 90
and 106 mm. Solution 7 ends at 287 to 289 mm. Its three seeds end within
about a millimetre of each other, so this is not bad luck in one fit.

The glass zone is 320 mm by 360 mm. An answer 288 mm from the teacher's is not
a push at the wrong glass. It is a motion somewhere else on the table. **The
fitting did not teach Evo-1 the task.**

So the project stopped the scoring run. It would have taken about two hours of
the graphics chip. It would have scored a policy that aims nowhere near the
glasses.
[Solution 5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md)
already measures what an unfitted borrowed model does on this bench.

**This does not show that the newer model is worse.** Both fits got the same
number of steps. But that hid a large difference in what each fit had to
learn. Solution 6 changes 3.8 million numbers. They correct a model that
already produces robot motions. Solution 7 fits 122.0 million numbers, about
32 times as many. And those numbers start from random values. Evo-1's first
stage freezes the half that sees. The half that moves is new, so it must be
built from nothing. A model trained too little looks the same as a model that
cannot do the task. Only more training can tell the two apart.

The project set down one expectation before any score. It expected Evo-1 to
score about as well as solutions 5 and 6. The stopped run means this guess was
never tested.

The next section says where the files are, and what test comes next.

## 2. Where the results will appear

The fits are known and the score is not. This section says where each part is
kept.

The project's
[`07-evo1-fine-tuned/`](https://github.com/RobinNagpal/robot-arm-projects/tree/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned)
folder holds the three fits. Each fit has its own folder, such as
[`fitted-0/`](https://github.com/RobinNagpal/robot-arm-projects/tree/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/fitted-0).
Its
[`training.json`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/fitted-0/training.json)
is the record the table above quotes. The folder has no
[`run.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/run.py)
output, because the scoring run was stopped. Its
[README](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/07-evo1-fine-tuned/README.md)
gives the same fitting result.

The next test is a cheap one.
[Issue #24](https://github.com/RobinNagpal/robot-arm-projects/issues/24) asks
whether Evo-1's action half can memorise fifty demonstrations. A network with
122 million free numbers should find that easy. If it cannot, the fault is in
how the two halves are joined. If it can, the fault is only the amount of
training. Then a longer fit on one seed is worth the time.

If a score arrives, this page and [the results](../11_the-results.md) will be
updated. The next page answers common questions about this solution.

← [What it needs](02_what-it-needs.md) · [Questions and answers](04_questions-and-answers.md) →
