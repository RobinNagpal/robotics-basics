Rigid transforms.

This page explains rigid transforms as a technique you can use in any program, and it answers five questions. How do you move a point from one frame into another? How do you store a turn and a shift together? How do you join several frames in a chain, and undo one? What is a quaternion, in plain words? And how do you blend smoothly from one orientation to another?

It is for a reader who has met frames and transforms in Book 1. The page on position, frames and transforms builds them by hand on a flat arm, and the page on vectors and matrices introduces the four-by-four matrix. This page does not rebuild those ideas, but instead writes them as one general method in 3D, adds quaternions and blending, and shows where each piece is used on a real arm with a camera.

The first section gives the idea in one sentence. A rigid transform is one turn followed by one shift, and it moves every point of a frame together without stretching or bending anything.

A frame is a starting point with three axes, fixed to one physical thing such as the table, the arm's base, the camera or the gripper, so a position always belongs to one frame. The word rigid means that distances and angles do not change, which is why a box that is 6 centimetres wide in the camera's frame is still 6 centimetres wide in the base's frame.

So think of an everyday example. Carry a tray with three cups across a room, and each cup stays at the same place on the tray while only the tray moves. To say where a cup is in the room, you need the cup's place on the tray and the tray's place in the room. That tray's place in the room is the rigid transform, because the cup's place on the tray never changes.

On an arm, the camera plays the part of the tray. The camera reports each object in its own frame, but the arm needs it in the base frame, so a rigid transform does the move.

The next section explains how it works. Because a transform is one turn and one shift, this section builds it as arithmetic. It takes the pieces in the order you use them: the turn, then applying a turn and a shift, then storing both in one matrix, undoing it, and joining several, while quaternions and blending come last.

The examples use the scene from Book 2, where a camera hangs 0.40 metres above the middle of a table, looking straight down. The world frame sits at the middle of the table, with z pointing up, while the arm's base frame sits 0.35 metres to the left and 0.10 metres back from the middle, turned 30 degrees about z. The spot on top of the red box is at 0.06442, -0.04110, 0.340 metres in the camera's frame, as the pinhole camera model page worked out, and all the numbers were checked in Python.

First, the turn, which is a rotation matrix. A rotation matrix is a three-by-three grid of numbers that turns a point about the frame's starting point. Its three columns are where the frame's x, y and z axes end up after the turn. Book 1 explains why the columns are the turned axes.

The camera above the table has a specific rotation relative to the world. Read by columns, the camera's x points along the world's x, which is 1, 0, 0. The camera's y, which points down the picture, points along the world's negative y, which is 0, -1, 0. The camera's z, which points out of the lens, points along the world's negative z, which is 0, 0, -1, meaning straight down at the table.

A rotation matrix is a special grid, because each column has length 1 and each column is at right angles to the other two. This matters in practice, because if you round a rotation's numbers it stops being a rotation. For example, rounding a 30 degree turn from 0.866 to 0.87 makes every turned point 1.0034 times too far out, which is 0.34 millimetres at 10 centimetres. So keep full precision, or store the rotation as a quaternion, which is described below.

Next is applying a transform, which means a turn, then a shift. A transform from frame A to frame B holds B's rotation and B's position, both measured in A. It is written T_A_B, and you read it as B, seen from A. Applying it to a point measured in B gives the same point measured in A. The formula is that the point in A equals the rotation times the point in B, plus the shift. The turn comes first, then the shift. Book 1 shows why the other order gives a different answer.

For example, take the transform of the camera seen from the world. Its rotation is the matrix we just described, and its shift is 0, 0, 0.40, because the camera is 0.40 metres above the table's middle. Turning the spot on the box gives 0.06442, 0.04110, -0.340. Adding the shift gives 0.06442, 0.04110, 0.060. So the spot is 0.060 metres above the table, which is the height of the box, and nothing in the arithmetic was told how tall the box is. Book 2 reaches the same answer by walking along the camera's axes.

Programs keep the turn and the shift together in one four-by-four matrix. The rotation fills the top-left three-by-three block, the shift fills the last column, and the bottom row is always 0, 0, 0, 1.

To apply it, write the point with a 1 on the end, and multiply. The 1 picks up the shift column, so the turn and the shift happen in one multiplication. This form is called homogeneous coordinates, and its real value is that joining two transforms becomes one matrix multiplication.

A direction, such as a surface normal or a velocity, is written with a 0 on the end instead of a 1. The 0 skips the shift column, so a direction is turned but not moved. Mixing these up is a common bug: a surface normal that gets shifted by 0.40 metres points somewhere meaningless.

Next is undoing a transform. The arm wants the spot in its base frame, not the world frame. We know the base seen from the world, which is turned 30 degrees about z and shifted to -0.35, 0.10, 0, so we need the opposite, which is the world seen from the base.

Undoing a rigid transform is cheap, because a rotation's inverse is just its transpose, which is the grid flipped across its diagonal. The inverse shift is the negative of that transpose multiplied by the original shift. Applying this inverse to the spot in the world frame gives 0.3294, -0.2582, 0.060 in the base frame. In other words, you take away the base's position, and then turn back by 30 degrees.

