Thresholding and colour masks. This page explains thresholding, which is the technique that decides whether a pixel belongs to the thing you are looking for. It makes that decision for every pixel on its own, so no pixel is ever compared with its neighbours.

The page answers four questions, and the first two are about grey pictures: how a threshold turns a picture into a mask, and how the picture itself can choose the limit. The other two questions move on to colour and depth. So the page also asks why robot programs test colour in hue, saturation and value rather than in red, green and blue, and it then shows how the same idea works on a depth picture.

It is for a reader who knows that a picture is a grid of pixels and that each pixel is stored as numbers. Beyond that you need no background in algorithms, because every example here uses a few pixels you can check by hand. Every number on this page came from a real run of the diagram script.

Thresholding is usually the first step of a hand-written perception program, so the overview of this chapter puts it first. It makes the mask that the later steps tidy, trace and group.

The whole idea fits into one sentence, and the rest of this page only fills that sentence in. A threshold compares each pixel with a fixed limit, and it writes 1 into a mask where the pixel passes and 0 where it does not.

The limit is called the threshold, and the grid of ones and zeros is called a mask. This mask has one entry for each pixel of the picture. Some libraries store 255 instead of 1 so that the mask can be shown as a black and white picture, but the meaning is the same.

For an everyday example, think of a farmer who sorts eggs by weight. Every egg goes on the scale, and the ones of 63 grams or more go in the large box while the rest go in the other box. The farmer never compares one egg with another, because each egg is tested on its own against a single number. A threshold treats pixels in exactly that way.

Moving on to how a brightness threshold works, that one-sentence idea is easiest to follow on a grey picture, which holds one number per pixel, its brightness. Brightness runs from 0 for black to 255 for white, so a bright object on a dark background is already separated by that one number.

The diagram shows a real 6 by 8 grey picture, in which a bright metal part lies on a dark rubber mat. Each square in it shows the brightness number of one pixel, alongside the mask for a brightness of 120 or more.

The rule here is brightness 120 or more, and it works cleanly because the two groups of numbers lie far apart. The mat pixels all fall between 45 and 66, so they all fail, while the part pixels all fall between 171 and 207, so they all pass. So the mask holds 13 ones out of 48 pixels, and those 13 pixels are the part.

Thresholding a whole picture takes only three steps. First, choose the limit, here 120. Second, go through the pixels one at a time. Finally, if the pixel's number is at the limit or above it, write 1 in the mask. Otherwise, write 0.

Each pixel is tested on its own, and the test never looks at the neighbours. This is why thresholding is so fast, because a computer can test a whole camera picture of 300,000 pixels in well under a millisecond.

Some programs want the dark pixels instead, for example a black part on a white tray. For them the rule becomes brightness below the limit, while other programs keep a band, with a lower limit and an upper limit. Both are the same idea pointed in a different direction.

The limit of 120 above was chosen by a person, which works only while the light stays the same. Because every number falls when the room gets darker, the part may drop to around 110, and the fixed limit then loses it.

Otsu's method chooses the limit from the picture itself, and it is named after Nobuyuki Otsu, who published it in 1979. It assumes that the picture holds two groups of pixels, a dark group and a bright group. So it tries every possible limit and keeps the one that separates those two groups best.

Separates best has an exact meaning, because for each possible limit the method splits the pixels into a dark group and a bright group. It then works out a score for that split. The score is the share of pixels in the dark group, multiplied by the share of pixels in the bright group, multiplied by the squared difference between the bright group's average and the dark group's average.

The score is large when the two averages are far apart and when neither group is tiny. So the method simply keeps the limit with the largest score.

Here is a small worked example with 14 pixel values, taken along one line across a mat and a part. The values start low around 48, rise through 85 and 110, and end high around 201. The value 110 is a pixel on the edge of the part, so it is half mat and half part. This means the method has to decide which of the two groups it belongs to.

The table shows the score for some of the possible splits. If you put every value up to 85 in the dark group, and the rest in the bright group, the score is 2,978. But if you split between 110 and 150, the score is 3,143, which is the highest score in the table. For this best split, the score is 8 over 14, multiplied by 6 over 14, multiplied by the squared difference of 181.2 and 67.9. So Otsu's method puts the edge pixel 110 with the mat, and the six values from 150 upwards with the part. Any limit between 111 and 150 gives that same split.

A real picture has thousands of pixels, so the method works on a histogram instead. A histogram counts how many pixels have each brightness from 0 to 255. This means the method only has to try 255 splits, whatever the size of the picture.

