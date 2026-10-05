# Geometry generates, a model ranks — the code

This page shows the code at the heart of this solution, and says exactly what
the solution hands back to the rest of the cell. The two belong on one page
because the second explains the first: the code is far easier to read once you
know which of its results leave this solution and which are working detail. By
the end you will be able to point at the lines that produce the pushes, and to
see where the ideas of [how it works](02_how-it-works.md) meet.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

Everything this solution adds to [solution 1](../04_one-fixed-nudge/01_what-it-is.md) sits in
two places, and they are small enough to read here. The first is the model
itself: scikit-learn's boosted trees, fitted once and then asked for one number
per candidate so that the candidates can be sorted. The second is the number
those trees are asked to predict, which is measured by making the push on the
bench and reading the table afterwards. Those two are the heart of this
solution because the candidates themselves are not its own — they come from
solution 1's enumerator unchanged — so the choosing is the only thing that
differs, and the label is what the choosing is taught to want.

The borrowed library does its work in a constructor and one call to `fit`, and
the sort that follows is the model's entire effect on the run. Both are in
`src/09_pushing-the-glasses-apart/02-geometry-ranked/ranker.py`:

```python
from sklearn.ensemble import GradientBoostingRegressor
...
TREES = 200
DEPTH = 3
LEARNING_RATE = 0.05
...
    @classmethod
    def fit(cls, rows: np.ndarray, labels: np.ndarray, seed: int = 0) -> Ranker:
        trees = GradientBoostingRegressor(
            n_estimators=TREES, max_depth=DEPTH, learning_rate=LEARNING_RATE, random_state=seed
        )
        trees.fit(rows, labels)
        return cls(trees)
...
def ranked(
    seen: list[Seen], skip: set[int], score: Scorer
) -> tuple[list[Candidate], np.ndarray, dict[int, str]]:
    """Every safe push on the table, best first, with its score and the refusals.
    ...
    """
    kept, why = survivors(seen, skip)
    if not kept:
        return [], np.zeros(0), why
    scores = np.asarray(score(features.rows(seen, kept)), dtype=np.float64)
    order = np.argsort(-scores, kind="stable")
    return [kept[i] for i in order], scores[order], why
```

What `labels` holds is the whole design decision, and it is produced by making
one candidate on the bench and measuring what it did, in
`src/09_pushing-the-glasses-apart/02-geometry-ranked/rollout.py`:

```python
def roll(table: Bench, before: Before, candidate: Candidate) -> Rolled:
    """Put the table back as it was, make the push, and measure what it did."""
    restore(table, before)
    felt = table.push(candidate.push)
    after = table.look()
    gained = nudge.shortfall(before.layout) - nudge.shortfall(truth(table))
    fell = any(table.tilt(i) >= STANDING_TILT_DEG for i in table.on_table())
    return Rolled(
        label=TOPPLED if fell else gained,
        ...
    )
```

Two things are visible in those blocks together. `survivors` is called before
the model and `score` only reorders what it returns, which is the safety
argument this whole document rests on. And the label is `gained`, metres of
room the whole table gained, while the run is marked on how many glasses end up
grippable — the mismatch that costs the ranker the comparison with the printed
rule.

## 2. The pushes are what this contributes

One point about the output has to be clear, because it decides what a
comparison with the other five is a comparison of.

This solution thinks in **parameterised pushes**: which glass to move, where to
put the fingertips down, which way to point the jaw, how far to feel forward
and how far to push once it has touched. That is exactly what the bench's
`push()` already accepts, and **the expansion of those numbers into a jaw
trajectory is a macro the bench owns.** The bench brings the closed jaw down at
the chosen start point, feels forward slowly until the force passes a small
threshold, pushes the asked-for distance, backs off a couple of centimetres and
lifts clear. Every parameterised push is expanded the same way by the same
code, so this solution gains nothing and loses nothing in that step.

It follows that **what this solution contributes is the choice of push and
nothing else**. The trajectory is the bench's, the physics is MuJoCo's, and the
marking reads the table afterwards rather than the action, which is what lets a
three-number push and a chunk of waypoints from a learned policy be compared at
all. [The test bench](../02_the-test-bench.md) states that once so that no solution has
to argue it again.

One consequence is worth drawing out, because it is a genuine limitation rather
than a formality. A parameterised push is a straight drag along one heading. A
policy that emits waypoints directly can describe a push that curves, slows,
or changes direction partway through, and no member of this solution's
candidate set can express any of those. That is part of the ceiling named in
the previous section, and it is the clearest example of what the enumeration
costs.

## 3. How the concepts fit together

The pieces now join into one loop, and the loop is the one [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) describes: plan, feel, look again.

Before any of it, and once, the model is fitted. Candidates are generated
geometrically on the training tables, every one of them is executed on the
bench, each is labelled with the clear room the table gained and with whether
the glass toppled, and a few hundred boosted regression trees are fitted to
those labels on a table of a few thousand rows.

At run time, one pass of the loop goes like this. `look()` hands over where
each glass stands and how wide it is at its widest and at its foot, carrying
the measurement error [the camera work
reports](../../08_seeing-the-glasses/11_the-results.md). Any glass that already
has room is racked and removed from the problem. For each glass that is still
crowded, the topple limit is evaluated from its measured foot across the
believed range of friction, and a glass that tips before it slides at every
friction in that range is refused with the reason. For the glasses that remain,
the enumerator sweeps the headings, steps the travel out, applies its four
tests and keeps the survivors. Each survivor is turned into the short list of
lengths, angles, counts and ratios described above, the model scores it, and
the candidates are sorted. The highest-scoring push is handed to the bench,
which expands it into a trajectory, carries it out, and reports what the jaw
felt. Then the arm looks again, and the loop repeats with the arrangement as it
now is rather than as it was planned to be.

Three things are worth holding on to from all of that.

**The safety is the geometry's and the ordering is the model's**, which is the
whole design, and deleting the model leaves a working run rather than a broken
one.

**The loop is what recovers from a bad prediction.** Nothing here trusts that a
push lands where it was aimed. The arrangement is re-read after every push, so
a push that fell short, went too far or turned the glass is simply the state of
the table that the next pass plans against. That is why a wrong ordering costs
a push rather than a run.

**What the loop cannot recover is a toppled glass**, because nothing here lifts
anything. That single fact is why the topple limit is a refusal rule rather
than a risk weighed against the value of moving the glass, and it is why the
model's position after the refusal matters more than the model's accuracy.

← [Geometry generates, a model ranks — how it works](02_how-it-works.md) · [Geometry generates, a model ranks — a worked example](04_a-worked-example.md) →
