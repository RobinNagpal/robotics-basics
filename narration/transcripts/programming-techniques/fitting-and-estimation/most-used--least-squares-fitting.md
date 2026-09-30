Least-squares fitting.

This page explains least-squares fitting, the standard way to find the line, plane or circle that best matches a set of measured points. It answers four questions in order: what "best" means, and how the best shape is found, both by hand and by a program. After that it asks where a robot arm uses it, and when it gives a wrong answer.

It is for a reader who knows what a point cloud and a coordinate frame are, and who has read the chapter overview. However, you do not need any linear algebra beyond knowing that a matrix is a table of numbers. Every number on this page comes from a real run of the diagram script.

Least squares is the most used fitting technique in robotics, because it sits inside so many other methods. It is inside plane finding, circle measurement, camera calibration, point cloud alignment and numerical inverse kinematics. So it is worth understanding well, since most of the other techniques in this chapter are built on top of it.

The first section covers what this page answers. A camera or a depth sensor never gives points that lie exactly on a shape. So the points along a straight box edge wobble a little to either side. Since a flat table is measured in the same way, its points sit a millimetre or so above and below the real surface. Yet the arm needs one straight edge, one flat table and one circle with one centre, which the measured points do not give it directly.

Least-squares fitting turns the wobbly points into that one shape, which is described by a few numbers called its parameters. A line in a picture has two of them, its slope and its offset, while a plane has three. A circle on a table also has three: the two coordinates of its centre and its radius. So fitting means choosing those parameters, which comes down to picking a few numbers that suit many measured points at once.

This page shows how least squares chooses them for lines, planes and circles, and how to check that the result can be trusted. Then it shows where the method breaks, which is the reason the next page, on RANSAC, exists.

The next part gives the idea in one sentence. Choose the shape that makes the sum of the squared distances from the points to the shape as small as possible.

Here is an everyday example. You hang a picture rail along a wall, and mark five heights where you want the screws, but your marks are a little uneven. So no straight rail can pass through all five of them. You do not want the rail to pass exactly through any two marks and miss the other three badly. Instead, you want it to pass as close as possible to all five at once. If you measure how far each mark is from the rail, square those five distances and add them up, you get a total for that rail. Then the best rail is the one where that total is smallest.

Squaring matters for two reasons, and the first is that every distance becomes positive. Because of that, a mark above the rail cannot cancel out a mark below it. Squaring also makes a large miss count much more than a small one. That is why a two millimetre miss counts four times as much as a miss of one millimetre. As a result, the shape that comes out runs through the middle of the points instead of through any two of them.

The next section explains how it works, step by step, starting with residuals and the sum of squares.

The sentence just mentioned talks about the distance from a point to a shape, so the first thing to pin down is that distance. Take one point and one candidate line: the residual is how far the point is from the line. For a line written as y equals m times x plus c, the usual residual is the vertical gap. This is the point's measured y, minus the y the line gives at that point's x. Here m is the slope, which is how much y rises for each one of x. Then c is the offset, which is the value of y where x is zero.

Once every point has a residual, square them all and add them up, and that total is the sum of squared errors. Each candidate line has its own sum, so least squares simply picks the line whose sum is smallest.

The diagram shows two lines drawn through the same five points along the edge of a box, found by a camera, in millimetres. The residuals are drawn as red bars, so a longer bar means a worse miss at that point. On the left is the line through the first and last points, and on the right is the least-squares line. The line through the two end points has zero error at those two points, but large errors at the three in between, which add up to 6.45. The least-squares line instead misses every point by a little, and it adds up to 2.72. That is the smallest total any straight line can reach for these points.

The next part is a worked example of a line through five points. That total of 2.72 is worth working out by hand, because doing the arithmetic once shows where such a number comes from. The table lists the same five points from the picture, in millimetres. The x values go from 0 to 40 in steps of 10. The corresponding y values rise from 1.0 to 19.4.

