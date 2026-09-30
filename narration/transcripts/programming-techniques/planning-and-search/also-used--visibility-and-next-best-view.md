Visibility and next-best-view. This page explains two linked techniques. The first is visibility, which means working out what a camera can see from a given place, and what is hidden behind something. The second is next-best-view planning, which means choosing where to put the camera next. This is done so that it sees as much as possible of what the robot does not know yet. The page answers four questions, and the first two are about the technique itself. How do you test whether one object hides another, and how do you score a place to look from? Then come the practical ones: where does a robot arm use these, and when is a fixed list of views the better choice?

It is for a reader who has read the chapter overview and knows what a camera pose is, at the level of the pinhole camera model. You do not need any geometry beyond a straight line and a circle. Every number on this page comes from a real run of a planning and search script.

Book two's page on choosing where to look covers the same subject from the camera's side, with real camera sizes and measured timings. This page is instead the technique underneath it, which means the test itself and the loop that uses it.

The first section gives the idea in one sentence. A camera sees a point only if the straight line from the camera to that point passes through nothing on the way. To choose where to look next, test that line for every point you still know nothing about, from every place the camera could go. Then go to the place that would show you the most.

An everyday example shows the idea before any robot arm is involved. You are looking for your keys on a crowded shelf, and from where you stand a tall vase hides a patch of the shelf behind it. You do not know whether the keys are in that patch, so you think about where to stand instead. Standing a step to the left would show you the patch behind the vase. However, standing on a chair would show you the whole shelf top, but the chair is in the next room. So you take the step to the left, because it shows you the most for a place you can actually get to. Then you look again from the new place and decide again.

That everyday choice is already the whole technique. The rest of this page then makes each part exact: what passing through nothing means for a real shape, how to count what a view would show, and how to handle the places the arm cannot reach.

The next part explains lines of sight and shadows. Before any of that can be counted, the two words the whole page rests on need definitions. A line of sight, also called a sight line or a ray, is the straight line from the camera's centre to a point in the scene, and light travels along it. So if an object sits across that line, the point is occluded, which means hidden.

Each object therefore hides a region behind it, and this region is called its shadow, or its occlusion shadow. It is the same shape as a real shadow would be if the camera were a lamp, and the camera cannot see anything inside it.

The scene on this page is a row of four upright cylinders on a table, with all units in centimetres and the table top at height zero. A table lists them, showing where each cylinder's centre is along the table, its radius, and its height. For example, the first object is bottle one, at thirty-five centimetres along the table, with a radius of four centimetres and a height of thirty centimetres. Further along are a short cup, a second bottle, and another short cup at the end.

A diagram shows the row from the side, where each cylinder appears as a rectangle. The grey regions are the shadows. The script found them by testing the sight line to every point on a two point five millimetre grid, from the table to forty-five centimetres up. The diagram shows that a camera at the side sees only the front of the first bottle, while a camera above sees nearly everything.

On the left of the diagram, the camera is at the side of the table, twenty centimetres up, which is lower than the first bottle. So the first bottle's shadow covers everything behind it, meaning both cups and the second bottle. As a result, fifty-five percent of the free space in the dashed box is hidden. The camera cannot see the top of any object, so it would report one bottle and nothing else.

On the right, the camera is sixty centimetres above the middle of the table, looking down. Each bottle now casts a thin shadow that leans away from the camera, so only eleven percent of the free space is hidden. The camera sees the tops of both bottles and the first cup. It sees only a small part of the top of the second cup, because the second bottle's shadow falls across it.

Two things follow from this picture, and both of them matter later. First, a tall object close to the camera hides far more than a short object further away. Second, the same scene can be almost invisible from one place and almost fully visible from another, which is why it is worth choosing where to look at all.

The next section covers how it works, step by step. Now that shadows have a definition, the technique that uses them has two layers. The lower layer is a test that answers one question: is this one point visible from this one camera position? The upper layer is a loop that uses the test many times, to score each place the camera could go and then pick the best.

