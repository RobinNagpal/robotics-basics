Collision and failure detection. This page answers two related questions about noticing trouble. The first is how a robot arm notices that it has bumped into something it should not have touched. The second is how it notices that a task has gone wrong, such as a mug dropped halfway through a carry. To answer both, the page explains the simple method most arms already use, where a learned model improves on it, and where a learned model must not be trusted on its own.

It is written for a reader who has already read the overview of this chapter, and it also helps to have read how a model learns. You do not need to know any physics beyond this: a motor that has to push harder uses more electric current. Before this page, it helps to have read about arm dynamics, which works out the torque each joint should need, and sensor streams, which turns a noisy reading into a clean alarm. This page uses the first as the expected torque and the second to raise the alarm.

The first section explains what it is. A collision detector compares what the arm's sensors measure with what they should measure, and raises an alarm when the two differ too much. A failure detector does the same for a whole task.

Here is an everyday example of the same comparison. You walk through a dark room you know well. So you expect the floor to be flat and the path to be clear. If your shin meets a chair, you feel a push you did not expect, and you stop at once. So you did not need to see the chair at all. Instead, you noticed that what you felt was different from what you expected.

So a robot arm can do the same thing. It knows what torque each joint should need to follow its planned path, where a torque is a turning force, the force that turns a joint. So if something pushes on the arm, the joints need a different torque from the one expected, and that difference is the signal.

This page covers two jobs that use this same idea. First, collision detection notices unexpected contact on the arm's body, within a few thousandths of a second, so the arm can stop or yield. Second, failure detection notices that a task has gone wrong, meaning the object was not picked, it was dropped, or it was placed in the wrong spot. This can take longer, from a fraction of a second to a few seconds.

The next part covers what goes in and what comes out. The last section said what the signal is, so this section lists the readings that carry it. For collision detection, the inputs are the arm's own joint readings over the last moment. These include, first, the angle of each joint, from its encoder, which is the sensor that measures a joint's angle. Second, the speed of each joint. Third, the electric current in each motor, or the torque from a torque sensor in each joint, on arms that have one. And finally, the commands the controller sent. The output is "collision" or "no collision", often with a number that says how sure the model is, and some methods also say which part of the arm was hit.

For failure detection, the inputs are wider than that. They can include the wrist force, the gripper's finger position, tactile readings, and pictures from a camera. The output is "the task is going normally" or "something is wrong", and sometimes also the kind of failure.

Moving on to how it works inside, starting with the gap between expected and measured. The last section listed the readings, and this section says what is done with them. The core idea is the same for the simple method and for most learned ones. Two numbers are compared, and the difference between them is called the residual, where "residual" means what is left over.

First, some model predicts the torque each joint should need right now, given its angle, its speed and how fast it is speeding up. Second, the sensors measure the torque each joint actually uses. Third, the program subtracts one from the other. Finally, if the difference stays near zero, all is well, but if it jumps above a limit, the program reports a collision and the arm stops.

The page has a diagram showing the torque a model expects on one joint, the torque the motor measures, and the gap between them. It is a drawn example, not a real measurement. The top half shows the expected torque on one joint as a dashed line, and the measured torque as a solid line, and they match closely until the forearm hits a box. The bottom half shows the gap between them, and when that gap crosses the stop line, the arm stops.

So the quality of the whole method depends on the first step. If the prediction is poor, the gap is never near zero, even with no collision. Then the stop line has to be set high, and gentle collisions are missed. This is where learning helps most, because a learned model can predict the expected torque better than the textbook physics can. It manages that by learning the friction and other effects the textbook leaves out, and the learned arm models page explains how.

The next subsection is about where the arm was hit. Besides saying that something was hit, the residuals at all the joints also say roughly where the contact was. The page shows a diagram of a three-joint arm whose forearm touches a box. Because a push on the forearm turns the joints between the base and the forearm, those joints show a gap. However, it cannot turn the joint beyond the forearm, so that joint shows no gap. This means the last joint with a gap tells you which part of the arm was hit.

The next part describes learned collision detectors. A learned collision detector either skips the explicit subtraction or adds to it. It is a network that reads a short window of joint readings and outputs "collision" or "no collision", where a window means the last few hundredths of a second of readings taken together. Then the network learns patterns that a single limit cannot. For example, a fast movement makes a large gap for a moment, and so does a hard stop, while a gentle bump makes a small gap with a particular shape over time. So a network trained on many examples of both can tell them apart better than one fixed stop line can.

The next subsection covers learned failure detectors. However, a failure detector usually watches a whole task rather than one moment, and there are two common ways to build one.

The first way learns what a normal run looks like, from many runs that went well. Then it flags any run that looks different. This is called anomaly detection, where "anomaly" means something unusual. It needs no examples of failures at all, which is its great advantage, because failures are rare.

