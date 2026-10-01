Learned motion planners. The previous page covered learning by trying, which takes over the part of a move where the arm touches something. So this page turns to the other part of the move, which is the long travel through open space. It answers one question: where can a neural network help an ordinary motion planner move an arm, and where is it better to leave the planner alone? It covers three kinds of learned helper, which are networks that plan a whole route, networks that check for collisions, and networks that work out joint angles.

The page is for a reader who knows what a robot arm and its joints are, and who has read the movement models overview. You do not need to know how a motion planner works inside, because the first section explains just enough of it. Every new word is explained where it first appears.

The honest summary comes first, because it is the most useful thing on the page. For moving an arm through open space, an ordinary planner is usually the better tool, since it is fast enough, it checks every move for collisions, and it is free. So a learned planner earns its place in a smaller set of jobs, which this page describes.

Before this, it helps to have read the page on sampling-based planning, which explains the ordinary planner and the collision checker that the networks here learn from.

The first section explains what a learned motion planner is. In short, it is a network that has studied a large number of answers from an ordinary planner. So it can give a similar answer much faster, in about the same time every run.

But first, what is an ordinary planner? A motion planner is a program that finds a route for the arm from where it is to where it needs to go, without hitting anything. A common kind, called a sampling-based planner, tries many random arm positions and throws away the ones that hit something. Then it joins up the good ones until it has a route from start to goal. But before it accepts any move, it asks a collision checker, which is a program that tests whether the arm's shape overlaps any obstacle's shape.

This approach works well. But the time it takes varies, because it usually answers quickly, while sometimes, in a tight space, it keeps trying random positions for much longer.

The page has a diagram comparing the time each planner takes. It shows that for a sampling planner, most runs are quick but a few take much longer. For a learned planner, every run takes about the same short time.

For example, a new taxi driver in a city uses a map and works out each route, while an experienced driver has driven thousands of routes and just knows which way to go. So the experienced driver is quicker than the new one. But the experienced driver can still make a wrong turn in a street that has changed, and the map can tell them so. A learned planner matches the experienced driver, while the ordinary planner and collision checker match the map, and they are still needed to check the answer.

The next part of the page lists what goes in and what comes out of the three kinds of learned helper. First is the learned route planner. It takes in a 3D picture of the scene, the arm's current joint angles, and the goal. It outputs the next arm position, or a whole route, and it replaces the search part of a sampling planner. Second is the learned collision checker. It takes in a set of joint angles and the scene. It outputs "hit" or "clear", or a distance to the nearest obstacle, and it replaces the exact geometric test while searching. Third is learned inverse kinematics. It takes in where the gripper should be and which way it should point. It outputs one or many sets of joint angles that put it there, and it replaces an iterative solver.

A 3D picture of the scene here usually means a point cloud, which is a list of 3D dots on every surface a depth camera sees. This is explained more fully on the point cloud models page.

Moving on to how a learned route planner works. It comes in two main designs. Both of them feed the scene and the goal into a network.

The first design proposes the next point, over and over. Here is how that design goes. First, a part of the network turns the point cloud into a short list of numbers that describes where the obstacles are. Second, the network looks at that description, the current arm position, and the goal position, and then it suggests the next arm position, which is a short hop towards the goal. Third, the arm position moves to that suggestion, and the second step repeats. Fourth, it stops when the suggestion reaches the goal. Finally, a classical collision checker tests each hop, and if a hop hits something, then an ordinary planner finds a replacement for just that hop.

A diagram illustrates this process. It shows a network proposing four points in turn, from the start to the goal. A checker passes the safe hops, finds that one hop clips a wall, and an ordinary planner replaces it with a detour.

The final step is the important one. The network has learned what good routes usually look like, but it can be wrong, so the check makes sure a wrong route never reaches the arm. And because only one short hop needed repairing, the whole job is still fast.

The second design is a learned sampler, which keeps the ordinary planner exactly as it is. The only change is where the planner picks its random positions. Instead of spreading them evenly everywhere, a network suggests positions in the places where routes usually pass, such as the gap between two shelves. So the planner finds a route sooner, and it still checks everything itself.

The next section covers learned collision checking. This exists because a collision check has to run many thousands of times while a planner searches. Each exact check compares the shapes of every arm link with every obstacle, which takes time. So a learned collision checker is a network that has seen many arm positions labelled "hit" or "clear", and it gives a quick guess for a new position.

Some versions give a distance instead of "hit" or "clear", which is how far the arm is from the nearest obstacle. A distance is useful to planners that improve a route step by step, because it tells them which way to push the route to get further from obstacles.

To see where this goes wrong, think of a simple arm with two joints and a post beside it. Each arm position is just two angles, so you can draw every possible position as one dot on a flat chart. Then the positions where the arm touches the post form a grey region on that chart.

A diagram shows this chart of all joint angles, with the true collision region and the network's slightly wrong guess of its edge. The network's guess is close, but not exact, so there are places where the network says "clear" when the arm is really touching the post.

The network is almost always right far from the edge, and its mistakes are near the edge. But that is exactly where a planner spends its time when it squeezes through a gap. So a learned checker is used only to guide the search, and the exact checker still tests the final route.