First, testing one sight line against one cylinder. Many objects on a table are close to upright cylinders, such as bottles, cups, cans, jars and posts. An upright cylinder has a very simple exact test, and it is exact because it uses the real shape rather than a grid of points. A test like this, done with a formula rather than by trying many points, is called an analytic test.

You can write every point on the sight line as a formula: the point at a value t equals the camera position plus t times the difference between the target and the camera. The number t says how far along the line the point is. At t equals zero the point is at the camera, at t equals one it is at the target, and halfway along t is zero point five.

A point is inside a solid upright cylinder when two things are true at the same time. First, seen from above, it is inside the circle. Ignore the height. The distance from the point to the cylinder's centre line must be less than the radius. Putting the point formula into the circle's equation gives a quadratic equation in t: an equation with a t squared term, a t term and a plain number. Its two answers are where the line enters and leaves the circle. If it has no answers, the line misses the circle completely.

Second, seen from the side, it is between the table and the top. Ignore the circle. The point's height must be between zero and the cylinder's height. The height changes in a straight line with t, so this gives one more stretch of t.

Each test gives a stretch of t, called an interval. So the cylinder blocks the sight line only if the two intervals overlap. That overlap must also lie between the camera and the target, which means somewhere between t equals zero and t equals one.

It is tempting to test from above only, or from the side only, but both are wrong on their own. For example, a sight line seen from above can cross a cup's circle while passing well over the cup's top. Seen from the side, a sight line can cross a bottle's rectangle while passing beside the bottle. The next example shows both mistakes on the same scene.

For a box whose sides line up with the table, the same idea works with three intervals, one for each direction. That is the slab method explained in book two's page on choosing where to look.

The page then gives a worked example with two sight lines. To see the two traps in action, put a camera at the left end of the table, ten centimetres in front of the row of objects and thirty centimetres up. Its position is zero, minus ten, thirty, where the first two numbers are the position on the table and the third is the height. The red sight line goes to the middle of the top of the first cup, at fifty, zero, ten. The green sight line goes instead to the middle of the top of the second bottle, at seventy, zero, twenty-six.

A diagram shows that each sight line is blocked only when being inside the circle and being below the top happen at the same t.

Here is the red line against the first bottle, worked by hand, where the first bottle's centre is at thirty-five, zero and its radius is four. First, the line moves fifty across, ten sideways and minus twenty in height from the camera to the target. Second, from above, the circle equation becomes two thousand six hundred t squared minus three thousand seven hundred t plus one thousand three hundred and nine equals zero. Its two answers are t equals zero point six six and t equals zero point seven six. So the line is inside the circle from sixty-six percent to seventy-six percent of the way along. Third, from the side, the height is thirty minus twenty t. It is below the bottle's top of thirty centimetres for every t above zero, and it reaches the table at t equals one point five. So the line is below the top from t equals zero to t equals one point five. Finally, the two intervals overlap from t equals zero point six six to t equals zero point seven six. That is between the camera and the target. So the first bottle blocks the red line, and the camera cannot see the top of the first cup.

The green line then gives the two opposite traps, one for each incomplete test. Against the first cup, it is inside the circle from t equals zero point six eight to t equals zero point seven six, but it is below the cup's top only from t equals five point zero onwards, far past the target. Over that stretch the line is about twenty-seven centimetres up, while the cup is only ten centimetres tall. There is no overlap, so the first cup does not block it, although a test from above alone would have said it did. Against the first bottle, it is below the top all the way, because the camera is at the same height as the bottle's top. However, from above it never enters the first bottle's circle, so the first bottle does not block it either, although a test from the side alone would have said it did.

The script tests both lines against all four cylinders. The red line is blocked by the first bottle only, while the green line is blocked by nothing, so the camera can see the top of the second bottle.

The test costs one square root and a few multiplications per cylinder. Book two measured the box version at about forty nanoseconds per obstacle. So a program can test thousands of sight lines against dozens of objects in well under a millisecond.

