# The code

This page shows the main code of this solution. It also says what the solution
hands back to the rest of the cell. It follows [what it is](01_what-it-is.md).
[How it works](03_how-it-works.md) then explains what the code is doing.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The pushes are what this contributes](#2-the-pushes-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code that does the work

This solution imports everything it shares with [solution
5](../08_a-foundation-model-as-it-downloads/01_what-it-is.md). So only the
training code is new. It has two pieces. The first says which parts of the
borrowed model the correction may change. The second turns a real push into a
training example.

The first piece is in
[`06-smolvla-fine-tuned/correction.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/correction.py).
It runs in three steps.

1. Set the three choices this project makes about the correction. These are
   the width of its squeeze, which is sixteen numbers, how hard it may pull,
   and which weight tables it is added to.
2. Bring in PEFT, the library that builds the correction. LeRobot trains whole
   policies and has no low-rank adaptation of its own, so PEFT is borrowed.
3. Add a new correction beside each named table. Freeze every borrowed number,
   so the optimiser can move only the correction. Hand the model back, ready
   to train.

Only step 1 holds a decision of this project. Its three settings are the whole
of that decision.

```python
# Step 1: set how narrow the correction's squeeze is -- sixteen numbers, the usual starting rank
RANK = 16
# Step 1: set how hard the correction may pull -- twice the rank, the usual pairing, which
# keeps its effect the same whatever rank it was fitted at
SCALING = 32
# Step 1: name the only tables the correction is added to -- attention's four projections
TABLES = ("q_proj", "k_proj", "v_proj", "o_proj")

...

def with_correction(policy, rank: int = RANK, scaling: int = SCALING):
    ...
    # Step 2: bring in the library that builds the correction -- PEFT, because LeRobot has none
    from peft import LoraConfig, get_peft_model

    # Step 3: add a correction beside each named table -- and freeze all the borrowed numbers
    policy.model = get_peft_model(
        policy.model,
        LoraConfig(r=rank, lora_alpha=scaling, lora_dropout=0.0, bias="none", target_modules=list(TABLES)),
    )
    # Step 3: hand back the same model, with only the correction left free to move
    return policy
```

`TABLES` names the four projections of every attention layer, and nothing
else. So the correction can change what the model pays attention to. It cannot
change the other tables. [Low-rank
adaptation](03_how-it-works.md#2-low-rank-adaptation--a-small-correction-instead-of-a-large-change)
explains this trade.

The training targets are built in
[`06-smolvla-fine-tuned/chunks.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/chunks.py).
This is a separate file, so its steps start from one again. It has four steps.
None of them invents a path.

1. Cut the recorded push down to the flat part, where the jaw moves forward at
   push height. Drop the recording if the jaw barely moved, because it holds
   no push to learn from.
2. Resample that part to the fifty waypoints a chunk holds. Fifty is the
   borrowed model's own number.
3. Drop the recording if a round trip through solution 5's convention moves
   it. The model cannot ask for such a push, so it is not a target.
4. Turn the waypoints into the numbers the model outputs. Check the shape, and
   raise an error if it is wrong, because a wrong shape is a bug in this file.

```python
def demonstration(path: tuple[Waypoint, ...]) -> np.ndarray | None:
    ...
    # Step 1: cut the recording down to the flat stretch the model has to produce
    part = pushing_part(path)
    # Step 1: drop it if the jaw barely moved -- there is no push in it to learn from
    if len(part) < 2 or across(part) < LEAST_ACROSS:
        return None
    # Step 2: resample that stretch to the fifty waypoints a chunk holds -- the model's own number
    waypoints = resampled(part)
    # Step 3: drop it if a round trip through the convention moves it -- it is not a target then
    if drift(waypoints) > FAITHFUL:
        return None
    # Step 4: read the waypoints into the numbers the model emits -- the units its answers are in
    action = as_action(waypoints)
    # Step 4: check the chunk is the shape the training expects -- a wrong shape is a bug here
    if action.shape != (CHUNK, SLOTS):
        raise AssertionError(f"a chunk is ({CHUNK}, {SLOTS}), not {action.shape}")
    return action
```

Step 2 has a side effect. A recorded push has two or three times fifty
waypoints. Squeezing it into fifty does not change where the jaw goes. It
changes how fast the jaw goes. This is because the examiner uses one waypoint
every fifty milliseconds, however far apart they are.

![One recorded push of 75 mm drawn twice: as the teacher made it, where no waypoint is more than 1.0 mm from the last because the teacher never pushes faster than 20 mm/s, and as the fifty waypoints the model is trained to emit, 1.5 mm apart, which the examiner eats at the same rate and therefore carries out at 31 mm/s.](../../images/pushing-the-glasses-apart/the-same-model-fine-tuned-here/finetuned-the-same-push-in-fewer-waypoints.png)

The second block also borrows its arithmetic from solution 5. `as_action` and
`drift` call `to_state` and `to_jaw`, which are solution 5's own. [`partners.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/partners.py)
re-exports them here, along with solution 5's `clear` loop. [`correction.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/06-smolvla-fine-tuned/correction.py)
declares `class Fitted(Downloaded)`, so the asking is inherited too. So the
targets use the same units as solution 5's answers, through the same code. The
only difference between the two solutions is the training.

The code makes chunks of waypoints. The next section says why those chunks are
all this solution adds.

## 2. The pushes are what this contributes

The code above produces chunks. This section says what else the cell provides,
so that the comparison with solution 5 is clear.

**This solution adds action chunks and nothing else.** It does not choose
where the glasses should end up. [The target
layout](../01_the-problem/04_the-target-layout.md) does that once, for all six
solutions. It does not own the topple check or the loop of plan, feel and look
again. It never makes a parameterised push. It outputs waypoints, and the
examiner carries them out as they are.

The examiner scores the table afterwards, not the action. [What must come
out](../01_the-problem/02_what-goes-in-and-what-comes-out.md#6-what-must-come-out)
explains why this lets a chunk and a three-number push be compared fairly.

So **a difference in the score comes from the chunks**. Solution 5 also adds
only chunks. This is why the gap between the two can be read.

The next section puts all the parts together in one picture.

## 3. How the concepts fit together

The sections above showed the pieces. Here they are in order.

1. Download a model trained on a large set of other people's robot recordings.
   Keep its numbers.
2. Run solution 2 over the training half of the tables. Record each push with
   the view from the top, the instruction and the joint readings at that
   moment.
3. Drop the recordings where something went wrong.
4. Train a small low-rank correction beside the borrowed numbers, until the
   model's chunks look like the teacher's pushes.
5. Fold the correction into the weights. The model that runs is the same size
   and speed as the original.

This closes the domain gap, because the model is trained on the pictures it
will see. It also puts the actions on this cell's scale. It does not add
anything the model has no input for, or anything the teacher never did.
[What fine-tuning closes, and what it cannot
touch](03_how-it-works.md#5-what-fine-tuning-closes-and-what-it-cannot-touch)
takes these gains and limits one at a time.

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
