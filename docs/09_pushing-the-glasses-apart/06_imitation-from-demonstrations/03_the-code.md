# The code

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

This solution lives or dies on one join. A demonstration is the path the jaw
really followed, written down waypoint by waypoint by the bench; a policy's
answer is an **action chunk**, a block of numbers of fixed shape. The code that
turns the first into something the model can be fitted on, and turns the model's
answer back into waypoints the bench will carry out, is this solution's own
contribution, and beside it sits the single call that reaches into the borrowed
library.

The conversion is in
[`code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations/chunks.py`](../../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations/chunks.py),
which holds no model and no geometry of pushing. `push_segment` keeps the part
of a recorded path at push height, from where the jaw started travelling across
the table to the furthest point it reached, and drops the descent, the back-off
and the lift, because the bench does all three itself. `to_action` then writes
what is left as the five columns the policy is fitted on. The way back is the
same file's `to_waypoints`, which turns the cosine-and-sine pair into an angle
again and pulls every waypoint inside what the jaw can reach:

```python
def push_segment(waypoints: tuple[Waypoint, ...]) -> tuple[Waypoint, ...]:
    """The feeling-and-pushing part of a recorded path, with the back-off and lift off.
    ...
    """
    low = [i for i, point in enumerate(waypoints) if point.z <= PUSH_HEIGHT + AT_PUSH_HEIGHT]
    ...
    start, end = low[0], low[-1]
    origin = waypoints[start]
    gone = [math.dist((p.x, p.y), (origin.x, origin.y)) for p in waypoints[start : end + 1]]
    furthest = start + int(np.argmax(gone))
    return tuple(waypoints[start : furthest + 1]) if furthest > start else ()

def to_action(waypoints: tuple[Waypoint, ...]) -> np.ndarray:
    """A run of waypoints as the (n, 5) numbers a policy is fitted on."""
    return np.array(
        [[p.x, p.y, p.z, math.cos(p.heading), math.sin(p.heading)] for p in waypoints],
        dtype=np.float32,
    )
```

The borrowed model is reached in one place, in
[`code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations/policy.py`](../../../code/src/09_pushing-the-glasses-apart/03-imitation-from-demonstrations/policy.py):
one call that builds LeRobot's ACT, and one that asks it for a chunk.

```python
    if kind == "act":
        from lerobot.policies.act.configuration_act import ACTConfig
        from lerobot.policies.act.modeling_act import ACTPolicy

        return ACTPolicy(
            ACTConfig(
                input_features=inputs,
                output_features=outputs,
                chunk_size=chunk,
                n_action_steps=chunk,
                pretrained_backbone_weights=None,
                normalization_mapping=_UNTOUCHED,
                push_to_hub=False,
            )
        )
...
    def chunk(self, picture: np.ndarray) -> np.ndarray:
        """One action chunk from one picture: (chunk, 5) in the table's own units."""
        self.net.eval()
        with torch.no_grad():
            answer = self.net.predict_action_chunk(self.batch(picture))
        return self.scale.back(answer[0].float().cpu().numpy())
```

Three of those settings are the whole of what this solution insists on against
LeRobot's own defaults: `pretrained_backbone_weights=None`, which switches off
the ImageNet weights ACT would otherwise download for its vision backbone and
is what makes "fitted from random numbers" true; `normalization_mapping`, which
hands the scaling back to this solution's own code so that the numbers reaching
the model are only ones written here; and `n_action_steps` set to the chunk's
full length, because one push is one chunk and nothing re-plans part way
through. The rest of the model is LeRobot's, untouched.

Reading the two blocks together says where the measured shortfall has to sit,
and it does sit there. The first two columns of the chunk come out roughly
right — the policy puts the fingertips down in about the neighbourhood the
teacher used — while the heading carried in the last two comes out about thirty
degrees away from the teacher's, which is enough that on a crowded table the
jaw meets a neighbour while it is still coming down, and the push ends before
any glass is touched.

## 2. The pushes are what this contributes

One point about the output has to be clear, because it decides what a
comparison with this solution is a comparison of.

**This solution emits waypoints directly, and nothing expands them.** [The test
bench](../02_the-test-bench.md) owns a macro that turns a parameterised push into a
descent, a feel, a slide, a back-off and a lift, and the solutions that think
in parameterised pushes go through it. A chunk is already a jaw trajectory, so
there is nothing for the macro to do. The bench carries the waypoints out as
given, through `Bench.follow`, which is built.

**Two small things travel beside the waypoints, and they are not the
policy's.** The bench's chunk carries the glass it is meant to move and the
place the solution expects that glass to arrive, because the scorecard counts
pushes per glass and measures how far each glass ended from its aim. A policy
whose output is a run of waypoints produces neither. Both are therefore read
back off the chunk after the fact: the glass is the one the jaw ends up
against, and the aim is that last fingertip moved forward by half the glass's
measured width, which is the convention [one fixed
nudge](../04_one-fixed-nudge/01_what-it-is.md) uses. Nothing about that reaches the policy or
changes the motion. It is bookkeeping for the scorecard, and it is named here
because it is the one place where this solution's output is not literally the
whole answer.

