# What it needs

This page is the bill for this solution. It lists the libraries, the machine,
the data, and the licence of the weights.

## 1. What it needs

It needs **[LeRobot](https://github.com/huggingface/lerobot)**, which holds ACT
and Diffusion Policy, with **PyTorch** underneath. LeRobot uses the Apache-2.0
licence. This solution downloads no weights. Its weights file is trained only on
data made in this project, so it carries nobody else's terms. By contrast,
[SmolVLA as it downloads](../08_a-foundation-model-as-it-downloads/01_what-it-is.md)
and [SmolVLA fine-tuned](../09_the-same-model-fine-tuned-here/01_what-it-is.md)
both carry borrowed weights.

It needs **[geometry generates, a model
ranks](../05_geometry-generates-a-model-ranks/01_what-it-is.md) to work**,
because that solution is the teacher. Without a good teacher there are no good
examples. That is why the teacher was built first.

It needed **two parts the examiner did not have**. The first was a **picture of
the table from straight above**. The examiner gave only numbers. It did render
the world, but from the arm's side, and only for films. The second was **a way
to follow a chunk of waypoints**. `push()` takes a few push numbers and expands
them itself, so a full path had no way in. Both parts are now built, as
[`bench/top_view.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/bench/top_view.py)
and `Bench.follow` in
[`bench/bench.py`](https://github.com/RobinNagpal/robotics-basics/blob/main/code/src/09_pushing-the-glasses-apart/bench/bench.py). Every LeRobot policy expects pictures
and waypoints, so these two parts were the real cost of using LeRobot. [One
fixed nudge](../04_one-fixed-nudge/01_what-it-is.md) and the teacher need
neither.

It needs **examples**, which cost only simulated arm time. They come only from
training tables. Giving extra weight to crowded tables is still a plan, as
[choosing which examples to
keep](03_how-it-works.md#3-choosing-which-demonstrations-to-keep-and-the-bias-it-buys)
explains.

It needs **compute**, and it is the cheapest of the seven to train. **Training
takes hours.** A transformer sounds costly, but three things keep this one
small. The data is small: thousands of pushes, each a picture and a short chunk.
The network is small next to the foundation models in the SmolVLA chapters. And
it learns only this cell's pictures, not vision in general.

**In the end nothing was rented.** This page first budgeted tens of dollars for
a rented accelerator. That is still the right figure for anybody who wants one.
But the network has a few tens of millions of parameters, and the data is a few
thousand small pictures. That fits on the graphics processor of an Apple M4.
Each of the three seeds took 54 to 78 minutes. So all of it was made on the
project's own machine: the examples, three training seeds, and the test run.
Two choices made this possible, and the project's
[`README.md`](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v5-pick-glasses/03-push-glasses-apart/03-imitation-from-demonstrations/README.md#does-it-train-on-this-machine)
records both. First, the
policy reads the picture at half the size the examiner draws it. The vision part
is most of the cost of a training step, so this saves a lot. Second, the example set had to be four
times larger than the first try before the network stopped memorising it.

At run time it needs very little. ACT makes **one forward pass per chunk**.
Diffusion Policy would need several passes per chunk. Both are fast next to a
push, which takes the arm seconds.

Once trained, it needs **a weights file that matches the examiner**. Suppose you
change how the top picture is drawn, or the macro that made the labels, or the
error in the readings. Then the weights file is out of date, and no code test
would notice.

The next page judges this solution and places it beside the other six.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
