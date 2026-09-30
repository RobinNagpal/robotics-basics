Rigid transforms. This page explains rigid transforms as a technique you can use in any program, and it answers five questions. How do you move a point from one frame into another? How do you store a turn and a shift together? How do you join several frames in a chain, and undo one? What is a quaternion, in plain words? And how do you blend smoothly from one orientation to another?

It is for a reader who has met frames and transforms in Book 1. The page on position, frames and transforms builds them by hand on a flat arm, and the page on vectors and matrices introduces the four by four matrix. This page does not rebuild those ideas, but instead writes them as one general method in 3D, adds quaternions and blending, and shows where each piece is used on a real arm with a camera.

The first section gives the idea in one sentence. A rigid transform is one turn followed by one shift, and it moves every point of a frame together without stretching or bending anything.

A frame is a starting point with three axes, fixed to one physical thing such as the table, the arm's base, the camera or the gripper, so a position always belongs to one frame. The word rigid means that distances and angles do not change, which is why a box that is six centimetres wide in the camera's frame is still six centimetres wide in the base's frame.

So think of an everyday example. Carry a tray with three cups across a room, and each cup stays at the same place on the tray while only the tray moves. To say where a cup is in the room, you need the cup's place on the tray and the tray's place in the room. That tray's place in the room is the rigid transform, because the cup's place on the tray never changes.

On an arm, the camera plays the part of the tray. The camera reports each object in its own frame, but the arm needs it in the base frame, so a rigid transform does the move.

The next part of the page explains how it works. The previous section described a transform as one turn and one shift, so this section builds it as arithmetic. It takes the pieces in the order you use them: the turn, then applying a turn and a shift, then storing both in one matrix, undoing it, and joining several, while quaternions and blending come last.

The examples use a scene where a camera hangs 0.40 metres above the middle of a table, looking straight down. The world frame sits at the middle of the table, with the z-axis pointing up, while the arm's base frame sits 0.35 metres to the left and 0.10 metres back from the middle, turned 30 degrees about z. The spot on top of a red box is at 0.06442, minus 0.04110, 0.340 metres in the camera's frame, as the pinhole camera model page worked out, and all the numbers were checked in Python.

Starting with the turn, a rotation matrix is a three by three grid of numbers that turns a point about the frame's starting point. Its three columns are where the frame's x, y and z axes end up after the turn. Book 1 explains why on the page about vectors and matrices.

The camera above the table has a specific rotation relative to the world. Reading it by columns, the camera's x-axis points along the world's x-axis. The camera's y-axis, which points down the picture, points along the world's negative y-axis. Finally, the camera's z-axis, which points out of the lens, points along the world's negative z-axis, which is straight down at the table.

A rotation matrix is a special grid, because each column has a length of one and each column is at right angles to the other two. This matters in practice, because if you round a rotation's numbers it stops being a rotation. For example, rounding a 30 degree turn from 0.866 to 0.87 makes every turned point 1.0034 times too far out, which is 0.34 millimetres at 10 centimetres. So keep full precision, or store the rotation as a quaternion, which is described later.

Next is applying a transform, which means a turn, then a shift. A transform from frame A to frame B holds B's rotation and B's position, both measured in A. It is written T underscore A underscore B, and you read it as B, seen from A. Applying it to a point measured in B gives the same point measured in A. The formula is that the point in A equals the rotation matrix multiplied by the point in B, plus the shift vector. The turn comes first, then the shift. Book 1 shows why the other order gives a different answer.

For example, take the transform of the camera seen from the world. Its rotation is the matrix just described, and its shift is zero, zero, 0.40, because the camera is 0.40 metres above the table's middle. First, the turn multiplies the rotation matrix by the camera point, which flips the signs of the y and z coordinates. Then, the shift adds 0.40 to the z coordinate. The result is that the spot is 0.06442, 0.04110, 0.060 metres in the world frame. So the spot is 0.060 metres above the table, which is the height of the box, and nothing in the arithmetic was told how tall the box is. Book 2 reaches the same answer by walking along the camera's axes on the page about where the camera is.

Programs keep the turn and the shift together in one four by four matrix. The rotation fills the top-left three by three block, the shift fills the last column, and the bottom row is always zero, zero, zero, one. To apply it, write the point with a one on the end, and multiply. The one picks up the shift column, so the turn and the shift happen in one multiplication. This form is called homogeneous coordinates, and its real value is that joining two transforms becomes one matrix multiplication, as the next parts show.

