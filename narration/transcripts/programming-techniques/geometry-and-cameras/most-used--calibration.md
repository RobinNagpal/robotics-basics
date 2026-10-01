Calibration. This page explains calibration as a technique you can use in any program, and it covers the two calibrations that every arm with a camera needs. Intrinsic calibration measures the camera's lens numbers from pictures of a printed checkerboard, while hand-eye calibration measures where the camera sits relative to the arm. The page then answers four questions about both of them. What exactly is being measured? How does the method find it? How many pictures are enough, and which ones? And how do you know the answer is right?

It is for a reader who has read the two pages before this one: the page on the pinhole camera model, which uses the lens numbers, and the page on rigid transforms, which uses the camera's pose. Book 2 explains why calibration matters so much in the section on calibration, which decides all of it, while this page explains how it works inside.

The first section gives the idea in one sentence. Photograph something whose shape you know exactly, then choose the unknown numbers so that the model predicts the pictures you really took.

Here is an everyday example. To check a kitchen scale, you put a bag of sugar on it that you know weighs exactly one kilogram, so if the scale reads 1.03 kilograms you now know how far off it is. Calibration does the same with a camera, where the bag of sugar is a printed board whose corners are at known places, and the reading is where those corners land in the picture.

Both calibrations on this page follow that idea, and they differ only in what is known and what is unknown. Intrinsic calibration knows the board and finds the lens, while hand-eye calibration knows the lens and the arm's movements, and finds the fixed transform between the arm's flange and the camera.

The next part of the page explains intrinsic calibration, which finds the lens numbers. The previous section said that calibration photographs something known, and the first of the two calibrations photographs a board to learn about the camera. Intrinsic calibration finds the numbers that belong to the camera itself and do not change when the camera moves. They are the four lens numbers from the pinhole camera model, f x, f y, c x, and c y, plus the lens's distortion, which is how much it bends straight lines.

The usual distortion model has five numbers, and they fall into two kinds. First, three of them, k 1, k 2, and k 3, describe radial distortion, which moves each point towards or away from the middle of the picture by an amount that grows with the distance from the middle. Second, the other two, p 1 and p 2, describe tangential distortion, which comes from a lens that is slightly tilted relative to the sensor, and which is usually tiny. Book 2 shows the five numbers arriving in ROS's CameraInfo message, as the field d, in the ROS camera page.

The page shows a diagram of radial distortion with k 1 equal to minus 0.12 and k 2 equal to 0.03, on a camera with Book 2's lens numbers. These values are made up for the example, but they are typical of a small wide lens. The diagram shows a grey grid of straight lines, which is where a perfect pinhole would put the points, and a blue grid with bent lines, mostly at the corners, which is where this lens puts them. In the middle of the picture nothing moves, but near the corner pixel 8, 8 the point moves 9.3 pixels towards the middle, which at 0.34 metres is about 11 millimetres. So a program that ignored this would be accurate in the middle of the picture and badly wrong at the edges.

The next heading covers the known pattern. The known object is usually a printed checkerboard, whose inner corners, where four squares meet, lie on a perfect grid. So if the squares are 20 millimetres, the corners are at zero, zero, zero, then 20, zero, zero, then 40, zero, zero, and so on, in millimetres, in the board's own frame. The board is flat, which means every corner has z equal to zero.

Then the program finds the corners in each picture to a fraction of a pixel. OpenCV's findChessboardCorners finds them, and cornerSubPix refines each one by looking at the brightness pattern around it. A good detector places a corner to about 0.1 to 0.3 pixels.

So you take many pictures, with the board in a different place and at a different tilt each time. The page shows a picture of six such views of a board with nine by six inner corners, as the camera sees them. The same board corners are photographed from six different angles. Every picture shows the same 54 corners, and the program knows which corner is which, because the board's pattern tells it where corner zero is and which way the rows run. That matching of "this pixel is that corner" is what the method feeds on.

A newer kind of board, the ChArUco board, puts a small printed code in the white squares. Each code names its own corners, so the board still works when part of it is hidden or out of the picture, which is why Book 2 recommends it.

The next part explains reprojection error, which is the number the method makes small. Suppose you guess all the unknown numbers: the lens numbers, the distortion, and the board's pose in each picture. With those guesses, you can work out where every corner should land, using the pinhole model and the distortion formula, and that step is called reprojection.

