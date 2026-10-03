# Tokens and embeddings

The page before this one, [Normalisation and
stability](../04_making-training-work/02_normalisation-and-stability.md), ended
by saying that the numbers going into a network have to be scaled so that
training stays steady. That page, and every page before it, quietly assumed
that the input was already a list of numbers, and this chapter is about where
those numbers come from, because nothing a robot deals with arrives as a list
of numbers on its own: a sentence is letters, a photo is light, and the arm's
own readings are angles and forces in units that have nothing to do with each
other.

This page does that job for text, because text is the clearest case and
everything else copies its pattern. It answers four questions. How is a
sentence cut into pieces? How does a piece become a list of numbers? What does
it mean for two of those lists to be near each other? And how does a model find
out what order the pieces came in? It assumes you know what a weight is, what a
layer is and what training does, and nothing at all about language.

The text behind the numbers here is made up: the script
[`turning_the_world_into_numbers.py`](../../diagrams/turning_the_world_into_numbers.py)
writes 3,200 short robot instructions from a set of sentence patterns, then
builds a small tokeniser and a small table of word vectors from them. The
methods are the real ones, worked out in full on that text, so every count and
similarity below is a genuine output. What is small is the scale, because a
real tokeniser is built from a vast amount of text and holds tens of thousands
of pieces, so it cuts words up less finely than this one.

## Contents

