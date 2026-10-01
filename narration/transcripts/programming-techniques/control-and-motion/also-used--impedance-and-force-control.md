Impedance and force control. This page explains impedance and force control, which are the techniques that decide how an arm behaves when it touches something. It answers four questions. Why does an ordinary position controller push so hard in contact, and how do you make an arm behave like a spring instead? How do you find a surface safely by touch, and why does a compliant arm sometimes bounce or buzz against a hard surface?

It is written for a reader who has read the overview of this chapter and the page on PID control. You also need to know what a force in newtons is, and that a spring pushes back harder the further it is squeezed. Every number on this page comes from a real run of the diagram script, which simulates a tool pressing on a surface.

Contact is where most hard arm tasks are decided. Examples are inserting a peg, pressing a connector home, putting a part down on a table whose height is not quite known, and wiping a surface. A good plan and a good trajectory do not help with any of those, because what helps is choosing what the arm does when it meets resistance.

The first section covers what this page answers. The page on PID control builds a loop that drives a joint to a target angle and holds it there. That loop is excellent in free space, but in contact it has a serious fault.

Suppose the target is one millimetre inside a table. The table does not move, so the controller sees an error it cannot remove. Its integral term therefore keeps growing, so it pushes harder and harder, until the motor reaches its limit or something breaks. This is not a bug, because it is exactly what a position controller is for. The Book 3 page on controlling the move calls it the most important single idea in the whole area.

So the fix is to stop commanding only a position, and to command how the arm should respond to force instead. This page shows three ways of doing that. First is impedance control, which makes the arm behave like a spring and a damper with a stiffness you choose. Second is admittance control, which gives the same behaviour on an arm that only accepts position commands, by reading a force sensor. Finally, guarded moves, which move until a force is felt and then stop.

It also shows the two ways these go wrong, which are bouncing off a hard surface and buzzing against it.

The next part gives the idea in one sentence. Since the fix is to command a response to force, here is the main technique. Impedance control sets the force the arm applies to be a stiffness times the distance from where it was told to be, minus a damping times its speed, so that unexpected contact produces a small, chosen force instead of an ever-growing one.

Here is an everyday example of the same idea, putting a plate into a dish rack without looking. You do not hold your arm rigid and drive the plate to where you think the slot is. If you did, and you were a few millimetres out, you would push the plate hard into a prong. Instead you hold your wrist loosely. Then when the plate touches a prong, it pushes your hand a little to one side, and the plate slides into the slot. In other words, your arm is acting as a soft spring around the place you aimed for. So a stiff arm needs perfect aim, while a soft one only needs to be close.

The next section explains how it works, step by step, starting with the tool and the wall used in the examples. Because the effects are easiest to see on one example, the simulations on this page all use a single straight line of motion, with a tool moving towards a wall. Everything below happens along that one line.

The tool, together with the part of the arm that moves with it, has a mass of 2 kilograms. The wall is stiff: it pushes back with 50 newtons for every millimetre the tool presses into it. That is 50,000 newtons per metre. Real metal is stiffer still, but the arm, the sensor and the gripper all bend a little, and together they behave like a spring about this stiff. The tool starts 10 millimetres in front of the wall. Its target moves towards the wall at 20 millimetres per second and stops 5 millimetres inside it. So the target asks for something impossible, as it would if the wall were 5 millimetres closer than the camera thought.

Next is why a position controller pushes too hard. The first thing to see is what goes wrong without any of these techniques. The page shows a diagram of a stiff PID position loop, running 1,000 times a second, like the one inside an ordinary joint drive. Here the motor can push with at most 150 newtons.

The diagram shows the tool touching the wall at half a second. Then the force rises steeply, passes 140 newtons at 0.66 seconds, and stays at the motor's limit of 150 newtons, ringing a little. If the motor had no limit at all, the integral term would keep pushing until the tool was 5 millimetres into the wall, which for this wall means 250 newtons.

