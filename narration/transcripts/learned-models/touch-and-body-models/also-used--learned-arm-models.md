Learned arm models. This page answers one question: how can a robot arm learn how its own body behaves, when the numbers in its manual are not quite right? To answer that, it explains what such a model predicts, how it is trained from the arm's own movements, the well-known kinds, and when it is worth using instead of plain physics.

It is written for a reader who has already read the overview of this chapter and the first chapter of this book. You should know from Book 1 that an arm is a chain of joints and links, and that each joint has a motor and an encoder, which is the sensor that measures the joint's angle. Before this page, it helps to have read the page on arm dynamics, which explains the textbook model of the torque each joint needs, and the page on system identification, which measures the numbers inside it. This page learns the part that those two leave out.

The first section explains what a learned arm model is. It is a model of the arm's own body, learned from recordings of the arm moving. 

Here is an everyday example of the same learning. When you start using a new bicycle, you do not know exactly how hard to push the pedals to go at a given speed. However, after a few rides you do. By then you have learned how this bicycle behaves: how heavy it is, how stiff its chain is, and how much its brakes grab, and nobody gave you any of those numbers.

A robot arm has a description of itself, too. The maker gives the length of each link, the mass of each part, and where each part's weight is centred, and from those numbers physics can work out how much torque each joint needs to move in a given way. A torque is a turning force, the force a motor uses to turn its joint. This is the arm's dynamics: how forces turn into movement.

However, the maker's description is close rather than exact. It leaves out the friction in the gearboxes, and it also leaves out the cables that hang along the arm and pull on it. It also does not know about the gripper you bolted on, or the wear after years of use. So a learned arm model fills in what the description leaves out.

This page also covers two related jobs of the same kind. Calibration means finding the small errors in the arm's geometry, so that the arm goes exactly where it is told. A self-model is a model an arm builds of its own shape, often by watching itself with a camera.

Now that the job is clear, the next part covers what goes in and what comes out. There are two main directions for such a model, and they answer opposite questions. 

The diagram shows the same arm twice. The dark arm is where it is now, while the pale arm is where it will be, or where you want it, a moment later. Orange arrows show the torques at the joints.

A forward model answers the question: if I apply these torques now, where will the arm be a moment from now? Its input is the joint angles, the joint speeds, and the torques. Its output is the joint angles and speeds a moment later.

An inverse model answers the opposite question: to move the way I want, what torque does each joint need? Its input is the joint angles, the joint speeds, and the change in speed you want, and its output is one torque for each joint.

Because the controller uses it to work out the torque to send to each motor, the inverse model is the one used most on real arms. The page on collision uses the same prediction as its expected torque.

A self-model has different inputs and outputs from both of those. Its input is the joint angles, and its output is the arm's shape in space, meaning which points around the robot the arm fills.

Moving on to how it works inside, most learned arm models used in practice do not throw away physics. Instead, they keep the textbook model and learn only the part it gets wrong. This is called residual learning, because the network learns the residual, which is what is left over after the physics has done its part.

The diagram shows a drawn example, not a real measurement, of the torque one joint needs at different speeds. A dashed line shows the textbook model, which leaves out friction, while dots show what the real arm needs. At zero speed the dots jump, because the joint must first overcome the friction that holds it still. A solid line shows the textbook model with a learned correction added, and it follows the dots.

The steps are as follows. First, the textbook model works out a torque from the joint angles, speeds, and the change in speed you want. Second, a small network looks at the same inputs and works out a correction. Finally, the program adds the two together and sends that torque to the motor.

This has two advantages over learning everything from nothing. The network has a small job, so it needs less data. Also, where the network has seen nothing, the textbook model still gives a sensible answer.

Instead of adding a correction, a second kind of model learns the whole thing from data, but it is built so that its answers obey the rules of physics. For example, the energy of a moving arm cannot appear from nowhere, so a network built this way cannot give an answer that breaks that rule. This means it needs less data than a plain network, and its answers are more sensible outside the training data.

A plain network with no physics inside it can also learn the whole model. However, it needs the most data of all, and it can give strange answers for movements it has never seen.

A self-model learns the arm's shape instead of its torques, and one way of building one works in two stages. The diagram shows an arm moving to many random poses while a camera records it, and each picture is paired with the joint angles at that moment. Then, the trained model is given a pair of angles it has never seen. For each point in space around the robot, it says whether the arm would fill that point. 

Once an arm has a self-model, it can plan without being told its own shape. So if a part is bent or replaced, the arm can record itself again and learn the new shape.

