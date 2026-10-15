# A transformer segmenter, fine-tuned

This page is a short summary of the sixth of the six solutions. This solution
uses a modern transformer model, trained further on this cell's own pictures.
Its licence is permissive. The page says what it is, how it differs, what it
needs, what it scored and when to choose it. The full story is in [the chapter
on this solution](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md).

## Contents

1. [What it is](#1-what-it-is)
2. [How it works](#2-how-it-works)
3. [What it needs](#3-what-it-needs)
4. [What it scored](#4-what-it-scored)
5. [Where it is strong and where it breaks](#5-where-it-is-strong-and-where-it-breaks)
6. [When to choose it](#6-when-to-choose-it)

## 1. What it is

The model is **RF-DETR-Seg**, under the Apache 2.0 licence. It comes already
trained on ordinary photographs. Here it is trained further with one class,
"glass", exactly as [the same model,
fine-tuned](05_the-same-model-fine-tuned.md) is.

So solutions 4 and 6 are trained the same way on the same pictures. Only the
design of the model differs. The next section shows what that design changes.

![One picture through the model to one mask per glass, with the fixed array of query slots the chain hands back drawn beside it.](../../images/seeing-the-glasses/a-transformer-segmenter-fine-tuned/transformer-flow-what-it-does.png)

## 2. How it works

This section shows the two ways this design differs from YOLO.

First, the model has a fixed number of slots, called **queries**. Each slot
reports one glass or nothing. In training, slots are matched to glasses one to
one. This is called **set prediction**. So two touching glasses fill two slots,
and nothing has to be cut apart. There is also no overlap limit to choose.

Second, the mask is drawn over the whole picture, not inside a box. So it is the
only one of the six that could be trained to mark the hidden part of a glass.
That second way was not trained to the end, so it has no score here. [How it
works](../10_a-transformer-segmenter-fine-tuned/03_how-it-works.md#4-set-prediction)
explains both in full. [The examiner](../03_the-examiner/01_the-examiner.md)
turns each mask into a place and a width, as for all six. The next section lists
what this needs.

## 3. What it needs

This section lists what the model above needs. It needs a deep learning
framework and a large downloaded weights file. It needs a training set, which
the examiner labels for free. It needs time on the machine for training, which
is its largest cost. It trains on this laptop's built-in graphics. Its weights
must be kept in step with the cell.

Its Apache 2.0 licence puts no duty on the code around it. [What it
needs](../10_a-transformer-segmenter-fine-tuned/05_what-it-needs.md) gives the
details. The next section shows what it scored.

## 4. What it scored

Every solution is run on a spawned set at the cell's own spacing and a crowded
set that is closer. Each row gives the count per 100 glasses, with the lowest
and highest block in brackets.

| | found per 100 | missed | merged | place | mask covered | mask not the glass |
|---|---|---|---|---|---|---|
| spawned | 96.4 (94.9–98.0) | 3.6 | 0.0 | 6.0 mm | 96.6% | 0.0% |
| crowded | 81.9 (77.2–86.5) | 18.1 | 1.4 | 0.5 mm | 97.2% | 0.0% |

It finds more crowded glasses than any other solution. It is the only one clear
of the group on crowded tables. Exact masks would find 86.4, because some
glasses are hidden completely. None of its masks spread onto a neighbour or the
table.

It is not best everywhere. The fine-tuned YOLO found more glasses on the spawned
set, 99.4 against 96.4. It also merged fewer crowded glasses, 0.8 per 100
against 1.4. [The results](../11_the-results.md#4-what-the-comparison-says)
compare all six. The next section sums up what this means.

## 5. Where it is strong and where it breaks

This section turns the scores above into strengths and weaknesses. It is strong
because it gives one mask per glass and never has to cut touching glasses apart.
It has one less setting to choose than YOLO. It is the only one that could be
asked for the hidden part of a glass. Its licence is permissive.

It has four weaknesses. Training needs patience, because the slots take time to
settle. The hidden-part way is easy to get wrong without any warning. A glass
hidden completely fills no slot. Its answers cannot explain themselves. [How it
compares](../10_a-transformer-segmenter-fine-tuned/06_how-it-compares.md#1-where-it-is-strong-and-where-it-breaks)
explains these in full. The next section says when to choose it.

## 6. When to choose it

This section turns the points above into advice. Choose it when the work must
ship with a clean licence. On ability alone it and the fine-tuned YOLO are close,
so the licence decides. Choose it also when the hidden part of an object matters.

Do not choose it when setup cost is the problem. Then [a foundation model with a
keeper](06_a-foundation-model-with-a-keeper.md) needs almost no training data.
It also needs depth, just as [rules on the table](02_rules-on-the-table.md)
does.

The code is in
[`src/08_seeing-the-glasses/06-rf-detr-fine-tuned/`](../../../code/src/08_seeing-the-glasses/06-rf-detr-fine-tuned).
It writes its own `results.json` beside itself. The full treatment starts at
[what it is](../10_a-transformer-segmenter-fine-tuned/01_what-it-is.md).

← [A foundation model with a keeper](06_a-foundation-model-with-a-keeper.md) · [Rules on the table — what it is](../05_rules-on-the-table/01_what-it-is.md) →
