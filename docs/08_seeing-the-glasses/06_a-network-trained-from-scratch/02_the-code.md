# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md), and [how it works](03_how-it-works.md) explains, part by
part, what the code below is doing. The second explains the first,
which is why they are on one page.

## Contents

1. [The network, in the code](#1-the-network-in-the-code)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The network, in the code

The network is written in
[`02-train-from-scratch/`](../../../code/src/08_seeing-the-glasses/02-train-from-scratch),
and the piece worth seeing is not its shape but what it is asked for. It
answers three numbers at every pixel of a half-size picture: one saying whether
the pixel is glass, and two holding the arrow to the middle of that pixel's own
glass.

The code runs in twenty steps, and the comments in it carry the same numbers.
Steps 1 to 7 build the answer the network is trained towards, steps 8 to 14 are
the network that produces it, and steps 15 to 20 turn its answer into one
glass's mask.

Steps 1 to 7 are in ``02-train-from-scratch/models.py``. Step 1 reads the
simulator's record of which glass each pixel shows, which is the answer key.
Step 2 makes room for three numbers at every pixel. Step 3 fills in the first of
them: one where a glass was seen, zero on the table. Step 4 notes the row and
column of every pixel, because an arrow has to be measured from somewhere. Steps
5 to 7 then run once for each glass in the scene. Step 5 works out where that
glass's rim middle falls in the picture. Step 6 picks out the pixels showing
that glass and no other. Step 7 writes, at each of those pixels, the arrow from
the pixel to that middle, divided by `VOTE_SCALE` so that the numbers sit near
one.

Steps 8 to 14 are the network, and this is where PyTorch does the work. Steps 8
to 10 are the down path: step 8 reads the picture at the size it arrived in,
step 9 halves it, and step 10 halves it again, so that a unit at the bottom sees
a wide patch of table. Steps 11 to 14 are the way back up, which is the same
pair of moves done twice. Step 11 enlarges the small block to half size and step
12 sets the half-size copy kept on the way down beside it; step 13 enlarges
again and step 14 sets the full-size copy beside that, then collapses the
channels into the three numbers asked for. The two `torch.cat` lines, steps 12
and 14, are those copies carried from the way down across to the way up.

```python
def top_target(picture: Picture, glasses) -> np.ndarray:
    """Per pixel: glass or not, and the offset to its rim's middle."""
    # Step 1: take the simulator's record of which glass each pixel shows, at the
    # half size the network works in -- this is the answer key
    ids = picture.ids[::SHRINK, ::SHRINK]
    # Step 2: make room for the three numbers wanted at every pixel
    target = np.zeros((3, *SMALL), dtype=np.float32)
    # Step 3: the first number is 1 where a glass was seen and 0 on the table
    target[0] = ids > 0
    # Step 4: the row and column of every pixel, to measure an arrow from
    rows, columns = np.indices(SMALL)
    for index, glass in enumerate(glasses):
        # Step 5: where this glass's rim middle sits in the picture -- the place
        # its own pixels have to point at
        column, row = rim_middle(picture, glass)
        # Step 6: the pixels showing this glass and no other
        mine = ids == index + 1
        # Step 7: at each of those pixels, the arrow to that middle, divided by
        # VOTE_SCALE so the numbers sit near one
        target[1][mine] = (column - columns[mine]) / VOTE_SCALE
        target[2][mine] = (row - rows[mine]) / VOTE_SCALE
    return target

class TopNet(nn.Module):
    ...
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Step 8: read the picture at the size it came in at, where fine detail is
        full = self.at_full(x)
        # Step 9: halve it, which loses exactly where things are and widens what
        # one unit can see
        half = self.at_half(full)
        # Step 10: halve it again, so a unit here sees a wide patch of table --
        # enough to tell which way its own glass's middle lies
        quarter = self.at_quarter(half)
        # Step 11: enlarge the small block back up to half size
        up = nn.functional.interpolate(quarter, size=half.shape[-2:])
        # Step 12: set the kept half-size copy beside it, so the detail the
        # halving threw away comes back
        up = self.up_half(torch.cat([up, half], 1))
        # Step 13: enlarge again, back to the size the picture came in at
        up = nn.functional.interpolate(up, size=full.shape[-2:])
        # Step 14: set the full-size copy beside it, then a window one pixel wide
        # turns the channels into the three numbers at every pixel
        return self.head(self.up_full(torch.cat([up, full], 1)))
```

Steps 15 to 20 are where the votes become one glass's mask, in
``02-train-from-scratch/pipeline.py``. Step 15 picks out the votes that landed
near one middle, and step 16 refuses a pile built from too few of them to be a
whole glass. Step 17 multiplies each voting pixel by `SHRINK`, which is how much
the picture was shrunk by, to get the corner of the block that pixel stands for.
Step 18 adds `_BLOCK`, the offsets of one shrunk pixel's own block, to every
corner, so the mask claims the whole block rather than the one sampled pixel.
Step 19 keeps those pixels inside the picture, and step 20 marks them in a mask
the size of the picture and hands it back.

```python
def pile_mask(picture: Picture, votes: Votes, middle) -> np.ndarray | None:
    """The pixels that voted for one middle, as a boolean mask, or None if too few did.
    ...
    """
    # Step 15: which votes landed close enough to this middle to belong to it
    mine = np.linalg.norm(votes.landed - middle, axis=1) < MIDDLE_RADIUS
    # Step 16: too small a pile is not a whole glass, so hand back nothing
    if mine.sum() < MIN_VOTES:
        return None
    # Step 17: the corner, in full-size pixels, of the block each voting pixel stands for
    corners = np.stack([votes.rows[mine], votes.columns[mine]], 1) * SHRINK
    # Step 18: grow every corner into its whole block, so the mask claims all the
    # pixels that voting pixel stood for
    pixels = (corners[:, None, :] + _BLOCK[None, :, :]).reshape(-1, 2)
    # Step 19: keep every one of those pixels inside the picture
    pixels = np.clip(pixels, 0, np.array(picture.depth.shape) - 1)
    # Step 20: mark them true in a picture-sized mask, which is what is handed back
    mask = np.zeros(picture.depth.shape, dtype=bool)
    mask[pixels[:, 0], pixels[:, 1]] = True
    return mask
```

Two things are worth reading off those. The borrowed library supplies the
layers and the training loop, while the idea — an arrow at every glass pixel
instead of a label — lives in the twelve lines that build the target, which is
this project's own arithmetic. And a mask here is a set of votes rather than a
drawn outline: nothing in either piece asks where a glass ends, and the only
line that mentions a boundary is step 19, which keeps a block inside the
picture.

## 2. The masks are what this contributes

Everything above produces one thing, and it is worth being plain about what
happens to it.

This solution contributes **only the masks**: which pixels in which picture are
which glass. Turning a mask into a place on the table and a rough width is the
examiner's job, done by one shared piece of arithmetic that every one of the six
solutions goes through, and it is described in the [test
examiner](../03_the-examiner/01_the-examiner.md). So a difference in the score belongs to the mask. This
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

A **survey picture** goes in, as a height-like channel made from the depth
reading and two channels saying where in the frame each pixel sits. The
**network**, whose down path and up path are shaped so that a unit near the
output can see 205 mm of table at once, produces two things at every pixel: a
**probability** that the pixel is glass, and an **arrow** towards the middle of
that pixel's own glass. The probability is thresholded into a **mask**. Every
mask pixel adds its arrow to its own position and casts a **vote**. The votes
pile up, one pile per glass, and the piles are counted without anything having
been told how many to expect. A pile with too few votes is doubted; a pile whose
fitted width is not one this kind of glass could have would be turned down by
the check prescribed above. What survives is one mask per glass, handed to the
examiner's shared arithmetic.

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

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
