# Language models

This chapter is about models that work with words. It answers three questions.
What does a model that reads words do for a robot arm? How do words get into a
model at all? And which of the three kinds of language model in this chapter
should you read about first?

It is for a reader who has read the first chapter of this book,
[what models are](../01_what-models-are/01_what-a-model-is.md). You should know that
a model is a program that turns numbers in into numbers out, and that it learns
this from examples. You do not need to know anything about language models yet.
Every new word is explained where it first appears.

## Contents

1. [What language models are for](#1-what-language-models-are-for)
2. [The question they answer for a robot arm](#2-the-question-they-answer-for-a-robot-arm)
3. [How words become numbers](#3-how-words-become-numbers)
4. [The three kinds in this chapter](#4-the-three-kinds-in-this-chapter)
5. [How they compare](#5-how-they-compare)
6. [How this chapter connects to the others](#6-how-this-chapter-connects-to-the-others)
7. [Where to read next](#7-where-to-read-next)

---

## 1. What language models are for

The [map of models](../01_what-models-are/06_the-map-of-models.md) sorts the models
in this book into seven families. This chapter covers the fifth one:

> Language models — understand words, and connect words to pictures and actions.

A **language model** is a model that reads text and writes text. It was trained on a
very large amount of written text, most of it from the public internet. During that
training it did one job, over and over again. It saw the start of a sentence, and it
guessed the next word. After enough practice, it guesses well. To guess well, it had
to pick up a great deal about the world. It knows that a spill is cleaned with a
sponge, and that cups go in a cupboard.

The very big language models are called **large language models**, or **LLMs**. The
word "large" means that the model has a very large number of adjustable numbers
inside it, usually billions. You may know some by name, such as ChatGPT, Claude or
Gemini.

A robot arm does not need a model to write essays. It needs three other things that
words can give it.

- A person can tell the robot what to do in ordinary words, instead of writing a
  program.
- The robot can use what the language model knows about everyday objects, such as
  which object is a sponge and what a sponge is for.
- The robot can check its own work by asking a question about a camera picture,
  such as "Is the mug in the bowl?"

---

## 2. The question they answer for a robot arm

Every family of models in this book answers one question for the robot. For this
family the question is:

> What did the person ask for, and what does that mean here, in front of this
> camera?

The first half of that question is about words. The second half is about pictures
and movement. A plain language model can only answer the first half, because it
never sees the table. The models later in this chapter add a camera picture, and
then movement, so that they can answer the second half too.

---

## 3. How words become numbers

A model only works with numbers. So before a model can read a sentence, the sentence
has to be turned into numbers. This happens in two steps.

![A sentence cut into tokens, and each token turned into a list of numbers](../../images/language-models/overview/words-become-numbers.svg)

The picture shows the sentence "put the red mug in the sink" going through both
steps. The numbers in it are made up, and a real model uses far more of them.

In the first step, the sentence is cut into small pieces called **tokens**. A token
is often a whole word, as in the picture. A long or rare word is cut into two or
three tokens. For example, "screwdriver" might become "screw" and "driver". The
model has a fixed list of all the tokens it knows. A typical list has tens of
thousands of entries.

In the second step, each token is looked up in a table. The table gives a list of
numbers for every token. The same token always gets the same list, which is why both
copies of "the" in the picture have the same numbers. The model learned the numbers
in this table during training. Tokens with similar meanings end up with similar
lists, so "mug" and "cup" get lists that are close to each other.

After these two steps, the sentence is a row of number lists. The model reads the
whole row, and works out what each token means in this sentence. The kind of
network that does this is called a **transformer**. A transformer lets every token
look at every other token in the row. That is how the model knows that "red" belongs
to "mug" and not to "sink". The chapter on
[what is inside a neural network](../01_what-models-are/03_inside-a-neural-network.md)
describes networks in general.

This idea matters for the whole chapter. A picture can also be cut into pieces and
turned into lists of numbers. So can a movement of the arm. Once everything is a row
of number lists, one transformer can read words, pictures and movements together.
The next three pages build on that.

---

## 4. The three kinds in this chapter

This chapter has three pages after this one. Each page adds one more thing to what
the model can take in or put out.

![One table and one instruction, used by a planner, a vision-language model and a vision-language-action model](../../images/language-models/overview/three-ways-to-use-words.svg)

The picture shows the three kinds side by side, with the same mug, bowl and
instruction. The planner writes steps. The vision-language model answers a question
about the picture. The vision-language-action model moves the gripper.

1. [Language models as planners](03_also-used/01_language-models-as-planners.md). A language
   model reads an instruction and writes a list of steps, chosen from skills the
   robot already has. It never sees a picture itself.
2. [Vision-language models](02_most-used/02_vision-language-models.md). A **vision-language
   model**, or **VLM**, takes a picture and a question in words, and answers in
   words. A robot uses it to find things, to describe a scene, and to check whether
   a step worked.
3. [Vision-language-action models](02_most-used/01_vision-language-action-models.md). A
   **vision-language-action model**, or **VLA**, takes a picture and an
   instruction, and outputs the movement of the arm directly. It is one model that
   does the seeing, the understanding and the moving.

---

### Most used, and also used

The pages of this chapter are in two groups. The first group, most used, holds
[vision-language-action models](02_most-used/01_vision-language-action-models.md)
and [vision-language models](02_most-used/02_vision-language-models.md). In
2026 these are where most of the work on language and robots happens. The
second group, also used, holds
[language models as planners](03_also-used/01_language-models-as-planners.md).
Planning with a plain language model came first, and it is still used to split
a long instruction into steps, but it is now often done by a vision-language
model instead.

## 5. How they compare

The table below compares the three kinds. Read each row across to see how the three
differ on one point. The columns go in the same order as the pages.

| | Planner | Vision-language model | Vision-language-action model |
| --- | --- | --- | --- |
| What goes in | words | a picture and words | a picture, words and the arm's joint readings |
| What comes out | a list of steps, or a short program | words, or a point on the picture | the next movements of the arm |
| Does it see the table? | no | yes | yes |
| Does it move the arm? | no, other code does | no, other code does | yes |
| How often it runs | once per task, or once per step | once per step, or once per check | many times a second |
| What it is trained on | text | pictures with text | pictures with text, then robot recordings |
| Typical use on an arm | break a long task into steps | find an object, check a step | do the whole task |

The rows show a pattern. Going from left to right, each kind does more of the job
by itself. It also needs more special training data, and more of that data has to
come from real robots. Recordings from real robots are slow and expensive to
collect, so the kind on the right is the hardest to build.

---

## 6. How this chapter connects to the others

Language models rarely work alone on a robot arm. They sit next to models from the
other chapters.

- A planner chooses the steps. Each step is then done by other models, such as a
  [grasp model](../05_grasp-models/01_overview.md) that decides where to hold an
  object, and a [movement model](../06_movement-models/01_overview.md) that moves
  the arm.
- A vision-language model often does the same job as the
  [open-vocabulary models](../03_seeing-models/02_most-used/03_open-vocabulary-models.md) in the
  seeing chapter. Both find objects from a name in words. The vision-language model
  can also answer questions and explain what it sees.
- A vision-language-action model is a movement model. It works in the same way as
  the models in the [movement models](../06_movement-models/01_overview.md) chapter,
  and adds an understanding of words and pictures from the internet. It uses the
  same ideas of
  [action chunks](../06_movement-models/02_most-used/02_action-chunking-transformers.md) and
  [flow policies](../06_movement-models/02_most-used/03_diffusion-and-flow-policies.md).
- Some of the newest robot models also predict what the camera will see next. Those
  are [world models](../08_world-models/01_overview.md), the next chapter.

---

## 7. Where to read next

Start with [language models as planners](03_also-used/01_language-models-as-planners.md). It
introduces the idea of a language model choosing steps, and the other two pages
build on it.

For the current state of the art, read
[foundation models and generalist policies](../../03_frameworks/08_frontier/02_foundation-models.md)
in the frameworks book. It lists every important vision-language-action model as of
September 2026, what each one can do, and whether you can download it. It is written
for a reader who has finished this chapter.
