# Finding one box with a camera

## The problem

A box is sitting on a table, and a robot arm has to pick it up. Before it can,
the arm needs to know two things about the box: **where it is** on the table, and
**how tall it is**, so that it knows how far down to reach.

In this doc we measure both with one depth camera. The camera hangs 40 cm above
the middle of the table and looks straight down, and it is the only thing doing
the measuring: nothing tells it where the box is, or how big it is.

![The scene, from above and from the side](../images/camera/one-box-intro/scene.svg)

The box is a 6 cm cube, and its middle is 6.5 cm to the right of the middle of the
table and 4 cm towards the top of the picture. We know those numbers because we
built the scene, but the camera does not, which makes it a fair test: by the end
of the doc, the camera's own measurement should match them.

Why use a camera for this? Because the robot cannot know ahead of time what will
be on the table, or where. Someone may have moved the box since last time. A
camera sees the whole table at once, in a fraction of a second, without touching
anything.

The table, the box and the camera are simulated in Gazebo, the robot simulator
most ROS projects use, and the code that finds the box is a small ROS 2 project,
`src/camera_one_box`, laid out the way a real robot arm's perception code is. The
pictures and numbers in this doc all come from that simulation.

This doc builds on [the basics](basics.md), which explain what a camera records
and the four numbers that describe its lens. It does the calculations that turn
the camera's pictures into the box's position and height, one idea at a time.
The [code doc](one-box-code.md) then writes the same calculations as pseudo code
and as Python, explains the libraries the code uses, and describes the project
itself: how its pieces connect, how to run it, and where things are in the code.

## Contents