Think of every possible line as one point on a map, with the slope m on one axis and the offset c on the other. Then give each point on that map the sum of squared errors of its line. The result is a bowl, because the total error is high at the edges of the map and lowest near the middle. The diagram draws that bowl as contour lines over slope and offset, like the height lines on a hiking map, with the lowest point marked.

Each ring joins lines with the same total error. The orange dot at the centre is the least-squares line. The grey dot is the line through the two end points, which sits outside the ring marked 6, since its own total is 6.45.

At the bottom of a bowl the ground is flat in every direction. So the best line is the one where a small change to m does not change the total. The same has to be true of a small change to c. Writing those two conditions out gives two ordinary equations, called the normal equations. For a line, the first equation is the sum of x squared, times m, plus the sum of x, times c, equals the sum of x times y. The second equation is the sum of x, times m, plus the number of points, times c, equals the sum of y.

Putting the five measured points into those sums gives the numbers below. The sum of x squared is 3000. The sum of x is 100. The sum of x times y is 1560. The sum of y is 55.3. And the number of points is 5.

So for these five points the two normal equations become: 3000 times m plus 100 times c equals 1560, and 100 times m plus 5 times c equals 55.3.

Multiply the second by 20 and subtract it from the first, which leaves 1000 times m equals 454, so m equals 0.454. Then put that back into the second equation, which gives 5 times c equals 55.3 minus 45.4, which is 9.9, so c equals 1.98. This is the best line: y equals 0.454 times x plus 1.98.

The residuals of that line are minus 0.98, plus 0.68, plus 0.84, plus 0.20 and minus 0.74 millimetres, and their squares add up to 2.72. That is the number at the lowest point of the bowl above. The typical distance of a point from the line is called the root mean square residual, or RMS residual. It is the square root of 2.72 divided by 5, which comes to 0.74 millimetres. Because it is one number in millimetres, the RMS residual is a useful summary of how well a fit went, and the rest of this page leans on it.

Because there is one normal equation per parameter, a shape with more parameters works in exactly the same way. A computer then solves all of the equations at once. In matrix form the equations are written as A-transpose times A, times p, equals A-transpose times b, where each row of A holds one point's values. Then b holds the measured values and p holds the parameters. You do not need to solve these by hand, since every numerical library has a function for it.

The next part shows the steps as pseudocode. Since a library does the solving, it is worth seeing the order of the steps first. The pseudocode fits any shape whose error is a straight sum of parameters times known values. That covers lines, planes written as z equals a times x plus b times y plus c, polynomials and the circle trick later on this page.

The code defines a function that takes a list of points. First, it creates an empty table called A with one row per point, and an empty list called b with one value per point. Then it loops through each point. For each point, it adds a row to A containing the values that multiply each parameter. For example, for a line, this would be the x value and a 1. It also adds the measured value to b, which for a line is the y value. After the loop, it solves the normal equations to find the parameters, p. It calculates the residuals by subtracting the predictions from the measured values in b. Then it calculates the RMS residual by squaring the residuals, summing them, dividing by the number of points, and taking the square root. Finally, it returns the parameters and the RMS residual.

In practice a library solves the problem with a method called QR or the singular value decomposition, instead of forming A-transpose times A directly. The answer is the same either way, but those methods lose fewer decimal places when the numbers are large or nearly repeat.

The next part explains planes and the singular value decomposition. A table, a wall or the face of a box is a plane, so the pseudocode above looks as though it already covers them. You could fit a plane as z equals a times x plus b times y plus c, with vertical residuals as for the line. That works well enough for a table seen from above. However, it fails for a wall, because a wall is nearly vertical, and a vertical plane cannot be written as z equals something. The vertical gaps also measure the wrong thing on a steep surface, so a plane needs its own method.

