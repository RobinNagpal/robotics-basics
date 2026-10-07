# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md), and [how it works](03_how-it-works.md) explains, part by
part, what the code below is doing. The second explains the first,
which is why they are on one page.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

Two pieces of the first way carry the whole idea, and they are short enough to read
here. The first is the forward model itself: five copies of a small network
that take a table and a candidate push and answer with what that push would do.
The second is the arithmetic that turns those five answers into a single
decision about one candidate — kept, or thrown away, and at what cost. They are
the heart of this solution because nothing else in it knows anything about
pushing: the model holds all of it, and this arithmetic is the only thing that
reads the model's mind.

The borrowed library does its work in the four `nn.Linear` lines, and
everything around them is the ensemble, in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py).

The model is built in three steps and asked in two. Step 1 stacks the four
layers that are the network. Step 2 stores the average and the spread of the
training inputs alongside the weights. Step 3 uses those two numbers, scaling
every input before the layers see it. Step 4 switches off the bookkeeping that
training needs and answering does not. Step 5 asks all five copies the same
question and keeps their five answers separate, which is the only reason there
are five of them.

```python
ENSEMBLE = 5
HIDDEN = 256

class PushNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        # Step 1: stack four layers of arithmetic with a bend between them -- this
        # is the whole network, and it turns one push into what that push would do
        self.net = nn.Sequential(
            nn.Linear(features.INPUTS, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, features.OUTPUTS),
        )  # fmt: skip
        # Step 2: keep the training set's own average and spread beside the
        # weights -- so a push asked about later is scaled as training scaled it
        self.register_buffer("mean", torch.zeros(features.INPUTS))
        self.register_buffer("spread", torch.ones(features.INPUTS))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Step 3: subtract that average and divide by that spread, then run the
        # layers -- every number reaches the first layer at about the same size
        return self.net((x - self.mean) / self.spread)
...
class Ensemble:
    """ENSEMBLE copies, asked together."""
    ...
    def predict(self, x: np.ndarray) -> np.ndarray:
        """(copies, rows, outputs), raw: movements scaled, yes-or-no as logits."""
        # Step 4: answer without recording the workings -- nothing is being
        # trained here, so the workings would only cost time and memory
        with torch.no_grad():
            x_t = torch.as_tensor(x)
            # Step 5: ask all five copies the same question and keep the five
            # answers apart -- where they disagree is how the planner sees doubt
            return np.stack([net(x_t).numpy() for net in self.nets])
```

