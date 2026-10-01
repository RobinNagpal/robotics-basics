Diffusion and flow policies.

The previous page said that action chunking reduces the adding-up of small mistakes, but it left one fault unfixed. When people show the same task in two different ways, the model still blends the two. So this page answers one question. When people show a robot arm the same task in different ways, how can a model copy them without mixing the ways together? The answer is a kind of movement model called a diffusion policy, together with its faster relative, the flow policy.

The next part of the page explains what it is. In short, a diffusion policy starts from a random guess at the arm's next movements, and it cleans that guess up in several small steps, until the guess looks like something a person really did.

A policy is the name for any model that decides what the arm does next, which it does by looking at the world and giving back an action. An action is a movement command, such as moving the gripper one centimetre to the left and closing it a little.

But to see why a new kind of policy was needed, think about an everyday example. You ask six people to carry a mug from one side of a table to the other, and there is a box in the middle. Three people go round the left of the box, and three people go round the right, so all six did the job well.

Now suppose a simple model learns from these six people. This is a model that gives one answer for each situation, and it tries to be as close as possible to all six people at once. But the answer closest to three going left and three going right is the middle. So the model learns to go straight through the middle, into the box, which is something none of the six people ever did.

The page has a diagram showing this problem. It shows the pale paths of the demonstrations going over or under a box, and a red dashed line representing the average of them, which runs straight into the box. Beside it, a second picture shows what a diffusion policy does instead, which is that each time it runs it picks one whole path that looks like a real demonstration.

A task with more than one good way to do it is called multi-modal, and a mode is one of those good ways, so going left is one mode and going right is another. Diffusion policies were built to handle multi-modal tasks, because they learn the whole spread of ways that people did the task, and each time they run they pick one of them.

A flow policy does the same job with a method called flow matching, and it usually needs fewer clean-up steps, so it runs faster. The difference between them is explained a little later.

First, the page covers what goes in and what comes out. Because the policy starts from a random guess, that random guess is one of its inputs. So a diffusion policy for a robot arm takes in three things altogether.

First, the latest camera pictures. Often there is one camera looking at the table and one camera on the wrist of the arm. Some policies take the last two or three pictures, so that they can see which way things are moving.

Second, the arm's own state. This is the angle of each joint and how open the gripper is, and the arm's own sensors measure these numbers.

Third, some random numbers. This is the starting guess that gets cleaned up, and it is called noise, because it is random and has no meaning yet.

Then the policy gives back a chunk of actions, which is a short list of the next movements, one after another, such as the next sixteen positions for the gripper. Chunks work better than one action at a time, and diffusion policies use them for that reason.

To turn that into a concrete example for an arm picking up a mug, the inputs are one picture from above the table and one from the wrist, the six joint angles and the gripper width, and a list of random numbers the same size as the output. The output is an action chunk containing the next sixteen gripper positions, each with an instruction to be open or closed.

The next section explains how it works inside. The cleaning-up happens in steps, and each step uses the same neural network. A neural network is a large calculation with many adjustable numbers, which a computer tunes by showing it examples.

Here is what happens each time the policy is asked for a new chunk.

First, the policy looks at the camera pictures and the arm state, and a part of the network turns them into a list of numbers that describes the scene.

Second, the policy makes a random chunk, where every position in it is random, so the chunk starts as a messy scatter of points.

Third, the network looks at the scene description, the messy chunk, and how many clean-up steps are left. From those it works out which way each point should move to look more like a real movement.

Fourth, the policy moves each point a little way in that direction.

Fifth, the third and fourth steps repeat, and after the last step the chunk is a clean, smooth path.

Finally, the arm plays the first part of the chunk, and then the policy looks again and makes a new chunk.

A diagram shows this process of one chunk being cleaned up. At the start the dots are random. Then at each step every dot moves a little, so by the last step they form a clean path from the start, round the box, to the mug.

But why does this whole procedure avoid the average? The answer is in the second step, because the random start is different each time. If the random dots happen to lean a little towards the top, then the clean-up pulls them into the path that goes over. But if they lean towards the bottom, the clean-up pulls them into the path that goes under. The network has learned where real paths are, rather than a single answer. So the random start decides which real path you get, and you never get the impossible middle.

Playing only part of the chunk matters on a real robot. This is because the world can change while the arm moves, since a mug can be nudged. So the policy plays a few movements, looks again, and plans again. This is sometimes called receding horizon, because the plan always reaches a fixed distance ahead of where the arm is now. A picture shows this, with rows representing plans of eight positions. The arm plays the first four positions, throws away the remaining four, and starts a new plan from where it now is.

The next section explains the difference between diffusion and flow matching. Both turn noise into a good chunk, but they differ in how the network learns the way from noise to the answer.

