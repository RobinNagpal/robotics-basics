# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The network, in the code](#1-the-network-in-the-code)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The network, in the code

The network is written in
[`02-train-from-scratch/`](../../../code/src/08_seeing-the-glasses/02-train-from-scratch),
and the piece worth seeing is not its shape but what it is asked for. It
answers three numbers at every pixel of a shrunk picture: one saying whether
the pixel is glass, and two holding the arrow to the middle of that pixel's own
glass.

This is the answer it is trained towards, and the network that produces it,
from ``02-train-from-scratch/models.py``. The first function builds the target
out of the simulator's record of which glass each pixel shows. The second is
where PyTorch does the work, and the two `torch.cat` lines are the copies
carried from the way down across to the way up.

```python
def top_target(picture: Picture, glasses) -> np.ndarray:
    """Per pixel: glass or not, and the offset to its rim's middle."""
    ids = picture.ids[::SHRINK, ::SHRINK]
    target = np.zeros((3, *SMALL), dtype=np.float32)
    target[0] = ids > 0
    rows, columns = np.indices(SMALL)
    for index, glass in enumerate(glasses):
        column, row = rim_middle(picture, glass)
        mine = ids == index + 1
        target[1][mine] = (column - columns[mine]) / VOTE_SCALE
        target[2][mine] = (row - rows[mine]) / VOTE_SCALE
    return target

class TopNet(nn.Module):
    ...
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        full = self.at_full(x)
        half = self.at_half(full)
        quarter = self.at_quarter(half)
        up = nn.functional.interpolate(quarter, size=half.shape[-2:])
        up = self.up_half(torch.cat([up, half], 1))
        up = nn.functional.interpolate(up, size=full.shape[-2:])
        return self.head(self.up_full(torch.cat([up, full], 1)))
```

And this is where the votes become one glass's mask, from
``02-train-from-scratch/pipeline.py``. `SHRINK` is how much the picture was
shrunk by, and `_BLOCK` is the offsets of one shrunk pixel's own block, so the
mask claims the whole block each voting pixel stands for.

```python
def pile_mask(picture: Picture, votes: Votes, middle) -> np.ndarray | None:
    """The pixels that voted for one middle, as a boolean mask, or None if too few did.
    ...
    """
    mine = np.linalg.norm(votes.landed - middle, axis=1) < MIDDLE_RADIUS
    if mine.sum() < MIN_VOTES:
        return None
    corners = np.stack([votes.rows[mine], votes.columns[mine]], 1) * SHRINK
    pixels = (corners[:, None, :] + _BLOCK[None, :, :]).reshape(-1, 2)
    pixels = np.clip(pixels, 0, np.array(picture.depth.shape) - 1)
    mask = np.zeros(picture.depth.shape, dtype=bool)
    mask[pixels[:, 0], pixels[:, 1]] = True
    return mask
```

Two things are worth reading off those. The borrowed library supplies the
layers and the training loop, while the idea — an arrow at every glass pixel
instead of a label — lives in the twelve lines that build the target, which is
this project's own arithmetic. And a mask here is a set of votes rather than a
drawn outline: nothing in either piece asks where a glass ends, and the only
line that mentions a boundary is the one that keeps a block inside the picture.

## 2. The masks are what this contributes

Everything above produces one thing, and it is worth being plain about what
happens to it.

This solution contributes **only the masks**: which pixels in which picture are
which glass. Turning a mask into a place on the table and a rough width is the
examiner's job, done by one shared piece of arithmetic that every one of the six
solutions goes through, and it is described in the [test
examiner](../03_the-examiner.md). So a difference in the score belongs to the mask. This
solution cannot win by measuring more cleverly and it cannot lose by measuring
worse.

One consequence follows, and it is the same for all six. **No model here
produces a pose.** Models produce masks. The place comes from the depth
readings under the mask together with the camera's own pose, by arithmetic, and
a glass standing upright on a flat table has no orientation left to find.

## 3. How the concepts fit together

Everything above is one chain, and it is worth seeing the whole of it in order
before the failure cases, because each stage inherits what the last one got
wrong.

A **survey picture** goes in, with its depth reading and two channels saying
where in the frame each pixel sits. The **network**, whose down path and up
path are shaped so that a unit near the output can see a large part of the
scene, produces two things at every pixel: a **probability** that the pixel is
glass, and an **arrow** towards the middle of that pixel's own glass. The
probability is thresholded into a **mask**. Every mask pixel adds its arrow to
its own position and casts a **vote**. The votes pile up, one pile per glass,
and the piles are counted without anything having been told how many to expect.
A pile with too few votes is doubted; a pile whose fitted width is not one this
kind of glass could have would be turned down by the check prescribed above.
What survives is one mask per glass, handed to the examiner's shared arithmetic.

Three things in that chain are worth holding on to.

**The output shape is what makes the merge answerable.** A class map has
nowhere to record which glass a pixel belongs to, so no amount of training
could make one separate two joined glasses. An arrow has somewhere to record
it, and the separation falls out of counting rather than out of cutting.

**The loss is what most often goes wrong.** Most pixels in these pictures are
table, so a measure of success that counts pixels rewards a network for saying
nothing, and the fix is to score the overlap of the shape rather than the count
of the pixels.

**The arithmetic after the network is what keeps the whole thing honest.** The
network proposes; the vote count and the kind's own range of widths dispose. A
pile of votes implying a footprint no glass of this kind could have is turned
down by a rule nobody trained.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
