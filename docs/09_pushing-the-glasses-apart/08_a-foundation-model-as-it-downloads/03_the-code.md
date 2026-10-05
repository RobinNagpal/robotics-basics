# The code

This page shows the code at the heart of this solution, and says exactly what
the solution hands back to the rest of the cell. The two belong on one page
because the second explains the first: the code is far easier to read once you
know which of its results leave this solution and which are working detail. By
the end you will be able to point at the lines that produce the pushes, and to
see where the ideas of [how it works](02_how-it-works.md) meet.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code that does the work

Nothing here is fitted, so the only code this project wrote is the join between
what the borrowed model emits and what this cell's jaw is. That join turned out
to be the whole solution, for a reason the sections below explain at length and
which is worth having in front of the code: the released checkpoint saves its
normalisation statistics under keys the normaliser never looks up, so both the
normaliser and the un-normaliser pass their numbers through unchanged, and the
actions arrive as z-scores with no units in them at all. A scale therefore had
to be **chosen** rather than converted, and the lines that choose it are the
lines to read.

The borrowed library does its work in one call, in
[`05-smolvla-as-it-downloads/policy.py`](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads/policy.py).
`predict_action_chunk` is LeRobot's; `self.pre` and `self.post` are the
processors the checkpoint ships, which are the ones that do nothing here; and
`to_jaw` is this project's.

```python
    def ask(self, picture: np.ndarray, jaw: Waypoint) -> np.ndarray:
        ...
        batch = {
            CAMERA: torch.from_numpy(picture.copy()).permute(2, 0, 1).float() / 255.0,
            "observation.state": torch.from_numpy(to_state(jaw, self.up)).float(),
            "task": INSTRUCTION,
        }
        with torch.no_grad():
            actions = self.policy.predict_action_chunk(self.pre(batch))
        return to_jaw(self.post(actions)[0].numpy().astype(float), self.up)
```

The scale that `to_jaw` applies is in
[`05-smolvla-as-it-downloads/joining.py`](../../../code/src/09_pushing-the-glasses-apart/05-smolvla-as-it-downloads/joining.py),
and the whole of the choice is one constant and the four lines that spend it.

```python
# Which of SmolVLA's six slots carries what, in the reading above.
ACROSS, OUT, UP, TURN = 0, 1, 2, 4

...

# How many standard deviations of the model's own action space the picture's
# frame covers. Two, because a z-score of two is the edge of what a normally
# spread quantity does, so the whole frame is reachable without the great
# majority of the model's output pinning itself against the edges.
ACTION_SPAN = 2.0

...

def to_jaw(action: np.ndarray, up: float = UP_HIGHER) -> np.ndarray:
    ...
    unit = np.clip(action / ACTION_SPAN, -1.0, 1.0)
    return np.stack(
        [
            VIEW_CENTRE[0] + unit[:, ACROSS] * TOP_VIEW_HALF_FRAME,
            VIEW_CENTRE[1] + unit[:, OUT] * TOP_VIEW_HALF_FRAME,
            PUSH_HEIGHT + (up * unit[:, UP] + 1.0) / 2.0 * (TRAVEL_HEIGHT - PUSH_HEIGHT),
            unit[:, TURN] * math.pi,
        ],
        axis=1,
    )
```

Two things show from that. The only object in this solution that has both a
metric extent and is seen by the model is the frame of the straight-down
picture, so `ACTION_SPAN = 2.0` is the decision that two standard deviations of
the model's output span that frame exactly — which is what lets the model put
the jaw anywhere it can see and nowhere it cannot. And because the bench
consumes waypoints a fixed period apart, the spacing of the waypoints this
function returns *is* the speed the jaw is asked to travel at, so the same
constant fixes the speed as well as the reach, and the two cannot be chosen
separately.

## 2. The pushes are what this contributes

It is worth stating plainly where this solution stops, because the boundary is
the same for all six and is what makes them comparable.

The input is fixed by [the test bench](../02_the-test-bench.md). This solution may read
what `look()` returns — where each glass stands, how tall it is, how wide it
is at its widest and at its foot, and whether it is standing, each reading
carrying the error measured for [telling the glasses apart in a
picture](../../08_seeing-the-glasses/11_the-results.md) — and the rendered view of the same table
from the top. In practice it reads mostly the picture, because the picture is
what the model takes. It may not read the simulator's record of what was placed,
and it is not told the friction, and neither of those exceptions is relaxed for
a borrowed model.

The output is fixed too: **a jaw trajectory**. This solution emits one
directly, as a run of waypoints, rather than as a parameterised push expanded
by the bench's macro. Both forms are accepted and the bench treats them alike,
because **what is scored is the table afterwards rather than the push that
changed it**. That is the only arrangement under which a push described by
three numbers and a run of fifty waypoints can be compared at all.

So this solution contributes only the trajectories, and any difference in its
score belongs to them. It cannot win by aiming at an easier arrangement,
because [the target layout](../01_the-problem/02_the-target-layout.md) is computed once from the
same measurements and handed to all six. It cannot win by marking itself
kindly, because the scorecard is the same counts computed the same way. And it
cannot lose by having its movement squeezed into a shape that does not suit it,
because waypoints are accepted as they come.

One thing about the repeats is specific to this solution and worth noting. The
bench requires every trained solution to be trained with several seeds and
evaluated over several runs, because training varies with its seed and one run
is not a measurement. **This solution has no training seed**, since it trains
nothing, so the only variation it has is in how its actions are drawn when it
answers. Its spread should therefore be narrower than solution 6's, and the
comparison between the two has to be read with that difference in mind rather
than against it.

## 3. How the concepts fit together

The pieces now connect into one picture, and it is a short picture because the
solution is short.

A model fitted on an enormous pool of real teleoperation across many robots and
many tasks would be downloaded unchanged and shown this bench's rendered view
of the table from the top, together with one unvarying English sentence and the
arm's own joint readings. It would return actions, which somebody has to
interpret as waypoints for this jaw, because the units and layout it emits were
fixed for other robots. The bench would carry those waypoints out, the table
would change, fresh measurements would be taken, and the model would be asked
again.

What the model brings to that loop is a general sense of how manipulation goes,
and nothing about this cell. What it is denied is the force reading, because its
three inputs do not include one for force, so the only channel through which
friction is observable is closed to it. And what stands between its general
competence and this particular table is a large domain gap: it learned from
real cameras, real light and cluttered rooms, and it is shown flat pale blue
shapes on an empty rectangle. Across that gap it would most likely produce
confident, plausible, wrong actions, which is the failure that is hardest to
notice because nothing about it looks wrong until the arrangement is examined.

Every one of those is a consequence of one decision: **fit nothing here**. That
decision is what makes the solution free to try, and it is also what removes
every lever that would normally be pulled to fix the problems above. Pulling
exactly one of those levers is [solution
6](../09_the-same-model-fine-tuned-here/01_what-it-is.md).

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
