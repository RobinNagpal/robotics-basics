# The code

This page shows the code at the heart of this solution, and says what the
solution hands back to the rest of the cell. The second explains the first,
which is why they are on one page.

## Contents

1. [The code at the heart of it](#1-the-code-at-the-heart-of-it)
2. [The masks are what this contributes](#2-the-masks-are-what-this-contributes)
3. [How the concepts fit together](#3-how-the-concepts-fit-together)

## 1. The code at the heart of it

This solution is two models meeting at one place, so that place is worth seeing
before the rest of the document explains it. On one side a grid of point
prompts goes into the borrowed model. On the other a short row of measurements
comes back out of what the borrowed model returned, and that row is the only
thing the fitted model ever reads. Everything after this section is an account
of those two sides.

Going in, in `05-sam2-with-a-keeper/sam_keeper.py`: how far apart the grid's
points stand is taken from the narrowest glass the kind allows rather than
chosen, the grid is then laid over the whole picture, and the borrowed model is
called on batches of its points with the picture already encoded.

```python
def prompt_spacing(kind: str) -> int:
    ...
    narrowest = data.widths(kind)[0] / _metres_per_pixel()
    return max(1, int(narrowest / POINTS_ACROSS_SMALLEST))

def _grid(spacing: int, inside: np.ndarray | None = None) -> list[list[float]]:
    """Prompt points (column, row) on a regular grid, optionally only where ``inside`` is true."""
    rows = np.arange(spacing // 2, render.HEIGHT, spacing)
    columns = np.arange(spacing // 2, render.WIDTH, spacing)
    points = [[float(column), float(row)] for row in rows for column in columns]
    ...

    def at(self, points: list[list[float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        ...
        asked = [[[point] for point in points]]
        prepared = self.processor(original_sizes=self.sizes, input_points=asked, return_tensors="pt")
        all_points = _onto(prepared["input_points"], self.where)
        ...
            for start in range(0, all_points.shape[1], PROMPTS_AT_ONCE):
                chunk = all_points[:, start : start + PROMPTS_AT_ONCE]
                out = self.model(image_embeddings=self.embeddings, input_points=chunk, multimask_output=True)
```

Coming out, in the same file: every region that survived the cleanup becomes
numbers measured on the table rather than in the picture. Six of the keeper's
eight come from here. The other two — how many prompt points returned this same
region, and how it nests among the regions beside it — are added by the function
that calls this one, because neither can be known from one region on its own.

```python
def _measure(picture, mask, found, jumps, step, camera, widths) -> list[float]:
    ...
    rows, columns = found.pixels[:, 0], found.pixels[:, 1]
    points = render.to_world(picture, rows, columns)

    low, high = widths
    edge = mask & ~cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    return [
        (found.width - low) / (high - low),  # where its width falls in the kind's range
        _roundness(mask),
        float(np.median(points[:, 2]) - TABLE_TOP_Z),  # how far its surface stands off the table
        float(math.dist((found.x, found.y), camera)),  # how far it sits from under the camera
        float(np.mean(jumps[edge] > step)) if edge.any() else 0.0,  # how much of its edge is a step
        _table_area(points),
    ]
```

Two things show in those two blocks. The borrowed half is one call,
`self.model(...)` on a `Sam2Model` loaded through Hugging Face `transformers`,
and every line written around it belongs to this project. And the fitted half
never sees a pixel: what reaches scikit-learn — a
`HistGradientBoostingClassifier` wrapped in a `CalibratedClassifierCV` — is the
list the second block returns. That is what borrowing the seeing and fitting the
deciding looks like in code.

## 2. The masks are what this contributes

Everything above produces masks, and nothing above produces a place or a width.

Turning a mask into a place on the table and a rough width is the examiner's job,
described once in [the examiner](../03_the-examiner.md) and shared by all six
solutions: every mask pixel carries a depth reading, so it becomes a point in
the room, the axis comes from the points at the top of the glass, and the width
is how far the cloud reaches from that axis. **So this solution contributes only
the masks, and any difference in its score belongs to the mask.** It cannot win
by measuring more cleverly and it cannot lose by measuring worse.

One consequence is worth stating because it removes a question this solution
invites. **No model here produces a pose.** The borrowed model produces regions,
the keeper produces a decision about a region, and the pose comes from depth and
the camera's own pose by arithmetic. A glass standing upright on a flat table
has no orientation left to find.

## 3. How the concepts fit together

Everything above is one pipeline, worth seeing in order before the failure
cases, because each stage works only on what the stage before it passed along.

The depth readings are **shaded** into a grey picture. The **picture encoder**
runs once over it. A **grid of point prompts** then goes through the mask
decoder, one cheap pass each, and scoring, stability and duplicate removal
reduce what comes back to a shortlist of **proposals**. Each proposal's pixels
become **points in the room**, and a place, a width, a height above the table
and the rest of the **measurements** come out of those points and of the
proposals beside it. The **keeper** reads the measurements and answers one of
three things, with its probability **calibrated** so that the two thresholds
mean what they say. A proposal it keeps must still pass the **width check**
against the kind before it is reported, and where two reports land at **one
place on the table** only the surer of them survives. A proposal it calls more
than one glass goes back for a **second round of prompts inside itself**.
Anything left over is **reported doubtful**, which for a pair means handing it
to the job of pushing the glasses apart.

Three things about that chain are worth holding on to.

**The only fitted stage is the keeper**, which reads a table of numbers rather
than pictures, so everything that finds objects is borrowed and none of it knows
anything about this cell.

**The riskiest stage is the shading**, because it is the only place where a
choice that no arithmetic can check changes what every later stage sees.

**The width check sits after the keeper rather than before it**, so a wrong
answer from the keeper still has to get past a rule nobody fitted, and a wrong
keep therefore becomes a doubtful report rather than a wrong glass.

← [How it works](02_how-it-works.md) · [A worked example](04_a-worked-example.md) →