The diagram shows a histogram of a 60 by 80 picture that holds a bright part on a dark mat, with some camera noise, and it has two humps. Below it is the score curve for every possible cut, and the highest score is at 119, in the empty gap between the humps. So 119 is the limit that Otsu's method returns. The score curve is almost flat across that gap, which is good news. This means a small change in the picture moves the limit a little, but the mask hardly changes.

Otsu's method has no number for you to choose, and that is its main strength. Its main weakness is the assumption that there are only two groups. So if the picture holds three groups, for example a dark mat, a grey part and a white label, the method still returns a single limit. This means it may cut through the wrong gap.

The next section covers colour and depth thresholds. Brightness is enough for a part that is plainly lighter or darker than its background, but many parts are picked out by their colour instead. A colour pixel is usually stored as three numbers, how much red, green and blue it has, and each of them runs from 0 to 255. This way of storing a colour is called RGB.

However, RGB is a poor way to ask if a pixel is red, because when the light gets weaker all three numbers fall together. A red block might be 200, 40, 40 in the light and 100, 20, 20 in shadow. So a rule such as red above 150 finds the first and misses the second.

So robot programs convert each pixel to HSV first, which stands for hue, saturation and value. HSV describes the same colour with three more useful numbers.

First, hue says which colour it is, going round a colour circle. In OpenCV, the most used vision library, hue runs from 0 to 179 so that it fits in one byte. Red is near 0, green near 60 and blue near 120. Second, saturation says how strong the colour is, from 0 to 255. Grey, white and black have saturation 0. Finally, value says how bright the pixel is, from 0 to 255.

In shadow, a red block keeps its hue and its saturation, and only its value falls. This is exactly why splitting the colour into three numbers helps. The table shows the numbers for six pixels, comparing a rule looking for red above 150 against an HSV rule looking for red hues with high saturation and value.

The RGB rule makes two mistakes, because it loses the shadowed red block whose red number drops to 100, and it accepts a white sheet of paper, whose red number is also high at 235. The HSV rule makes neither mistake, since it looks at hue for the colour and at saturation to throw out grey and white. It then looks at value only to throw out pixels that are too dark to judge.

The table also shows a quirk of red, which sits at both ends of the hue circle, just above 0 and just below 179. So a slightly bluish red has hue 176 rather than 2. This means a red rule needs two hue ranges, where every other colour needs only one.

The diagram shows a 14 by 20 pixel picture of a red block half in shadow, alongside the RGB mask and the HSV mask. The red block covers 80 pixels. The RGB rule keeps only the 40 lit pixels, while the HSV rule keeps all 80. The green block is also in the shadow, and neither rule keeps it, because both rules are looking for red.

A colour mask has six numbers to choose, a lower and an upper limit for each of hue, saturation and value. So it takes more tuning than a brightness threshold, which has only one. People usually find the six by pointing at the object in a few pictures and reading off its HSV numbers, then leaving some room on each side.

Colour separates a part from its background only when the two differ in colour, whereas a depth camera separates them by distance instead. A depth camera gives a depth picture, in which each pixel holds a distance from the camera, often in millimetres. So a depth threshold keeps the pixels whose distance is inside a range.

The most common use is to keep everything nearer than the table. For example, imagine a camera looking straight down at a table 600 millimetres away. Anything standing on that table is nearer than 600, so the rule distance below 590 keeps every object taller than about 10 millimetres, whatever its colour.

A depth picture has one trap, which is that most cameras write 0 wherever they could not measure. This happens on glass, on shiny metal, on very dark surfaces and along the edges of objects. A reading of 0 would pass the test below 590, because 0 is below 590, so the rule must also say above 0.

The diagram shows one real row of 14 depth pixels, the cut at 590 millimetres, and the mask for the row. The table pixels read 599 to 602 and two objects read between 520 and 538. Pixel 6 reads 0, because the camera saw nothing there. With the rule above 0 and below 590, the mask keeps 6 of the 14 pixels. Without the above 0 part it would keep 7, and pixel 6 would count as an object right next to the camera.

However, a missing reading is not always noise to throw away. A patch of zeros shaped like a glass, with the glass clearly visible in the colour picture, is a strong sign of a transparent object. Book 2 uses this in the depth hole, for glass and chrome, where the threshold is simply reading equals 0.

A fixed limit such as 590 only works if the camera looks straight down at a flat table. That is because a tilted camera sees the table nearer at the top of the picture than at the bottom. So the usual fix is to turn the depth picture into a point cloud, find the table plane with RANSAC, and keep the points higher than 10 millimetres above that plane. This is the same threshold, measured from the table instead of from the camera.

