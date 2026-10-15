# What it needs

This page is the bill for this solution. It lists the data it needs, the
machine it wants, the libraries it uses, and their licences.

## 1. What it needs

The worked example showed the solution at work. This section lists what it
takes to build and run it.

**It needs a physics engine and thousands of pushes in it.** This is the main
cost. Every training example is one real push in the simulator: look, push,
look again. The first way's README records 38,012 of them, collected in two
rounds:

- 24,759 random pushes on 4,000 tables;
- then 13,253 pushes on 5,000 new tables. Three quarters of these were chosen by
  the planner, using the first round's model. This fills the gaps the search
  would otherwise use.

**Nobody labels any of it.** The answer for each example is the difference
between two looks, one before the push and one after. So the model learns to
predict what the camera will report next, with its error. It does not learn
what the world really does. This is the right choice, because the camera's next
report is what the planner will see. A model that predicted a truth the arm can
never see would predict the wrong thing. It also means the data costs simulator
time and no human time. This is the biggest practical advantage over any
method trained on demonstrations.

![One training table yields a dozen examples, because the table is built once and the state after each push starts the next and no push has to be a useful one; a real run makes as few pushes as it can, so gathering the same 38,012 rows from ordinary runs would take about sixteen thousand tables, where the simulator produces them in about fifty core-minutes and nobody labels any of it.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/10-the-data-it-takes.png)

**It needs a training run before it can answer anything.** The first way trains
five small networks. Its README says the pushes and the training together take
about half an hour on a laptop processor. **The first way needs no accelerator
at all.** This is because the model is small, and its input is 34 numbers, not
a picture.

**The second way needs rented hardware.** TD-MPC2 is reinforcement learning,
and it needs an accelerator. Renting one for a weekend costs about a hundred
dollars, which covers one training run. One run is not a measurement, so
several training seeds are needed. The realistic cost is a small accelerator
for about a month, which is about five hundred dollars.

**It needs computing time on every push.** Before each push, the search asks
the model about 1,500 candidates for every crowded glass. Each candidate goes to
five networks. The topple question is asked on five readings of the table. The run measured **0.37 seconds
of thinking per push**, in
[`results.json`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/results.json).
The machine was busy with other work, so this number is only rough. A real arm
movement takes longer than this, so the arm does not wait. A two-push search
would cost much more. [The results](../11_the-results.md#2-the-results) compare
this time with the other five solutions.

**It needs weights that match the cell.** The weights record what the cell was
like when they were trained. Suppose the jaw, the glass zone, the shapes of the
glasses or the camera's error changes. Then the weights are out of date, and no
test of the code will notice.

**It needs libraries, and no borrowed model.** Both ways use PyTorch, and MuJoCo
through the examiner. The second way needs TD-MPC2. The library this project
uses elsewhere has only the earlier method, TD-MPC, and not TD-MPC2. So TD-MPC2
would have to be fetched from its own project. Neither way downloads trained
weights, so there is no model licence to meet. Only the libraries' own licences
apply, and TD-MPC2's licence is MIT.

**Its score has no spread.** The first way was trained once and run once. So
its results give the time per push but no spread across runs. [The test
examiner](../01_the-problem/03_the-examiner.md) explains why one run is not a
full measurement.

The next page weighs these costs against what the solution achieves.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
