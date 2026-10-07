# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md), and [how it works](03_how-it-works.md) explains, part by
part, what the code below is doing. The second explains the first,
which is why they are on one page.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code that does the work

Everything this solution shares with [solution
5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md) is imported from
it rather than written again, so what is left to read is the fitting itself.
That is two pieces: which parts of the borrowed model the correction is allowed
to touch, and how a push the jaw really made becomes a training example.

The first piece is in
[`06-smolvla-fine-tuned/correction.py`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/correction.py),
and it runs in six steps.

Steps 1 to 3 are settings, and they are this project's only choice about the
correction. Step 1 sets the width of the squeeze the correction is forced
through, which is sixteen numbers. Step 2 sets how hard the correction is
allowed to pull. Step 3 names the weight tables it may be added to. Step 4
brings in PEFT, the library that builds the correction, which is borrowed
because LeRobot trains whole policies and has no low-rank adaptation of its
own. Step 5 adds a fresh correction beside each named table and freezes every
borrowed number, so the optimiser can move the correction and nothing else.
Step 6 hands the same model back, ready to train.

```python
# Step 1: set how narrow the correction's squeeze is -- sixteen numbers, the usual starting rank
RANK = 16
# Step 2: set how hard the correction may pull -- twice the rank, the usual pairing, which
# keeps its effect the same whatever rank it was fitted at
SCALING = 32
# Step 3: name the only tables the correction is added to -- attention's four projections
TABLES = ("q_proj", "k_proj", "v_proj", "o_proj")

...

def with_correction(policy, rank: int = RANK, scaling: int = SCALING):
    ...
    # Step 4: bring in the library that builds the correction -- PEFT, because LeRobot has none
    from peft import LoraConfig, get_peft_model

    # Step 5: add a correction beside each named table -- and freeze all the borrowed numbers
    policy.model = get_peft_model(
        policy.model,
        LoraConfig(r=rank, lora_alpha=scaling, lora_dropout=0.0, bias="none", target_modules=list(TABLES)),
    )
    # Step 6: hand back the same model, with only the correction left free to move
    return policy
```

`TABLES` names the four projections of every attention layer and nothing else,
so the correction can change what the model attends to and cannot change the
feed-forward tables at all. That is the trade [low-rank
adaptation](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
sets out, written down as four strings.

What the correction is fitted towards is built in
[`06-smolvla-fine-tuned/chunks.py`](../../../code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/chunks.py).
It is a separate file, so its steps are numbered from one again. Nothing in
them invents a path.

Step 1 cuts the recorded push down to the flat stretch the model has to
produce, which is the jaw at push height travelling forward. Step 2 throws the
recording away if the jaw barely moved across the table, because there is no
push in it to learn from. Step 3 resamples that stretch to the fifty waypoints
a chunk holds, which is the borrowed model's own number. Step 4 throws the
recording away if reading it through solution 5's convention and back out again
moves it, because a push the model cannot ask for is not a target. Step 5 reads
the waypoints into the numbers the model emits. Step 6 checks the result is the
shape the training expects, and raises if it is not, because a wrong shape here
is a mistake in this file rather than a bad recording.

```python
def demonstration(path: tuple[Waypoint, ...]) -> np.ndarray | None:
    ...
    # Step 1: cut the recording down to the flat stretch the model has to produce
    part = pushing_part(path)
    # Step 2: drop it if the jaw barely moved -- there is no push in it to learn from
    if len(part) < 2 or across(part) < LEAST_ACROSS:
        return None
    # Step 3: resample that stretch to the fifty waypoints a chunk holds -- the model's own number
    waypoints = resampled(part)
    # Step 4: drop it if a round trip through the convention moves it -- it is not a target then
    if drift(waypoints) > FAITHFUL:
        return None
    # Step 5: read the waypoints into the numbers the model emits -- the units its answers are in
    action = as_action(waypoints)
    # Step 6: check the chunk is the shape the training expects -- a wrong shape is a bug here
    if action.shape != (CHUNK, SLOTS):
        raise AssertionError(f"a chunk is ({CHUNK}, {SLOTS}), not {action.shape}")
    return action
```

Step 3 is the line with a consequence in it. A chunk holds fifty
waypoints, which is the borrowed model's own number, and a recorded push is two
or three times that many once the examiner has sampled it. Squeezing the longer
path into the shorter one does not change where the jaw goes; it changes how
fast it gets there, because the examiner consumes waypoints a fixed fifty
milliseconds apart whatever the gaps between them stand for.

![One recorded push of 89 mm drawn twice: as the teacher made it, where no waypoint is more than 1.0 mm from the last because the teacher never pushes faster than 20 mm/s, and as the fifty waypoints the model is trained to emit, 1.8 mm apart, which the examiner eats at the same rate and therefore carries out at 36 mm/s.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-the-same-push-in-fewer-waypoints.png)

The second block also borrows its arithmetic from its partner rather than
repeating it. `as_action` and `drift` call `to_state` and `to_jaw`, which are
solution 5's own, re-exported here by `partners.py` along with solution 5's
`clear` loop, and `correction.py` declares `class Fitted(Downloaded)` so that
the asking is inherited too. The targets are therefore written in the same
units the partner's answers are read in, by the same code, and the only
difference between the two solutions is that one of them was fitted.

## 2. The pushes are what this contributes

One point about the output has to be clear, because it decides what the
comparison with solution 5 is a comparison of.

**This solution contributes action chunks and nothing else.** It does not
compute where the glasses should end up: that is [the target
layout](../01_the-problem/02_the-target-layout.md), computed once from the
measurements and handed to all six, so that no solution can look good at
pushing by having aimed at an easier arrangement. It does not own the topple
check, the loop of plan, feel and look again, or the macro that turns a
parameterised push into a jaw trajectory — and it never produces a
parameterised push in any case. It emits waypoints, and the examiner carries
them out as they are.

That last point is the reason this solution is allowed to be itself. The
examiner could have insisted that every solution hand back the same handful of
push parameters, which sounds fairer and is not, because squeezing a chunked
policy down to three numbers destroys the action chunking that makes it work.
What the examiner does instead is score the outcome and never the action: which
glasses have room, which are standing, where each one ended up, and how many
pushes it took. So a three-number push and a chunk of fifty waypoints are
compared on the only thing this problem actually cares about, which is the
table afterwards.

It follows that **a difference in the score belongs to the chunks**. This
solution contributes the chunks and so does solution 5, which is exactly why
the gap between the two is readable.

## 3. How the concepts fit together

A model fitted on a very large pool of other people's teleoperation is
downloaded, and its borrowed numbers are kept rather than replaced. Solution 2
is run over the training half of the tables, and every push it makes is
recorded together with the view from the top, the one instruction and the joint
readings that were true at that moment. Those recordings are the examples, the
ones in which something went wrong are discarded, and the training moves a
small low-rank correction beside the borrowed numbers until the chunks the
model emits look like the teacher's pushes. The correction is then folded into
the weights, so what runs afterwards is a model of the original size and the
original speed.

What that buys is the domain gap closed, because the pictures the model was
fitted on are the pictures it is shown, and actions on this cell's own scale,
because the targets it was trained towards were this cell's own pushes. What it
does not buy is anything the model has no input for, anything the teacher never
did, and anything the shared machinery owns. [What fine-tuning closes, and what
it cannot
touch](03_how-it-works.md#5-what-fine-tuning-closes-and-what-it-cannot-touch)
is those gains and those limits taken one at a time.

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
