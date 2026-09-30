The building blocks. 

The techniques in this book look very different from each other at first. One turns a pixel into a position, another finds a path round a table, and another keeps a motor at the right angle. However, almost all of them are built from the same six ingredients, so this page explains those six ingredients one at a time, with a small example of each on a robot arm.

It is for a reader who has read the page on programmed, not learned, and has never studied algorithms. Once you know the six ingredients, each later technique page reads as a new way of putting familiar pieces together.

The six ingredients are frames and transforms, arrays and grids, graphs, noise and uncertainty, cost functions, and loops that run at a fixed rate. Each of them gets its own section.

The first ingredient is frames and transforms, which answers the question of where a thing is, because a position is always measured from somewhere. So "the mug is 300 millimetres away" means nothing until you say 300 millimetres from what, and in which direction.

A frame is that "from what", and it is a starting point, called the origin, together with a set of directions, called the axes. Each axis is a direction in which you measure, so on a flat table there are two axes, x and y, while in space there are three, x, y and z. A frame is always fixed to one physical thing. For example, a robot arm has a base frame fixed to its base, and a camera has a camera frame fixed to the camera. Book 1 introduces frames on the page about position, frames and transforms.

The same mug has different numbers in different frames, because the camera measures the mug from the camera while the arm needs to know where the mug is from the base. So the program must convert the camera's numbers into the base's numbers, and a transform is the recipe for that conversion. For a solid object that does not bend, the transform has two parts. First a rotation turns the directions of one frame to line up with the other, and then a translation shifts the origin from one place to the other.

Here is a small example on a flat table, seen from above. The diagram shows a base frame, a camera frame turned by 90 degrees, and one mug measured from each. The camera sits at x equals 400 millimetres, y equals 100 millimetres in the base frame, and it is turned by 90 degrees, so its x axis points the same way as the base's y axis. From there the camera sees a mug at camera x equals 50 millimetres, camera y equals 120 millimetres.

The mug is at 50, 120 when measured along the camera's axes, and at 280, 150 when measured along the base's axes. The conversion goes in two steps, in this order.

First, rotate. Turning the camera's numbers by 90 degrees uses the rule that the new x equals the cosine of 90 degrees times 50, minus the sine of 90 degrees times 120. The new y equals the sine of 90 degrees times 50, plus the cosine of 90 degrees times 120. Since the cosine of 90 degrees is 0 and the sine of 90 degrees is 1, this gives a new x of minus 120 and a new y of 50.

Second, translate. Add the camera's position in the base frame. That gives x equals 400 plus minus 120, which is 280, and y equals 100 plus 50, which is 150.

So the mug is at 280, 150 in the base frame, which you can check against the picture. Real arms do the same thing in three dimensions, with three numbers instead of two. Programs usually pack the rotation and the translation into one 4 by 4 table of numbers, called a homogeneous transform matrix, so that one multiplication does both steps. That matrix is explained on the rigid transforms page.

Transforms can also be chained. For example, if you know the camera from the wrist, and the wrist from the base, you can combine them to get the camera from the base. An arm program does this all the time, and getting one link in the chain wrong is one of the most common bugs in robotics. That is why Book 3 spends a whole page on it, titled frames, conventions, and the bug class that comes from mixing them.

The next section is about arrays and grids. Frames say where a thing is, but a program also needs somewhere to keep many numbers at once, and that is the second ingredient. An array is a list of numbers kept in a fixed order, and each number has a position in the list, called its index. Most programming languages count the index from 0, so the first number is number 0. For example, the row of 16 depth readings on the previous page was an array with indexes 0 to 15.

A grid is an array with rows and columns, like a spreadsheet, so you find one number in it by giving its row and its column. A picture from a camera is a grid in which each cell is a pixel. A picture 640 pixels wide and 480 pixels tall is therefore a grid of 480 rows and 640 columns, which is 307,200 pixels. A colour picture holds three numbers per pixel, which are red, green and blue, while a depth picture holds one number per pixel, which is the distance in millimetres.

The diagram for this section shows two things. On the left is a very small depth picture, 6 rows by 8 columns, taken from above a mug. Most cells read about 600 millimetres, which is the table, and nine shaded cells read between 503 and 512 millimetres, which is the top of a mug. On the right, it shows six gripper poses joined by lines with lengths, which is a graph, explained in the next section.