The next part is about choosing where to look next. With a cheap test in hand, the upper layer can afford to run it everywhere, and that loop is called next-best-view planning. The pose it chooses is the next best view, and these are its steps.

First, keep a record of what you do not know yet. The usual record is a grid of small cells covering the work area, where each cell is marked free, occupied or unknown, and at the start every cell is unknown. The page on volumetric maps covers these grids.

Second, list the candidate poses. A candidate is one place the camera could go, together with the direction it would face. A common choice is a ring or a half-sphere of points around the work area, each one facing its centre.

Third, remove the ones the arm cannot reach. The cheapest check is distance, because a pose further from the arm's shoulder than the arm is long is out. A stricter check asks inverse kinematics for joint angles that put the camera there.

Fourth, predict what each one would reveal. For each remaining candidate, test the sight line to every unknown cell, and count the cells that are inside the camera's picture and not hidden. This count is the candidate's gain, and the gain can also be the number of objects not yet seen, or any other count of new information.

Fifth, take the best. Move the camera to the candidate with the highest gain, take a picture, and mark every cell it saw as known.

Finally, repeat from step four, because the gains have changed. Stop when the budget runs out, or when no candidate would reveal enough to be worth the move.

The last step is the one that matters, because after the first view the cells it saw are no longer unknown. So a candidate that looks at the same region from nearly the same place now gains almost nothing, even though it scored well in round one.

The page gives a worked example with eleven candidate views. To see that recounting happen, the scene is the same row of four cylinders, seen from the side. The unknown space is the region from the table to thirty-two centimetres up, over the whole one hundred centimetres of table, cut into two centimetre squares. So leaving out the squares inside objects makes six hundred and twenty-nine unknown cells.

There are eleven candidate views, and they sit on a half circle of radius fifty-five centimetres around the middle of the table, every fifteen degrees from fifteen degrees to one hundred and sixty-five degrees. The angle is measured from the right-hand end of the table, and each camera faces a point five centimetres above the middle of the table, with a picture seventy degrees wide. The arm's shoulder is ten centimetres to the left of the table, and the arm can hold the camera at most one hundred centimetres from the shoulder. The budget for the whole loop is three views.

A diagram shows the eleven candidate cameras. It shows that three are out of reach, and the one at one hundred and five degrees would see the most unknown cells.

Step three removes the three candidates at the right-hand end, because they are more than one hundred centimetres from the shoulder. The one at sixty degrees is ninety-nine point six centimetres away, so it just stays in.

Step four then gives the round one gains. The candidate at one hundred and five degrees has the highest gain in round one, seeing two hundred and eighteen unknown cells. The loop then runs three rounds.

Round one takes the view at one hundred and five degrees, which would see two hundred and eighteen cells. That is thirty-five percent of the unknown space.

Round two recounts. The views at seventy-five degrees and ninety degrees looked strong in round one, with one hundred and ninety-four cells each. Now they would add only twenty-two and seventeen, because most of what they see was seen from one hundred and five degrees. The view at one hundred and thirty-five degrees adds one hundred and twenty-nine, because it sees the space just left of the first bottle, which was in its shadow from one hundred and five degrees, and a strip high up at the right-hand end. The known space rises to three hundred and forty-seven cells, which is fifty-five percent.

Round three takes one hundred and sixty-five degrees, a low view from the left end of the table. It adds seventy-two cells near the table at the left end, so the known space rises to four hundred and nineteen cells, or sixty-seven percent.

A diagram illustrates these three rounds, showing that each takes the view that adds the most unknown cells, so later views fill in what earlier ones missed.

After three views, most of the right-hand end is still unknown, and the reason is reach. The views that look into the region behind the second bottle from the right are the three out-of-reach candidates, and the one at forty-five degrees alone would see one hundred and ninety-five cells. So a robot in this position would need to move its base, or accept that the right-hand end stays unknown. The loop tells you this plainly, which is useful in itself.

