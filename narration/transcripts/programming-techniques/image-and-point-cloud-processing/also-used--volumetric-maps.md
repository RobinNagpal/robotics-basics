Volumetric maps.

This page explains how a robot turns many depth pictures into one 3D map of the space round it. It answers five questions, and the first four of them follow the order in which the map is built. How is space cut into small cubes, and how is each cube marked as free, occupied or not yet seen? How does a program combine many noisy depth readings of the same cube into one answer? Why do most maps store their cubes in a tree instead of a plain grid? What are the truncated signed distance function, or TSDF, and the Euclidean signed distance field, or ESDF, and why do planners like them? And finally, which libraries do this, and which of them are used most?

It is for a reader who knows what a depth picture and a point cloud are. While a depth picture holds one distance for each pixel, a point cloud is the list of 3D points you get by turning each depth pixel into a point. That step is explained on the pinhole camera model page, and it also helps to have read about voxel downsampling, which cuts space into the same small cubes this page uses.

One depth picture only shows the surfaces in front of the camera at one moment. But a robot arm needs more than that, because it has to remember the shelf behind it after it has turned away. It also has to know that the space under its gripper is empty, and to know which space it has never seen at all. A volumetric map holds all of this, and "volumetric" means that it describes the space itself, cube by cube, and not only the surfaces.

The first section gives the idea in one sentence. A volumetric map cuts space into small cubes and, for every depth reading, marks the cubes the camera saw through as more likely free and the cube where the reading ended as more likely occupied, so that many readings add up to one steady answer.

For example, you walk into a dark room with a torch. Each time you shine it, the beam passes through empty air and stops on a wall or a chair. This means you learn two things from each beam: the air along the beam is empty, and something solid stands where the beam stopped. But corners you never shine the torch at stay unknown. After a few minutes of shining the torch round, you have a good picture of the room in your head, even though no single beam showed you much. So a volumetric map does the same with the thousands of beams in each depth picture.

The next part of the page explains how it works. The map described in the last section is built in six steps. Steps 1 to 4 build an occupancy map, which says for each cube whether it is free, occupied or unknown. Then steps 5 and 6 build two other kinds of map from the same readings. While one of them gives a smooth surface, the other gives the distance to the nearest obstacle, which is what many planners read.

All the examples here describe a slice of a table seen from above, 64 centimetres by 64 centimetres, cut into cells of 1 centimetre. A real map is 3D, with cubes instead of squares, but every step works the same way. The table holds a box, a round tin and, at the back, a wall.

Step 1 is to cut space into voxels. A voxel, short for "volume pixel", is one small cube of space. That is why the map cuts the robot's work space into voxels of equal size and keeps a few numbers for each one. The size of a voxel is called the resolution, and for a table-top arm it is usually 1 to 2 centimetres. Because a smaller voxel shows more detail, it also needs more memory and more time.

But a plain grid of voxels grows fast, because a cube of space 1 metre on each side, cut into 1 centimetre voxels, has 100 by 100 by 100, which is one million voxels. So step 4 will show how a tree cuts that number down.

Step 2 is to cast a ray for each depth pixel. Each depth pixel says that along this line from the camera, the first surface is at this distance. So the program follows that line, called a ray, from the camera to the measured point. This is called ray casting, and along the way it collects two kinds of voxel.

First, it collects every voxel the ray passes through before the end. The camera saw through them, so they are evidence for free. This is called a miss. Second, it collects the voxel where the ray ends. Something is there, so it is evidence for occupied. This is called a hit.

But voxels behind the end point get nothing, because the camera cannot see behind a surface, so they stay unknown. Unknown is not the same as free, because the space behind a box might hold another object.

The page shows a diagram of a depth camera's rays over a table, and the free, occupied and unknown cells after one view and after two. The first panel shows the real scene and every tenth ray of the camera. The camera has a 70 degree view and 141 rays, and each ray's reading has a small random error of about 3 millimetres. While the middle panel is the map after three pictures from that camera, the right panel adds three pictures from a second camera position on the right.

After the first camera, 933 cells are free, 74 are occupied and 3,089 are unknown. Most of the map is unknown, because the camera only sees a wedge of the table, and the areas behind the box and the tin are hidden. The second view sees round the tin and along the right of the table. As a result, free cells rise to 1,200, occupied cells to 109, and unknown cells fall to 2,787. But the inside of the box and the tin stays unknown in both maps, because no camera can see inside a solid object.

