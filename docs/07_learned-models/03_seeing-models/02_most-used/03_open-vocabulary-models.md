# Open-vocabulary models

This page answers one question: how can a robot find an object it was never trained
on, just because someone typed its name or clicked on it? The models on the earlier
pages of this chapter can only find the kinds of object in their training list,
whereas the models on this page do not have a fixed list at all.

It is written for a reader who has already read the earlier pages of this chapter,
especially [object detection](01_object-detection.md) and
[segmentation](02_segmentation.md), so you should know what a detection box and a
segmentation outline are. This page covers four ideas: matching pictures to
sentences, finding boxes from words, finding outlines from a click, and
general-purpose picture features.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: "pick up the blue mug"](#6-a-worked-example-pick-up-the-blue-mug)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

The one-sentence idea is this: an open-vocabulary model finds things in a picture
from a prompt you give it at the time, such as a few words or a click, instead of
from a fixed list learned during training.

A **vocabulary** is a set of words, and an ordinary detector has a **closed
vocabulary**, because it is trained on a list of classes such as "mug", "bowl" and
"banana". So it can find those three things and nothing else, which means that if
you want it to find a sponge, you must collect labelled photos of sponges and train
it again.

An open-vocabulary model has no fixed list, so you type "sponge" and it looks for a
sponge, or you type "the blue mug on the left" and it looks for that. This works
because the model learned from a very large number of pictures that came with text,
so it has seen almost every common word next to pictures of that thing.

Here is an everyday example: imagine two new helpers in a kitchen, where the first
has learned to recognise only ten kinds of object, one at a time, from flash cards,
while the second has read many illustrated books. Ask the first to fetch a "whisk",
and it cannot, because whisk was not on its cards. Ask the second, and it can,
because it has seen whisks and the word "whisk" together many times before.

There is a second kind of prompt too, because a **promptable segmentation** model
takes a click or a box instead of words. You click on a mug, and it returns the
exact outline of the mug. However, it does not know that the thing is a mug, since
it only knows where the object you pointed at begins and ends.

A **prompt** is simply what you give the model to tell it what you want, whether
that is a few words, a click, or a rough box.

---

## 2. What goes in and what comes out

Those prompts and answers differ from one model to the next, so the table below
lists the four kinds of model on this page. Read each row as: what you give it, and
what it gives back.

| Kind | What goes in | What comes out | Example model |
| --- | --- | --- | --- |
| Picture and text matching | a picture and some sentences | a score for how well each sentence fits the picture | CLIP |
| Detection from words | a picture and a few words | a box around each thing the words describe, with a confidence number | Grounding DINO, OWL-ViT |
| Segmentation from a click | a picture and a click or a box | the outline of the thing you pointed at | Segment Anything (SAM), SAM 2 |
| General picture features | a picture | a list of numbers for each small patch of the picture | DINOv2 |

Detection from words is the most direct use for a robot arm, because you give it a
photo of the table and the words "blue mug", and it draws a box only around the
blue mug.

![The same photo with two different prompts](../../../images/seeing-models/open-vocabulary-models/text-prompt-to-box.svg)

The picture is the same in both panels, and only the typed words change which
object gets a box.

Segmentation from a click gives outlines instead, but a single click can be
unclear, since a click on a mug's handle might mean "the handle" or "the whole
mug". So Segment Anything returns three possible outlines, each with a score,
and either the software or a person then picks one.

![One click on a mug handle gives three possible outlines](../../../images/seeing-models/open-vocabulary-models/click-to-mask.svg)

A click on the handle is unclear, so the model offers the handle, the whole mug,
and the mug with its saucer.

---

## 3. How it works inside

### Turning pictures and words into numbers

To match words against pictures at all, both have to become the same kind of thing,
and that thing is a list of numbers. Such a list is called an **embedding**, which
is a list of a few hundred numbers that describes the meaning of a picture or a
sentence.

A model like CLIP does this with two networks.

1. The **image encoder** turns a picture into an embedding.
2. The **text encoder** turns a sentence into an embedding of the same length.
3. The model then compares the two lists of numbers, and if they point in the same
   direction, the picture and the sentence mean the same thing, so the model gives
   them a high score.

![Pictures and sentences scored against each other](../../../images/seeing-models/open-vocabulary-models/words-and-pictures-matched.svg)

Each picture is scored against each sentence, and the matching pairs get the
darkest squares.

### Finding boxes from words

A detector like Grounding DINO or OWL-ViT uses that same idea, but it applies it to
parts of a picture rather than to the whole picture.

1. The image encoder makes an embedding for many small regions of the photo.
2. The text encoder makes an embedding for the words, such as "blue mug".
3. The model then compares each region with the words.
4. Regions that match well become candidate boxes, and the model tightens each box
   around the object.
5. Finally it outputs the boxes whose scores are above a set threshold, together
   with their scores.

### Finding outlines from a click

Segment Anything works in a different way, because its prompt is a click rather
than a word.

1. A large image encoder looks at the photo once and turns it into a grid of
   embeddings, and this is the slow step.
2. A small prompt encoder turns the click, or the box, into numbers.
3. A small, fast decoder then combines the two and draws the outline.

Because only step 3 repeats for each new click, the model can answer a new click
very quickly once the photo has been encoded. SAM 2 adds a memory, so it can follow
the same outline through the frames of a video, and the page
[tracking and motion](../03_also-used/03_tracking-and-motion.md) covers that.

### General picture features

DINOv2 is only an image encoder, so it has no text and draws no boxes, and instead
it turns each small patch of a picture into an embedding. Patches that show the
same kind of thing get similar embeddings, even across different photos, so the
handle of one mug gets numbers close to the handle of another mug. Other models are
often built on top of DINOv2, because its features are good and free to use.

---

## 4. How it is trained

All four of those models are trained on far more pictures than an ordinary detector
ever sees.

CLIP learned from about 400 million pairs of a picture and its caption, collected
from the internet, and nobody labelled them for CLIP, because the captions were
written by the people who put the pictures online. In training, CLIP is shown a
batch of pictures and a batch of captions, and it must work out which caption
belongs to which picture. Each time it pairs them correctly, it has learned a
little more about how words and pictures relate.

Grounding DINO and OWL-ViT learn instead from pictures with boxes and matching
phrases, for example a box around a dog with the phrase "a brown dog". Some of
these come from detection datasets, while others come from caption datasets, where
a program matched phrases in a caption to boxes in the picture.

Segment Anything was trained on a dataset called SA-1B, which has about 11 million
photos and over one billion outlines. People did not draw all of them, because the
team started with outlines drawn by people with the model's help, and then the
model drew more outlines itself, people checked them, and the model was trained
again. In the last round the model drew outlines on its own.

DINOv2 was trained on about 142 million pictures with no labels at all, which is
called **self-supervised learning**. The model is shown two different crops of the
same picture and learns to give them similar embeddings, and it also learns to fill
in the embedding of a hidden patch from its neighbours, so no human ever has to say
what anything is.

The page [where the data comes
from](../../01_what-models-are/05_where-the-data-comes-from.md) explains these
kinds of data in general.

---

## 5. Well-known models

This section names the models you would actually download, and says which of them
answers "find the thing I described in words" well enough to put on a robot.

Read the table like this. The first column is the model, the second says what it
is best at, the third says how large it is, the fourth gives the licence of the
code and the licence of the weights separately, and the last says when to pick
it. A **parameter** is one number inside the model that training chooses, so a
model with more parameters is a larger download and a slower answer. The counts
come
from each model's own page on Hugging Face, except for YOLOE, whose counts come
from the Ultralytics documentation. The two licences are apart because they often
differ, and it is the one on the weights that decides whether you may ship the
robot.

| Model | What it is best at | Parameters | Licence (code / weights) | Pick it when |
| --- | --- | --- | --- | --- |
| CLIP | scoring one picture against several sentences | 428 M (`openai/clip-vit-large-patch14`) | MIT / the model card states no licence | you already have a cropped picture and only have to choose between words |
| OWLv2 | boxes from short names, with the least setup | 155 M (`google/owlv2-base-patch16-ensemble`) | Apache-2.0 / Apache-2.0 | your objects have ordinary names and you want one install and one call |
| Grounding DINO | boxes from a longer phrase | 172 M (tiny), 233 M (base) | Apache-2.0 / Apache-2.0 | the prompt is a description, such as "the blue mug on the left" |
| YOLOE | open-vocabulary boxes and outlines at camera speed | 3.9 M to 55.2 M | AGPL-3.0 / AGPL-3.0 | the model has to keep up with a live camera on the robot |
| SAM 2 | exact outlines from a click or a box | 39 M (tiny), 224 M (large) | Apache-2.0 / Apache-2.0 | something else has already decided where the object is |
| SAM 3 | every object matching a phrase, with outlines | 860 M | bespoke SAM License / same licence, and the download is gated | you want words to outlines in one model and can accept that licence |

DINOv2, from section 3, is not in the table. It answers no prompt, so it cannot be
compared with the models here, and [3D feature
maps](../../04_3d-models/03_also-used/02_3d-feature-maps.md) is the page that uses
it.

### 5.1 CLIP, the model the others are built on

**Historical**: you rarely call it yourself now, but the open-vocabulary idea comes
from it, and OWLv2 below has CLIP inside it.

CLIP (Contrastive Language-Image Pre-training) was published by OpenAI in 2021. It
has one network for pictures and one for sentences, and it scores how well a
picture and a sentence go together. It draws no boxes and finds nothing, because
it looks at the whole picture at once.

You would pick CLIP rather than OWLv2, the obvious alternative, only when the
picture is already cropped to one object and the question is which of several
words fits it best. A detector has returned three candidate boxes, and you want to
know which one is the blue mug. For "where is the blue mug on this table", OWLv2
or Grounding DINO is the right model, because CLIP cannot point at anything.

The large checkpoint holds 428 million parameters, which is slow without a
graphics card but usable, because you run it once per crop rather than once per
frame. OpenAI's code is MIT, while the model card for the weights states no
licence at all, and weights published with no licence grant you no rights by
default. The
thing that goes wrong most often is that CLIP always picks a winner, because the
scores are scaled to add up to one across the sentences you gave it.

The library is Hugging Face `transformers`, and this follows its [CLIP
documentation page](https://huggingface.co/docs/transformers/en/model_doc/clip).

```python
from PIL import Image
from transformers import AutoModel, AutoProcessor

model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")
processor = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")

image = Image.open("mug_crop.jpg")      # one object, already cut out of the photo
labels = ["a photo of a blue mug", "a photo of a red mug", "a photo of a bowl"]

inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)

# One number per sentence. They are scaled so that they add up to one.
probs = outputs.logits_per_image.softmax(dim=1)
print(labels[probs.argmax().item()], round(probs.max().item(), 3))
```

The library resizes the picture, turns the sentences into numbers and runs both
networks. You supply the crop, the sentences, and a rule for refusing an answer:
refuse when the best two probabilities are close, because the model is then
choosing between words rather than recognising the object.

### 5.2 OWL-ViT and OWLv2

**Most used in 2026**, because it is the shortest path from a name to a box, and
its code and its weights are both Apache-2.0.

OWL-ViT came from Google Research in 2022 and OWLv2 followed in 2023. OWL-ViT
takes CLIP, removes the layer that pools the picture into one embedding, and
attaches a small box head to each patch, so the CLIP idea is applied to parts of
the picture. OWLv2 is the same design trained on far more data that it labelled
itself, by letting an existing detector draw boxes on picture-and-text pairs from
the internet.

You would pick OWLv2 rather than Grounding DINO, the obvious alternative, when
your objects have ordinary one-word or two-word names. It is smaller, 155 million
parameters against 233 million, and you pass your names as a plain list. Grounding
DINO is better when the prompt is a description rather than a name, because it
reads the phrase as a phrase.

It expects one query per kind of object, written in the style "a photo of a blue
mug", and short names work better than long sentences. It is not fast enough for a
live camera on a small computer, so you run it once and then track. The mistake
that catches people is reading the raw box numbers out of the model: the processor
pads the picture to a square, so those numbers belong to the padded picture, and
`post_process_grounded_object_detection` with `target_sizes` is what brings them
back to your photo.

The library is Hugging Face `transformers`, and this follows its [OWLv2
documentation page](https://huggingface.co/docs/transformers/en/model_doc/owlv2).

```python
import torch
from PIL import Image
from transformers import Owlv2ForObjectDetection, Owlv2Processor

model_id = "google/owlv2-base-patch16-ensemble"
processor = Owlv2Processor.from_pretrained(model_id)
model = Owlv2ForObjectDetection.from_pretrained(model_id)

image = Image.open("table.jpg")
text_labels = [["a photo of a blue mug", "a photo of a bottle"]]  # one list per picture

inputs = processor(text=text_labels, images=image, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

results = processor.post_process_grounded_object_detection(
    outputs=outputs,
    target_sizes=torch.tensor([(image.height, image.width)]),  # back to your own pixels
    threshold=0.1,            # how sure the model must be to report a box
    text_labels=text_labels,
)[0]

for box, score, label in zip(results["boxes"], results["scores"],
                             results["text_labels"]):
    print(label, round(score.item(), 3), [round(v, 1) for v in box.tolist()])
```

The library does the padding, the scaling back, and the matching of each box to
the query it came from. You supply the wording of the queries, the threshold, and
the rule for the case where two boxes come back for one query. When their scores
are close, the safe answer on a robot is to stop and ask.

### 5.3 Grounding DINO

**Most used in 2026**, because it is the model people reach for when the prompt is
a phrase rather than a name.

Grounding DINO was published by IDEA Research in 2023. It takes a picture and a
text prompt, and returns a box for each thing the prompt describes, together with
the words that matched that box. Its code and its weights are both Apache-2.0,
which is why it appears in so many robot projects.

You would pick it rather than OWLv2, the obvious alternative, because it handles a
prompt with extra words in it, such as "the blue mug on the left" or "a screw with
a flat head". It also has a second threshold, for how well the words matched,
which lets you tune the two kinds of mistake apart. Pick OWLv2 instead when your
prompts are plain names, since it is smaller and simpler.

The base checkpoint holds 233 million parameters and needs a graphics card to
answer quickly. The original repository has had no commit since August 2024, so
install the model from `transformers`, whose implementation is maintained. One
trap is worth knowing before you plan around it: **Grounding DINO 1.5, 1.6 and
DINO-X have no downloadable weights.** Those repositories hold client code for a
paid hosted service, and only the original Grounding DINO runs on your own
machine. The answers also move with the wording, so "mug", "cup" and "coffee mug"
can give three different results on one photo.

The library is Hugging Face `transformers`, and this follows its [Grounding DINO
documentation
page](https://huggingface.co/docs/transformers/en/model_doc/grounding-dino).

```python
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

model_id = "IDEA-Research/grounding-dino-tiny"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)

image = Image.open("table.jpg")
text_labels = [["a blue mug", "a bottle"]]   # one list of phrases per picture

inputs = processor(images=image, text=text_labels, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

result = processor.post_process_grounded_object_detection(
    outputs,
    inputs.input_ids,
    threshold=0.4,          # how sure the model must be that an object is there
    text_threshold=0.3,     # how well the words must match
    target_sizes=[image.size[::-1]],   # (height, width) of your photo
)[0]

for box, score, label in zip(result["boxes"], result["scores"], result["labels"]):
    print(label, round(score.item(), 3), [round(v, 1) for v in box.tolist()])
```

The library joins the phrases into the one text string the model wants and maps
each box back to the words it matched. You supply the phrase and the two
thresholds, which you tune separately: `threshold` controls how sure the model must
be that an object is there, and `text_threshold` how well the words have to match.
Something in your program also has to turn the instruction "pick up the blue mug"
into the prompt "a blue mug".

### 5.4 YOLOE

**Worth betting on**, because it puts open-vocabulary detection inside a fast
detector instead of a large transformer, which is how this kind of model will run
at camera speed on a robot. Its licence is why it is not the default.

YOLOE, from Ultralytics, is an open-vocabulary detector that also returns outlines.
You give it the names you want when you run it, or an example picture of the
object, or no prompt at all, in which case it reports names from a built-in list of
4,585 words. It was inspired by YOLO-World, which did the same job earlier and
whose repository has had no commit since February 2025.

You would pick YOLOE rather than Grounding DINO, the obvious alternative, when
speed decides the design. Grounding DINO runs a vision-language transformer for
every picture, while YOLOE turns your prompts into numbers once and then compares
those numbers against regions inside an ordinary convolutional head. It is less
accurate: the Ultralytics documentation reports YOLOE-26s at 30.8 mean average
precision on LVIS with no training on it, at 10.7 million parameters, against 27.4
for Grounding DINO's tiny model, in a group of transformer detectors the same
table says carry 155 to 232 million parameters.

The licence is AGPL-3.0 for the Ultralytics package and for the original YOLOE
repository, so a product built on it must publish its own source or buy a
commercial licence from Ultralytics. Text prompting needs a text encoder that is
fetched on first use rather than at install time, about 254 MB for the YOLOE-26
checkpoints, into the directory you ran from. The time one prediction takes also
grows with the number of names you prompt with, by about 19 % going from 80 names
to 1,203 and about 89 % at the full 4,585-name list, as Ultralytics measured, and
the reported arithmetic cost does not move at all, so a profile will not warn you.

The library is `ultralytics`, and this follows its [YOLOE documentation
page](https://docs.ultralytics.com/models/yoloe/).

```python
from ultralytics import YOLOE

model = YOLOE("yoloe-26s-seg.pt")      # boxes and outlines in one checkpoint

# The first call downloads a text encoder into the current directory.
model.set_classes(["blue mug", "bottle"])

result = model.predict("table.jpg")[0]
print(result.boxes.xyxy)               # one row per object: left, top, right, bottom
print(result.boxes.conf)               # one confidence number per object
print(result.masks.xy[0].shape)        # the first object's outline, as points
```

The library downloads the checkpoint, installs and runs the text encoder, and
gives you boxes and outlines together. You supply the list of names, and the
knowledge that a freshly loaded checkpoint reports numeric class names until
`set_classes` has been called.

### 5.5 SAM 2

**Most used in 2026** for turning a box into an exact outline, and the newest
member of the Segment Anything family whose code and weights are both plainly
Apache-2.0.

Segment Anything (SAM) came from Meta in 2023 and SAM 2 followed in 2024. You give
it a click, a box or a rough region, and it returns the outline of the thing you
pointed at. SAM 2 adds a memory for video, so it can keep the same outline from
frame to frame.

You would pick SAM 2 rather than the original SAM, the obvious alternative,
because it is faster, it works on video, and it carries the same permissive
licence. You would pick it rather than SAM 3 when you need a standard open licence
and a download nobody has to approve.

The large checkpoint holds 224 million parameters and the tiny one 39 million, so
there is a version small enough for a robot with no graphics card. The real cost is
that SAM 2 decides nothing by itself, so one of the detectors above has to say
where to point. The failure people meet first is that it outlines whatever is under
the prompt, including a shadow or a reflection.

The library is Hugging Face `transformers`, and this follows its [SAM 2
documentation page](https://huggingface.co/docs/transformers/en/model_doc/sam2).
The box in the example is the one Grounding DINO returned in
[section 5.3](#53-grounding-dino), which is the Grounded-SAM pairing in full.

```python
import torch
from transformers import Sam2Model, Sam2Processor

model_id = "facebook/sam2.1-hiera-large"
model = Sam2Model.from_pretrained(model_id)
processor = Sam2Processor.from_pretrained(model_id)

box = result["boxes"][0].tolist()      # left, top, right, bottom, from Grounding DINO
inputs = processor(images=image, input_boxes=[[box]], return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

masks = processor.post_process_masks(outputs.pred_masks.cpu(),
                                     inputs["original_sizes"])[0]
best = outputs.iou_scores.squeeze().argmax()   # the model offers several outlines
outline = masks[0, best] > 0        # one true-or-false value per pixel of the photo
```

The library encodes the picture, prompts the model with your box, and scales the
outlines back to your photo's size. You supply the box and the choice between the
candidate outlines, and then the step after the outline, which is reading the depth
pixels inside it and turning them into a point cloud.

### 5.6 SAM 3

**Worth betting on**, because it does in one model what the Grounding DINO and SAM
pairing does in two, and returns every object matching the phrase rather than the
best one. Its licence is why it is not yet the default.

SAM 3 came from Meta, with an updated set of checkpoints called SAM 3.1. You give
it a short phrase, and it returns an outline, a box and a score for every object in
the picture that matches the phrase. Meta calls this promptable concept
segmentation, and its repository reports that the model reaches 75 to 80 % of human
performance on a benchmark of its own, SA-CO, which contains 270,000 concepts.

You would pick it rather than the Grounding DINO and SAM 2 pairing, the obvious
alternative, when one model is simpler than two, or when you need every matching
object rather than one. Counting the screws on a tray is the clearest case, because
the pairing gives you the best box while SAM 3 gives you every screw. Stay with the
pairing when a standard open licence matters.

The model holds 860 million parameters, so it needs a graphics card. The licence is
not a standard open licence but Meta's own SAM License, which has to be read rather
than assumed. The weights are also gated: you request access on Hugging Face, wait
for it to be granted, and sign in from the machine that downloads them, so a build
machine with no credentials cannot fetch them at all.

The library is Hugging Face `transformers`, and this follows its [SAM 3
documentation page](https://huggingface.co/docs/transformers/en/model_doc/sam3).

```python
import torch
from PIL import Image
from transformers import Sam3Model, Sam3Processor

# Works once your access request on huggingface.co/facebook/sam3 is granted
# and you have signed in on this machine with `hf auth login`.
model = Sam3Model.from_pretrained("facebook/sam3")
processor = Sam3Processor.from_pretrained("facebook/sam3")

image = Image.open("table.jpg")
inputs = processor(images=image, text="blue mug", return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

results = processor.post_process_instance_segmentation(
    outputs,
    threshold=0.5,        # how sure the model must be about an object
    mask_threshold=0.5,   # where the edge of the outline is drawn
    target_sizes=inputs.get("original_sizes").tolist(),
)[0]

print(len(results["masks"]))   # one outline for every blue mug on the table
```

The library handles the access token, the phrase and the scaling of the outlines.
You supply the phrase, the two thresholds, and a decision about how many objects
your robot will accept, because a phrase that is slightly too broad now returns
several outlines rather than one wrong box.

### 5.7 How to choose

Start with Grounding DINO for the box and SAM 2 for the outline, both run from
`transformers`. That pair answers "find the thing I described in words" accurately,
and the code and weights of both are Apache-2.0, so no licence stops you shipping
it.

Five things change that choice.

- Your objects have plain names and you want the smallest setup. Use OWLv2, which
  is one model, one call and a shorter download.
- The model has to keep up with a live camera on the robot. Use YOLOE, and accept
  that AGPL-3.0 means publishing your source or buying a licence from Ultralytics.
- You need every object that matches the words, not the best one. Use SAM 3, and
  accept its bespoke licence and the gated download.
- You already have crops and only need to choose between words. Use CLIP, and
  refuse the answer when the best two scores are close.
- Your objects have no name a person would use, such as two valve bodies that
  differ by one hole. None of these models is the answer, and
  [object detection](01_object-detection.md) trained on your own photos is.

Whatever you choose, the check after the answer is yours to write, because none of
these models knows when it is wrong. [Section 7](#7-what-goes-wrong) lists the ways
they fail.

---

## 6. A worked example: "pick up the blue mug"

Those models are most easily understood together, so here is a worked example in
which a person types "pick up the blue mug". The table has a red mug, a blue mug, a
bowl and a banana, and the robot has never been trained on any of them.

1. The wrist camera takes a colour photo and a depth image.
2. The software sends the photo and the words "blue mug" to Grounding DINO.
3. Grounding DINO returns one box, around the blue mug, with a score. The score is
   above the threshold, so the robot accepts it.
4. The software then gives that box to SAM as a prompt, and SAM returns the exact
   outline of the blue mug.
5. The robot keeps only the depth pixels inside the outline, and turns them into a
   small point cloud of the blue mug alone.
6. A [grasp model](../../05_grasp-models/01_overview.md) works out where to close the
   gripper on that point cloud.
7. The arm moves, grasps and lifts the mug.

Step 3 is where a wrong answer is most likely, so if Grounding DINO returns two
boxes, or none, or a low score, the robot should stop and ask rather than guess.
A good system also checks the result afterwards, for example by asking a
[vision-language
model](../../07_language-models/02_most-used/02_vision-language-models.md)
whether the gripper is now holding a blue mug.

The words in step 2 came straight from the person, but when the instruction is
longer, such as "tidy the table", a [language
model](../../07_language-models/03_also-used/01_language-models-as-planners.md)
can break it into short phrases like "blue mug" first.

---

## 7. What goes wrong

Useful as these models are, they fail in ways that a closed-vocabulary detector
does not, and the list below gives the common ones.

- **Similar words, different answers.** "Mug", "cup" and "coffee mug" can give
  different boxes on the same photo, so people test several phrasings and keep the
  one that works best for their objects.
- **Things with no everyday name.** Two similar metal parts may differ only by a
  hole, which words cannot describe, so an ordinary detector trained on those two
  parts does better here.
- **Colours, positions and counting.** "The mug on the left" or "the second bowl"
  is harder for these models than a plain name, because they often pick the most
  mug-like thing and ignore the rest of the phrase. The robot can apply the "left"
  part itself, using the box positions.
- **Speed.** These models are large, so on a small computer on the robot they may
  take much longer than a small closed-vocabulary detector. People often run them
  once to find the object and then use something faster, such as a tracker, to
  follow it.
- **No sense of when they are wrong.** They return a confident box for
  "screwdriver" even when the object is a pen, and the score helps a little but is
  not reliable. So safety decisions should never rest on these models alone.
- **SAM does not know what it outlined.** It will happily outline a shadow or a
  reflection if that is where the click landed.

---

## 8. Why this kind, and what it costs

Now that you have seen what these models do and where they fail, this section
answers four questions: what they are, what they do for you, why you would choose
them over the obvious alternative, and what they cost.

Open-vocabulary models find things in a picture from words or clicks given at the
time, rather than from a fixed list learned in training. So they let a robot handle
new objects the same day, with no new photos and no training, because a person can
simply name the object and the robot can then find it.

The obvious alternative is to train an ordinary detector on your own objects,
and for a factory that handles the same five parts for years that is usually the
better choice, because such a detector is smaller, faster, more repeatable and
more accurate on those five parts. The open-vocabulary model wins instead when
the list of objects is long, changes often, or is not known in advance, such as
in a home, a laboratory or a warehouse with thousands of items. It is also
useful for making training labels for a small detector, since you can let
Grounding DINO and SAM label your photos, check them by eye, and then train the
small detector on the result.

The costs are these. The models are large and need a GPU to run at a useful
speed, and the same object can give different answers for slightly different
words. Then they give no guarantee about any answer, so they need a check
afterwards. Finally, some newer versions come with licences that must be read
carefully before commercial use.

---

## 9. The written alternative

There is no written alternative for finding things from words, because the link
between a word and what the thing looks like can only be learned from a very
large number of pictures with captions. Only the click-to-outline half has a
partial written stand-in. After the table is removed,
[clustering](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
splits the depth points that are left into separate objects without knowing what
they are, as long as those objects stand apart. The robot can then choose an
object by its place, such as the nearest one, but never by its name.

---

## 10. Where to read next

- [Tracking and motion](../03_also-used/03_tracking-and-motion.md) is the next page, and it shows
  how SAM 2 and other models follow an object through a video.
- [Object detection](01_object-detection.md) and [segmentation](02_segmentation.md)
  explain the closed-vocabulary models these are compared with.
- [3D feature maps](../../04_3d-models/03_also-used/02_3d-feature-maps.md) put CLIP and DINOv2
  features into a 3D map of a room, so the robot can search the room by words.
- [Vision-language models](../../07_language-models/02_most-used/02_vision-language-models.md) go
  further, because they answer full questions about a picture, not only "where is
  it".
- For downloadable models and their licences, read
  [models that find](../../../02_perception/02_object-perception/04_models-that-find.md).
- For how these models fit with larger robot models, read
  [foundation models](../../../03_frameworks/08_frontier/02_foundation-models.md).
