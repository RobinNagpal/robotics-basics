# The six solutions — one question, six ways to see

## 1. Introduction

This book asks for one record per glass. A record says which pixels are that
glass and where it stands on the table. [What is asked
for](../02_the-problem/01_what-is-asked-for.md) states the question in full.
This chapter answers it in six different ways. No one of the six is "the"
answer. The point is to compare them, and then to choose one knowing what it
costs.

This page is the map of all six. It has three tables. The first says what each
solution is built from. The second says how each one works. The third gives
each one's score.

After this page, the chapter has one short page for each solution. Each takes
about eight minutes to read. Later in the book, six full chapters treat the
same six in about an hour each. So read this page first, then the short page
for any solution you care about, and then its full chapter.

## Contents

1. [Introduction](#1-introduction)
2. [What all six share](#2-what-all-six-share)
3. [What each one is built from](#3-what-each-one-is-built-from)
4. [How each one works](#4-how-each-one-works)
5. [What each one scored](#5-what-each-one-scored)
6. [Where to go next](#6-where-to-go-next)

## 2. What all six share

Before the tables, you need to know why the six can be compared at all. All six
get the same question, the same arrangements of glasses and the same marking.
[The examiner](../03_the-examiner/01_the-examiner.md) describes this. Read it
before any solution page.

One fact from it matters for the tables. Each solution gives back only masks.
A mask is the set of pixels it says belong to one glass. The examiner turns
every mask into a place and a width in the same way for all six. So a
difference in score is a difference in the masks. The next section starts the
comparison with what each solution needs.

## 3. What each one is built from

This table lists what you must install, train and accept the licence of to run
each solution. Read the rows from top to bottom. The top row fits nothing to
data, and the bottom row fits everything.

| Solution | What it is built from |
|---|---|
| **1. [Rules on the table](02_rules-on-the-table.md)** | NumPy and OpenCV, both already in the cell. Nothing is fitted, so there is no model, no training set and no weights file. No licence condition. |
| **2. [A network trained from scratch](03_a-network-trained-from-scratch.md)** | PyTorch and a small network written for this book. All of it is fitted on this cell's own pictures. It needs a training set and a training run. No licence condition. |
| **3. [A borrowed model, as it downloads](04_a-borrowed-model-as-it-downloads.md)** | Ultralytics YOLO26-seg, used as it downloads. Nothing is fitted, so there is no training set and no training run. Licence: AGPL-3.0. |
| **4. [The same model, fine-tuned](05_the-same-model-fine-tuned.md)** | The same YOLO26-seg and the same downloaded weights as solution 3, trained further on this cell's pictures. It needs a labelled training set and a training run. Licence: AGPL-3.0. |
| **5. [A foundation model with a keeper](06_a-foundation-model-with-a-keeper.md)** | SAM 2 through the `transformers` library, plus a small scikit-learn classifier on top. Only the classifier is fitted. The large model is not changed. Permissive licence. |
| **6. [A transformer segmenter, fine-tuned](07_a-transformer-segmenter-fine-tuned.md)** | RF-DETR-Seg, a transformer segmenter, with all of it fitted on this cell's pictures. It needs a labelled training set, a training run and the most computer power of the six. Licence: Apache 2.0, which is permissive. |

Knowing what each solution needs does not say what it does with a picture, so
the next section covers that.

## 4. How each one works

This table takes the same six in the same order. Each row says what happens
when a picture arrives, and where the knowledge about glasses comes from.

| Solution | How it works |
|---|---|
| **1. Rules on the table** | Each pixel with a depth reading becomes a point in the room. The height is dropped, so each glass becomes a flat patch of dots on the table. Dots close to each other form one glass. A group too wide for the kind is cut in two. The knowledge is a rule somebody wrote down. |
| **2. A network trained from scratch** | A small network is trained on this cell's pictures. For each pixel it says whether the pixel is glass and which way the middle of its glass lies. Each glass pixel votes for a point, and each pile of votes is one glass. All the knowledge comes from this cell. |
| **3. A borrowed model, as it downloads** | A model trained on photographs of everyday objects is shown this cell's pictures. It returns an outline and a name for each object it sees. Outlines named as drinking vessels are kept as masks. All the knowledge is somebody else's. |
| **4. The same model, fine-tuned** | The model of solution 3 is trained further on this cell's pictures, with its list of names cut to one class. It then returns one outline per glass. The knowledge starts as somebody else's and is moved towards this cell. |
| **5. A foundation model with a keeper** | A large model that can outline anything returns many outlines. Each outline becomes a few measurements on the table. A small classifier, fitted on this cell, reads them and says keep, drop, or "more than one glass". Only the keeper is fitted. |
| **6. A transformer segmenter, fine-tuned** | A transformer looks at the whole picture and predicts a fixed number of objects at once, each with an outline. Training on this cell teaches it which objects are glasses. Like solution 4 it starts from borrowed weights, but the model has a different design. |

Knowing how each one works leads to the question of how well each one did,
which the next section answers.

## 5. What each one scored

This section gives the score of each solution, so you can see how the
designs above turned out. Each solution is run twice. The **spawned** run uses
the spacing the cell's own layout rule gives. The **crowded** run puts the
glasses closer than that rule allows. [The
examiner](../03_the-examiner/01_the-examiner.md#every-solution-is-tested-twice-once-on-each-family)
explains the two runs.

Each run is repeated over five blocks of 20 arrangements, about 500 glasses in
all. The table gives the average of the five blocks. The lowest and highest
block are in brackets. Where two solutions' brackets overlap, this test has not
separated them. On the crowded run, 86.4 per 100 is the best any method could
score, because some glasses are fully hidden. Read the last column as the main
reason for each result.

| Solution | Spawned, found per 100 | Crowded, found per 100 | Main reason |
|---|---|---|---|
| **1. [Rules on the table](02_rules-on-the-table.md)** | **100.0** (100.0–100.0) | 73.0 (70.3–75.5) | Crowding removes the strip of bare table the rule needs. |
| **2. [A network trained from scratch](03_a-network-trained-from-scratch.md)** | 64.1 (62.4–66.7) | 74.6 (71.3–79.8) | A glass whose middle falls outside the picture gets no votes. |
| **3. [A borrowed model, as it downloads](04_a-borrowed-model-as-it-downloads.md)** | 6.4 (2.0–11.9) | 2.1 (0.0–4.2) | It was never trained on pictures like these. |
| **4. [The same model, fine-tuned](05_the-same-model-fine-tuned.md)** | **99.4** (99.0–100.0) | 72.0 (70.8–72.9) | Training closed the gap, but a partly hidden glass still comes back as a slice. |
| **5. [A foundation model with a keeper](06_a-foundation-model-with-a-keeper.md)** | 83.0 (78.0–86.1) | 73.6 (71.9–76.6) | It cannot find a glass the large model did not outline. |
| **6. [A transformer segmenter, fine-tuned](07_a-transformer-segmenter-fine-tuned.md)** | 96.4 (94.9–98.0) | **81.9** (77.2–86.5) | Two touching glasses get two separate predictions, so they are never joined. |

Three results stand out. [The results](../11_the-results.md#4-what-the-comparison-says)
explains each one in full.

- On crowded tables, solutions 1, 2, 4 and 5 are not separated. Their brackets
  overlap.
- Solutions 3 and 4 are the same model, and only training differs. So the gap
  from 6.4 to 99.4 shows what training on this cell gave. The cause of the low
  score is the **domain gap**: the model learned from photographs, but this cell
  shows grey pictures shaded from depth.
  [The borrowed model's results](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#2-why-it-failed-the-names-it-reached-for)
  explains it.
- The two mask numbers disagree about which solution is best. Solution 4 covers
  the most glass but also claims the most table. Solutions 1, 5 and 6 claim no
  table.

One cost is not in the scores. Solutions 3 and 4 use the AGPL-3.0 licence.
[Its terms](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#6-what-it-costs-to-run-and-the-licence)
matter if the work is ever shipped.

All six were built and run by the examiner, and no number here is an estimate.
The next section says where to read next.

## 6. Where to go next

- [The examiner](../03_the-examiner/01_the-examiner.md) gives the shared input,
  output and marking. **Read this before any solution page.**
- [The problem](../02_the-problem/01_what-is-asked-for.md) says what is asked
  for, and the two difficulties.
- [Looking again at what was hidden](../02_the-problem/02_looking-again-at-what-was-hidden.md)
  covers the part all six share, which deals with a glass no picture shows.
- Then read the six short pages of this chapter, in order: [rules on the
  table](02_rules-on-the-table.md), [a network trained from
  scratch](03_a-network-trained-from-scratch.md), [a borrowed model as it
  downloads](04_a-borrowed-model-as-it-downloads.md), [the same model
  fine-tuned](05_the-same-model-fine-tuned.md), [a foundation model with a
  keeper](06_a-foundation-model-with-a-keeper.md), and [a transformer segmenter,
  fine-tuned](07_a-transformer-segmenter-fine-tuned.md). Each one ends with a
  link to its full chapter.
- [The results](../11_the-results.md) gives the full scorecard, with every column.

← [Comparing the outputs](../03_the-examiner/04_comparing-the-outputs.md) · [Rules on the table](02_rules-on-the-table.md) →
