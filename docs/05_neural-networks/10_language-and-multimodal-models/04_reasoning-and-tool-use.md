# Reasoning and tool use

The page before this one, [vision-language
models](03_vision-language-models.md), built a model that can look at a camera
picture and answer a question about it in ordinary words. Everything it did
happened in one pass, because the model read the stream once and wrote its answer
straight away. This page is about what you can buy by refusing to do that, and it
answers one question: what happens when the model is allowed to spend more work
at the moment somebody asks, rather than more work during training?

There are two things it can spend that work on, and this page takes them in
order. The first is writing its own working out before the answer, which costs
nothing but tokens and time. The second is calling a program, reading what comes
back, and carrying on, which is how a model gets facts and arithmetic right
instead of guessing at them. Repeating the second one with a goal in mind is what
people mean by an agent, and the last section works out why that machinery
belongs at the planning level of a robot and never inside its control loop.

This page is for a reader who has read [large language
models](01_large-language-models.md) and [post-training a language
model](02_post-training-a-language-model.md), so you already know that a model
writes one token at a time, that it can state something false with a confident
tone, and that training on problems with checkable answers makes it write longer
working out.

The numbers in the pictures come from
`docs/diagrams/language_and_multimodal_2.py`, which prints every one of them. The
accuracy curves, the vote and search curves, the argument checks and the episode
times are simulations of small made-up tasks with the seeds given in the script,
and they are labelled illustrative because that is what they are: they show the
shape of a trade and are not benchmark scores for any model.

## Contents