The page shows a diagram where many good picks form a grey band, and one pick leaves the band when the mug falls. It is a drawn example, not a real measurement. It shows the weight felt at the wrist during twenty-five picks that went well, as grey lines. Those lines form a narrow band, because the weight rises at the lift and falls at the put-down. One pick, in red, leaves the band halfway through the carry, because the weight vanished when the mug fell. So an anomaly detector learns the band and flags any run that leaves it.

A common network for this is an autoencoder, which is a network trained to squeeze its input down to a few numbers and then rebuild the input from them. It learns to rebuild normal runs well, so when it is shown an odd run, it rebuilds that run badly. This means a bad rebuild is a sign that the run is unusual.

The second way instead trains a model on labelled examples of success and failure. A vision-language model is a model that reads a picture and answers a question about it in words, so it can look at a picture after a task and answer "did the mug end up on the shelf?" The vision-language models page covers this.

The next section explains how it is trained. The last section described the detectors, and this section says where their examples come from. For a learned collision detector, you need windows of joint readings marked "collision" or "no collision".

The "no collision" examples are easy to get in bulk. You run the arm through many normal movements at many speeds, with and without loads in the gripper, and record everything.

The "collision" examples are harder, because you have to hit things on purpose. People push the arm by hand at different places, or let it move into soft padded objects at low speeds, and each contact is marked from the time it happened. Because this is slow and needs care, collision sets are much smaller than normal-motion sets.

For an anomaly detector, you need only normal runs. You record the task many times while it succeeds, and you train the model to rebuild those runs. Then you set the alarm limit using a separate batch of normal runs, so that normal variation does not trigger it.

For a success detector that uses a camera, you need pictures of finished tasks marked "success" or "failure". People often collect these for free, because a robot cell that is already running records its own results.

The next section lists well-known methods and models. First is the momentum observer. This is the classic non-learned method. It was developed by Alessandro De Luca, Sami Haddadin and colleagues, for lightweight arms at the German Aerospace Center. It computes the residual from earlier in a way that needs the joint speeds but not their rate of change, which is noisy to measure. It is the standard method in textbooks on this job. Haddadin and colleagues wrote a well-known survey of the whole field in 2017, called "Robot Collisions: A Survey on Detection, Isolation, and Identification".

Second is CollisionNet, by Heo and colleagues in 2019. This is a convolutional neural network that reads a short window of joint signals from a collaborative arm and outputs whether a collision happened, and it was trained on real collisions caused on purpose.

Third is the multimodal anomaly detector for robot-assisted feeding, by Park, Hoshi and Kemp in 2018. A robot fed a person with a spoon, and the model watched force, sound and motion signals and flagged anything unusual. It used a kind of autoencoder built from long short-term memory networks, where an LSTM is a network that reads a signal one step at a time and keeps a short memory of what it has read. It learned only from runs that went well.

Fourth is SuccessVQA, by Du and colleagues in 2023. It turns "did the task succeed?" into a question a vision-language model can answer about a video. It showed that such a model, once trained on examples, can serve as a success detector for many tasks.

Finally, REFLECT, by Liu and colleagues in 2023. It turns a robot's sensor readings into a written summary of what happened, and asks a large language model to explain why a task failed and suggest a fix.

The next section gives a worked example of a pick-and-place cell next to a person. Here is how the three detectors work together in one cell. A collaborative arm picks mugs from a tray and puts them on a shelf. While that happens, a person works at the next bench and sometimes reaches across.

First, the arm has a built-in safety function, which stops it if a joint torque goes far above what it expects. This function is certified, and the learned models below never replace it.

Second, on top, a learned model predicts the torque each joint needs. It was trained on the arm's own normal movements, so it knows this arm's friction and the weight of its gripper. The gap between its prediction and the measured torque is small in normal work.

Third, the person's elbow brushes the arm's forearm. The gap on joints one and two rises. It rises much less than a hard hit would make, but it is well above the small normal gap. The program slows the arm and moves it away from the contact.

Fourth, a few picks later, the wrist weight vanishes halfway through a carry, so the anomaly detector flags the run. The program then stops the cell and reports "object lost during carry", with the time.

Finally, at the end of each place, a camera takes one picture of the shelf. A success detector checks that a mug is in the expected spot before the next pick.

In this cell each layer catches something that the others miss. The certified function catches hard hits, while the learned residual catches gentle ones. The anomaly detector catches the dropped mug, which is not a collision at all, and the camera check catches a mug that was placed but fell over afterwards.

The next section covers what goes wrong. The sections above described these detectors at their best. This list gives the six things that go wrong in practice, and what people do about each one.

First, false alarms. A detector that stops the arm every few minutes for nothing is soon switched off, and the main cause is a poor prediction of the expected torque. So people improve the prediction, or they allow a larger gap during fast movements.

Second, missed gentle contacts. A stop line high enough to avoid false alarms may miss a soft bump, so people improve the prediction until the stop line can be lower.

