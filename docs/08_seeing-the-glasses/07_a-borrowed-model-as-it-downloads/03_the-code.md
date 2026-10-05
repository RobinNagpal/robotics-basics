# A borrowed model, as it downloads — the code

This page shows the code at the heart of this solution, and says exactly what
the solution hands back to the rest of the cell. The two belong on one page
because the second explains the first: the code is far easier to read once you
know which of its results leave this solution and which are working detail. By
the end you will be able to point at the lines that produce the masks, and to
see where the ideas of [how it works](02_how-it-works.md) meet.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code that does the work

This solution is almost entirely somebody else's code, so the part worth reading
is small: one call into the borrowed library, and the handful of lines that
decide what to keep out of the answer. Those lines are the whole of what this
project wrote, and seeing them is the quickest way to understand both what the
solution is and how little of it is this project's.

The call and the handling of its answer are in
[`03-yolo-zero-shot/yolo_zero_shot.py`](../../../code/src/08_seeing-the-glasses/03-yolo-zero-shot/yolo_zero_shot.py).
The library is Ultralytics: `YOLO` is the model, `attempt_download_asset` is
what fetches the weights, and `model.predict` is the one line where the borrowed
model does its work. Everything around it is this project's, and it is short.

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
outlined. And nothing above reads a fitted file, because there is none: the
folder has no training command at all, and its `fit` function exists only to
refuse. The bar on the confidence number, the share of pixels that makes two
outlines one, and those five names are everything this solution chose, and none
of it came from this cell's data.

## 2. The masks are what this contributes

It is worth stating plainly where this solution stops, because the boundary is
the same for all six and is what makes them comparable.

The input is fixed by the bench: for each survey picture, the grey picture
shaded from depth, the depth reading at every pixel, and the camera's own pose,
and nothing else. In particular no solution may read the simulator's record of
what it spawned. The output is fixed too: one record per glass, holding its mask
pixels, its place on the table and a rough width.

The step between the mask and the place belongs to [the test
bench](../03_the-test-bench.md) rather than to the solution. So **this solution
contributes only the masks**, and any difference in its score belongs to the
mask. It cannot win by measuring more cleverly and it cannot lose by measuring
worse. One consequence is worth repeating because it removes a question that
would otherwise be asked here: **no model in this book produces a pose.**
Models produce masks, the place comes from depth and the camera's own pose by
arithmetic, and a glass standing upright on a flat table has no orientation left
to find.

Two further points follow from that boundary. A single glass can be named twice,
under two neighbouring drinking-vessel categories, and arrive as two outlines
covering nearly the same pixels; the bench counts a real glass that collected
two reports as a split, so the design should merge outlines that cover
substantially the same pixels before it hands anything over, rather than leaving
the bench to count one glass twice. And a mask that asserts pixels the camera
never saw the glass at must say which ones, because the depth reading at such a
pixel belongs to whatever stood in front; that case does not arise here, since
the outlines this model returns mark only pixels where the object was actually
visible.

## 3. How the concepts fit together

The pieces now connect into one picture, and it is a short picture because the
solution is short.

A model fitted elsewhere would be shown this cell's grey picture from the top
and would return, for each thing it found, an outline and a name. The names come
from a general list, so they would be used only to decide which outlines are
worth keeping and then thrown away, because a borrowed category carries an
implied size that must not enter this project. The outlines are built from a
short weighted sum of coarse patterns and then enlarged, so they are good about
where a glass is and only approximate about where its edge lies, and the shared
arithmetic reads the width from that edge. The number beside each outline would
order them usefully but would mean nothing as a probability, because the
pictures are not what it was calibrated on. And the same change of pictures is
the main risk to the whole arrangement, since the light and the transparency
that tell a model it is looking at a glass are mostly absent from a grey picture
shaded from depth.

Every one of those is a consequence of one decision: **fit nothing here**. That
decision is what would make the solution free to try, and it is also what
removes every lever that would normally be pulled to fix the problems above.

← [A borrowed model, as it downloads — how it works](02_how-it-works.md) · [A borrowed model, as it downloads — a worked example](04_a-worked-example.md) →