1. [The working out is tokens, not a separate faculty](#1-the-working-out-is-tokens-not-a-separate-faculty)
2. [What more tokens at answering time buy](#2-what-more-tokens-at-answering-time-buy)
3. [The three shapes of test-time compute](#3-the-three-shapes-of-test-time-compute)
4. [Calling a tool and reading the result](#4-calling-a-tool-and-reading-the-result)
5. [What goes wrong in the loop, and the plain answers](#5-what-goes-wrong-in-the-loop-and-the-plain-answers)
6. [An agent loop, and what it costs](#6-an-agent-loop-and-what-it-costs)
7. [Where this belongs on a robot](#7-where-this-belongs-on-a-robot)
8. [Where to read next](#8-where-to-read-next)
9. [Using it in Python](#9-using-it-in-python)

---

## 1. The working out is tokens, not a separate faculty

**Chain of thought** means letting the model write out the steps of its reasoning
as ordinary tokens before it writes the answer. It is worth being blunt about
what that is, because the name suggests something grander: there is no separate
thinking machinery inside the model, and the working out is a run of tokens
chosen in exactly the way every other token is chosen.

![A stream split into 32 question tokens, 68 working-out tokens and 14 answer tokens, with the five lines of working written out](../../images/language-and-multimodal-models/reasoning-and-tool-use/working-out-stream.svg)

For one small question about a tray of cups, the working out is 68 of the 114
tokens and the answer is only 14.

Read the lines under the bar in the order the model writes them. It works out
that 3 rows of 7 cups is 21 cups, takes away the 4 cracked ones to get 17, says
it needs 17 times 180, splits that into 17 times 18 tens, works 17 times 18 out
as 306, and so gets 3060 grams. Each of those lines is a small step, and each
small step is easier to get right than the whole thing at once, which is the
entire reason the method works.

![Three rows of tokens growing from three to five to seven, each with an empty box asking what comes next](../../images/language-and-multimodal-models/reasoning-and-tool-use/one-token-at-a-time.svg)

Each piece of the working out is produced by the same next-token step that
produces ordinary prose.

The model reads 3 tokens and picks the one that comes next, then reads 5 and
picks again, then reads 7 and picks again, and the step that writes "21" is the
same step that writes "the" in a sentence. Nothing inside the model knows that
these particular tokens are working out rather than prose, which has one
consequence worth holding on to: the only way for a model to spend more effort on
a question is to write more tokens before the answer.

![Two panels: a bar chart of 23 per cent against 83 per cent, and a curve rising with the number of steps written out](../../images/language-and-multimodal-models/reasoning-and-tool-use/written-vs-silent.svg)

In a simulated six-step task, doing every step in one jump gets 23 per cent of
them right, while writing every step out gets 83 per cent right.

The simulation is a chain of six small steps that all have to be right, where a
step the model writes out goes wrong 3 times in 100 and a step it does silently
goes wrong 22 times in 100, and those two rates are the made-up part. Everything
else is measured by running the task 8,000 times. The right panel shows the curve
between the two ends, rising through 43 per cent at three steps written, and it
rises for an unremarkable reason: every step written out is one less step
guessed.

---

## 2. What more tokens at answering time buy

Writing the steps out costs tokens, and tokens cost time, so the natural next
question is what the exchange rate is. Spending work at the moment of the
question rather than during training is called **test-time compute**, where test
time is the old name for the moment a trained model is used.

![A curve of accuracy against tokens written, rising steeply to 83 per cent at 124 tokens and then flattening to 90 per cent at 334](../../images/language-and-multimodal-models/reasoning-and-tool-use/accuracy-vs-tokens.svg)

Accuracy on the simulated task climbs from 23 per cent at 40 tokens to 83 per
cent at 124, and then another 210 tokens buy only 7 more points.

The solid part of the curve is the model writing more of its six steps, at 14
tokens a step, and it runs 40, 54, 68, 82, 96, 110 and 124 tokens for 23, 29, 35,
43, 55, 67 and 83 per cent. The dashed part is the model reading its own working
back afterwards, where each reading pass costs 70 tokens and catches each mistake
already made about three times in ten, and it runs 194, 264 and 334 tokens for
87, 89 and 90 per cent. The flattening is the honest part of the picture, because
it is what you actually get when you let a model think for longer and longer.

![A straight line of seconds against tokens, from 1.35 seconds at 40 tokens to 8.70 seconds at 334](../../images/language-and-multimodal-models/reasoning-and-tool-use/time-vs-tokens.svg)

At a writing rate of 40 tokens a second with 0.35 seconds before the first one,
the shortest answer takes 1.35 seconds and the longest takes 8.70.

The time is a straight line because the model writes its tokens one after
another, so the seconds are the token count divided by the rate plus the fixed
wait at the start. The rate and the wait are stated assumptions, but the shape
does not depend on them, since whatever the rate, six and a half times the tokens
is six and a half times the writing.

![Two panels: accuracy against seconds flattening after about 3.5 seconds, and bars of the accuracy gained per second spent](../../images/language-and-multimodal-models/reasoning-and-tool-use/accuracy-per-second.svg)

The steepest stretch of the trade runs from 110 to 124 tokens, worth 43 more
tasks right per second spent, after which the last stretch is worth 0.6.

Putting the two together gives the picture that matters when you are deciding how
long to let a model think. Early seconds are cheap and buy a great deal, and
later seconds buy almost nothing, so the question is never whether to let the
model think but how long to let it. On a robot that answer is usually set by the
operator's patience rather than by the curve, and section 7 explains why the
curve cannot be allowed to set it.

---

## 3. The three shapes of test-time compute

Writing longer working out is only one way of spending more at answering time,
and there are two others in common use. The second is to answer the same question
several times over and keep the answer that came up most often, and the third is
to grow several partial answers at once and throw away the ones that look worst.

![A curve of accuracy after a vote, rising from 44 per cent with one attempt to 85 per cent with fifteen](../../images/language-and-multimodal-models/reasoning-and-tool-use/vote-curve.svg)

In the simulation, one attempt gets 44 per cent right, three attempts with a vote
get 53 per cent, five get 61 per cent and fifteen get 85 per cent.

The simulation takes an attempt that is right 43 times in 100, and when it is
wrong it lands on one of six wrong answers, one of which is the easy mistake and
takes 35 of every 100 wrong attempts. Voting works because the right answer is
the single most likely one while the wrong answers are spread out, so with enough
attempts the right one wins the count. Notice the condition hidden in that
sentence: if the easy mistake were more likely than the right answer, voting
would make matters worse, and no number of attempts would help.

![Two panels: tokens rising in a straight line from 82 to 1,230 with the number of attempts, and accuracy rising much more slowly](../../images/language-and-multimodal-models/reasoning-and-tool-use/vote-cost.svg)

Fifteen attempts cost 1,230 tokens against 82 for one, and buy 42 more tasks
right in every hundred.

The cost of a vote is the plainest cost in this chapter, because every attempt is
paid for in full. One thing softens it, which is that the attempts do not depend
on each other and can be written at the same time on different machines, so the
seconds need not rise with the tokens even though the bill does.

![A tree of partial answers with the judge's score written on each, and the two kept at each step outlined](../../images/language-and-multimodal-models/reasoning-and-tool-use/search-tree.svg)

In the search, each step makes three new partial answers from each kept one, a
judge scores them all, and only the best two go forward.

Follow the tree down. One partial answer becomes three, the judge scores each,
the best two are kept, those two become six, and so on. The judge gives a partial
answer still on the right path a true score of 1 and every other a 0, then adds
noise with a spread of 0.7, which is what makes it imperfect, and the red
outlines mark the ones that really were on the right path. At the second step a
partial answer on the right path scores -0.62 and is thrown away, which is the
whole difficulty of search.

![Two panels: the share of runs that find the answer rising from 31 to 69 per cent with beam width, and tokens rising from 360 to 1,980](../../images/language-and-multimodal-models/reasoning-and-tool-use/search-curve.svg)

Keeping one partial answer finds the right one 31 times in 100 for 12 partial
answers written, while keeping nine finds it 69 times in 100 for 66.

A wider beam survives the noisy judge more often because it has to be unlucky
more times to lose the right path altogether, and the price is a straight line of
tokens. Search is the most expensive of the three shapes and the only one that
needs a judge, so it is reached for last, and usually only when the answer has
clear steps that can be scored on their own.

---

## 4. Calling a tool and reading the result

All three of those shapes make the model work harder at the same thing, which is
guessing. The next idea is different, because it stops the model guessing at all:
a **tool call** is a structured piece of text the model writes, which a program
outside the model recognises, runs, and answers by appending the result to the
same stream of tokens.

![A four-station loop with the worked example beside it: three calls and three results, ending with 3060](../../images/language-and-multimodal-models/reasoning-and-tool-use/tool-loop.svg)

One turn of the loop has four stations, and the question about the cups took
three turns of it.

Go round the loop once. The model writes tokens that happen to spell a call and
then stops, the program checks that the call names a real tool with allowed
arguments, the program runs it, and the result is appended to the stream as plain
tokens. Then the model is asked to continue, and from its point of view the
result was simply the next thing in the conversation. In the example it counts
the cups and gets 21 back, counts the cracked ones and gets 4 back, asks a
calculator for (21 - 4) * 180 and gets 3060 back, and then writes the answer. The
model never multiplied anything and never counted anything, so neither of those
could come out wrong.

![Two panels: the tokens each part of the loop adds, and a step chart of the stream growing to 169 tokens](../../images/language-and-multimodal-models/reasoning-and-tool-use/tool-transcript.svg)

The three turns take the stream from 47 tokens to 169, with the calls costing 23,
31 and 29 tokens and each result costing 7.

The step chart carries the cost that people forget. The results are tiny, but the
stream only ever grows, and the model reads the whole of it again on every turn,
so a loop that runs for twenty turns is reading a long stream twenty times. That
is why the number of turns is the thing to watch rather than the size of any one
result.

![Two lines against the number of digits: multiplying by hand falls from 88 per cent to 0, while the calculator stays at 100](../../images/language-and-multimodal-models/reasoning-and-tool-use/tool-vs-no-tool.svg)

A simulated model multiplying by hand gets 88 per cent of one-digit problems
right, 33 per cent of three-digit ones and 1 per cent of six-digit ones, while a
calculator gets all of them right.

The simulation assumes the model writes each digit step wrong 6 times in 100 and
that a problem of d digits by d digits needs about 2 d squared steps, so the
chance of surviving all of them falls fast. The point the picture makes is not
that the tool is cleverer, because a calculator knows nothing; it is that the job
has been taken away from the part of the system that is bad at it and given to a
part that cannot get it wrong.

![A stacked bar of one turn at 1.21 seconds, and bars of the total rising to 7.2 seconds over six turns](../../images/language-and-multimodal-models/reasoning-and-tool-use/tool-cost.svg)

One turn takes 1.21 seconds, made of 0.35 waiting, 0.57 writing the call, 0.22
running the tool and 0.06 reading the result, so three turns take 3.62 seconds.

The seconds here are stated assumptions, and the reason to look at them anyway is
the shape: the fixed wait before the first token is paid again on every single
turn, so the turn count multiplies a cost that has nothing to do with how much
work the tool did. That is the arithmetic behind everything in section 7.

---

## 5. What goes wrong in the loop, and the plain answers

The loop as described assumes the model writes a sensible call, that the tool
works, and that the loop ends. None of the three is safe, and the answers to all
three are ordinary engineering rather than anything to do with models.

![A funnel of 400 simulated calls, with 29, 41, 18 and 10 thrown out and 302 run](../../images/language-and-multimodal-models/reasoning-and-tool-use/argument-check.svg)

Of 400 simulated calls, 98 are thrown out before anything moves: 29 name a tool
that does not exist, 41 use a class outside the allowed list, 18 put a number
outside its range and 10 leave out a required argument.

The four rates behind that draw are made up and the counts are what the draw
gave, but the lesson does not depend on them. The model writes a call as text, so
it can write anything, including a tool you never had and a class name it
invented, and the only thing between that text and a moving arm is a check
written against the tool's own written shape. That check is a few lines long, it
runs before anything happens, and when it fails the right thing to do is hand the
error back to the model as an ordinary result, because the model will usually fix
the call and try again.

![A histogram of turns per episode with a cap at 8 marked, and bars of the average turns with and without the cap](../../images/language-and-multimodal-models/reasoning-and-tool-use/turn-cap.svg)

In 3,000 simulated episodes the average is 3.86 turns, 8.8 in every 100 run past
8 turns, and the longest ran to the hard limit of 40.

The simulation finishes a job on any turn with a chance of 35 in 100, but on any
turn it may fall into a state where it keeps asking the same thing, after which
its chance of finishing drops to 10 in 100. That is what a stuck loop looks like
from outside: not a crash, but a model politely asking the same question with
slightly different words until somebody stops it. Capping the turns at 8 brings
the average down from 3.86 to 3.05, and more importantly it bounds the worst case
instead of leaving it open.

![A histogram of episode times with a long tail, marked at the median of 6.0 seconds, the 95th percentile of 34.5 and a timeout at 30](../../images/language-and-multimodal-models/reasoning-and-tool-use/wall-clock.svg)

Half the simulated episodes finish inside 6.0 seconds, one in twenty takes more
than 34.5, the slowest took 112.9, and a 30 second timeout cuts off 6.2 per cent
of them.

A turn cap is not enough on its own, because a tool can be slow even when the
turn count is small, so the whole thing is given a deadline as well. The tail in
that picture is the reason: the average episode time of 10.4 seconds describes
almost none of the episodes, and a system sized for the average will be late far
more often than it is designed to be.

![A table of three failures, what each looks like and the plain engineering answer to each](../../images/language-and-multimodal-models/reasoning-and-tool-use/three-guards.svg)

Three guards cover the three failures: check the arguments, return a tool's
failure as an ordinary result, and stop after 8 turns or 30 seconds whichever
comes first.

None of the three guards is clever, and that is the point. They are exactly the
guards any program gets when it calls out to something it does not control, and
the only unusual thing about this case is that the caller is a model that can
write any text at all, which makes the first guard more necessary than usual
rather than different in kind.

---

## 6. An agent loop, and what it costs

An **agent loop** is the loop of section 4 run with a goal that outlives one turn,
so instead of answering one question the model keeps going until the goal is met
or a guard stops it. Nothing new is added to the model, and everything that is
added lives in the program around it.

![A four-station loop of look, decide, act and check, with a goal fed in and an exit for done or out of turns](../../images/language-and-multimodal-models/reasoning-and-tool-use/agent-loop.svg)

The goal is written once, and then the model looks, decides on one tool call,
the program acts, and the result is checked against the goal.

The one thing to understand about this loop is that the model has no memory
between turns except the stream itself, so the goal, every call it has made and
every result it has read all stay in the stream and are read again from the
beginning on every turn. That is what makes the loop simple to write, because
there is no state to manage, and it is also what makes it expensive to run.

![A stacked bar chart of five turns, totalling 12.93 seconds, with the longest turn at 4.09](../../images/language-and-multimodal-models/reasoning-and-tool-use/latency-stack.svg)

One simulated episode of five turns takes 12.93 seconds, and the longest single
turn takes 4.09 of them.

Look at where the seconds go in each bar. The grey part at the bottom of every
turn is the fixed wait before the first token, which is paid five times in this
episode and would be paid twenty times in a longer one. The tool time varies a
great deal between turns, because some tools answer at once and some do real
work, and that variation is what the next picture is about.

![A box plot of episode times on a log scale beside a curve of the time by percentile, rising sharply after 85 per cent](../../images/language-and-multimodal-models/reasoning-and-tool-use/time-spread.svg)

Half the episodes finish inside 6.0 seconds, one in twenty takes over 34.5, and
the slowest takes 112.9, which is 19 times the middle.

That spread is the real cost of an agent loop, and it is a worse problem than the
average time. A part of a system that usually takes 6 seconds and occasionally
takes 113 cannot be given a job that anything else is waiting on, unless whatever
waits can carry on safely without it. Section 7 turns that sentence into a line
drawn through a robot.

---

## 7. Where this belongs on a robot

Everything on this page costs seconds, and a robot arm is run by a loop that
costs milliseconds, so the two cannot be the same loop. This section says exactly
where the line between them sits.

![A time axis of 6 seconds, with one agent turn across the top, 59 policy steps below it and 2,979 control steps below that](../../images/language-and-multimodal-models/reasoning-and-tool-use/two-rates.svg)

In the median simulated agent loop of 6.0 seconds, a 500 hertz joint controller
runs 2,979 times and a 10 hertz movement policy runs 59 times.

The hertz is the ordinary unit for how many times a second something happens, so
500 hertz means the controller reads the encoders, works out the next current and
writes it 500 times a second. Put the two on one axis and the question answers
itself: the controller has taken nearly three thousand decisions in the time the
agent took one, and no arm can stand still for 6 seconds waiting to be told what
to do next.

![A log-scale bar chart of six parts, from a 2 millisecond control cycle to a 5,959 millisecond agent loop](../../images/language-and-multimodal-models/reasoning-and-tool-use/rate-ladder.svg)

One run takes 2 milliseconds for the joint controller, 25 for one model token, 33
for the detector, 100 for the movement policy, 1,850 for one vision-language
answer and 5,959 for one agent loop.

That ladder covers four orders of magnitude, which means the slowest thing on it
takes about three thousand times as long as the fastest. The three fastest rungs
are things a robot can put inside a loop that keeps the arm moving, and the three
slowest are things it cannot, and there is a clear gap between the two groups
rather than a gradual slope.

![One 2 millisecond control cycle divided into four parts, beside bars comparing it with one model token and one short answer](../../images/language-and-multimodal-models/reasoning-and-tool-use/cycle-budget.svg)

One control cycle is 2 milliseconds, one model token is 25 milliseconds, which is
12 cycles, and one short answer of 60 tokens is 1,850 milliseconds, or 925
cycles.

Read the left bar as a budget that has to balance every single cycle: a fifth of
a millisecond to read the encoders, a little over half to work out the next
current, a quarter to write it to the drivers, and a millisecond spare for safety
checks. Now set one model token beside it. A single token takes twelve whole
cycles, so the model cannot produce even one token inside a cycle, which settles
the matter: this machinery is not slow for a control loop, it is in a different
world from one.

![A red line with four slow parts above it and four fast parts below it, and two arrows showing a goal going down and a result coming up](../../images/language-and-multimodal-models/reasoning-and-tool-use/boundary.svg)

Above the line sit the agent loop at about 6 seconds a turn, the vision-language
model at about 2 seconds an answer, a planner at tens of milliseconds and the
operator; below it sit the movement policy at 10 a second, the detector at 30, the
joint controller at 500 and the hardware safety stop.

Only two things cross that line. Downwards goes a goal in words, such as which
object to pick or which tray to clear, and nothing else; upwards comes a report
of whether it worked and what was seen. Above the line nothing has a deadline, so
a slow answer only makes the robot wait with the arm held still or parked; below
the line everything has a deadline, and a missed one is a dropped cup or a fault.
That is why no model that writes tokens may ever sit inside the control loop,
however good its answers are, and why the policies in [models that
act](../12_models-that-act/03_vision-language-action-models.md) are built to run
at a fixed rate with no loop around them.

---

## 8. Where to read next

- [Reinforcement learning](../11_learning-from-outcomes/01_reinforcement-learning.md)
  is the next page, and it explains learning by trying something and seeing how
  it turned out, which is where the training behind long working out comes from.
- [Rewards, preferences and verifiers](../11_learning-from-outcomes/02_rewards-preferences-and-verifiers.md)
  explains where the checkable answer comes from that makes a reasoning model
  worth training in the first place.
- [Post-training a language model](02_post-training-a-language-model.md) is worth
  rereading once you have seen section 1, because it explains the training that
  makes a model write its working out without being asked.
- [Vision-language-action models](../12_models-that-act/03_vision-language-action-models.md)
  is what sits below the line in section 7, and it runs at a fixed rate with no
  loop around it.
- [Running and evaluating a model](../14_using-a-model-for-real/01_running-and-evaluating-a-model.md)
  takes the latency budget of section 7 seriously and shows how it is measured on
  a real machine.
- [Language models as planners](../../07_learned-models/07_language-models/03_also-used/01_language-models-as-planners.md)
  is the catalogue page for this machinery on an arm, with the real models and
  what they cost.

---

## 9. Using it in Python

Sections 4 and 5 described the loop and its three guards, and no library hides
that loop from you, because the program that runs the tools is yours. So this
code is the loop itself, with a stubbed model that writes the three calls from
section 4, and it prints the token counts the page quoted.

```python
import json, re, time

TOOLS = {"count_objects": {"class": ["cup", "bottle", "tray"]},
         "calculator": {"expression": str}}          # section 5: the written shape
MAX_TURNS, TIMEOUT = 8, 30.0                         # section 5: the two stops

def toks(text):                                      # section 4: a rough token count
    return len(re.findall(r"[A-Za-z0-9_.]+|[^\sA-Za-z0-9_]", text))

def run_tool(name, args):                            # section 4: station 3
    if name == "count_objects":
        return {"count": 4 if args.get("condition") == "cracked" else 21}
    return {"value": eval(args["expression"], {"__builtins__": {}})}

SCRIPT = ['{"tool": "count_objects", "arguments": {"class": "cup"}}',
          '{"tool": "count_objects", "arguments": {"class": "cup", "condition": "cracked"}}',
          '{"tool": "calculator", "arguments": {"expression": "(21 - 4) * 180"}}']

stream = ("You may call count_objects(class, condition) and calculator(expression). "
          "Write one call at a time and wait for its result. "
          "How many good cups are on the tray, and what do they weigh if one cup "
          "is 180 grams?")
total, started = toks(stream), time.monotonic()
for turn in range(MAX_TURNS):                        # section 6: the loop
    if turn >= len(SCRIPT) or time.monotonic() - started > TIMEOUT:
        break
    call = SCRIPT[turn]
    total += toks(call)
    asked = json.loads(call)
    if asked["tool"] not in TOOLS:                   # section 5: guard one
        result = {"error": "no such tool"}
    else:
        result = run_tool(asked["tool"], asked["arguments"])
    back = json.dumps(result, separators=(", ", ": "))
    total += toks(back)
    print(turn + 1, toks(call), back, toks(back), total)

total += toks("There are 17 good cups on the tray and they weigh 3060 grams, "
              "which is 3.06 kilograms.")
print("tokens in the whole stream:", total)          # 169
```

Running it prints 23 and 7 on the first turn, 31 and 7 on the second, 29 and 7 on
the third, and 169 at the end, which are section 4's counts. The calculator
really does work (21 - 4) * 180 out and gets 3060, which is the number the model
in the picture quotes.

What a library gives you is the part this code stubs out. Hugging Face's
`transformers` package takes a list of tool descriptions and a conversation and
writes them into the exact format a given model was trained to read, through
`apply_chat_template`, and it parses the model's reply back into a tool name and
a dictionary of arguments. Hosted models do the same thing behind their own
interfaces. None of them runs your tools, keeps your stream or stops your loop.

What you still have to decide is every number in sections 5 and 7. You choose how
many turns and how many seconds the loop may have, and section 5 showed the tail
is long enough that both are needed; you choose what the arguments are allowed to
be, which is the cheapest safety you will ever write; and you choose which side
of section 7's line each part of your robot sits on, which is the decision that
makes everything else either safe or impossible.