However, the occupied cells are not perfect lines. Where a ray grazes a surface at a shallow angle, the small reading error puts its end in the cell next door. Step 3 is how the map copes with that error.

A real program steps along each ray with a method that visits exactly the voxels the ray crosses, one after another. The usual one was published by John Amanatides and Andrew Woo in 1987.

Step 3 is to combine readings with log-odds. A single reading can be wrong, because a depth camera makes stray points at the edges of objects, and a hand can pass through the view for one frame. So a map does not say "free" or "occupied" after one reading. Instead it keeps, for each voxel, a probability: a number from 0 to 1 that says how likely the voxel is to be occupied. Every voxel starts at 0.5, which means "no idea".

Then each new reading changes that probability a little. The most common library, OctoMap, uses these default values. While a hit means the voxel is occupied with probability 0.7, a miss means it is occupied with probability only 0.4. This means that after one hit, a voxel's probability is 0.7, and after two hits it is 0.845. After one hit and then one miss it is 0.609.

But multiplying probabilities together is awkward and slow, so the map stores each voxel's value as a log-odds number instead. The odds of a voxel are its probability of being occupied divided by its probability of being free, and the log-odds is the natural logarithm of the odds. This is useful because, to combine a new reading, you simply add a fixed number.

A table on the page shows that a hit stands for a probability of 0.7 and adds 0.847 to the log-odds, while a miss stands for a probability of 0.4 and subtracts 0.405.

So every hit adds 0.847 to the voxel's log-odds, and every miss subtracts 0.405. A log-odds of 0 means a probability of 0.5. Therefore a positive log-odds means "probably occupied", and a negative one means "probably free". A voxel that was never touched by any ray stays at exactly 0, which marks it as unknown.

There is one more rule, because the log-odds is clamped. It is not allowed to go above positive 3.511, which is a probability of 0.971, or below negative 2.0, which is a probability of 0.1192. Without this cap, a voxel that was seen many times would become so certain that it could hardly change again.

A diagram shows a cell's chance of being occupied over 10 hits and then 25 misses, with and without the cap. Because a cup stands on the table for 10 depth pictures, its voxel gets 10 hits. Then the arm lifts it away, and every following picture gives the voxel a miss.

Without a cap, 10 hits give a log-odds of 8.47, a probability of 0.9998. Then it takes 21 misses before the voxel reads free again. At 30 pictures a second, the map would show a ghost cup for most of a second after the cup has gone. But with the cap, the log-odds stops at 3.511 after the fifth hit, and it then takes only 9 misses to read free. In other words, the cap costs a little certainty and buys a map that keeps up with a changing table.

Step 4 is to store the map in a tree. Most of a work space is either empty air or unknown. But a plain grid spends the same memory on a big block of empty air as on the edge of an object. So a tree avoids that waste.

An octree is a tree of cubes, and the whole work space starts as one big cube. If everything inside it is the same, it stays one cube. But if not, it is cut into 8 equal smaller cubes, and each of those is checked in the same way, down to the smallest voxel size. In 2D, the same idea cuts a square into 4 smaller squares, and then the tree is called a quadtree.

A diagram shows the same map as a plain grid of 4,096 cells and as a tree of 799 squares. The first panel is the two-view map from step 2 as a plain grid of 64 by 64 cells. While the second panel is the same map as a quadtree, it needs only 799 squares. Of these, 556 are single cells at the edges of objects and of the camera's view, 157 are 2 by 2 blocks, 66 are 4 by 4, 17 are 8 by 8 and 3 are 16 by 16. Because the big squares hold open air and unknown space, the map says exactly the same thing with a fifth of the pieces.

In 3D the saving is much larger, because a big cube holds 8 times as many voxels at each level, not 4. This is why OctoMap, the most used occupancy map, is an octree. It has a second benefit as well, because a program can ask the map at a coarser level, such as "is anything in this 8 centimetre cube?", with one look.

Step 5 explains the truncated signed distance function. An occupancy map is good for asking if a space is free. But it is poor at showing the exact shape of a surface, because each voxel is only "in" or "out". So a signed distance function stores something more precise. For each voxel it stores the distance from the voxel's centre to the nearest surface. The sign says which side the voxel is on: positive in front of the surface, in free space, and negative behind it, inside the object. This means the surface itself is where the value crosses zero.