The diagram also shows impedance control on the same task, with two stiffness settings, on a scale ten times smaller. With a stiffness of 2,000 newtons per metre the force settles at 9.6 newtons, while with 500 newtons per metre it settles at 2.5 newtons. The target is just as impossible as before, so the difference is that the force no longer depends on how hard the motor can push. Instead it depends on a number you chose.

There is still a first spike in each impedance run, up to 6.5 newtons with the softer setting. That is the impact, because the tool arrives at 20 millimetres per second and has to stop. But a slower approach makes it smaller, as the guarded move section shows.

The next part explains the impedance law, which acts as a spring and a damper. The law behind that result is short, because the impedance controller computes the force to apply from only two terms. The force equals a stiffness K times the difference between the target position and the actual position, minus a damping D times the speed.

K is the stiffness, in newtons per metre. It says how hard the arm pushes back for each metre it is away from its target, so a high K is a stiff arm and a low K is a soft one.

D is the damping, in newton seconds per metre. It is a force against the speed, in the way that moving through thick oil resists you, and it is what stops the spring from bouncing.

This looks like a PD controller from the PID page, and in form it is. But the difference is in purpose and in size. A position PD loop uses the largest gains that stay stable, so that the arm reaches its target whatever resists it. An impedance controller, in contrast, chooses K and D to be a particular spring, often a soft one. It also has no integral term, because the whole point is that it does not insist on reaching the target.

Here is one tick of that law worked by hand, with K equal to 500 newtons per metre and D equal to 44.3 newton seconds per metre. The tool is 2 millimetres short of its target and moving towards it at 10 millimetres per second. First, the spring term is 500 times 0.002, which is 1.0 newtons towards the target. Second, the damping term is 44.3 times 0.010, which is 0.443 newtons against the motion. Finally, the force to apply is 1.0 minus 0.443, which is 0.557 newtons.

Where does the final force in the simulation come from? At rest the arm's spring and the wall form two springs in a line, and the arm is set 5 millimetres too far. So the force is the stiffness K times the wall stiffness, divided by the sum of K and the wall stiffness, all multiplied by 5 millimetres.

For K equal to 500 newtons per metre, that is 500 times 50,000, divided by 50,500, times 0.005, which is 2.48 newtons, and the tool sits 0.05 millimetres into the wall. For K equal to 2,000 newtons per metre it is 9.62 newtons. When the wall is much stiffer than the arm's spring, the answer is close to K times the error, which is 500 times 0.005, or 2.5 newtons. So you can choose the largest force a given position error will cause, just by choosing K.

On a real arm the law is usually written for the tool in all six directions, three along the axes and three around them. Each direction then gets its own stiffness and damping, so the arm can be stiff sideways and soft along the tool, for example. The force at the tool is turned into joint torques using the Jacobian, which is the table of numbers that relates small joint movements to small tool movements. The page on numerical inverse kinematics explains it. The controller also adds the torque needed to hold the arm up against gravity, taken from a model of the arm. So if that model is wrong, the arm drifts as soon as it is made soft.

The next part is about choosing the damping. Choosing K sets the force, but D still has to be chosen, because a spring with too little damping bounces. On an arm that means the tool hits the surface, bounces off, hits it again, and so on.

So a common rule sets the damping from the stiffness and the mass. D equals two times zeta times the square root of K times the mass. Here the Greek letter zeta is the damping ratio. At a zeta of 1, the spring returns to rest as fast as it can without swinging past, which is called critical damping, while below 1 it swings and above 1 it creeps.

The page shows a diagram of the tool hitting the stiff wall at 50 millimetres per second under impedance control with K equal to 1,000 newtons per metre, using three different damping values. It shows that too little damping bounces the tool off the wall many times.

With a damping of 9 newton seconds per metre, which is a zeta of 0.1, the tool leaves the wall 14 times in the first second, and the force peaks at 31 newtons each time it hits. With a damping of 63, or a zeta of 0.7, it leaves the wall twice. With a damping of 134, or a zeta of 1.5, it never leaves at all. But all three end at the same steady force of 4.9 newtons, because the damping only acts while the tool is moving.

