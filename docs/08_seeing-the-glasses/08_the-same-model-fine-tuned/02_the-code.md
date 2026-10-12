# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. It follows [what it
is](01_what-it-is.md), and [how the model is trained](03_how-the-model-is-trained.md)
then takes the training step below apart line by line.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)

## 1. The code that does the work

One thing separates this solution from [solution
3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md), and it is the
training. So the piece worth reading first is the fitting step.

The fitting step is in
[`04-yolo-fine-tuned/yolo_fine_tuned.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/yolo_fine_tuned.py),
and it runs in three steps.

1. Take the scenes it was handed, hold every fourth one back so the training run
   has pictures to check its own progress on, and write both parts out as a
   directory of pictures and label files, which is the only shape Ultralytics
   reads a training set from. The writing is done by
   [`dataset.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/dataset.py).
2. Pick up the downloaded weights, the same file solution 3 runs untouched, and
   continue that model's training on these pictures. The continuing is a single
   line, because the borrowed library owns the training loop.
3. Copy the best weights the run produced into a file of this project's own,
   which is what [`run.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/run.py) loads afterwards.

```python
def fit(examples: Iterable[data.Example], *, amodal: bool, save: Path, epochs: int = EPOCHS) -> Mapping:
    ...
    # Step 1: draw the scenes and hold every fourth one back -- the run checks itself on those
    drawn = list(examples)
    fitting = [example for place, example in enumerate(drawn) if place % CHECK_EVERY]
    checking = [example for place, example in enumerate(drawn) if not place % CHECK_EVERY]
    ...
    from ultralytics import YOLO

    # Step 1: write both parts out as pictures and label files -- the only shape Ultralytics reads
    described, counts = dataset.build(fitting, checking)
    # Step 2: pick up the downloaded weights -- the same file solution 3 runs untouched
    model = YOLO(str(borrowed()), task="segment")
    # Step 2: continue that model's training on these pictures -- the one line that does the work
    model.train(
        data=str(described),
        epochs=epochs,
        imgsz=PICTURE,
        batch=BATCH,
        device=device.pick(),
        ...
        seed=FITTING_SEED,
        deterministic=True,
        plots=False,
        verbose=False,
    )
    # Step 3: copy the run's best weights out -- this file is what run.py loads later
    shutil.copy(model.trainer.best, save)
```

What the fitted model's answers then go through is in the same file, in
`Finder.find`, and it is short for the reason the training makes it short. There
is no filter on category names here, because there is one class, so the only
judgement left is the width check against the kind and the exemption for a
candidate the frame cut short.

Two more steps run, and their numbers carry on from the fitting step, because
the fitting happens once and these run on every picture afterwards.

4. Look up the narrowest and the widest footprint a glass of the known kind
   could have, then walk the model's candidates surest first, turning each
   candidate's mask into a place on the table and a width by arithmetic every
   solution in the chapter shares, in
   [`bench/masks_to_glasses.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/bench/masks_to_glasses.py).
5. Keep a candidate whose width suits the kind, and keep one whose mask the
   frame cut short whatever its width. Every candidate left is reported as a
   doubt, as is one with too few depth readings to place at all, and what
   survives is reduced to one report per place on the table, so two masks
   landing on one glass become one answer.

```python
    def find(self, picture, kind: str) -> tuple[list[Found], list[str]]:
        ...
        # Step 4: look up the narrowest and widest footprint a glass of this kind could have
        narrowest, widest = data.widths(kind)
        kept: list[Found] = []
        doubts: list[str] = []
        # Step 4: walk the model's candidate masks, surest first -- one candidate per object found
        for mask in self.candidates(picture)[0]:
            # Step 4: turn one mask into a place and a width -- arithmetic every solution shares
            found = masks_to_glasses.one_glass(picture, mask)
            # Step 5: too few depth readings to place it -- report a doubt instead of a glass
            if found is None:
                doubts.append(TOO_LITTLE)
            # Step 5: keep it if its width suits the kind -- a frame-cut mask is excused the check
            elif narrowest <= found.width <= widest or found.cut_off:
                kept.append(found)
            else:
                # Step 5: no glass of this kind is this wide -- report a doubt, never a glass
                doubts.append(NO_SUCH_WIDTH)
        # Step 5: leave one report per place on the table -- two masks on one glass become one
        return masks_to_glasses.one_per_place(kept, narrowest), doubts
```

Read beside solution 3's own code section, those two blocks are where the pair
differs and the rest of both folders is where it does not. Solution 3 reaches
the library once, to ask it about a picture, and then spends its lines filtering
borrowed category names. This one reaches the same library twice, once to
continue its training and once to ask it about a picture, and holds no list of
category names anywhere. The width check in the second block is the one
difference the training did not bring, and the section on what this solution
contributes says what it is for.

## 2. The masks are what this contributes

The code above ends by handing masks on, and this section says what happens to
them afterwards and which part of that is this solution's own.

[The examiner](../03_the-examiner/01_the-examiner.md#6-what-must-come-back) turns
every solution's masks into places and widths by the same arithmetic, so a
difference in the score belongs to the mask. This solution contributes only the
masks, and so does solution 3, which is why the gap between the two can be read
as the effect of training.

The one thing this solution adds after the model is the width check in step 4
and step 5, and solution 3 deliberately has none. A candidate whose footprint
no glass of the known kind could have is reported as a doubt. That check can
only turn a reported glass into a doubt and never the other way round, so it
cannot flatter this side of the comparison. It stands down for a mask that
reaches the edge of the picture, because a width read off part of a footprint
is not the glass's width. [The results](../11_the-results.md) gives the
measurement that showed the check had been refusing those cut-off masks.

The next page, [how the model is trained](03_how-the-model-is-trained.md), opens
up the one line in step 2 that does the training, because that line is the
whole difference between this solution and solution 3.

← [What it is](01_what-it-is.md) · [How the model is trained](03_how-the-model-is-trained.md) →