A truncated signed distance function, or TSDF, only keeps the exact value close to the surface. So values further than a chosen truncation distance are cut off at that distance. Many libraries go further and only visit the voxels inside this thin band. Because the camera knows nothing about voxels far behind a surface, those voxels are not updated at all. So keeping only a thin layer round each surface saves work, and it stops one side of a thin object from wiping out the other.

Each new depth picture updates the TSDF by a weighted average. For each voxel near the measured surface, the program works out the signed distance from this reading, then mixes it into the stored value. For example, take one camera ray, with 1 centimetre voxels and a truncation distance of 3 centimetres. A surface stands 50.0 centimetres from the camera, and three depth readings measure it at 50.4, 49.7 and 50.2 centimetres.

A diagram shows these three readings giving three TSDF lines along a ray, and their average crossing zero at 50.10 centimetres. Take the voxel whose centre is at 49.5 centimetres. Because the first reading says the surface is at 50.4, this voxel is 50.4 minus 49.5, which is 0.9 centimetres in front of it. The other two readings give 0.2 and 0.7, so the average of the three is 0.6. The next voxel, at 50.5 centimetres, gets negative 0.1, negative 0.8 and negative 0.3, which average to negative 0.4. This means the value crosses zero between these two voxels, and a straight line between them crosses zero at 49.5 plus 0.6 divided by the sum of 0.6 and 0.4, which equals 50.10 centimetres. That is exactly the average of the three readings, and within 1 millimetre of the true surface. Because the voxels at 53.5 and 54.5 centimetres are more than 3 centimetres behind every reading, they are not updated.

This is how a TSDF turns many noisy depth pictures into one smooth surface, finer than its own voxels. A program then pulls a triangle mesh out of the zero crossing with a method called marching cubes. The method became well known through KinectFusion, published in 2011, which built live 3D models this way from a moving depth camera. The TSDF itself goes back to Brian Curless and Marc Levoy in 1996.

Step 6 covers the distance field that planners read. A planner does not need to know what an obstacle looks like. Instead it needs to know how far each point of the arm is from the nearest obstacle. So a Euclidean signed distance field, or ESDF, stores exactly that for every voxel: the straight-line distance from the voxel to the nearest occupied voxel, which is negative inside obstacles.

This is the same idea as the distance transform, which measures how far each pixel of a mask is from the nearest edge. An ESDF does it in 3D, for the free space outside the obstacles. Libraries build it from the TSDF or the occupancy map by spreading a wave out from the surfaces, one layer of voxels at a time.

The second panel of the previous diagram shows the ESDF of the two-view map, with lines at 5, 10 and 15 centimetres from the nearest obstacle. In this picture only the occupied cells count as obstacles. A planner models the arm as a set of balls. This means a ball is clear of every obstacle when the ESDF at its centre is bigger than its radius, and that is one look-up per ball, however many obstacles there are.

The picture checks two balls that stand for parts of the gripper. The ball at 50 by 13 centimetres has a radius of 4 centimetres, and the ESDF at its centre is 12.4 centimetres, so it is clear by 8.4 centimetres. But the ball at 21 by 21.5 centimetres has a radius of 5 centimetres, and the ESDF at its centre is only 4.1 centimetres. This means it overlaps the box by 0.9 centimetres, and the planner rejects that pose.

An ESDF also says which way is "away from the obstacle": the direction in which the distance grows fastest. So optimisation planners such as CHOMP use that direction to push a path away from obstacles, as explained on the trajectory optimisation page.

The page then shows the steps as pseudocode. Instead of reading the code symbol by symbol, here is what it does. The code has four main functions.

The first updates the occupancy map. For every measured point in the depth picture, it finds all the voxels along the ray from the camera to that point. For every voxel along the way, except the last one, it adds the miss value to the log-odds, marking it as seen through and therefore free, while making sure it does not drop below the minimum limit. Then, for the final voxel where the point lies, it adds the hit value to the log-odds, marking it as occupied, up to the maximum limit.

The second function reads a voxel's state. If it was never updated, it returns unknown. If its log-odds is greater than zero, it returns occupied. Otherwise, it returns free.

The third function updates the TSDF. For each measured point, it walks along the ray up to the truncation distance behind the point. It calculates the signed distance from the camera to the point minus the distance to the voxel centre, capping it at the truncation distance. It then updates the voxel's stored value using a running average based on how many times it has been updated.