The middle case is worth a closer look. A damping ratio of 0.7 is a common choice for free motion, and it is well damped for the arm's own spring of 1,000 newtons per metre. But once the tool touches the wall, it is sitting on the wall's spring, which is 50 times stiffer, and for that much stiffer spring the same damping is far too little. So a damping that is right in free space is too small in contact with something hard. This means that on a real arm the damping is set with the stiffest surface in mind, or else raised when contact is detected.

The next section compares impedance and admittance, which are two ways to build this behaviour. The law and its two numbers are the same whatever the hardware, but there are two ways to build the behaviour, and they need different hardware. The Book 3 page on holding on compares them, and in short they work like this.

Impedance control measures the arm's position and commands a force. It is the law above, sent as joint torques. So it needs an arm whose joints accept torque commands, which in practice means an arm with torque sensing in every joint or very good motor current control. But it behaves well against stiff surfaces, because the torque loop is fast.

Admittance control goes the other way, measuring a force and commanding a position. A force-torque sensor at the wrist reads the contact force. Then the controller works out how a virtual mass, spring and damper would move under that force, and it sends the result as a position target to an ordinary position-controlled arm. This means it works on nearly any industrial arm with a sensor bolted on, which is why the open-source ROS 2 stack ships an admittance controller and not an impedance one.

But admittance has a known weakness, which the next diagram reproduces. The loop through the force sensor and the arm's position controller has delay in it. Here the sensor is read 500 times a second with a delay of 8 milliseconds, while the arm's own position loop takes a few tens of milliseconds to follow a new target. The task is to press on a surface with 10 newtons.

The diagram shows that admittance control settles on foam, bounces on metal, and settles on metal only with much more damping. On foam, which gives 2 newtons per millimetre, a damping of 200 newton seconds per metre works well, because the force settles at 10 newtons within about 0.2 seconds of touching. But on metal, which is 100 times stiffer, the same setting hits the surface with 268 newtons and bounces off. A damping of 1,000 newton seconds per metre still bounces on and off the surface about five times a second, with peaks of 58 newtons, so only 5,000 newton seconds per metre settles, at 10 newtons.

The reason for all of that is the delay. Against a stiff surface a tiny movement makes a large change in force. So by the time the controller reads that force and the arm responds, the tool has already moved further, which makes each correction too large and too late. More damping makes each correction smaller and slower, which is why it cures the problem. This agrees with Book 3, because the fix for an admittance controller that chatters against metal is more damping, not more force resolution.

But the cure has a price, and the same simulation shows it. With 5,000 newton seconds per metre of damping the arm approaches the surface at only 2 millimetres per second, because the push of 10 newtons divided by the damping gives that speed. On foam, the same setting has reached only 1.8 newtons after one second, 4.5 newtons after two, and 6.3 newtons after three. So a setting that is safe on a hard surface is slow on a soft one.

The next part explains guarded moves, which stop when you feel contact. Impedance and admittance both shape a whole response, but the simplest force technique of all is a guarded move. The arm moves slowly in one direction and stops as soon as a sensor reading passes a threshold, so it is how an arm finds a surface whose position it does not know exactly.

A diagram simulates one. The arm creeps towards a surface 20 millimetres away, and that surface gives 5 newtons per millimetre, like a plastic part. The force sensor is read 500 times a second, with some noise, and the last 5 readings are averaged. Then when the average passes 1 newton, the arm waits one tick and brakes at 0.5 metres per second squared.

The diagram shows that a slow guarded move stops almost at the surface, while a fast one presses in and hits 14.7 newtons. At 10 millimetres per second the sensor fires at 20.26 millimetres, the arm stops at 20.37 millimetres, and the largest force is 1.8 newtons. At 50 millimetres per second it fires at 20.40 millimetres, but the arm needs 2.5 millimetres to brake from that speed and stops at 22.95 millimetres. So the largest force is 14.7 newtons, eight times as much. This happens because the braking distance grows with the square of the speed, so going five times faster costs 25 times the braking distance.