Instead, the better way measures each point's distance at right angles to the plane. It uses a tool called the singular value decomposition, or SVD, which in plain words does this. First, take the average of all the points, which is the centre, and the plane passes through it. Second, subtract the centre from every point, so the points sit around the origin. Third, the SVD finds the three directions in which the points spread out, one at right angles to the next, and how far they spread in each: the longest spread, the middle one and the thinnest one. Fourth, for points on a flat surface the thinnest direction points straight out of the surface, and so it is the plane's normal, the direction the plane faces. Finally, the plane is all points whose offset from the centre is at right angles to the normal.

The thinnest direction is exactly the one that makes the sum of squared right-angle distances smallest. So this is a least-squares fit too, even though no normal equations were written out. The diagram shows the result for 150 points on the tilted face of a board. It shows the points on the tilted face, the fitted plane with its longest, middle and normal directions, and a bar chart of the spread in each direction.

The points spread 92.4 millimetres along the longest direction and 57.3 millimetres along the middle one. Along the thinnest direction they spread only 0.93 millimetres, and that thinnest direction is the normal. The fitted normal is minus 0.230, 0.321, 0.919, while the true face used to make the points has the normal minus 0.230, 0.322, 0.919, so the fit agrees to three decimal places. The spread of 0.93 millimetres along the normal is also the RMS distance of the points from the plane: the noise that was added was 1 millimetre.

Because the three spreads come back as well, they carry a free check. If the thinnest spread is not much smaller than the middle one, then the points do not lie on a plane at all. They might lie on a curved surface, or across two surfaces, so a program should test the spreads before it trusts the normal.

The same three directions, computed for the points of one object, give its long axis and its thin axis. So that is how a program finds which way a box or a pen lies. The NumPy page in Book 1 shows this in the section on which way an object lies.

The next part covers circles, and a trick that keeps it simple. Lines and planes both drop straight into the normal equations, but a circle does not, so it needs one extra step first. Cups, glasses, bottle caps and holes are all round objects. Seen from above, their rim is a circle with a centre a, b, and a radius r. The natural error is each point's distance from the circle, but that error does not make a straight sum of parameters, so the normal equations do not apply directly.

A short piece of algebra fixes this in one step. Because a point x, y on the circle satisfies the equation x minus a, all squared, plus y minus b, all squared, equals r squared, multiplying that out and moving the terms around gives this: x squared plus y squared equals 2 times a times x, plus 2 times b times y, plus k, where k equals r squared minus a squared minus b squared.

Now the unknowns a, b and k appear only multiplied by known values 2x, 2y and 1. So this is the same shape of problem as the line, with three parameters instead of two. That means you can solve it with the pseudocode above, and then recover the radius as r equals the square root of k plus a squared plus b squared. This is called the algebraic circle fit, or the Kåsa fit after the person who described it.

The diagram shows why the fit matters on a real arm. A camera looking at a glass from the front sees only the near half of its rim. The diagram shows rim points on the near half of a circle, the fitted circle and its centre, and the mean of the points well off the centre.

The 18 rim points came from a circle centred at 120, 80 millimetres with a radius of 40 millimetres, and they carry 0.6 millimetres of noise. The fit gives a centre of 120.2, 80.1 and a radius of 40.2 millimetres. The plain average of the points is 120.3, 50.2, and that lies 30 millimetres towards the camera, because all the points are on the near side. As a result, a gripper sent to the average would hit the front of the glass.

The algebraic fit does have one known weakness, which shows up when the points cover only a short arc. Below a quarter of the circle, it tends to give a radius that is too small. A second step, which minimises the true distances with a few rounds of nonlinear least squares, corrects this. The next section on the leftover error says how to spot the problem in the first place.

The next part explains how the leftover error tells you how good the fit is. Every fit on this page returns an answer, and that is exactly where the danger lies. Least squares returns a line even for points that lie on a curve, and a plane even for points on two surfaces. That means the only sign that the shape is wrong is the leftover error.