The fourth function checks if the arm is clear of obstacles using the ESDF. It looks at each ball making up the arm, and if the distance field at the ball's centre is less than or equal to the ball's radius, it returns false because there is a collision. If all balls are clear, it returns true.

With OctoMap's defaults, the hit value is positive 0.847, the miss value is negative 0.405, the minimum is negative 2.0 and the maximum is positive 3.511.

The next section explains where this is used on a robot arm. The six steps above describe the map on its own, so this section shows where it sits in a real arm's software. A volumetric map sits between the depth camera and the parts of the program that must not hit anything, and there are several common uses.

First, avoiding obstacles nobody put in the model. A planning program knows the shape of the arm and of the fixed table, but it does not know about a toolbox someone left on the table. That is why MoveIt, the most used planning framework for arms, builds an OctoMap from the depth camera for exactly this, and its planners then treat every occupied voxel as an obstacle. This is described in the book's section on the planning scene.

Second, remembering what the camera cannot see now. A camera on the wrist looks wherever the gripper points, so when the arm turns to a shelf, the table behind it leaves the view. The map keeps the table's voxels, so the planner still avoids them.

Third, removing the arm from its own map. The arm is often in the camera's view, and its own points would fill the map with false obstacles right where the arm wants to move. So MoveIt removes every point that lies on the arm's known shape, plus a small margin, before it updates the map.

Fourth, planning fast with a distance field. GPU planners such as NVIDIA's cuMotion can read an ESDF built by nvblox, and optimisation planners use its distance and direction at every waypoint.

Fifth, scanning an object before grasping it. A camera on the wrist takes pictures from several sides of a part, and a TSDF fuses them into one closed mesh. A grasp planner then works on the whole shape, not only the side one picture showed.

Sixth, choosing where to look next. Unknown voxels show where the robot has not looked, so a program can pick the next camera pose that would turn the most unknown voxels into known ones. This is covered in the pages on choosing where to look, and visibility and next best view.

Finally, checking whether a space is empty. Before placing a part in a bin, the arm asks the map whether the voxels where the part will go are free, and not only "not occupied", because an unknown voxel means "look first".

But a volumetric map is not a measuring tool. As warned in the packages for measuring page, an occupancy map with 1 or 2 centimetre voxels is the model of what the arm must not hit, not the model of the part it is about to grasp. Instead the part itself is measured on the point cloud, with the methods on the clustering and RANSAC pages.

The next section covers where it is useful, and where it is not. The places in the last section all assume the same conditions. A volumetric map works best when the camera's pose is known well, the depth is good, and the scene changes slowly compared with the camera's frame rate. But it fails in a few common ways, which are listed in a table showing what goes wrong, what you would see, and what people do instead.

First, if the camera's pose is wrong, from a bad hand-eye calibration or a late joint reading, walls and objects appear twice, or smeared, and free space eats into real obstacles. Instead, you should recalibrate, use the joint angles from the same moment as the picture, or slow the arm while mapping.

Second, if the voxels are too big, the planner refuses gaps the gripper could pass through, and thin rods vanish or grow fat. The solution is a smaller voxel near the work area, or a separate precise model for the part being grasped.

Third, if the voxels are too small, the map update is slow, and memory grows. People fix this by using a larger voxel, a GPU library such as nvblox, or updating the map at a lower rate than the camera.

Fourth, glass, shiny metal or black foam cause missing hits, so a real obstacle reads as free or unknown. To handle this, treat unknown space as blocked near the arm, add the object as a known shape, or look into methods for the depth hole.

Fifth, objects that move quickly, such as a person's hand, leave ghost obstacles that stay after the hand has gone, or a hand that is missed. This is handled by clamping, as in step 3, clearing the map before each plan, or using a separate safety sensor for people.

Sixth, if the arm's own body is not fully removed, you see a cloud of false voxels round the gripper, and the planner reports that the start pose is in collision. The fix is a larger removal margin, and checking the arm model and the camera's pose.

Finally, if unknown space is treated as free, the planner sends the arm into space no camera has seen. Instead, mark unknown voxels near the path as obstacles, or look there first.

The next section lists libraries that provide it. None of the six steps has to be written from scratch, because four libraries do most of this work for robot arms.

The first is OctoMap, used from C++ with ROS wrappers. It builds a log-odds occupancy octree, with the clamping of step 3. It is the most used occupancy map for arms, because MoveIt uses it. MoveIt's occupancy map monitor builds it from a point cloud or a depth picture.