A computer works through a grid in order, starting with row 0 from left to right, then row 1, and so on. Many techniques in this book are therefore loops over a grid. The depth rule on the previous page is one such loop, because it visits each cell and compares its number with 580, and on this grid it marks 9 cells.

A point cloud is also an array, because it is a list of points in which each point has three numbers, x, y and z. So you can think of it as a grid with one row per point and three columns. A depth camera with 307,200 pixels gives up to 307,200 points, one for each pixel that got a reading.

Grids are also used for space itself. For example, a planner can split the table top into small squares and mark each square as free or full, which is called an occupancy grid. The graph search page then finds paths across such a grid.

Arrays matter for a practical reason too, because libraries such as NumPy in Python and Eigen in C plus plus can do the same sum on every cell of a large array very quickly. Book 1 introduces this on the NumPy intro page.

The third ingredient is graphs. Arrays and grids hold numbers in rows and columns, but some problems are instead about places and the ways between them. In this book, a graph is not a chart, but a set of places together with the connections between them.

First, each place is called a node. A node can be a pose of the gripper, a square of an occupancy grid, or a state of a task, such as holding a mug. Second, each connection is called an edge. An edge says you can go directly from one node to another. Finally, an edge can carry a number, called its weight or its cost. It often means distance or time.

The right side of the picture mentioned earlier is a graph, and its six nodes are poses of the gripper, which are home, above mug, grasp, side, above rack, and on rack. The lines are moves the arm can make safely, and each line is labelled with its length in millimetres.

A question you can ask of a graph is what is the shortest way from one node to another. From home to on rack there are three routes in this graph, so you add the lengths along each one. The first route goes from home, to above mug, to above rack, to on rack, which adds up to 789 millimetres. The second route goes from home, to above mug, to grasp, to on rack, adding up to 847 millimetres. The third route goes from home, to side, to grasp, to on rack, which is 295 plus 179 plus 301, adding up to 775 millimetres.

The third route is the shortest, at 775 millimetres. With six nodes you can check every route by hand, but a real planning graph can have millions of nodes. So the techniques on the graph search page find the shortest route without trying every one.

Graphs appear in many places on a robot arm. For example, a grid of squares is a graph in which each square is joined to its neighbours, and a roadmap is a graph of arm poses known to be free of collisions, used by the page on sampling-based planning. A behaviour tree is another special kind of graph, one that holds the order of a task.

The next part of the page explains noise and uncertainty. The first three ingredients all assumed that the numbers are correct, but on a real arm they never quite are. Every sensor is a little wrong, and the error changes each time you read it, so this changing error has a name of its own, noise.

Here is an example. A depth camera looks at a mug that does not move, and the program reads the distance to that mug 20 times in a row. The diagram shows 20 readings of one distance scattered around a line at their average. The 20 readings of the same still mug fall between 406.3 millimetres and 416.0 millimetres, around an average of about 411.0 millimetres. The diagram also shows a bowl-shaped cost curve, which is explained in the next section.

The mug did not move, yet the readings differ by up to 9.7 millimetres, so no single reading is the truth. The best you can say is that the mug is probably near 411 millimetres, give or take a few millimetres, and that "give or take" is the uncertainty. For these readings, 16 of the 20 fall within 3 millimetres of the average.

Noise is not the only kind of error. Sometimes a reading is completely wrong, for example when light bounces off a shiny surface, and a reading like that is called an outlier. Outliers need different handling from ordinary noise, because one outlier can pull an average far away from the truth. The page on choosing a technique shows this with a picture.

Three chapters of this book exist mostly because of noise and outliers. The chapter on fitting and estimation gets a clean shape or a steady number out of many noisy readings. Then the Kalman filter combines each new reading with what it already knew, while random sample consensus, or RANSAC, ignores outliers. Every technique page also has a section on what goes wrong, which is very often about noise.

The fifth ingredient is cost functions. Because noise makes many answers possible, a technique needs a way to pick between them. Many techniques have to choose the best answer from many possible answers, and to do that they need a way to say how good each answer is, as a single number.

A cost function is that way, because it takes one possible answer and gives back one number, called its cost. A smaller cost means a better answer, so the technique's job becomes finding the answer with the smallest cost, which is called minimising the cost. Some techniques use the opposite, a score to make as large as possible, but the idea is the same.