A direction, such as a surface normal or a velocity, is written with a zero on the end instead of a one. The zero skips the shift column, so a direction is turned but not moved. Mixing these up is a common bug: a surface normal that gets shifted by 0.40 metres points somewhere meaningless.

The next part covers undoing a transform. The arm wants the spot in its base frame, not the world frame. We know the base seen from the world, which is turned 30 degrees about z and shifted to minus 0.35, 0.10, zero, so we need the opposite, the world seen from the base.

Undoing a rigid transform is cheap, because a rotation's inverse is just its transpose, which is the grid flipped across its diagonal. We write R transpose for that. The inverse rotation is R transpose, and the inverse shift is the negative of R transpose multiplied by the original shift.

Applying this to the spot in the world frame gives its position in the base frame. In other words, you take away the base's position, and then turn back by 30 degrees.

Never undo a transform by inverting the four by four matrix with a general-purpose inverse routine. It works, but it is slower, and small rounding errors creep into the rotation block, while the transpose rule is exact.

Moving on to joining frames in a chain. Two transforms that meet at a shared frame join into one, by multiplying their matrices. For example, the camera seen from the base is the world seen from the base multiplied by the camera seen from the world. The names show whether the order is right, because written this way the inner names match, with "world" next to "world", and the outer names give the answer, which are "base" and "camera". So the result takes a point in the camera's frame straight to the base frame.

The page has a diagram showing one spot on the box, seen from above, with its numbers in all three frames. All three triples describe the same spot. The camera's triple says 0.340 metres in front of me, the world's says 0.060 metres above the table, and the base's says 0.329 metres ahead of me and 0.258 metres to my right. The diagram also shows a grey cross, which is what happens if the two transforms are joined in the wrong order. The arm then reads a target that is 0.589 metres away from the real spot, and no error message warns about it.

A camera on the arm's wrist makes a longer chain, and one link of it changes every time the arm moves. The point in the base frame is the flange seen from the base, multiplied by the camera seen from the flange, multiplied by the point in the camera frame. The flange seen from the base comes from the joint angles, by forward kinematics, and it says where the arm's last mechanical face, the flange, is. The camera seen from the flange is fixed instead, and comes from hand-eye calibration.

A second diagram shows this chain with the flange 0.45 metres above the base, pointing straight down, and the camera 0.06 metres along the flange's x-axis. The same camera reading as before now lands at a different place in the base frame. The reading did not change, because only the chain behind it did. This is how every wrist camera turns what it sees into a place the arm can reach, and it must use the flange pose from the moment the picture was taken, not the moment the calculation runs.

The next part explains quaternions, in plain words. A rotation matrix uses nine numbers to describe something that has only three degrees of freedom, which is more numbers than the job needs. So robot software usually stores a rotation as four numbers instead, called a quaternion.

The idea behind it is simple, because every rotation, however complicated, is one turn by some angle about some single axis, and this fact is known as Euler's rotation theorem. So a quaternion stores that axis and that angle, in a particular way. The x, y, and z values are the axis, as a direction of length one, multiplied by the sine of half the angle. The w value is the cosine of half the angle.

A diagram shows the two rotations in this page's scene, with each panel looking straight down the turning axis, making the turn a plain turn on the page. The arm's base is turned 30 degrees about z, so its axis is zero, zero, one, and half the angle is 15 degrees. This makes the quaternion zero, zero, the sine of 15 degrees, and the cosine of 15 degrees. The camera is turned 180 degrees about x, so its axis is one, zero, zero, and half the angle is 90 degrees, which makes the quaternion one, zero, zero, zero. That half turn is what makes the camera look down, because its y and z axes both flip.

So four facts are enough to use quaternions safely.

First, the four numbers always have a length of one. That is, x squared plus y squared plus z squared plus w squared equals one. If rounding or averaging breaks this, divide all four by their length. This one step is much simpler than repairing a rotation matrix.

Second, q and negative q are the same rotation. For example, flipping the signs of all four numbers in the 30 degree turn about z still gives a 30 degree turn about z. So never compare quaternions number by number, and compare the rotations they make instead.