In diffusion, the network learns to remove a little noise at a time. This is an idea that came from models that make pictures, because those models learn to turn a screen of random coloured dots into a photo. So a diffusion policy does the same thing with a list of arm positions instead of a picture. But the path from noise to answer is wiggly, so it usually takes many small steps.

Instead, in flow matching, the network learns a direction to travel from the noise to the answer. During training, the method connects each noise sample to a real chunk by a straight line, and the network learns to point along those lines. Because the lines are straight, the policy can take a few big steps instead of many small ones.

A diagram compares the two. It shows the many small, wobbly steps of diffusion on one side, and the few straight steps of flow matching on the other, which end at the same kind of answer in less time.

Speed matters here because the network runs once per step. So if a policy needs many steps and each takes a few thousandths of a second, then the arm waits. Fewer steps means the arm can get a new chunk more often. This is one main reason most large robot models built in 2025 and 2026 use flow matching for their actions.

To summarize the comparison, both methods handle tasks with several good ways to do them. However, diffusion learns how to remove a little noise, takes a wiggly path, and needs many clean-up steps. You meet it in models like Diffusion Policy, RDT-1B, and Octo. Flow matching learns which direction to travel, takes a path close to a straight line, and needs few steps. You meet it in pi-zero and most newer large robot models.

The next section covers how it is trained. The network learns where real paths are from demonstrations, where a demonstration is one recording of a person doing the task by driving the robot. The recording keeps the camera pictures, the joint angles, and the commands the person gave, all at the same moments.

Training a diffusion policy works in six steps.

First, take a short piece of one demonstration, which is the pictures at one moment and the next sixteen actions the person really took.

Second, add a known amount of random noise to those sixteen actions, so that they become messy.

Third, ask the network which way the messy actions should move to get back to the real ones.

Fourth, compare its answer with the right answer, which you know, because you added the noise yourself.

Fifth, adjust the network's numbers a little, so that the next answer is closer.

Sixth, repeat with many pieces and many different amounts of noise.

Flow matching training is almost the same, and the difference is in the third step. There the network is asked for the straight-line direction from the noise to the real actions.

For one task, such as putting a mug on a plate, people usually record somewhere between tens and a few hundred demonstrations. Large general models that do many tasks are trained on far more, pooled from many robots, and then adjusted to a new task with a smaller set. In every case, training needs a computer with a graphics card, which is a chip that does many small sums at once.

The page then lists well-known models of this kind.

Diffusion Policy, from 2023, is the paper that made the idea popular for robot arms. It takes camera pictures and makes a chunk of actions by diffusion, showing clearly that the approach copes with tasks that have several good ways to do them.

3D Diffusion Policy, or DP3, from 2024, does the same job, but its input is a 3D point cloud instead of flat pictures. A point cloud is a list of 3D dots on the surfaces a depth camera sees.

Consistency Policy, from 2024, takes a trained diffusion policy and teaches a second network to jump to the answer in one or a few steps, so it runs much faster.

Octo, from 2024, is an early open, general model trained on many robots' data, and it uses a small diffusion part at the end to produce its actions.

RDT-1B, from 2024, is a large diffusion model built for robots with two arms working together.

Pi-zero, from 2024, is a large model that understands pictures and words, and it uses flow matching in a separate part, called the action expert, to turn its understanding into arm movements.

You can download and run Diffusion Policy inside the LeRobot framework.

The next section gives a worked example of reaching round a box to a mug. Suppose you want a small arm to pick up a mug and put it on a plate, and a cereal box stands between the arm and the mug. You record one hundred demonstrations, and in some of them you went round the left of the box. In others you went round the right, because that is what felt natural each time.

First, you train a plain behaviour-cloning policy on the recordings. On the robot it heads for the box, slows down near it, and bumps into it, because it learned the middle of the two ways.

Next, you train a diffusion policy on the same recordings. Here is what happens when you run it on the robot.

The two cameras send a picture each, and the arm reports its joint angles. The policy makes a random chunk of sixteen gripper positions and cleans it up in several steps. This time the random start leans left, so the chunk goes round the left of the box. The arm plays the first eight positions.

Then the policy looks again. It is already on the left, so the new chunk carries on round the left. It does not switch sides halfway, because a path that switches halfway does not look like any demonstration. Near the mug, the chunks slow down and bring the gripper round the handle, as the demonstrations did, and then the gripper closes. The policy carries the mug to the plate in the same way, and opens the gripper.

The next time you run it, the random start may lean right, and then the arm goes round the right instead. Both runs are correct, but they are also different.

This leads to the next section, which explains what goes wrong, and what people do about it.

First, it is slower than a plain policy. Each chunk needs several passes through the network, where a plain policy needs only one. So people reduce the number of steps with flow matching, or with a faster version such as Consistency Policy. They also run the next chunk's clean-up while the arm is still playing the current chunk.

