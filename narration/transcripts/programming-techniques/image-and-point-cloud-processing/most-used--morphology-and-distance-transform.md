Morphology and the distance transform. This page explains two related techniques that work on a mask. Morphology shrinks and grows a mask, so that specks go away, holes fill in, and edges become smooth. The distance transform measures, for every pixel in a mask, how far that pixel is from the nearest edge.

The page answers four questions, and the first two are about morphology: how erosion and dilation work, and why they are almost always used in pairs, as opening and closing. The other two questions are about the distance transform. So the page also asks how the transform is worked out, and what a robot arm uses it for, such as finding the most central point of a part, or separating two parts that touch.

It is for a reader who already knows what a mask is, which is a grid the size of a picture. That grid holds one where a pixel belongs to the object and zero where it does not. The page before this one, about thresholding and colour masks, explains how a mask is made, so you do not need any background in algorithms. Every example uses a small mask you can check by hand, and every number on this page came from a real run of the diagram script.

The first section gives the idea in one sentence. Each technique fits into a single sentence, and the rest of this page only fills those two sentences in. Morphology slides a small shape over the mask, and it keeps or adds each pixel depending on what the shape covers there. The distance transform writes into each mask pixel the distance to the nearest pixel that is not in the mask.

The word "morphology" means "the study of shape", and the small shape it slides is called the brush on this page. Many books call it the structuring element or the kernel instead, and it is usually a three by three square, a small disc, or a small cross.

An everyday example helps for each of them. Morphology is like trimming a hedge and then letting it grow back evenly, because the trimming removes the thin twigs that stick out. The regrowth brings the hedge back to its old size, but the twigs do not come back. The distance transform is like standing on a lawn and asking how many steps it is to the nearest flower bed. This means the middle of a big lawn is many steps from any bed, while a spot right next to a bed is only one step.

The next part explains how morphology works, starting with erosion and dilation. The one-sentence description becomes concrete as soon as you see that morphology has only two basic operations, and everything else in it is built from those two.

Erosion shrinks a mask, and it works by putting the centre of the brush on each pixel in turn. The pixel stays one only if every pixel under the brush is one, so if the brush touches even one zero, the pixel becomes zero. This means erosion peels one layer off every edge, and anything thinner than the brush disappears completely.

Dilation grows a mask, and it puts the brush on each pixel in the same way. The pixel becomes one if any pixel under the brush is one, so dilation adds one layer to every edge. This also means that gaps narrower than the brush get filled.

A diagram on the page shows both operations on a real nine by eleven mask, using a three by three square brush. That mask holds a five by five block, a thin arm one pixel wide sticking out to the right, and a single stray pixel above the arm.

The mask has 29 pixels, and the diagram shows the brush centred on a pixel at the block's left edge. That brush covers three zero pixels, so erosion removes that pixel.

After erosion, nine pixels are left, which is the three by three middle of the block, so the whole outer layer of the block has gone. The arm and the stray pixel are gone too, because they are only one pixel wide. After dilation, the mask has 67 pixels instead. Every part has grown by one pixel on every side, and the stray pixel has grown into a three by three square.

A bigger brush has a bigger effect, so a five by five square peels two layers at once. This means that running a three by three erosion twice has the same effect as one five by five erosion.

The brush does not have to be a square at all. A disc-shaped brush shrinks and grows the mask by the same distance in every direction, so round objects stay round. However, a square brush grows round objects towards a square shape. So in practice, people use a disc when shape matters, and a square when speed matters.

The page moves on to opening and closing. Erosion and dilation on their own change the size of the object, so a robot that measures a part after an erosion finds it too small. This is why the two are nearly always used in pairs.

Opening is an erosion followed by a dilation with the same brush. The erosion removes everything thinner than the brush, such as specks, thin arms, and small bumps, and the dilation then grows what is left back to its old size. However, the specks do not come back, because nothing of them survived the erosion.

Closing is a dilation followed by an erosion with the same brush. The dilation fills every hole and gap narrower than the brush, and the erosion then shrinks the object back to its old size. However, the holes stay filled, because the erosion only peels the outside edge.

Another diagram shows both of these on a real fifteen by twenty-one mask, which looks like the mask a colour threshold gives. It holds a nine by twelve part with four specks around it, two small holes where a shiny highlight broke the colour, and a one-pixel bump on the top edge.

The mask starts with 110 pixels, and opening with a three by three square removes the four specks and the bump, which leaves 105 pixels. Closing then fills the two holes, which gives 108 pixels. That is exactly the nine by twelve part, 108 pixels, with no pixel wrong.

The order matters here, because opening first removes the specks. If closing ran first, it would not remove the specks at all, and it could even join a speck to the part when the two lie close together. The second book in this series uses the same order, opening then closing, when tidying the mask.