Never undo a transform by inverting the four-by-four matrix with a general-purpose inverse routine. It works, but it is slower, and small rounding errors creep into the rotation block, while the transpose rule is exact.

Next is joining frames in a chain. Two transforms that meet at a shared frame join into one, by multiplying their matrices. For example, the camera seen from the base equals the world seen from the base multiplied by the camera seen from the world. The names show whether the order is right, because written this way the inner names match, with world next to world, and the outer names give the answer, which is base and camera. So the result takes a point in the camera's frame straight to the base frame.

The first diagram on the page shows one spot on the box, seen from above, with its numbers in all three frames. All three triples describe the same spot. The camera's triple says 0.340 metres in front of me, the world's says 0.060 metres above the table, and the base's says 0.329 metres ahead of me and 0.258 metres to my right. A grey cross shows what happens if the two transforms are joined in the wrong order. The arm then reads a target that is 0.589 metres from the real spot, and no error message warns about it.

A camera on the arm's wrist makes a longer chain, and one link of it changes every time the arm moves. The point in the base frame equals the flange seen from the base, times the camera seen from the flange, times the point in the camera frame. The flange seen from the base comes from the joint angles, by forward kinematics, and it says where the arm's last mechanical face, the flange, is. The camera seen from the flange is fixed instead, and comes from hand-eye calibration.

The second diagram shows this chain with the flange 0.45 metres above the base, pointing straight down, and the camera 0.06 metres along the flange's x axis. The same camera reading as before now lands at 0.5244, 0.0411, 0.110 in the base frame. The reading did not change, because only the chain behind it did. This is how every wrist camera turns what it sees into a place the arm can reach, and it must use the flange pose from the moment the picture was taken, not the moment the calculation runs.

Next is quaternions, in plain words. A rotation matrix uses nine numbers to describe something that has only three degrees of freedom, which is more numbers than the job needs. So robot software usually stores a rotation as four numbers instead, called a quaternion.

The idea behind it is simple, because every rotation, however complicated, is one turn by some angle about some single axis, and this fact is known as Euler's rotation theorem. So a quaternion stores that axis and that angle. The x, y, and z values are the axis direction times the sine of half the angle. The w value is the cosine of half the angle.

The third diagram shows the two rotations in this page's scene. The arm's base is turned 30 degrees about z, so its axis is 0, 0, 1 and half the angle is 15 degrees. This makes the quaternion 0, 0, 0.2588, 0.9659. The camera is turned 180 degrees about x, so its axis is 1, 0, 0 and half the angle is 90 degrees, which makes the quaternion 1, 0, 0, 0. That half turn is what makes the camera look down, because its y and z both flip.

Four facts are enough to use quaternions safely.

First, the four numbers always have a length of 1. That is, x squared plus y squared plus z squared plus w squared equals 1. If rounding or averaging breaks this, divide all four by their length. This one step is much simpler than repairing a rotation matrix.

Second, a quaternion and its exact negative are the same rotation. So never compare quaternions number by number, and compare the rotations they make instead.

Third, the order of the four numbers differs between libraries. ROS and SciPy put w last, while MuJoCo and Eigen put w first. Reading one as the other gives a wrong rotation with no error, and Book 3 lists who uses which.

Finally, you do not have to multiply them by hand. Every library converts a quaternion to a rotation matrix and back, putting the numbers in the usual places.

The other common way to write a rotation is three angles, such as roll, pitch and yaw. They are easy to read, which is why URDF files and user interfaces use them. But they need a stated axis order and convention, and at some poses two of the three axes line up so that one direction of turning is lost, which is called gimbal lock. So use three angles for people to read and type, and convert to a quaternion or a matrix for the arithmetic. Book 3 covers the convention problem in detail.

Next is blending two orientations. A motion from one gripper orientation to another needs the orientations in between. The obvious way is to blend the numbers directly, so that at the halfway point you take half of each. However, for rotations this goes badly wrong.

The fourth diagram blends from a turn of 0 degrees to a turn of 90 degrees about z, and follows the tip of the turned x axis. Blending along the circle keeps equal steps, so at a quarter, half and three quarters of the way they are at 22.5, 45 and 67.5 degrees, and the axis keeps its length of 1. This is called spherical linear interpolation, or slerp for short. Blending the matrix numbers in a straight line instead means the motion speeds up and slows down, and the axis shrinks to 0.707 of its length at halfway. A shrunken axis is not a rotation at all.

For quaternions, slerp finds the angle between them using the dot product of the four numbers. If the dot product is negative, you flip the sign of one quaternion first to pick the shorter way round. Without it the gripper can swing the long way, nearly a full turn. When the two are almost equal, you blend the numbers directly and then set the length back to 1.

The page then provides pseudocode showing the whole technique in plain steps. It defines a transform as a rotation and a shift. It shows how applying it to a point adds the shift, while applying it to a direction only turns it. It shows joining by multiplying the matrices, inverting by using the transpose, converting a quaternion by forcing its length to 1 first, and blending with slerp by checking the dot product for the shortest path.