Third, a new payload. If the gripper picks up something heavier than usual, the torques change, and the detector may call it a collision. So people tell the model the payload, or they weigh it first with the wrist sensor.

Fourth, rare failures. A failure that never happened during training may look normal to a classifier trained on labelled failures. That is why people use anomaly detection instead, because it flags anything unusual.

Fifth, wear. As the arm's gearboxes wear, friction changes, and the normal gap grows, so people retrain or recalibrate from time to time.

Finally, trusting it for safety. A learned detector has no guarantee. It must never be the only thing that keeps a person safe, so the certified safety function stays in place. The frameworks book makes the same point in its section on compliance: a safety function is separate, certified equipment.

The next section discusses why you would use this rather than the obvious alternative, and what it costs. The last section listed what goes wrong, so this section weighs those problems against the alternatives. The obvious alternative is a fixed torque limit on each joint, with no model of what the torque should be. This is simple and predictable, and every arm has it. However, the torque in normal work changes a lot with speed and pose, so a fixed limit must be set above the largest normal torque. This means a gentle bump during a slow movement never reaches it.

The next alternative is the momentum observer with a textbook physics model, which is what good collaborative arms already do. It is fast, well understood and needs no training data. So a learned model is worth adding only when this is not enough: when the textbook model's errors force the stop line so high that gentle contacts are missed, or when you want to catch failures that are not collisions at all, such as a dropped object.

What it costs you is four things. First, data. You need many normal runs, and for a collision classifier, some real collisions caused carefully on purpose. Second, tuning. Someone has to choose the alarm limit, and choose between false alarms and missed contacts. Third, upkeep. The model must be retrained when the gripper, the payload or the arm's wear changes. And fourth, no guarantee. It adds to the certified safety function and never replaces it.

The next section is about the written alternative. This page has argued for adding a learned model, so the last question is what the written version alone gives you. The written alternative is the expected-against-measured check with a textbook physics model, which is the second alternative in the previous section, and Book five gives the pieces. The page on arm dynamics works out the torque each joint should need, and the page on sensor streams turns the gap into an alarm that does not flicker. The page on safety monitoring covers the software checks that act on such an alarm, and where certified safety equipment must take over.

Because it is fast, needs no training data and is well understood, the written check wins on most arms. A learned model wins when the textbook model's errors force the stop line so high that gentle contacts are missed. It also wins when the failure is not a collision at all, such as a dropped mug.

The next section suggests where to read next. In this chapter, the page on learned arm models explains how a model learns to predict the torque each joint needs, which is the "expected" half of this page. The page on force and slip models covers a failure that starts in the fingers rather than on the arm.

Elsewhere in this book, the page on vision-language models explains how they can look at a picture and say whether a task succeeded. The page on learned motion planners includes learned collision checks, which predict a collision with an obstacle before the arm moves, whereas this page is about noticing one after it happens.

In the other books, the section on holding on explains how to confirm that a release really happened, which is failure detection without a model. And the page on controlling the move explains what the controller does between a planned path and the motors.

The final section is about using it in Python. Earlier, the page said that the whole method is a subtraction: the torque the physics says each joint should need, taken away from the torque the motors really used. This section shows that subtraction as code, because the expected torque is the one part you do not have to write, and after hearing it you will know which library computes it and what you still have to supply.

The code uses the Pinocchio library to build a model from the arm's description file. It then calculates the expected torque using the arm's joint angles, joint speeds, and how fast those speeds are changing. It subtracts this expected torque from the measured torque to find the residual. If the absolute value of the residual is greater than a set limit for any joint, it stops the arm and identifies the contact point by finding the last joint in the chain that crossed the limit.

Pinocchio gives you the expected torque, and that is the hard half. Its function is the recursive Newton-Euler algorithm, which is the standard way of computing the torques a chain of links needs, and it is fast enough to run inside a control loop, which a version you wrote in NumPy would not be. It reads the arm's masses and lengths from a URDF file, where "URDF" stands for unified robot description format and is the same file that ROS and most simulators read, so you normally already have it.

What you have to supply is everything the arm side of the subtraction needs. You read the angles, speeds, and acceleration from the joints, and on most arms you have to work the acceleration out from the speeds yourself, which is noisy, and that is exactly why the momentum observer mentioned earlier avoids it. You also have to turn the motor current into the measured torque, because an arm without joint torque sensors reports current rather than torque, and the two are only roughly proportional. Finally you have to run the arm through normal work to see how big the residual gets when nothing has been hit, since that is the only honest way to choose the limit.

What you have to decide is the limit, one number per joint, and the earlier section on what goes wrong says what each choice costs: too low and the arm stops for nothing, too high and it misses a gentle bump. For the failure detector, where you have only good runs and no failures, the short version is to use the Isolation Forest algorithm from scikit-learn. You fit it on features from your normal runs and it then returns a negative one for a run that does not look like them. Neither of these replaces the arm's certified safety function, for the reason given earlier.
