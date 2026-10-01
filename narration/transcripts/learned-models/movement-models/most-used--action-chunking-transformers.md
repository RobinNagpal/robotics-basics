Action chunking transformers.

The previous page ended with a problem: a policy that chooses one move at a time lets small mistakes add up until the arm drifts away from anything it was shown. This page explains ACT, which is short for Action Chunking with Transformers, and which was built to reduce that adding-up. ACT is a movement model that looks at the robot's cameras and chooses the next burst of moves all at once, instead of one move at a time. It was published in 2023 together with ALOHA, a cheap two-armed robot for recording demonstrations, and today it is the first policy most people train, usually through a software library called LeRobot.

The page answers five questions, in the order you would meet them. What does ACT take in, and what does it give out? How does the model work inside, once the data is in? How is it trained, and on how much recorded data? What are ALOHA and LeRobot, and why do they come up every time? And when is ACT the right choice for your own task? 

It is for a reader who has read about behaviour cloning, because ACT is a kind of behaviour cloning, and it was built to fix the problem of small mistakes adding up that is described there.

The first section explains what ACT is. The introduction said that ACT chooses a burst of moves at once, and this section says what that burst is called and why it helps. In other words, ACT is a behaviour cloning policy that predicts a whole chunk of future moves at each decision.

A chunk is a short list of moves, one after another, and in ACT a chunk is usually one hundred moves long. The arm makes fifty moves a second, so one chunk covers the next two seconds.

For example, when you pour water from a jug into a glass, you do not decide what to do every hundredth of a second. Instead you decide on the next second or so of pouring: tip the jug, hold it, start to tip it back. Then you look at the glass and decide again. So you make only a few decisions, and each one covers a stretch of movement.

ACT does the same thing. A diagram compares a policy that decides one move at a time with one that decides a chunk at a time. It shows twelve decisions of one move each, against two decisions of six moves each. With one move per decision there are twelve chances for a small mistake, while with chunks there are only two.

This is why chunking helps with compounding error, which is the adding-up of small mistakes from behaviour cloning. Mistakes build on each other at each new decision, so fewer decisions means fewer chances for them to build up.

The other half of the name is transformer, which is a kind of neural network. It takes a set of pieces, such as parts of a picture, and it lets each piece take information from every other piece. The main step inside it is called attention, because for each piece the network works out which other pieces matter to it, and how much. Transformers were first used for text, and they are now used for pictures and actions too.

The next part of the page covers what goes in and what comes out. It gives the exact numbers that the original ACT reads and writes. In the original ACT the robot is ALOHA, which has two arms, and each arm has six joints and a gripper. That makes fourteen numbers in all, and together they describe where the robot is.

So the observation that ACT reads at each moment has two parts. First, four camera pictures, each 480 pixels tall and 640 pixels wide, where one camera looks down from above, one looks from the front, and one sits on each wrist. Second, the fourteen current joint positions, which are six joint angles and one gripper opening for each arm.

The action is a chunk of one hundred targets for each of the fourteen joints, which is 1,400 numbers in all. Each target is a joint position the arm should reach at one moment in the next two seconds. But the targets are joint positions rather than motor commands. So ordinary control code in each joint moves the motor towards each target.

The third section explains how it works inside. It follows the data between the input and the output. When ACT runs on the robot, that data goes through three steps.

First, an image encoder turns each picture into a grid of numbers. An encoder is the part of a network that turns its input into numbers the rest of the network can use. ACT uses ResNet-18, which is a small and well-known convolutional neural network. For each picture it gives a small grid, and each cell of that grid holds a list of numbers that describe one patch of the picture.

Second, a transformer compares every piece with every other piece. All the grid cells from all four cameras go into the transformer, together with the joint positions. Attention lets a piece from the wrist camera use a piece from the top camera, so this is how the network can match where the gripper is with where the cup is.

Third, the transformer gives out the chunk. The last part of the transformer has one hundred slots, one for each future moment, and each slot is turned into fourteen joint targets.

A diagram shows this process: four camera pictures and the joint angles go in, and one hundred future targets for each joint come out. A plot next to it shows the chunk for one joint, the elbow, forming a smooth curve of one hundred targets over two seconds.