The third section covers where this is used on a robot arm. Rigid transforms appear everywhere a number crosses from one part of the robot to another. They are used to move every camera detection into the base frame. They are used in forward kinematics, where the gripper's pose is the product of one transform per joint, from the base outwards. They turn the flange into the tool centre point. They move grasp poses stored in an object's frame into the base frame. They merge point clouds from different camera views. They turn force sensor readings into the base frame, treating the force as a direction so it is turned but not shifted. They blend smooth orientation changes for trajectory generation. And they are the core of ROS's TF system, which keeps a tree of every frame on the robot and joins transforms on request.

The fourth section explains where it works, and where it goes wrong. The arithmetic of rigid transforms is exact, so the mistakes come from feeding it the wrong things, and each mistake has a sign you can look for.

If two transforms are joined in the wrong order, the answer is off by tens of centimetres, often in a plausible-looking place. You fix this by naming every variable with its parent and child frames, and checking that the inner names match. If a transform is used in the wrong direction, the answer is mirrored or rotated. If a quaternion is read in the wrong order, objects appear turned by large, odd angles. If a rotation drifts from being a rotation, lengths grow or shrink slowly over many joins, which you fix by renormalising the quaternion. If a direction is shifted as if it were a point, surface normals and forces point the wrong way. If a wrist camera's picture is paired with the wrong arm pose, points smear or jump while the arm moves, and you fix this by looking up the flange pose at the picture's exact timestamp. If degrees are read as radians, turns are 57 times the intended size. And if everything is consistently off by a few millimetres or a degree, the transform itself is wrong, which is a calibration problem that arithmetic cannot fix.

Rigid transforms work only for rigid things, because a cable, a soft gripper finger or a bending arm under a heavy load does not move rigidly, and a rigid transform will then describe it only approximately.

The fifth section lists libraries that provide it. Every robotics stack provides rigid transforms, and you should use one rather than writing your own. For C++, Eigen is the base of MoveIt and most robotics code, though its quaternion constructor takes the w value first. SciPy is used in Python, converting between formats and putting w last by default. ROS provides tf2 for both languages, which keeps the whole frame tree and joins transforms for you at a given time. Pinocchio and KDL provide transforms alongside kinematics. Open3D and PCL apply a four-by-four matrix to a whole point cloud. And NumPy is enough for simple arrays in small Python programs.

The sixth section asks why transforms, and what they cost. A rigid transform lets every part of the robot describe positions in its own simplest frame, and lets any program ask for any position in any other frame. The obvious alternative is to write one formula for each question, but every new joint or new question means a new formula. With transforms you describe each part once, against its neighbour, and let joining do the rest. Another alternative is storing orientations as three angles, but they depend on conventions, lose a direction at gimbal lock, and cannot be blended correctly.

The cost is that each transform has a direction, and each quaternion library has an order, and neither of those is visible in the numbers themselves. A wrong one gives a plausible answer rather than an error. So you must name frames carefully, test with a known point, and rely on good calibration.

The seventh section covers the learned alternative. There is no learned model that replaces rigid transforms, because joining, undoing and blending them is exact arithmetic, and a network could only make it approximate. Instead, learned models produce transforms that this arithmetic then uses. A model might estimate an object's pose from a picture, but that answer still has to be joined into the chain to reach the arm's base. Where a part of the arm bends under its own weight, a small network might learn the leftover error and add a correction, but the transforms still do the main work.

The eighth section suggests where to read next. The next page is calibration, which measures the transform from the flange to the camera. The previous page is the pinhole camera model. Other related pages cover iterative closest point, numerical inverse kinematics, trajectory generation, and Book 3's deep dive into frames and conventions.

The final section is about using it in Python. It shows the two libraries you are most likely to use, because they answer two different questions. SciPy answers what this rotation is in another form, while tf2 answers where this frame is right now.

SciPy's Rotation class converts between matrices, quaternions, and angles without you writing a single sine. You can use it to build a four-by-four matrix, use NumPy to multiply them to join or undo transforms, and use SciPy's Slerp to blend along the shortest turn.

On a running robot you do not build those matrices yourself. Instead, tf2 collects where every part of the robot is into one tree. You ask the tf2 buffer for the transform between two frames at a specific time, and it joins every link in the chain for you, including the joints that moved since the last picture.

The libraries do the hard math, but you still write the naming. Nothing in either library records the direction of your transform, so it lives only in your variable names. Writing them with the matching frame names touching is the cheapest way to check it. You also have to handle tf2 exceptions, because the tree might be incomplete at start-up or asked for a time too far in the past.

Finally, you have to decide or measure the quaternion order and the frame names. SciPy takes w last, while ROS messages and Eigen put w first. The frame names must match what the robot publishes exactly, and the numbers come from hand-eye calibration rather than a drawing. The one test worth writing is to transform a point you have measured with a ruler, and check the answer in millimetres.