The reprojection error of one corner is the distance, in pixels, between where it should land and where the detector found it. The method combines all of them into one number, the root mean square error, or RMS: square each distance, take the mean, and take the square root. A good intrinsic calibration has an RMS below one pixel, and a very good one is 0.1 to 0.3 pixels.

So calibration is the search for the guesses that make the RMS as small as possible. That makes it a least-squares problem, the same kind of problem as least-squares fitting a line to points, which is explained on the page about least-squares fitting, only with many more unknowns.

The next heading is about how the numbers are found. The formulas are not linear, because of the division by depth and the distortion terms, so the method cannot solve them in one step. Instead it works in two stages, and the whole method is known as Zhang's method, after the paper that described it in the year 2000.

First, it makes a first guess, ignoring distortion. For a flat board, the mapping from board points to pixels in one picture is a simple formula called a homography, which is a three by three matrix that maps one flat plane to another. The program fits one homography per picture from its corners. Each homography constrains the lens numbers a little. With three or more pictures at different tilts, the lens numbers can be solved directly, and each picture's board pose follows.

Second, it refines everything together. Starting from that guess, the program adjusts all the unknowns at once to shrink the RMS. It uses the Levenberg–Marquardt method, which is a repeated step that asks which small change to all the numbers reduces the error most, makes that change, and repeats until the error stops falling, and this stage also adds the distortion numbers.

With 15 pictures, there are 4 lens numbers, 5 distortion numbers and 6 pose numbers per picture, making 99 unknowns. The pictures give 15 times 54 corners, each with two coordinates, which is 1,620 measurements. So having many more measurements than unknowns is what lets the noise average out.

The page then shows a worked run for the lens numbers. For this page, OpenCV's calibrateCamera was run on a simulated camera, so that the true answer is known. The camera had Book 2's lens numbers and the distortion from the earlier picture. Then a nine by six board with 20 millimetre squares was placed at 15 random poses, 0.30 to 0.45 metres away and tilted up to 35 degrees. After that, the corners were projected and random noise of 0.2 pixels was added to each, which is what a good corner detector achieves.

A table compares the true values with the calibration found. The four lens numbers are close, with f x and f y landing within a fraction of a pixel of 277.1, and c x landing exactly on 160.0. The number c y is off by 1.3 pixels, which is the largest error among them. The RMS reprojection error is 0.269 pixels, which is about what the 0.2 pixels of noise predicts, so the model fits the pictures well.

However, k 2 looks badly wrong, because it is 0.03 in truth and came back as minus 0.139. That is not a bug, because k 2 controls the bending far from the middle, and in these 15 pictures no corner came further than 110 pixels from the middle. So the pictures never tested the corners of the picture, and many different k 2 values fit them equally well. Inside the area the board covered, the found lens and the true lens send each pixel along almost the same ray, within 1.6 pixels. However, in the picture's far corners, which the board never reached, they differ by 21 pixels. A calibration is only good where the board has been. So move the board into every corner of the picture.

The number of pictures also matters, so that was measured too. The run was repeated 30 times for each count of pictures, and the middle result was taken. A second table shows how far f x landed from the truth as the number of pictures increases. The error falls quickly up to about 8 pictures and slowly after 20. For example, with 3 pictures, the typical error is 2.36 pixels, and the worst tenth of runs are off by 4.70 pixels or more. With 8 pictures, the typical error drops to 0.83 pixels. By 20 pictures, the typical error is 0.56 pixels, and the worst runs are off by 1.19 pixels or more. So 15 to 25 well spread pictures is a sensible target, because more pictures of the same kind add little.

The next part describes a trap: flat-on pictures. The same calibration was run on 15 pictures where the board always faced the camera squarely, with no tilt. The RMS came out at 0.272 pixels, which is as good as before. However, f x came out as 1,754 instead of 277.1, which is more than six times too large.

A diagram shows why that happens. It shows that flat-on pictures cannot tell focal length from distance, while tilted ones can. A board 0.30 metres from a camera with f x equal to 277.1, and the same board 1.90 metres from a camera with f x equal to 1,754, give exactly the same picture when the board faces the camera. So the camera cannot tell "near and wide" from "far and zoomed in".