The next part explains learned inverse kinematics. Inverse kinematics, often shortened to IK, is the sum that answers which joint angles put the gripper here, pointing this way. The ordinary way to solve it is to start from a guess and improve it step by step, which is quick for easy targets. But it can be slow or fail for awkward ones, and the answer you get depends on the starting guess.

Many arms also have more than one correct answer for the same target. An arm with seven joints, or a flat arm with three joints reaching a point, can reach that target in many different ways, because it can hold its elbow high or low, for example.

A diagram compares the two approaches. It shows a classical solver giving one arm pose, while a learned solver gives five different arm poses at once, all putting the gripper on the exact same target.

A learned IK solver is a network trained on many pairs of joint angles and the gripper positions they produce. The pairs are easy to make, because you pick random joint angles and work out where the gripper ends up, using the arm's known sizes. That sum, from angles to gripper position, is called forward kinematics, and it is exact and fast, so the network only has to learn to go the other way. Some learned solvers, such as IKFlow, give many different answers at once, drawn from all the ways the arm can reach the target. A planner can then choose the answer that avoids obstacles or stays far from joint limits.

But the learned answer is usually close rather than exact. So people pass it to the ordinary solver as a starting guess, and the ordinary solver then finishes the job in a step or two.

The next section explains how these networks are trained. All three are trained in the same basic way, which has one large advantage, because the training data is made by a computer, and not collected by people.

First, a program makes many scenes by placing random boxes, shelves and tables around a simulated arm. Second, it asks the slow, correct method. An ordinary planner finds a route in each scene, or an exact collision checker labels many arm positions, or forward kinematics works out gripper positions for many random joint angles. Third, it saves the questions and answers. Each scene and goal is a question, and the planner's route is the answer to it. Finally, it trains the network to give the same answers. It shows the network a question, compares its answer with the saved one, and adjusts it a little. Then it repeats that many times.

Because a computer makes the data, people can make a great deal of it. Motion Policy Networks, for example, learned from millions of planner answers, so the cost here is computing time, and not human time.

But there is a catch in the first step, because the network only learns scenes like the ones the program made. If the program made boxes on tables, then a real kitchen with a hanging lamp may confuse it.

The page then lists some well-known models of this kind. First is MPNet, short for Motion Planning Networks. This is one of the first learned route planners, and it proposes the next point over and over. It then falls back to an ordinary planner when a hop fails its collision check. Second is learned sampling distributions, a method that trains a network to suggest where a sampling planner should try its random positions, while the planner itself stays unchanged. Third is Motion Policy Networks. This is a network for a Franka arm that takes a point cloud from a depth camera and produces a collision-free route directly. It was trained on millions of routes from an ordinary planner in generated scenes, and it answers in a fixed time. Fourth is SceneCollisionNet, a network that takes a point cloud and an object's position, and quickly says whether the object would hit anything. It was used to plan where to move objects when tidying a cluttered table. Fifth is Fastron, a learning method that builds a quick collision guesser for one arm, and updates it as obstacles move. Finally, IKFlow is a learned IK solver that gives many different joint-angle answers at once, all for the same gripper target.

To show where one of these models would actually earn its place, the next section gives a worked example of reaching into a shelf. Suppose a warehouse arm picks items from shelves, where the shelves are close together and the arm often has to reach into a narrow gap. The team uses an ordinary sampling planner, which works, but in the narrowest gaps it sometimes takes over a second to find a route, and the whole cell waits.

Here is how a learned helper could fit in. First, the team keeps the ordinary planner and the exact collision checker, so nothing is removed. Second, they generate many simulated shelf scenes with different gaps and item places, and the ordinary planner solves each one, however long it takes. Third, they train a learned sampler on these solutions, and it learns that routes into a shelf all pass through the front of the gap. Fourth, on the real arm, the planner now picks most of its random positions where the sampler suggests, so it finds a route sooner in the narrow gaps. Finally, the exact collision checker still tests the final route. If the learned sampler is wrong about a strange new shelf, then the planner simply takes longer, as it did before, and it does not crash.

Notice that the team did not replace the planner, because they only helped it with the slow cases. That is the pattern that works best in practice. And if the shelves were open and wide, then the ordinary planner would answer quickly every time, so there would be nothing for a network to fix.

The worked example kept the ordinary planner in place for a reason, and the next section explains the faults that cause this, and what people do about them.

First, a learned planner gives no guarantee. A network can return a route that hits something, or a collision guess that is wrong near an edge. So people always check the final route with an exact collision checker, and fall back to an ordinary planner when the check fails.

Second, it is confused by unusual scenes. A scene shaped unlike anything in training can give a poor answer. So people make the training scenes as varied as they can, and keep the ordinary planner as a fallback.

Third, it only works for the arm it learned. A network trained on one arm's joint lengths and shape does not work on a different arm. So you have to train again for each arm you own.

Fourth, it is hard to understand when it fails. An ordinary planner can at least say that it ran out of time, whereas a network just gives a route. So people log the inputs, so that they can replay a failure in simulation.