So three rules follow from that, and Book 3's section on guarded moves states them in full. First, the measurement comes from the joint encoders, not from the force sensor. The sensor only says when. The position at that moment says where. Second, the threshold must be lower than the force that moves or damages the object. The sibling project that pushes drinking glasses, called plan, feel, look again, creeps at 10 millimetres per second and stops at 0.1 newtons, because the lightest glass starts to slide at about a quarter of a newton. Its fingers found one glass after 19.4 millimetres of creeping, a number no camera had predicted. Finally, always set a travel limit. If nothing is there, the sensor never fires, and without a limit the arm keeps going. In the simulation, with no surface at all, the arm stops at the 50 millimetre travel limit.

The next part covers force limits and direct force control. Impedance control makes the force predictable, but a large position error can still make a large force, so two more tools keep the force inside a safe range.

A force limit clips the force the controller will ever command, just as the PID page clips torque. With impedance control you can also limit the distance between the target and the actual position. So with K equal to 500 newtons per metre and at most 20 millimetres of difference allowed, the spring can never push harder than 500 times 0.020, which is 10 newtons, however wrong the target is.

Direct force control commands a force instead of a position along some directions, and the usual example is to press down with 20 newtons while following a path across the surface. Along the pressing direction a PI loop acts on the force error, while along the other directions an ordinary position or impedance loop follows the path. This mix is called hybrid force-position control, and it is what wiping, sanding and polishing need.

But one thing is not force control at all. A collaborative arm's safety function, which stops the arm when it detects an unexpected force, is a monitor with a threshold. It acts by stopping rather than by giving way, and it can fire in the middle of a planned insertion. Book 3's page on holding on makes this point, and it is easy to confuse the two.

The next part shows the steps as pseudocode. Once all three techniques are clear, each of them fits in a few lines. The page provides pseudocode for one tick of each, for one direction of motion. On a real arm each quantity has six parts, one per direction, and the impedance force is turned into joint torques with the Jacobian.

For impedance control, which needs an arm that accepts torque or force commands, every tick it measures the tool position and speed. It calculates the force as the stiffness times the position error, minus the damping times the speed. It clips the force to the force limit, and sends that force as joint torques, plus gravity compensation.

For admittance control, which needs a force sensor and a position-controlled arm, it starts by setting the command position to the current position and the command speed to zero. Every tick it measures the contact force pushing back on the tool. It calculates the push as the wanted force minus the measured force. It calculates acceleration by taking the push minus the damping times the command speed, all divided by a virtual mass. It updates the command speed and position using that acceleration and the tick length, and sends the new position to the arm's position controller.

For a guarded move, it sets the start position and commands a slow, steady speed in the search direction. Every tick it averages the last few force readings. If the force is greater than the threshold, it stops the arm and returns that contact was made, along with the position. If the distance from the start is greater than the travel limit, it stops the arm and returns that nothing was found.

The next section explains where this is used on a robot arm. Because contact is where the position of things stops being known exactly, these techniques turn up wherever an arm touches its work. The main places include inserting a part. A peg that must go into a hole with less clearance than the arm's accuracy is the classic case. The arm is made soft sideways and moderately stiff along the peg, so when the peg meets the edge of the hole, the side force pushes it towards the centre and it slides in.

Another use is putting something down. The height of the table under a part is never known exactly. So a guarded move lowers the part until the force rises, and then the arm stops and opens the gripper. With impedance control the part is placed gently even if the table is a few millimetres higher than expected.

They are also used for finding things by touch. A guarded move measures a height, finds the edge of a part, or confirms that a part is present.

Pressing a connector home is another example. The force during the last millimetre tells you whether it seated, because a sharp rise and then a drop is a click. A force limit then stops the arm pushing on if it jammed instead.

Wiping, sanding and polishing use hybrid force-position control to hold a set force on a surface the arm cannot model exactly. But for fast work the force loop often lives in a spring-loaded flange between the arm and the tool rather than in the arm, because a heavy arm cannot correct fast enough.

Hand guiding uses it too. A person pushes the arm to show it a pose, so the arm is made very soft, with gravity compensation so that it does not sag, and it follows the push.

Finally, gripping. A gripper's squeeze is a crude kind of force control, because the fingers close until the motor current reaches a limit. Book 3 explains why that limit is not the same as a force.