Third, the order of the four numbers differs between libraries. ROS and SciPy put w last, as x, y, z, w, while MuJoCo and Eigen's constructor put w first. So reading one as the other gives a wrong rotation with no error, and Book 3 lists who uses which on the page about quaternion ordering.

Finally, you do not have to multiply them by hand. Every library converts a quaternion to a rotation matrix and back. The conversion from x, y, z, w to a matrix involves squares and products of the four numbers, and putting in the numbers for the 30 degree turn gives the correct rotation matrix with 0.866 and 0.5 in the usual places.

The other common way to write a rotation is three angles, such as roll, pitch and yaw. They are easy to read, which is why URDF files and user interfaces use them. But they need a stated axis order and convention, and at some poses two of the three axes line up so that one direction of turning is lost, and this is called gimbal lock. So use three angles for people to read and type, and convert to a quaternion or a matrix for the arithmetic. Book 3 covers the convention problem on the page about Euler angles.

The next part is about blending two orientations. A motion from one gripper orientation to another needs the orientations in between. The obvious way is to blend the numbers directly, so that at the halfway point you take half of each. However, for rotations this goes badly wrong.

A diagram shows a blend from a turn of zero degrees to a turn of 90 degrees about z, following the tip of the turned x-axis. It shows two paths. The first path blends along the circle, so at a quarter, half and three quarters of the way the points are at 22.5 degrees, 45 degrees and 67.5 degrees. These are equal steps, and the axis keeps its length of one. This is called spherical linear interpolation, or slerp for short. The second path instead blends the matrix numbers in a straight line, so the points are at 18.4 degrees, 45 degrees and 71.6 degrees. This means the motion speeds up and slows down, and the axis shrinks to 0.707 of its length at halfway. A shrunken axis is not a rotation at all.

For quaternions, slerp between two quaternions at a given fraction involves finding the angle between them using the dot product of their four numbers. Then you blend them using sines of the angles. If the dot product is negative, you flip the sign of the second quaternion first. Because q and negative q are the same rotation, this picks the shorter way round. Without it the gripper can swing the long way, nearly a full turn. When the two are almost equal, the sine of the angle is almost zero, so you blend the numbers directly and then set the length back to one.

The section ends with pseudocode that gives the whole technique in plain steps, working in any language. A transform is stored as a three by three rotation matrix and a three-vector shift. To apply it to a point, you multiply the rotation by the point and add the shift. To apply it to a direction, you only multiply by the rotation. To join two transforms where the inner frame names match, you multiply their rotations together, and for the shift, you multiply the first rotation by the second shift and add the first shift. To invert a transform, you transpose the rotation matrix, and the new shift is the negative of that transposed matrix multiplied by the original shift. To convert a quaternion to a rotation, you first divide the four numbers by their length to ensure the length is one, then use the matrix conversion formula. Finally, to slerp between two quaternions, you take their dot product. If it is negative, you flip the second quaternion and the dot product to take the shorter way round. If the dot product is very close to one, you blend the numbers directly and divide by the new length. Otherwise, you calculate the angle with the arccosine of the dot product, and blend them using the sine formula.

The third section explains where this is used on a robot arm. Rigid transforms appear everywhere a number crosses from one part of the robot to another.

First, from camera to base, for every detection. Every back-projected point is moved into the base frame before the arm can use it. With a fixed camera this is one fixed transform. With a wrist camera it is the chain through the flange.

Second, in forward kinematics. The gripper's pose is the product of one transform per joint, from the base outwards.

Third, for the tool centre point. The arm's controller reports the flange, but the point that touches the object is the tool tip, typically 100 to 200 millimetres further on. One fixed transform turns one into the other.

Fourth, for grasp poses stored relative to the object. A good grasp on a mug is stored once, in the mug's own frame. When the mug is found at a new pose, one join gives the grasp in the base frame.

Fifth, for merging views. Point clouds from three camera positions are each moved into the world frame and added together. The result of iterative closest point is itself a rigid transform that lines two clouds up.

Sixth, for force readings. A force sensor reports in its own frame. Before the controller compares a force with "straight down", it turns the force into the base frame. A force is a direction, so it is turned but not shifted.

Seventh, for smooth orientation changes. A planner that moves the gripper from one orientation to another blends them with slerp.

Finally, in ROS's TF system. ROS keeps a tree of every frame on the robot and joins transforms on request.