So a careful program always returns the RMS residual with the fit, and compares it with the sensor's known noise. If a depth camera is good to about 1 millimetre and a plane fit leaves an RMS residual of 0.9 millimetres, then the plane is real. If it leaves 3 millimetres instead, then something else is in the points. That something might be an object on the table, the edge of the table, or a second surface. Book 2 makes the same point in the section on reporting the margin, not the verdict.

The next section covers where it is used on a robot arm. The sections above took lines, planes and circles one at a time. On a real arm those three fits turn up together, across perception, calibration, sensing and movement. The page lists the most common places, and most of them link to a page that goes further.

First, finding the table's height and tilt. After RANSAC picks the points that belong to the table, an SVD plane fit on those points gives the most accurate plane. Every object's height is then measured from it.

Second, measuring a round object. A program fits a circle to the rim of a cup or glass, as above, to find where to aim the gripper. The glass-picking project in the sibling repository does exactly this, with the same x squared plus y squared equals 2 times a times x, plus 2 times b times y, plus k trick.

Third, finding which way a face points. Before a wrist turns a board to lie flat, it must know the direction of the board's face. That is why the turn-top-flat project fits the face with the SVD, then refits with only the points within 6 millimetres, then 3 millimetres, then 2 millimetres, to drop the points from a neighbouring edge.

Fourth, finding a straight edge in a picture. Edge pixels along a box side or a tray wall are fitted with a line, to give its angle for the gripper. The page on edges and contours shows where these pixels come from.

Fifth, correcting a sensor. Plot a distance sensor's readings against known true distances and fit a line, whose slope and offset then give the correction. Book 1 shows this in the section on solving and fitting.

Sixth, calibration. Camera calibration fits the camera's focal length and lens distortion to many checkerboard corners, while hand-eye calibration fits where the camera sits on the arm from many arm poses. Both are least-squares problems, and the calibration page explains them.

Seventh, aligning two point clouds. Each step of iterative closest point finds the rotation and shift that best line up matched pairs of points, in the least-squares sense, using the SVD.

Eighth, moving the arm to a pose. Numerical inverse kinematics repeatedly solves a small least-squares problem for how much to turn each joint. The page on numerical inverse kinematics calls this damped least squares.

Finally, learning a contact constant. A robot that pushes objects can fit the friction of the table from many pushes, one equation per push. The contact-parameters page in the sibling repository does this, and moves on to recursive least squares, which updates the fit one push at a time.

The next section explains where it is useful, and where it is not. Those uses all assume the fit can be trusted, so this section says when it can be. Least squares is the right choice when every point belongs to the shape, the noise is small and spread evenly, and you know the shape in advance. In that case it is exact, fast and needs no settings.

Because the errors are squared, its big weakness is stray points: one point far from the rest pulls the answer hard. In the worked example above, change the last point from 19.4 to 29.4, as a depth camera might report for a single bad pixel. Then the fitted slope jumps from 0.454 to 0.654, and the offset from 1.98 to minus 0.02. That means one bad point out of five has moved the whole line.

The page includes a table listing the common ways least squares goes wrong, the sign you would see, and what people use instead. Here are the main patterns.

If some points belong to something else, like an object on the table or a stray reading, the RMS residual will be much larger than the sensor's noise, and the shape will be tilted towards the stray points. Instead, use RANSAC to pick the good points first, or a robust loss that counts large errors less.

If there are two surfaces in the same points, the thinnest SVD spread is not much smaller than the middle one. You should split the points first with clustering or RANSAC.

If the shape is wrong, such as a curve fitted with a line, the residuals are not random: they are positive in the middle and negative at the ends. The solution is to fit the right shape, or a polynomial of higher degree.

If a circle is fit to a short arc, the radius comes out too small, and the centre moves a lot when one point changes. Instead, use a geometric fit with nonlinear least squares, or a known radius.

If points cover a very small area, two parameters trade against each other, and the fit changes a lot with the noise. You should measure over a wider area, or fix one parameter from other knowledge.