Here is a cost function for the 20 noisy readings above, where the question is which single number best describes the distance to the mug. Take any possible answer, and subtract it from each reading. Then square each difference, so that a reading below and a reading above count the same way, and add up the 20 squares. That total is the cost of that answer, and it is called the sum of squared differences.

The page shows a table of the cost for four possible answers. As the possible answer increases, the cost falls, reaches its lowest value near the average, and rises again. For example, an answer of 405.0 millimetres has a high cost of 835.7. The cost drops to its lowest point of 104.9 for an answer of 411.0 millimetres, and then rises back up to 417.7 for an answer of 415.0 millimetres.

The right side of the picture in the previous section draws this cost for every possible answer from 400 to 424 millimetres. The curve is shaped like a bowl, and its lowest point is at 411.0 millimetres, which is the same as the average. That is not an accident, because for the sum of squared differences the lowest point is always at the average. This is the simplest case of least squares, which the least-squares fitting page uses to fit lines and planes.

Because a cost function turns a choice into a single number, it appears all through this book. First, in graph search, the cost of a route is the sum of its edge lengths. Second, in trajectory optimisation, the cost of a path adds up its length, its jerkiness and how close it comes to obstacles. Third, in assignment and matching, the cost of matching two detections is how far apart they are. Finally, in numerical inverse kinematics, the cost is how far the gripper is from where you want it.

When a technique gives a strange answer, the cost function is often the first thing to check. The technique did find the answer with the lowest cost, so if that answer is wrong, the cost function may be measuring the wrong thing.

The sixth ingredient is loops that run at a rate. A cost function says which answer is best, but a robot arm does not answer a question once and then stop. It answers the same question again and again, as fast as new readings arrive, because the camera keeps sending new pictures and the joints keep reporting new angles. So the program must use each new reading before the next one arrives.

A loop is a set of steps that repeats, and a loop that runs at a rate repeats on a fixed clock, for example 1,000 times a second. The rate is measured in hertz, which means times per second. So 1,000 hertz is 1,000 times a second, which works out as once every 1 millisecond.

The page shows pseudocode for the loop that holds one joint at its target angle. Every 1 millisecond, it reads the joint's angle sensor, calculates the error by subtracting that angle from the target angle, figures out a push command that grows with the error, and sends that command to the joint's motor. This is the shape of proportional-integral-derivative control, or PID control, which explains how to work out the push.

Each loop gives the technique inside it a time budget. At 1,000 hertz, all four steps must finish in less than 1 millisecond, because if they take longer the next reading is late and the arm stops moving smoothly. A camera loop at 30 hertz, in contrast, has about 33 milliseconds per picture. So a technique that is fine in the camera loop can be far too slow for the joint loop.

Different parts of an arm run at different rates. A joint controller often runs at 500 or 1,000 hertz, while a camera runs at 15 to 60 hertz. A planner may run only once before each move, and the logic to decide what to do next may run only when something changes. The page on choosing a technique draws these budgets side by side.

The next section explains where each building block appears in this book. Now that all six building blocks have been described, the page provides a table showing where each of them matters most. 

Frames and transforms do most of the work in the chapters on geometry and cameras, and planning and search. An example is turning the mug's camera position into a base position. 

Arrays and grids are mainly used in image and point cloud processing, and searching and matching, for example marking every depth pixel closer than 580 millimetres. 

Graphs appear mostly in planning and search, and decisions and task logic, to find things like the shortest route from home to on rack. 

Noise and uncertainty matter most in fitting and estimation, and geometry and cameras, dealing with things like 20 readings of one still mug. 

Cost functions are used in fitting and estimation, planning and search, and decisions and task logic, for example calculating the sum of squared differences. 

Finally, loops at a rate do most of the work in control and motion, and fitting and estimation, such as the 1,000 hertz joint loop.

Learned models in Book 6 use the same building blocks. A model's input is an array, and its training minimises a cost function, which Book 6 calls a loss. A trained model then runs inside a loop at a rate, as the page on running a model on a robot describes.

The final section suggests where to read next. The next page is choosing a technique, which uses these building blocks to compare techniques. In Book 1, the page on vectors and matrices for a robot arm explains the maths behind rotations and translations. The rigid transforms page takes the first section on frames and transforms into three dimensions. Finally, the page on how a model learns in Book 6 shows a cost function being used to train a model.
