# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The code that does the work](#1-the-code-that-does-the-work)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code that does the work

One thing separates this solution from [solution
3](../07_a-borrowed-model-as-it-downloads/01_what-it-is.md), and it is the training. So the piece worth reading
first is the fitting step: it is where the borrowed file is picked up, where the
borrowed library is asked to continue its training, and where the result is
written down as a file of this project's own.

The fitting step is in
[`04-yolo-fine-tuned/yolo_fine_tuned.py`](../../../code/src/08_seeing-the-glasses/04-yolo-fine-tuned/yolo_fine_tuned.py).
`borrowed()` is the downloaded file, the same one solution 3 runs untouched;
`dataset.build` writes the examiner's scenes out as the directory of pictures and
label files Ultralytics reads a training set from; and `model.train` is the one
line where the borrowed library does the work.

```python
def fit(examples: Iterable[data.Example], *, amodal: bool, save: Path, epochs: int = EPOCHS) -> Mapping:
    ...
    from ultralytics import YOLO

    described, counts = dataset.build(fitting, checking)
    model = YOLO(str(borrowed()), task="segment")
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
    shutil.copy(model.trainer.best, save)
```

What the fitted model's answers then go through is in the same file, in
`Finder.find`, and it is short for the reason the training makes it short. There
is no filter on category names here, because there is one class, so the only
judgement left is the width check against the kind and the exemption for a
candidate the frame cut short.

```python
    def find(self, picture, kind: str) -> tuple[list[Found], list[str]]:
        ...
        narrowest, widest = data.widths(kind)
        kept: list[Found] = []
        doubts: list[str] = []
        for mask in self.candidates(picture)[0]:
            found = masks_to_glasses.one_glass(picture, mask)
            if found is None:
                doubts.append(TOO_LITTLE)
            elif narrowest <= found.width <= widest or found.cut_off:
                kept.append(found)
            else:
                doubts.append(NO_SUCH_WIDTH)
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

One point about the output has to be clear, because it decides what the
comparison with solution 3 is a comparison of.

**Turning a mask into a place on the table and a rough width is the examiner's
job, not this solution's.** Every solution in this chapter is given that same
step, so **a difference in the score belongs to the mask.** This solution
contributes only the masks, and so does solution 3, which is exactly why the gap
between the two is readable.

**One check stands between the model and the examiner, and solution 3 deliberately
has none.** The kind of glass is known, so the narrowest and the widest
footprint a glass of that kind could have are known too, and a candidate whose
footprint falls outside that range is reported as a doubt rather than kept. That
is a limit on the kind and never the size of any one glass. It can only turn a
reported glass into a reported doubt and never the other way round, so it cannot
flatter this side of the comparison.

**The check stands down when the frame cut the glass short.** At the cell's own
survey height one picture does not hold the glass zone, so a candidate whose
mask reaches the edge of the picture is kept whatever its width: the picture ran
out before the glass did, and a width read off part of a footprint is not the
glass's width. Two measurements said so. Handed the examiner's own exact masks, one
station at a time over 20 held-out spawned scenes, the kind's own range refuses
66 of 297 glass sightings, and every one of those 66 reaches the frame edge; and
of this model's own refusals over eight of those scenes, all eleven too-narrow
ones had a mask touching that edge. So the check was refusing the view rather
than the mask. What makes standing down safe rather than generous is the
survey's three overlapping stations: where a glass was seen squarely from
another station, that is the report the examiner keeps.

It follows that **this solution produces no pose.** Models produce masks. The
place comes from depth and the camera's own pose, by arithmetic, and a glass
standing upright on a flat table has no orientation left to find. [The
examiner](../03_the-examiner/01_the-examiner.md) states this once so that no solution has to argue it
again.

## 3. How the concepts fit together

The pieces now join into one pipeline, and it is short, because almost
everything in it was borrowed and only one thing was changed.

Once, before any run, the model was fitted: weights that arrived from a large
collection of everyday photographs had their training continued on the training
half of these arrangements, with labels taken from the examiner's id image and
the general list of categories replaced by the single class "glass". At run time
the fitted model is shown a grey picture shaded from depth and returns
candidates, each with a box, a confidence number and an outline. Candidates
overlapping a better one too heavily are discarded, so one object leaves one
answer, and the outlines above the bar are the masks.

Three things are worth holding on to from that.

**The finding was borrowed and the fitting was local**, which is the whole
design. The expensive, general part of the model — turning a picture into useful
local descriptions — came from somebody else's training, and the cheap, specific
part — what an instance is in this cell, and where its edge lies — was learned
here from labels that cost nothing.

**The domain gap closed and the coarse outline did not.** Those are the two
halves of solution 3's trouble, and training addresses exactly one of them. The
marking shows both halves at once: this solution finds 99.4 glasses per 100
against its partner's 6.4, and its masks still carry 4.6 per cent of pixels that
are not the glass, where a rule written by hand carries none.

**The comparison is the product.** Even if this solution were not the one
carried forward, the pair would have earned its place, because a measured answer
to "what does fine-tuning buy on this kind of picture?" is worth more than an
opinion about it.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
