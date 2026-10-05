# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

Two pieces of rung one carry the whole idea, and they are short enough to read
here. The first is the forward model itself: five copies of a small network
that take a table and a candidate push and answer with what that push would do.
The second is the arithmetic that turns those five answers into a single
decision about one candidate — kept, or thrown away, and at what cost. They are
the heart of this solution because nothing else in it knows anything about
pushing: the model holds all of it, and this arithmetic is the only thing that
reads the model's mind.

The borrowed library does its work in the four `nn.Linear` lines, and
everything around them is the ensemble, in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py):

```python
ENSEMBLE = 5
HIDDEN = 256

class PushNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(features.INPUTS, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, features.OUTPUTS),
        )  # fmt: skip
...
class Ensemble:
    """ENSEMBLE copies, asked together."""
    ...
    def predict(self, x: np.ndarray) -> np.ndarray:
        """(copies, rows, outputs), raw: movements scaled, yes-or-no as logits."""
        with torch.no_grad():
            x_t = torch.as_tensor(x)
            return np.stack([net(x_t).numpy() for net in self.nets])
```

What the five answers are then used for is in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py),
where every candidate push is scored at once and the unacceptable ones are given
a cost of infinity:

```python
def score(model: Ensemble, seen: list, target, kind: str, heading, offset, travel, rng: np.random.Generator):
    """Expected crowding after each candidate push, and why any were dropped.
    ...
    """
    rows = features.encode(seen, target, kind, heading, offset, travel)
    out = model.predict(rows)
    move = out.mean(0)
    topple = sigmoid(out[:, :, features.TOPPLED]).max(0)
    blocked = sigmoid(out[:, :, features.BLOCKED]).mean(0)
    for _ in range(JITTERS):
        shifted = jittered(seen, rng)
        mine = next(s for s in shifted if s.id == target.id)
        out = model.predict(features.encode(shifted, mine, kind, heading, offset, travel))
        topple = np.maximum(topple, sigmoid(out[:, :, features.TOPPLED]).max(0))
    ...
    cost = blocked * here + (1 - blocked) * crowding + TRAVEL_COST * travel

    dropped = {
        "topple": ~(topple <= TOPPLE_LIMIT),
        "map": ~(inside & reachable),
        "unsure": moved_far,
    }
    cost[dropped["topple"] | dropped["map"] | dropped["unsure"]] = math.inf
    return cost, landing, {k: int(v.sum()) for k, v in dropped.items()}
```

Those two blocks are where this solution's result comes from, in both
directions. The displacements are **averaged** over the copies and the topple
chance is taken as the **worst** of them, and taken again on each shifted copy
of the table, so a push only has to look risky once to be dropped — which is
why this solution racks more glasses than any other answer to this problem, in
the fewest pushes, and why the glasses it gives up on are given up on with a
reason. It is also where the one glass it topples comes from: `topple` is the
model's opinion and nothing else's, so where all five copies are confident and
all five are wrong, there is nothing left in the code above to disagree with
them.

## 2. The pushes are what this contributes

Having chosen a push, this solution hands it over in the form [the test
examiner](../02_the-examiner.md) defines, and it is worth being exact about where its
contribution stops.

**It emits a parameterised push.** Which glass to move, where the fingertips
come down, which way the jaw points, how far it feels forward and how far it
pushes. That is what `push()` accepts, and **the expansion of those numbers
into a jaw trajectory is a macro the examiner owns**: the descend, the slow feel
forward until contact, the push at a steady speed, the back-off and the lift.
This solution does not write that expansion and gains nothing from it, and
neither does any other solution that thinks in pushes.

Two of the numbers in that push are arithmetic rather than model output, and
saying so keeps the boundary clean. Where the fingertips come down is behind the
glass's widest edge with a margin for the camera's error. How far forward the
jaw feels is far enough to pass the glass's middle, because a stemmed glass is
met at its stem, well inside its widest edge, and a jaw that misses and lifts
under the bowl tips it. Neither number is learned, because neither depends on
anything nobody knows.

**The height is not a choice.** [Pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) settles that for all six: the jaw
rides as low as the gripper can go, always, so there is nothing to trade and
nothing to tune. What this solution decides is only whether to push at all, and
where to.

**What it does not contribute is the destination.** Where the glasses should
end up is [the target layout](../01_the-problem/02_the-target-layout.md), computed once from the
same measurements and so that no solution aiming at a destination can score
well by aiming at an easier arrangement.

So the whole of this solution's contribution sits in one place: **which push,
out of all the pushes the geometry allows, is the one worth making.** It is
scored on the table afterwards, the same as everything else.

## 3. How the concepts fit together

The pieces have been introduced separately, so here they are in the order they
run, once per push.

**Look.** `look()` returns one reading per glass: where it stands, how tall,
how wide at its widest and at its foot, whether it is standing. Every reading
carries the error measured in [telling the glasses
apart](../../08_seeing-the-glasses/11_the-results.md).

**Apply the shared topple limit.** The arithmetic in [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md) is worked out from each glass's
measured foot width before anything is asked of the model, and a glass that
fails it is refused with that reason. This step is the same for all six and is
the one part of the loop the built planner does not yet have.

**Take anything that can be taken.** Any glass with clear room is lifted off
immediately, with a small extra margin for the camera's error, because a glass
that is gone cannot be toppled and cannot be in the way. The model is not
consulted.

**For each glass still crowded, search.** Draw candidate pushes, encode each
one with the table into a row in the push's own frame, ask all five copies of
the model, average their displacements, take the worst copy's topple chance,
and repeat the topple question on four copies of the table shifted by about the
camera's error.

**Throw away everything unacceptable.** Any candidate over the topple limit.
Any candidate whose predicted table puts a moved glass outside the glass zone or
outside the arm's reach. Any candidate whose predicted movement is longer than
the push, which is the model answering about something it has not seen.

**Score the survivors and refine.** The score is the room still missing on the
predicted table, plus a small penalty per millimetre pushed. Keep the best
thirty, draw the next round around them, and repeat four times in all.

**Make one push.** The best push over every crowded glass on the table is
expanded by the examiner's macro and carried out. The jaw reports what it felt.

**Then look again**, and begin at the top with the arrangement as it now is.
The loop ends when every glass has been racked, when the table's push budget is
spent, or when no push the model expects to help survives the filters — and
each glass left behind is reported with the reason it was left.

Two guards sit around that loop and are worth naming because they are what stop
it running for ever. A glass may be pushed only a few times before it is
reported as refused, and the table has a budget of pushes for the whole run.
Both are plain counters, both belong to the loop rather than to the model, and
the budget must be the same number for all six or the push counts on the
scorecard cannot be compared.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
