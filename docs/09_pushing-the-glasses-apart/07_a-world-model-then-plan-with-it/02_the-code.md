# The code

This page shows the code at the centre of this solution. It also says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md). [How it works](03_how-it-works.md) then explains each
part of this code.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

Two short pieces of code hold the whole idea. The first is the forward model:
five copies of a small network. Each copy takes a table and a candidate push,
and it says what that push would do. The second piece turns the five answers
into one decision about a candidate. The candidate is kept or dropped, and it
gets a cost. Nothing else in the solution knows anything about pushing.

The model is in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py).
The library, PyTorch, does its work in the four `nn.Linear` lines. Everything
around them is the set of five copies.

The whole of it runs in six steps. Steps 1 and 2 are the model, in
[`model.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/04-a-world-model/model.py).
Steps 3 to 6 are the planning that uses it, in
[`plan.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py).

1. Stack the four layers of the network. Store the average and the spread of
   the training inputs beside the weights. Every input is scaled by those two
   numbers before the layers see it.
2. Ask all five copies the same question, and keep their five answers apart.
   Training bookkeeping is switched off, because nothing is being trained.
   Keeping the answers apart is the only reason there are five copies.
3. Write each candidate push, with its table, as one row of numbers. Hand every
   row to all five copies at once.
4. Turn the five answers into three numbers per candidate: the average
   movement, the worst copy's chance of a topple, and the average chance that
   the jaw is blocked on the way down. Then ask the topple question again on
   four copies of the table, each shifted by about the camera's error. Keep the
   highest topple chance of all.
5. Build the table each candidate should leave behind. Mark the candidates
   that must go: a glass predicted to travel much further than the push, a jaw
   path the arm cannot reach well, and a moved glass that ends up outside the
   zone.
6. Measure the room still missing on each predicted table and on the table as
   it is now. Turn that into one cost per candidate. Give every refused
   candidate a cost of infinity.

Steps 1 and 2 are the model itself, and the code below is all of it.

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
        # Step 1: keep the training set's own average and spread beside the
        # weights -- so a push asked about later is scaled as training scaled it
        self.register_buffer("mean", torch.zeros(features.INPUTS))
        self.register_buffer("spread", torch.ones(features.INPUTS))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Step 1: subtract that average and divide by that spread, then run the
        # layers -- every number reaches the first layer at about the same size
        return self.net((x - self.mean) / self.spread)
...
class Ensemble:
    """ENSEMBLE copies, asked together."""
    ...
    def predict(self, x: np.ndarray) -> np.ndarray:
        """(copies, rows, outputs), raw: movements scaled, yes-or-no as logits."""
        # Step 2: answer without recording the workings -- nothing is being
        # trained here, so the workings would only cost time and memory
        with torch.no_grad():
            x_t = torch.as_tensor(x)
            # Step 2: ask all five copies the same question and keep the five
            # answers apart -- where they disagree is how the planner sees doubt
            return np.stack([net(x_t).numpy() for net in self.nets])
```

The five answers are used in
[`code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/04-a-world-model/plan.py).
There every candidate push is scored at once, and the unacceptable ones get a
cost of infinity.

This is steps 3 to 6 of the list above. Steps 3 and 4 ask the model, and they
refuse nothing. Steps 5 and 6 judge the answers, and they do not ask the model
again.

```python
def score(model: Ensemble, seen: list, target, kind: str, heading, offset, travel, rng: np.random.Generator):
    """Expected crowding after each candidate push, and why any were dropped.
    ...
    """
    # Step 3: write every candidate push, together with the table it would be
    # made on, as one row of numbers each -- this is all the model is ever shown
    rows = features.encode(seen, target, kind, heading, offset, travel)
    # Step 3: ask all five copies of the model about every candidate at once
    out = model.predict(rows)
    # Step 4: average the five copies' predicted movements -- for how far a glass
    # slides, the middle of the five answers is the best guess available
    move = out.mean(0)
    # Step 4: take the worst copy's chance of toppling, not the average -- one
    # copy calling a push risky is enough to treat it as risky
    topple = sigmoid(out[:, :, features.TOPPLED]).max(0)
    # Step 4: average the five copies' chance that the jaw is blocked on the way
    # down, which costs the push rather than endangering a glass
    blocked = sigmoid(out[:, :, features.BLOCKED]).mean(0)
    # Step 4: ask the topple question again on four copies of the table, each
    # reading moved by about as much as the camera could be wrong
    for _ in range(JITTERS):
        shifted = jittered(seen, rng)
        mine = next(s for s in shifted if s.id == target.id)
        out = model.predict(features.encode(shifted, mine, kind, heading, offset, travel))
        # Step 4: keep the highest topple chance seen on any of those tables --
        # so a push has to look safe however the measurements fell
        topple = np.maximum(topple, sigmoid(out[:, :, features.TOPPLED]).max(0))

    # Step 5: build the table each candidate is predicted to leave behind: start
    # from what the camera sees and add every glass's predicted movement, read
    # back out of the push's own along-and-across frame into table directions
    along, left = features.frame(heading)
    ...
    landing = after[:, index[target.id]]

    # Step 5: mark a candidate whose glass is predicted to travel much further
    # than the push itself -- that is the model guessing beyond what it has seen
    moved_far = np.linalg.norm(landing - now[index[target.id]], axis=1) > travel + ENVELOPE
    # Step 5: work out both ends of the jaw's path, where the fingertips come
    # down and where they stop, and mark a candidate the arm cannot comfortably
    # reach at either end
    start = np.array([features.jaw_start(target, h, o) for h, o in zip(heading, offset, strict=True)])
    tip_end = start + (features.jaw_reach(target) + travel)[:, None] * along
    reachable = _in_reach(start) & _in_reach(tip_end)
    # Step 5: mark a candidate that would leave a moved glass outside the zone
    # glasses are allowed to stand in. A glass the push leaves where it is may
    # stand near the edge already; only one it moves has to land well inside.
    moves = np.linalg.norm(after - now[None], axis=-1) > STILL
    inside = np.all(
        [_in_zone(after[:, i]) | ~moves[:, i] for i in range(len(seen))], axis=0
    )

    # Step 6: measure the room still missing on each predicted table, and on the
    # table as it stands now, which is what a blocked jaw would leave it as
    crowding = np.array([shortfall(a, widest) for a in after])
    here = shortfall(now, widest)
    # Step 6: the score for one candidate -- the missing room it is expected to
    # leave, weighted by whether the jaw gets down, plus a small charge for travel
    cost = blocked * here + (1 - blocked) * crowding + TRAVEL_COST * travel

    # Step 6: collect the three reasons a candidate is unacceptable
    dropped = {
        "topple": ~(topple <= TOPPLE_LIMIT),
        "map": ~(inside & reachable),
        "unsure": moved_far,
    }
    # Step 6: price every unacceptable candidate at infinity -- the search then
    # throws it away without needing to know why
    cost[dropped["topple"] | dropped["map"] | dropped["unsure"]] = math.inf
    return cost, landing, {k: int(v.sum()) for k, v in dropped.items()}
```

