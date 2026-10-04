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
   · [Qwen3-VL](#51-qwen3-vl)
   · [SmolVLM2](#52-smolvlm2)
   · [Gemini Robotics ER 2](#53-gemini-robotics-er-2)
   · [Molmo2-ER](#54-molmo2-er)
   · [PaliGemma](#55-paligemma)
   · [LLaVA](#56-llava)
   · [How to choose](#57-how-to-choose)
6. [A worked example: fetching the right mug](#6-a-worked-example-fetching-the-right-mug)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why use a vision-language model, and what it costs](#8-why-use-a-vision-language-model-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

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
robot work, with the code for each one and a recommendation at the end. The size of a
model is given as its number of **parameters**, which are the adjustable numbers inside
the network that training sets, and more parameters usually means a better answer from a
bigger computer.

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
the one the case study in the frameworks book uses. Alibaba's Qwen team released the
family from September 2025 onwards, in sizes of 2, 4, 8 and 32 billion parameters plus
two larger models that activate only part of themselves per question. Each size comes in
an Instruct edition, which answers directly, and a Thinking edition, which writes out
its reasoning first. It reads pictures and video, and it answers with boxes or with
points.

The obvious alternative is a hosted service such as Gemini Robotics ER 2. You pick
Qwen3-VL when the pictures must not leave your building, when you need the same answer
next year, or when the robot asks enough questions that paying for each one adds up. You
also pick it when you want one model for several jobs, because the same checkpoint reads
the instruction, finds the object and reads the label on a box.

It costs you hardware and setup. The larger sizes need a graphics card of their own, and
the way people fit them on smaller cards is to run the FP8 versions that the Qwen team
publishes alongside the ordinary ones, which store each number in fewer bits. The
licence is Apache-2.0 on the 2, 8, 32 and 235 billion sizes, read from their model cards
in October 2026. The choice that most often goes wrong is the size: the 2-billion model
is quick and noticeably worse at counting and at exact positions, and people blame the
wording of their question instead.

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
graphics card. Hugging Face published it on 20 February 2025, in three sizes of 256
million, 500 million and 2.2 billion parameters, and it reads video as well as still
pictures. The code below uses the 256-million one, and the larger two are run by
changing the name. This family is also the vision-language backbone inside the SmolVLA
policy on the [next
page](01_vision-language-action-models.md#51-smolvla-the-one-to-start-with).

The obvious alternative is Qwen3-VL. You pick SmolVLM2 when the question is simple and
the answer is needed often: "is the mug in the bowl?" asked after every step, on the
robot's own computer, with no network and no bill. It is also MLX-ready, which means it
runs with Apple's own machine-learning library, so it works on a Mac without a graphics
card.

It costs you capability, and the drop is real rather than slight. A
256-million-parameter model is poor at counting, at exact positions and at anything
needing several steps of reasoning, so use it for yes-or-no questions and send the hard
ones elsewhere. It will also answer confidently when it is wrong, which is the failure
that [section 7](#7-what-goes-wrong-and-what-people-do-about-it) warns about, and a
small model does it more often.

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
robot questions rather than adapted to them. Google DeepMind [published
it](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-robotics-er-2/)
on 30 July 2026, and "ER" stands for embodied reasoning, which means reasoning about a
physical scene and a body in it. It points at objects, draws boxes, plans the steps of a
long task, calls your own robot functions as tools, and watches a video feed to say
whether a step worked. Google reports 91.3 per cent accuracy at finding the moment in a
video when something happened, and 57.4 per cent at classifying how far through a task a
robot is.

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
directly, and this is the strongest open model whose whole purpose is pointing. The
Allen Institute for AI published it on 4 May 2026. It has 4 billion parameters, built on
a Qwen3-4B language model and a SigLIP2 vision encoder, and it is the vision-language
model inside the MolmoAct2 policy on the [next
page](01_vision-language-action-models.md#54-molmoact2-from-the-allen-institute-for-ai).
It continues [Molmo](https://arxiv.org/abs/2409.17146), from 2024, which was the first
open model trained to answer by pointing.

The obvious alternative is Gemini Robotics ER 2, which also points. You pick Molmo2-ER
when you want those answers from a model you run yourself, under Apache-2.0 on the
weights as well as the code, and its authors report beating both GPT-5 and Gemini
Robotics ER 1.5 Thinking on 9 of 13 established tests of reasoning about physical
scenes, with an average score of 63.8 per cent. Those numbers come from the people who
built it, on benchmarks rather than on your robot, so treat them as a reason to try it
rather than as proof.

It costs you a graphics card for its 4 billion parameters, and it costs you breadth,
because a model specialised for scenes and pointing is not the one to ask about the text
on a label. The practical cost is tooling: the model is run through the project's own
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
policies are built on it, so its licence becomes your licence. Google published it in
2024 as a small open vision-language model of about 3 billion parameters, meant to be
fine-tuned for one job rather than chatted with. π0 and π0.5, the two
vision-language-action models on the [next
page](01_vision-language-action-models.md#52-the-pi-models-from-physical-intelligence),
are built on top of it.

You would not pick PaliGemma to answer questions today, because Qwen3-VL and SmolVLM2
are newer, better at conversation and easier to run. You meet it anyway when you
fine-tune a policy that contains it, and then its terms matter: its model card carries
the Gemma licence rather than Apache-2.0, and the download is gated, so you have to
accept the licence on the Hugging Face website with an account. LeRobot's π0.5 recipe
fails at the first step until you do, which is the single most common error people hit
when training that model.

It costs you a licence to read. The Gemma terms are not Apache-2.0, and a model you
fine-tune from PaliGemma inherits them, so check them before a commercial plan depends
on the result.

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
above follows. A university group published it in 2023, and its 1.5 release came as a
7-billion and a 13-billion model whose weights carry the Llama 2 licence rather than a
permissive one. It showed that you do not need to train a vision-language model from
nothing: take an existing vision encoder, take an existing language model, join them
with a small **projector** network, and train on pictures with questions and answers.
[Section 3](#3-how-it-works-inside) is a description of that recipe.
[PaLM-E](https://arxiv.org/abs/2303.03378), from Google in the same year, did the robot
version of the same move, feeding robot camera pictures into a large language model and
using the answers to plan tasks.

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
build the success check in [section 6](#6-a-worked-example-fetching-the-right-mug), it
costs nothing, and it teaches you how much of the problem is the wording of your
question rather than the model.

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

## 6. A worked example: fetching the right mug

A single arm stands at a table with two mugs, a bowl and an apple, and a camera looks
at the table from the front. A person then says: "Put my red mug in the bowl."

1. **Find the target.** The robot sends the camera picture to the vision-language
   model with the question "Point to the handle of the red mug." The model answers
   with a point, in pixels.
2. **Turn the point into 3D.** The robot reads the depth camera at that pixel, and
   with the camera's known position this gives a 3D point on the handle.
3. **Choose the grasp and move.** A [grasp
   model](../../05_grasp-models/01_overview.md) chooses how to hold the mug near that
   point. Ordinary motion planning moves the arm there, closes the gripper, and
   carries the mug over the bowl. The vision-language model is not used during the
   movement, because it is too slow.
4. **Check after each step.** After each step, the robot asks the vision-language
   model: "Is the red mug in the bowl?" It asks the same question each time, and waits
   for "yes".

![Four camera frames of the mug being moved into the bowl, with the answer No, No, No, Yes below them](../../../images/language-models/vision-language-models/checking-success.svg)

The picture shows the four checks. The answer stays "no" while the mug is on the
table, in the air, and on its way, and it turns to "yes" only after the mug is in the
bowl. Checking whether a step worked is called **success detection**, and it is one of
the most common uses of a vision-language model on a robot, because it replaces a
check that someone would otherwise have to program by hand for every task.

If the answer is still "no" after the last step, the robot does not simply stop. It
tells a [planner](../03_also-used/01_language-models-as-planners.md#feeding-back-what-happened)
what happened, and the planner writes the next steps.

---

## 7. What goes wrong, and what people do about it

A vision-language model is good at "what" and weaker at "exactly where" and "exactly
how much". The list below gives the common failures, and the usual fix for each one.

- **It is not precise about position.** A point from the model can be several pixels
  off, which can be enough to miss a small handle. The fix is to use the point only to
  choose the object, and then measure the object with a depth camera and a [seeing
  model](../../03_seeing-models/02_most-used/02_segmentation.md) that outlines it
  exactly.
- **It miscounts, and mixes up left and right.** Counting many small objects, and
  telling left from right, are known weak points. Left and right are also ambiguous:
  the camera's left may be the robot's right. The fix is to ask for points instead of
  words, and to do the counting and the left-right logic in ordinary code.
- **It says things that are not there.** Like a language model, a vision-language
  model can hallucinate, which means it describes an object that is not in the
  picture. The fix is to ask for a point, and then check with the depth camera that
  something is really there.
- **It says "yes" too easily.** For success detection, a wrong "yes" is worse than a
  wrong "no", because the robot moves on and the mistake is hidden. The fixes are to
  ask from two camera views, to ask the question in the opposite form as well ("Is the
  bowl empty?"), and to back the answer with a measurement, such as the weight on a
  scale or how far the gripper closed.
- **It misses small details.** The picture is cut into patches, and a detail smaller
  than a patch, such as a thin crack or a lid that is almost closed, can be lost. The
  fix is to crop the picture around the object and ask again.
- **It is slow.** A large model takes from a fraction of a second to a few seconds per
  answer. That is fine for "which mug?" and "did it work?", but it is far too slow to
  steer the arm while it moves.

---

## 8. Why use a vision-language model, and what it costs

A vision-language model reads a picture and a question, and answers in words or
points. It lets a robot find an object from a description, and check its own work,
without anyone writing a special program for each object or each task.

The obvious alternative is an [object
detector](../../03_seeing-models/02_most-used/01_object-detection.md) trained on a
fixed list of object names. A detector is much faster, because it answers in
milliseconds, where a vision-language model takes seconds. It is also more precise
about position, small enough to run on the robot's own computer, and it always gives
an answer in the same form. So if your robot only ever handles the same five kinds of
object, a detector is the better choice. The next step up is an [open-vocabulary
model](../../03_seeing-models/02_most-used/03_open-vocabulary-models.md), which finds
objects from any name, but still only answers "where is this?". The vision-language
model earns its place when the question itself changes, as in "the mug that is upside
down", "the one with the chipped rim", or "did the lid close?".

But it costs you speed, hardware and certainty in return. A useful model needs a large
graphics card or a paid online service, and it answers in seconds, not milliseconds.
Its answers are also not guaranteed, so anything that matters has to be checked with a
measurement.

---

## 9. The written alternative

There is no full written alternative, because no written program can answer a question
that nobody planned for. But the two jobs a vision-language model does most on an arm
do have written versions. To pick out an object by a fixed property, such as "the red
mug", [thresholding and colour
masks](../../../06_programming-techniques/05_image-and-point-cloud-processing/02_most-used/01_thresholding-and-colour-masks.md)
is fast and exact, while to check that a step worked, a measurement is more reliable.
[Sensor
streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#thresholds-that-do-not-flicker-hysteresis-and-debouncing)
turns how far the gripper closed, or the weight on a scale, into a clean yes or no.

The written way wins whenever the question is fixed and a colour or a sensor reading
answers it. But the vision-language model wins when the question itself changes.

---

## 10. Where to read next

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