Second, it does not do the same thing twice. Two runs from the same start can take different paths, and that is by design. But a factory cell that must repeat exactly the same motion cannot accept that, so people fix the random start to the same numbers each time, or they put a classical check above the policy.

Third, it only knows the situations it was shown. Like every copying method, it is confused by a scene unlike its demonstrations. For example, a new table colour, a camera moved by a few centimetres, or a mug it has never seen will all confuse it. The fix is more varied demonstrations, which cost time.

Fourth, it has no idea of obstacles it was not shown. The policy does not check for collisions, so if you put a new object in the way, it may drive into it. So a separate safety layer under the policy has to stop the arm.

Finally, its advantage is not always proven. A 2026 study found that on its tests, flow matching did no better than plain copying, while running several times more slowly. So try the simpler policy first, and measure whether the diffusion version really helps on your task.

The next section asks why you would choose this kind of policy, and what it costs. The obvious alternative is plain behaviour cloning, which gives one answer for each situation, and which is simpler, faster and easier to understand.

You choose a diffusion or flow policy when your demonstrations really contain several good ways to do the task, so that averaging them would be wrong. For example, reaching round an obstacle is one such task, grasping a mug by the handle or by the rim is another, and folding a cloth, where people fold in different orders, is a third.

What it gives you is a policy that stays inside one of the real ways of doing the task, instead of a blend that nobody ever performed.

What it costs you is speed, and also repeatability. It needs several network passes per chunk, and its results vary from run to run. It also needs the same amount of careful demonstration data as any copying method, and a graphics card to train on.

To sum up the choice, if there is only one sensible way to do your task, plain behaviour cloning or an action chunking transformer is enough. If people did the task in clearly different ways, a diffusion or flow policy is worth trying. If the motion must be the same every run, neither is right, and you should use a programmed motion. And if the policy is too slow on your computer, use flow matching, fewer steps, or a smaller model.

The next section looks at the written alternative, which is programmed motion. The written way to reach round an obstacle is a motion planner. Sampling-based planning is told where the box is, finds one route round it, and checks that route for collisions. It returns one route, so it never blends a way round the left with a way round the right. Trajectory generation then makes that route smooth.

The written way is better when the obstacles can be measured and the motion must be the same on every run. But a diffusion or flow policy is better when the task has several good ways that are easy to show and hard to write down, such as folding a cloth in different orders.

The page then suggests where to read next. This page finishes the three copying policies. You can go back over behaviour cloning and action chunking, or move on to reinforcement learning policies, which learn by trying and scoring instead of by copying. Other related topics include vision-language-action models, which use flow matching inside them, and the practicalities of running a model on a real robot where speed matters.

The final section explains how to use this in Python. The packaged version is the Diffusion Policy in the LeRobot framework. It also needs the diffusers library, because it borrows the noise schedule from there. Building the policy from scratch takes a little more code than an action chunking transformer does, because you have to tell it the shape of your data first.

The page shows a block of code that sets up the policy. It uses a function to read the shape of every camera and every joint from your dataset, so you do not have to write them out by hand. Then it creates a configuration with several important settings.

These settings are the whole subject of this page in a concrete form. One setting is the number of training timesteps, which is how finely the noise was added during training, and one hundred is the default. Another is the number of inference steps, which is how many cleaning steps you pay for at run time. If you leave it out it becomes equal to the training steps, which means one hundred forward passes of the network for every chunk of actions. Setting it to ten makes the policy ten times faster and slightly less precise, which is the trade-off described earlier. This speed-up only works well if you set the noise scheduler type to DDIM, because DDIM is the schedule designed to be skipped through, while the default expects every step. The code also sets the horizon, which is the number of actions produced in one pass, and the action steps, which is how many of those the robot actually carries out before planning again.

LeRobot gives you the network, the schedules, the training loop and the queue of actions. Training and running it use the same commands as other policies in the framework.

What you have to collect is the demonstrations, and here there is a specific reason why they cannot be borrowed. The whole advantage of a diffusion policy is that it keeps two different good ways of doing a task apart instead of averaging them. It can only do that if both ways are in your recordings. If you always reach round the box on the left, the policy learns one way and you have paid the extra computation for nothing. So recording for a diffusion policy means deliberately demonstrating the alternatives, which is a habit rather than a quantity, and it is the opposite of what people naturally do when they want consistent data.

The code example uses a simulated task with one camera and a simple action, so it loads and trains in minutes and is a fair place to check that your installation works. Moving to your own robot arm means using your own dataset, and the decision you cannot avoid is how many cleaning steps your control loop can afford, which depends on your graphics card and on how fast the arm has to react.