On the left of the diagram, the blue and red corners sit exactly on top of each other, because the largest gap is zero pixels. On the right, the board is tilted 35 degrees, so the near edge of the board is now closer than the far edge, and the amount of perspective depends on the distance. The two answers then differ by up to 9.11 pixels, so the method can tell which one is right.

The lesson is that a low RMS does not prove a calibration is right, because it proves only that the numbers explain the pictures you took. So tilt the board in every picture, in different directions.

The next section explains hand-eye calibration, which finds where the camera is on the arm. The previous section measured the camera on its own, and this section measures where that camera sits on the robot. Hand-eye calibration finds a rigid transform between the arm and the camera, and there are two common set-ups, which find different transforms.

First is eye in hand. The camera is fixed to the arm's wrist. The unknown is the transform from the flange to the camera, which is the camera's pose relative to the flange, and a board lies still on the table.

Second is eye to hand. The camera is fixed in the room, looking at the arm. The unknown is the transform from the base to the camera, which is the camera's pose relative to the arm's base, while a board is fixed to the gripper.

The two use the same equation and the same solvers, so this page describes only eye in hand, because it is the harder one to picture.

So why not just measure the transform with a ruler? Because the numbers that matter are the camera's optical centre and the direction of its optical axis, and both sit somewhere inside the camera body, where no ruler can reach. And a small error costs a lot: Book 2's error budget shows that one degree of error in this transform costs 5.9 millimetres at 340 millimetres.

The next heading explains the equation A times X equals X times B, in plain words. The arm moves the camera to several poses, and at each one two things are recorded.

First, the flange's pose in the base frame. The arm's controller reports it, from the joint angles and forward kinematics.

Second, the board's pose in the camera's frame. The program finds it from the board's corners and the lens numbers found by intrinsic calibration. Finding an object's pose from known points and their pixels is called perspective-n-point, or P n P, and OpenCV's solvePnP does it.

Then take any two of those poses, 1 and 2. Write A for how the flange moved from pose 1 to pose 2, measured in the flange's own frame at pose 1. Write B for how the camera moved between the same two poses, measured in the camera's own frame. A comes from the arm's readings, while B comes from the board, because the board did not move, so any change in how the camera sees it is the camera's own movement.

The camera is bolted to the flange, so the two movements are linked by the unknown bolt, X, which is the transform from the flange to the camera. Going "flange at pose 1, then move A, then bolt X" must reach the same place as "flange at pose 1, then bolt X, then move B". Written as transforms, A times X equals X times B.

A diagram shows the two poses, drawn from the side, where the flange moves by A, the camera by B, and X joins them at both poses. The red bar is X, which is the same at both poses, while the black arrow is A, known from the joint angles, and the purple arrow is B, found from the board. In this drawing both movements turn by minus 35.0 degrees, and the two sides of the equation agree to 12 decimal places, because the numbers were computed from a true X.

That also gives a useful check on real data. A and B must always turn by the same angle, because they are the same physical movement seen from two points on one rigid body. If a pair of poses shows A turning 14.4 degrees and B turning 12.1 degrees, one of the two measurements is wrong: a blurred picture, or an arm pose recorded at the wrong moment.

One pair of poses is not enough to find X, because each pair constrains X only partly. With three or more poses, and movements that turn about at least two different axes, X is fixed. Movements that only slide, with no turn, tell the method nothing about X's rotation, so the poses must tilt the camera in different directions, not just move it around.

So several published methods solve A times X equals X times B from many pairs. Tsai and Lenz's method and Park and Martin's method find the rotation first and then the shift. However, Horaud and Dornaika's method and Daniilidis's method find both together. Andreff's method treats the problem as one set of linear equations, and OpenCV's calibrateHandEye offers all five.

The page then shows a worked run for the camera on the flange. An eye-in-hand calibration was simulated with OpenCV, so that the true X is known. The true camera sat 60 millimetres along the flange's x axis, 20 millimetres back along its z axis, and turned 2 degrees about its y axis. At each pose, the board's corners were projected into the camera, given 0.2 pixels of noise, and passed to solvePnP. Each flange position was given 0.2 millimetres of noise, which is what a good arm repeats to. The camera was 0.30 to 0.40 metres from the board and tilted up to 25 degrees each way.

