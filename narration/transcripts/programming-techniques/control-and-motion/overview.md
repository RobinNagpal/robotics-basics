Control and motion. This chapter is about turning a planned path into smooth, safe motor commands. It covers five techniques: proportional-integral-derivative control, which is usually called PID control, trajectory generation, arm dynamics, safety monitoring, and impedance and force control. All five are written sets of rules that a program follows many times a second. That means none of them is trained from data.

This overview page answers four questions. What job do these techniques do for an arm, and what does each of the five do in one line? How do they work together on one real move, and how does this chapter connect to the rest of the book and to learned movement models?

The page is written for a reader who knows what a joint, a joint angle, and a motor are. It also helps to understand planning and search, because this chapter starts where the planner stops, though you do not need any control theory beforehand. Every number mentioned comes from a real simulation of a joint, a move, and a contact, rather than being drawn by hand.

The first section explains what control and motion is for. The job is to turn a planned path into smooth, safe motor commands. In everyday terms, think of carrying a full mug of coffee from the kitchen to a desk. Since you already know the route, what is left is how you walk it. You do not start at full speed, because the coffee would slop, and you do not stop dead at the desk for the same reason. While you walk, you keep correcting your hand, because the mug is never quite where you meant it to be. Then, when you put the mug down, you lower it until you feel the desk, and only then do you stop pushing.

Because an arm carrying a mug faces the same problem, it has the same three jobs every time it moves. First, it must decide how fast to go along the route at each moment, without going faster, or speeding up faster, than the motors allow. Second, it must make each motor actually follow that plan, even though gravity, friction, and the load all push the joint off course. Finally, it must behave sensibly when it touches something. A mug put down on a table, a peg pushed into a hole, and a person bumping the arm all need the arm to give way a little instead of pushing harder.

A planner does none of those three jobs, because all it hands over is a list of joint angles to pass through. That means it says where to pass but not when, and it knows nothing at all about motors or contact.

The next part of the page divides this work into three layers, where each layer answers one question and hands its answer to the layer below it.

The trajectory layer answers where each joint should be at each instant. A trajectory is simply a path with times attached to it. Since the same path can be driven slowly or quickly, and with gentle or sudden changes of speed, this is the layer that chooses which of those it will be.

The controller layer answers what torque each motor should produce right now, so that the joint is where the trajectory says. A torque is a turning force measured in newton metres. The controller reads the joint's sensor, compares the reading with the target, and chooses a torque. It does this again and again, often 1,000 times a second. This repeated correction is called a feedback loop, because the measurement is fed back into the next decision.

The controller does that job better when it knows the arm's own body, and the arm's dynamics are what describe that body. That means they say how much torque each joint needs to hold the arm up against gravity and to speed it up. Because a controller can add that torque before any error appears, it follows fast moves far more closely than one that waits for an error to show up first.

The contact layer answers what should happen when the arm touches something. A plain position controller has only one answer, which is to push harder until the joint is where it was told to be. Instead of that, the contact layer lets you choose the behaviour, such as acting like a soft spring, or stopping when the force passes 1 newton.

Beside all three layers runs a safety monitor. This does not command the arm itself. Instead, it watches the commands and the measurements, and it stops the arm when a speed, a force, a position, or a distance to a person goes outside its limit, or when a loop stops sending commands.

These layers appear in ROS 2 as the ros2_control framework and its controllers. While other pages show how to use them, this chapter explains the techniques inside them.

The page then introduces the five techniques, split into two groups based on how often you will meet them.

The most used group holds four techniques that run on nearly every arm, every time it moves. Even an arm that only moves between fixed poses uses all four, although the dynamics and the safety checks are often hidden inside the arm maker's controller. 

First is PID control, which makes one joint follow its target. It adds up three pushes: one in proportion to the error now, one that grows while an error lasts, and one that brakes when the error is changing fast. It is the loop that runs inside nearly every joint of nearly every arm.

Second is trajectory generation, which decides where each joint should be at each instant. It turns a list of waypoints into smooth curves, and gives them a speed profile that keeps within the motors' limits of speed, acceleration, and jerk.

Third is arm dynamics. This works out the torque each joint needs, based on inertia times acceleration, plus the pull of gravity, plus a part that grows with speed. It holds the arm still with no error, lets a controller follow fast moves closely, and lets a simulator predict how the arm will move.

Fourth is safety monitoring, which watches the arm's software limits for joint positions, speeds, torques, forces, and the distance to people. It includes a watchdog, which is a timer that every new command must reset, stopping the arm when a loop stops sending commands. It also includes speed and separation monitoring, which slows the arm as a person comes closer, and stops it if they come too close.

The remaining technique is in the also used group. It is used often, but only in tasks where the arm touches things on purpose, such as pressing, inserting, or being guided by hand. This is impedance and force control, which decides how the arm behaves in contact. It makes the arm act like a spring with a stiffness you chose, stops a move when a force sensor fires, and keeps contact forces inside a limit.

The next section sets these five techniques side by side in a table, comparing what goes in, what comes out, how often they run, and the sign of a bad setup.