The second is Open3D, used from Python and C++. It builds a TSDF and a mesh from its zero crossing. It is the most used way to fuse depth pictures into a mesh in Python, for scanning an object or a scene for a digital twin. It does not build an ESDF for planning.

The third is nvblox, used from C++ on an NVIDIA graphics card, Python, and ROS 2 through Isaac ROS. It builds a TSDF, an ESDF and a mesh, updated on the graphics card many times a second. It is used in NVIDIA's robot stack, and needs an NVIDIA card.

The fourth is voxblox, used from C++ and ROS 1. It builds a TSDF, then an ESDF built from it step by step as new pictures arrive. It is used in research and flying robots, where it began. It is written for ROS 1 and there is no official ROS 2 version, so new arm projects rarely start with it.

In plain words: if you use MoveIt, you already use OctoMap, and it is the one to learn first. But if you want a clean 3D model of an object or a scene from a handful of depth pictures, use Open3D's TSDF. And if you have an NVIDIA card and a planner that reads a distance field, use nvblox. Since voxblox is the older CPU version of the same idea as nvblox, you will meet it mainly in papers.

In MoveIt, the map is set up in a configuration file usually called sensors 3D dot yaml. It names the sensor plugin, such as the point cloud octomap updater, the topic to read, the maximum range, and the margin used to remove the arm's own body. But the voxel size is a separate setting, called the octomap resolution.

The next section asks why a volumetric map, and what it costs. The libraries in the last section make a volumetric map easy to build. So this section asks whether you need one at all. It answers the four questions for this technique: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

A volumetric map is a grid of small cubes, often stored as a tree, in which each cube holds either a probability of being occupied or a distance to the nearest surface. Then every depth picture updates it by casting rays from the camera.

What it does for you is give one steady answer, built from many noisy pictures, to three questions: is this space free, is it occupied, or has the robot not looked there yet? It also remembers space the camera no longer sees. And, with a distance field, it tells a planner how far every point is from the nearest obstacle in one look-up.

The obvious alternative is to skip the map and use the latest point cloud directly as the obstacle. That is simpler and has no delay, and some collision checkers can take a point cloud. But a single cloud has holes, stray points and no memory, so it says nothing about the space behind objects, or about space that left the view a second ago. And it cannot tell "free" from "not seen", which is the difference between safe and unsafe. So choose the raw cloud when the scene is fully in view and nothing is hidden. But choose a map when the camera moves, when parts of the scene are hidden, or when the robot must be sure a space is empty.

A second alternative is a learned model that fills in the 3D shape, and the next section compares the two.

The costs of a volumetric map come in several parts. Because the map is only as good as the camera's pose, it needs a good calibration and exact timing. You must also choose the voxel size, which is a trade between detail, speed and memory. Since a 3D map at 1 centimetre has up to a million voxels per cubic metre, updating it at the camera's full rate takes real computing time. This is why nvblox moves that work to the graphics card. Moving objects leave ghosts unless the map is clamped or cleared. And the map is coarse by design, because it tells the arm what not to hit, not the exact shape of what to grasp.

The next section covers the learned alternative. Section 6 named a learned model as the second alternative, so this section says what those models can and cannot do. No model replaces the map as the record of free, occupied and unseen space, but three kinds of model help it. For example, a shape completion model guesses the hidden back of an object from one view, where the map keeps it as unknown. Then scene reconstruction builds a 3D scene from colour photos, so it sees glass and shiny surfaces that leave holes in a depth map. But it takes seconds to minutes, and the scene must stay still. A learned collision checker gives a fast distance to obstacles like an ESDF. But it is least reliable near the edge of an obstacle. So for collision avoidance the map still wins, because it never guesses: it keeps unseen space as unknown, and that honesty is what keeps the arm safe. In practice the map and the models are often used together.

The final section suggests where to read next. The clustering page covers voxel downsampling, the same grid of cubes used to thin a point cloud. Morphology and the distance transform explains the 2D distance transform that an ESDF extends to 3D. Sampling-based planning explains the collision checks that read this map, and trajectory optimisation uses the distance field to push a path away from obstacles. Visibility and next best view uses the unknown voxels to choose where the camera should look. Choosing where to look casts rays in 3D to test what a camera can see. The chapter overview compares all the techniques in this chapter. And finally, the diagrams on this page are drawn by a Python script in the documentation. Every number on the page comes from the functions in that script; you can run it with a numbers flag to print them.
