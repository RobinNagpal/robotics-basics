# Edges and contours

This page explains how a program finds the outline of an object in a picture,
and what it can learn from that outline. It answers five questions. What is an
edge, and how is it computed? How does the Canny edge detector turn a noisy
picture into thin, clean lines? How does a program walk round the outline of a
blob and store it as a list of points? How does it turn that list into a
polygon with a few corners? And how does it count the corners, or fit a known
shape, to say "this is a triangle" or "this is a circle"?

It is for a reader who knows what a pixel and a grey picture are, and who has
read [thresholding and colour masks](02_thresholding-and-colour-masks.md). That
page explains how to turn a picture into a **mask**: a picture where each pixel
is either "object" or "not object". This page often starts from such a mask.
The page on [morphology and the distance transform](03_morphology-and-distance-transform.md)
explains how to tidy a mask before you trace its outline.

On a robot arm, edges and outlines answer questions like "where exactly is the
border of this part?", "which way is this block turned?" and "is this block a
hexagon or a circle?". They cost a few milliseconds and need no training data.

## Contents

1. [The idea in one sentence](#1-the-idea-in-one-sentence)
2. [How it works](#2-how-it-works)
   · [Step 1: the gradient of a picture](#step-1-the-gradient-of-a-picture)
   · [Step 2: the Canny edge detector](#step-2-the-canny-edge-detector)
   · [Step 3: tracing a contour](#step-3-tracing-a-contour)
   · [Step 4: simplifying the contour to a polygon](#step-4-simplifying-the-contour-to-a-polygon)
   · [Step 5: counting corners and fitting shapes](#step-5-counting-corners-and-fitting-shapes)
3. [Where it is used on a robot arm](#3-where-it-is-used-on-a-robot-arm)
4. [Where it works, and where it does not](#4-where-it-works-and-where-it-does-not)
5. [Libraries that provide it](#5-libraries-that-provide-it)
6. [Why edges and contours, and what they cost](#6-why-edges-and-contours-and-what-they-cost)
7. [Where to read next](#7-where-to-read-next)

---

## 1. The idea in one sentence

An **edge** is a place in a picture where the brightness changes sharply, and a
**contour** is the closed line you get by following the edge all the way round
one object.

Here is an everyday example. Put a white plate on a dark wooden table and look
at it. Your eye finds the plate's rim at once, because on one side of the rim
everything is dark and on the other side everything is bright. If you traced the
rim with a pencil on a photo, you would draw its contour. If someone then asked
"is the plate round or square?", you would look at the traced line and count its
corners. A program does the same three things, in the same order.

---

## 2. How it works

The work has five steps. The first two find edges in a grey picture. The last
three start from a mask, trace its outline and describe its shape. A real
program often uses only some of them. For example, a program that already has a
clean mask from a colour threshold skips steps 1 and 2.

### Step 1: the gradient of a picture

The **gradient** of a picture at a pixel is an arrow. It points in the direction
in which the brightness rises fastest. Its length says how fast the brightness
rises there. In a flat area the arrow has length zero. On an edge it is long.

A program cannot measure a slope at one pixel, so it compares neighbours. The
most common way is the **Sobel operator**. It looks at the 3 by 3 patch of
pixels round the pixel it is working on, and it multiplies the patch by two
small tables of weights. One table measures the change from left to right. The
other measures the change from top to bottom. The two tables are:

```
change left to right (gx)      change top to bottom (gy)
   -1   0  +1                     -1  -2  -1
   -2   0  +2                      0   0   0
   -1   0  +1                     +1  +2  +1
```

To get `gx`, multiply each weight by the pixel under it and add the nine
results. Do the same with the second table to get `gy`. The length of the arrow
is `sqrt(gx² + gy²)`, and its direction is the angle of the point `(gx, gy)`.
The middle row and column carry a weight of 2 because the pixels right next to
the centre are the best evidence of what happens at the centre.

Here is a worked example. The picture below is 8 pixels wide and 8 high. A
bright square with brightness 200 sits on a dark table with brightness 20.

![An 8 by 8 picture of a bright square, and the gradient arrow at each pixel](../../images/image-and-point-cloud-processing/edges-and-contours/gradient-arrows.svg)

The left panel shows the brightness numbers, and the right panel shows the
gradient that the Sobel operator computes at every pixel.

Take the pixel in row 3, column 1. It is dark, and its right-hand neighbour is
bright. The orange box marks its 3 by 3 patch. Each row of the patch reads
20, 20, 200. For `gx`, each row gives `−20 + 0 + 200 = 180`, and the middle row
counts twice. So `gx = 180 + 2 × 180 + 180 = 720`. For `gy`, the top row and the
bottom row are the same, so they cancel and `gy = 0`. The arrow has length 720
and points straight to the right, towards the bright square.

The pixel in row 3, column 3 sits inside the square. Its whole patch reads 200,
so both sums are 0 and it gets no arrow. The pixel on the square's top-left
corner, row 2, column 2, gets `gx = 540` and `gy = 540`. Its arrow has length
763.7 and points diagonally down and to the right, into the square. These
numbers come from running the Sobel operator in NumPy on this exact picture.

Notice two things in the right panel. First, the arrows sit on both sides of the
real border, so a raw gradient gives an edge two pixels thick. Second, the
arrows always point across the edge, never along it. Canny uses both facts.

### Step 2: the Canny edge detector

The **Canny edge detector**, published by John Canny in 1986, is the standard
way to turn a gradient into thin edge lines one pixel wide. It has four steps.

1. **Blur** the picture a little with a Gaussian blur. A **Gaussian blur**
   replaces each pixel by a weighted average of the pixels round it, with the
   nearest pixels weighted most. This removes single-pixel noise, which would
   otherwise give strong gradients everywhere.
2. **Compute the gradient** at every pixel with the Sobel operator.
3. **Thin the edges.** Look at each pixel's two neighbours across the edge, in
   the direction of its gradient arrow. Keep the pixel only if its gradient is at
   least as long as both of theirs. Otherwise set it to zero. This step is called
   **non-maximum suppression**. It leaves only the ridge of each thick band.
4. **Keep strong edges, and weak edges that touch them.** Use two thresholds, a
   high one and a low one. A pixel above the high threshold is a **strong** edge
   and is kept. A pixel between the two is a **weak** edge. It is kept only if it
   is connected, through other kept pixels, to a strong edge. Everything below
   the low threshold is dropped. This step is called **hysteresis
   thresholding**.

The two thresholds in step 4 are the reason Canny works so well. A real edge
often has a strong part and a faint part, for example where a shadow falls on
it. A single high threshold would break the edge at the faint part. A single low
threshold would also keep every patch of noise. The two thresholds together keep
the whole of a real edge and drop noise that stands alone.

The picture below shows the four steps on a 64 by 96 picture with a lot of
noise. A dim triangle (brightness 130) and a bright turned square (brightness
200) sit on a table of brightness 60.

![The four steps of the Canny detector on a noisy picture of a triangle and a square](../../images/image-and-point-cloud-processing/edges-and-contours/canny-steps.svg)

Each panel is the real output of that step, computed in NumPy with a Gaussian
blur whose spread (its standard deviation, called sigma) is 1 pixel, a low
threshold of 80 and a high threshold of 200.

The numbers tell the story. A single threshold of 80 on the gradient keeps 1,185
pixels. They form thick bands round both shapes, plus many specks of noise.
After thinning, 515 pixels above 80 remain. Of these, 163 are strong. The other
352 are weak. Hysteresis keeps 76 of the weak pixels, because they touch a
strong chain, and drops the other 276. The final result has 239 edge pixels. In
the last panel the kept weak pixels are blue. They lie almost all on the dim
triangle, whose edge is too faint in places to be strong. The dropped weak
pixels are light grey. They are scattered noise.

In pseudocode, Canny is:

```
function canny(image, blur_width, low, high):
    smooth = gaussian_blur(image, blur_width)
    for each pixel p:
        gx, gy = sobel(smooth, p)
        size[p] = sqrt(gx*gx + gy*gy)
        direction[p] = angle(gx, gy) rounded to 0, 45, 90 or 135 degrees

    for each pixel p:                              # thin
        a, b = the two neighbours of p along direction[p]
        ridge[p] = size[p] if size[p] >= size[a] and size[p] >= size[b] else 0

    edge = all pixels with ridge >= high           # strong
    queue = list of those pixels
    while queue is not empty:                      # grow into weak pixels
        p = take one from queue
        for each of the 8 neighbours n of p:
            if ridge[n] >= low and n not in edge:
                add n to edge and to queue
    return edge
```

### Step 3: tracing a contour

Edges are loose pixels. To describe an object, a program needs its outline as
one list of points in order. This list is the **contour**.

Contours are usually traced from a mask, not from Canny edges. A mask's outline
is always closed, while an edge line can have gaps. The usual method is **border
following**, also called **Moore-neighbour tracing**. It works like a person
walking round a pond while keeping one hand on the fence.

1. Scan the mask row by row from the top. The first object pixel you meet is on
   the outline. Call it the start.
2. Stand on the current pixel. Look at its 8 neighbours one by one, turning
   clockwise, beginning just after the pixel you came from.
3. The first object pixel you meet is the next outline pixel. Step onto it.
4. Repeat until you come back to the start pixel, arriving the same way as the
   first time.

The result is a list of pixel positions in walking order. The picture below
shows it for a mask of a hexagonal block.

![A mask, its traced outline, and the polygon that simplifies it](../../images/image-and-point-cloud-processing/edges-and-contours/outline-to-polygon.svg)

The middle panel shows the 130 outline points the trace found, and the right
panel shows the 6 corners that step 4 keeps from them.

A contour gives several useful numbers straight away. Its **area** is the number
of pixels inside; here it is 1,624. Its **perimeter** is the length of the line
through the outline points; here it is 154.0 pixels. Its **centroid**, the
average position of the pixels inside, is a good point to aim the gripper at for
a compact object. Book 2 uses exactly these numbers in
[the biggest blob, and its middle](../../02_perception/01_camera/02_finding-objects.md#34-the-biggest-blob-and-its-middle).

A mask can hold several objects, and an object can have a hole, such as a washer.
Real contour functions handle both. They return one contour per outline, and
they record which contour lies inside which. When you only want the outer
outline of each object, you ask for the outer contours only.

### Step 4: simplifying the contour to a polygon

The traced outline follows every pixel step. A hexagon's outline has 130 points,
but a person would describe it with 6 corners. The **Ramer–Douglas–Peucker
algorithm** (RDP) removes the points that are not needed. It keeps a point only
if leaving it out would move the line by more than a chosen **tolerance**.

For an open line it works like this.

1. Draw a straight line from the first point to the last point.
2. Find the point that lies farthest from that line.
3. If that distance is less than the tolerance, the straight line is good
   enough. Keep only the two end points.
4. Otherwise keep the farthest point, and repeat the whole method on the part
   before it and the part after it.

A contour is closed, so it has no first and last point. The usual fix is to cut
the loop in two at two points far apart, simplify each half, and join them. The
code behind the pictures on this page starts at the outline point farthest from
the centroid, because that point is almost always a real corner.

```
function simplify(points, tolerance):              # open line
    a = first point, b = last point
    far = the point in points farthest from the line a-b
    if distance(far, line a-b) <= tolerance:
        return [a, b]
    left  = simplify(points from a to far, tolerance)
    right = simplify(points from far to b, tolerance)
    return left without its last point, then right
```

The tolerance is the one setting that matters. A common choice is 2% of the
contour's perimeter, so the setting grows with the object's size in the picture.
For the hexagon that is 0.02 × 154.0 = 3.08 pixels, and it gives 6 corners.

The table below shows how the number of corners changes with the tolerance, for
the hexagon and for a circle of about the same size. Read each row as "with this
tolerance, the program would report this many corners".

| tolerance, as a share of the perimeter | hexagon corners | circle corners |
|---|---|---|
| 0.5% | 12 | 16 |
| 1% | 6 | 16 |
| 2% | 6 | 8 |
| 5% | 6 | 4 |
| 10% | 4 | 4 |

The hexagon gives 6 corners over a wide range, from 1% to 5%. That wide, flat
range is the sign of a real corner count. The circle has no real corners, so its
count keeps falling as the tolerance grows. At 5% it would even pass for a
square. So corner counting alone cannot tell a circle from a polygon. The next
step adds a second measure.

### Step 5: counting corners and fitting shapes

Once a program has the polygon, naming the shape is simple for flat, straight
sided parts. Three corners is a triangle. Four corners is a square or a
rectangle; the side lengths and angles tell which. Six corners is a hexagon.

Round shapes need a different test. The usual one is **roundness**, also called
**circularity**: `4π × area / perimeter²`. It is 1 for a perfect circle and
smaller for any other shape. A perfect square gives 0.79 and a perfect
equilateral triangle gives 0.60.

The picture below runs steps 3 to 5 on four masks of the same size.

![Four shapes, their simplified polygons, the number of corners and the roundness](../../images/image-and-point-cloud-processing/edges-and-contours/counting-corners.svg)

Each title is the corner count at 2% tolerance, and each caption is the measured
roundness.

The measured roundness values are 0.56, 0.69, 0.83 and 0.90. They are lower than
the perfect values, because a traced outline steps from pixel to pixel and so is
a little longer than the true smooth outline. The order is still right, and the
circle stands clearly apart. A rule such as "roundness above 0.87 means round,
otherwise count the corners" sorts all four shapes correctly here. On your own
camera you would measure the values on real parts before choosing that number.

For a round object you usually want its centre and radius, not a corner count.
A **least-squares circle fit** finds the circle that passes closest to all the
outline points at once. It is explained on the
[least-squares fitting](../04_fitting-and-estimation/02_least-squares-fitting.md)
page. Run on the circle's 128 outline points, it gives a centre of (30.0, 30.0)
and a radius of 22.56 pixels. The mask was drawn with its centre at (30, 30) and
a radius of 23 pixels. The fit is half a pixel small because the traced points
are the centres of the outer ring of pixels, which lie half a pixel inside the
true edge. This is a real effect worth knowing when you turn pixels into
millimetres. The dashed blue line in the picture is this fitted circle.

Other fits work the same way. A program can fit the smallest turned rectangle
round a contour, to learn a part's length, width and angle. It can fit an
ellipse, to learn how a round rim is tilted. It can compute the **convex hull**,
the outline you get by stretching a rubber band round the contour, and compare
its area with the contour's area to find dents and notches.

---

## 3. Where it is used on a robot arm

Edges and contours turn up at many points in an arm's software. Here are some
concrete places.

- **Sorting blocks by shape.** A camera looks down at blocks on a table. A
  threshold gives a mask, the contour gives a polygon, and the corner count and
  roundness give the shape. The robot-arm-projects repository does exactly this
  in its
  [find-shape-and-mass project](https://github.com/RobinNagpal/robot-arm-projects/blob/main/v4-find-shape-and-mass/README.md),
  where it uses it as the score a trained detector must beat.
- **Finding which way a part is turned.** The smallest turned rectangle round a
  contour gives the angle of a long part, such as a pen or a bolt. The wrist then
  turns by that angle, so that the gripper fingers close across the part's width.
- **Measuring a part before grasping it.** The contour's width in pixels, with
  the depth and the camera's focal length, gives the width in millimetres. The
  [pinhole camera model](../02_geometry-and-cameras/02_pinhole-camera-model.md)
  page explains that conversion. The program then checks that the part fits
  between the gripper fingers.
- **Checking a part against a drawing.** For flat parts, such as gaskets or
  sheet metal blanks, the contour can be compared with the outline in a
  drawing. Holes, burrs and missing corners show up as differences.
- **Finding printed markers.** Square fiducial markers, such as the ArUco
  markers used for calibration, are found by looking for contours whose polygon
  has exactly four corners. The
  [calibration](../02_geometry-and-cameras/04_calibration.md) page uses them.
- **Finding the rim of a cup or bowl.** An ellipse fitted to the rim's edge
  tells the program where the opening is and how it is tilted, which matters for
  pouring into it or for grasping it by the rim.
- **Checking the result of a place.** After placing a part in a tray, the arm
  takes a picture. A small gap between the part's contour and the tray pocket's
  contour means the part sits correctly.

---

## 4. Where it works, and where it does not

Edges and contours work best when the object is flat or seen straight from
above, has a clear border against a plain background, and does not touch
anything else. They get worse quickly as those conditions fail.

The table below lists the common failures. Read each row as: this is what goes
wrong, this is what you would see, and this is what people do instead.

| what goes wrong | the sign you would see | what people use instead |
|---|---|---|
| Low contrast between object and table | Canny finds only parts of the outline; contours come back open or too small | Better lighting, a table colour chosen to contrast, or a depth threshold instead of a brightness one |
| Textured objects or a patterned table | Hundreds of edges inside the object; no single contour is the object | A colour or depth mask first, then contours of the mask |
| Shadows | The contour includes the shadow, so the object looks bigger or the wrong shape | Diffuse lighting from several sides; a depth camera |
| Objects touching each other | Two objects come back as one contour with too many corners | The distance transform and watershed from the [morphology page](03_morphology-and-distance-transform.md), or depth clustering from the [clustering page](05_clustering.md) |
| Camera at a slant | Squares look like irregular four-sided shapes; circles look like ellipses; roundness drops | Look from straight above, or correct the view with the camera's known pose |
| A small or far object | Corners get rounded off; a hexagon reports 4 or 8 corners | Move the camera closer; use a larger tolerance only if the shapes are very different |
| Noise in the mask | A single stray pixel adds an extra corner or an extra tiny contour | An opening step on the mask, and a minimum contour area |
| See-through or shiny objects | The edge found is a reflection, not the object's border | A [segmentation model](../../06_neural-network-models/02_seeing-models/04_segmentation.md) trained on such objects |

Book 2 gives the same trade-off as five jobs these methods suit and five they
cannot do, in
[edges, contours and connected components](../../02_perception/02_object-perception/03_programmed-methods.md#13-edges-contours-and-connected-components).

---

## 5. Libraries that provide it

Every step on this page is available in well-known libraries. You rarely write
them yourself. Read the table below as: this library, used from these
languages, provides this step under this name.

| library | languages | function or class | note |
|---|---|---|---|
| OpenCV | C++, Python, Java | `cv::Sobel`, `cv::Scharr` | Gradient in x or y. Scharr is a slightly more accurate 3 by 3 version of Sobel. |
| OpenCV | C++, Python, Java | `cv::Canny` | The full Canny detector. You pass the low and high thresholds. |
| OpenCV | C++, Python, Java | `cv::findContours` | Border following on a mask. It can return outer contours only, or all contours with their nesting. |
| OpenCV | C++, Python, Java | `cv::approxPolyDP`, `cv::arcLength`, `cv::contourArea` | Ramer–Douglas–Peucker simplification, perimeter and area. |
| OpenCV | C++, Python, Java | `cv::minAreaRect`, `cv::fitEllipse`, `cv::minEnclosingCircle`, `cv::convexHull` | Fitting a turned rectangle, an ellipse, a circle round the points, and the convex hull. |
| OpenCV | C++, Python, Java | `cv::HoughLinesP`, `cv::HoughCircles` | Find straight lines and circles directly from edges, even when the outline is broken. |
| scikit-image | Python | `skimage.filters.sobel`, `skimage.feature.canny` | Gradient and Canny on NumPy arrays. |
| scikit-image | Python | `skimage.measure.find_contours`, `skimage.measure.approximate_polygon` | Contours at sub-pixel accuracy, and polygon simplification. |
| scikit-image | Python | `skimage.measure.regionprops` | Area, perimeter, centroid, orientation and other measures for each labelled blob. |
| SciPy | Python | `scipy.ndimage.sobel` | The Sobel gradient on any NumPy array, including a depth picture. |
| PCL | C++ | `pcl::BoundaryEstimation` | The 3D counterpart: marks points on the border of a surface in a point cloud. |

In OpenCV's Python interface the names start with `cv2.` instead of `cv::`, as in
`cv2.Canny`.

---

## 6. Why edges and contours, and what they cost

This section answers the four questions for this technique: what it is, what it
does for you, why it rather than the obvious alternative, and what it costs.

Edges and contours are a fixed set of rules. The gradient finds where brightness
changes, Canny thins that into lines, border following turns a mask into an
ordered outline, and polygon simplification and shape fitting describe that
outline in a few numbers.

What they do for you is give exact geometry. A contour tells you the border of
an object to within about a pixel. From it you get the area, the centre, the
angle, the width and the shape class. Every one of those numbers is easy to
check by hand, and when one is wrong you can see why by drawing the contour on
the picture.

The obvious alternative is a trained
[segmentation model](../../06_neural-network-models/02_seeing-models/04_segmentation.md)
or [object detector](../../06_neural-network-models/02_seeing-models/03_object-detection.md).
A model copes with texture, clutter and shadows that break contours. But it needs
labelled training pictures, a computer that can run it, and it can fail in ways
that are hard to explain. Choose contours when the scene is controlled: a plain
table, good light, parts that stand apart, and shapes that differ in clear
geometric ways. Choose a model when the scene is not controlled. Even then,
programs often run contour steps on the model's output mask, because the mask
still needs to be turned into a centre, an angle and a size.

The costs are these. You must control the scene, because every method on this
page depends on a clear border. You must choose thresholds: the two Canny
thresholds, the mask threshold, the polygon tolerance and the roundness cut-off.
Each one depends on the lighting and the camera, so each needs checking on real
pictures. And a contour is a two-dimensional outline. It says nothing about
height or about the parts of the object the camera cannot see.

---

## 7. Where to read next

- The next page is [clustering](05_clustering.md). It groups mask pixels into
  separate objects with connected components, and does the same for 3D points
  with Euclidean clustering and DBSCAN.
- [Thresholding and colour masks](02_thresholding-and-colour-masks.md) makes the
  masks this page traces, and
  [morphology and the distance transform](03_morphology-and-distance-transform.md)
  tidies them and splits touching objects.
- [Least-squares fitting](../04_fitting-and-estimation/02_least-squares-fitting.md)
  explains the circle and line fits used in step 5, and
  [RANSAC](../04_fitting-and-estimation/03_ransac.md) fits a shape when many of
  the edge points are wrong.
- The chapter [overview](01_overview.md) compares all the techniques in this
  chapter.
- Book 6's [segmentation](../../06_neural-network-models/02_seeing-models/04_segmentation.md)
  and [keypoints and object pose](../../06_neural-network-models/02_seeing-models/05_keypoints-and-object-pose.md)
  pages do the same jobs with learned models.
- Book 2's
  [methods you write yourself](../../02_perception/02_object-perception/03_programmed-methods.md)
  puts edges and contours next to the other programmed perception methods, and
  [finding an object in a picture](../../02_perception/01_camera/02_finding-objects.md)
  runs `findContours` on a real camera picture.
- The diagrams on this page are drawn by `docs/diagrams/image_processing_2.py`.
  Every number on the page comes from the functions in that script; run it with
  `--numbers` to print them.
