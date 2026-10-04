# Reinforcement learning policies

The four pages before this one all assumed that a person can do the task,
because a copying policy has nothing to learn from otherwise. So this page
answers one question: how can a robot arm learn a movement that nobody can show
it, by trying again and again and being told how well each try went? That way of
learning is called reinforcement learning, and the model it produces is a
reinforcement learning policy.

The page is for a reader who has read
[how a model learns](../../01_what-models-are/02_how-a-model-learns.md) and, ideally,
[behaviour cloning](../02_most-used/01_behaviour-cloning.md). Behaviour cloning
copies a person, whereas reinforcement learning does not need a person to do the
task at all, because it needs a way to score each attempt instead. Every new word is
explained where it first appears.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models and methods](#5-well-known-models-and-methods)
6. [A worked example: pushing a peg into a hole](#6-a-worked-example-pushing-a-peg-into-a-hole)
7. [What goes wrong, and what people do about it](#7-what-goes-wrong-and-what-people-do-about-it)
8. [Why this kind, and what it costs](#8-why-this-kind-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

The introduction said that the arm learns by trying, so here is that idea in one
sentence. The arm tries a movement, a program gives the attempt a score, and the
model is changed a little, so that high-scoring movements become more likely
next time.

The score is called the **reward**, and it is a number that a person writes a
rule for, such as "1 if the peg is in the hole, 0 if it is not". The model that
picks the movements is called the **policy**, as it is on every page in this
chapter. The process of trying, scoring and adjusting, over and over, is called
**reinforcement learning**, which is often shortened to RL. The word
"reinforcement" means that actions which led to a good score are made stronger.

For example, think of a child learning to throw a ball into a bin, where nobody
explains the angle of the arm or the force of the throw. The child throws, sees
whether the ball went in, and throws again a little differently. So after many
throws the child is good at it, and the child needed only one piece of
information each time, which was in or out.

Reinforcement learning works the same way, but with two differences. It needs
far more tries than a child does, often millions of them. And the rule for the
score has to be written down exactly, because the computer follows it exactly.

![Three attempts at pushing a peg into a hole, each with a reward number](../../../images/movement-models/reinforcement-learning-policies/try-score-adjust.svg)

So the picture shows three attempts from early, middle and late in training. The
first
attempt misses and scores low, while the last one puts the peg in the hole and
scores
1.0. Those numbers are an example of a reward rule, and not a measurement.

---

## 2. What goes in and what comes out

Section 1 introduced the reward, so this section shows where it sits among the
other numbers. A reinforcement learning policy for an arm takes in a description
of the current moment, which is called the **observation**, and for an arm it
can include:

- the joint angles and how fast each joint is turning
- the position of the gripper
- readings from a force sensor at the wrist, which measure how hard the arm is
  pushing on something
- sometimes camera pictures, although many policies use simple numbers instead,
  because pictures make learning much slower

Then it gives back one **action**, which is a small movement command for the
next moment, such as "move the gripper 2 mm down and 1 mm left". The policy is
asked again many times a second, so the arm moves in many small steps.

The table below shows one concrete example of all of these. Read each row as one
input or output of the policy.

| | What it is | An example for pushing a peg into a hole |
| --- | --- | --- |
| In | joint angles and speeds | six angles and six speeds |
| In | gripper position | where the peg tip is, in millimetres |
| In | force at the wrist | how hard the peg presses on the block, and in which direction |
| Out | an action | a small push: 2 mm down and 1 mm left, repeated many times a second |
| Used only in training | the reward | 1.0 when the peg is fully in, less when it is close |

Notice that the reward is not an input to the finished policy. It is only used
while training, to decide how to change the policy.

---

## 3. How it works inside

Section 2 said what goes in and out, and this section says what sits between them.
Inside, the policy is usually a small neural network. A **neural network** is a
calculation with many adjustable numbers, and Chapter 1 explains it in
[inside a neural network](../../01_what-models-are/03_inside-a-neural-network.md).
For a task that uses simple numbers as input, the network can be small, with only a
few layers.

So what makes reinforcement learning different is not the network. It is the
loop around the network during training, and here is that loop.

1. The arm, which is usually a simulated one, starts in some position.
2. The policy looks at the observation and picks an action. While learning, it adds
   a little randomness, so that it sometimes tries something new, and this is called
   **exploration**.
3. The arm makes that movement, and the simulation works out what happened.
4. The program computes the reward for what happened.
5. This repeats until the attempt ends, either because the peg goes in or because
   time runs out, and one whole attempt is called an **episode**.
6. After many episodes, a learning method looks at which actions came before high
   rewards and which came before low ones. Then it changes the network's numbers, so
   that the good actions become more likely.
7. Back to step 1, with the slightly better policy.

Many methods also train a second network, called a **critic** or a **value
function**, which learns to guess how much reward is still to come from the
current moment. This helps, because the real reward often arrives only at the
very end, so the critic lets the learner tell early on whether things are going
well.

One difficulty in that loop is important enough to need a name. When the reward
only arrives at the end, the learner has to work out which of hundreds of small
actions deserved the credit. This is called the **credit assignment problem**,
and it is one reason reinforcement learning needs so many tries.

---

## 4. How it is trained

Section 3 described a loop that runs many times, and this section says where
those runs happen. Reinforcement learning makes its own data by trying things,
so it does not need recorded demonstrations. But it needs a very large number of
tries, often in the millions. A real arm cannot do millions of tries, because it
would take years, and it would wear out or break things. So almost all
reinforcement learning for arms happens in a **simulator**, which is a program
that works out how a virtual arm and virtual objects move and bump into each
other. A simulator can run thousands of virtual arms at once, much faster than
real time, on a graphics card.

But this creates a new problem, because the simulator is never exactly like the
real world. Friction, weight, springiness and camera pictures are all a little
wrong, so a policy that learned in the simulator can fail on the real arm, and
this gap is called the **sim-to-real gap**.

The most common fix for that gap is called **domain randomisation**. Instead of
building one very accurate simulated world, you train in thousands of slightly
different ones. Each one has a different table colour, different lighting, a
different friction, a slightly different mug size, or a camera in a slightly
different place. The policy has to work in all of them, so the real world is,
with luck, just one more variation it has already met.

![Six randomised simulated tables, then the real table](../../../images/movement-models/reinforcement-learning-policies/many-simulated-worlds.svg)

The picture shows six of the randomised training worlds on the left, each with
one thing changed, and the real table on the right.

But there are two other ways to get the practice.

- **Offline reinforcement learning** learns from a fixed pile of recorded attempts,
  without practising at all.
- **Real-world reinforcement learning** practises on the real arm, but only for a
  short time. It usually starts from a policy that already works a little, which is
  often one trained by copying. A person watches and can take over when the arm goes
  wrong, and those corrections help the learning.

The second of these is where much of the useful work happens in 2026, and the
[learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#2-learning-from-trial-and-error)
describes the evidence.

---

## 5. Well-known models and methods

The pages before this one each end with a shelf of models you can download. This
page cannot, and saying so plainly is the most useful thing in it. Reinforcement
learning is the one method in this chapter where you train rather than download,
because a finished policy belongs to one reward rule, one simulated world and one
robot, so nobody publishes it for you to pick up. The names worth knowing are
therefore the learning methods and the libraries that implement them, and the rest of
this section helps you choose one of each.

Read the table as a shortlist of choices rather than of products. These are methods,
so the column that would hold a model's size instead holds the amount of practice the
method needs, which is the cost that decides most projects. The licence column is the
licence of the code you would actually run, read from that project's own licence
file, because a method itself has no licence.

| Name | What it is | Best at | Practice it needs | Licence of the code you run | Pick it when |
| --- | --- | --- | --- | --- | --- |
| PPO | an algorithm, 2017 | a simulator running many arms at once | millions of steps | MIT, in Stable-Baselines3 | you can simulate the task and score it |
| SAC | an algorithm, 2018 | learning from as few attempts as possible | far fewer steps, by replaying a store of past ones | MIT, in Stable-Baselines3 | every attempt costs real time |
| HIL-SERL | a system you can run, 2024 | improving a half-working policy on the real arm | one to two and a half hours of real practice | Apache-2.0, and it ships inside LeRobot | you have the arm, and a person to watch it |
| Recap, in π*0.6 | a method, not released, 2025 | polishing a large pretrained policy | not stated | no code or weights released | never today, but follow it |
| Offline: IQL and CQL | algorithms | learning from recordings without practising | none at all | not checked | almost never now, see 5.5 |
| The landmark systems | published results, 2018 to 2023 | showing what the method has achieved | weeks of real collection, or none | various | you are reading rather than building |

### 5.1 PPO, for practising in a simulator

**Most used in 2026** when the practice happens in a simulator, because it stays
stable while thousands of simulated arms practise at once.

PPO stands for Proximal Policy Optimization, and OpenAI published it in July 2017 in
[Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347). It
collects a batch of attempts with the current policy, works out which actions did
better than the policy expected, and then moves the policy towards those actions.
The part that gives it its name is a limit on how far the policy may move in one
update. That limit is why a PPO run of many hours rarely falls apart.

Pick PPO rather than SAC in the next sub-section when attempts are cheap. PPO throws
each batch of experience away once it has learned from it, which sounds wasteful and
is the right trade in a simulator that runs a thousand arms side by side on a
graphics card. There, attempts cost almost nothing and what you want is a run that
does not collapse overnight.

What it costs you is practice, and more of it than anything else on this page.
Millions of steps is normal, so PPO is only sensible where a simulator can produce
them. The hardware question is which simulator you can run.
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) (BSD-3) and
[MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground) (Apache-2.0)
are where large-scale practice happens, and both want an NVIDIA card, so on an Apple
Silicon Mac you are limited to plain MuJoCo on the processor and to small tasks. Note
also that Isaac Gym, the simulator behind a great many older papers, is officially no
longer supported, and Isaac Lab replaced it, so a tutorial built on Isaac Gym is out
of date. What most often goes wrong is not the algorithm but the reward, which
section 7 describes.

The library for the algorithm itself is
[Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3), which is MIT and
installs with `pip install "stable-baselines3[extra]"`. The code below trains on
sixteen copies of a simulated pushing task from
[panda-gym](https://github.com/qgallouedec/panda-gym) (MIT,
`pip install panda-gym`).

```python
import panda_gym                       # registers the Panda tasks with gymnasium
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# Sixteen copies of the task in one process. PPO learns from all of them together,
# which is the whole reason it suits a simulator.
env = make_vec_env("PandaPush-v3", n_envs=16)

# MultiInputPolicy because this task's observation is a dictionary, holding the
# arm's state, the object's position and the goal separately.
model = PPO("MultiInputPolicy", env, n_steps=2048, batch_size=64, verbose=1)
model.learn(total_timesteps=2_000_000)
model.save("ppo_panda_push")
```

Stable-Baselines3 gives you the algorithm. `n_steps=2048` and `batch_size=64` are its
own defaults for PPO, and with sixteen copies of the task each update learns from
32,768 steps of experience. What panda-gym gives you is the simulated arm, built on
the PyBullet physics engine, the task and, most importantly, the reward. On your own
task you write that reward yourself, and section 7 explains why that is where the
difficulty actually lives. For a wider set of manipulation tasks,
[robosuite](https://github.com/ARISE-Initiative/robosuite) (MIT) provides them on
MuJoCo instead, and it runs on Apple Silicon because MuJoCo does.

### 5.2 SAC, for when every attempt is expensive

**Most used in 2026** when attempts are expensive, because it reuses old attempts
instead of throwing them away.

SAC stands for Soft Actor-Critic, and researchers at the University of California,
Berkeley published it in January 2018 in [Soft Actor-Critic: Off-Policy Maximum
Entropy Deep Reinforcement Learning with a Stochastic
Actor](https://arxiv.org/abs/1801.01290). It keeps the attempts it has made in a
store called a **replay buffer** and trains on random samples drawn from that store,
so one real movement teaches the policy many times over. It also adds a term that
pays the policy for keeping some randomness, which stops it settling early on the
first thing that half worked.

Pick SAC rather than PPO when you count your attempts. The numbers in
Stable-Baselines3 say the difference plainly: SAC's replay buffer holds 1,000,000
past steps by default and it trains on a batch of 256 of them after every single step
the robot takes, where PPO waits for 2,048 fresh steps and then discards them. That
is why SAC is the usual choice on a real arm, or in a simulator too slow to run many
copies.

What it costs you is complexity and memory. SAC trains two networks that score
actions, a third that chooses them, a slowly updated copy for stability, and the
randomness term, and each of those has details that quietly ruin a run when they are
wrong. Getting a tested implementation is the real value of the library here. The
buffer costs memory too, and a million camera pictures will not fit in a laptop's
memory, which is one reason these policies often take plain numbers as input rather
than pictures, as section 2 said.

The library is Stable-Baselines3 again, and the simulated arm below is panda-gym.

```python
import gymnasium as gym
import panda_gym
from stable_baselines3 import SAC

env = gym.make("PandaPickAndPlace-v3")
model = SAC("MultiInputPolicy", env, buffer_size=1_000_000, batch_size=256, verbose=1)
model.learn(total_timesteps=500_000)
model.save("sac_panda_pick_and_place")

observation, info = env.reset()
# deterministic=True switches off the exploring randomness, so the trained
# policy does its best instead of trying something new.
action, _ = model.predict(observation, deterministic=True)
observation, reward, terminated, truncated, info = env.step(action)
```

Look at `total_timesteps=500_000` before you believe this is cheap. If the arm
decides twenty times a second, half a million steps is about seven hours of
continuous motion, and on a real arm it is far more, because somebody has to put the
object back after every attempt. What you have to supply for your own robot is a
simulator of that arm, accurate enough to train against, plus the randomisation of
section 4 and usually a short spell of real practice at the end. That last step is
the subject of the next sub-section.

### 5.3 HIL-SERL, for learning on the real arm

**Most used in 2026** for work on a real arm, and the one entry on this page whose
published numbers are strong enough to plan around.

HIL-SERL stands for Human-in-the-Loop Sample-Efficient Robot Learning, and it came
from the University of California, Berkeley in 2024
([project page](https://hil-serl.github.io/),
[repository](https://github.com/rail-berkeley/hil-serl)). It starts from a small set
of human demonstrations, trains a classifier from them so that the robot can score
its own attempts, and then runs SAC on the real arm while a person watches with a
gamepad and takes over when things go wrong. Those take-overs are the learning
signal rather than merely extra data.

Pick it rather than training in simulation with PPO because it removes the simulator,
which section 4 named as the hardest part to get right. The published result is the
reason to take it seriously. HIL-SERL reached 100 per cent success on every task it
was tried on, after between one and two and a half hours of training on the real
robot, on tasks including seating memory in a motherboard, inserting an SSD and a USB
connector, clipping a cable, fitting a timing belt and assembling IKEA panels, where
the strongest copying baseline on the same tasks averaged under 50 per cent. That was
peer-reviewed in *Science Robotics*, which is worth saying in a field where most
strong numbers are published by the company that produced them.

What it costs you is several hours of a person's time and a prepared robot. Somebody
has to sit with the arm throughout, holding the gamepad. You also need force and
speed limits underneath the policy, a way to put the task back to its starting state
between attempts, and a reward classifier you trust, and the
[learned methods document](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#12-interactive-imitation-correcting-it-as-it-goes)
gives the evidence and the practical requirements. One other thing to know: its
predecessor SERL is formally deprecated in favour of it, so ignore any tutorial built
on SERL.

The original repository is Apache-2.0, read from its licence file, but the version to
use is the one inside [LeRobot](https://github.com/huggingface/lerobot), documented
as [its reinforcement learning
workflow](https://huggingface.co/docs/lerobot/hilserl). It runs as two processes.

```bash
# The learner holds the policy and does the SAC updates.
python -m lerobot.rl.learner --config_path train_config_hilserl_so100.json

# The actor, in a second terminal, drives the arm and sends its experience back.
python -m lerobot.rl.actor --config_path train_config_hilserl_so100.json
```

LeRobot gives you the actor-and-learner split, the SAC implementation underneath it
and the gamepad handling. What you supply is that JSON file and the robot. The file
names your arm, your cameras, the reward classifier and an `algorithm` block whose
`type` is `sac`. Before either command runs you record the demonstrations and train
the classifier, which LeRobot does with its own commands. To walk through the whole
workflow without any hardware, the [gym_hil](https://github.com/huggingface/gym-hil)
package gives you a simulated Franka arm with gamepad take-overs, in tasks such as
`PandaPickCubeGamepad-v0`.

### 5.4 Practice on top of a pretrained policy

**Worth betting on**, because the field has largely stopped training policies from
nothing, and this is what it does with reinforcement learning instead.

The idea is to train a large policy by copying demonstrations, and then let it
practise and be corrected rather than collecting more demonstrations. The clearest
published instance is π*0.6 from Physical Intelligence, published on 17 November
2025. Its method is called Recap, and it has three stages: ordinary demonstrations
first, then a person taking over when the robot starts to go wrong, then the robot
practising alone. The technical difficulty is knowing which earlier action caused a
failure that only showed up much later, which is the credit assignment problem from
section 3, and Recap handles it by training a value function that scores how good
each situation is. The change in that score from one moment to the next says whether
the action in between helped.

Bet on this rather than on training from scratch because it fixes the thing that
copying cannot fix. Demonstrations show what success looks like and never show how to
recover from the particular mistakes that your policy makes. It is also where the
field's attention has gone, since training a reinforcement learning policy from
scratch is now the exception rather than the rule, and this repository's frontier
chapter calls demonstrate-then-polish the most important arrival of the year.

What it costs you today is that you cannot have it, because none of it is released,
neither the code nor the weights. The figures that exist come from the company
itself, and its per-task numbers appear only as bar charts rather than in the text,
so read them as a direction and not as a measurement. Its authors also name the limit
themselves, which is that the corrections are only as good as a person's judgement
about when to step in, and that works for obvious mistakes and not for subtle ones. So there is no code to show here,
and the nearest thing you can actually run is HIL-SERL in 5.3, which is the open
version of the human-take-over stage. The
[frontier chapter on foundation models](../../../03_frameworks/08_frontier/02_foundation-models.md)
records what was claimed, with its sources.

### 5.5 Offline reinforcement learning: IQL and CQL

**Historical**, kept because it explains a part of the methods above rather than
because you should start a project with it.

Offline reinforcement learning learns from a fixed pile of recorded attempts and
never practises at all, which section 4 listed as one of the three ways to get the
practice. IQL and CQL are the two algorithms people name. Both exist to stop the
critic becoming over-confident about actions that nobody in the recordings ever
tried, which is the central difficulty when you cannot test an idea.

The reason it is historical is not that it stopped working. Its benchmark suite, D4RL,
was formally deprecated, with [Minari](https://github.com/Farama-Foundation/Minari)
as its replacement for datasets, and its algorithms were absorbed into the
post-training of copied policies, which is sub-section 5.4. So read this branch to
understand how a critic can be trained without new attempts, and take its datasets
from Minari rather than from a tutorial built on D4RL. Stable-Baselines3 does not
implement either algorithm, which is itself a fair guide to how much demand there
is.

### 5.6 The landmark systems

**Historical**, and listed because people cite these as the proof that the method
works on real hardware, so it is worth knowing what each one actually showed.

[QT-Opt](https://arxiv.org/abs/1806.10293) (Google, 2018) learned to grasp objects
from a bin using several real robot arms at once, collecting attempts over weeks. It
showed that learning on real hardware was possible, and how costly it was.
[Dactyl](https://arxiv.org/abs/1808.00177) (OpenAI, 2018, with a
[Rubik's Cube follow-up](https://arxiv.org/abs/1910.07113) in 2019) learned to turn a
block in a robot hand's fingers, trained only in simulation with heavy domain
randomisation. [IndustReal](https://github.com/NVLabs/industrealkit) (NVIDIA, 2023)
is the most useful one for an arm, because it fitted pegs and gears into holes after
training only in simulation, transferring to a real Franka arm with no real practice
at all, and reaching between 83 and 99 per cent across 600 trials on parts modelled
on a standard assembly test board. Its successor FORGE improved gear meshing to 98
per cent and nut threading to 69 per cent while halving the contact forces.

Read IndustReal's caveats rather than its headline, because they say what the method
cannot yet do. Its authors deliberately used no force sensor at all, working from
vision and joint positions, on the grounds that such sensors are costly, noisy and
fragile. The clearances were half a millimetre, which is much looser than a real
electrical connector. And none of it is deployed in a factory. None of these four
systems ships a policy you can download, which is the point section 5 opened with.

### 5.7 How to choose

Before choosing anything here, check that you need this method at all, because
section 8 shows that most arm tasks do not. If a person can demonstrate the task,
the earlier pages in this chapter are far less work for the same result.

When you do need it, the default is not to train from nothing. Train a copying
policy first, then improve it on the real arm with HIL-SERL, which is sub-section
5.3. That is the one recipe here with published numbers strong enough to plan
around, and it needs no simulator.

Three things change that answer.

If nobody can demonstrate the task at all, you have nothing to improve, so you train
in simulation. Use PPO from 5.1 with a simulator that runs many arms at once, and
expect the simulator and the reward to take more of your time than the learning does.

If attempts are expensive, because the simulator is slow or the practice is on the
real arm, use SAC from 5.2 instead of PPO, because replaying old attempts is the
whole point of it.

If you are learning the subject rather than shipping a robot, install
Stable-Baselines3 with panda-gym and read the SAC implementation. It is MIT, it runs
on an Apple Silicon Mac, and watching a simulated arm fail for an afternoon will
teach you more about reward design than reading does.

Leave 5.4, 5.5 and 5.6 out of the decision. One is not released, and the other two
are there to be read.

---

## 6. A worked example: pushing a peg into a hole

The methods in section 5 all need a task that suits them, and pushing a peg into
a tight hole is the classic one for reinforcement learning on an arm. The gap
around the peg can be smaller than a camera can see, so the arm has to feel its
way in, by reacting to the force it senses. A person finds this hard to
demonstrate with a joystick, but a program can easily check whether the peg is
in.

Here is how such a project would go, step by step.

1. **Build the simulation.** Model the arm, the peg and the block with the hole,
   where the shapes can come from the parts' computer drawings.
2. **Write the reward.** For example: 1.0 when the peg is all the way in, a smaller
   amount the closer the peg tip is to the hole, and a small penalty for pushing too
   hard.
3. **Add randomness.** Each episode starts the peg in a slightly different place,
   with slightly different friction and a slightly different hole position.
4. **Train.** Run thousands of simulated arms at once with PPO. At first the peg
   lands anywhere, but after many attempts it finds the hole, and then it learns to
   wiggle in when it catches the edge.
5. **Move to the real arm.** A classical planner brings the peg to just above the
   hole, and then the learned policy takes over for the last few millimetres, where
   contact matters.
6. **Check and, if needed, fine-tune.** Test it many times on the real arm. If it
   fails often, then a short period of real-world learning with a person watching can
   close the gap.

Note step 5, because the learned policy does only the part near the contact. The
long
move across the table is done by ordinary planning, which is faster and safer for
that job, and the
[learned motion document](../../../03_frameworks/03_arm-movement/05_learned-motion.md#1-which-part-of-the-move-a-policy-stands-in-for)
explains this split.

---

## 7. What goes wrong, and what people do about it

The worked example assumed a reward rule that says what you meant, and that
assumption is the first thing to fail. Each problem below is followed by what
people do about it.

**The reward says something you did not mean.** The learner finds any way to get a
high score, including ways you did not expect. Suppose the reward is "the mug is
near
the target spot". Then the policy may learn to knock the mug across the table, so
that it slides there and falls over, and that scores just as well as carrying it.
So this is a case of what people call **reward hacking**.

![The person meant carry the mug; the policy learned to knock it over onto the target](../../../images/movement-models/reinforcement-learning-policies/reward-loophole.svg)

The left picture shows what the person meant, while the right picture shows a
movement that earns the same reward and is not what anyone wanted. So people fix
this by adding terms to the reward, such as "the mug must be upright", and by
watching the trained policy carefully before trusting it.

**The simulator is wrong about contact.** Soft, slippery, bendy or breakable things
are hard to simulate, so a policy trained on a simulated sponge may fail on a real
one. So people use domain randomisation, measure the real parts to tune the
simulator, and finish with a short spell of real practice.

**It needs a huge number of tries.** However, training can take hours or days on a
graphics card, even in simulation. So people start from a policy trained by copying,
so that the learner does not start from nothing.

**It gives no safety guarantee.** The policy can output any action, and nothing
inside it stops it pushing too hard or moving too fast. So a separate layer
under the
policy has to limit forces and speeds. The
[collision and failure detection page](../../09_touch-and-body-models/02_most-used/02_collision-and-failure-detection.md)
covers one part of that layer.

**It does not transfer to a new task or a new arm.** A policy trained to insert one
peg does not insert a different connector, so usually you train again from the
start.

---

## 8. Why this kind, and what it costs

Section 7 listed the costs of the method, and this section asks when to pay
them. So there are two obvious alternatives to weigh against it.

The first is to program the movement by hand, where you write a search pattern:
push down, and if it catches then move in a small spiral, and so on. This is
often good enough, because it is easy to understand and to check. Reinforcement
learning is worth it only when the right reaction depends on forces too
complicated to write rules for.

The second is to copy a person, with
[behaviour cloning](../02_most-used/01_behaviour-cloning.md) or a
[diffusion policy](../02_most-used/03_diffusion-and-flow-policies.md). Copying is
cheaper, and it needs no simulator and no reward. So reinforcement learning is worth
it when a person cannot demonstrate the task well, or when you need the policy to
become better than the person was.

What reinforcement learning gives you is a policy that reacts to what it feels,
and that improves by practice instead of by more recordings.

What it costs you is a great deal more than copying. You need a simulator that
models the contact well enough, and you need a reward rule you trust. You also
need a large amount of computing, and the result is hard to explain when it
fails. So the table below sums up when it is worth the cost. Read each row as a
situation, and the column on the right as the usual choice.

| Situation | Usual choice |
| --- | --- |
| The motion is a free-space move from A to B | a classical planner, not learning |
| A person can easily show the task | copy them: behaviour cloning or ACT |
| The task is contact-heavy and easy to score, and can be simulated | reinforcement learning in simulation |
| A copied policy works most of the time but not reliably | a short burst of real-world reinforcement learning on top of it |
| The contact cannot be simulated and is hard to score | hand-written force control, or more demonstrations |

---

## 9. The written alternative

The table above put hand-written force control in the last row, so this section says
what that code is. The written way to fit a peg into a hole is force control with a
search pattern. [Impedance and force
control](../../../06_programming-techniques/07_control-and-motion/03_also-used/01_impedance-and-force-control.md)
makes the arm give way like a spring, so that when the peg meets the edge of the
hole, the side force pushes it towards the centre. Then a small written search, such
as the spiral in section 8, covers the rest when the hole's position is not known
exactly. For moves through free space, the written choice is [sampling-based
planning](../../../06_programming-techniques/06_planning-and-search/02_most-used/01_sampling-based-planning.md).
Book 3's [position, stiffness and
force](../../../03_frameworks/03_arm-movement/04_controlling-the-move.md#4-position-stiffness-and-force)
explains which contact jobs compliance suits.

The written way is better when the contact is simple enough to describe with a
spring and a few rules. But reinforcement learning is better when the right
reaction depends on forces too complicated to write rules for.

---

## 10. Where to read next

This page covered the first of the also-used methods, and the reading below
either compares it with copying or moves on to the next one.

In this chapter:

- [Diffusion and flow policies](../02_most-used/03_diffusion-and-flow-policies.md) learn by copying
  instead of by scoring.
- [Learned motion planners](02_learned-motion-planners.md) is the next page, and it
  covers networks that speed up classical planning.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Latent world models](../../08_world-models/03_also-used/03_latent-world-models.md) explains
  learners that practise inside their own imagined world, which needs far fewer real
  tries.
- [Learned simulators](../../08_world-models/03_also-used/02_learned-simulators.md) covers networks
  that stand in for parts of a simulator.
- [Force and slip models](../../09_touch-and-body-models/02_most-used/01_force-and-slip-models.md)
  explains the force signals these policies often react to.

Deeper documents elsewhere in this repository:

- [Learning from trial and error](../../../03_frameworks/04_one-arm-training/03_learned-methods.md#2-learning-from-trial-and-error)
  gives the evidence, the branches of the method and where it stands in 2026.
- [Sim-to-real: what actually closed the gap](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#5-sim-to-real-what-actually-closed-the-gap)
  goes deeper into moving from simulation to a real arm.