If some points are more accurate than others, residuals are larger at one end. Use weighted least squares, which gives each point a weight.

Finally, if the errors are not a straight sum of parameters, the simple solve gives a biased answer. Instead, use nonlinear least squares, such as the Gauss-Newton or Levenberg-Marquardt method, which repeat a linear fit and improve the guess each time.

The next section covers libraries that provide it. Since the cures just mentioned are all standard, you rarely write the solve yourself. The page provides a table listing the well-known libraries that do it for you.

For Python, NumPy is the first thing to reach for, using functions like least-squares and SVD. SciPy provides nonlinear least squares with robust losses. Scikit-learn offers the same line and plane fit with a machine-learning style interface.

For C++, Eigen is the matrix library under most C++ robotics code. Ceres Solver handles large nonlinear least-squares problems, such as calibration.

OpenCV, used from C++ and Python, provides line and ellipse fits on image points. Open3D and the Point Cloud Library fit small planes around points to get their normals.

A plane fit with NumPy is three lines, since you subtract the mean, call SVD and take the last row of the result as the normal. Even the circle trick is only one call to the least-squares function.

The next section explains why least squares is used, and what it costs. Those libraries make the method easy to run, so it is worth saying plainly what it is and what it costs. Least squares is a way to choose a shape's parameters so that the sum of the squared distances from the points to the shape is as small as possible. In other words, it gives the arm clean numbers, such as a table height, a cup centre or an edge angle, from noisy points. It also gives a measure of how well the shape fits.

The obvious alternative is to use only a few special points. You could take the two end points of an edge, the highest and lowest points of a surface, or the middle of a bounding box around a rim. That takes no maths at all, but it throws away most of the data, and it lets the noise on those few points decide the answer. The worked example shows the difference, because the end-point line has more than twice the total error of the least-squares line. The glass example shows a worse case, since the average of the points is 30 millimetres off while the fit is 0.2 millimetres off. Least squares instead uses every point, so the noise averages out.

The second alternative is to minimise something other than squared distances, for example the plain sum of distances. That resists stray points better, but it has no direct solution. Instead it needs repeated steps, which are slower and can stop at the wrong answer. That is why squared distances are chosen: they give a direct, exact solution in one step.

Three costs come with that choice, and the first is that you must know which shape to fit before you start. Second, every point must belong to that shape, because one stray point can move the answer a long way. Third, the answer always looks confident, so you must check the leftover error yourself. That is why, when stray points are likely, you add RANSAC in front of the fit.

The next section discusses the learned alternative. That comparison was with hand-picked points, so the other one a reader will want is with machine learning. Fitting a known shape, such as a table plane or a cup's rim, has no learned replacement. The shape's formula is known, and least squares gives its best fit exactly, in one step. So learning takes over only when nobody knows the shape in advance.

The linear regression page in Book 6 shows that linear regression is least squares itself. Its Gaussian processes page shows that a Gaussian process, a method that gives an error bar with each prediction, can learn a curve that nobody wrote down, such as a depth camera's error against distance. A small neural network can learn the same kind of curve. However, with a few input numbers and tens to hundreds of examples, the classical methods do as well as the network or better. A network pulls ahead only when the input is a picture, a point cloud or a long recording, and there are many examples.

The final section suggests where to read next. The next page is RANSAC, which finds which points belong to the shape, so that least squares can then fit only those. The Kalman filter applies the same idea to readings that arrive one at a time, rather than all at once. Iterative closest point uses an SVD least-squares fit inside each step to line up two point clouds. Numerical inverse kinematics uses damped least squares to move the arm to a pose. The page on how a model learns in Book 6 shows that training a network is the same idea, because it makes the total error as small as possible, over millions of parameters instead of three. Finally, the section on methods you write yourself in Book 2 shows how a fitted table plane is used to measure objects standing on it.