A table shows the five methods, each run 20 times on 15 poses, giving the median shift and rotation errors. Four methods land under one millimetre and near a tenth of a degree. For example, Park's method had a shift error of 0.84 millimetres and a rotation error of 0.121 degrees. Andreff's method found the rotation as well as the others, but its shift was 17.54 millimetres out in this simulation, and the reason was not investigated. So the practical lesson is to run two methods on the same data and compare them, and if they disagree by more than a millimetre or two, find out why before trusting either.

A second table shows Park's method with different numbers of poses, each run 30 times. As with intrinsic calibration, the error falls fast up to about 10 poses and slowly after. With 3 poses, the shift error is 3.28 millimetres and the rotation error is 0.50 degrees. By 10 poses, the shift error drops to 1.04 millimetres and the rotation error to 0.19 degrees. At 25 poses, it reaches 0.72 millimetres and 0.11 degrees. Book 2 reports that careful real calibrations reach about 0.9 millimetres and a quarter of a degree, which is close to these simulated numbers. However, a real calibration also carries errors this simulation left out, such as an imperfect intrinsic calibration and a board that is not perfectly flat.

The next section is about checking the result. The previous section gave numbers from a simulation where the true answer was known, but on a real robot you never have that. A calibration tool always returns an answer, so checking it is a separate job, and the reprojection error alone is not enough, as the flat-on pictures showed. There are five ways to check.

First, the touch test. Put a small, sharp object on the table. Find it with the camera, move it into the base frame, send the tool tip to it, and measure the miss with a ruler. This tests the whole chain at once: lens numbers, the hand-eye transform, arm kinematics and the tool transform. Book 3 describes it on the page about the known object in a known place.

Second, the straight edge. Photograph a straight edge near the corner of the picture, undistort it, and check that it comes out straight.

Third, run two hand-eye methods on one data set and compare.

Fourth, use held-out pictures. Keep a few pictures out of the calibration, and then compute their reprojection error with the result, which should be about as small as the RMS of the pictures that were used.

Finally, take several views of one point. With a wrist camera, look at one fixed point from several arm poses. After moving each measurement into the base frame, all of them should land on the same spot. A spread of several millimetres points at the hand-eye transform.

The next section provides pseudocode. It describes the whole technique in plain steps, naming the inner solvers that libraries provide rather than writing them out.

For intrinsic calibration, it starts with the known corner positions in the flat board frame. It creates an empty list of views. Then it loops over each picture, aiming for 15 to 25 tilted pictures that cover the corners. In the loop, it finds the board corners. If they are not found, it skips the picture. If they are, it refines the pixels to subpixel accuracy and adds the board corners and pixels to the views list. After the loop, it guesses the camera matrix and one board pose per view from homographies, which is Zhang's first stage. Then it refines the camera matrix, distortion, and all board poses to minimise the squared difference between the projected corners and the found pixels. Finally, it reports the RMS error and checks it with held-out pictures.

For hand-eye calibration, specifically eye in hand, it creates empty lists for flange poses and board poses. It loops over at least 10 arm poses, tilting about different axes. For each, it moves the arm there and waits until it is still. It records the transform from the base to the flange from the arm controller. It takes a picture and finds the board corners, then uses solve P n P to find the transform from the camera to the board, and adds both transforms to the lists. Before solving, it runs a sanity check. For each pair of poses, it calculates A, the movement of the flange, and B, the movement of the camera. If the turn angles of A and B differ by more than half a degree, it flags the pair. Finally, it solves A times X equals X times B using a method like Park's, and checks X with a second method and with the touch test.

The next section explains where calibration is used on a robot arm. Calibration runs rarely, but everything the camera measures depends on it, and here are the concrete places where it is needed.

First, setting up a new camera. Intrinsic calibration runs once per camera, per resolution. Many depth cameras ship with their own factory calibration, which is usually good enough for the depth camera itself, while a plain colour camera almost never does.

Second, mounting a camera on the wrist. Hand-eye calibration runs once after the camera is bolted on, and again after anything touches the mount. Book 2's wrist camera page shows this transform in the middle of every measurement.