The fourth section covers where it works, and where it goes wrong. The arithmetic of rigid transforms is exact, so the mistakes come from feeding it the wrong things, and each mistake has a sign you can look for. The page provides a table of these common errors.

For example, if two transforms are joined in the wrong order, the answer is off by tens of centimetres, often in a plausible-looking place. The fix is to name every variable with its parent and child frames, and check that the inner names match.

If a transform is used in the wrong direction, the answer is mirrored or rotated, and moving the camera moves the result the wrong way.

If a quaternion order of w, x, y, z is read as x, y, z, w, objects appear turned by large, odd angles, and the identity looks like a half turn.

If a rotation drifts from being a rotation, lengths grow or shrink slowly over many joins, so you must renormalise the quaternion or re-orthogonalise the matrix.

If a direction is shifted as if it were a point, surface normals and forces point the wrong way.

If a wrist camera's picture is paired with the wrong arm pose, points smear or jump while the arm moves, and are fine when it is still. The fix is to look up the flange pose at the picture's timestamp.

If degrees are read as radians, you see turns of 57 times the intended size.

And if the transform itself is wrong, everything is consistently off by a few millimetres or a degree, which is a calibration problem that arithmetic cannot fix.

Rigid transforms work only for rigid things, because a cable, a soft gripper finger or a bending arm under a heavy load does not move rigidly, and a rigid transform will then describe it only approximately.

The fifth section lists libraries that provide rigid transforms. Every robotics stack provides them, and you should use one rather than writing your own for anything beyond a small script. The page has a table of well-known libraries.

For C++, Eigen is the base of MoveIt, PCL and most C++ robotics code. Its quaternion constructor takes w first.

For Python, SciPy provides a Rotation class that converts between matrices, quaternions, axis-angle and Euler angles, and it puts w last by default.

ROS 2 provides tf2 for C++ and Python, which keeps the whole frame tree and joins transforms for you at a given time.

Pinocchio provides rigid transforms plus the arm's kinematics in one library.

The Kinematics and Dynamics Library, or KDL, is used by many ROS kinematics plugins.

Open3D and the Point Cloud Library both have functions to apply a four by four matrix to a whole point cloud.

Finally, NumPy provides plain four by four arrays and matrix multiplication, which is enough for small programs.

The sixth section explains why we use transforms, and what they cost. A rigid transform is one turn and one shift, kept together. So it lets every part of the robot describe positions in its own simplest frame, and lets any program ask for any position in any other frame.

The obvious alternative is to write one formula for each question, such as calculating the box from the base as a sum of sines and cosines. Book 1 shows why this breaks: every new joint, every move to 3D, and every new question means a new formula. With transforms you describe each part once, against its neighbour, and let joining do the rest. Adding a wrist camera adds one transform to the chain, not a new formula.

A second alternative is to store orientations as three angles everywhere. Three angles are easy to read, but they depend on a convention that differs between libraries, they lose a direction at gimbal lock, and they cannot be blended correctly. Quaternions and matrices have none of these problems, so use angles only where people read and type them.

The cost is this. Each transform has a direction, and each quaternion library has an order, and neither of those is visible in the numbers themselves. A wrong one gives a plausible answer rather than an error. So you must name frames carefully and test with a known point. And the transforms are only as right as the measurements behind them: the joint readings, and the calibration.

The seventh section discusses the learned alternative. There is no learned model that replaces rigid transforms, because joining, undoing and blending them is exact arithmetic, and a network could only make it approximate. Instead, learned models produce transforms that this arithmetic then uses. For example, a trained model might estimate an object's rigid transform from a picture, and that answer still has to be joined into the chain on this page to reach the arm's base. Where a part of the arm is not quite rigid, such as a link that bends a little under its own weight, a small network can learn the leftover error and add a correction to the tool's position. So the transforms still do the main work.

The final section suggests where to read next. The next page is about calibration, which measures the transform from the flange to the camera that this page took as given. The previous page on the pinhole camera model makes the camera-frame points this page moves. The page on iterative closest point finds the rigid transform that lines two point clouds up. The page on numerical inverse kinematics runs the transform chain backwards, from a wanted pose to joint angles. The page on trajectory generation uses slerp to move the gripper smoothly between orientations. Finally, Book 3 has a page on frames, conventions, and the bug class that comes from mixing them, which goes much deeper into the conventions and how to check them.