Finally, the ordinary tools keep getting faster. Planners that run on a graphics card now find routes quickly for many everyday scenes. So each gain on the classical side shrinks the gap a learned planner was built to fill, and the document on planning a path describes this.

The next section asks when a network is still worth adding. The obvious alternative is the ordinary planner with its exact collision checker and its ordinary IK solver. For most free-space moves, this is the right choice, because it is free, well tested, and it checks every move. It also answers quickly for most scenes, and a learned planner copies it, so it cannot do better than the planner it learned from.

You choose a learned helper only when the ordinary tools are too slow in a way that matters. Maybe the planning time varies too much for a cell with a strict cycle time. Or an optimiser needs a smooth distance to obstacles, or a seven-joint arm needs many IK answers to choose from. In those cases the learned helper gives a fast first answer, and the ordinary tools then check or finish it.

What it gives you is speed that stays the same from run to run, and a good first guess. What it costs you is a training set, a training run for each arm, and extra code. On top of that, the ordinary planner and checker have to stay in the system as well.

The page sums up the choice with a few common situations. If you have open space and planning is already fast enough, the usual choice is the ordinary planner with no learning. If planning is usually fast but sometimes far too slow, you choose a learned sampler or learned route planner, and keep the exact check. If an optimiser needs a smooth distance to obstacles, you choose a learned collision distance, with the exact check on the final route. If a redundant arm needs many IK answers quickly, you choose a learned IK solver, finished by the ordinary solver. And if the part is always in the same place, you use a taught, fixed route, with no planner at all.

The next part discusses the written alternative, which is unusually close at hand, because it is the set of ordinary tools these networks learn from. The page on sampling-based planning explains finding the route and checking it for collisions, and the page on numerical inverse kinematics explains finding the joint angles. When an optimiser needs a smooth distance to obstacles, the written tool is a distance field, which is explained on the volumetric maps page. Another page on planning a path explains how these planners behave on a real arm.

So the written tools are better for most moves through free space, and they stay in the system even when a learned helper is added. A learned helper is better only when the written tools are too slow, or too uneven in their speed, for the job.

The page then suggests where to read next. Since this page and the previous one both took over one part of an ordinary system, the reading either compares them, or moves on to the two methods that supply data and scores instead.

In the same chapter, the page on reinforcement learning policies covers learning by trying, which suits the contact at the end of a move. The page on diffusion and flow policies covers copying a person's movements. And the movement models overview compares every kind in the chapter.

In other chapters, the point cloud models page explains how a network reads the 3D dots these planners take in. The learned arm models page covers networks that learn the arm's own body. And the collision and failure detection page covers noticing a collision that has already happened, which is a different job.

There are also deeper documents available on learned pieces inside a planned system, sampling-based planners, what collision checking really checks, and why one gripper target can have many joint answers.

The final section is about using these tools in Python. It shows the learned inverse kinematics solver running in Python, and explains why it is the only one of the three you can realistically try. After hearing this, you will know what is downloadable in this area and what is not.

Learned inverse kinematics is the most packaged of the three, because the problem is small and self-contained. IKFlow publishes trained models for several arms, including the Franka Panda. There is a package on the Python package index, but it must be installed from a clone of the repository, and the authors only support Ubuntu.

The code imports the PyTorch library and gets the IK solver for a specific model. It then defines a target pose using coordinates and a rotation, and asks the solver to generate five different sets of joint angles that all reach that same pose.

Those five answers are the point of the method. The Franka has seven joints and only six are needed to reach a pose, so there are infinitely many correct answers, and an ordinary solver returns one of them. IKFlow returns a spread of different ones in a single pass, so you can then choose the one that is furthest from the joint limits, or nearest to where the arm already is. The library also has a function to polish the network's answers with a few ordinary numerical steps, because the network on its own is approximate and the polishing is what brings the error down to about a millimetre.

What the library gives you is the trained models, the sampling, and the checking. It will also tell you which answers break the joint limits or collide with the arm itself. What you have to supply is your arm. The published models are for the arms the authors trained, so if yours is not among them you train your own, which needs your arm's description file and the training script. You also have to decide which of the answers to use, because the model has no opinion about that. This is a genuine choice rather than a detail: picking the solution nearest the current joint angles avoids large sudden motions, while picking the one furthest from the limits leaves more room for the next move.

The other two helpers are harder to try, and it is worth saying so plainly rather than pretending otherwise. Motion Policy Networks, the learned route planner mentioned earlier, is published as a repository whose recommended installation is a Docker container of about 30 gigabytes, built on top of NVIDIA Isaac Sim, for which you need a developer account and an API key. You then download a checkpoint and run an inference script on planning problems in the repository's own format. There is no package to install and no simple call to make. SceneCollisionNet and Fastron are research code of the same kind. MPNet has no maintained release at all.

So the honest summary of this page in practice is that the learned parts of motion planning are mostly still papers with code attached, and the one you can actually use tomorrow is learned inverse kinematics. You choose a learned helper only when the ordinary tools are too slow in a way that matters, and the state of the software is a second reason to reach for the ordinary planner first. It is also why the one situation that is easy to act on today is the redundant arm needing many inverse kinematics answers quickly.