For PID control, the target angle and measured angle go in, and a torque or motor current comes out. It runs 1,000 times a second or more. A bad setup is obvious if the joint overshoots and rings, or stops a little short of the target.

For trajectory generation, waypoints and joint limits go in, and a target angle for every tick of the controller comes out. It runs once per move, then is read out at the controller's rate. If it is set up badly, the arm jerks at the start and end, or the tool wobbles after it stops.

For arm dynamics, the joint angles, speeds, wanted accelerations, and the arm's masses go in. It outputs a torque for each joint, or the accelerations that a torque will cause. It runs 1,000 times a second inside the controller, and also inside every simulator. A bad setup means the arm sags when held still, lags on fast moves, or sets off false collision alarms after a grasp.

For safety monitoring, the inputs are the commands, the measured angles, speeds, forces, and the distance to people. The output is a decision to carry on, slow down, or stop. It runs every controller tick, 500 to 1,000 times a second. If set up badly, the arm stops for no reason, or does not stop when a limit is broken.

Finally, for impedance and force control, the target pose and measured force or position go in. It outputs a force or torque, or a changed target position. It runs 500 to 1,000 times a second. A bad setup causes the arm to push too hard on contact, bounce off, or buzz against a hard surface.

The page then explains how these layers work together on one real move of two joints. A diagram shows a 2.4 second move passing through the three layers. It shows the planner's output on the left, the speed of each joint over time in the middle, and the error of each joint on the right, which is the target angle minus the measured angle.

Three things in this run are worth noticing.

First, the planner's waypoints have no times of their own, so the trajectory layer is what chose them. It gave each stretch of the path a share of the 2.4 seconds in proportion to its length. The waypoints are passed at 0, 0.91, 1.70, and 2.40 seconds, and both joints start and end at zero speed.

Second, the controller never follows the trajectory exactly, because it lags behind while the joint is moving. The largest error is 3.4 degrees on joint 1, and 4.3 degrees on joint 2. This lag is called the following error, and it is perfectly normal. Because of this, a controller with its tolerances set to zero will always fail.

Third, the error is still not zero when the trajectory ends. At 2.4 seconds, joint 1 is still 1.85 degrees off, and half a second later it is still 0.96 degrees off. This happens because the controller keeps working after the trajectory has stopped changing, closing the remaining gap slowly. This is called settling time, and it means a move that is done by the clock is not always done at the joint.

This specific move has no contact in it, so the contact layer never runs. But if the gripper were lowering a mug onto a table, the last few millimetres would be handed to that layer.

The next section explains that these layers do not run at the same speed. A planner runs once per move and may take a tenth of a second or more, while a controller runs every millisecond. Some sources sit in between, like a camera-based loop sending targets 30 times a second, or a learned policy sending them 10 to 15 times a second.

Something has to fill the gap between a slow stream of targets and a fast controller. A diagram shows why this matters by comparing two ways of sending 10 targets a second to a joint.

In the first way, shown as a red run, each target is sent straight to the controller and held there for 100 milliseconds. Because every new target is a small step, the controller answers each step with a sudden rise in torque. The largest change from one millisecond to the next is 2.48 newton metres, causing the arm to move in small jerks.

In the second way, shown as a green run, the target is moved smoothly, 1,000 times a second, from the previous value to the newest one. Here, the largest change in one millisecond is only 0.03 newton metres, giving smooth torque. However, this smooth run has a cost: it is always one target behind, meaning it is a tenth of a second late. This trade-off is why learned policies still need the trajectory and controller layers underneath them.

The general rule is that every loop should hand the loop below it a signal that changes smoothly at the lower loop's own rate.

The next part explains how control and motion connects to the rest of the book. Because it turns decisions into motor commands, it sits at the end of the chain.

Planning and search hands over the path. Trajectory optimisation can provide a path with times, leaving the trajectory layer here to just check and smooth it. Numerical inverse kinematics turns a target pose into joint angles, which is how a Cartesian controller works inside.

Fitting and estimation cleans up the signals the controllers read. For example, a Kalman filter can smooth a noisy joint speed or force reading before a controller uses it.

Geometry and cameras provide the frames that a Cartesian impedance controller works in, because stiffness along a tool only means something once the tool frame is known.

Decisions and task logic decide when to switch layers, such as moving fast in free space, then switching to a guarded move, and finally switching to impedance control to press.

Learned models also do parts of this job, but they sit on top of the programmed loops rather than replacing them. A movement model decides where the arm should go next, replacing the planner, but its output is still a stream of joint targets that a PID loop must follow. A learned arm model predicts the torque a joint needs, usually correcting the physics model so the result can be added to a PID loop. A force and slip model reads touch signals that a force controller could then act on.

The final section suggests where to read next. You should start with PID control, because it is the loop inside every joint and the other pages build on it. Then read trajectory generation, which makes the targets that PID follows. Next is arm dynamics, which adds the torque a PID loop would otherwise wait for an error to find. After that, read safety monitoring, which watches the loops and stops the arm when a limit is broken. Finally, read impedance and force control, which changes what happens at contact. The chapter also links to other parts of the book covering ROS 2 controllers, gripper compliance, and what learned policies take over versus what they leave to these loops.