The next section covers where it is useful, and where it is not. These techniques are useful whenever the arm touches something whose position is not known precisely. But they do not help in free space, and they cannot make up for missing hardware. The page provides a table of common problems, the signs you would see, and how to fix them.

If you use admittance control against a stiff surface, the tool bounces or buzzes on the surface, often loudly. To fix this, people use more damping, a softer tool or pad, or impedance control on a torque-controlled arm.

If there is too little damping for the contact, the force trace shows repeated peaks with zero force between them. The fix is to set the damping for the stiffest surface, or raise it on contact.

If a soft arm is holding a heavy tool, the tool sags below its target. This requires accurate gravity compensation and stiffer settings in the vertical direction.

If you have a wrong mass model, the arm drifts or creeps as soon as it is made soft. You must identify the arm's masses, or use a learned arm model for the leftover error.

If a guarded move is too fast, you see a large force spike and a stop well past the surface. The fix is to slow down near the expected surface and lower the braking latency.

If the threshold is above the force that moves the object, the object slides away and the move never fires. You need to lower the threshold to just above the sensor noise, and average the readings.

If a contact happens on an axis the sensor does not measure, the guarded move never fires, and never reports an error. You must watch every axis the contact could appear on, and always set a travel limit.

If you need both accuracy and softness at once, you get a stiff arm that pushes too hard, or a soft one that misses. The solution is to be stiff in some directions and soft in others, or switch settings between phases.

Finally, if you have no force sensor and no torque-controlled joints, there is nothing to measure force with. People use motor current as a rough force estimate, or add a compliant pad or flange on the tool.

The problem of contact on an axis the sensor does not measure is the most dangerous one, because nothing looks wrong when it happens. Book 3 gives three concrete cases of this.

The next section lists libraries that provide it. The open-source choice is narrower here than for other techniques, because contact control needs hardware support. The page gives a table of well-known options.

For C++, the ros2_controllers library offers admittance control for a position-controlled arm with a wrist sensor, but there is no impedance controller in upstream ros2_controllers. The FZI cartesian_controllers library provides Cartesian compliance and force control as ros2_control plugins. The crisp_controllers library offers Cartesian impedance and operational-space controllers for any arm with a torque interface. For Franka arms, which sense torque in every joint, franka_ros2 and libfranka provide example impedance controllers. Pinocchio, available in C++ and Python, computes the gravity torque and the Jacobian that an impedance controller needs. MoveIt 2, however, plans collision-free motion only and has no force control.

A guarded move needs no special library at all. It is only a loop over the force sensor's topic with a stop command and a travel limit.

Simulators, however, deserve a warning. In a simulator the stiffness of a contact is a solver setting that nobody measured, so a compliance controller tuned against a simulated contact has been tuned against an invented number. This applies to every simulation on this page too: the wall stiffnesses here were chosen to show the effects clearly, not measured.

The next section summarises why to use impedance and force control, and what it costs. To put all of the above together, impedance control makes the arm apply a force equal to a chosen stiffness times its distance from the target, minus a chosen damping times its speed. Admittance control gives the same behaviour through a force sensor and a position-controlled arm, while a guarded move simply stops when a force threshold is passed. Together they let an arm touch things without knowing exactly where they are, with forces you chose in advance.

The obvious alternative is to make the positions accurate enough that contact is never a surprise, by calibrating the camera better, measuring the table and building a precise fixture. That works, and in a factory with fixed parts it is often the right answer. But it moves the cost into calibration and fixtures, and a 5 millimetre error turns a position controller into a 150 newton press. So compliance is chosen because being close and soft is cheaper than being exact and stiff.

The second alternative is a stiff position controller with a force limit, so that it cannot push past a set force. That is simple, and a gripper does exactly this. But the limit acts only at the extreme, because below it the arm is as stiff as ever, and a sideways error still jams a peg rather than guiding it in. Impedance control, in contrast, shapes the whole response rather than only its maximum.