These three steps give one chunk for one situation, but people do the same task in slightly different ways. For example, one time the demonstrator moves quickly, and another time slowly. A network that has to give one answer blends these ways together.

But ACT has a partial fix for this problem. During training only, a second small network looks at the real chunk the person made, and it sums up how the person did it this time in a few numbers. We can call those few numbers the style numbers. The main network gets the style numbers as an extra input. So it does not have to blend different styles, because the style numbers tell it which one to produce.

At run time there is no person, so there is no real chunk to look at. ACT therefore sets the style numbers to zero, which stands for the most typical style, and the result is a smooth, typical movement.

This design has a name, which is a conditional variational autoencoder, or CVAE. However, you do not need the details of it to use ACT. The idea is only that some of the variation between demonstrations is put into separate numbers, so that it does not blur the actions. It is only a partial fix, because setting the style to typical at run time still gives one answer. So if half the demonstrations go left of an obstacle and half go right, ACT can still struggle.

A chunk covers two seconds, so if the arm plays the whole chunk without looking again, it cannot react to anything that happens during those two seconds. There are two common ways to run ACT, and they differ in how they handle that.

The first way is to play part or all of a chunk, and then ask the policy for a new one. This is simple, but the arm can jump a little where one chunk ends and the next begins.

The second way is to ask the policy for a new chunk at every step, and then blend the chunks together. The ACT paper calls this temporal ensembling, because temporal means to do with time, and ensembling means combining several guesses into one. A diagram shows four overlapping chunks that each predict the elbow angle for step three, and the arm uses their weighted average. A weighted average is an average where some values count for more than others. This makes the movement smooth, because one odd guess is outweighed by the others.

The fourth section describes how it is trained. ACT is trained like any behaviour cloning policy, with one change: the answer is a whole chunk, and not one move.

The data is a set of demonstrations. At each moment of each demonstration, the training program takes the pictures and joint positions as the question. Then it takes the next one hundred recorded joint positions as the answer. The loss is the size of the difference between the predicted chunk and the recorded chunk, added up over all 1,400 numbers. The training program then nudges the network to make that loss smaller.

In the ACT paper, each task was learned from about fifty demonstrations, which is about ten minutes of recording. The tasks were fine two-handed tasks, such as opening a small plastic cup with a lid and slotting a battery into a holder. This is much less data than people expected fine tasks to need, and that is the main reason ACT became popular. Training runs on one ordinary graphics card, so it does not need a cluster of computers.

The fifth section explains ALOHA and LeRobot. ACT is closely tied to these two names.

ALOHA is the robot ACT was built for. It stands for A Low-cost Open-source Hardware System for Bimanual Teleoperation, where bimanual means using two hands. ALOHA has two follower arms, which do the task, and two smaller leader arms, which a person holds and moves by hand. Each follower joint copies the matching leader joint, and there are four cameras. A diagram shows the setup: a person moves two small grey leader arms, and two bigger blue follower arms copy them joint by joint to do the task, while the cameras and joint sensors record everything.

This way of recording has one large advantage over a joystick. The person's hands do the task directly, joint for joint, so they can control all fourteen joints at once. The designs were published openly, so other groups could build the same robot.

LeRobot is a free software library from the company Hugging Face, first released in 2024. It holds a standard way to store robot recordings, the code to train several kinds of policy, and drivers for cheap robot arms. ACT is one of its policies, and LeRobot recommends it as a first policy. LeRobot also works with cheap leader-and-follower arms, such as the SO-101, which use small hobby motors and 3D-printed parts. A pair costs a few hundred dollars, so a person can record ACT demonstrations at home.

The sixth section lists well-known models of this kind. First is the original ACT from 2023, published with ALOHA. Second is the ALOHA recording robot itself. Third is Mobile ALOHA from 2024, which put the ALOHA arms on a wheeled base so the robot can move around a room. Fourth is ALOHA 2 from Google DeepMind, a sturdier redesign of the hardware. Finally, LeRobot's ACT is the version most people use today. The idea of predicting a chunk of actions spread well beyond ACT itself, and almost every policy since ACT does some kind of chunking.

