# A world model, then plan with it — what it needs

This page is the bill for this solution: the libraries it rests on, the machine
it wants, the data somebody has to supply and, where there is one, the licence
that comes with the weights. It is deliberately short and deliberately separate
from the method, so that the cost of any of the six can be read without reading
how it works all over again.

## 1. What it needs

**A physics engine and thousands of pushes in it.** This is the real cost, and
it is a cost no other solution in this set pays in the same currency. Every
training example is one push really made: look, push, look again. Rung one's
README records thirty-eight thousand of them, collected in two rounds — a first
round of random pushes on thousands of tables, and a second round of pushes
chosen by the planner using the first round's model, which is what fills the
holes the search would otherwise exploit. **Nobody labels any of it.** The
answer to every example is what the second look found, so the data costs
simulator time and no human time at all, which is the single biggest practical
advantage this family has over anything trained on demonstrations.

![One training table yields a dozen examples, because the table is built once and the state after each push starts the next and no push has to be a useful one; a real run makes as few pushes as it can, so gathering the same thirty-eight thousand rows from ordinary runs would take thousands of them, where the simulator produces them in under an hour of processor time and nobody labels any of it.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/10-the-data-it-takes.png)

**A training run, before the solution can answer anything.** Rung one trains
five small networks, and its README records the whole of that — the pushes and
the five networks — at about half an hour on a laptop processor. **No
accelerator is needed for rung one at all.** This is unusual among the learned
solutions here and it follows directly from the model being small and the inputs
being thirty-four numbers rather than a picture.

**For rung two, rented hardware.** TD-MPC2 is reinforcement learning, it trains
on far more interaction than a one-step fit needs, and it wants an accelerator.
Renting one for a weekend is of order a hundred dollars, which covers a single
training run. Because several training seeds are needed before any result is a
result, the realistic figure is a small accelerator for about a month, which is
of order five hundred dollars.

**Run-time compute, and this is where this solution is expensive.** Every single
push the arm makes is preceded by about fifteen hundred candidate pushes, each
evaluated by five networks, repeated across five copies of the table for the
topple check, for every crowded glass. That is cheap in absolute terms, because
the networks are small and the batch goes through in one call, but it is
hundreds of times the arithmetic a fixed nudge costs, and it is the reason [the
test bench](../02_the-test-bench.md) puts a compute column on the scorecard. A
two-push search multiplies it again. On a real arm this still sits comfortably
inside the time one arm movement takes, which is the comparison that matters.

**A file of weights kept in step with the cell.** The code says what the cell
is; the weights say what the cell was like when they were fitted. Change the
jaw, the glass zone, the range of proportions a kind is drawn from, or the
camera's error, and the weights are quietly out of date in a way no test of the
code will notice.

**Libraries, and no borrowed model.** PyTorch for both rungs, MuJoCo through the
bench, and LeRobot for rung two. Neither rung downloads trained weights from
anybody, so there is no model licence to meet in either — the only conditions
are the libraries' own, and LeRobot is Apache 2.0.

**Two additions to the bench, both of which it now has.** [The test
bench](../02_the-test-bench.md) listed them as missing: repeats with a spread on the
scorecard, because one run of a trained solution is not a measurement, and the
time per push beside the counts. Both are in `bench/scoring.py` today, as
`Repeats` and as the seconds-per-push the scorecard records. Rung one's runner
uses the plain scorecard, so its results carry the time per push but no spread:
it has been trained once and run once.

← [A world model, then plan with it — a worked example](04_a-worked-example.md) · [A world model, then plan with it — how it compares](06_how-it-compares.md) →
