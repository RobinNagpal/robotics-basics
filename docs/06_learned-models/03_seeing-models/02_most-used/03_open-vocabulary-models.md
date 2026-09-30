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

It helps to see the models named so far side by side, and all of these are real
models that are widely used in robot research.

- **CLIP** (Contrastive Language-Image Pre-training), from OpenAI, scores how well a
  picture matches a sentence, and it does not draw boxes. It is often used inside
  other models, and for choosing the right object from a few candidates.
- **OWL-ViT** and **OWLv2**, from Google, are detectors that take words, and OWLv2
  trained itself further by labelling a very large number of internet pictures with
  its own boxes.
- **Grounding DINO** takes a picture and a phrase and returns boxes, so it is the
  most common choice for "find this object by name".
- **Segment Anything (SAM)**, from Meta, takes a click or a box and returns an
  outline, but it does not name anything.
- **SAM 2** is the next version, and it also works on video, keeping the outline of
  the same object from frame to frame.
- **DINOv2**, from Meta, gives general features for every patch of a picture, so it
  is used as the base of many other models, and for matching the same part across
  two photos.

Grounding DINO and SAM are often used together, in a pairing called
Grounded-SAM, because Grounding DINO turns words into a box and SAM then turns
that box into an exact outline. Newer versions of SAM can take a short phrase
directly and outline every object that matches it. The deeper document [models
that
find](../../../02_perception/02_object-perception/04_models-that-find.md#14-open-vocabulary-models)
lists these models with their licences and says which ones you can download.

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
[clustering](../../../05_programming-techniques/05_image-and-point-cloud-processing/02_most-used/03_clustering.md)
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