One more useful result falls out of erosion, because the mask minus its own erosion is the outer ring of edge pixels. That ring is the outline of the object, one pixel thick. The overview uses this to draw outlines, and the page on edges and contours traces such outlines into shapes.

The next section explains how the distance transform works. Morphology tidies a mask, whereas the distance transform measures one instead. It takes a mask and gives back a grid of the same size, in which each pixel outside the mask gets zero. Each pixel inside the mask gets its distance to the nearest pixel outside the mask. This means pixels on the edge get small numbers, while pixels deep inside get large ones.

There are three common ways to measure that distance. First, the city-block distance counts steps up, down, left, or right, as a person walks along the streets of a grid-shaped town. Second, the chessboard distance also allows diagonal steps, as a king moves in chess. Finally, the straight-line distance is the ordinary distance you would measure with a ruler. It is also called the Euclidean distance.

The worked examples here use the city-block distance, because its numbers are whole steps that you can count by hand. Libraries usually give the straight-line distance instead, but the ideas behind the two are the same.

A slow way to compute the transform is to take each mask pixel, measure its distance to every outside pixel, and keep the smallest. However, that takes a long time on a big picture. So the classic fast way needs only two passes over the mask, and it was published by Rosenfeld and Pfaltz in 1966.

First, give every mask pixel a very large number, and every outside pixel zero. The first pass goes from the top-left corner, row by row, to the bottom-right corner. For each mask pixel, look at the pixel above and the pixel to the left. Set the pixel to the smaller of its own number, the pixel above plus one, and the pixel to the left plus one. The second pass goes from the bottom-right corner, backwards, to the top-left corner. For each mask pixel, look at the pixel below and the pixel to the right. Set the pixel to the smaller of its own number, the pixel below plus one, and the pixel to the right plus one.

After the first pass, every pixel knows the distance to the nearest outside pixel above it or to its left. After the second pass, it also knows about the outside pixels below it and to its right, so after both passes the number is the true distance.

The page shows a worked example on a five by five square of mask pixels, with zeros all round it. After the first pass, the numbers grow towards the bottom-right, because that pass has only looked up and to the left. The second pass then corrects the bottom and right sides, so the final grid has one on the edge, two one step in, and three in the very middle.

Those numbers are useful because the pixel with the largest distance is the most central point, which is the point deepest inside the object and furthest from every edge. It is also the centre of the largest circle that fits inside the object, and that circle's radius is the distance itself.

This matters because the obvious alternative, the centroid, can be badly wrong. The centroid is the average position of all the mask pixels, so for a round or square part it lands in the middle. However, for a bent part it can lie outside the part altogether.

A diagram shows a real U-shaped bracket seen from above, and each number in it is the city-block distance to the nearest pixel outside the bracket. The bracket has 90 pixels, and its centroid lands in the empty space between the two walls, so a suction cup sent there would touch nothing at all.

The largest distance is three steps, at two pixels where the walls meet the base, and the two tie because the bracket is the same on both sides. Either one is a safe place for a suction cup, because it is three pixels from every edge. This means a cup up to three pixels in radius fits there entirely on the part. On a real picture a pixel is often about one millimetre on the table, so the robot can read the largest cup that fits straight from the number.

The distance transform is also used for separating objects that touch. When two objects of the same colour touch, a threshold gives one patch, so grouping the mask then finds one object where there are really two. However, the distance transform can split them again.

The idea behind that is simple, because where two round objects touch, the join between them is narrow. Pixels at the join are close to an edge, so their distance is small. However, the middle of each object is far from every edge, so its distance is large. So if you keep only the pixels whose distance is large, the join falls away, and what is left is one core inside each object.

The page shows this on a real mask of two touching coins, each eight pixels in radius, with their centres fourteen pixels apart. The mask has 404 pixels in one patch, and the largest straight-line distance is 7.6 pixels, in the middle of each coin. The pixels at the join have a distance of only 5.0. Therefore keeping the pixels with at least 70 percent of the largest distance, which is 5.3, drops the join. This leaves two separate cores of 36 pixels each, one per coin.

The cores are not yet the full coins, because they are only seeds, one starting point per object. So a second step grows each seed back out to the edge of the mask, and draws a line where two seeds meet. The standard method for that step is called watershed, and it treats the distance picture as a landscape and floods it from each seed. The second book describes it in the section on watershed and GrabCut.

The 70 percent limit is a number you choose yourself, and it can go wrong in either direction. If it is too low, the join survives and the coins stay as one, and on this mask 60 percent still leaves a single core. If it is too high, a small or oddly shaped object may lose its core entirely.