The page then provides pseudocode for the whole loop. It defines a function to check if a cylinder blocks a line by finding where the line is inside the circle from above, and where it is between the table and the top. If those two stretches overlap between the camera and the target, the line is blocked. A second function checks if a camera sees a cell by making sure it is in the picture and not blocked by any object. The main loop takes the reachable candidates and repeats for the given budget. In each round, it counts how many unknown cells each candidate sees. It picks the best one, stops if the gain is too small, and otherwise moves the camera, updates the map, removes the seen cells from the unknown list, and records the chosen view.

On a real robot, the step that updates the map uses the real picture rather than the prediction, because the prediction assumed that unknown cells are empty. If the picture shows a new object, the map gains an occupied region, and that object will cast its own shadow in the next round's predictions.

The next part is about choosing several views at once. The loop above chooses one view, looks, and then chooses again, which is right when each picture can change the plan. Sometimes the objects are known in advance instead, and the task is to pick a fixed set of views, all at once, that together see everything.

That is a different problem called set cover. In it, each view is a set of things it sees, and you want the fewest sets that together cover everything. The same greedy rule solves it well, because you take the view that adds the most, then the next, and so on. The page on greedy algorithms and set cover works an example with eight glasses and shows how far from the best the greedy choice can be. The visibility test on this page is what builds the sets that page takes as given.

The next section explains where this is used on a robot arm. Both layers earn their place, but in different tasks, so here are the places where an arm cell uses a visibility test or a full next-best-view loop.

First, throwing away useless camera poses early. Before any view reaches the motion planner, the visibility test removes the ones from which the target is hidden. Book two's worked scene removed sixty-two percent of the views that had passed every other check, in its section on occlusion.

Second, picking a small fixed set of views for a cell. When the objects are roughly known, an engineer runs the visibility test on many candidates once, offline, and keeps two or three good ones, so the arm then drives to them by name every cycle.

Third, looking into a bin or a shelf. The sides of a bin, and the objects near the front of a shelf, hide what is behind them, so a next-best-view loop with an unknown grid finds a view down past the edge.

Fourth, finding a hidden object. When the object the robot needs is not in the first picture, the unknown cells are the only places it can be, so the loop scores views by how many of those cells they would show.

Fifth, building a model of an unfamiliar object. To scan an object it has never seen, the robot needs many views, and each new view should show surface that the earlier ones missed. This is the job next-best-view planning was invented for.

Sixth, checking a grasp before committing. A grasp chosen from a single view may land on a side the camera never saw, so a second view aimed at that side, chosen by the same test, confirms the surface is there.

Finally, keeping the camera's view clear while the arm moves. A camera on a post can be hidden by the arm itself, so the same sight-line test, with the arm's links as the obstacles, tells the planner which arm poses would block the camera's view of the gripper.

The next part covers where it is useful, and where it is not. Those uses divide along one line, and it is worth saying which side each falls on. The visibility test is exact for the shapes it models. However, the next-best-view loop is only as good as its record of the unknown and its list of candidates. A table lists the common problems, the signs you would see, and what people do instead.

The most important problem is when the task needs only one or two views. The sign is that the loop runs once, and costs an extra move and a map for no gain. Instead, people use a fixed set of views chosen offline.

Another problem is when objects are not simple shapes, so the test says a view is clear, but a handle or a lid blocks it. The fix is to wrap each object in a slightly larger cylinder or box, or ray-cast against a mesh.

If the test uses footprints only, ignoring height, views over short objects are thrown away although they were fine. The fix is to test in three dimensions, with the height interval.

If the best view is out of reach, the gains are high but the arm cannot get there. You should check reach before scoring, move the base, or accept what is left unknown.

If every move is slow, the loop finds good views but the cycle time doubles. Instead, use a fixed set, or divide the gain by the time to reach the view.

If the scene changes between pictures, cells marked known are now wrong. You must re-mark cells as unknown after a set time, or re-scan the changed region.

If candidates are too few, or all at one height, the loop stops with large regions still unknown. You need to add candidates at other heights and angles.

If gains assume unknown cells are empty, a view that should see behind a box sees a new object instead. There is nothing to fix here: just update the map from the real picture and score again.