Third, fixing a camera above the table. Eye-to-hand calibration finds the camera's pose relative to the base. Without it, the fixed camera's points cannot be sent to the arm.

Fourth, adding a second camera. Two cameras looking at the same scene each need their own calibration, and their points only line up if both are right.

Fifth, correcting the arm itself. The same least-squares idea can measure the arm's own small errors, such as a link that is 0.3 millimetres longer than its drawing. This is called kinematic calibration, and it uses a camera or a tracker to watch the flange at many poses.

Finally, undistorting every picture. After intrinsic calibration, every picture, or every pixel the program uses, is corrected before the pinhole camera model is applied.

The next section covers where it works, and where it does not. The uses just mentioned all assume the calibration itself was good, and that depends on the data you gave it. Calibration works well when the pictures and poses give it enough to go on, so most failures come from poor data rather than poor solvers. A table lists the common ones.

If the board always faces the camera, you see a low RMS, but f x and the board distance are both far off. The fix is to tilt the board 20 to 45 degrees in different directions.

If the board never reaches the picture's corners, points near the edges of the picture are several millimetres off, and k 2 and k 3 look strange. The fix is to fill the whole picture, including every corner, across the set of pictures.

If the board is blurred or partly hidden, corners are detected in the wrong place, and a few pictures have a much larger error than the rest. The fix is to drop the worst pictures, or use a ChArUco board.

If the printed board is not flat, or its squares are not the size you typed, you see a consistent size error in every measurement. The fix is to mount the print on glass or aluminium, and measure the squares with calipers.

If hand-eye poses only slide, or turn about one axis, you get a hand-eye shift error of several millimetres or more. The fix is to turn the wrist about at least two different axes between poses.

If the arm pose is read while the arm is still moving, A and B turn by different angles for some pairs. The fix is to wait until the arm stops, and check the angle pairs.

If the camera is bumped, or its focus or zoom changed, the touch test misses by more than it used to. The fix is to recalibrate, lock the focus, and add a periodic check.

Finally, if you use a different resolution than was calibrated, every point is scaled towards or away from the picture's middle. The fix is to calibrate at the resolution you use, or scale the numbers exactly.

Calibration also does not fix things that are not in its model. For example, it cannot correct a depth camera's depth errors on shiny objects, and it cannot correct an arm whose links bend under load. And it describes the camera only as it was on the day it was measured.

The next section lists libraries that provide calibration. Because the solvers are long and the details matter, calibration is almost always done with a library. A table lists well-known tools.

OpenCV covers C++ and Python, providing functions for finding corners, calibrating the camera, solving P n P, and calibrating hand-eye in its calib3d module. It is the reference implementation of both, and its hand-eye function offers the Tsai, Park, Horaud, Andreff and Daniilidis methods.

The OpenCV aruco module covers C++ and Python for ChArUco board detection, for boards that may be partly hidden.

ROS camera_calibration is a Python tool providing the cameracalibrator node, which is a window that guides you to move the board, then writes the camera's calibration file.

easy_handeye2 is for Python and ROS 2, providing calibration nodes. It is the usual ROS 2 tool for hand-eye calibration; it collects the poses and calls OpenCV's solvers.

MoveIt Calibration is a C++ and ROS tool providing an RViz plugin for hand-eye calibration inside MoveIt, though Book 2 notes its ROS 2 state as partly maintained.

Kalibr provides C++ and Python command-line tools for rigs of several cameras, and for cameras with a motion sensor.

mrcal provides C and Python command-line tools, and it reports how uncertain each calibrated number is, not just its value.

Finally, Ceres Solver provides C++ least-squares problem classes for writing your own calibration, such as kinematic calibration.

Book 2 lists the licences of these tools on the page about calibration, which decides all of it.

The next section explains why to calibrate, and what it costs. It answers the four questions for calibration: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

It is the method of photographing a known object and choosing the camera's numbers so that the model predicts the pictures. So it gives you the lens numbers, the distortion, and the camera's place on the arm, each with a measured error.

The obvious alternative is to use numbers from somewhere else: the lens numbers from the camera's datasheet, and the camera's position from the mount's drawing. That costs nothing and needs no board, and for the lens numbers it is often close. Book 2 works out the Raspberry Pi camera's f x from its datasheet in two separate ways, and they agree within 0.2 per cent. However, a datasheet does not know your particular lens's distortion or where its sensor really sits, and a drawing does not know where the optical centre is inside the camera body. On a wrist camera, an error of one degree from the drawing costs about 6 millimetres at a normal working distance, so calibration measures the actual camera on the actual arm.