Calibration is usually done without a neural network at all. The arm moves to many poses, and a precise measuring device, such as a laser tracker, records where the tool really is. A program then finds the small errors in the link lengths and joint angles that best explain the difference.

However, some errors are not simple length or angle errors. The links bend a little under their own weight, and the gears have a little play. So a small network can learn these left-over errors, in the same way as the residual learning mentioned earlier. It takes the joint angles as input, and it outputs the correction to the tool's position.

The last section described the model, and the next section explains how it is trained and where its recordings come from. A learned arm model trains on the arm's own movements. This is its great advantage, because that data is cheap and safe to collect.

First, the arm moves through many different movements. People often use smooth movements that sweep each joint through its range at different speeds, so the model sees a wide variety. Second, at each moment, the program records the joint angles, the joint speeds, and the torque or current in each motor. The speed change is worked out from the speeds. Third, for an inverse model, each moment becomes one example. The input is the angles, the speeds, and the speed change. The right answer is the torque that was actually used. Finally, the network is trained to give the right answer for each example.

Because the arm reports many readings a second, an hour of movement gives a very large number of examples. This means the limit is not the number of examples but how varied they are, because a model trained only on slow movements does badly on fast ones.

For a self-model, the data is the joint angles paired with camera pictures. For calibration, it is the joint angles paired with measurements from the precise measuring device.

There are several well-known models in this area. First is locally weighted projection regression, an early learning method for arm dynamics from before deep networks. It fits many small simple models, each good for one region of movement, and blends them, and it can learn while the arm runs. 

Second is local Gaussian process regression. A Gaussian process is a learning method that gives both a prediction and how sure it is. This work made it fast enough to learn an arm's inverse model while the arm runs. 

Third are Deep Lagrangian Networks, which are built so that their answers follow the rules of physics for moving bodies. They learned an arm's inverse model from less data than a plain network, and gave more sensible answers for new movements. 

Fourth is the actuator network. A team learned a model of each motor of a four-legged robot from recordings. They put that model inside a simulator, so that the simulated motors behaved like the real ones. Policies trained in that simulator then worked on the real robot. It is a legged robot, not an arm, but the idea transfers directly to arm motors. 

Fifth are task-agnostic self-modeling machines, where a robot arm moved at random, learned a model of itself from the recordings, and then used that model to plan tasks. When a part was damaged, it learned the change. 

Finally, full-body visual self-modeling, where an arm watched itself with cameras and learned which points in space its body fills for any set of joint angles.

To make this concrete, here is a worked example of a heavier gripper on an old arm, step by step. An arm has worked in a cell for several years. Then the team fits a new, heavier gripper with a tactile sensor on each finger. Two problems then appear. The arm follows its planned paths less exactly than before, and its collision detector gives false alarms during fast moves.

To fix this, first, the team keeps the maker's physics model, but adds the new gripper's mass. Second, they run the arm through an hour of varied movements, with the gripper open and empty, and record the joint angles, speeds, and motor currents. Third, they train a small network to predict the residual, which is the difference between the torque the physics model gives and the torque the motors actually used. Fourth, the network learns two things the physics model left out. The first is the friction in each gearbox, which has grown with wear. The second is the pull of the new gripper's cable, which drags on the last two joints. Fifth, the controller now sends the physics torque plus the learned correction, so the arm follows its paths more closely. Finally, the collision detector uses the same corrected prediction as its expected torque. Its gap in normal work is now smaller, so the stop line can be set lower without false alarms. Gentle bumps that it used to miss now cross the line.

The model will need retraining when the gripper changes again, or when the wear changes the friction further. So the team schedules a short recording run every few months, and compares the new residual with the old one.

The sections above described this kind of model at its best. The next part lists six things that go wrong in practice, and what people do about each one.

First, movements it has not seen. A model trained on slow movements gives poor answers for fast ones. So people collect varied data, and they keep a physics model underneath so that the answer is never far off.

Second, changes over time. Friction changes as the arm warms up during the day, and as the gearboxes wear over years. So people retrain from time to time, or they use a method that learns while the arm runs.

Third, a payload it does not know about. The model learned the arm with an empty gripper, so a heavy object in the gripper changes the torques. People give the model the payload's mass as an input, or they weigh the object first with the wrist sensor.

Fourth, motor current is not torque. On arms without joint torque sensors, the model learns from motor current, but current is only roughly proportional to torque, because the friction in the gearbox sits between them. So people accept a coarser model, or they use an arm that measures joint torque directly.

Fifth, speed. The controller needs a torque answer many hundreds of times a second, and a large network may be too slow. So people use small networks for this job. The page on running a model on a robot explains the trade-off.