What the five answers are then used for is in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py`](../../../code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py),
where every candidate push is scored at once and the unacceptable ones are given
a cost of infinity.

That arithmetic runs in fifteen steps, and they all go one way: ask first, then
judge. Step 6 writes each candidate push, and the table it would be made on, as
one row of numbers. Step 7 hands every row to all five copies at once. Steps 8
to 10 boil the five answers down to three numbers per candidate: the average
movement, the worst copy's chance of toppling something, and the average chance
the jaw is blocked on the way down. Steps 11 and 12 ask the topple question
again on four copies of the table shifted by about the camera's error, and keep
the highest answer of all of them. Step 13 builds the table each candidate is
predicted to leave behind. Steps 14 to 16 mark the candidates that have to go:
the glass predicted to travel far further than the push, the jaw path that
leaves the arm's comfortable reach, and the moved glass that lands outside the
zone. Step 17 measures the room still missing, on each predicted table and on
the table as it stands. Step 18 turns that into one cost per candidate. Steps 19
and 20 gather the three refusals and price every refused candidate at infinity.

```python
def score(model: Ensemble, seen: list, target, kind: str, heading, offset, travel, rng: np.random.Generator):
    """Expected crowding after each candidate push, and why any were dropped.
    ...
    """
    # Step 6: write every candidate push, together with the table it would be
    # made on, as one row of numbers each -- this is all the model is ever shown
    rows = features.encode(seen, target, kind, heading, offset, travel)
    # Step 7: ask all five copies of the model about every candidate at once
    out = model.predict(rows)
    # Step 8: average the five copies' predicted movements -- for how far a glass
    # slides, the middle of the five answers is the best guess available
    move = out.mean(0)
    # Step 9: take the worst copy's chance of toppling, not the average -- one
    # copy calling a push risky is enough to treat it as risky
    topple = sigmoid(out[:, :, features.TOPPLED]).max(0)
    # Step 10: average the five copies' chance that the jaw is blocked on the way
    # down, which costs the push rather than endangering a glass
    blocked = sigmoid(out[:, :, features.BLOCKED]).mean(0)
    # Step 11: ask the topple question again on four copies of the table, each
    # reading moved by about as much as the camera could be wrong
    for _ in range(JITTERS):
        shifted = jittered(seen, rng)
        mine = next(s for s in shifted if s.id == target.id)
        out = model.predict(features.encode(shifted, mine, kind, heading, offset, travel))
        # Step 12: keep the highest topple chance seen on any of those tables --
        # so a push has to look safe however the measurements fell
        topple = np.maximum(topple, sigmoid(out[:, :, features.TOPPLED]).max(0))

    # Step 13: build the table each candidate is predicted to leave behind: start
    # from what the camera sees and add every glass's predicted movement, read
    # back out of the push's own along-and-across frame into table directions
    along, left = features.frame(heading)
    ...
    landing = after[:, index[target.id]]

    # Step 14: mark a candidate whose glass is predicted to travel much further
    # than the push itself -- that is the model guessing beyond what it has seen
    moved_far = np.linalg.norm(landing - now[index[target.id]], axis=1) > travel + ENVELOPE
    # Step 15: work out both ends of the jaw's path, where the fingertips come
    # down and where they stop, and mark a candidate the arm cannot comfortably
    # reach at either end
    start = np.array([features.jaw_start(target, h, o) for h, o in zip(heading, offset, strict=True)])
    tip_end = start + (features.jaw_reach(target) + travel)[:, None] * along
    reachable = _in_reach(start) & _in_reach(tip_end)
    # Step 16: mark a candidate that would leave a moved glass outside the zone
    # glasses are allowed to stand in. A glass the push leaves where it is may
    # stand near the edge already; only one it moves has to land well inside.
    moves = np.linalg.norm(after - now[None], axis=-1) > STILL
    inside = np.all(
        [_in_zone(after[:, i]) | ~moves[:, i] for i in range(len(seen))], axis=0
    )

    # Step 17: measure the room still missing on each predicted table, and on the
    # table as it stands now, which is what a blocked jaw would leave it as
    crowding = np.array([shortfall(a, widest) for a in after])
    here = shortfall(now, widest)
    # Step 18: the score for one candidate -- the missing room it is expected to
    # leave, weighted by whether the jaw gets down, plus a small charge for travel
    cost = blocked * here + (1 - blocked) * crowding + TRAVEL_COST * travel

    # Step 19: collect the three reasons a candidate is unacceptable
    dropped = {
        "topple": ~(topple <= TOPPLE_LIMIT),
        "map": ~(inside & reachable),
        "unsure": moved_far,
    }
    # Step 20: price every unacceptable candidate at infinity -- the search then
    # throws it away without needing to know why
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

Two of those numbers are arithmetic rather than model output, and saying so
keeps the boundary clean. The fingertips come down 20 mm behind the glass's
widest edge, which is the margin that clears it despite the camera's error. The
jaw then feels forward until 10 mm past the glass's middle, because a stemmed
glass is met at its stem, well inside its widest edge, and a jaw that misses and
lifts under the bowl tips it. Neither number is learned, because neither depends
on anything nobody knows. The search chooses the other three.

![A push on one glass drawn from above with its five numbers marked: the fingertips come down 20 mm behind the widest edge and the jaw feels forward to 10 mm past the middle, both of which are arithmetic on the measured width, while the heading, the offset across the glass and the travel are the three numbers the search is free to choose.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-pages-what-the-push-says.png)

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
immediately, with 3 mm of extra margin for the camera's error, because a glass
that is gone cannot be toppled and cannot be in the way. The model is not
consulted. The margin was chosen on the tuning tables: at 4 or 5 mm, glasses
that already had room were pushed instead of taken, and every extra push is
another chance to topple one.

**For each glass still crowded, search.** Draw candidate pushes, encode each
one with the table into a row in the push's own frame, ask all five copies of
the model, average their displacements, take the worst copy's topple chance,
and repeat the topple question on four copies of the table shifted by about the
camera's error.

**Throw away everything unacceptable.** Any candidate over the topple limit.
Any candidate whose predicted table puts a moved glass outside the glass zone or
outside the arm's reach. Any candidate whose predicted movement is more than two
centimetres longer than the push, which is the model answering about something
it has not seen.

**Score the survivors and refine.** The score is the room still missing on the
predicted table, plus a tenth of a millimetre of that for every millimetre the
jaw travels, with the chance of a blocked descent mixed in. Keep the best
thirty, draw the next round around them, and repeat four times in all. A push
has to be expected to clear at least 2 mm of missing room, or the whole table is
refused rather than nudged for nothing.

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

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