The three kinds of threshold described above can be written out as plain steps in pseudocode. For a brightness mask, you create a grid of zeros, loop through each pixel, and write a 1 if the pixel's brightness is at or above the limit. For Otsu's limit, you count how many pixels have each brightness, then test every limit from 1 to 255 to find the one that gives the highest score based on the averages of the dark and bright groups. For a red mask, you convert each pixel to hue, saturation, and value, and write a 1 if the hue is in the red ranges and the saturation and value are high enough. For a depth mask, you write a 1 if the depth is greater than zero and falls between the near and far limits.

Real libraries do not loop over pixels one by one in slow code. Instead they run the same test on the whole grid at once, in fast compiled code, and the result is the same.

Now that all three kinds of threshold are on the table, it is worth seeing where they actually turn up on a robot arm. Thresholding appears in almost every hand-written perception program on an arm, and there are several concrete places it is used.

First, a coloured part is found with a colour mask, so a red block, a blue bin or a green marker on a table is picked out by an HSV mask. The middle of the mask, together with the depth at that pixel, gives the point the arm reaches for, and Book 2 runs this end to end in finding it by colour.

Second, anything that stands on the table is found with a depth threshold, because a threshold measured from the table plane keeps every object whatever its colour. This is the first step of the classic remove the plane, then cluster recipe, described in Book 2.

Third, the point cloud is cropped to the workspace by a box-shaped threshold on x, y and z, which keeps only the points inside the arm's reach. It throws away the floor, the walls and the robot's own base, and so it makes every later step faster.

Fourth, a depth threshold checks that the gripper holds something, because a wrist camera looks between the fingers and the program counts the depth pixels nearer than the fingertips inside a small window. If that count is above a limit, then something is in the gripper.

Fifth, Otsu's method suits parts on a backlit tray, since a light box under the tray makes every part a dark shadow on a white background. Otsu's method then finds the limit on its own, even as the lamp ages and dims.

Sixth, a depth threshold notices a person entering the cell, because a fixed overhead depth camera watches the cell all the time. If more than a set number of pixels become nearer than the empty floor, then something has entered, and the arm slows down or stops.

Finally, a threshold turns a learned model's scores into a mask, because a segmentation model gives each pixel a number from 0 to 1 saying how sure it is that the pixel belongs to an object. A threshold, often 0.5, turns that into a mask, so even a learned pipeline ends in a threshold.

All of those uses share one condition, which is that a single simple number separates the object from everything else. That number is its brightness, its colour or its height. So thresholding fails whenever no such number exists, and there are common failures and fixes.

If the light changes, for example daylight through a window, the mask shrinks or grows during the day, and the part is lost in the evening. Instead, people use HSV, Otsu's method, a controlled lamp, or a depth threshold.

If the light is uneven, bright on one side of the table and dark on the other, Otsu's limit is right on one side and wrong on the other. The fix is an adaptive threshold, which picks a separate limit for each small area of the picture.

If the object is the same colour as the background, such as a white mug on a white table, the mask is empty or covers the whole table. Here, a depth threshold or a segmentation model is used.

If two objects of the same colour touch, you see one patch in the mask where there should be two. People fix this with the distance transform and watershed, or 3D clustering.

If there is a shiny highlight on the object, it leaves a hole in the middle of the mask, which can be filled using a technique called closing.

Camera noise near the limit leaves single specks scattered across the mask, which can be fixed by opening, or a small blur before the threshold.

For glass, mirrors and polished metal, you get zeros in the depth picture, and colour taken from whatever is behind. The solution is to treat the zeros as a signal, or use a learned depth model such as depth from pictures.

Finally, if there are many kinds of object, each a different colour, you would need one mask per colour and a new rule every time a new part arrives. In this case, people use a trained object detector. Book 2 lists these same failures from the other side in when colour stops working.

Because those failures and their fixes are so well known, they are already built into the standard libraries. So you rarely write a threshold yourself, apart from the one-line comparison. Well-known libraries provide thresholds out of the box.

In OpenCV for C++ and Python, you can use the threshold function with a binary flag, and add an Otsu flag for Otsu's method, though it needs an 8-bit grey picture. OpenCV also has an adaptive threshold function for uneven light. For colour, you can use OpenCV to convert to HSV and then use its in-range function, keeping in mind that OpenCV reads pictures as blue, green, red, and its hue runs from 0 to 179.

In Python's scikit-image, there are functions for Otsu's threshold and RGB to HSV conversion, but its HSV numbers run from 0 to 1, not 0 to 179 and 0 to 255.

In NumPy, a threshold is just one line using comparison operators, which results in an array of true and false.