The seventh section gives a worked example: putting a paper cup into a box with a cheap arm. Say you have one SO-101 follower arm with its leader arm, one camera looking down, and one camera on the wrist. First you record fifty demonstrations with LeRobot, moving the cup to a new place each time. Then you train ACT on those fifty demonstrations using LeRobot's training script on one graphics card. Then you run the trained policy on the real arm. Every time it is asked, it looks at both cameras and the joint angles, and it gives the next chunk of joint targets. The motion is smooth, because each chunk is a smooth two-second plan. But if you move the cup while the arm is reaching, and the policy is playing a long chunk, the arm keeps going to the old place for a moment before it reacts. That delay is the price of the chunk.

The eighth section covers what goes wrong. ACT shares the problems of every behaviour cloning policy: it only works in situations like the ones it was trained on, the cameras must stay where they were, it cannot say it does not know, and it knows nothing about collisions.

ACT also has problems of its own. First, the chunk length is a trade-off. Longer chunks mean fewer decisions and less adding-up of mistakes, but they also mean slower reactions. The ACT paper showed success going from one percent with one move per decision to forty-four percent with one hundred moves per chunk, and then getting worse again with longer chunks. The best length depends on your task.

Second, the style numbers only partly fix the problem of two good ways becoming one bad way. If the demonstrations split into two different paths, ACT can still blend them. Third, fifty demonstrations is enough for a narrow task, but not for a task that varies a lot. Finally, ACT learns one task at a time and does not take a sentence as input, so it cannot be told to do a different task.

The ninth section weighs why you would choose ACT, and what it costs. It gives you smooth, fine movement from a small number of demonstrations, on cheap hardware and one graphics card. That is why it is the usual first policy. It is better than plain behaviour cloning because chunking stops small mistakes from adding up. It is simpler and cheaper to train than diffusion or flow policies, though those handle varied tasks better. What ACT costs you is careful recording, a policy that only works near its training data, no way to check it in advance, and the slower reactions that a long chunk brings.

The tenth section compares ACT with the written alternative, which is a route from sampling-based planning turned into smooth joint targets by trajectory generation. A written motion is planned as one whole movement, so it does not have the adding-up of small mistakes either. The written motion is better when the objects and the task stay the same, because you can check it before it runs. But ACT is better when the task is fine and easier to show than to write down, and when you can record a few dozen demonstrations of it.

The eleventh section suggests where to read next. The next page covers diffusion and flow policies. You can also read the chapter overview, or read about vision-language-action models to see how chunks are used in very large policies. There are also pages on running a model on a robot, learned motion, and data and demonstration.

The final section explains using ACT in Python. The training is a command rather than a program, because LeRobot reads the number of joints and cameras from your dataset and sizes the network to fit. The Python code then runs what that produced. It loads the pretrained policy and sets up processors for the data. It then resets the policy, which empties a queue of unused actions from the last attempt. Finally, it selects an action in a loop.

The code relies on two main numbers that control the chunking. The first is the chunk size, which is how many future actions the network produces in one pass. It defaults to one hundred, which at thirty pictures a second is a little over three seconds of movement. The second is the number of action steps, which is how many of those moves the robot actually carries out before the policy is asked again. The function that selects the action hides the difference: it keeps a queue, returns the next action from it, and only runs the network again when the queue is empty.

If you want the blending described earlier instead of plain chunks, you turn on a setting called the temporal ensemble coefficient. LeRobot requires the number of action steps to be one when you use it, because blending means the policy must run at every single step.

What LeRobot gives you is the network, the training loop, the queue, and the scaling. What you have to collect is the demonstrations, and ACT is the model where this is least avoidable. ACT was designed for delicate tasks, so the demonstrations have to be good. Careless demonstrations train a policy that fails delicately. There is no pretrained ACT policy that transfers, because the network's output layer has one number per joint of the arm it was trained on.

What you have to decide is the pair of numbers. A larger number of action steps means smoother motion and fewer decisions, but the arm reacts late if the object moves. A smaller number reacts sooner but brings back some of the jerkiness. Half of the chunk size is a common starting point, and the right answer depends on how much the scene moves while the arm is working.