**The score is the outcome, not the action.** The bench does not ask whether
the chunk was the chunk it would have chosen, or whether the waypoints were
smooth. It looks only at the table afterwards: which glasses have room, which
are standing, where each one ended up, and how many pushes it took. That is
what makes a three-number push and a chunk of a hundred-odd waypoints comparable at
all, and it is the only reason this solution and its teacher can be set side by
side.

**Everything else in the pipeline is shared, so a difference in the score
belongs to the policy.** The tables are the bench's. The measurements are the
bench's, carrying the measured error of [telling the glasses
apart](../../08_seeing-the-glasses/11_the-results.md). The destinations come
from [the target layout](../01_the-problem/02_the-target-layout.md), computed
once per arrangement and so every solution that aims at a destination aims at
the same places, rather than at an easier arrangement than another. The topple
limit and the refusal rule come from [pushing without
toppling](../01_the-problem/03_pushing-without-toppling.md). What this solution
contributes is one mapping — from a picture of the table to a short run of
waypoints — and nothing else.

There is a pleasing detail in how the shared parts reach this solution, and it
is worth noticing because it explains what the policy is really learning. The
target layout never appears inside the network. It reached the demonstrations,
because the teacher aimed at it, and the demonstrations are all the policy ever
saw. In the same way, the bench's macro never appears inside the network, but
the waypoints it produced are the labels the network was fitted to, so **the
student's action space is the teacher's macro, written down as motion.** The
policy begins by being able to express only what the macro expressed, and
whatever it learns beyond that comes from generalising between those examples
rather than from being given a wider vocabulary.

## 3. How the concepts fit together

The pieces now join into one pipeline. It has an offline half that happens once
and an online half that happens on every push, and the halves are worth keeping
apart because almost all the cost is in the first and almost all the risk is in
the second.

**Offline, and once.** Tables are drawn from numbers below the dividing line.
The teacher is run over them. For every push it chooses, three things are
recorded: the view of the table from the top at that moment, the waypoints the
bench's macro produced, and the bench's verdict on what happened to the table
afterwards. Pushes that failed are dropped and the dropping is counted, so the
thinning is visible. Refusals are kept as refusals. What remains is a dataset
of pairs — a picture, and a chunk of waypoints — which is exactly the shape
behaviour cloning needs. One detail of the shape is worth naming, because the
document above does not settle it: a recorded path is a few hundred waypoints
long and a chunk is a fixed, shorter run, so every demonstration is trimmed to
the part at push height and resampled to the chunk's length. The trimming is
free, because the bench does the descent and the lift itself. The resampling is
not free: waypoints are consumed at a fixed rate, so squeezing a long push into
a fixed chunk runs it faster than it was demonstrated. The chunk's length is
therefore set near the median length of the teacher's own pushes, and a push
longer than that is replayed quicker than it was made.

ACT is then fitted on the dataset from random numbers, for hours. The second
rung fits Diffusion Policy on the same dataset, changing the model and nothing
else. Both are fitted several times with different seeds, because one training
run is not a measurement.

**Online, on every push.** The arm looks at the table and racks every glass
that already has room. The shared topple limit is then evaluated on every
glass still standing there, before the policy is asked anything, and a glass
that fails it is refused with its reason and taken out of play. Only then does
the straight-down view go into the policy, which returns one action chunk; the
chunk is charged to one of the glasses the limit left in play, so a refused
glass can never be pushed. The bench carries the chunk out: the closed jaw is
placed clear above the first waypoint, comes down to it, follows the waypoints
one control period apart, and lifts clear, reporting what it felt in the same
words a parameterised push reports. The arm looks again. The loop repeats
until every glass has room, or the glasses that are left have all been
refused, or the push budget is spent.

Three things are worth holding on to from all of that.

**Nothing in the method represents pushing.** There is no friction coefficient,
no slide prediction, no candidate list and no geometry inside the policy. The
consequences of friction are in the data, and what the network holds is a
mapping, not an understanding. This is the most economical of the six in terms
of what somebody had to know in order to build it.

**The loop is what makes copying survivable.** A cloned policy run open-loop
over a whole run would compound its own error. Run one chunk at a time against
a freshly measured table, it is re-anchored on every push. The method and the
loop are a pair; neither would be sensible here without the other.

**The ceiling is the teacher.** Every label this policy ever saw came from the
teacher, and nothing in behaviour cloning evaluates an outcome. So the student
has no mechanism by which to discover a better choice of glass, or a better
destination, than the one it was shown. The next sections are about what that
does and does not rule out.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
