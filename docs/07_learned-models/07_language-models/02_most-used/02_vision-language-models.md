# Vision-language models

This page answers one question: how can a model look at a camera picture and answer a
question about it in words, and what can a robot arm do with those answers?

This is a page for a reader who has read the [chapter overview](../01_overview.md) and
the page on [language models as
planners](../03_also-used/01_language-models-as-planners.md). So you should already
know that a language model reads and writes tokens, and that a token is turned into a
list of numbers. It also helps to have read the [seeing models
overview](../../03_seeing-models/01_overview.md), because this page compares the two.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models of this kind](#5-well-known-models-of-this-kind)
   · [5.1 Qwen3-VL](#51-qwen3-vl)
   · [5.2 SmolVLM2](#52-smolvlm2)
   · [5.3 Gemini Robotics ER 2](#53-gemini-robotics-er-2)
   · [5.4 Molmo2-ER](#54-molmo2-er)
   · [5.5 PaliGemma](#55-paligemma)
   · [5.6 LLaVA](#56-llava)
   · [5.7 How to choose](#57-how-to-choose)
6. [Where to read next](#6-where-to-read-next)

---

## 1. What it is

Here is the idea in one sentence. A **vision-language model**, or **VLM**, is a
language model that can also read a picture, so you can ask it questions about what
the picture shows.

Think of showing a friend a photo on your phone. You ask, "Which of these mugs is
mine?" Your friend looks at the photo and says, "The red one, on the left." They used
the picture and your words together, and a vision-language model does the same.

A plain language model cannot do this, because it has never seen the table. A [seeing
model](../../03_seeing-models/01_overview.md), such as an object detector, can see the
table, but it can only answer one fixed question, such as "where is every cup?", with
names from a fixed list. So a vision-language model is the one that can answer a
question that nobody planned for, such as "Which mug is upside down?"

---

## 2. What goes in and what comes out

Two things go in:

- one or more pictures, such as the latest frame from the robot's camera
- a question or an instruction in words

One thing comes out, and that is text. The text can be an ordinary answer, a "yes" or
"no", or numbers written as text, such as the position of a point on the picture.

![One camera picture, three questions, and three answers, one of them a point on the picture](../../../images/language-models/vision-language-models/asking-about-a-picture.svg)

The picture shows three questions about one camera picture. The first two answers are
words, while the third answer is a point, given as two pixel numbers, and the orange
circle shows where that point falls on the picture. The pixel numbers in the picture
are only an example. A **pixel** is one small dot of a camera picture, and a position
on a picture is given as a count of pixels across and down.

The third kind of answer matters most for a robot arm, because words alone cannot tell
a gripper where to go, while a point on the picture can. Combined with a depth camera,
a point on the picture becomes a point in 3D space that the arm can reach. The [camera
basics document](../../../02_perception/01_camera/01_basics.md) explains how a pixel
and a depth reading become a 3D point.

Some models answer with a box around an object instead of a point, and the box is also
written as numbers in the text.

---

## 3. How it works inside

The trick is to turn the picture into tokens, in the same way that a sentence is
turned into tokens. Then the language model reads the picture tokens and the word
tokens together, in one row.

![A picture cut into 16 patches, the patches and the words joined in one row of tokens, and the language model answering](../../../images/language-models/vision-language-models/patches-and-words.svg)

The picture shows the steps, and here they are in order.

1. **Cut the picture into patches.** The picture is cut into a grid of small squares,
   called **patches**. The drawing uses a 4 by 4 grid, so there are 16 patches. But a
   real model uses a much finer grid, because a patch is often 14 or 16 pixels wide,
   so one picture gives hundreds of patches.
2. **Turn each patch into a list of numbers.** A seeing network, called the **vision
   encoder**, reads all the patches, and it turns each patch into a list of numbers
   that describes what is in it, such as "part of a red handle". The vision encoder is
   itself a transformer, the kind of network described in the [chapter
   overview](../01_overview.md#3-how-words-become-numbers).
3. **Make the lists fit.** A small extra network, often called the **projector**,
   changes each patch's list so that it has the same length as a word token's list.
   After this step, the language model can read a patch in the same way as a word.
4. **Join the row.** The patch tokens go first, and then come the word tokens of the
   question, so the model now has one long row of tokens.
5. **Answer one token at a time.** The language model reads the whole row. Then it
   writes the answer, one token at a time, in the same way as it writes any text. Each
   word token can look at every patch token, so the word "mug" in the question can
   find the patches that contain the mug.

A point is written in the same way as any other answer, because the model writes the
digits of the two pixel numbers as ordinary tokens. It learned to do this from
training examples that had points written as text. Some models are trained on far more
of those examples than others, which is why [section 5.4](#54-molmo2-er) singles out one
whose whole purpose is pointing.

These five steps are the recipe LLaVA published in 2023, and [section 5.6](#56-llava) is
about that paper. Every open model in [section 5](#5-well-known-models-of-this-kind) is
built in this shape, with a larger vision encoder, a larger language model and far more
training data. The one hosted model there, in [section
5.3](#53-gemini-robotics-er-2), does not publish what is inside it, so the steps above
describe the models you can download rather than that one.

---

## 4. How it is trained

A vision-language model is trained in stages, and each stage uses a different kind of
data. The table below lists the usual stages, so read it from top to bottom, in the
order the stages happen.

| Stage | What is trained | The data | Where the data comes from |
| --- | --- | --- | --- |
| 1 | the language model alone | text | the public internet, books and code |
| 2 | the vision encoder alone | pictures, each with a caption | the internet; hundreds of millions of pairs |
| 3 | the projector, then all parts together | pictures with captions and descriptions | the internet, and descriptions written by people or by other models |
| 4 | all parts together | pictures with questions and correct answers | people, and questions generated by other models |
| 5, for robots | all parts together | robot camera pictures with questions, points and success labels | robot recordings, labelled by people or by models |

Stages 1 and 2 are usually done by someone else, because the builders of a
vision-language model start from a language model and a vision encoder that already
exist. In stage 2, a common method trains the vision encoder to match each picture
with its own caption and not with the other captions, which teaches it which picture
patches go with which words. The [open-vocabulary models
page](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md) describes this
matching, which is how CLIP was trained.

Stage 4 is the one that teaches the model to answer questions instead of only writing
captions, and this stage is called **instruction tuning**.

Stage 5 is optional, and it is what makes a robot vision-language model. General
models are good at "what is in this picture?", but they are weaker at robot questions,
such as "Where exactly is the handle?", "Did the grasp work?" and "How far through the
task is the robot?" So robot laboratories add examples of exactly these questions, and
the examples come from recordings of robots at work. People or other models then write
the questions and the correct answers.

---

## 5. Well-known models of this kind

Many vision-language models exist, and this section covers the six you will meet in
robot work, with the code for each one and a recommendation at the end. Each sub-section
opens with one short line giving the model's size, the machine it needs and its licence,
in the bands that [section 7 of the chapter
overview](../01_overview.md#7-how-this-chapter-writes-size-machine-and-licence) defines.
So read that line for the band and the table below for the exact figure.

The table has two columns, so read a row from left to right as one sentence about one
model. The left column names the model and says how current it is. The right column
holds the size, the licence, what the model is best at, and the case for choosing it.
The licence given is the terms on the trained numbers, because those are what you
download and keep. One model in the table has no such terms, because it is a hosted
service: you send your picture to somebody else's computer and pay for each answer, and
there is nothing to download. A row says `not stated` where nobody published the
number.

| Model | What decides it |
| --- | --- |
| [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL), most used in 2026 | It comes in sizes of 2, 4, 8 and 32 billion parameters and larger, under Apache-2.0 on the cards checked. It is the best model here at general questions about a picture. Pick it when you want one open model that is good at everything. |
| [SmolVLM2](https://huggingface.co/blog/smolvlm2), most used in 2026 | It comes in sizes of 256 and 500 million parameters and 2.2 billion, under Apache-2.0. It is the best model here at yes-or-no checks on a laptop. Pick it when the robot's own computer has to answer the question. |
| [Gemini Robotics ER 2](https://ai.google.dev/gemini-api/docs/robotics-overview), most used in 2026 | It is a hosted service, so there are no weights to licence and its size is not stated. It is the best model here at pointing, planning and watching video. Pick it when you want robot-specific answers and will pay per question. |
| [Molmo2-ER](https://huggingface.co/allenai/Molmo2-ER), worth betting on | It has 4 billion parameters, under Apache-2.0. It is the best model here at pointing at exact places. Pick it when you need points, from a model you run yourself. |
| [PaliGemma](https://arxiv.org/abs/2407.07726), historical | It has 3 billion parameters, under the Gemma licence, which you must accept. Its job today is being the backbone of a robot policy. Pick it when you are fine-tuning something built on it. |
| [LLaVA](https://arxiv.org/abs/2304.08485), historical | Its 1.5 release came as a 7-billion and a 13-billion model, under the Llama 2 licence on those weights. It explains how all of these are built. Pick it when you are reading the paper that started the recipe. |

### 5.1 Qwen3-VL

Qwen3-VL is **most used in 2026** as the general open vision-language model, and it is
the one the case study in the frameworks book uses.

Size l at 2 to 8 billion parameters and xl above that, a big card for the smallest size
and more for every size up, Apache-2.0 on the cards checked.

Alibaba's Qwen team released the family from September 2025 onwards, in sizes of 2, 4, 8
and 32 billion parameters plus two larger models that activate only part of themselves
per question. Each size comes in an Instruct edition, which answers directly, and a
Thinking edition, which writes out its reasoning first. It reads pictures and video, and
it answers with boxes or with points.

The one idea it is built on is that a picture should not be flattened on the way in. The
five steps in [section 3](#3-how-it-works-inside) throw two things away without saying
so. They take only the last layer of the vision encoder, and they describe where a patch
sat using position numbers meant for a line of words. Qwen3-VL changes both, and its
repository gives its changes names.

The first is called DeepStack, and it fuses several levels of the vision encoder rather
than only the top one. A vision encoder's early levels hold fine detail, such as the
exact edge of a rim, and its later levels hold conclusions, such as that the object is a
mug. Taking only the last level means handing the language model the conclusion and
throwing the detail away, so DeepStack hands it both. The second is called
interleaved-MRoPE, and it is about position. A patch has a place across the picture, a
place down the picture and, in video, a place in time, and this scheme spreads the
position numbers over all three at full detail instead of giving each one its own block
of the number. There is a third change for video alone, which ties frames to real
timestamps, so the model can say when something happened rather than in which frame.

What those changes buy is the things a flattened picture cannot do: counting, exact
positions, and reading the small text on a label. What they cost is tokens. SmolVLM2 in
the next sub-section gets its speed by cutting a frame down to sixty-four tokens;
Qwen3-VL goes the other way and keeps the picture's own shape and several levels of
detail, so the work grows with the size of the picture and the smallest model still
wants a graphics card.

On an arm, the difference shows up when the answer depends on detail rather than on
identity. Asked "which of these mugs is mine?" of two mugs that differ by a printed
name, Qwen3-VL can read the name, and that is a DeepStack-and-resolution question rather
than a question about how big the language model is.

The obvious alternative is a hosted service such as Gemini Robotics ER 2. You pick
Qwen3-VL when the pictures must not leave your building, when you need the same answer
next year, or when the robot asks enough questions that paying for each one adds up. You
also pick it when you want one model for several jobs, because the same checkpoint reads
the instruction, finds the object and reads the label on a box.

It costs you hardware and setup. The way people fit the larger sizes on smaller cards is
to run the FP8 versions that the Qwen team publishes alongside the ordinary ones, which
store each number in fewer bits. The choice that most often goes wrong is the size: the
2-billion model is quick and noticeably worse at counting and at exact positions, and
people blame the wording of their question instead.

The library is `transformers` from Hugging Face. This is the shape its own
[documentation](https://huggingface.co/docs/transformers/en/model_doc/qwen3_vl) gives,
with the smallest instruct model, which runs on one ordinary graphics card.

```python
from transformers import AutoModelForImageTextToText, AutoProcessor

model_id = "Qwen/Qwen3-VL-2B-Instruct"
model = AutoModelForImageTextToText.from_pretrained(model_id, dtype="auto",
                                                    device_map="auto")
processor = AutoProcessor.from_pretrained(model_id)

messages = [{"role": "user", "content": [
    {"type": "image", "image": "table.jpg"},      # the latest camera frame
    {"type": "text", "text": "Point to the handle of the red mug."},
]}]

# apply_chat_template puts the picture and the words in the order
# this model was trained on, and returns tensors ready for the model.
inputs = processor.apply_chat_template(messages, tokenize=True,
                                       add_generation_prompt=True,
                                       return_dict=True, return_tensors="pt")
inputs = inputs.to(model.device)

generated = model.generate(**inputs, max_new_tokens=64)
print(processor.batch_decode(generated[:, inputs.input_ids.shape[1]:],
                             skip_special_tokens=True))
```

The library downloads the model, cuts the picture into patches and writes the answer.
You supply the camera frame, the wording of the question, and the code that reads the
answer. That last part is work: the model writes the point as text, so you parse the
numbers out of the reply, and you ask for a fixed format in the question to make parsing
possible.

### 5.2 SmolVLM2

SmolVLM2 is **most used in 2026** for the small, constant checks a robot makes while it
works, because it is the only model here that runs on an ordinary computer with no
graphics card.

Size m at 256 and 500 million parameters and l at 2.2 billion, a laptop, Apache-2.0.

Hugging Face published it on 20 February 2025, in three sizes of 256 million, 500
million and 2.2 billion parameters, and it reads video as well as still pictures. The
code below uses the 256-million one, and the larger two are run by changing the name.
This family is also the vision-language backbone inside the SmolVLA policy on the [next
page](01_vision-language-action-models.md#51-smolvla-the-one-to-start-with).

The one idea it is built on is that the expensive part of a vision-language model is the
number of picture tokens, not the size of the language model. So the compression of the
picture, which is step 3 of [section 3](#3-how-it-works-inside), is where its designers
did their work.

Inside, it is a SigLIP vision encoder and a SmolLM2 language model, which is the
ordinary arrangement. What is not ordinary is how hard the patches are squeezed. The
method is called pixel shuffle, and it folds the encoder's grid of patch lists so that
a square of neighbouring patches becomes a single token, whose list of numbers is as
long as all of theirs put together. SmolVLM's authors fold a four-by-four square, so
sixteen tokens become one, where larger models fold a two-by-two square and four become
one. A picture of 512 pixels a side therefore reaches the language model as about
sixty-four tokens instead of a thousand. Two further details go with it. A high-resolution picture is cut into
sub-images, with a shrunken copy of the whole picture sent alongside them, and each
piece carries a position token that was learned during training rather than a written
label such as "row 1, column 2", which the authors found trains more steadily.

What the squeeze buys is the thing the sub-section opens with: a frame that costs only
sixty-four tokens is cheap enough for an ordinary processor, which is why this is the
only model here with no graphics card in its requirements. What it costs is detail, and
this is the part people get wrong. The weakness of the 256-million model is usually
blamed on the language model being small, but the compression is doing much of the
damage: whatever distinguished two similar objects may have been folded away before the
language model received anything. Qwen3-VL, above, makes the opposite choice on exactly
this point.

On an arm, the split is clean. "Is the mug in the bowl?", asked after every step on the
robot's own board, is a question about one large, obvious relationship, and sixty-four
tokens hold that easily. "Which of these three identical mugs is chipped?" is a question
about a few pixels, and those pixels were folded together with their neighbours before
the language model received them.

The obvious alternative is Qwen3-VL. You pick SmolVLM2 when the question is simple and
the answer is needed often: "is the mug in the bowl?" asked after every step, on the
robot's own computer, with no network and no bill. It is also MLX-ready, which means it
runs with Apple's own machine-learning library, so it works on a Mac without a graphics
card.

It costs you capability, and the drop is real rather than slight. The smallest model is
poor at counting, at exact positions and at anything needing several steps of reasoning,
so use it for yes-or-no questions and send the hard ones elsewhere. It will also answer
confidently when it is wrong, and a small model does it more often.

The library is `transformers`, and `pipeline` is its shortest route to a working model:
a **pipeline** is one object holding the processor and the model together, so you hand
it a picture and a question and it hands you text. Install it with `pip install
transformers torch accelerate`.

```python
from PIL import Image
from transformers import pipeline

pipe = pipeline("image-text-to-text",
                model="HuggingFaceTB/SmolVLM2-256M-Video-Instruct")

image = Image.open("table.jpg")   # the latest frame from the robot's camera

messages = [{"role": "user", "content": [
    {"type": "image"},            # says where the picture belongs in the question
    {"type": "text", "text": "Is the red mug in the bowl? Answer yes or no."},
]}]

outputs = pipe(text=messages, images=[image], max_new_tokens=20,
               return_full_text=False)
print(outputs[0]["generated_text"])
```

The model gives you the whole of [section 3](#3-how-it-works-inside): the vision
encoder, the projector and the language model, trained and ready. You supply the
picture, the wording, and the code that turns the reply into something your program can
use. That matters more than it looks, because "Yes, the mug is in the bowl" and "yes"
are both possible answers to the same question, and your code has to accept both.

### 5.3 Gemini Robotics ER 2

Gemini Robotics ER 2 is **most used in 2026** when you want a model that was built for
robot questions rather than adapted to them.

Size not stated, nothing to run on your side because it is a hosted service, and no
licence because there are no weights to license.

Google DeepMind [published
it](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-robotics-er-2/)
on 30 July 2026, and "ER" stands for embodied reasoning, which means reasoning about a
physical scene and a body in it. It points at objects, draws boxes, plans the steps of a
long task, calls your own robot functions as tools, and watches a video feed to say
whether a step worked. Google reports 91.3 per cent accuracy at finding the moment in a
video when something happened, and 57.4 per cent at classifying how far through a task a
robot is.

This is the one model on the page whose central idea cannot be named, because Google
publishes nothing about the inside of it. There is no parameter count, no description of
the vision encoder, and no account of how a point is produced.
The single published fact about its insides is in Google's own documentation, which says
the `gemini-robotics-er-2-preview` endpoint is built on Gemini 3.5 Flash, and nothing
about the shape of Gemini 3.5 Flash is published either. So the five steps in [section
3](#3-how-it-works-inside) describe the models you can download, and whether they
describe this one is not known.

What you can see from outside is the interface, and the interface is not the mechanism.
You can set how long the model reasons before answering, with a thinking level. You can
send a stream of video and audio rather than one still picture. You get a point back as
two numbers in the order y then x, scaled to a range of 0 to 1000 rather than given in
pixels. And you can hand it the names of your own robot's functions and have it ask for
them. Each of those is a fact about what the service accepts and returns, and none of
them tells you what happens in between.

What that costs you is the ability to work out why it was wrong. With a model you can
download, in the way [section 5.6](#56-llava) describes, a wrong answer can be traced to
one half of the model: an object misidentified points at the vision encoder, and an
object seen correctly but described badly points at the language model. Here a wrong
point is just a wrong point. The two levers you have are the wording of your question and the thinking
level, and when neither helps there is nothing further to try.

On an arm, that shows up the first time the points come back consistently wrong in the
same direction, which is a common way for a pointing model to fail. With an open model
you can look at how the picture was cut up and at what resolution it arrived. Here you
measure the error, add a correction in your own code, and hope the next preview of the
service does not change it.

The obvious alternative is Qwen3-VL, which you can download. You pick Gemini Robotics ER
2 when the robot-specific jobs are what you need, because no open model publishes
numbers for progress classification or moment finding, and because this one also has a
streaming endpoint for continuous audio and video rather than one picture at a time. You
pick Qwen3-VL instead when the pictures cannot leave your building, or when you need the
behaviour to stay fixed, because a hosted preview changes under you: Google's own
documentation already tells users of the earlier ER 1.6 endpoint to move to ER 2, and
gives a date after which the old one stops answering.

It costs you money per question, a network connection and control. The model cannot be
downloaded, so every answer is a round trip to Google, which rules it out for anything
inside the control loop and for a robot with no network. The current endpoints are
previews, which means they can change or stop. Your pictures also go to Google, which is
the question to settle before you start rather than after.

The library is `google-genai`, Google's own client. This is the shape of Google's own
pointing example.

```python
from google import genai

# The format has to be asked for, or the reply is prose you cannot parse.
PROMPT = """
Point to no more than 10 items in the image. The label returned should be an
identifying name for the object detected. The answer should follow the json format:
[{"point": <point>, "label": <label1>}, ...]. The points are in [y, x] format
normalized to 0-1000.
"""

client = genai.Client()
uploaded_file = client.files.upload(file="my-image.png")

image_response = client.interactions.create(
    model="gemini-robotics-er-2-preview",
    input=[
        {"type": "image", "uri": uploaded_file.uri,
         "mime_type": uploaded_file.mime_type},
        {"type": "text", "text": PROMPT},
    ],
    generation_config={"thinking_level": "high"},
)
print(image_response.output_text)
```

Google supplies the model and the computer it runs on. You supply an API key in the
environment, the picture, and the code that reads the JSON out of the reply. Note the
coordinates: the points come back as y then x, scaled to 0 to 1000 rather than in
pixels, so you multiply by your picture's height and width in that order. Getting that
pair the wrong way round is the most common mistake with this model.

### 5.4 Molmo2-ER

Molmo2-ER is **worth betting on**, because pointing is the answer a robot can use most
directly, and this is the strongest open model whose whole purpose is pointing.

Size l, a big card, Apache-2.0 for the code and the weights.

The Allen Institute for AI published it on 4 May 2026. It is built on a Qwen3-4B language
model and a SigLIP2 vision encoder, and it is the vision-language model inside the
MolmoAct2 policy on the [next
page](01_vision-language-action-models.md#54-molmoact2-from-the-allen-institute-for-ai).
It continues [Molmo](https://arxiv.org/abs/2409.17146), from 2024, which was the first
open model trained to answer by pointing.

The one idea this family is built on is that the data is the mechanism. Its architecture
is deliberately ordinary, the five steps of [section 3](#3-how-it-works-inside) with a
good encoder and a good language model, and nothing in the network explains why it
points better than Qwen3-VL does. What explains it is what people were paid to produce,
and the Molmo paper is mostly about that.

Two pieces of that collection matter. For the descriptions, people were asked to look at
a picture and talk about it out loud for at least sixty seconds, and the recording was
then transcribed, because it is hard to write a long description and easy to say one.
For the pointing, people were asked to point at something in a picture, say what it was,
and then point at every other instance of the same thing, so that nothing was left out.
Neither step asked a closed model for its answers, which is the claim the project makes
about itself and the reason it can publish the data with the weights. Gemini Robotics ER
2, above, publishes neither the data nor the architecture.

What that buys is two things. A point lands on the object rather than near it, because
the training answers were people's own points rather than the centre of a box. And the
model counts by pointing at each instance in turn rather than by producing a number,
which is a different and more reliable way to count than asking a language model for a
total. What it costs is breadth, because a model trained on scenes and pointing is not
the one to ask about the text on a label.

On an arm, the difference shows up the moment the grasp has to be somewhere particular.
A box around a mug tells you the mug is there; a point on the handle tells the arm where
to close the gripper, and the [camera basics
document](../../../02_perception/01_camera/01_basics.md) turns that point and a depth
reading into a place in the world.

The obvious alternative is Gemini Robotics ER 2, which also points. You pick Molmo2-ER
when you want those answers from a model you run yourself, under Apache-2.0 on the
weights as well as the code, and its authors report beating both GPT-5 and Gemini
Robotics ER 1.5 Thinking on 9 of 13 established tests of reasoning about physical
scenes, with an average score of 63.8 per cent. Those numbers come from the people who
built it, on benchmarks rather than on your robot, so treat them as a reason to try it
rather than as proof.

The practical cost is tooling. The model is run through the project's own
[molmo2](https://github.com/allenai/molmo2) code rather than through a one-line
`transformers` pipeline, so there is more to install.

The library is the project's own. Its predecessor, Molmo 7B, does load straight from
`transformers`, and this is its own model card's example, which is the shortest working
pointing code in this family.

```python
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
from PIL import Image

# trust_remote_code lets the checkpoint bring its own model code with it.
processor = AutoProcessor.from_pretrained("allenai/Molmo-7B-D-0924",
                                          trust_remote_code=True,
                                          torch_dtype="auto", device_map="auto")
model = AutoModelForCausalLM.from_pretrained("allenai/Molmo-7B-D-0924",
                                              trust_remote_code=True,
                                              torch_dtype="auto", device_map="auto")

inputs = processor.process(images=[Image.open("table.jpg")],
                           text="Point to the handle of the red mug.")
inputs = {k: v.to(model.device).unsqueeze(0) for k, v in inputs.items()}

output = model.generate_from_batch(
    inputs, GenerationConfig(max_new_tokens=200, stop_strings="<|endoftext|>"),
    tokenizer=processor.tokenizer)
print(processor.tokenizer.decode(output[0, inputs["input_ids"].size(1):],
                                 skip_special_tokens=True))
```

The library handles the picture, the patches and the writing of the answer. You supply
the frame, the question and the parsing, because the point arrives inside the text. You
also supply the depth reading, since a point on the picture is not yet a place in the
world, and [section 2](#2-what-goes-in-and-what-comes-out) explains that step. For
Molmo2-ER itself, follow the molmo2 repository, because its model card sends you there
instead of publishing a snippet of its own.

### 5.5 PaliGemma

PaliGemma is **historical** on this page, and it is here for one practical reason: robot
policies are built on it, so its licence becomes your licence.

Size l, a big card, the Gemma licence on the weights, and a download gated behind an
account.

Google published it in 2024 as a small open vision-language model, meant to be
fine-tuned for one job rather than chatted with. π0 and π0.5, the two
vision-language-action models on the [next
page](01_vision-language-action-models.md#52-the-pi-models-from-physical-intelligence),
are built on top of it.

The one idea it is built on is that a model which will always be fine-tuned should be
trained differently from a model that will be talked to. Its parts are a SigLIP-So400m
vision encoder and a Gemma-2B language model, which is the ordinary arrangement again.
The difference is in the attention, and it is the only structural difference from
LLaVA's recipe in this whole section.

In the shape [section 3](#3-how-it-works-inside) describes, every token is read in one
direction: each token may look at the tokens before it and not at the tokens after it,
because that is how a model that writes text one token at a time has to work. PaliGemma
splits the row in two. The picture tokens and the question get full attention in both
directions, so every one of them may look at every other, forwards as well as
backwards, and only the answer is written one token at a time with each token seeing
only what came before it. Letting the question look at itself and at the whole picture
at once gives the model a better reading of a short instruction before it starts to
answer, and a short instruction of a fixed shape is exactly what a fine-tuned model
gets.

The second deliberate choice is what the project left out. PaliGemma was published
without instruction tuning, which is stage 4 of [section 4](#4-how-it-is-trained), on
the stated grounds that it is a base model to transfer from. That is the whole trade. It
transfers with small amounts of fine-tuning, which is why π0 and π0.5 start from it, and
asked a question cold it answers poorly, because nobody taught it to follow
instructions.

On an arm, the two choices show up as the difference between a model you prompt and a
model you train. With Qwen3-VL you change the wording of your question until the answers
improve. With PaliGemma there is little point, because it was never taught to follow an
instruction of a kind it had not been trained on, so the only way to make it do your job
is to fine-tune it on examples of your job. That is why it appears on this page as a
part of something else rather than as a tool of its own.

You would not pick PaliGemma to answer questions today, because Qwen3-VL and SmolVLM2
are newer, better at conversation and easier to run. You meet it anyway when you
fine-tune a policy that contains it, and then its terms matter: its model card carries
the Gemma licence rather than Apache-2.0, and the download is gated, so you have to
accept the licence on the Hugging Face website with an account. LeRobot's π0.5 recipe
fails at the first step until you do, which is the single most common error people hit
when training that model.

It costs you a licence that travels. A model you fine-tune from PaliGemma inherits the
Gemma terms, so check them before a commercial plan depends on the result.

There is no code of its own to show here, because you will almost never call PaliGemma
directly. What you do instead is accept its licence and log in, once, before training
any model built on it.

```bash
# Accept the licence at huggingface.co/google/paligemma-3b-pt-224 first,
# then give your machine an account that has accepted it.
hf auth login
```

Hugging Face supplies the download and the licence check. You supply the account and the
acceptance, and you read the terms, because nobody else in your project will.

### 5.6 LLaVA

LLaVA is **historical**, and it is on this page because it is the recipe every model
above follows.

Size l, a big card for the 7-billion model and a workstation for the 13-billion one, the
Llama 2 licence on the weights.

A university group published it in 2023, and its 1.5 release came as a 7-billion and a
13-billion model. It showed that you do not need to train a vision-language model from
nothing: take an existing vision encoder, take an existing language model, join them
with a small **projector** network, and train on pictures with questions and answers.
[Section 3](#3-how-it-works-inside) is a description of that recipe.
[PaLM-E](https://arxiv.org/abs/2303.03378), from Google in the same year, did the robot
version of the same move, feeding robot camera pictures into a large language model and
using the answers to plan tasks.

The one idea it is built on is that the join can be tiny. Two large models already
existed, a CLIP vision encoder that had learned what pictures contain and a language
model that had learned to write, and LLaVA's contribution was the small piece between
them. In the first release that piece was a single layer, and in 1.5 it became two.
Everything else in the model was already trained by somebody else.

That smallness decides the training, which runs in two stages. In the first stage only
the join is trained, so the encoder and the language model are left exactly as they
were, and all the training does is teach the join to write a patch's numbers in a form
the language model can read. In the second stage the language model is allowed to change
too, and it is trained on questions and answers. The questions and answers themselves
are the other half of the idea: a text-only GPT-4 wrote them, from captions and box
coordinates for each picture rather than from the picture, so a model that had never
seen an image invented the conversations used to teach one.

What that buys is the reason every model above it exists. The 13-billion model's whole
training fits on one machine of eight cards in about a day, on publicly available data,
so a university group rather than a laboratory can do it. What it costs is set by the
same two choices. A frozen encoder puts a ceiling on what the model can see, which is
what Qwen3-VL's DeepStack later went back and changed. And the instruction data came out
of another model, which is precisely the practice Molmo2-ER refused, three sub-sections
above, and spent its own budget on people instead.

On an arm, LLaVA's two choices come back as your own the first time you fine-tune a
vision-language model on your robot's pictures. You have to decide whether to leave the
vision encoder frozen, which is cheap and keeps the ceiling, or to train it as well,
which is expensive and the only way the model will learn to see your workshop's
lighting. And you have to decide where your questions and answers come from, which is
the choice between an afternoon of asking a larger model for them and a week of writing
them yourself. LLaVA answered both questions one way and Molmo2-ER answered the second
one the other way, and reading the two is how you see what each answer bought.

You would not pick LLaVA for a robot now. Qwen3-VL is the obvious alternative and is
better at every part of the job. You read LLaVA to understand why the newer models have
the shape they do, and that is worth an hour, because it tells you which part to change
when a model is weak: a model that mistakes objects has a vision encoder problem, and a
model that sees correctly and answers badly has a language model problem.

It costs you nothing but time, since nobody should deploy it. The models that came after
it are better in every direction, and the reason to read the paper is the idea rather
than the checkpoint.

There is no code for it here on purpose. The code in [section 5.2](#52-smolvlm2) is
LLaVA's recipe as it stands in 2026, with a smaller encoder, a smaller language model
and far more training data, and running that is a better use of your graphics card than
running the 2023 original.

### 5.7 How to choose

Start with SmolVLM2 on your own computer. It answers yes-or-no questions well enough to
build the check that says whether a step worked, it costs nothing, and it teaches you how
much of the problem is the wording of your question rather than the model.

Three things change that answer.

- **You need a point, not a word.** Then use Molmo2-ER if you run your own hardware, or
  Gemini Robotics ER 2 if you would rather pay per question than own a graphics card.
  Both were trained to point, and a general model points less accurately.
- **The questions keep getting harder.** Then move to Qwen3-VL, and pick the size by the
  card you have. This is the default when one model has to handle reading labels,
  finding objects and following an instruction.
- **You want planning, progress checks and tool calls in one place.** Then use Gemini
  Robotics ER 2, which is the only model here that publishes numbers for those jobs, and
  accept that your pictures leave your building and the endpoint is a preview.

Whichever you choose, do not put it inside the loop that moves the arm. Every model on
this page answers in a fraction of a second at best, so it chooses the target and checks
the result, while faster code does the moving. The [frontier
document](../../../03_frameworks/08_frontier/02_foundation-models.md#5-google-deepmind-gemini-robotics-2-and-er-2)
has more on Gemini Robotics ER 2, and on the other robot models built on top of
vision-language models.

---

## 6. Where to read next

- [Vision-language-action models](01_vision-language-action-models.md) takes a
  vision-language model and teaches it to output arm movements as well as words.
- [Open-vocabulary models](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md) in the
  seeing chapter covers the smaller models that find objects from words, such as
  CLIP, Grounding DINO and SAM.
- [Language models as planners](../03_also-used/01_language-models-as-planners.md) shows how the
  answers from this page are fed back into a plan.
- [Models that find](../../../02_perception/02_object-perception/04_models-that-find.md)
  in the perception book compares finding models in more depth, including when a
  large model is worth its cost.
- For the robot models built on vision-language models today, read
  [foundation models and generalist policies](../../../03_frameworks/08_frontier/02_foundation-models.md).