Finally, if the number of rounds varies with the scene, the cycle time is different every run and hard to guarantee. You can cap the budget, and fall back to a fixed set when the cap is reached.

The first row is the most important one. Book two counts the views each task needs and finds that most arm tasks need one or two. A fixed set of views can also be tested and signed off, which a loop that decides at run time cannot. So the visibility test is almost always worth having, while the full loop is worth having only when the robot genuinely does not know what is in front of it.

The next section lists libraries that provide it. Because both layers are short, the cylinder test and the loop on this page are a few dozen lines of plain code. So no library is needed for them. The libraries listed give you ray casting against more complex shapes, or the grid of unknown cells. Open 3D and trimesh provide ray casting against meshes in Python and C++. MuJoCo and PyBullet provide ray casts against every shape in a simulated scene. OctoMap is the standard C++ library for the free, occupied and unknown grid, where cells cost little when empty. PCL marks which cells of a voxel grid are hidden from a camera. Finally, MoveIt 2 has a visibility constraint that asks the planner to keep a sensor's view of a target clear. Book two's libraries section gives the licence of each of these and says which run on an Apple Silicon Mac.

With the test, the loop and the libraries covered, the next section answers the four questions for visibility and next-best-view planning. What is it, what does it do for you, why choose it rather than the obvious alternative, and what does it cost?

The visibility test checks whether a straight line from the camera to a point passes through any object. For simple shapes such as upright cylinders and boxes, it is an exact formula. Next-best-view planning then uses that test to score candidate camera poses by how much new they would show, and takes the best one and repeats.

What it does for you is replace guessing with counting. Without it, a program chooses a view, drives there, takes a picture, and only then finds out the target was behind a bottle. With it, the program knows before the arm moves at all. Each wasted move costs between a few hundred milliseconds and a couple of seconds on a real arm, while the test itself costs microseconds.

The obvious alternative is to render each candidate view, which means drawing the whole scene as a picture from that pose, as a game engine would, and looking at the picture. That works for any shape and gives a full image. However, it is far slower than a few sight lines, and it needs a full model of the scene. For the question of whether a target is hidden from here, a handful of sight-line tests answers it exactly. So choose rendering when you need the whole predicted picture, for example to predict what a detector will see. Choose sight lines instead when you need a yes or no, or a count.

The second alternative is to skip the loop and use a fixed list of views, which for most arm tasks is the better choice, as the previous section says. The loop earns its place only when the robot does not know the scene in advance.

The costs come in four parts. First, you must model each object as a simple shape, and a shape that is too small lets a blocked view through. Second, the loop needs a record of the unknown space, which is a map you now have to keep correct. Third, its cycle time depends on the scene, so it is harder to promise a fixed time per task. Fourth, its choices are only as good as its candidate list, because it cannot choose a view you did not offer it.

The next section discusses the learned alternative. Since the test is written by hand, the last question is what a learned model would do in its place. There is no learned model in book six that replaces the sight-line test. This is because the test is an exact formula that runs in microseconds, and a network could only copy it less exactly. The nearest learned alternative is instead to skip the extra view altogether. A shape completion model guesses the hidden back of an object from one picture. So it wins when the camera cannot get round the object, such as in a bin or on a shelf, or when every extra move costs too much time. However, the back it gives is invented rather than measured, so book six's rule is to use completion when you cannot look, and to look when you can afford it. The two also work together, because a model's low confidence is the signal to look again, and this page then chooses where.

The final section suggests where to read next. Book two's page on choosing where to look applies this page with a real camera, covering distance, viewing angle, reach, and the order in which to visit the chosen views. The page on greedy algorithms and set cover explains picking several views at once, and how far greedy can be from the best. The page on volumetric maps covers the grid of free, occupied and unknown cells that the loop scores against. Numerical inverse kinematics is the stricter reach check for each candidate view. Sampling-based planning plans the arm's move to the chosen view. Finally, book two's page on the wrist camera covers what a view costs and how many views each task needs.