1. [Calculations](#1-calculations)
   - [1.1 Pixel plus depth gives back the point](#11-pixel-plus-depth-gives-back-the-point)
     · [What we are doing](#what-we-are-doing)
     · [The variables](#the-variables)
     · [Why the calculation works](#why-the-calculation-works)
     · [Step by step](#step-by-step)
     · [The same steps as three formulas](#the-same-steps-as-three-formulas)
   - [1.2 Where the camera is](#12-where-the-camera-is)
     · [camera_to_world](#camera_to_world)
     · [Where the numbers come from](#where-the-numbers-come-from)
   - [1.3 What one capture contains](#13-what-one-capture-contains)
   - [1.4 The box, measured](#14-the-box-measured)
2. [Vocabulary](#2-vocabulary)

---

## 1. Calculations

[The basics](basics.md) showed that each pixel gives a direction, and that the
depth picture gives a distance for every pixel. This section turns those two
facts into arithmetic, in four parts that build on one another. Section 1.1
turns one pixel and its depth reading into a point measured from the camera.
Section 1.2 moves that point into the room, using where the camera is and which
way it points. Section 1.3 shows everything one capture contains, including the
point cloud, which is every pixel turned into a point at once. Section 1.4 then
uses all of this to measure the red box: where it is on the table, and how tall
it is.

### 1.1 Pixel plus depth gives back the point

This is the part that the basics have been building up to, so it is worth
taking slowly, one idea at a time.

#### What we are doing

Before any calculation, it helps to picture the scene. The camera hangs 40
centimetres above the middle of the table, and it points straight down at it.
The red box stands on the table a little to one side of the middle, and because
the box is 6 centimetres tall, its top is 34 centimetres below the camera.
Because the camera points straight down, anything "in front of the camera" is
really below it, and we will keep using the phrase "in front of" because that
is how a camera sees the world.

![Where the camera is, and what we are measuring](../images/camera/one-box-intro/deproject_setup.svg)

In this section we pick one small spot on the top of the red box, and we work
out exactly where that spot is, measured from the camera. We want three
distances, all in metres. The first is how far the spot is to the right of the
camera, which we call `x`. The second is how far it is towards the bottom of
the picture, which we call `y`. The third is how far it is in front of the
camera, which we call `z`. The picture above shows `x` and `z` from the side,
while `y` runs across the table at right angles to the page, so it does not
show up in a side view.

We need these numbers because a robot arm cannot move to a pixel. A pixel only
tells us where the box appears in the picture, but the arm has to know where the
box really is in space, so turning pixels into distances is the step that
connects what the camera sees to what the arm can do.

The camera has already given us everything we need to find those three
distances, in two pictures taken at the same moment. The colour picture tells us
which pixel the spot appears in, and [section 3 of the
basics](basics.md#3-what-a-picture-loses) showed that a pixel tells us a
direction, meaning one straight line out from the lens. The depth picture tells
us, for that same pixel, how far away the surface is, as [section 4 of the
basics](basics.md#4-getting-distance-back-the-depth-picture) explained. Once we
know which line to follow and how far to go along it, we arrive at exactly one
point, and that point is the spot on the box.

#### The variables

To do the calculation we use seven numbers that we already know, and we get
three numbers back. Before using them, it is worth knowing what each one means
and where it comes from, so this part goes through them one by one, starting
with the picture itself.

![The variables in the picture](../images/camera/one-box-intro/deproject_pixel.svg)

A position in the picture is described by two directions, and it helps to name
them clearly. **Across** means along the width of the picture, from its left
edge to its right edge. **Down** means along the height of the picture, from
its top edge to its bottom edge. These are the two directions you would use to
describe a place on a printed photo lying on a desk, and in this picture
"across" is the camera's right, while "down" is towards the bottom of the
picture.

The first two numbers, `u` and `v`, say which pixel we are looking at. The number
`u` counts pixels across the picture, starting from 0 at the left edge and going
up to 320 at the right edge. The number `v` counts pixels down the picture,
starting from 0 at the top edge and going up to 240 at the bottom edge. The spot
we chose appears at `u = 212.5` and `v = 86.5`, which is on the top of the red
box. Both numbers end in `.5` because a pixel is a small square rather than a
point, and we want the middle of that square: pixel number 212 covers the strip
from 212 to 213, so its middle is at 212.5.

The next two numbers, `cx` and `cy`, give the position of the middle of the
picture. The picture is 320 pixels wide and 240 pixels tall, so its middle is at
`cx = 160` across and `cy = 120` down. The middle matters because anything
exactly in front of the camera appears there, which makes it the natural place
to measure every other pixel from, and the diagram above shows it as a cross.

The fifth number is the `depth` reading for our pixel, which we read from the
depth picture at the same `u` and `v`. For our pixel it is `0.340` metres. As
[section 4 of the basics](basics.md#4-getting-distance-back-the-depth-picture)
explained, this distance is measured straight out in the direction the camera
points, and not along the slanted line from the lens to the spot. That detail is
what will make the last step of the calculation so simple.

The last two numbers, `fx` and `fy`, are the focal length of the lens, measured
in pixels, which [section 6 of the basics](basics.md#6-the-lens-as-four-numbers)
introduced. They describe how zoomed in the camera is, and they have a simple
meaning that we will rely on in a moment: a point that is as far to the side of
the camera as it is in front of it appears exactly `fx` pixels from the middle
of the picture. In our camera both numbers are `277.1`, and they are equal
because the pixels are square.

The three numbers that come out, `x`, `y` and `z`, are the distances described
at the start of this section. They are measured along the camera's own axes from
[section 6 of the basics](basics.md#6-the-lens-as-four-numbers), which point the
same ways as the picture: `x` points across, to the right, `y` points down the
picture, and `z` points straight out of the lens.

Here are all ten together, for looking things up later:

| Name | What it is | Where it comes from | For our pixel |
| --- | --- | --- | --- |
| `u` | the pixel's position across the picture, counted from the left edge | the pixel we picked | 212.5 |
| `v` | the pixel's position down the picture, counted from the top edge | the pixel we picked | 86.5 |
| `cx` | the middle of the picture, across | the four lens numbers ([section 6 of the basics](basics.md#6-the-lens-as-four-numbers)) | 160 |
| `cy` | the middle of the picture, down | the four lens numbers | 120 |
| `depth` | how far in front of the camera the spot is, in metres | the depth picture, at the same pixel | 0.340 |
| `fx` | the focal length across, in pixels | the four lens numbers | 277.1 |
| `fy` | the focal length down, in pixels | the four lens numbers | 277.1 |
| `x` | **answer:** how far to the right of the camera, in metres | worked out below | |
| `y` | **answer:** how far towards the bottom of the picture, in metres | worked out below | |
| `z` | **answer:** how far in front of the camera, in metres | worked out below | |

#### Why the calculation works

Before doing any arithmetic, it helps to see why the calculation works, because
then each step will make sense instead of being a rule to memorise. The reason
is that there are two triangles with exactly the same shape.

![Why it works: two triangles with the same shape](../images/camera/one-box-intro/deproject_triangles.svg)

Light from the spot on the box travels to the camera in a straight line, passes
through the lens, and lands on the picture inside the camera. That one straight
line makes two triangles. The small triangle is inside the camera, between the
lens and the picture. Its long side, pointing straight out of the lens, is the
focal length `fx`, and its short side, pointing across, is how far the pixel is
from the middle of the picture, which is `u - cx`. The large triangle is outside
the camera, between the lens and the spot. Its long side, pointing straight out
of the lens, is the depth `z`, and its short side, pointing across, is `x`, the
distance we want to find.

Both triangles have a right angle, and both have the same angle at the lens,
because the light travels in one straight line. Two triangles with the same
angles always have the same shape, even when one is much bigger than the other,
and even when one is measured in pixels while the other is measured in metres.
Because the shapes are the same, the short side divided by the long side gives
the same answer in both triangles:

```
(u - cx) / fx  =  x / z
```

For our pixel, the left side is `52.5 / 277.1`, which is about `0.19`. This
number is the direction from [section 3 of the
basics](basics.md#3-what-a-picture-loses), written as a number: it says that the
line from the lens moves 0.19 metres to the right for every metre it goes
forwards. Since we know the line goes 0.340 metres forwards before it reaches
the box, we can find how far to the right it has moved by that point, and that
is exactly `x`. The steps below do this calculation carefully, and the same
reasoning, turned on its side, gives `y` from `v` and `cy`.

#### Step by step

We can now work through the calculation for the spot on the red box, one step
at a time, using the numbers from the table above.

**Step 1: find how far the pixel is from the middle of the picture.** Both
triangles start from the line that points straight out of the lens, and that
line lands on the middle of the picture. So the first thing we need is the
number of pixels between our pixel and the middle, first across and then down:

```
pixels to the right of the middle = u - cx = 212.5 - 160 =  52.5
pixels below the middle           = v - cy =  86.5 - 120 = -33.5
```

The first result tells us that the pixel is 52.5 pixels to the right of the
middle. The second result is negative because `v` counts downwards and 86.5 is
smaller than 120, which means that our pixel is 33.5 pixels *above* the middle
rather than below it.

**Step 2: find how much of the table one pixel covers at that distance.** A
pixel does not cover a fixed amount of the world, because a camera takes in more
of the world the further away it looks. When a pixel looks at something close to
the camera, it covers a tiny patch, and when the same pixel looks at something
far away, it covers a much larger patch. The triangles tell us exactly how
large the patch is. Since `fx` pixels in the picture match a distance across
that is equal to the depth, a single pixel matches a distance of the depth
divided by `fx`:

```
one pixel covers = depth / fx = 0.340 / 277.1 = 0.001227 metres
```

This means that at the height of the box top, each pixel covers about 1.2
millimetres. It is the same idea as the last column of the tables in [section 7
of the basics](basics.md#7-field-of-view-and-resolution-are-separate-knobs),
where one pixel covered 1.44 millimetres of the table, which is 0.40 metres
away. The box top is 6 centimetres closer to the camera than the table, so each
of its pixels covers a little less.

**Step 3: turn the distance in pixels into a distance in metres.** We now know
that the pixel is 52.5 pixels to the right of the middle, and that each pixel
covers 0.001227 metres at that distance. Multiplying these two numbers together
gives the distance to the right in metres, and doing the same with the pixels
below the middle gives the distance down the picture:

```
x = pixels to the right × one pixel =  52.5 × 0.001227 = +0.0644 metres
y = pixels below        × one pixel = -33.5 × 0.001227 = -0.0411 metres
```

**Step 4: find how far in front of the camera the spot is.** This last distance
needs no calculation at all, because it is the depth reading itself:

```
z = depth = 0.340 metres
```

This is where the detail from [section 4 of the
basics](basics.md#4-getting-distance-back-the-depth-picture) pays off. The depth
is measured straight out from the lens, rather than along the slanted line, so
it is already the long side of the large triangle, and we can use it exactly as
it is.

When we put the three results together, the spot is at `(+0.0644, -0.0411,
0.340)` metres, measured from the camera. In everyday terms, the spot on top of
the red box is 6.4 centimetres to the right of the camera, 4.1 centimetres
towards the top of the picture, and 34 centimetres in front of the camera. The
value of `y` is negative, and that is correct, because `y` measures distance
towards the bottom of the picture, while this spot sits towards the top.

#### The same steps as three formulas

The four steps are usually written in a shorter form, as three formulas. The
first two formulas do steps 1, 2 and 3 in one line each, one for `x` and one for
`y`, and the third formula is step 4:

```
x = (u - cx) · depth / fx
y = (v - cy) · depth / fy
z =  depth
```

Turning a pixel and a depth back into a point in this way is called
**deprojection**, because it undoes what the camera did when it took the
picture. It is the exact reverse of the formula in [section 6 of the
basics](basics.md#6-the-lens-as-four-numbers), which starts from a point and
works out which pixel that point lands on. We can check this by putting our
answer back into that formula: `277.1 × 0.0644 / 0.340 + 160` comes to 212.5,
which is the pixel we started from. The two formulas are really one formula,
read in two directions.

One small detail is worth repeating, because it causes real mistakes. If we used
the corner of the pixel, 212, instead of its middle, 212.5, the answer would move
by half a pixel. That sounds too small to matter, but at the edge of a box, half
a pixel can be the difference between a point on the box and a point on the
table behind it.

The picture below shows the whole journey in one place: the pixel and its depth
on the left, the arithmetic we have just done in the middle, and, on the right,
the point placed in the room. That last part is still to come.

![Pixel plus depth gives back the point](../images/camera/one-box-intro/deprojection.svg)

The point we have found is measured from the camera, not from the room. To use
it, the robot also needs to know where the camera is and which way it points,
and section 1.2 explains that step next. The same four steps appear again in the
[code doc](one-box-code.md), as [pseudo
code](one-box-code.md#11-one-pixel-into-one-point) and as
[Python](one-box-code.md#32-one-pixel-into-one-point).

### 1.2 Where the camera is

The point we found in section 1.1 is measured from the camera, so what it really
says is "34 centimetres in front of me, and a little to the right". That is not
yet useful to the arm, because the arm needs to know where things are in the
room, not where they are compared with the camera. To turn one into the other,
we also need to know where the camera is and which way it points, and together
those two things are called the camera's **pose**. Every picture has to come
with the pose it was taken from, because without it, the picture's numbers
cannot be placed anywhere in the room.

#### camera_to_world

The pose is usually kept as one table of numbers, called **camera_to_world**,
because it takes a point measured from the camera and gives the same point
measured in the room, which is also called the world. For the camera in this
doc, which hangs 40 centimetres above the middle of the table and looks straight
down, the table is:

|  | camera's RIGHT | camera's DOWN | camera's FORWARD | camera's POSITION |
| --- | :---: | :---: | :---: | :---: |
| world x | 1 | 0 | 0 | 0.00 |
| world y | 0 | −1 | 0 | 0.00 |
| world z | 0 | 0 | −1 | 0.40 |
|  | 0 | 0 | 0 | 1 |

The table is easiest to read one column at a time. The last column says where
the camera is, measured in metres from the middle of the table, and it shows
that the camera is 0.40 metres straight up. The first three columns are
directions, and each of them says which way one of the camera's own axes points
in the room. The camera's right points along the room's x, so the first column
is `(1, 0, 0)`. The camera's down, towards the bottom of the picture, points
along the room's negative y, so the second column is `(0, −1, 0)`. The camera's
forward points straight down at the table, which is the room's negative z, so
the third column is `(0, 0, −1)`. The bottom row is always `0 0 0 1` and carries
no information of its own. It is only there so that a computer can do the
turning and the shifting in a single multiplication.

This is the same idea as a transform in the [arm area](../arm/overview.md): a
turn and a shift, kept together.

Using the table is simpler than it looks. We start at the camera's position,
then walk `x` along the camera's right, `y` along its down, and `z` along its
forward, and wherever we end up is the point in the room. For the spot on the
red box, we start at the camera, 0.40 metres above the middle of the table.
Walking 0.0644 metres along the camera's right moves us 0.0644 metres along the
room's x. Walking −0.0411 metres along the camera's down means walking 0.0411
metres the opposite way, which is towards the room's positive y. Finally,
walking 0.340 metres along the camera's forward takes us 0.340 metres straight
down, which leaves us 0.060 metres above the table. So the spot is at
`(+0.0644, +0.0411, +0.0600)` in the room.

That last number, 0.060 metres, is exactly the height of the red box, even
though nothing in the calculation was told how tall the box is. The height came
from the depth reading and the camera's pose alone. Notice also that `y` changed
sign on the way into the room. For this camera, "down the picture" points along
the room's negative y, so a spot towards the top of the picture has a positive
y in the room.

#### Where the numbers come from

Nobody types this table in. In the project, it comes from the camera's
description, the file `urdf/camera.urdf.xacro`, which says where the stand holds
the camera. Its joint `camera_mount` puts `camera_link` 0.40 metres above the
middle of the table, turned a quarter turn down so that the lens looks at the
table, and a quarter turn around so that the room's +Y comes out at the top of
the picture. A second joint turns `camera_optical_frame` so that its axes match
the picture, as [section 4.2 of the code
doc](one-box-code.md#42-the-cameras-two-frames) explains.

robot_state_publisher reads that description and publishes both joints on TF,
the part of ROS that keeps track of where every frame is. When the box locator
needs `camera_to_world`, it asks TF for the transform from `world` to
`camera_optical_frame`, and TF joins the two joints together. The answer comes
back as a translation and a quaternion rather than a table, and the function
`transform_matrix()` in `measure.py` turns it into exactly the table above.

### 1.3 What one capture contains

So far we have used two pictures from each capture: the colour picture and the
depth picture. A real camera, and the ROS messages that carry its pictures, can
give the same shot in a few more forms, all the same size and all describing the
same pixels. ROS tells them apart by their **encoding**, which is a short name
that says what the numbers in each pixel mean. The encodings are worth knowing,
because reading a picture in the wrong encoding is one of the most common bugs
in camera code.

| Picture | Encoding | Each pixel holds | At the red box pixel |
| --- | --- | --- | --- |
| colour | `rgb8` | red, green, blue, 0 to 255 each | `(202, 121, 112)` |
| grey | `mono8` | brightness, 0 to 255 | `144` |
| depth | `32FC1` | distance, in metres | `0.3400` |
| depth | `16UC1` | distance, in whole millimetres | `340` |

The **colour** picture, `rgb8`, is what most people mean by "a camera". Each
pixel holds three numbers from 0 to 255, one each for red, green and blue. On its
own it is the least useful picture for our job, because it gives directions and
appearance but no measurements.

The **grey** picture, `mono8`, holds a single brightness number for each pixel,
so it is a third of the size of the colour picture. A lot of vision work, such as
finding edges and corners or following something as it moves, never looks at
colour, so the smaller picture is enough. The brightness is not the plain
average of red, green and blue, because the human eye is much more sensitive to
green than to blue. To match what a person sees, grey weights them `0.299` for
red, `0.587` for green and `0.114` for blue.

The **depth** picture comes in two forms, and they are easy to mix up. `32FC1`
holds the distance in metres, as a decimal number, while `16UC1` holds the same
distance in whole millimetres. They are the same measurement written in two
ways, but if a program reads one as the other, every distance comes out a
thousand times too big or too small.

A colour-only camera, such as the Raspberry Pi camera from [section 5 of the
basics](basics.md#5-the-cameras-used-in-these-docs), gives only the first two
forms, colour and grey. It has no depth to report, so it never produces either
of the depth forms.

One more thing comes out of the same shot, and for a robot it is the most useful
one: a **point cloud**. A point cloud is what we get when we take every pixel
that has a depth reading and turn it into a point, with the calculation from
section 1.1. In the project, a standard ROS package called `depth_image_proc`
does this for all 76,800 pixels and publishes the result on `/camera/points`.
It leaves the points measured from the camera, and RViz moves them into the room
using TF, exactly as section 1.2 describes. Here are two points, worked out with
the calculation from section 1.1 and moved into the room:

| Landed on | x | y | z |
| --- | --- | --- | --- |
| the table, at pixel (0.5, 0.5) | −0.230 | 0.172 | 0.000 |
| the red box, at pixel (212.5, 86.5) | 0.064 | 0.041 | 0.060 |

In every point, `z` is the height of whatever that pixel landed on, which is 0
for the table and 0.060 for the red box. This is the form the rest of a robot
wants, because a picture is a grid of directions, while a point cloud is a
collection of places, and places can be grouped, measured and picked up. This is
also where a colour-only camera falls short: the Raspberry Pi camera has no depth
reading for any of its pixels, so it cannot make a point cloud on its own.

A real depth camera never fills in every pixel. Shiny, dark or see-through
surfaces, and anything too near or too far away, come back with no reading at
all. Gazebo's camera fills in every pixel in this scene, but the project's code
still treats a missing reading as missing: `depth_to_points()` keeps it as NaN,
and `measure_box()` leaves NaN points out, rather than filling them with a
made-up value, because a made-up value would put a surface where there is none.

### 1.4 The box, measured

Everything is now in place to measure the box. Section 1.1 showed how to turn one
pixel into a point measured from the camera, and section 1.2 showed how to move
that point into the room, so measuring the whole box needs only four steps.

The first step is to turn every pixel into a point in the room, using the
calculations from sections 1.1 and 1.2. The second step is to keep only the
points that stand more than a centimetre above the table. With one box on the
table, those are the points on the box: 2,582 of them. They are a few fewer than
the 2,624 readings that landed on the box, because the lowest part of its side
is less than a centimetre above the table, and it is left out along with the
table. The third step is to keep only the highest of those points, the ones
within a millimetre of the highest, because those are the top of the box. This
step is needed because the thin strip of the box's side from
[section 4 of the basics](basics.md#4-getting-distance-back-the-depth-picture)
also stands above the table, but lower than the top. That leaves 2,401 points:
the 2,352 on the top itself and 49 from the very top of the side. The fourth step
is to average the points that are left. The average position of the top is the
middle of the box, and the height of the top is how tall the box is.

Nothing about the box was looked up along the way. The answer comes only from the
depth readings, the four lens numbers, and where the camera was.

The table below compares the answer with the true values, which we know because
we built the scene. Positions are in metres from the middle of the table, which
is the spot straight under the camera.

| Box | Measured middle | True middle | Measured height | True height |
| --- | --- | --- | --- | --- |
| red | (+0.064, +0.040) | (+0.065, +0.040) | 0.060 m | 0.060 m |

The middle is within a millimetre of the truth, and the height is exact, so the
red box has been measured from one picture. In the project, this calculation is
`measure_box()` in `camera_one_box/measure.py`. The `box_locator` node runs it
on every picture the camera sends, prints the answer in the terminal, and
publishes it for the rest of the robot. The [code doc](one-box-code.md) shows
the same four steps as pseudo code and as Python.

---

## 2. Vocabulary

| Term | Full name | Meaning |
| --- | --- | --- |
| deprojection | — | pixel and depth in, 3D point out: the reverse of taking a picture |
| pose | — | where the camera is, and which way it points |
| camera_to_world | — | the pose, as a table of numbers |
| point cloud | — | a collection of 3D points, made from a depth picture |
| encoding | — | what the numbers in an image message mean: `rgb8`, `32FC1`, and so on |
| optical frame | — | the camera's picture-matching axes: X right, Y down, Z forward |
| TF | transform | the part of ROS that keeps track of where every frame is |

Next: [the code](one-box-code.md), which does these calculations in Python.

Previous: [the basics](basics.md), which explain what a camera records and the
four numbers that describe its lens.
