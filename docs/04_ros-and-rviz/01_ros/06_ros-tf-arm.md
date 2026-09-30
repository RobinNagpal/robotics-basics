# ROS TF: handing the arm's frames to ROS

This doc answers one question: how does every program on a robot find out where
the gripper is, without each one doing the maths itself? The answer is TF, the
part of ROS (Robot Operating System) that keeps track of frames.

It is for a reader who has done two things. The first is the
[frames and transforms doc](../../01_robotics-intro/03_arm/01_overview.md) in
Book 1, which builds the maths on a flat two-joint arm over steps 1 to 3. The
second is [ROS basics](02_ros-basics.md), which explains nodes, topics and
frames. This doc is steps 4 and 5 of the same arm. It uses the same arm, the same
three transforms and the same code package, `src/arm_transforms/`.

## Contents

1. [Step 4: hand the arm to ROS](#1-step-4-hand-the-arm-to-ros)
2. [Step 5: ask instead of working it out](#2-step-5-ask-instead-of-working-it-out)
3. [A bigger arm changes nothing here](#3-a-bigger-arm-changes-nothing-here)
4. [Running it](#4-running-it)
5. [Notes](#5-notes)

---

## 1. Step 4: hand the arm to ROS

File: `step4_broadcast.py`. This is the first step that uses ROS.

In steps 1 to 3, everything was one program talking to itself. Nothing else on
the robot could ask where the gripper was.

**TF** fixes that. It is the part of ROS that keeps track of frames, and the
name is short for *transform*. Programs publish the transforms they know about,
and TF joins them up for anyone who asks.

Step 4 publishes the arm's three transforms, thirty times a second, as the
joints swing:

```
base_link -> link1      turn by q1              (joint 1)
link1     -> link2      move L1, turn by q2     (joint 2)
link2     -> gripper    move L2                 (bolted on)
```

The maths did not change at all. Step 4 imports the same list of transforms that
step 2 used. It only turns each one into a ROS message before sending it.

Two things are worth noticing.

Each link is published on its own. Step 4 never publishes `base_link` →
`gripper`, even though it could work it out easily. Each program publishes only
what it actually knows.

The shapes are drawn in their own frames. The bar for link 1 is described inside
`link1`, and it never moves there. TF moves the frame, and the bar goes along
with it. None of the five shapes is ever repositioned. This is the same idea as
the ball in the [RViz area](../02_rviz/01_overview.md): you do not move the thing,
you move the frame it is attached to.

---

## 2. Step 5: ask instead of working it out

File: `step5_lookup.py`. This is where the work pays off.

Nobody published `base_link` → `gripper`. This program asks for it anyway:

```python
buffer.lookup_transform('base_link', 'gripper', Time())
```

TF joins the three published links and answers.

Now open the file and look for trigonometry. There is none. There is no `cos`,
no `sin` and no `q1 + q2`. The file never imports `arm_math`. It does not know
how long the links are, how many joints there are, or that the arm is flat.

It only knows two frame names.

That is the reason for all the work in steps 2 and 3 of the Book 1 doc. You
describe each part once, in the one place that knows it, and publish that. Then
any other program can ask about any pair of frames, without knowing how the
robot is built.

---

## 3. A bigger arm changes nothing here

Section 6 of the Book 1 doc adds a third joint by adding one row to the list of
transforms. Step 4 would publish that row like the others. Step 5 does not change
at all, because it still asks for two frame names.

A gripper that can turn is the same. Its row starts changing with the new joint.
TF treats a moving transform and a fixed one exactly the same.

---

## 4. Running it

Run these from `code/`:

```
make arm.demo      step 4: publish the arm and draw it in RViz
make arm.watch     step 5: ask TF where the gripper is (needs arm.demo running)
```

`make arm.demo` opens RViz with the arm swinging. The two joints move at
different speeds, so the arm keeps reaching new poses instead of repeating a
short loop. You should see:

- two blue bars, one per link
- a yellow ball at each joint
- a red ball at the gripper
- frame arrows moving along with all of them

`make arm.watch` prints one line a second, like this one:

```
gripper at (+4.037, +2.713) facing   +17.4°   tool tip at (+4.991, +3.012)
```

The arm is swinging through every angle, so the numbers depend on the moment you
run it. The gap between the two pairs is always 1 m. The tool tip is fixed in the
`gripper` frame, and only the frame moves.

---

## 5. Notes

ROS stores a rotation as four numbers, called a **quaternion**, rather than as
angles. Three angles have an awkward case in 3D: at certain poses two axes line
up and one direction of movement disappears. Four numbers have no such case.
`yaw_to_quaternion()` does the conversion for you, and you can use it without
following the theory. The
[frames in 3D doc](../../01_robotics-intro/03_arm/02_frames-in-3d.md) in Book 1
explains quaternions and the awkward case in plain words.