The page then provides the steps for all these operations as pseudocode. It defines functions for erode, dilate, open, and close, showing how opening is just erosion followed by dilation, and closing is dilation followed by erosion. It also writes out the two-pass distance transform, the method to find the most central point by finding the largest distance, and the method to find seeds for touching objects by keeping pixels above a fraction of the largest distance. The seed-finding step uses connected components to group the cores, which is explained on the page about clustering.

The next section lists where these techniques are used on a robot arm. They appear wherever an arm works from a mask, and the page gives several concrete places.

First, opening and closing tidy a threshold's mask, so a small brush is run right after almost every colour or depth threshold. Without that step, a speck of the right colour on the table counts as an object, and a highlight on the part splits its mask in two.

Second, the distance transform chooses where to place a suction cup, because the most central point of a part's mask is the spot furthest from every edge. The distance there, turned into millimetres, says whether the cup fits. So if the largest distance is smaller than the cup's radius, the part is too narrow for that cup, and the program can say so before the arm moves.

Third, erosion keeps a grasp away from the edges, because eroding a part's mask by the width of a fingertip leaves only the places where the fingertip can land fully on the part.

Fourth, dilation grows obstacles by the size of the gripper, so on a top-down map of the table, dilating every obstacle by the gripper's radius gives the area where the gripper's centre must not go. A planner can then treat the gripper as a single point, and the planning and search chapter builds on this kind of map.

Fifth, the distance transform separates touching parts, which matters because coins, pills, fruit, and nuts in a tray often touch. It gives one seed per part, and watershed then splits the mask.

Sixth, the distance transform measures thickness, since twice the largest distance is the diameter of the largest circle that fits inside a part. This means a part that must be at least eight millimetres thick to grip can be checked with one number.

Seventh, erosion cleans up a learned model's masks. A glass-picking project uses this to erode each region from a trained segmentation model before counting its doubtful pixels. The erosion removes the thin rim of doubt that every region has along its edge. So what is left in the middle points to a second glass hiding behind the first.

Finally, erosion also draws outlines, because the mask minus its erosion is the outline of each part, one pixel thick. This is a quick way to draw what the robot found on a screen for a person to check.

The next part discusses where these techniques are useful, and where they are not. All of those uses rest on two conditions. Morphology works when the unwanted things are smaller than the objects you want, while the distance transform works best on compact objects such as discs and blocks. This means both fail in known ways, and the page provides a table of common failures.

If the brush is bigger than a thin part of the object, a handle, a wire, or a thin wall disappears, or a part with a narrow waist splits in two. Instead, people use a smaller brush, or remove specks by size with connected components.

If closing bridges the gap between two nearby objects, the object count drops by one when two parts come close. Instead, people use a smaller brush for closing, or split them with the distance transform afterwards.

If specks are bigger than the brush, small false objects survive opening. Instead, people throw away every patch smaller than a set area.

If holes are bigger than the brush, a large hole stays, and the most central point might land next to it. Instead, people use a bigger closing brush, or fill all holes inside the outer contour.

If long thin objects stand side by side, their distance transform has a ridge along each object, not a peak. Two touching ridges join, so there is only one seed. Instead, people use a different cue, such as where each object meets the table, or a segmentation model.

If a part is cut off by the edge of the picture, the most central point sits near the picture edge. Instead, people ignore parts that touch the picture edge, or move the camera.

Finally, if a mask has ragged edges from noise, the distance values near the edge jump about, and the central point moves between frames. Instead, people use opening and closing before the distance transform.

The failure with long thin objects comes from a real project, because a glass-picking project tried the distance transform and watershed on standing wine glasses seen from the side. A glass is several times taller than it is wide, so the deepest part of its mask is a line up its middle rather than a single point. When two glasses overlap in the picture, their two lines join into one, and so watershed has only one seed to work with. The project measured this across every merged pair it could produce, and watershed split only a handful of them. Instead it used the row where each glass meets the table.

On a point cloud the same ideas have their own forms. Radius outlier removal deletes points with too few neighbours within a set distance, so it removes lone points in the way that opening removes specks. Growing an obstacle in 3D is usually done with voxels, which are small cubes that divide space into a 3D grid. Each cube near an occupied cube is also marked occupied, and that is dilation on a 3D grid.

The page then lists libraries that provide these tools. Because both techniques are used so widely, they come ready-made in every image library. OpenCV provides them for C++ and Python. It has functions to erode and dilate, and a morphology function that can do opening and closing in one call. It also has functions to make square, disc-like, or cross-shaped brushes, and to calculate the city-block or straight-line distance transforms. It also includes watershed and connected components for splitting touching objects.

SciPy for Python provides binary erosion, dilation, opening, and closing that work on masks of true and false in any number of dimensions, as well as the exact straight-line distance transform. Scikit-image for Python provides morphology and watershed functions, including one to remove patches below a certain area. For point clouds, Open3D and the Point Cloud Library provide radius and statistical outlier removal, which is the point cloud form of removing specks.

