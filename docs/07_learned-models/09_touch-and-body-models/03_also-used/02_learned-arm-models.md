# Learned arm models

This page answers one question: how can a robot arm learn how its own body behaves,
where the numbers in its manual are not quite right? To answer that, it explains what
such a model predicts, how it is trained from the arm's own movements, the well-known
kinds, and when it is worth using instead of plain physics.

It is written for a reader who has already read the
[overview of this chapter](../01_overview.md) and the first chapter of this book. You
should know from Book 1 that an arm is a chain of joints and links, and that each
joint has a motor and an encoder, which is the sensor that measures the joint's
angle.

> Before this page, it helps to have read [arm
> dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md),
> which explains the textbook model of the torque each joint needs, and [system
> identification](../../../06_programming-techniques/04_fitting-and-estimation/03_also-used/01_system-identification.md),
> which measures the numbers inside it. This page learns the part that those two
> leave out.

## Contents

1. [What it is](#1-what-it-is)
2. [What goes in and what comes out](#2-what-goes-in-and-what-comes-out)
3. [How it works inside](#3-how-it-works-inside)
4. [How it is trained](#4-how-it-is-trained)
5. [Well-known models](#5-well-known-models)
6. [A worked example: a heavier gripper on an old arm](#6-a-worked-example-a-heavier-gripper-on-an-old-arm)
7. [What goes wrong](#7-what-goes-wrong)
8. [Why this rather than the obvious alternative, and what it costs](#8-why-this-rather-than-the-obvious-alternative-and-what-it-costs)
9. [The written alternative](#9-the-written-alternative)
10. [Where to read next](#10-where-to-read-next)

---

## 1. What it is

A learned arm model is a model of the arm's own body, learned from recordings of the
arm moving.

Here is an everyday example of the same learning. When you start using a new bicycle,
you do not know exactly how hard to push the pedals to go at a given speed. However,
after a few rides you do. By then you have learned how this bicycle behaves: how
heavy it is, how stiff its chain is, and how much its brakes grab, and nobody gave
you any of those numbers.

A robot arm has a description of itself, too. The maker gives the length of each
link, the mass of each part, and where each part's weight is centred, and from those
numbers physics can work out how much torque each joint needs to move in a given
way. A **torque** is a turning force, the force a motor uses to turn its joint. This
is the arm's **dynamics**: how forces turn into movement.

However, the maker's description is close rather than exact. It leaves out the
friction in the gearboxes, and it also leaves out the cables that hang along the arm
and pull on it. It also does not know about the gripper you bolted on, or the wear after
years of use. So a learned arm model fills in what the description leaves out.

This page also covers two related jobs of the same kind. **Calibration** means
finding the small errors in the arm's geometry, so that the arm goes exactly where
it is told. A **self-model** is a model an arm builds of its own shape, often by
watching itself with a camera.

## 2. What goes in and what comes out

Now that the job is clear, here is what passes in and out. There are two main
directions for such a model, and they answer opposite questions.

![A forward model predicts where the arm will be from the torques; an inverse model gives the torques to get where you want](../../../images/touch-and-body-models/learned-arm-models/forward-and-inverse.svg)

The picture shows the same arm twice. The dark arm is where it is now, while the pale
arm is where it will be, or where you want it, a moment later. The orange arrows are
the torques at the joints.

A **forward model** answers: "if I apply these torques now, where will the arm be a
moment from now?" Its input is the joint angles, the joint speeds and the torques.
Its output is the joint angles and speeds a moment later.

An **inverse model** answers: "to move the way I want, what torque does each joint
need?" Its input is the joint angles, the joint speeds, and the change in speed you
want, and its output is one torque for each joint.

Because the controller uses it to work out the torque to send to each motor, the
inverse model is the one used most on real arms. The
[collision page](../02_most-used/02_collision-and-failure-detection.md#31-the-gap-between-expected-and-measured)
uses the same prediction as its "expected torque".

A self-model has different inputs and outputs from both of those. Its input is the
joint angles, and its output is the arm's shape in space, meaning which points around
the robot the arm fills.

## 3. How it works inside

### 3.1 Physics plus a learned correction

The last section said what the model predicts, and this section says how it does it.
Most learned arm models used in practice do not throw away physics. Instead, they
keep the textbook model and learn only the part it gets wrong. This is called
**residual learning**, because the network learns the residual, which is what is left
over after the physics has done its part.

![Torque against joint speed: the textbook line, the measured dots, and the textbook plus a learned correction](../../../images/touch-and-body-models/learned-arm-models/textbook-plus-correction.svg)

The picture is a drawn example, not a real measurement, and it shows the torque one
joint needs at different speeds. The dashed line is the textbook model, which leaves
out friction, while the dots are what the real arm needs. At zero speed the dots
jump, because the joint must first overcome the friction that holds it still. The
solid line is the textbook model with a learned correction added, and it follows the
dots.

The steps are these:

1. The textbook model works out a torque from the joint angles, speeds and the
   change in speed you want.
2. A small network looks at the same inputs and works out a correction.
3. The program adds the two together and sends that torque to the motor.

This has two advantages over learning everything from nothing. The network has a
small job, so it needs less data. Where the network has seen nothing, the textbook
model also still gives a sensible answer.

### 3.2 A network that learns the whole thing

Instead, a second kind learns the whole model from data, but it is built so that its
answers obey the rules of physics. For example, the energy of a moving arm cannot
appear from nowhere, so a network built this way cannot give an answer that breaks
that rule. This means it needs less data than a plain network, and its answers are
more sensible outside the training data.

A plain network with no physics inside it can also learn the whole model. However, it
needs the most data of all, and it can give strange answers for movements it has
never seen.

### 3.3 A self-model from a camera

A self-model learns the arm's shape instead of its torques, and one way of building
one works as follows.

![An arm moving at random while a camera records it, and the learned shape for new joint angles](../../../images/touch-and-body-models/learned-arm-models/self-model-from-a-camera.svg)

The picture shows the two stages. On the left, the arm moves to many random poses
while a camera records it, and each picture is paired with the joint angles at that
moment. On the right, the trained model is given a pair of angles it has never seen.
For each point in space around the robot, it then says whether the arm would fill
that point. The green dots are the points it says the arm fills.

Once an arm has a self-model, it can plan without being told its own shape. So if a
part is bent or replaced, the arm can record itself again and learn the new shape.

### 3.4 Calibration

Calibration is usually done without a neural network at all. The arm moves to many
poses, and a precise measuring device, such as a laser tracker, records where the
tool really is. A program then finds the small errors in the link lengths and joint
angles that best explain the difference.

However, some errors are not simple length or angle errors. The links bend a little
under their own weight, and the gears have a little play. So a small network can
learn these left-over errors, in the same way as the residual in section 3.1. It
takes the joint angles as input, and it outputs the correction to the tool's
position.

## 4. How it is trained

The last section described the model, and this section says where its recordings come
from. A learned arm model trains on the arm's own movements. This is its great
advantage, because that data is cheap and safe to collect.

1. The arm moves through many different movements. People often use smooth
   movements that sweep each joint through its range at different speeds, so the
   model sees a wide variety.
2. At each moment, the program records the joint angles, the joint speeds, and the
   torque or current in each motor. The speed change is worked out from the
   speeds.
3. For an inverse model, each moment becomes one example. The input is the angles,
   the speeds and the speed change. The right answer is the torque that was
   actually used.
4. The network is trained to give the right answer for each example.

Because the arm reports many readings a second, an hour of movement gives a very
large number of examples. This means the limit is not the number of examples but how
varied they are, because a model trained only on slow movements does badly on fast
ones.

For a self-model, the data is the joint angles paired with camera pictures, as in
section 3.3. For calibration, it is the joint angles paired with measurements from
the precise measuring device.

## 5. Well-known models

The earlier sections explained what this kind of model does, and this section is for
choosing one. There is no learned arm model to download, because such a model
describes one arm and is worth nothing on another. What people publish instead are the
methods, and the libraries that fit them to your own recordings. So this section
compares the seven methods a developer meets most often, and section 5.8 says which to
start with and when a learned model beats the maker's own model.

Read the table one row at a time. The second column says whether a developer starting
today would reach for that method. "Size and speed" says what the method costs to run,
which matters because a torque model is asked hundreds of times a second. Each licence
is the licence of the library named in that sub-section, read from the library's own
repository, and `not stated` means a fact could not be sourced.

| Method | How current | Best at | Size and speed | Licence | Pick it when |
|---|---|---|---|---|---|
| 5.1 The maker's model with its numbers fitted to your arm (Pinocchio) | most used in 2026 | getting the torque roughly right in every pose, with numbers you can read and check | one linear fit; the physics call itself runs inside a control loop | BSD-2-Clause | always, as the first step |
| 5.2 A residual torque network on top of 5.1 (Pinocchio and PyTorch) | most used in 2026 | friction, cable pull and wear that the equations have no term for | two small layers are usual; fast enough for a control loop | BSD-2-Clause (Pinocchio), three-clause BSD (PyTorch) | error is left over after 5.1 |
| 5.3 An actuator network (Isaac Lab) | most used in 2026 | making a simulated motor behave like the real motor | network size `not stated`; runs inside the simulator | BSD-3-Clause | you train a policy in simulation to run on your arm |
| 5.4 MuJoCo's system identification toolbox | worth betting on | fitting the masses, frictions, gains and delays of a whole simulated robot | one simulation run per parameter per optimiser step | Apache-2.0 | your simulator does not move like your arm |
| 5.5 Deep Lagrangian Networks | worth betting on | one network that cannot break the rules of physics for moving bodies | larger and slower than a residual network of the same accuracy | MIT | you want the physics inside the network rather than beside it |
| 5.6 Local learners with an error bar (locally weighted projection regression, local Gaussian processes) | historical | a correction that also says how unsure it is | an exact Gaussian process costs time growing with the cube of the number of examples | Lesser General Public License with a linking exception, MIT (GPyTorch) | the controller must know when to distrust the correction |
| 5.7 A visual self-model | worth betting on | the arm's shape, when no trustworthy description of it exists | trained offline on an NVIDIA graphics card; not a control-loop model | MIT | the arm is new, modified or damaged |

### 5.1 The maker's model with its numbers fitted to your arm

**Most used in 2026**, because it removes the largest part of the error for the least
work, and it is not a learned model at all. You keep the textbook equations, read the
arm's shape from its description file, written in the Unified Robot Description Format
(URDF), and fit the ten numbers that describe each link: its mass, three for where its
weight is centred, and six for how it resists turning. The library is
[Pinocchio](https://github.com/stack-of-tasks/pinocchio), published by the
Stack-of-Tasks project under BSD-2-Clause.

The obvious alternative is to trust the numbers the maker wrote into the URDF. Fitting
them costs one recording, and it gives you numbers you can print, compare with the
maker's and argue about, which no network does. It also tells you how much error is
left for a network to learn.

What it costs you is care. The fit is rank deficient, meaning several different sets of
numbers explain the same recording equally well, so an individual mass can come out
physically impossible even when the predicted torque is good. The regressor has no term
for friction either, so you add two columns per joint yourself: one for friction that
grows with speed, and one for friction that only depends on the direction of travel.

```python
import numpy as np
import pinocchio as pin

model = pin.buildModelFromUrdf('arm.urdf')
data = model.createData()

# One row per recorded moment, from the run described in section 4.
q, v, a, tau = (np.load(f'{name}.npy') for name in ('q', 'v', 'a', 'tau'))

# Each call returns a matrix whose columns stand for the ten numbers of every link,
# so that matrix times numbers equals torque. Stacking the whole recording turns the
# question "which numbers explain these torques?" into one large linear system.
rows = [pin.computeJointTorqueRegressor(model, data, qi, vi, ai)
        for qi, vi, ai in zip(q, v, a)]
A, b = np.vstack(rows), tau.reshape(-1)

fitted, *_ = np.linalg.lstsq(A, b, rcond=None)
print(np.abs(A @ fitted - b).mean())    # the error left over, in newton metres
```

You supply the recording and the URDF, and Pinocchio supplies the regressor matrix,
which is tedious to write by hand. The friction columns and the rank deficiency are
still yours, unless you use [FIGAROH](https://pypi.org/project/figaroh/) (Apache-2.0,
at [thanhndv212/figaroh-plus](https://github.com/thanhndv212/figaroh-plus)), which
reduces the regressor to the combinations that can actually be identified, generates
the movements that excite them, and also does the geometric calibration of section
3.4.

### 5.2 A residual torque network on top of the maker's model

**Most used in 2026** for learned arm dynamics, and the method of section 3.1. The
physics model from 5.1 gives a torque, a small network predicts what the physics
missed, and the controller sends the sum. The libraries are Pinocchio for the physics
and [PyTorch](https://pytorch.org/) for the network, and the split is visible in the
code: one call does the physics, and a handful of lines do the learning.

The obvious alternative is one plain network that learns the whole torque. The residual
wins twice over. It has a much smaller job, so an hour of recording is enough, and
where it has seen nothing its output is a small correction to a sensible answer rather
than a guess.

What it costs you is a retraining whenever the gripper, the payload or the wear
changes, and a correction that carries no guarantee, which is why the code clips it. It
also needs a way to send torques. Many industrial controllers accept only positions,
and on those arms this model can only be used off the control loop, for example as the
expected torque of a collision detector.

```python
import numpy as np
import pinocchio as pin
import torch
from torch import nn

model = pin.buildModelFromUrdf('arm.urdf')
data = model.createData()
q, v, a, tau = (np.load(f'{name}.npy') for name in ('q', 'v', 'a', 'tau'))

# rnea is the standard algorithm for "what torque does this movement need?".
physics = np.array([pin.rnea(model, data, qi, vi, ai) for qi, vi, ai in zip(q, v, a)])

x = torch.tensor(np.hstack([q, v, a]), dtype=torch.float32)
y = torch.tensor(tau - physics, dtype=torch.float32)   # only what the physics missed

net = nn.Sequential(nn.Linear(x.shape[1], 64), nn.Tanh(), nn.Linear(64, y.shape[1]))
optimiser = torch.optim.Adam(net.parameters(), lr=1e-3)
for _ in range(2000):
    optimiser.zero_grad()
    loss = nn.functional.mse_loss(net(x), y)
    loss.backward()
    optimiser.step()
```

At run time the controller adds the two parts and clips the learned part, so that a
strange answer in a strange pose cannot do much harm. Here `q` and `v` are this
moment's reading, and `a_wanted` is the change in speed the controller is asking for.

```python
with torch.inference_mode():
    correction = net(torch.tensor(np.hstack([q, v, a_wanted]), dtype=torch.float32))
send_to_motors(pin.rnea(model, data, q, v, a_wanted) + np.clip(correction.numpy(), -5, 5))
```

You supply the recording, the change in speed worked out from the recorded speeds, and
the clipping limit, which is a decision rather than a measurement. Keep the units the
same on both sides of the subtraction, because a current in amperes minus a torque in
newton metres is a mistake rather than a residual. Without joint torque sensors you
train on motor current, with the accuracy cost section 7 describes.

### 5.3 An actuator network

**Most used in 2026** wherever a policy is trained in simulation for a real machine.
Hwangbo and colleagues introduced it in [Learning agile and dynamic motor skills for
legged robots](https://arxiv.org/abs/1901.08652) in 2019. Instead of modelling the
whole arm you model one motor: a network reads the recent joint position errors and
speeds, and outputs the torque the real motor actually produced. It then replaces the
simulator's ideal motor, so a policy trained in simulation meets a motor that lags and
saturates like the real one. The library is
[Isaac Lab](https://github.com/isaac-sim/IsaacLab), BSD-3-Clause, whose
`isaaclab.actuators` package offers `ActuatorNetMLPCfg` and `ActuatorNetLSTMCfg`. MLP
stands for multi-layer perceptron, which is a plain stack of layers, and LSTM is a
network that carries its own memory of the recent past.

The obvious alternative is the simulator's ideal motor with a stiffness and a damping
number, randomised during training. The network wins because gearbox friction,
communication delay and torque saturation arrive together and in the right proportions,
instead of being covered by a random range wide enough to include machines that do not
exist.

What it costs you is a recording from the real motor with its torque measured, which
without joint torque sensors means a test rig. The network is saved as a TorchScript
file, which is a PyTorch network stored so that it loads without its original Python
code, so somebody else's file does not fit your motor. The frontier chapter also
records that Isaac Lab needs an NVIDIA graphics card and lists no macOS support.

```python
from isaaclab.actuators import ActuatorNetLSTMCfg
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# Isaac Lab ships this configuration for the ANYdrive 3.0 motors of ANYmal-C, and
# the three limits below are the ones in that file.
ANYDRIVE_3_LSTM_ACTUATOR_CFG = ActuatorNetLSTMCfg(
    joint_names_expr=[".*HAA", ".*HFE", ".*KFE"],   # which joints this model stands for
    network_file=f"{ISAACLAB_NUCLEUS_DIR}/ActuatorNets/ANYbotics/anydrive_3_lstm_jit.pt",
    saturation_effort=120.0,
    effort_limit=80.0,
    velocity_limit=7.5,
)
```

You supply your own joint names, your own TorchScript file and your own three limits
from the motor's data sheet, and Isaac Lab supplies the history buffer and the
per-joint plumbing. For a plain stack of layers use `ActuatorNetMLPCfg`, which also
asks for the units the network was trained in, as `pos_scale`, `vel_scale` and
`torque_scale`, and for `input_idx`, which picks the moments of history the network
reads, where `0` is now and `n` is n steps ago.

### 5.4 MuJoCo's system identification toolbox

**Worth betting on**, because it turned fitting a simulator to a real machine from a
research exercise into a feature of a standard install. MuJoCo 3.5.0, on 12 February
2026, added a system identification toolbox in Python under Apache-2.0, as the frontier
chapter records in [its simulation
section](../../../03_frameworks/08_frontier/04_simulation-and-evaluation.md#52-measuring-the-robot-instead-of-randomising-over-it).
You give it a model, your recorded controls and your recorded sensor readings, and it
fits the parameters you choose by nonlinear least squares with bounds, using batched
simulation runs. The same release made delays a property of actuators and sensors, so a
control loop's latency became something to fit rather than something to write yourself.

The obvious alternative is domain randomisation: randomise the simulator's physical
numbers over a wide range so that the policy copes with all of them. The frontier
chapter puts the difference as moving from randomising over your ignorance to measuring
first and randomising over what is left. Against 5.1, pick this toolbox when the thing
to fix is a simulator rather than a controller, because it fits contact friction and
motor gains, which the torque regressor of 5.1 has no column for.

What it costs you is simulation time. The optimiser works out its gradients by small
changes, so every parameter needs its own simulation run at every step. It fits only
parameters your model has a term for, and its README says the measurement part of the
interface is "not yet final".

```python
import mujoco
from mujoco import sysid          # an optional extra: pip install "mujoco[sysid]"

spec = mujoco.MjSpec.from_file('arm.xml')
model = spec.compile()

def set_link1_mass(spec, p):      # a callback writes one fitted number into the model
    spec.body('link1').mass = p.value[0]

params = sysid.ParameterDict()
params.add(sysid.Parameter('link1_mass', nominal=2.0, min_value=0.5, max_value=5.0,
                           modifier=set_link1_mass))   # these values are the README's

control = sysid.TimeSeries.from_control_names(times, ctrl_array, model)
measured = sysid.TimeSeries.from_names(times, measurement_array, model)
state0 = sysid.create_initial_state(model, qpos_0, qvel_0)
sequences = sysid.ModelSequences('arm', spec, 'traj_1', state0, control, measured)

residual_fn = sysid.build_residual_fn(models_sequences=[sequences])
fitted, result = sysid.optimize(initial_params=params, residual_fn=residual_fn)
```

You supply the model, the recordings and one callback per parameter, which says where
in the model that number belongs. The toolbox supplies the optimiser, the parallel
simulation runs and an HTML report of the fitted values. Its
[README](https://github.com/google-deepmind/mujoco/blob/main/python/mujoco/sysid/README.md)
lists helpers for the awkward parameters.

### 5.5 Deep Lagrangian Networks

**Worth betting on**, because it is the cleanest answer to the complaint that a learned
correction can do anything it likes. Michael Lutter, Christian Ritter and Jan Peters
published [Deep Lagrangian Networks](https://arxiv.org/abs/1907.04490) in 2019. The
network does not output a torque directly. It outputs the quantities that the equations
of motion are built from, so every torque it can produce obeys those equations, which
is the second kind of model in section 3.2. The code is at
[milutter/deep_lagrangian_networks](https://github.com/milutter/deep_lagrangian_networks)
under MIT, in a PyTorch and a JAX version.

The obvious alternative is the residual network of 5.2. Pick Deep Lagrangian Networks
when you want one model whose answers stay sensible far outside the recording, and when
you have no trustworthy URDF, because this network learns the arm's inertia from the
recording instead of reading it. Pick 5.2 when the URDF is good, because then the
physics is free and the network only has to learn the leftovers.

What it costs you is speed and fiddliness. The network differentiates itself to build
the equations of motion, so one prediction does more work than a plain stack of layers
of the same width, and the activation has to be smooth, which is why the repository
ships its own derivative of each activation. It learns only what the equations of
motion can express, so friction has to be added separately.

```python
import torch
from deep_lagrangian_networks.DeLaN_model import DeepLagrangianNetwork

# n_dof is the number of joints. The repository's own example uses two hidden layers
# of width 64 and the SoftPlus activation, which is smooth everywhere.
net = DeepLagrangianNetwork(n_dof, n_width=64, n_depth=2, activation='SoftPlus',
                            diagonal_epsilon=0.01)
optimiser = torch.optim.Adam(net.parameters(), lr=5e-4, weight_decay=1e-5, amsgrad=True)

for q, qd, qdd, tau in batches:          # the recording of section 4, in small groups
    optimiser.zero_grad()
    tau_hat, dEdt_hat = net(q, qd, qdd)  # the predicted torque, and the predicted power
    power = torch.sum(qd * tau, dim=1)   # the power the real motors delivered
    loss = (torch.mean(torch.sum((tau_hat - tau) ** 2, dim=1))
            + torch.mean((dEdt_hat - power) ** 2))
    loss.backward()
    optimiser.step()

torque = net.inv_dyn(q, qd, qdd_wanted)  # what the controller asks for at run time
```

You supply the recording, and the network supplies the physics structure. The second
part of the loss is worth keeping: it asks the model to account for where the energy
went, which is what stops two wrong answers cancelling each other out.

### 5.6 Local learners with an error bar

**Historical** as code, and kept here because one of its properties is still missing
from the methods above. Sethu Vijayakumar and Stefan Schaal's locally weighted
projection regression (LWPR) fits many small simple models, each good for one region of
movement, and updates them while the robot runs. Duy Nguyen-Tuong, Jan Peters and
Matthias Seeger did the same with Gaussian processes in [Local Gaussian Process
Regression for Real Time Online Model
Learning](https://proceedings.neurips.cc/paper/2008/hash/01161aaa0b6d1345dd8fe4e481144d84-Abstract.html)
in 2008. A Gaussian process is a method that returns a prediction together with how
unsure it is. The [LWPR library](https://informatics.ed.ac.uk/slmc/lwpr) is ANSI C with
a Python wrapper, under the Lesser General Public License with an exception for static
linking.

The obvious alternative is the residual network of 5.2, which is easier to train and
faster to run on a recording you already have. The reason to read this family anyway is
the error bar. Section 7 ends by saying that a learned correction gives no guarantee,
and an error bar answers that directly: where the model has no data it says so, and the
controller can shrink the correction instead of trusting it. To get that today you use
a Gaussian process in [GPyTorch](https://github.com/cornellius-gp/gpytorch) (MIT) or in
[scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html)
(BSD-3-Clause) rather than the original libraries.

What it costs you is scale. An exact Gaussian process inverts a matrix with one row and
column per training point, so the training time grows with the cube of the number of
points, and an hour of recording has far too many. You sample the recording, or use one
of the approximate methods in GPyTorch. Prediction is slower than a small network too,
which is why the original work made its models local.

```python
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

x = np.hstack([q, v, a])        # the arrays of 5.2: one row per recorded moment
y = tau[:, 2] - physics[:, 2]   # the leftover torque of one joint, here the third

# An exact Gaussian process cannot take the whole recording, so take a sample of it.
pick = np.random.default_rng(0).choice(len(x), size=2000, replace=False)

kernel = ConstantKernel() * RBF(length_scale=np.ones(x.shape[1])) + WhiteKernel()
gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True).fit(x[pick], y[pick])

mean, std = gp.predict(x_now, return_std=True)   # the correction, and how unsure it is
```

You supply the sample size, and one model per joint, because this fit predicts one
number. The `std` that comes back is what the network in 5.2 cannot give you, and the
controller uses it by scaling the correction down as `std` grows.

### 5.7 A visual self-model

**Worth betting on** for arms that change, because it is the only method here that
needs no description of the arm at all. Boyuan Chen, Robert Kwiatkowski, Carl Vondrick
and Hod Lipson published [Full-Body Visual Self-Modeling of Robot
Morphologies](https://arxiv.org/abs/2111.06389) at Columbia University in 2021. The arm
moves while cameras watch it, and the trained model answers one question for any joint
angles: is this point in space filled by the robot? That is the model of section 3.3,
and the paper reports one "accurate to about one percent of the workspace". Robert
Kwiatkowski and Hod Lipson's earlier task-agnostic self-modeling learned the same kind
of model and relearned it after damage. The code is at
[BoyuanChen/visual-selfmodeling](https://github.com/BoyuanChen/visual-selfmodeling)
under MIT.

The obvious alternative is forward kinematics from the URDF, which is exact, free and
instant when the description is right. So this method earns its cost only when the
description is wrong or missing: a hand-built arm, a modified one, or one that has been
damaged and no longer matches its drawing.

What it costs you is a camera rig, a long random-motion recording and research code.
The README was tested on Ubuntu 18.04 with CUDA 11.0 and Python 3.6, and it asks you to
uncomment particular lines of `models.py` before one of the training steps, which tells
you what kind of software this is. The model predicts shape and not torque, so it feeds
a planner rather than a controller.

```bash
git clone https://github.com/BoyuanChen/visual-selfmodeling
cd visual-selfmodeling
# Install its pinned requirements in a virtual environment, as its README describes.
python sim.py            # makes the training data in the PyBullet simulator
cd scripts && CUDA_VISIBLE_DEVICES=0 python ../main.py ../configs/state_condition/config1.yaml NA
```

You supply the robot, the cameras and the recording, and in practice a port of `sim.py`
to your own arm, because the published pipeline makes its data in a simulator. What you
get out is a model you can ask about any point in space, which a planner then uses in
place of the arm's collision geometry.

### 5.8 How to choose

Fit the maker's model to a recording of your own arm first, with 5.1, and only then
decide whether anything is left to learn. For most catalogue arms doing most jobs,
nothing is, and the work stops there.

When the error that is left does matter, these are the cases where a learned model
beats the maker's model and the maker's calibration.

- The error depends on something the equations have no term for. Gearbox friction that
  changes as the arm warms up, a cable that pulls differently in each pose, and a link
  that bends under load are the common three. Add a residual network, 5.2.
- The controller must know how far to trust its own correction. Use a Gaussian process
  with its error bar, 5.6.
- The target is a simulator rather than a controller. Fit the simulator's parameters and
  delays with 5.4, and replace its ideal motors with actuator networks, 5.3.
- The arm has no trustworthy description, because it is hand-built, modified or damaged.
  Learn its shape with 5.7.
- You want one model rather than a model plus a patch, and can afford a slower network.
  Use Deep Lagrangian Networks, 5.5.

These are the cases where the maker's model and the maker's calibration win, and a
learned model does not help.

- Absolute positioning accuracy. A factory calibration is measured against the
  workspace with an outside instrument, such as a laser tracker, and a model trained
  from the arm's own encoders cannot discover an error those encoders cannot see.
- A limit that has to be justified to somebody. The written model's behaviour can be
  checked in every pose by argument, and a network's cannot, so where the number must be
  defended, keep the written model and keep the learned part clipped.
- A controller that accepts only position commands. A learned torque correction needs a
  torque or current interface. Without one the model can still run off the control loop,
  for example as the expected torque of a collision detector, but it cannot improve the
  arm's tracking.
- An error that really is one unknown number, such as the mass of a new gripper. Measure
  it or fit it, as in 5.1, rather than training a network to hide it.

## 6. A worked example: a heavier gripper on an old arm

Here is one arm and one upgrade, step by step. An arm has worked in a cell for
several years. Then the team fits a new, heavier gripper with a tactile sensor on
each finger. Two problems then appear. The arm follows its planned paths less exactly
than before, and its collision detector gives false alarms during fast moves.

1. The team keeps the maker's physics model, but adds the new gripper's mass.
2. They run the arm through an hour of varied movements, with the gripper open and
   empty, and record the joint angles, speeds and motor currents.
3. They train a small network to predict the residual: the difference between the
   torque the physics model gives and the torque the motors actually used.
4. The network learns two things the physics model left out. The first is the
   friction in each gearbox, which has grown with wear. The second is the pull of
   the new gripper's cable, which drags on the last two joints.
5. The controller now sends the physics torque plus the learned correction, so the
   arm follows its paths more closely.
6. The collision detector uses the same corrected prediction as its expected
   torque. Its gap in normal work is now smaller, so the stop line can be set lower
   without false alarms. Gentle bumps that it used to miss now cross the line.

The model will need retraining when the gripper changes again, or when the wear
changes the friction further. So the team schedules a short recording run every few
months, and compares the new residual with the old one.

## 7. What goes wrong

The sections above described this kind of model at its best. This list gives the six
things that go wrong in practice, and what people do about each one.

- **Movements it has not seen.** A model trained on slow movements gives poor
  answers for fast ones. So people collect varied data, and they keep a physics
  model underneath so that the answer is never far off.
- **Changes over time.** Friction changes as the arm warms up during the day, and
  as the gearboxes wear over years. So people retrain from time to time, or they use
  a method that learns while the arm runs.
- **A payload it does not know about.** The model learned the arm with an empty
  gripper, so a heavy object in the gripper changes the torques. People give the
  model the payload's mass as an input, or they weigh the object first with the
  wrist sensor.
- **Motor current is not torque.** On arms without joint torque sensors, the model
  learns from motor current, but current is only roughly proportional to torque,
  because the friction in the gearbox sits between them. So people accept a coarser
  model, or they use an arm that measures joint torque directly.
- **Speed.** The controller needs a torque answer many hundreds of times a second,
  and a large network may be too slow. So people use small networks for this job.
  [Running a model on a robot](../../10_making-models-work-on-an-arm/02_most-used/02_running-a-model-on-a-robot.md)
  explains the trade-off.
- **No guarantee.** A learned correction can make things worse in an odd pose. A
  controller that uses one should limit how large the correction may be.

## 8. Why this rather than the obvious alternative, and what it costs

The last section listed what goes wrong, so this section weighs those problems
against the alternative. The obvious alternative is **a better physics model,
identified from data**, and that is called **system identification**. You keep the
textbook equations, and you measure the arm's real masses and friction numbers by
running it through set movements and fitting the numbers. This is a well-established
method, because it needs little data, its answers can be checked and it behaves
sensibly everywhere. So it is the right first step, and it is often enough on its
own.

A learned model is worth adding when the effects left over do not fit the textbook
equations. Friction that changes with speed and temperature, a cable that pulls
differently in each pose, and a link that bends under load are all examples, because
none of them is a simple number to fit. Instead, a network can learn them from the
same recordings.

A self-model is worth it in a different case, which is when the arm's shape is not
known in advance or may change, such as a new or damaged robot. For a standard
factory arm with an accurate description, it is not needed.

What it costs you:

- Recording time on the arm. It is cheap and safe, but it must be varied.
- Retraining whenever the arm, its gripper or its wear changes.
- A model that must run fast enough for the controller.
- A model that gives no guarantee. Keep the physics model underneath, and limit the
  size of the learned correction.

## 9. The written alternative

This page has argued for adding a learned correction, so the last question is what
the written model alone gives you. The written alternative is the textbook model with
its numbers measured on your own arm, which is the first alternative in section 8.
Book 5's
[arm dynamics](../../../06_programming-techniques/07_control-and-motion/02_most-used/03_arm-dynamics.md)
explains the model.
[System identification](../../../06_programming-techniques/04_fitting-and-estimation/03_also-used/01_system-identification.md)
explains how to move the arm so that the data can tell the numbers apart, and how to
fit them. The geometry calibration in section 3.4 is written code too: a fit of the
kind that
[least-squares fitting](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/01_least-squares-fitting.md)
explains.

Because it needs little data and behaves sensibly everywhere, the written model wins
as a first step, and it is often enough on its own. A learned correction wins only
for effects that are not a simple number to fit, such as friction that changes with
temperature, or a cable that pulls differently in each pose.

## 10. Where to read next

In this chapter:

- [Collision and failure detection](../02_most-used/02_collision-and-failure-detection.md) uses
  the inverse model from this page as its expected torque.
- The [overview](../01_overview.md) compares all four kinds.

In this book:

- [Learned dynamics models](../../08_world-models/02_most-used/01_learned-dynamics-models.md)
  predict how the world changes when the arm acts. A learned arm model is the same
  idea with the arm's own body as the whole world.
- [Learned motion planners](../../06_movement-models/03_also-used/02_learned-motion-planners.md)
  cover learned inverse kinematics: a network that turns a wanted gripper position
  into joint angles.
- [Reinforcement learning
  policies](../../06_movement-models/03_also-used/01_reinforcement-learning-policies.md) are often
  trained in a simulator. A learned model of the arm's motors makes that simulator
  closer to the real arm.

In the other books:

- [Learned pieces inside a planned
  system](../../../03_frameworks/03_arm-movement/05_learned-motion.md#3-learned-pieces-inside-a-planned-system)
  in the frameworks book describes where small learned models help a planned arm.
- [Calibration, which decides all of
  it](../../../02_perception/02_object-perception/02_sensors.md#4-calibration-which-decides-all-of-it)
  in the perception book covers calibrating the camera and the arm together.
- [Controlling the move](../../../03_frameworks/03_arm-movement/04_controlling-the-move.md)
  explains what the controller does with a torque.
