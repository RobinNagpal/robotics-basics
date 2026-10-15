# The code

This page shows the main code of this solution. It also says what the solution
hands back to the rest of the cell. [What it is](01_what-it-is.md) explains the
idea that this code carries out.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The code that measured the failure](#2-the-code-that-measured-the-failure)
3. [The masks are what this contributes](#3-the-masks-are-what-this-contributes)
4. [How the concepts fit together](#4-how-the-concepts-fit-together)

## 1. The code that does the work

Most of this solution is somebody else's code. So the part worth reading is small.
It is one call into the borrowed library, and a few lines that choose what to
keep. Those lines are all that this project wrote.

The code is in the `robot-arm-projects` repository, in the folder
`v5-pick-glasses/02-segment-glasses/03-yolo-zero-shot/`. The main file is
[`03-yolo-zero-shot/yolo_zero_shot.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/03-yolo-zero-shot/yolo_zero_shot.py).
The library is Ultralytics. `YOLO` is the model. `attempt_download_asset` fetches
the weights. `model.predict` is the one line where the borrowed model does its work.

One picture becomes a list of masks in four steps. The comments in the code use
the same step numbers.

1. Load the borrowed model. The weights download on the first picture and are
   read from disk after that.
2. Shade the depth picture into the three-channel picture the model expects. Run
   the model on it. Bring the answer back into ordinary memory.
3. Read the name and the confidence of each outline. Keep the outlines named as a
   drinking vessel with a confidence of at least 0.25. Sort them, surest first.
4. Fill each kept outline into a mask. Drop a mask that covers mostly the same
   pixels as a surer one.

`Finder.find` runs these steps. The examiner calls it once for each picture. It
calls `look`, which does steps 1 and 2. Then it calls `masks_from`, which does
steps 3 and 4. Then it hands each mask to the examiner's shared arithmetic, which
turns the mask into a place on the table. Only the most important lines are
shown here.

```python
class Finder:
    def find(self, picture, kind: str) -> tuple[list[Found], list[str]]:
        # Steps 1 and 2 in look, then steps 3 and 4 in masks_from.
        masks = masks_from(look(picture), picture.depth.shape)
        if not masks:
            return [], ["the model named nothing in this picture a drinking vessel"]
        ...
        for mask in masks:
            # The examiner's arithmetic, not this solution's, turns a mask into a place.
            one = masks_to_glasses.one_glass(picture, mask)
            ...
        return found, doubts
```

The two functions it calls are below, with the function that loads the model.
In the file, the filtering comes before the call that makes its input. So the
step numbers below do not read from top to bottom.

```python
# Step 1: load the borrowed model once and keep it -- every later picture reuses it for free.
@lru_cache(maxsize=1)
def _model():
    ...
    from ultralytics import YOLO
    from ultralytics.utils.downloads import attempt_download_asset
    ...
    # Step 1: fetch the weights, downloading them if missing -- none of them was fitted here.
    return YOLO(attempt_download_asset(CACHE / MODEL)), device.pick()

...

def masks_from(answer, shape: tuple[int, int]) -> list[np.ndarray]:
    ...
    # Step 3: read the model's own list of category names -- the numbering belongs to the weights.
    names: Mapping[int, str] = answer.names
    # Step 3: read how sure the model was about each outline -- only their order is worth trusting.
    confidences = np.asarray(answer.boxes.conf, dtype=float).ravel()
    # Step 3: keep the outlines named a drinking vessel that also clear the bar -- name, then score.
    keep = drinking_vessels.are_drinking_vessels(answer.boxes.cls, names) & above_the_bar(confidences)
    # Step 3: put the outlines in order, surest first -- so a repeated glass keeps its better mask.
    surest = sorted(range(len(confidences)), key=lambda index: -confidences[index])
    # Step 4: fill every kept outline into a mask, surest first, and drop the ones that repeat.
    return merge_doubles(outline_to_mask(answer.masks.xy[index], shape) for index in surest if keep[index])

def look(picture) -> object:
    ...
    # Step 1: ask for that model and its processor -- only the first picture pays for loading it.
    model, where = _model()
    # Step 2: shade the depth picture into the three-channel picture the model expects, and run it.
    answers = model.predict(
        pictures.shade(picture),
        conf=CONFIDENCE_BAR_SET_BY_HAND,
        device=where,
        verbose=False,
    )
    # Step 2: bring the answer back into ordinary memory -- the rest of the chain is plain numpy.
    return answers[0].cpu()
```

Step 3 tests names against a list in
[`03-yolo-zero-shot/drinking_vessels.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/03-yolo-zero-shot/drinking_vessels.py).
It is shown here because this solution promises that nothing was tuned to this
cell, and that promise covers this list too. Every name in it comes from the
model's own fixed list. No name was added after anybody saw what the model called
a glass here.

```python
VESSELS = ("wine glass", "cup")

...

NEIGHBOURS = ("bowl", "vase", "bottle")

# Step 3: the five names worth keeping, as one set to test against -- all read off the model's list.
ACCEPTED = frozenset(VESSELS + NEIGHBOURS)

def is_drinking_vessel(name: str) -> bool:
    """Whether one of the model's category names is kept."""
    # Step 3: say whether one of the model's names is on that list -- anything else is dropped.
    return name in ACCEPTED
```

The borrowed library is called in one place only. This project adds three
things: a cut-off on confidence, a filter on names, and the joining of a glass
that was reported twice. After that the names are gone, and only masks leave.
Nothing above reads a fitted file, because there is none. The folder has no
training command. Its `fit` function exists only to refuse. The cut-off, the
share of shared pixels that makes two outlines one, and the five names are
everything this solution chose. None of them came from this cell's data.

The next section shows one more file. It does not find glasses. It measures why
this solution fails.

## 2. The code that measured the failure

The code above explains what the solution does. This file explains why its score
is so low.
[`what_it_named.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/03-yolo-zero-shot/what_it_named.py)
runs the model on held-out arrangements with the name filter removed. It prints
every name the model gave. A scorecard only says that glasses were missed. This
file says which names the model used instead.
[Why it failed](03_results-and-comparison.md#2-why-it-failed-the-names-it-reached-for)
shows what it found, and why those names must not be added to the list.

The next section says what this solution hands back to the rest of the cell.

## 3. The masks are what this contributes

The section above showed how the failure was measured. This section shows where
the solution's job ends. The examiner fixes what goes in and what comes out, as
[what a solution is given](../03_the-examiner/01_the-examiner.md#4-what-a-solution-is-given)
explains. **This solution gives only the masks.** The examiner turns each mask
into a place, so any difference in score comes from the mask.

`merge_doubles` handles one case. A model can name one glass twice, under two
similar names. The examiner would count those two reports as a split. So
`merge_doubles` joins outlines that cover mostly the same pixels. In the marked
runs it never had to, because the scorecard records no split in any block.

A mask that claims pixels the camera never saw must name them, as
[how a mask becomes a record](../12_how-a-mask-becomes-a-record.md#4-why-a-mask-that-asserts-pixels-must-say-which-ones)
explains. That case does not happen here. This model outlines only pixels where
the glass was visible.

The last section puts these parts together.

## 4. How the concepts fit together

The sections above showed each part. This section shows the one decision behind
them all: **fit nothing here**. The names belong to somebody else, so they can
only filter. The outline belongs to somebody else, so its edge is only as fine as
that model makes it. The confidence belongs to somebody else, so it is not a
probability on these pictures. And the pictures are not like the ones the model
was trained on. That last point is what made the solution fail.

This decision makes the solution free to try. It also removes every way to fix
these four problems. The next page gives the results.

← [What it is](01_what-it-is.md) · [Results and comparison](03_results-and-comparison.md) →