1. [A token is a piece of text the model treats as one unit](#1-a-token-is-a-piece-of-text-the-model-treats-as-one-unit)
2. [Why pieces, and not whole words or single letters](#2-why-pieces-and-not-whole-words-or-single-letters)
3. [The embedding table is a lookup](#3-the-embedding-table-is-a-lookup)
4. [Near each other means used in the same way](#4-near-each-other-means-used-in-the-same-way)
5. [Telling the model what order the tokens came in](#5-telling-the-model-what-order-the-tokens-came-in)
6. [What the picture of the geometry leaves out](#6-what-the-picture-of-the-geometry-leaves-out)
7. [Where to read next](#7-where-to-read-next)
8. [Using it in Python](#8-using-it-in-python)

---

## 1. A token is a piece of text the model treats as one unit

A network takes a fixed number of numbers in, so the first job is to cut a
sentence into pieces the network can count. A **token** is one such piece of
text, and the model treats it as a single unit it never looks inside, while a
**tokeniser** is the program that does the cutting and its **vocabulary** is
the list of every piece it is allowed to produce. Each piece has a number,
which is simply its place in that list, and that number is the only thing the
model ever receives.

![The sentence "pick up the blue mug and put it on the tray" above a row of eleven labelled boxes, each with a small number underneath it](../../images/turning-the-world-into-numbers/tokens-and-embeddings/sentence-into-tokens.svg)

One instruction is cut into eleven tokens, and the number under each one is its place in the vocabulary of 429.

The open box character stands for the space in front of a word, which the
tokeniser keeps inside the token so that it can rebuild the sentence exactly.
Every one of those eleven words is common in the text the tokeniser was built
from, so each became a single token, and the model receives the numbers 72, 73,
31, 146, 45, 51, 69, 64, 38, 31 and 121, where the two 31s are both the word
"the". Words that are not common behave differently.

![Five words with how often each appeared in the training text, and the tokens each becomes: mug and gripper stay whole, thermometer becomes four pieces, recalibrate seven, polycarbonate eight](../../images/turning-the-world-into-numbers/tokens-and-embeddings/common-and-rare.svg)

A word the tokeniser saw often gets a token of its own, while a rare word is spelled out of smaller pieces and a word it never saw at all is still spellable.

The word "mug" appeared 1,323 times in the training text and earned a token of
its own, and "gripper" appeared 405 times and earned one too, while
"thermometer" appeared only 25 times and is spelled out of four pieces instead,
and "polycarbonate" never appeared at all and is still spelled out of eight
pieces that do exist. This is called **subword tokenisation**, because the
pieces are parts of words rather than whole words, and it is what lets a model
read a word nobody showed it during training. It also means the token count of
a sentence is not its word count, which matters because everything a model
costs is counted in tokens.

![A bar chart of five robot instructions with three bars each: whole words, subword tokens and single letters](../../images/turning-the-world-into-numbers/tokens-and-embeddings/token-counts.svg)

Five robot instructions are counted three ways, and the subword count always sits between the word count and the letter count.

The first sentence is eleven words and eleven tokens, because every word in it
is common, while the fourth is ten words and twenty-seven tokens, because it
contains "until", "force", "sensor", "reads" and "newtons", none of which the
training text used. Across all five there are 52 words, 93 tokens and 212
letters, which is 1.79 tokens for every word. The next section explains why the
pieces are chosen this way rather than either obvious alternative.

---

## 2. Why pieces, and not whole words or single letters

Subword pieces look like a strange compromise, so this section works out what
the two simpler choices would cost: giving every whole word its own token, or
giving every single letter its own token.

![The sentence "unscrew the polycarbonate lid and place it in the bin" split three ways: ten whole words with one marked unknown in red, twenty-one subword pieces, and forty-four letters](../../images/turning-the-world-into-numbers/tokens-and-embeddings/three-ways-to-split.svg)

The same instruction is split three ways, and the whole-word row loses the one word it has never seen.

A whole-word vocabulary gives the shortest sequence, ten tokens here, and that
is its whole appeal. The cost is in the red box, because "polycarbonate" is not
in the vocabulary and the tokeniser has nothing to hand the model except a
single "unknown" token, which every unseen word also becomes. The model then
cannot tell a polycarbonate lid from a titanium one and cannot spell anything
back out, because the information was thrown away before the model ever ran,
and robot work is full of part names and measurements, so this happens
constantly.

Single letters have the opposite problem, because they never fail, every word
being made of letters the vocabulary already holds, but the sequence is four
times as long at 44 tokens instead of 10. Length is the thing a transformer
cannot afford, since the attention step described in
[Attention](../06_the-transformer/01_attention.md) compares every token with
every other one, so doubling the length makes that step about four times as
much work. Subword pieces take the useful half of each, keeping common words
whole and spelling anything unusual out of smaller pieces, and how short the
sequence gets then depends on how many pieces the vocabulary holds.

![Two falling curves of average tokens per word against vocabulary size, one for the text the tokeniser was built from and one for five unseen instructions, both flattening towards one token per word](../../images/turning-the-world-into-numbers/tokens-and-embeddings/vocabulary-size-curve.svg)

A bigger vocabulary gives shorter sequences, and the gain runs out: most of it has already arrived by about 200 tokens.

With an alphabet alone, 29 tokens in all, it takes 4.81 tokens to write the
average word, and that falls to 1.74 at 129 tokens, to 1.20 at 329 tokens, and
to exactly 1.00 at 665 tokens, where no more merging is possible. The gains get
small quickly while the embedding table described in the next section grows in
direct proportion to the vocabulary, which is why real models settle somewhere
between about 30,000 and 150,000 pieces rather than going further.

The way the pieces are chosen is called **byte pair encoding**, and it is
simpler than its name: the tokeniser starts with every word written out as
single characters, counts every pair of neighbouring pieces across the training
text, joins the most common pair everywhere it appears, and repeats, so each
round adds one new piece to the vocabulary.

![On the left, the ten pairs joined first with how often each appeared; on the right, the word gripper going from eight pieces down to one as those merges are applied](../../images/turning-the-world-into-numbers/tokens-and-embeddings/merge-table.svg)

The first ten merges are listed on the left, and on the right the merge list collapses one word from eight pieces to one in seven steps.

The first pair joined is a space and the letter t, which appeared 11,845 times,
and the third joins the results of the first two into the whole word "the",
which appeared 8,900 times. On the right, "gripper" starts as eight separate
characters and the merges numbered 21, 26, 37, 68, 70, 76 and 77 turn it into
one token. Nothing here chooses meaningful units, because the rule is only ever
about how often a pair appears next to each other, and that is why
"thermometer" splits as "the", "r", "mo", "meter" rather than into anything a
person would call parts of a word. Once the pieces exist, each one needs
numbers of its own, and that is the embedding table.

---

## 3. The embedding table is a lookup

A token number such as 45 is a name rather than a measurement, so feeding it to
a network directly would be wrong, since 45 is not three times as much of
anything as 15. What the model needs is a list of numbers for each token that
it can do arithmetic on, learned during training like any other weight. A
**vector** is an ordered list of numbers, an **embedding** is the vector that
stands for one token, and all of them together, one row per token, make the
**embedding table**.

![A table of ten tokens with their vocabulary numbers and six learned numbers each, with the row for the token mug highlighted and an arrow pointing to it](../../images/turning-the-world-into-numbers/tokens-and-embeddings/embedding-table.svg)

Ten rows of a 429-row embedding table each hold six numbers, and token number 45 picks out the highlighted one.

The lookup is as simple as it sounds, because the tokeniser says the word is
token number 45, the model goes to row 45, and it takes the six numbers there.
The same token always gets the same row, and the numbers start as small random
values and are changed by gradient descent along with every other weight, so by
the end of training they are whatever made the model's predictions good.
Libraries call this a layer rather than a lookup, and there is a reason.

![A row of six numbers that are all 0 except one 1, multiplied by a six-row table, giving exactly the highlighted row](../../images/turning-the-world-into-numbers/tokens-and-embeddings/lookup-as-matrix.svg)

Picking row three is the same arithmetic as multiplying the table by a row of zeros with a single one in the third place.

If you write the token as a row of zeros with a single 1 at its own place and
multiply that row by the table, every term in every column is zero except the
one multiplied by 1, so the answer is exactly the chosen row: column one works
out as 0 times -0.50, plus 0 times -0.54, plus 1 times -0.57, plus three more
zero terms, which gives -0.57. Nobody multiplies in practice, because reading
row 45 out of memory is far cheaper, but writing it this way explains why the
table trains like any other matrix of weights. The table is small here because
the vocabulary is small, and it is not small in a real model.

![A bar chart on a log scale of embedding table sizes, from 2,574 weights for this page's table up to 524,288,000 for a large model](../../images/turning-the-world-into-numbers/tokens-and-embeddings/table-size.svg)

Four embedding tables are compared by the weights each holds and by the memory each needs when every weight is stored in two bytes.

The table on this page holds 429 times 6, which is 2,574 weights, while a
vocabulary of 32,000 at 1,024 numbers a token holds 32,768,000 weights at 65.5
megabytes, and one of 128,000 at 4,096 numbers a token holds 524,288,000
weights, a little over a gigabyte, which is often the single largest block of
weights in a model. The width of a row is also the width that runs through
every layer after it, so it is chosen once and everything else follows. What
makes those numbers useful is where they end up relative to each other.

---

## 4. Near each other means used in the same way

Training never tells the table what any word means, and yet the rows do end up
arranged in a way that is easy to describe, so this section explains what that
arrangement is and how it is measured. Two rows count as similar when they
point the same way, and the measure of that is called **cosine similarity**:
you multiply the two vectors number by number, add up the products, and divide
by the length of each vector, where a vector's length is the square root of the
sum of its squares. The answer runs from +1, meaning the two point exactly the
same way, through 0, meaning they are unrelated, down to -1, meaning they point
exactly opposite ways.

![Two side-by-side tables of six multiplications each, one comparing mug with bowl and one comparing mug with table, each ending in a division that gives the cosine](../../images/turning-the-world-into-numbers/tokens-and-embeddings/cosine-worked.svg)

Cosine similarity is worked out in full twice, and it gives 0.995 for mug against bowl and 0.219 for mug against table.

For mug and bowl the six products add up to 0.4438, the two lengths are 0.6356
and 0.7019, and dividing gives 0.995, while for mug and table the products add
up to only 0.0602 and the same division gives 0.219. The arithmetic is the same
both times, and the difference is entirely in the rows, which came from
counting which words appear near which other words in the made-up instructions.
Doing that for every pair gives a picture of the whole arrangement.

![A ten by ten grid of cosine similarities, with dark blocks where the four containers meet each other, where table meets shelf, where gripper meets wrist and where red meets blue](../../images/turning-the-world-into-numbers/tokens-and-embeddings/similarity-heatmap.svg)

Every pair of ten tokens is scored by cosine similarity, and four blocks appear where things are used in the same way.

Mug, cup, bowl and block score 0.99 against each other, table and shelf score
0.99, gripper and wrist score 1.00 and red and blue score 1.00, while mug
against gripper scores 0.07. Nobody labelled any of these words, and the blocks
appear only because words used in the same position in the same kinds of
sentence end up with the same neighbours. The obvious alternative to cosine is
straight-line distance, so it is worth saying why cosine is used instead.

![Three arrows from the origin: a at (3, 1), b at (6, 2) pointing exactly the same way, and c at (1, 3) pointing elsewhere but ending closer](../../images/turning-the-world-into-numbers/tokens-and-embeddings/cosine-not-length.svg)

Vector b points exactly the same way as a and scores 1.00, while c is closer in a straight line and scores only 0.60.

The arrow b is twice as long as a and points in exactly the same direction, so
cosine gives 1.00 even though the distance between their tips is 3.16, while c
ends only 2.83 away and yet scores 0.60 because it points somewhere else.
Length in an embedding table tends to follow how often a token appears rather
than what it is used for, so throwing length away and keeping direction is what
makes the measure say something about the token rather than about its
frequency. Asking which rows are nearest to a given row is the usual way to
look at a trained table.

![Four small bar charts showing the five nearest tokens to mug, gripper, table and red, with their cosine scores](../../images/turning-the-world-into-numbers/tokens-and-embeddings/nearest-neighbours.svg)

The five nearest tokens to each of four given tokens are found using all 64 numbers of a row rather than the six that fit in a picture.

The nearest tokens to "mug" are cup at 0.92, bottle at 0.88, bowl at 0.87 and
box at 0.85, which are all things an arm picks up, and the nearest to "gripper"
are wrist at 0.99, arm at 0.97, camera at 0.97 and elbow at 0.95, which are all
parts of the robot, after which the list drops to 0.37 because the text holds
only four such words. The nearest to "red" are green, blue and yellow, and then
"carefully" at 0.70, which is a reminder that the grouping follows sentence
position rather than meaning. Everything here treats the tokens as an unordered
collection, which is exactly the problem the next section fixes.

---

## 5. Telling the model what order the tokens came in

Having a row for each token is not yet enough, because the attention step that
follows takes the tokens as a set and compares every one with every other
without caring which came first, and that is easy to show rather than assert.

![Two sentences made of the same six tokens in different orders, each with the sum of its six embedding rows written out, and the two sums identical](../../images/turning-the-world-into-numbers/tokens-and-embeddings/same-tokens-different-order.svg)

"The mug is in the bowl" and "the bowl is in the mug" are the same six tokens, so adding their rows up gives exactly the same six numbers.

Both sentences become the tokens for the, mug, is, in, the and bowl, so adding
the six rows gives -2.59, -0.18, -0.73, +0.06, -0.57 and -0.27 for both, to
every decimal place, because addition does not care about order. A robot told
to put the mug in the bowl would then do the same thing as one told to put the
bowl in the mug, which is why the order has to be put into the numbers
deliberately, and anything that does that is called a **positional encoding**.
The most direct way is to keep a second table with one row for each place in
the sentence rather than for each token, learned in training like the first,
and to add the row for the place to the row for the token.

![A table of six learned position rows on the left, and on the right the row for mug added to the row for position 1 and then to the row for position 4, giving two different results](../../images/turning-the-world-into-numbers/tokens-and-embeddings/position-vectors-added.svg)

The same token at two different places in the sentence becomes two different lists of numbers once the position row is added.

The token for "mug" is -0.50, -0.12, +0.09, -0.03, -0.35, +0.09 wherever it
appears, but at position 1 it becomes -0.27, +0.03, +0.30, +0.18, -0.28, -0.04
and at position 4 it becomes -0.84, -0.11, +0.42, -0.22, -0.36, +0.79, with a
cosine of only 0.554 between them, so the model can now tell the two apart.
What this costs is that the table has a fixed number of rows, so a sentence
longer than it has places for cannot be handled at all, and the row for
position 900 is only ever trained by text that was that long.

The method almost every current model uses instead is **rotary position
embedding (RoPE)**, which turns the numbers rather than adding to them. The row
is taken two numbers at a time, each pair is treated as a point on a flat
sheet, and that point is turned about the origin by an angle that grows in
proportion to the place in the sentence, with each pair given its own turning
rate so that some sweep round quickly and others barely move.

![Three circles showing the first, second and third pair of numbers of the token mug, each with six arrows for positions 0 to 5, turning fast in the first panel and barely at all in the third](../../images/turning-the-world-into-numbers/tokens-and-embeddings/rope-rotation.svg)

The same token is drawn at positions 0 to 5, and its first pair of numbers turns 1.0000 radians a step, its second 0.2154 and its third 0.0464.

The first pair of the row for "mug" starts at (-0.500, -0.120) at position 0
and by position 3 has become (+0.512, +0.048), which is the same point turned
three radians round the circle. Nothing is added and nothing is stretched,
because turning leaves the length of the pair alone, which is part of why this
behaves well during training. The turning rates here were made large on purpose
so that the movement is visible over six positions, and a real model uses far
smaller ones, so that its slowest pairs have barely turned even after thousands
of positions. The reason to prefer turning over adding is not that it is
tidier, but that it changes what attention ends up measuring.

![A table of four pairs of places that are all three apart, each giving the same dot product to six decimal places, beside a curve of the dot product against the gap](../../images/turning-the-world-into-numbers/tokens-and-embeddings/rope-relative.svg)

Four different pairs of places with the same gap of three give exactly the same answer, because turning both rows leaves only the difference between their angles.

When one turned row is multiplied with another and the products are added up,
the two angles only ever appear as their difference, so the answer depends on
how far apart the two tokens are and not on where either of them is. A query at
place 0 with a key at place 3 gives -0.323777, and so do places 2 and 5, places
7 and 10, and places 20 and 23, while without any turning the answer is
+0.453112 whatever the gap. That is what makes rotary position embedding work on
sentences longer than anything in training, because there is no table of
positions to run off the end of and a gap of three means the same thing at
position 20,000 as at position 3. What it costs is that it only applies inside
attention, on the query and key rows, so it is part of that step rather than
something you can do once at the input and forget.

---

## 6. What the picture of the geometry leaves out

Everything so far has described the table as a space with directions in it,
which is useful but is also drawn in a misleading way almost everywhere, so
this section says plainly what is and is not true. The first thing to be
careful about is the flat scatter plot of words that appears in every talk on
this subject.

![Two scatter plots of the same twelve tokens projected onto two different pairs of directions, with the words sitting in completely different places in each](../../images/turning-the-world-into-numbers/tokens-and-embeddings/two-shadows.svg)

The same twelve rows of 64 numbers are flattened onto two different pairs of directions, so the picture changes completely while the table has not changed at all.

Each row in this chapter's table holds 64 numbers and a page can show only two,
so any flat picture is a shadow cast by something with 64 directions in it. In
the first shadow the distance from mug to bowl is 0.053 and from mug to gripper
is 0.121, so mug looks much nearer to bowl, while in the second those become
0.081 and 0.086, which are nearly equal. Neither picture is wrong and neither
is the truth, because the arrangement is the 64 numbers and the picture is a
choice of two directions to look along, and in a real model each row holds a
few thousand numbers, so the shadow is thinner still. How much is lost in the
squashing can be measured rather than guessed.

![Two scatter plots of cosine in the squashed version against cosine using all 64 numbers, one for two directions with a correlation of 0.26 and one for the first six numbers with a correlation of 0.89](../../images/turning-the-world-into-numbers/tokens-and-embeddings/shadow-distorts.svg)

All 2,016 pairs of tokens in the table are plotted, comparing the real cosine with the cosine you get after throwing most of the numbers away.

Flattening to two directions and then measuring cosine tracks the real answer
with a correlation of only 0.26, and the worst pair is wrong by 1.73, which on
a scale running from -1 to +1 means the picture reverses the relationship
completely. Keeping the first six numbers does better at 0.89, and even there
the worst pair is out by 0.78, which is why section 4's scores for mug, cup and
bowl were all 0.99 on six numbers and spread out to 0.92 and 0.87 on all 64.
The second thing to be careful about is the idea that a row holds the meaning
of a word.

![Two sentences whose only difference is mug or bolt, both containing the token "it", with arrows from both to a single row of six numbers](../../images/turning-the-world-into-numbers/tokens-and-embeddings/one-row-many-meanings.svg)

The token "it" has exactly one row in the table, and that row is the same whether "it" means the mug or the bolt.

The lookup happens before anything has read the sentence, so the table cannot
possibly hold what "it" refers to, and the same is true of every word with more
than one sense. What the row holds is a starting point that is good on average
across all the uses of that token, and the work of making it specific to this
sentence is done afterwards by the attention layers, which mix each token's
numbers with those of the tokens around it. By the middle of a trained model
the numbers where "it" sits are nothing like the row that was looked up, and
that is the intended behaviour rather than a flaw.

The arrangement is not tidy even where it is real, because there are far more
properties worth representing than there are directions to put them in, so
several properties share each direction and a direction read off a trained
model usually turns out to mean several things at once. The honest summary is
that the table is a learned convenience which puts tokens used alike in similar
places, that this is genuinely useful, and that the pictures people draw of it
are flat shadows of something nobody can see.

---

## 7. Where to read next

- [Pictures, sound and robot states](02_pictures-sound-and-robot-states.md) is
  the next page, and it does this same job for photos, depth pictures, point
  clouds, sound and the arm's own readings.
- [Attention](../06_the-transformer/01_attention.md) is where these tokens are
  actually used, and where section 5's rotary position embedding is applied.
- [A transformer block](../06_the-transformer/02_a-transformer-block.md) shows
  how a stack of such blocks turns the looked-up rows into something that
  depends on the sentence.
- [Training and running a
  transformer](../06_the-transformer/03_training-and-running-a-transformer.md)
  explains next-token prediction, the job that gives the table its numbers.
- [Language models](../../07_learned-models/07_language-models/01_overview.md)
  is the catalogue of real language models used on robot arms.
- [Vision-language
  models](../../07_learned-models/07_language-models/02_most-used/02_vision-language-models.md)
  covers models that read a picture and a sentence together, which need both
  this page and the next one.

---

## 8. Using it in Python

Section 1 cut a sentence into eleven tokens, section 3 looked them up in a
table of 429 rows of 6 numbers, section 4 measured two rows against each other,
and section 5 turned a pair of numbers by an angle. The code below does all
four on the exact numbers this page printed, so you can check every value
against the pictures above.

```python
import torch
from torch import nn

# Section 3: the embedding table, as a layer. 429 tokens, 6 numbers each.
table = nn.Embedding(num_embeddings=429, embedding_dim=6)
print(table.weight.shape)                           # torch.Size([429, 6])
print(sum(p.numel() for p in table.parameters()))   # 2574

# Section 1: the tokeniser has already turned the sentence into these numbers.
ids = torch.tensor([[72, 73, 31, 146, 45, 51, 69, 64, 38, 31, 121]])
print(table(ids).shape)                             # torch.Size([1, 11, 6])

# Section 4: cosine similarity, on the rows printed in section 3.
mug   = torch.tensor([-0.50, -0.12,  0.09, -0.03, -0.35,  0.09])
bowl  = torch.tensor([-0.57, -0.12,  0.07, -0.05, -0.38,  0.04])
shelf = torch.tensor([-0.19,  0.04, -0.23, -0.15, -0.03, -0.27])
print(torch.cosine_similarity(mug, bowl,  dim=0))   # tensor(0.9947)
print(torch.cosine_similarity(mug, shelf, dim=0))   # tensor(0.2191)

# Section 5: rotary position embedding, on the first pair of numbers.
def turn(pair, place, rate):
    angle = place * rate
    c, s = torch.cos(angle), torch.sin(angle)
    return torch.stack([pair[0] * c - pair[1] * s, pair[0] * s + pair[1] * c])

pair = mug[:2]
print(turn(pair, torch.tensor(0.0), torch.tensor(1.0)))  # tensor([-0.5000, -0.1200])
print(turn(pair, torch.tensor(3.0), torch.tensor(1.0)))  # tensor([0.5119, 0.0482])
```

The library gives you the table, its random starting values, its gradients and
a lookup that handles a whole batch of sentences at once. It does not give you
the tokeniser, because a tokeniser belongs to a particular model: the
vocabulary, the merge list and the numbering were fixed when that model was
trained, so pairing a trained model with a different tokeniser gives nonsense,
since row 45 would then stand for a different piece of text. In practice you
load the tokeniser that came with the model, which in Hugging Face's
`transformers` package is `AutoTokenizer.from_pretrained(name)`, and you call it
on your text to get the numbers that go into `ids` above.

That same choice settles most of the decisions, because a pretrained model
fixes the vocabulary size, the width of a row and the kind of positional
encoding, and changing any of them means training from scratch. The decision
that stays yours is what you put into the tokeniser, because text unlike
anything it was built from gets chopped into far more tokens than you expect,
and that costs time and context on every call, so it is worth measuring the
token count of the text your robot will really produce rather than assuming it
matches the count of words.
