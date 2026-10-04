# Learning from human video

The previous page supplied the score that the earlier methods needed, and this
last page of the chapter supplies the other scarce thing, which is the data. It
answers one question: can a robot arm learn from videos of people doing a task,
instead of from recordings of the robot itself? Robot recordings are slow and
costly to make, whereas video of people using their hands is cheap, and there is
a huge amount of it. But the catch is that a video of a person does not say what
the robot should do. So this page explains the models that bridge that gap, and
where the gap stays open.

The page is for a reader who has read
[behaviour cloning](../02_most-used/01_behaviour-cloning.md). Behaviour cloning
learns from **demonstrations**, which are recordings of the robot doing the task
while a person steers it. Each such recording pairs what the cameras saw with the
movement command at that moment. But a video of a person has the pictures, and not
those commands. Every new word is explained where it first appears.

## Contents

1. [What it is](#1-what-it-is)
2. [What a human video has, and what it lacks](#2-what-a-human-video-has-and-what-it-lacks)
3. [The four ways to use it](#3-the-four-ways-to-use-it)
4. [A worked example: one frame of a pinch, turned into a gripper command](#4-a-worked-example-one-frame-of-a-pinch-turned-into-a-gripper-command)
5. [Latent actions: learning actions without labels](#5-latent-actions-learning-actions-without-labels)
6. [Where it is used on a robot arm](#6-where-it-is-used-on-a-robot-arm)
7. [Well-known models and libraries](#7-well-known-models-and-libraries)
8. [The gap between a hand and a gripper](#8-the-gap-between-a-hand-and-a-gripper)
9. [Why this kind, and what it costs](#9-why-this-kind-and-what-it-costs)
10. [The written alternative](#10-the-written-alternative)
11. [Where to read next](#11-where-to-read-next)

---

## 1. What it is

The introduction said that these models bridge a gap, so here is the idea in one
sentence. Models that understand hands and video pull something useful for a
robot out of videos of people. So the robot then needs only a little of its own
data to fill in the rest.

For example, think of learning to fold a paper plane from a video, where nobody
moves your hands for you. Instead you watch the person's hands, see where each
fold goes, and copy it with your own hands. You do this even though your hands
are a different size, and even though the camera was somewhere you are not. A
robot learning from a person's video has the same job, but with a harder version
of each problem. Its "hand" is a two-finger gripper, its eyes are cameras in
fixed places, and it cannot feel what the person felt.

---

## 2. What a human video has, and what it lacks

Section 1 said the robot needs something useful out of the video, so this
section says exactly what is there and what is missing. A robot demonstration
has two things in every frame, which are the pictures and the action. An
**action** is the movement command the robot was given at that moment, such as
"move the gripper 2 mm left and close it a little". But a video of a person has
only the first of these. So the table below lists what each kind of recording
contains. Read each row as one kind of information, and the two right columns as
whether each recording has it.

| Information | Robot demonstration | Video of a person |
| --- | --- | --- |
| pictures of the scene and the objects | yes | yes |
| what the task looks like when done | yes | yes |
| the movement command at each moment | yes | no |
| a body the robot has | yes | no: a human hand and arm |
| a camera where the robot's cameras are | yes | usually no |
| how hard things were pressed | sometimes, from a force sensor | no |

So the question is always the same one. How do you get the missing movement command,
or else do without it? The frontier document puts it this way: turning a video into
training data "means inventing the missing action labels", and the quality of that
invention is the whole subject. The
[human video section of that document](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#8-human-video-instead-of-teleoperation)
covers the research in depth, while this page explains the models underneath.

---

## 3. The four ways to use it

Section 2 ended with the question of the missing action, and there are four ways
to answer it. But they give different amounts of help, and they need different
amounts of robot data afterwards.

**Pretrain the robot's eyes.** A **camera encoder** is the part of a policy that
turns a picture into a list of numbers the rest of the network can use. You can train
the encoder on human video first, with no actions at all, so that it learns what
hands, objects and contact look like. Then you train the policy on a small number of
robot demonstrations, starting from that encoder. For example, R3M and VC-1 are two
encoders trained in this way. This gives the least help, but it is the safest,
because the video never
has to say anything about movement.

**Track the hand and map it onto the gripper.** A **hand pose estimator** is a model
that finds the position of each joint of a hand in a picture, and it runs on every
frame of the video. Then a second step, called **retargeting**, turns the hand's
motion into a motion the robot's gripper can make. The result is a demonstration with
actions, made up from the video, and section 4 works through one frame of it.

**Learn actions from the video itself.** A **latent-action model** watches two frames
of video and learns a short code for "what changed between them". However, nobody
tells it what the codes mean at all. Later, a little robot data links each code
to a real robot
movement, and section 5 explains this.

**Edit the video.** Some 2026 work redraws the video, so that the human hand becomes
a robot gripper. The frontier document calls this the video-editing route, and it is
new, so this page does not cover it further.

The frontier document names three routes, which are visual pretraining,
retargeting and video editing. Latent actions sit between the first two, because
like pretraining they need no hand tracking, and like retargeting they produce
something that stands in for an action. This page gives them their own section,
because they are a separate kind of model.

---

## 4. A worked example: one frame of a pinch, turned into a gripper command

The second of the four ways was retargeting, and this example follows one frame
of a video through it. A person pinches the handle of a mug between the thumb
and the first finger. The numbers are made up, but the arithmetic was run in
Python, so the results below are copied from that run.

1. **Find the hand.** A hand pose estimator such as MediaPipe Hands gives 21 points
   per hand, where point 0 is the wrist, point 4 is the tip of the thumb, and point 8
   is the tip of the first finger, called the index finger. A 3D estimator such as
   HaMeR also gives how far each point is from the camera.
2. **Read the two fingertips, in the camera's frame.** A **frame** here means a set
   of directions to measure in, and the camera measures sideways (x), downwards (y)
   and forwards from the lens (z), in metres. The thumb tip is at (0.020, 0.150,
   0.520), and the index tip is at (0.075, 0.140, 0.505).
3. **Move them into the robot's frame.** The robot measures from its own base, which
   is forwards (x), to its left (y) and up (z). Calibration, the step that measures
   where the camera is, found that the camera sits at (0.10, 0, 0.60) in the robot's
   frame, looking forwards. So the camera's forwards is the robot's forwards, the
   camera's sideways is the robot's right, and the camera's down is the robot's
   down. The thumb tip therefore becomes (0.620, −0.020, 0.450), and the index tip
   becomes (0.605, −0.075, 0.460). The
   [rigid transforms page](../../../06_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md)
   explains this step in full.
4. **Place the gripper between the two tips.** The gripper's centre goes to the
   midpoint of the two tips, which is (0.613, −0.048, 0.455) metres, rounded to the
   nearest millimetre.
5. **Turn the pinch into an opening.** The distance between the two tips is 57.9 mm,
   so the gripper is told to open to 57.9 mm. This gripper opens to at most 80 mm, so
   any wider pinch is cut down to 80 mm.
6. **Check that the arm can get there.** The gripper's centre is 0.764 m from the
   robot's base, and the made-up arm here reaches 0.85 m, so this frame is reachable.

![Left: 21 hand points with the thumb tip, index tip and wrist marked. Right: a two-finger gripper opened to 57.9 mm, centred between the two tips](../../../images/movement-models/learning-from-human-video/hand-to-gripper.svg)

The left picture shows the 21 points, numbered in the order MediaPipe Hands
uses, and the dashed line is the pinch. The right picture shows the gripper
command that the pinch becomes. So if you repeat this for every frame, the video
becomes a list of gripper positions and openings, and that list can be used like
a robot demonstration.

But a real video is not as clean as one frame, because the tracker is noisy and
fingers get hidden.

![A graph over four seconds: the tracker's pinch distance is noisy, goes above 80 mm and drops to near zero for a moment; the cleaned gripper command follows it smoothly](../../../images/movement-models/learning-from-human-video/pinch-over-time.svg)

The grey line is the pinch distance from the tracker over a made-up four-second
grasp, and it wobbles from frame to frame. It goes above 80 mm when the hand
opens wider than the gripper can. Then just after 2 seconds it drops to near
zero for four frames, because the hand turned and hid the index finger. The blue
line is the command after two cleaning steps. First, each value is replaced by
the middle value of the nine frames around it, which removes short jumps.
Second, the result is cut to between 0 and 80 mm. Without the first step, the
gripper would squeeze hard on the mug for a moment, for no reason at all.

---

## 5. Latent actions: learning actions without labels

The third of the four ways needs no hand tracker at all. The word **latent**
means hidden, because the model finds the actions itself, and nobody ever labels
them. So a latent-action model learns in two separate parts.

1. **Learn codes from video.** The model sees two frames, one just after the other,
   and it must describe what changed using only a code from a short list, such as one
   of a few dozen. A second part of the model must then redraw the later frame from
   the earlier frame and the code. So if the redrawing is good, the code has captured
   the change. Over millions of frame pairs, each code comes to stand for one kind of
   change, such as "the hand moved left" or "the hand closed".
2. **Link codes to the robot.** A policy is trained to predict the code for each
   moment of human video. Then a small amount of robot data teaches it which real
   robot command each code stands for.

The example below shows the idea with numbers you can see, and it is much
simpler than a real model. Each dot is how an object moved between two frames of
a made-up video, in centimetres, and nobody labelled the dots. A simple grouping
method, k-means, was run on them in the script. It puts each dot in the group
whose centre is nearest, then moves each centre to the middle of its group, and
then repeats.

![Left: dots of frame-to-frame motion fall into four groups, each with a centre. Right: code 0 to 3 mapped to move left, down, right and up](../../../images/movement-models/learning-from-human-video/latent-actions.svg)

The four groups it found have centres at about (−3.0, −0.1), (−0.1, −3.1),
(+2.9, +0.1) and (−0.1, +2.9) centimetres per frame, and these are the four
codes. On the right, a few robot demonstrations give each code a name on this
arm, which are left, down, right and up. A real latent-action model finds its
codes from the pictures themselves, and not from measured motions. But the
result has the same shape, which is a short list of codes found without labels,
then named with a little robot data.

The appeal is that it works on any video, including video with no visible hand.
The cost is that nothing makes the codes match what the robot can do. So a code
can stand for a camera shake, or for something that happened with no action at
all.

---

## 6. Where it is used on a robot arm

Sections 3 to 5 described the methods, and this section says where each one is
actually used.

**A better start for any policy.** A policy that starts from an encoder pretrained on
human video, such as R3M or VC-1, often needs fewer robot demonstrations. It needs
fewer of them than a policy that starts from nothing. This is the most common use,
and it costs almost nothing to try.

**Showing a task by doing it.** A person does the task in front of a camera, and the
robot copies the retargeted motion. This is best for simple pick-and-place moves,
where only the gripper's path and its opening matter. The
[learning path's fourth project](../../../03_frameworks/04_one-arm-training/04_learning-path.md#project-4-copy-it-from-video)
builds exactly this with MediaPipe, and explains why the first attempt misses.

**Pretraining large policies.** Large
[vision-language-action models](../../07_language-models/02_most-used/01_vision-language-action-models.md)
are now pretrained partly on human video. The
[foundation models document](../../../03_frameworks/08_frontier/02_foundation-models.md#6-nvidia-isaac-gr00t)
describes one released model pretrained on human video together with robot data. It
notes that this works partly because its movement commands are relative to where the
gripper is now, which means the same thing for a hand and a gripper.

**Judging progress.** The progress estimators on the
[reward and progress models page](03_reward-and-progress-models.md) are trained on
human video. They learn what "closer to done" looks like from people, and then they
score the robot's attempts.

---

## 7. Well-known models and libraries

Section 6 described where each method is used, and this section names the tools
people actually run, in the order of the four ways in section 3: the two hand
trackers, then the library that turns a tracked hand into robot commands, then two
models whose own pretraining used human video, and last the camera encoder that
started the pretraining route.

Each tool carries one mark: **most used in 2026** means a developer starting today
would reach for it, **worth betting on** means it is not the default yet but the
field is moving that way, and **historical** means it is kept because it explains
how the current tools work.

The table is the short answer. Read each row as one tool. The second column says
what it is best at, the third says how big it is and what hardware it needs, the
fourth gives its licence, and the last says when to pick it. A cell says `not
stated` where the figure is not published.

| Tool | Best at | Size and hardware | Licence | Pick it when |
| --- | --- | --- | --- | --- |
| MediaPipe Hand Landmarker | 21 hand points per frame, while the camera runs | 7.8 MB model file; a laptop processor | Apache-2.0 for the library | you want hand tracking on your own video today |
| HaMeR | a full 3D hand from one picture, including hidden fingers | not stated; its install instructions target an NVIDIA graphics card | MIT for the code; the MANO hand model has its own registration | the video is processed after recording and MediaPipe loses fingers |
| dex-retargeting | turning tracked hand points into robot joint commands | a solver, not a network; runs on the processor | MIT | you have hand points and need gripper commands out of them |
| NVIDIA Isaac GR00T N1.7 | a policy whose pretraining already included 20,000 hours of human video | 3 billion parameters; about 6 GB to download; 16 GB or more of video memory | Apache-2.0 for the code; NVIDIA Open Model License for the weights | you have an NVIDIA graphics card and want that pretraining done for you |
| LAPA | learning actions from video that has no action labels at all | 7 billion parameters; its fine-tuning ran on four 80 GB graphics cards | MIT for the code and the published weights | you have a lot of video, little robot data, and a cluster |
| R3M | a camera encoder trained on human video, to start a small policy from | a ResNet-50 encoder; runs on a laptop | MIT | you will train your own policy and want the cheapest gain there is |

Three much-discussed 2026 results are deliberately absent, because you cannot
download any of them. They are Skild's S1, explained in
[prompting with a demonstration](../../10_making-models-work-on-an-arm/03_also-used/02_prompting-with-a-demonstration.md),
and the large retargeting and video-editing corpora HuRo and RoboEdit, which the
frontier document records in
[the three mechanisms people actually use](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#83-the-three-mechanisms-people-actually-use).
Read those to see where the field is going, and build with the six tools above.

### 7.1 MediaPipe Hand Landmarker

This is the tool **most used in 2026** for getting hand points out of video,
because it is the only one here that runs in real time on a laptop with no
graphics card. MediaPipe Hand Landmarker is Google's hand tracking task, part of
the MediaPipe library. For each hand it finds, it returns the 21 points of section
4 in the same numbering, so point 4 is the thumb tip and point 8 is the index
fingertip.

You would pick it rather than HaMeR, the other tracker below, because HaMeR needs
an NVIDIA graphics card and a separate registration before it runs at all.
MediaPipe runs on the computer you already have, which is what you want while you
are still finding out whether your task survives the hand-to-gripper gap of
section 8. Once you know that it does, HaMeR's accuracy starts to matter.

Its cost is not the licence or the hardware, since the model file is 7.8 MB and
the library is Apache-2.0. The cost is depth, and this is the mistake people make
most often with it. The library returns two versions of each point:
`hand_landmarks` holds them in picture coordinates, scaled from 0 to 1 across the
width and the height, and `hand_world_landmarks` holds them in metres. Those
metres are measured from the middle of the hand, and not from the camera.

The library is `mediapipe`, installed with `pip install mediapipe`. You also
download the model file, `hand_landmarker.task`, from
[Google's own page for the task](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python).

```python
import mediapipe as mp

options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=mp.tasks.vision.RunningMode.IMAGE,
    num_hands=1,
)
with mp.tasks.vision.HandLandmarker.create_from_options(options) as landmarker:
    image = mp.Image.create_from_file("frame_0001.jpg")
    result = landmarker.detect(image)

points = result.hand_world_landmarks[0]      # 21 points, in metres
thumb_tip, index_tip = points[4], points[8]  # the two points section 4 used
pinch = ((thumb_tip.x - index_tip.x) ** 2
         + (thumb_tip.y - index_tip.y) ** 2
         + (thumb_tip.z - index_tip.z) ** 2) ** 0.5
```

The library gives you the palm detector, the landmark model, the fixed numbering
of the 21 points, and, in `handedness`, whether it saw a left or a right hand. For
video you pass `RunningMode.VIDEO` and call `detect_for_video` with a timestamp,
which lets the model follow the hand between frames.

What you supply yourself is everything that places the hand in the room. The pinch
above is real, in metres, which is why step 5 of section 4 could turn it into a
gripper opening, but steps 2, 3 and 4 need a depth camera, two cameras or HaMeR,
and then the calibration that says where the camera sits relative to the robot's
base. The cleaning in section 4 is also yours to write, and it is not optional,
because a tracker that loses the index finger for four frames will otherwise tell
the gripper to close hard on nothing.

### 7.2 HaMeR

HaMeR, which stands for hand mesh recovery, is the tracker **most used in 2026**
for video that is processed after recording rather than live. Pavlakos and
colleagues released it in December 2023 with the paper
[Reconstructing Hands in 3D with Transformers](https://arxiv.org/abs/2312.05251),
and it rebuilds a complete 3D hand surface from one picture. Because it fits a
whole hand model instead of finding points one at a time, it still returns a
sensible hand when some fingers are behind the object.

You would pick it rather than MediaPipe Hand Landmarker when fingers keep
disappearing. Section 8 explains that a hand hides the thing it is holding, which
is exactly the case where a point-finding tracker drops fingers and a model of the
whole hand does not. The project's own record is the only accuracy claim this page
repeats: it took second place in the Ego-Pose Hands task of the Ego-Exo4D
Challenge in June 2024.

It costs you set-up and a graphics card, since the install instructions target
NVIDIA hardware and extra packages are needed for person detection and pose
estimation. The code is MIT, but the model will not run without `MANO_RIGHT.pkl`,
the MANO hand model, and you get that only by registering on
[the MANO website](https://mano.is.tue.mpg.de) and accepting its own licence. So
the code licence and the licence on the thing you need in order to run the code
are different documents, and a commercial project has to read the second one. The
distance from the lens is also computed with a focal length taken from the model's
configuration, which makes it an estimate rather than a measurement.

The project is run as a program rather than imported.

```bash
git clone --recursive https://github.com/geopavlakos/hamer.git
cd hamer
pip install -e ".[all]"
pip install -v -e third-party/ViTPose   # the pose estimator it depends on
bash fetch_demo_data.sh                 # downloads the trained weights
# Now put MANO_RIGHT.pkl in _DATA/data/mano yourself, after registering.
python demo.py \
    --img_folder example_data --out_folder demo_out \
    --batch_size=48 --side_view --save_mesh --full_frame
```

The project gives you the detector, the hand model and the rendering, so you can
judge the fit by eye. What you supply yourself is the step from a hand surface to a
gripper command: the output holds the hand's parameters, its vertices and one
camera translation per detected hand, and turning that into the two fingertip
positions of section 4 is your code.

### 7.3 dex-retargeting

This is the library **most used in 2026** for the retargeting step, which section
3 described as turning a tracked hand into a motion the robot can make. It comes
from the AnyTeleop project of Qin and colleagues, published in 2023, and it holds
several optimisers rather than one. Each solves the same problem: find the robot
joint angles whose fingertips best match the measured human ones.

You would use it rather than writing the midpoint arithmetic of section 4
yourself, and the reason is the robot rather than the hand. Section 4 works
because a two-finger gripper has one number to set. As soon as the robot has a
multi-finger hand, or you want the wrist oriented as well, that arithmetic becomes
a small optimisation problem with joint limits, and this library has already
solved it for real hands, including Allegro, Shadow, LEAP, Inspire, Ability,
Schunk SVH and the two-finger Panda gripper.

It costs you little, since it installs with `pip install dex_retargeting`, it is
MIT, and it runs on the processor. Two things catch people. The library returns
joint positions in its own order, so you must map them to your simulator or driver
by joint name, which the project's notes warn about. It also needs the robot's URDF
file, the file that describes a robot's links and joints, and the ones for the
supported hands come with the repository rather than with the installed package.

```python
from dex_retargeting.constants import (
    RobotName, RetargetingType, HandType, get_default_config_path,
)
from dex_retargeting.retargeting_config import RetargetingConfig

# panda here is Franka's two-finger gripper, so the whole hand becomes one number.
config = get_default_config_path(RobotName.panda, RetargetingType.vector, HandType.right)
RetargetingConfig.set_default_urdf_dir("assets/robots/hands")  # from the repository
retargeting = RetargetingConfig.load_from_file(config).build()

# joint_pos holds the 21 hand points of section 7.1 as metres, one row per point.
indices = retargeting.optimizer.target_link_human_indices      # [[4], [8]]
ref_value = joint_pos[indices[1, :], :] - joint_pos[indices[0, :], :]
qpos = retargeting.retarget(ref_value)   # one angle, for panda_finger_joint1
```

The two numbers in `target_link_human_indices` are worth noticing, because they
are 4 and 8: the configuration that ships for the Panda gripper reads the thumb
tip and the index fingertip, the pair section 4 used by hand. The value it is
given is the direction and distance from one tip to the other, and the
configuration scales that by 1.5 before matching it, because a human pinch and a
gripper opening are not the same size.

What you supply yourself is the hand points, from section 7.1 or 7.2, and
everything about where the gripper goes, because this library sets the fingers and
not the position of the wrist in the room. The repository's own example,
`detect_from_video.py`, puts MediaPipe and this library together over a video
file, and it is the shortest complete thing to read next.

### 7.4 NVIDIA Isaac GR00T N1.7

This model is **worth betting on**, because it is the only released model here
whose own pretraining used human video at scale, so the transfer this page is
about has already been paid for by somebody else. GR00T is NVIDIA's open
vision-language-action model, meaning one network that takes pictures and a
sentence and produces movement commands. The frontier document's
[section on it](../../../03_frameworks/08_frontier/02_foundation-models.md#6-nvidia-isaac-gr00t)
records that N1.7 was tagged as a general-availability release on 18 April 2026,
and that it was pretrained on 20,000 hours of human video from a corpus NVIDIA
calls EgoScale, alongside robot demonstrations.

You would pick it rather than building the pipeline of sections 7.1 to 7.3
yourself. That pipeline gives you a few hundred retargeted demonstrations of one
task, from one camera, with the error chain of section 9; this gives you a policy
that has already watched 20,000 hours of people handling objects, which you then
fine-tune on your own recordings. Its mechanism is also the one you would have to
copy anyway: its movement commands are relative to where the gripper is now, so
three centimetres to the left means the same thing for a hand and for a gripper,
while a target coordinate does not.

It costs you an NVIDIA graphics card, and there is no way round that. Inference
wants 16 GB or more of video memory, fine-tuning wants 40 GB or more, and nothing
about it runs on a Mac. The code is Apache-2.0, but the weights are under the
[NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/),
which permits commercial use while adding conditions Apache-2.0 does not. The
thing that most often goes wrong on a first run is not the hardware: the base
model loads a gated backbone, `nvidia/Cosmos-Reason2-2B`, so without Hugging Face
access to it the run stops with a `GatedRepoError`.

The code is [the Isaac-GR00T repository](https://github.com/NVIDIA/Isaac-GR00T),
and the shortest real thing you can do is run the base model on the sample data it
ships with.

```bash
uv run python scripts/deployment/standalone_inference_script.py \
    --model-path nvidia/GR00T-N1.7-3B \
    --dataset-path demo_data/droid_sample \
    --embodiment-tag OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT \
    --traj-ids 1 2 \
    --inference-mode pytorch \
    --execution-horizon 8
```

That runs the model over two recorded episodes and compares its predicted
movements with the recorded ones, which proves the installation works before any
robot is involved, and the weights download on the first run. What you supply
yourself is your own robot: a dataset in the GR00T LeRobot format, an embodiment
tag that describes your arm's state and action layout, and a fine-tuning run. The
tag above belongs to the DROID dataset's arm, and using it for your own arm
produces commands of the wrong shape.

### 7.5 LAPA

LAPA, which stands for latent action pretraining from videos, is also **worth
betting on**, because it is the only openly published implementation of the
latent-action route that section 5 explained. Ye and colleagues published it in
October 2024, and it was accepted at ICLR 2025. The released model, LAPA-7B-openx,
learned its codes from video and was then pretrained on the pooled Open
X-Embodiment data without using its action labels at all.

You would pick it rather than the retargeting route of sections 7.1 to 7.3 when
the video has no usable hand in it. Retargeting needs a visible hand, a depth
estimate and a calibrated camera, and it fails on video that has none of them.
LAPA needs only pairs of frames, so it can use video where the hand is out of
shot, where the camera moved, or where the person did something a gripper could
never copy. The price is the one section 5 named: nothing makes the learned codes
match what your robot can do.

It costs you a cluster and a second training stage. The model has 7 billion
parameters, it is written in JAX rather than PyTorch, and the project's
fine-tuning scripts were run on four 80 GB A100 graphics cards. The code and the
published weights are both MIT, which is unusually clean for a model this size.
The misunderstanding to avoid concerns the output, and the project states it
plainly: inference gives you a latent action, one of 4,096 possible codes, and not
a robot command.

There is no installable package, so the model is run from the repository.

```bash
git clone https://github.com/LatentActionPretraining/LAPA.git
cd LAPA && pip install -r requirements.txt
mkdir lapa_checkpoints && cd lapa_checkpoints
# The three parts of the checkpoint: text tokeniser, image tokeniser, weights.
wget https://huggingface.co/latent-action-pretraining/LAPA-7B-openx/resolve/main/tokenizer.model
wget https://huggingface.co/latent-action-pretraining/LAPA-7B-openx/resolve/main/vqgan
wget https://huggingface.co/latent-action-pretraining/LAPA-7B-openx/resolve/main/params
cd ..
python -m latent_pretraining.inference   # prints a latent action, not a command
```

The project gives you both halves of section 5 already built: the code book
learned from video, and a policy that predicts a code from a picture and a
sentence. What you supply yourself is the robot data that gives the codes meaning,
because the fine-tuning step wants real trajectories with their actions and
gripper states. So the robot recordings this page is trying to avoid are still
needed at the end, only fewer of them.

### 7.6 R3M

R3M is **historical**, and it is kept here because it is the clearest example of
the cheapest idea on this page. Nair and colleagues of Stanford and Meta released
it in March 2022 and published it at the Conference on Robot Learning that year.
It is a camera encoder trained on Ego4D, a large collection of first-person video
of people doing everyday tasks, and it was trained so that its output follows how
a task unfolds over time and matches the words that describe the video. The models of sections 7.4 and
7.5 now do that for a whole policy rather than for the encoder alone, which is why
this one is historical and not current.

You would still pick it over VC-1, the obvious alternative, for a reason that has
nothing to do with accuracy. VC-1, from Meta in 2023, was trained on a wider mix
of first-person video and ordinary pictures and tested on more robot tasks, and
MVP, from the University of California, Berkeley, in 2022, learns by filling in
hidden patches of the same kind of video. But the repository that holds VC-1 carries a
Creative Commons Attribution-NonCommercial 4.0 licence, and so does MVP's, so
neither can go into a product. R3M's repository is MIT. This is the kind of detail
this book exists for, because the model you can measure is not always the model
you can ship.

It costs you almost nothing to try, which is its point: it is a ResNet-50, it runs
on a laptop processor, and the embedding is 2048 numbers. Its real cost is age,
because the repository has not changed since March 2023, so you are on your own
with new versions of PyTorch. And since the encoder is normally frozen, whatever it
throws away is gone, so a task that turns on a thin wire or a small printed mark
may not be represented at all.

```python
import torch
import torchvision.transforms as T
from PIL import Image
from r3m import load_r3m

r3m = load_r3m("resnet50")   # resnet18 and resnet34 are also published
r3m.eval()

transforms = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor()])
image = transforms(Image.open("frame_0001.jpg")).reshape(-1, 3, 224, 224)
with torch.no_grad():
    embedding = r3m(image * 255.0)   # R3M expects values from 0 to 255
print(embedding.shape)               # torch.Size([1, 2048])
```

The library is `r3m`, installed from its repository, and the multiplication by 255
is not a mistake, because `ToTensor` divides by 255 and R3M wants the original
range back. What you supply yourself is the policy that sits on top of those 2048
numbers, the robot demonstrations to train it on, and the decision whether to keep
the encoder frozen or let training change it. Nothing here produces a movement
command on its own.

### 7.7 How to choose

Start with MediaPipe Hand Landmarker and dex-retargeting, because they run on the
computer you already have and they tell you within a day whether your task
survives the hand-to-gripper gap of section 8, which is the question that decides
everything else. Five situations change that answer.

If the video is processed after recording and the hand keeps hiding its own
fingers, replace MediaPipe with HaMeR, and accept the graphics card and the MANO
registration as the price.

If you have an NVIDIA graphics card with 16 GB or more of video memory, start from
GR00T N1.7 instead of building a pipeline, because its pretraining already
included 20,000 hours of human video and yours will not.

If you have a large amount of video in which no usable hand is visible, and a
cluster to train on, LAPA is the route that needs no hand tracker.

If you will train a small policy on your own robot demonstrations anyway, add R3M
as the encoder and keep the rest of your plan. Do not reach for VC-1 or MVP in a
commercial project, because both repositories are Attribution-NonCommercial.

If you can still choose how the data is recorded, do not use bare-hand video at
all. A person holding an instrumented gripper removes the hand-to-gripper gap
completely, and the frontier document's
[section on handheld grippers](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#4-handheld-grippers-collecting-without-a-robot)
says what you can print and what you can buy.

One rule cuts across all five. Read the licence on the weights and not the one on
the code, because GR00T, HaMeR and VC-1 each pair permissive code with different
terms on the part you actually run.

---

## 8. The gap between a hand and a gripper

The tools in section 7 all work, so the hard part is not the models themselves.
Instead it is that a hand is not a gripper, and a person is not a robot. The
frontier document names three things that human video still cannot supply, and
this section explains each of them, then adds two more.

**The hand can do things the gripper cannot.** A hand has five fingers and a turning
wrist. So a person rolls a pen in the fingers, holds two things at once, or pushes
with the side of the palm, and a two-finger gripper can do none of that. A large part
of any human video therefore shows movements the robot cannot make, and these have to
be found and thrown away, or else the policy learns them wrongly. The sign is a
retargeted
gripper that closes on nothing, because the person was using three fingers.

**The path may be out of the robot's reach.** A person's arm is a different length
and moves from a different place. So a path that is easy for a person can be outside
the robot's reach, and nothing in the video says so.

![Top view: the arm's reach as a blue ring around its base. A retargeted hand path starts inside the ring, and its last part, in red, goes outside](../../../images/movement-models/learning-from-human-video/outside-the-reach.svg)

The picture shows a made-up hand path after it has been moved into the robot's frame,
where the blue ring is the area the arm can reach. The script checks every point, and
25 % of the path is outside the ring. So a reach check like step 6 of the worked
example has to run on every frame. And even a reachable path can need a joint angle
the arm does not have, which a check with the arm's
[inverse kinematics](../../../06_programming-techniques/06_planning-and-search/02_most-used/02_numerical-inverse-kinematics.md)
catches.

**Force is missing.** A video shows where a hand went, and not how hard it pressed.
So for tasks that are about contact, such as pushing a plug into a socket, the video
is missing the part that mattered.

**The camera is in the wrong place.** The person's video was filmed from their head
or from across the room, whereas the robot's cameras are somewhere else. So a policy
that learned from one view can fail from another. The sign is a policy that works on
the human video it trained on, and does badly on the robot's own pictures.

**The hand hides the object.** In many frames the person's hand covers the thing it
is holding. So the hand tracker loses fingers, as in the pinch graph in section 4,
and the object tracker loses the object.

So these five gaps are why every method still needs some robot data at the end. The
frontier document's
[section on what human video cannot supply](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#84-what-human-video-still-cannot-supply)
makes the same point. And its
[section on the 2026 result](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#82-the-result-that-changed-the-argument)
explains why the robot data may now be a small final step rather than most of the
work.

---

## 9. Why this kind, and what it costs

Section 8 listed the gaps, so this section asks when human video is still worth
using. Learning from human video is a way to get training data for a movement
model from videos of people. What it does for you is replace some of the robot
demonstrations, which are the scarcest thing in robot learning.

The obvious alternative is to record more robot demonstrations, by steering the
robot while it does the task. That data is exactly right, because it has the
right body, the right cameras and the real commands. Its problem is cost, since
each hour needs a robot, a person, and a set-up. So human video is worth it when
you need variety that you cannot record on a robot, such as many rooms, many
objects, or many ways of doing a task.

The second alternative is a handheld gripper, where a person holds a gripper with a
camera on it and does the task. It is described in
[the frontier document's section on handheld grippers](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#4-handheld-grippers-collecting-without-a-robot).
This removes the hand-and-gripper gap, because the person uses the same fingers as
the robot. So human video is worth it over that only when you want to use video that
already exists, or video of people who were not collecting data at all.

What it costs you is a chain of models, each of which can be wrong: the hand tracker,
the depth estimate, the camera calibration, the retargeting, and the filtering. Their
errors add up, as the pinch graph showed. It also costs you robot data in the end,
because none of these methods removes the need for it. And the claims in this area
move fast, because the
[frontier document](../../../03_frameworks/08_frontier/06_what-is-coming.md#73-robots-now-learn-a-new-task-from-a-single-video)
shows how a claim to learn "from a single video" can mean much less than it sounds.

The table below sums up the usual choice for each case. Read each row as a
situation, and the right column as what people usually do.

| Situation | Usual choice |
| --- | --- |
| You will record robot demonstrations anyway | start from an encoder pretrained on human video, such as R3M or VC-1 |
| A simple pick-and-place, shown once by a person | hand tracking and retargeting, checked for reach before running |
| The task needs force, or fingers the gripper does not have | record robot demonstrations; human video will not show it |
| Lots of varied video, little robot data | latent actions or a large pretrained policy, then fine-tune on robot data |
| You want the person's motion without the hand-gripper gap | a handheld gripper instead of bare-hand video |

---

## 10. The written alternative

Human video is a source of training data, and not a way to move the arm. So its
written alternative is to program the task instead of teaching it. Book 3's [teach and
replay](../../../03_frameworks/04_one-arm-training/02_programmed-methods.md#1-teach-and-replay)
records a motion from a person with no model at all. The person moves the arm to each
position, by buttons or by hand, and then the arm plays the positions back. The
retargeting steps on this page are written code themselves. [Rigid
transforms](../../../06_programming-techniques/02_geometry-and-cameras/02_most-used/02_rigid-transforms.md)
moves the hand points into the robot's frame, and [sensor
streams](../../../06_programming-techniques/04_fitting-and-estimation/02_most-used/04_sensor-streams.md#smoothing-moving-average-exponential-and-median-filters)
explains the median filter that cleans the pinch.

So the written way is better when one fixed motion is enough. But learning from
video is better when you need variety that nobody could program, or record on a
robot.

---

## 11. Where to read next

This is the last page of the chapter, so the reading below either closes the
thread that ran through it or opens the chapters that build on it.

In this chapter:

- [Reward and progress models](03_reward-and-progress-models.md) covers judge models,
  several of which are trained on the same human video.
- [Behaviour cloning](../02_most-used/01_behaviour-cloning.md) is the learner that
  uses the demonstrations made from video.
- [The movement models overview](../01_overview.md) compares every kind in this
  chapter.

In other chapters of this book:

- [Keypoints and object pose](../../03_seeing-models/02_most-used/04_keypoints-and-object-pose.md)
  explains how models find points in a picture, which is what a hand pose estimator
  does for the joints of a hand.
- [Where the data comes from](../../01_what-models-are/05_where-the-data-comes-from.md)
  compares human video with every other source of training data.
- [Video prediction models](../../08_world-models/03_also-used/01_video-prediction-models.md)
  are close relatives of latent-action models, because they learn from video what
  happens next.

Deeper documents elsewhere in this repository:

- [Human video instead of teleoperation](../../../03_frameworks/08_frontier/03_data-and-demonstration.md#8-human-video-instead-of-teleoperation)
  gives the 2026 research, its numbers and its maturity.
- [Project 4: copy it from video](../../../03_frameworks/04_one-arm-training/04_learning-path.md#project-4-copy-it-from-video)
  is a hands-on project that builds hand tracking and retargeting in simulation.