A key note is that OpenCV treats a mask as zero and 255, while SciPy and scikit-image use false and true. Converting between them is one line, but forgetting it gives a mask that is all zeros or all ones.

With the libraries in hand, the remaining question is when to reach for these two techniques at all. So this section answers why you would use these techniques, and what they cost.

Morphology shrinks and grows a mask with a small brush, so it removes specks, fills holes, and smooths edges. It also keeps the object's size, because erosion and dilation are used in pairs. The distance transform gives every mask pixel its distance to the nearest edge. So it finds the most central point of a part, tells you how big a tool fits there, and gives seeds for splitting touching objects. Both run in about a millisecond on a camera picture, and both give exactly the same answer every time.

The obvious alternative to opening is to label the patches with connected components and throw away the small ones. That removes specks, and it does not change the shape of the real object at all. However, it does not fill holes, and it does not remove thin bumps attached to the object. That is why many programs use both: opening and closing with a small brush, then an area filter for anything larger that got through.

The obvious alternative to the distance transform's central point is the centroid, which is cheaper and smoother from frame to frame. It is right for round, square, and other convex parts, which have no dents or gaps. However, it is wrong for U shapes, L shapes, rings, and anything else with a gap or a hole, where it can fall off the part. This means the distance transform costs a little more, but it never chooses a point outside the mask.

The obvious alternative for splitting touching objects is a learned segmentation model, and the page takes a closer look at that alternative next. A segmentation model gives one mask per object from the start, so it splits touching objects without the distance transform and watershed. It wins on long, thin, and oddly shaped objects that defeat the distance transform, but it needs training pictures and a bigger computer.

A suction model scores every pixel for where a cup would seal, which is the job the most central point does on this page. However, plain geometry is hard to beat for suction, and a model pays off only when the geometry keeps choosing badly, such as on lumpy bags or surfaces that look flat but leak. There is no learned model that replaces opening and closing, because they are a cheap clean-up step that runs on any mask, including a model's own.

Against all that, you must choose the brush size, and that one number trades two errors against each other. A bigger brush removes more noise, but it also removes thin parts and joins close objects. The distance transform also only knows about the mask, so if the mask is wrong, its central point is confidently wrong too.

The page mentions several places to read next. The page on edges and contours traces the outline of a tidy mask and fits shapes to it. Clustering turns a mask into separate objects, and does the same for a point cloud. The page before this one, about thresholding and colour masks, makes the masks that this page tidies. Nearest-neighbour search is how radius outlier removal finds each point's neighbours. Finally, the glass-picking project's notes on splitting a blob show in detail why the distance transform fails on tall thin objects.

The final section shows how to use these techniques in Python. It brings together the OpenCV calls in order on one mask, so you can clean a mask, find the most central point of each patch, and know which numbers you have to choose from your own camera's geometry.

The code starts from a grayscale mask of the kind a threshold produces. It creates a disc-like brush, which is the usual choice because a square brush leaves square corners on round objects. It runs opening to remove specks, and then closing to fill small holes. Then it calculates the distance transform to find how far every kept pixel is from the nearest edge, and finds the brightest pixel and where it is.

On a made-up mask of two green blocks, the threshold left 8152 pixels. The opening and closing together leave 8136, and the distance transform's brightest point is 36.0 pixels from the nearest edge. That 36 pixels is the radius of the largest circle that fits inside the patch, so a suction cup narrower than 36 pixels across will land entirely on the block.

OpenCV does both techniques in one call each. You do not write the two steps for opening or closing yourself, and the distance transform does the two passes over the mask automatically.

What you still have to write is the decision about which operation to use, and in which order. Nothing in the call knows whether your problem is specks outside the object or holes inside it, and opening and closing are not interchangeable. Opening first and then closing removes specks and then fills holes, while the other order fills the specks into the object before it can remove them. You also have to convert between conventions if you mix libraries, because OpenCV works on masks of zero and 255 while SciPy and scikit-image work on true and false.

What you have to decide or measure is the brush size and the meaning of a pixel. A five by five brush says that a patch narrower than about five pixels is noise, and whether that is right depends entirely on how far your camera is from the table. The same real speck is two pixels wide from one metre, and ten pixels wide from 200 millimetres. So you work the brush size out from the camera's resolution and its distance.

The same conversion applies to the distance transform, because its output is in pixels and a suction cup is specified in millimetres. You need the millimetres per pixel at the table's distance before the 36 pixels means anything. Finally, you decide whether to use the straight-line distance or the city-block distance. The straight-line distance is almost always what you want, because the city-block distance counts diagonal steps as two and so underestimates clearance in a diagonal direction.
