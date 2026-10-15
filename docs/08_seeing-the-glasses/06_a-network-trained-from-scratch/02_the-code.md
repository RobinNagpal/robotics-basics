# The code

This page shows the main code of this solution. It also says what the
solution hands back. [How it works](03_how-it-works.md) explains each part of
this code in more detail.

## Contents

1. [The network, in the code](#1-the-network-in-the-code)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The network, in the code

The network is written in
[`02-train-from-scratch/`](../../../code/src/08_seeing-the-glasses/02-train-from-scratch).
The network works on a half-size picture. At every pixel it gives three
numbers. The first says whether the pixel is glass. The other two hold the
arrow to the middle of that pixel's own glass.

The code runs in six steps. The comments in the code use the same step
numbers. Steps 1 and 2 build the answer the network is trained to give. Steps 3
and 4 are the network itself. Steps 5 and 6 turn its answer into one glass's
mask. A **mask** is a picture where each pixel is marked glass or not glass.

1. Build the first number at each pixel. It is 1 where a glass was seen and 0
   on the table. It comes from the simulator's record of which glass each pixel
   shows.
2. Build the other two numbers. They hold the arrow from a pixel to the middle
   of its own glass's rim. The arrow is divided by `VOTE_SCALE` so the numbers
   are near one. This runs once for each glass.
3. Go down the network. Read the picture at its own size, then halve it twice.
   A unit at the bottom then sees a wide patch of table.
4. Come back up the network. Enlarge twice, and put the copy kept on the way
   down beside each enlargement. Then reduce the channels to the three numbers.
5. Gather the votes that landed near one middle. Refuse a pile with too few
   votes to be a whole glass.
6. Grow each voting pixel back into the block of pixels it stands for. Keep
   those pixels inside the picture, and mark them in a full-size mask.

Steps 1 to 4 are in ``02-train-from-scratch/models.py``. Steps 1 and 2 are the
answer key. Step 2 needs the row and column of every pixel, because an arrow
is measured from somewhere. Steps 3 and 4 use PyTorch. The two `torch.cat`
lines in step 4 bring the kept copies from the way down to the way up.

```python
def top_target(picture: Picture, glasses) -> np.ndarray:
    """Per pixel: glass or not, and the offset to its rim's middle."""
    # Step 1: take the simulator's record of which glass each pixel shows, at the
    # half size the network works in -- this is the answer key
    ids = picture.ids[::SHRINK, ::SHRINK]
    # Step 1: make room for the three numbers wanted at every pixel
    target = np.zeros((3, *SMALL), dtype=np.float32)
    # Step 1: the first number is 1 where a glass was seen and 0 on the table
    target[0] = ids > 0
    # Step 2: the row and column of every pixel, to measure an arrow from
    rows, columns = np.indices(SMALL)
    for index, glass in enumerate(glasses):
        # Step 2: where this glass's rim middle sits in the picture -- the place
        # its own pixels have to point at
        column, row = rim_middle(picture, glass)
        # Step 2: the pixels showing this glass and no other
        mine = ids == index + 1
        # Step 2: at each of those pixels, the arrow to that middle, divided by
        # VOTE_SCALE so the numbers sit near one
        target[1][mine] = (column - columns[mine]) / VOTE_SCALE
        target[2][mine] = (row - rows[mine]) / VOTE_SCALE
    return target

class TopNet(nn.Module):
    ...
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Step 3: read the picture at the size it came in at, where fine detail is
        full = self.at_full(x)
        # Step 3: halve it, which loses exactly where things are and widens what
        # one unit can see
        half = self.at_half(full)
        # Step 3: halve it again, so a unit here sees a wide patch of table --
        # enough to tell which way its own glass's middle lies
        quarter = self.at_quarter(half)
        # Step 4: enlarge the small block back up to half size
        up = nn.functional.interpolate(quarter, size=half.shape[-2:])
        # Step 4: set the kept half-size copy beside it, so the detail the
        # halving threw away comes back
        up = self.up_half(torch.cat([up, half], 1))
        # Step 4: enlarge again, back to the size the picture came in at
        up = nn.functional.interpolate(up, size=full.shape[-2:])
        # Step 4: set the full-size copy beside it, then a window one pixel wide
        # turns the channels into the three numbers at every pixel
        return self.head(self.up_full(torch.cat([up, full], 1)))
```

Steps 5 and 6 are in ``02-train-from-scratch/pipeline.py``. There the votes
become one glass's mask. In step 6, the growing takes two lines. Each voting
pixel is multiplied by `SHRINK`, the amount the picture was shrunk by. This
gives the corner of the block that pixel stands for. Then `_BLOCK`, the list
of offsets inside one block, is added to every corner. So the mask claims the
whole block, not just one pixel.

```python
def pile_mask(picture: Picture, votes: Votes, middle) -> np.ndarray | None:
    """The pixels that voted for one middle, as a boolean mask, or None if too few did.
    ...
    """
    # Step 5: which votes landed close enough to this middle to belong to it
    mine = np.linalg.norm(votes.landed - middle, axis=1) < MIDDLE_RADIUS
    # Step 5: too small a pile is not a whole glass, so hand back nothing
    if mine.sum() < MIN_VOTES:
        return None
    # Step 6: the corner, in full-size pixels, of the block each voting pixel stands for
    corners = np.stack([votes.rows[mine], votes.columns[mine]], 1) * SHRINK
    # Step 6: grow every corner into its whole block, so the mask claims all the
    # pixels that voting pixel stood for
    pixels = (corners[:, None, :] + _BLOCK[None, :, :]).reshape(-1, 2)
    # Step 6: keep every one of those pixels inside the picture
    pixels = np.clip(pixels, 0, np.array(picture.depth.shape) - 1)
    # Step 6: mark them true in a picture-sized mask, which is what is handed back
    mask = np.zeros(picture.depth.shape, dtype=bool)
    mask[pixels[:, 0], pixels[:, 1]] = True
    return mask
```

PyTorch gives the layers and the training loop. The main idea, an arrow at
every glass pixel, is in the twelve lines that build the target. Those lines
are this project's own arithmetic. Also, nothing in this code asks where a
glass ends. The only line about an edge is the clipping line in step 6. It
keeps a block inside the picture.

The next section says what happens to the masks this code makes.

## 2. The masks are what this contributes

The code above ends with masks. This section says where they go.

This solution hands back only masks. The examiner's shared arithmetic turns
each mask into a place and a width, the same way for all six solutions. [The
examiner](../03_the-examiner/01_the-examiner.md#6-what-must-come-back)
explains this. So any score difference comes from the masks.

The next section puts the code's steps in one line.

## 3. How the concepts fit together

The two sections above showed the code and its output. This section joins
them into one chain.

A survey picture goes in. The network gives each pixel a chance of being glass
and an arrow. A threshold on the chance gives the glass pixels. Each glass
pixel adds its arrow to its position and casts a vote. The votes form piles,
one per glass. A pile with too few votes is refused. Each pile that is left
becomes one mask, and the masks go to the examiner.

[How it works](03_how-it-works.md) explains each link in this chain.

← [What it is](01_what-it-is.md) · [How it works](03_how-it-works.md) →
