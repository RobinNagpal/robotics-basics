# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The code that measured the failure](#2-the-code-that-measured-the-failure)
3. [The masks are what this contributes](#3-the-masks-are-what-this-contributes)
4. [How the concepts fit together](#4-how-the-concepts-fit-together)

## 1. The code that does the work

This solution is almost entirely somebody else's code, so the part worth reading
is small: one call into the borrowed library, and the handful of lines that
decide what to keep out of the answer. Those lines are the whole of what this
project wrote.

The call and the handling of its answer are in
[`03-yolo-zero-shot/yolo_zero_shot.py`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/yolo_zero_shot.py).
The library is Ultralytics: `YOLO` is the model, `attempt_download_asset` is
what fetches the weights, and `model.predict` is the one line where the borrowed
model does its work.

```python
@lru_cache(maxsize=1)
def _model():
    ...
    from ultralytics import YOLO
    from ultralytics.utils.downloads import attempt_download_asset
    ...
    return YOLO(attempt_download_asset(CACHE / MODEL)), device.pick()

...

def masks_from(answer, shape: tuple[int, int]) -> list[np.ndarray]:
    ...
    names: Mapping[int, str] = answer.names
    confidences = np.asarray(answer.boxes.conf, dtype=float).ravel()
    keep = drinking_vessels.are_drinking_vessels(answer.boxes.cls, names) & above_the_bar(confidences)
    surest = sorted(range(len(confidences)), key=lambda index: -confidences[index])
    return merge_doubles(outline_to_mask(answer.masks.xy[index], shape) for index in surest if keep[index])

def look(picture) -> object:
    ...
    model, where = _model()
    answers = model.predict(
        pictures.shade(picture),
        conf=CONFIDENCE_BAR_SET_BY_HAND,
        device=where,
        verbose=False,
    )
    return answers[0].cpu()
```

The filter those lines call is in
[`03-yolo-zero-shot/drinking_vessels.py`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/drinking_vessels.py),
and it is worth showing rather than describing, because the solution's one
promise is that nothing in it was tuned to this cell and that promise covers
this list. Every name in it is one of the borrowed model's own categories, read
off its fixed list, and not one was added after anybody saw what the model
called a glass here.

```python
VESSELS = ("wine glass", "cup")

...

NEIGHBOURS = ("bowl", "vase", "bottle")

ACCEPTED = frozenset(VESSELS + NEIGHBOURS)

def is_drinking_vessel(name: str) -> bool:
    """Whether one of the model's category names is kept."""
    return name in ACCEPTED
```

Two things show from that. The borrowed library is reached in exactly one place,
and what this project contributes is a bar on the confidence number, a filter on
names, and the collapsing of a glass that arrived twice — after which the name
is gone and what leaves is a list of masks carrying no claim about what was
outlined. Nothing above reads a fitted file, because there is none: the folder
has no training command at all, and its `fit` function exists only to refuse.
The bar, the share of pixels that makes two outlines one, and those five names
are everything this solution chose, and none of it came from this cell's data.

## 2. The code that measured the failure

One more file is worth reading, because the result turns on it.
[`what_it_named.py`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/what_it_named.py)
runs the model over held-out arrangements and prints every name it offered, with
the filter removed. A scorecard says only that glasses were missed. This says
which names the model reached for instead, which is the difference between
knowing that the method failed and knowing why.

Its own docstring carries the rule that makes it safe to run: reading these
names and then adding them to the accepted list would be fitting the filter on
this cell's own data, which is the one thing this solution promises not to do.
The measurement is allowed. Acting on it is not.

## 3. The masks are what this contributes

The input is fixed by the examiner: for each survey picture, the grey picture
shaded from depth, the depth reading at every pixel, and the camera's own pose,
and nothing else. No solution may read the simulator's record of what it
spawned. The output is fixed too: one record per glass, holding its mask pixels,
its place on the table and a rough width.

The step between the mask and the place belongs to [the
examiner](../03_the-examiner/01_the-examiner.md) rather than to the solution. So
**this solution contributes only the masks**, and any difference in its score
belongs to the mask. It cannot win by measuring more cleverly and it cannot lose
by measuring worse. One consequence is worth repeating because it removes a
question that would otherwise be asked here: **no model in this book produces a
pose.** Models produce masks, the place comes from depth and the camera's own
pose by arithmetic, and a glass standing upright on a flat table has no
orientation left to find.

Two further points follow from that boundary. A single glass can be named twice,
under two neighbouring drinking-vessel categories, and arrive as two outlines
covering nearly the same pixels; the examiner counts a real glass that collected
two reports as a split, so `merge_doubles` collapses outlines that cover
substantially the same pixels before anything is handed over. In the marked runs
it never had to: the scorecard records no split and no merge in any block, which
is what a method that names almost nothing looks like. And a mask that asserts
pixels the camera never saw the glass at must say which ones, because the depth
reading at such a pixel belongs to whatever stood in front; that case does not
arise here, since the outlines this model returns mark only pixels where the
object was actually visible.

## 4. How the concepts fit together

Every part of this solution is a consequence of one decision: **fit nothing
here**. The names are somebody else's, so they can only filter. The outline is
somebody else's, so its edge is only as fine as the machinery that drew it. The
confidence number is somebody else's, so it means nothing as a probability on
these pictures. And the pictures are nothing like the ones the weights were
fitted on, which is what destroyed the whole arrangement.

That decision is what makes the solution free to try, and it is also what
removes every lever that would normally be pulled to fix any of those four.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