Finally, there is no guarantee. A learned correction can make things worse in an odd pose. A controller that uses one should limit how large the correction may be.

The last section listed what goes wrong, so this section weighs those problems against the alternative. The obvious alternative is a better physics model, identified from data, and that is called system identification. You keep the textbook equations, and you measure the arm's real masses and friction numbers by running it through set movements and fitting the numbers. This is a well-established method, because it needs little data, its answers can be checked, and it behaves sensibly everywhere. So it is the right first step, and it is often enough on its own.

A learned model is worth adding when the effects left over do not fit the textbook equations. Friction that changes with speed and temperature, a cable that pulls differently in each pose, and a link that bends under load are all examples, because none of them is a simple number to fit. Instead, a network can learn them from the same recordings.

A self-model is worth it in a different case, which is when the arm's shape is not known in advance or may change, such as a new or damaged robot. For a standard factory arm with an accurate description, it is not needed.

What it costs you is, first, recording time on the arm. It is cheap and safe, but it must be varied. Second, retraining whenever the arm, its gripper, or its wear changes. Third, a model that must run fast enough for the controller. And finally, a model that gives no guarantee. You must keep the physics model underneath, and limit the size of the learned correction.

This page has argued for adding a learned correction, so the next question is what the written model alone gives you. The written alternative is the textbook model with its numbers measured on your own arm, which is the first alternative just mentioned. The page on arm dynamics explains the model. The page on system identification explains how to move the arm so that the data can tell the numbers apart, and how to fit them. The geometry calibration mentioned earlier is written code too: a fit of the kind that the page on least-squares fitting explains.

Because it needs little data and behaves sensibly everywhere, the written model wins as a first step, and it is often enough on its own. A learned correction wins only for effects that are not a simple number to fit, such as friction that changes with temperature, or a cable that pulls differently in each pose.

Before looking at the code, the page suggests where to read next. In this chapter, the page on collision and failure detection uses the inverse model from this page as its expected torque. The overview compares all four kinds of models. 

Elsewhere in this book, the page on learned dynamics models predicts how the world changes when the arm acts. A learned arm model is the same idea with the arm's own body as the whole world. The page on learned motion planners covers learned inverse kinematics, which is a network that turns a wanted gripper position into joint angles. Also, reinforcement learning policies are often trained in a simulator, and a learned model of the arm's motors makes that simulator closer to the real arm. 

In the other books, the frameworks book describes where small learned models help a planned arm, and explains what the controller does with a torque. The perception book covers calibrating the camera and the arm together.

The final section shows how to use this in Python. Earlier, the page said that a learned arm model in practice keeps the textbook physics and learns only the part it gets wrong. This split is visible in the code: one library computes the physics, and a network of about six lines learns the leftover. After hearing this, you will understand how to turn an hour of recordings into a correction that the controller can add.

The training code first loads the robot's physical description using the Pinocchio library. Then it loads the recorded data: one row per recorded moment, containing the joint angles, the joint speeds, how fast those speeds changed, and the torque used. It uses Pinocchio to calculate the physics-based torque for every moment. 

The code then sets up a small neural network using PyTorch. The input to the network is the angles, speeds, and speed changes. The target output to learn is the actual torque minus the physics torque, so it learns only what the physics missed. The network trains for two thousand steps to minimize the error.

At run time, the controller then adds the two parts together, and it limits how much the network is allowed to change, to provide a safety guarantee. It asks the network for a correction based on the current angles, speeds, and the change in speed the controller wants. It then sends the motors the physics torque plus the learned correction, clipped to a safe range between minus five and five.

Pinocchio gives you the physics half, and it reads the masses and lengths from the arm's own description file. It is fast enough to run in a control loop, which matters here because this model is asked hundreds of times a second rather than once per picture. PyTorch gives you the network, and it can be small precisely because the physics has already done most of the work.

What you have to collect yourself is the recording. You sweep every joint through its range at many speeds, with the gripper empty, and log the angles, the speeds, and the motor torque or current at every reading. You also have to work out the speed change from the speeds, because most arms do not report it, and you have to keep the same units on both sides of the subtraction, since a current in amps minus a torque in newton metres is not a residual but a mistake.

What you have to decide is how varied the recording is, how large the network may be and still answer in time, and what the clipping limit should be. The first of those matters most, because a model trained only on slow movements is confidently wrong on fast ones, and the physics model underneath is the only thing that keeps the answer sensible there. Retrain after every change to the gripper, the payload, or the arm's wear, just as the worked example does.