For point clouds, Open3D has a crop function with a bounding box, and the Point Cloud Library in C++ has a pass-through filter that keeps points whose x, y or z is inside a range.

When you copy HSV limits from one library to another, check the scale first. This matters because a hue of 0.5 in scikit-image is a hue of 90 in OpenCV.

With the libraries in hand, the remaining question is when to reach for thresholding at all. It is a test applied to each pixel on its own, against a fixed limit or a range. This turns a picture into a mask of the pixels that might be the object. It runs in well under a millisecond, needs no training and no graphics card, and gives the same answer every time for the same picture. So when it goes wrong, you can find out why by reading one pixel's numbers.

The obvious alternative is a learned segmentation model, which is discussed next.

The second obvious alternative is to skip the mask and go straight to 3D clustering. But clustering needs a depth camera, and it still needs a threshold first to remove the table. So in practice the two are used together rather than one instead of the other.

Against all that, you must choose the limits, and a colour mask has six of them, so there is real tuning work before anything runs. Because those limits are tied to the light, the camera and the objects, they need checking again whenever one of those three changes. A threshold also only says might be the object. So it cannot tell two touching objects apart, and it cannot say what an object is.

That first alternative is worth a closer look, because Book 6 has two kinds of model that do this same job. A segmentation model marks the pixels of each object without any hand-set limits, and an object detector puts a named box round each object. A model wins when you cannot control the scene, because it handles mixed colours, clutter and changing light much better. It also copes with many kinds of part without a new rule for each one. However, a threshold still wins when the object has a property that nothing else in the scene shares. That property may be a colour you chose, a height above a known table, or a brightness against a backlit tray. In a robot cell you often control these things, so a threshold is the right answer more often than its simplicity suggests.

The page then lists where to read next. This includes morphology and the distance transform, which removes the specks and fills the holes that a threshold leaves behind. It mentions clustering, which turns a mask into separate objects, and does the same for a point cloud. It points to RANSAC, which finds the table plane that a height threshold is measured from, and the pinhole camera model, which turns the middle of a mask into a 3D point. It also links to other pages with real code for an HSV mask and a summary of colour ranges.

The final section explains using it in Python. It puts the OpenCV calls into a program so you can turn a picture into a mask in three lines, and know which numbers you have to measure in your own workcell.

The code makes two masks from the same picture. First, it loads a picture and converts it to greyscale. It then uses OpenCV to apply Otsu's method, which automatically finds the best brightness limit and returns both that limit and the resulting mask. Next, it creates a colour mask by converting the original picture to HSV. It uses an OpenCV range function to keep only the pixels where the hue is between 40 and 80, which is green, and where the saturation and value are high enough to be reliable. Finally, it demonstrates a depth threshold by loading a depth picture in metres and using standard math operations to keep only the pixels that are between 0.30 and 0.70 metres away.

On a made-up 320 by 240 picture of two green blocks on a grey table, Otsu's method picks a limit of 138 and marks 68,457 pixels as bright, which is the table and not the blocks, because the table is the brighter of the two. The colour mask keeps 8,152 pixels, which is the two blocks. That difference is the whole argument for colour masks: brightness alone cannot tell a green block from a grey table of similar brightness, and colour can.

OpenCV does the per-pixel comparison and, for Otsu's method, the search for the limit as well. The threshold function returns two values, and the first is the limit it chose, which is worth printing because a limit that jumps between pictures tells you the lighting is changing. The in-range function tests all three channels at once and returns a mask of 0 and 255, and the logical AND on the depth arrays is NumPy doing the same thing on true and false values. The last line shows why the depth version needs no library at all: a comparison on a NumPy array already is a threshold.

What you still have to write is what happens to the mask. A mask is not an answer, because it is a picture of true and false values, and the arm needs a position. Morphology cleans the mask and clustering turns it into separate objects with centres, and those two steps almost always follow this one.

What you have to decide or measure is the limits, and this is the part that decides whether the mask works tomorrow as well as today. The hue range of 40 to 80 is a claim about your lighting and your camera, so you measure it by opening real pictures of your own workcell and reading the hue values off the pixels you want to keep. The saturation floor of 80 and the value floor of 40 matter just as much, because a very pale or very dark pixel has an unreliable hue, and leaving those floors at 0 is the usual reason a colour mask picks up half the room. For the depth mask you decide 0.30 and 0.70 metres, which are distances in your own camera's frame, so moving the camera changes them. Otsu's method looks like it removes the decision, but it only moves it: it assumes the picture has two groups of brightnesses, and earlier sections explain what it returns when that assumption is false.
