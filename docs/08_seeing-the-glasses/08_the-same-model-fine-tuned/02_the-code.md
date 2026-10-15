# The code

This page shows the main code of this solution. It also says what the solution
hands back to the rest of the cell. It follows [what it is](01_what-it-is.md).
The next page, [how the model is trained](03_how-the-model-is-trained.md),
explains the training step line by line.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)

## 1. The code that does the work

Training is the only thing that separates this solution from [solution
3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md). So the first code
to read is the training step.

The training step is in
[`04-yolo-fine-tuned/yolo_fine_tuned.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/yolo_fine_tuned.py).
It runs in three steps.

1. Take the scenes and hold every fourth one back. The training run checks its
   own progress on those. Then write both parts to disk as pictures and label
   files, because Ultralytics only reads a training set in that shape.
   [`dataset.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/dataset.py)
   does the writing.
2. Load the downloaded weights. This is the same file that solution 3 uses
   unchanged. Then continue the model's training on these pictures. This takes
   one line, because the library runs the training loop.
3. Copy the best weights from the run into this project's own file.
   [`run.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/04-yolo-fine-tuned/run.py)
   loads that file later.

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

The trained model's answers then go through `Finder.find`, in the same file.
This code is short. There is only one class, so there is no filter on category
names. The only check left is the width check against the kind of glass. A
candidate that the edge of the picture cuts short is excused from that check.

Two more steps follow. Training happens once. These two steps run on every
picture afterwards.

4. Look up the narrowest and the widest footprint a glass of this kind can have.
   Then go through the model's candidates, surest first. Turn each candidate's
   mask into a place on the table and a width. Every solution shares this
   arithmetic, in
   [`bench/masks_to_glasses.py`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/02-segment-glasses/bench/masks_to_glasses.py).
5. Keep a candidate if its width suits the kind. Also keep it if the edge of the
   picture cut its mask short. Report every other candidate as a doubt. Also
   report a doubt when a mask has too few depth readings to place. Last, keep
   one report per place on the table, so two masks on one glass become one
   answer.

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

These two blocks are where this solution differs from solution 3. The rest of
the two folders is the same. Solution 3 calls the library once, to ask about a
picture. Then most of its code filters the borrowed category names. This
solution calls the library twice: once to train and once to ask about a picture.
It has no list of category names. The width check is the one difference that
training did not bring. The next section says what it is for.

## 2. The masks are what this contributes

The code above ends by handing on masks. This section says what happens to them
next, and which part is this solution's own.

[The examiner](../03_the-examiner/01_the-examiner.md#6-what-must-come-back) turns
every solution's masks into places and widths in the same way. So a difference
in score comes from the masks. Solution 3 also hands over only masks. This is
why the gap between the two shows the effect of training.

The width check in steps 4 and 5 is the one thing this solution adds after the
model. Solution 3 has none, on purpose. The check can only turn a reported glass
into a doubt, never the other way round. So it cannot make this solution look
better than it is. The check is skipped for a mask that reaches the edge of the
picture. A width read from part of a footprint is not the glass's width. [The
results](../11_the-results.md) gives the measurement that showed why this
exemption is needed.

The next page, [how the model is trained](03_how-the-model-is-trained.md),
explains the one training line in step 2. That line is the whole difference
between this solution and solution 3.

← [What it is](01_what-it-is.md) · [How the model is trained](03_how-the-model-is-trained.md) →