The costs are these. You need the right hardware, meaning a wrist force sensor for admittance or torque-controlled joints for impedance. You also need an accurate model of the arm's masses, or the arm drifts when it is made soft. A soft arm is in any case an inaccurate arm, because any load pushes it off target. Stiffness and damping must be tuned for the stiffest surface the arm will meet, so a setting that is safe on metal is slow on foam. And outside ROS 2's admittance controller, much of this is code you write yourself or buy from the arm's maker.

The next section describes the learned alternative. Because the right reaction to a force can be hard to write down, the learned alternative for contact is a reinforcement learning policy, which learns by trying, usually in simulation, how to react to the force it feels. Book 6's worked example pushes a peg into a tight hole. It wins when the right reaction depends on forces too complicated to write rules for, the task is easy to score, and the contact can be simulated. Impedance control with a hand-written search pattern still wins when it is good enough, which is often, because it is easy to understand and check and needs no simulator, reward or training. It also wins when the contact cannot be simulated. A policy does not replace the force limits either, because nothing inside it stops it pushing too hard, so a programmed layer under it still limits forces and speeds. Book 6's force and slip models and collision and failure detection read the same force signals with learned models, to catch slip and unexpected contact. For tuning the stiffness and damping of the impedance controller itself, Book 6's Bayesian optimisation chooses each next setting to try from the scores of the tries so far, so a good setting is found in a few tens of real insertions.

The next section suggests where to read next. The page on PID control is the position loop this page modifies, and the loop inside an admittance controller's arm. The page on trajectory generation brings the arm to the start of the contact phase slowly and smoothly. Finite state machines are the usual way to switch between free motion, a guarded move, and pressing. Book 3's pages on controlling the move and holding on cover the same ideas with the ROS 2 packages, licences and hardware.

The final section is about using it in Python. Earlier parts of the page wrote the impedance law as a spring and a damper, and showed that ready-made controllers are often C++ plugins. This means there is no Python function called impedance control to just call. This section shows what the law itself looks like in Python, so you can see which parts a library provides and which parts are the two lines of algebra that stay yours.

The page shows a code example using the Pinocchio library for the geometry, because the impedance law needs the tool's position and the Jacobian, which is the matrix that relates joint speeds to tool speeds. The code sets up the robot model and defines the stiffness and damping matrices. Then, in a loop, it reads the joint angles and speeds.

What the library does for you is the geometry. It works out where every frame of the arm is for the current joint angles, it gives the Jacobian matrix that turns a force at the tool into joint torques, and it gives the torque that holds the arm up so that the spring does not have to. Writing any of those three by hand for a six-joint arm is a long job and an easy one to get wrong.

What you write is the law in the middle. The code computes the force by multiplying the stiffness by the position error, and subtracting the damping multiplied by the tool speed. It then converts that force into joint torques using the Jacobian, adds the gravity compensation, and sends the torques to the arm. You also write the target position, which normally comes from the trajectory generator, and you write the reading and the sending. Guarded moves need no library at all: they are just a loop over the force reading with a stop command and a travel limit.

There is one hard requirement behind all of this. The arm has to accept joint torques, because impedance control works by commanding torque. On a position-controlled arm you cannot run this code, and you write admittance instead, which means reading a wrist force sensor and moving the position target. For that case, ros2_controllers ships an admittance controller, but it is a C++ plugin whose stiffness and damping you set in a configuration file, so your Python only publishes the target and reads the state.

What you have to decide or measure is the list of numbers for stiffness and damping, and the frame they are written in. Each direction gets its own stiffness, so that the direction pressing into a surface can be soft while the others stay stiff. The damping then follows from the stiffness and the mass. The page warns again that a damping which is right in free space is too small the moment the tool touches something hard, so you set it with the stiffest surface in mind. Both matrices are expressed in the world's orientation at the tool, so if you want stiffness along the tool's own axis you must either rotate the stiffness matrix or ask for a different frame convention. One more measurement is easy to forget: a wrist force sensor reads the weight of the tool bolted to it, so you measure that reading with the tool hanging in free air and subtract it, or every force you compute will be wrong by the tool's weight.