So the cost is this. You need a flat, accurately printed board, along with 15 to 25 careful pictures and 10 to 20 careful arm poses. You also need to check the result separately, because the tools always return an answer. And you need to do it again whenever the camera is bumped, refocused, or moved to a different resolution.

The next section covers the learned alternative. No model in Book 6 measures a camera's lens numbers or its place on the arm. So the learned alternative is to skip calibration altogether. A policy, which is a network from Book 6's movement models, turns pictures straight into arm movements, so no lens numbers or hand-eye transform appear anywhere in the plan. But the policy then learns one camera in one place. Book 6's page on diffusion and flow policies notes that a camera moved by a few centimetres can confuse it, and the fix is more demonstrations, while a calibrated camera can be moved and recalibrated in half an hour. For the arm's own geometry, Book 6's page on learned arm models describes a small network that learns what kinematic calibration leaves out, such as links that bend under their own weight. It then adds that on top of the calibrated numbers rather than replacing them.

The next section suggests where to read next. The previous pages on the pinhole camera model and rigid transforms use every number this page measures. The overview page shows how calibration errors compare with the other errors in a measurement. The page on least-squares fitting explains the kind of problem that calibration solves, on simpler examples. The page on RANSAC explains how some tools reject bad pictures or bad corners before fitting. Finally, Book 2 goes deeper into why calibration matters on the pages about calibration, which decides all of it, and the wrist camera, end to end.

The final section is about using it in Python. The earlier sections described the two calibrations and gave both as pseudocode, while the libraries section named OpenCV as the library that implements them. This section shows the OpenCV calls themselves, because the pseudocode hides how little code the two solvers need once the pictures and the poses have been collected. After reading it you should see that the solver is three lines and the collecting is everything else.

Intrinsic calibration comes first, and it is two calls per picture followed by one call over all of them. The code sets up a board with 9 by 6 inner corners and 20 millimetre squares. It creates the board's own corners in the board's frame, setting z to zero because the board is flat. Then it loops over the picture files. For each picture, it reads it in greyscale and calls findChessboardCorners. If the corners are not found, it skips the picture, which is normal. If they are found, it calls cornerSubPix to refine them, and adds the board points and image points to its lists. After the loop, it calls calibrateCamera with those lists, which returns the RMS error, the camera matrix, the distortion coefficients, and the rotation and translation vectors for each picture.

Hand-eye calibration then reuses those rotation and translation vectors that came back, because each of them is already the board's pose in the camera for one picture. What you add is the arm's own pose for the same picture, read from t f 2 at the moment the picture was taken. The code converts the rotation vectors to matrices, then calls calibrateHandEye. It passes the arm's flange pose for each picture, the board's pose in the camera for each picture, and specifies a method like Tsai's.

What the library does for you is the whole of both solvers. findChessboardCorners finds the corners and puts them in a known order, cornerSubPix refines each one to a fraction of a pixel, and calibrateCamera runs the first guess and the least-squares refinement over every picture at once, returning the four lens numbers, the five distortion numbers and the board's pose in each picture. calibrateHandEye solves the equation of section 3, and it offers the Tsai, Park, Horaud, Andreff and Daniilidis methods behind that one method argument.

What you still write yourself is the collecting, and it is the larger half. You write the loop over the pictures, you skip the pictures where the board was not found, and you have to pair each picture with the arm pose at the moment it was taken rather than the pose a moment later, which means either stopping the arm or recording both with timestamps. Nothing checks that the pairing is right, and a single mismatched pair moves the answer by centimetres.

What you have to decide or measure is the board and the poses. You measure the square size with calipers, on the printed board rather than from the file you sent to the printer, because printers scale. You decide how many pictures to take and how varied they are, and for hand-eye you decide the rotations, because calibrateHandEye fails outright when the flange poses are not turned enough relative to each other. Finally, the RMS reprojection error that calibrateCamera returns is not a verdict. As shown earlier, a low number can come from poor pictures, so check the answer against a measured distance instead.