Two choices in this code decide how the solution behaves. The movements are
**averaged** over the five copies. The topple chance is the **worst** copy's,
on any of the shifted tables. So a push has to look risky only once to be
dropped. But `topple` is only the model's opinion. If all five copies are sure
and all five are wrong, nothing in this code disagrees with them. [Where it is
strong and where it
breaks](06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks) shows
how often that happened.

The next section says what this code hands to the examiner once a push is
chosen.

## 2. The pushes are what this contributes

The code above chooses a push. This section says what form that push takes,
and where the solution's work stops.

**It hands over a push described by a few numbers.** These say which glass to
move, where the fingertips come down, which way the jaw points, how far it
feels forward, and how far it pushes. This is what `push()` accepts. The
examiner turns those numbers into a jaw path, as [what must come
out](../01_the-problem/02_what-goes-in-and-what-comes-out.md#6-what-must-come-out)
explains.

Two of those numbers are plain arithmetic, not model output. The fingertips
come down 20 mm behind the glass's widest edge. This margin clears the glass
even with the camera's error. The jaw then feels forward until 10 mm past the
glass's middle. This is because a stemmed glass is met at its stem, well inside
its widest edge. A jaw that misses the stem and lifts under the bowl tips the
glass. Neither number is learned, because neither depends on anything unknown.
The search chooses the other three numbers.

![A push on one glass drawn from above with its five numbers marked: the fingertips come down 20 mm behind the widest edge and the jaw feels forward to 10 mm past the middle, both of which are arithmetic on the measured width, while the heading, the offset across the glass and the travel are the three numbers the search is free to choose.](../../images/pushing-the-glasses-apart/a-world-model-then-plan-with-it/worldmodel-pages-what-the-push-says.png)

**The height is not a choice.** [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) sets it for all seven
solutions.

**The solution does not choose where the glasses should end up.** [The target
layout](../01_the-problem/04_the-target-layout.md) sets that for all seven.

So this solution adds one thing: **which push, out of all the pushes allowed,
is worth making.** It is scored on the table afterwards, like every other
solution.

The next section puts all the pieces in the order they run.

## 3. How the concepts fit together

The pieces above were shown one at a time. Here they are in the order they run,
once per push.

**Look.** `look()` returns one reading per glass. It gives where the glass
stands, how tall it is, how wide it is at its widest and at its foot, and
whether it is standing. Every reading carries the error measured in [telling
the glasses apart](../../08_seeing-the-glasses/11_the-results.md).

**Apply the shared topple limit.** This step belongs here for all seven
solutions, but the built planner does not have it yet. [The main
idea](01_what-it-is.md#4-the-main-idea) explains this gap.

**Take any glass that already has room.** Such a glass is lifted off at once,
with 3 mm of extra margin for the camera's error. The model is not asked. A
glass that is gone cannot be toppled and cannot be in the way. The margin was
chosen on the tuning tables. At 4 or 5 mm, glasses that already had room were
pushed instead of taken, and every extra push is another chance of a topple.

**For each glass still crowded, search.** Draw candidate pushes and ask all
five copies about each one, as the code above does.

**Drop everything unacceptable.** The three filters are in [planning by
sampling](03_how-it-works.md#6-planning-by-sampling-the-cross-entropy-method).

**Score the survivors and refine.** Keep the best thirty, draw the next round
around them, and repeat four times in all. The best push must be expected to
clear at least 2 mm of missing room. If it is not, the whole table is refused.

**Make one push.** The examiner carries out the best push over every crowded
glass. The jaw reports what it felt.

**Then look again.** Start from the top with the table as it now is. The loop
ends in one of three ways. Every glass is racked, or the table's push budget is
spent, or no push the model expects to help passes the filters. Each glass
left behind is reported with its reason.

Two counters stop the loop from running for ever. A glass may be pushed only a
few times before it is refused. The table also has a budget of pushes for the
whole run. Both counters belong to the loop, not to the model. The budget must
be the same for all seven solutions, or their push counts cannot be compared.

[How it works](03_how-it-works.md) explains each of these ideas in turn.

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
