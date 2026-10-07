# What it needs

This page is the bill for this solution: the libraries it rests on, the
machine it wants, the data somebody has to supply and, where there is one,
the licence that comes with the weights.

## 1. What it needs

**A physics engine and thousands of pushes in it.** This is the real cost, and
it is a cost no other solution in this set pays in the same currency. Every
training example is one push really made: look, push, look again. The first way's
README records 38,012 of them, collected in two rounds: 24,759 random pushes on
4,000 tables, and then 13,253 on 5,000 fresh tables, three quarters of them
chosen by the planner using the first round's model, which is what fills the
holes the search would otherwise exploit. **Nobody labels any of it.** The
answer to every example is what the second look found, so the data costs
simulator time and no human time at all, which is the single biggest practical
advantage this family has over anything trained on demonstrations.

![One training table yields a dozen examples, because the table is built once and the state after each push starts the next and no push has to be a useful one; a real run makes as few pushes as it can, so gathering the same 38,012 rows from ordinary runs would take about sixteen thousand tables, where the simulator produces them in about fifty core-minutes and nobody labels any of it.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/10-the-data-it-takes.png)

**A training run, before the solution can answer anything.** The first way trains
five small networks, and its README records the whole of that — the pushes and
the five networks — at about half an hour on a laptop processor. **No
accelerator is needed for the first way at all.** This is unusual among the learned
solutions here and it follows directly from the model being small and the inputs
being thirty-four numbers rather than a picture.

**For the second way, rented hardware.** TD-MPC2 is reinforcement learning, it trains
on far more interaction than a one-step fit needs, and it wants an accelerator.
Renting one for a weekend is of order a hundred dollars, which covers a single
training run. Because several training seeds are needed before any result is a
result, the realistic figure is a small accelerator for about a month, which is
of order five hundred dollars.

**Run-time compute, which is the price of searching rather than answering.**
Every single push the arm makes is preceded by fifteen hundred candidate pushes,
each put to five networks and asked about again on five readings of the table
for the topple check, for every crowded glass still on it. The scorecard measures
what that comes to: **0.41 seconds of thinking per push**, against 0.01 for the
imitation policy, 0.06 and 0.08 for the two geometry solutions, and 0.82 and
1.07 for the two that run a borrowed model. So this is the dearest of the four
that are not a foundation model, and it is the reason [the
examiner](../02_the-examiner.md) puts a compute column on the scorecard. Those
times were all measured on a machine that was busy with other work, so they are
good for the order of magnitude and nothing finer. A two-push search would
multiply this one again. On a real arm 0.41 seconds still sits comfortably
inside the time one arm movement takes, which is the comparison that matters.

**A file of weights kept in step with the cell.** The code says what the cell
is; the weights say what the cell was like when they were fitted. Change the
jaw, the glass zone, the range of proportions a kind is drawn from, or the
camera's error, and the weights are quietly out of date in a way no test of the
code will notice.

**Libraries, and no borrowed model.** PyTorch for both of them and MuJoCo through
the examiner. The second way needs TD-MPC2 fetched from its own project, because
the library this project uses elsewhere ships the earlier TD-MPC instead.
Neither way downloads trained weights from anybody, so there is no model licence
to meet in either; the only conditions are the libraries' own, and TD-MPC2 is
MIT.

**Two additions to the examiner, both of which it now has.** [The test
examiner](../02_the-examiner.md) listed them as missing: repeats with a spread on the
scorecard, because one run of a trained solution is not a measurement, and the
time per push beside the counts. Both are in `bench/scoring.py` today, as
`Repeats` and as the seconds-per-push the scorecard records. The first way's runner
uses the plain scorecard, so its results carry the time per push but no spread:
it has been trained once and run once.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
