Trajectory optimisation. This page explains trajectory optimisation, which is a way to plan an arm's motion by starting from a rough path and improving it, step by step. The aim is a path that is short, smooth and clear of obstacles, so the page answers five questions about how that is done. What does it mean to give a path a cost? How does a program lower that cost? What do the three well-known methods, CHOMP, STOMP and TrajOpt, do differently? Where does a robot arm use this? And when does it get stuck?

It is for a reader who has met a path planner before, for example on the pages about graph search and sampling-based planning. Those planners find a route, whereas this page is about making a route good. You do not need any calculus, because the one idea borrowed from it, the gradient, is explained where it first appears.

Book 3 compares the planner families in the section on planning a path. This page agrees with it and goes one level down, because it runs a small optimiser, so you can see every number move.

The first section gives the idea in one sentence. Write down one number that says how bad a path is, then keep nudging the path in the direction that makes that number smaller.

That number is called the cost, and a path that is long, jerky or close to an obstacle has a high cost. A path that is short, smooth and well clear of everything has a low cost instead. So the program never searches for a route from scratch, because it starts with a guess and improves it.

Here is an everyday example. Think of a garden hose laid straight across a lawn, with a flower bed in the way. You do not lay a new hose. Instead you push the middle of the hose sideways, off the bed, and the rest of the hose follows, since it is all one piece. Pushing too hard at one point makes a sharp kink, so you push a little at many points. Then, when the hose is off the bed and has no kinks, you stop.

Trajectory optimisation does the same thing with numbers, so the push off the bed is the obstacle cost, and the resistance to kinks is the smoothness cost.

A word on the name is needed here. A path is the list of positions the arm passes through, while a trajectory is a path with times attached. The methods on this page treat the points as evenly spaced in time, so smooth also means no sudden changes of speed. The exact timing is set afterwards, by the step on the page about trajectory generation.

The next part of the page explains how it works. It takes the idea apart in the order a program runs the steps. The example is flat, with two numbers per point, so that it can be drawn. Then a later step explains what changes for a real arm with six joints.

Step one is that a path is a list of waypoints. The program stores the path as a list of points called waypoints, where the first waypoint is the start and the last one is the goal. Those two never move, but all the others are free to move.

The example uses twenty-one waypoints, with the start at zero, zero and the goal at ten, zero. One unit is ten centimetres, so the move is one metre long. The first guess is the obvious one, which is a straight line with the waypoints spread evenly along it, five centimetres apart.

In the middle of the area stands a round pot, thirty centimetres across, and its centre sits a little to one side of the straight line. However, the line still goes straight through it. The program also wants a margin of five centimetres, which means the path should stay at least that far from the pot, and not merely miss it.

Step two is a cost for smoothness. With the waypoints laid out, the next thing to write down is what makes a path smooth. The smoothness cost adds up, for every pair of neighbouring waypoints, the square of the distance between them.

The squaring matters here, because two gaps of one cost one plus one, which is two, while one gap of zero and one gap of two cost zero plus four, which is four. This means the cost is lowest when the waypoints are evenly spaced and in a straight line, and a kink or a sudden jump makes it rise fast.

For the straight first guess there are twenty gaps of half a unit each, so the smoothness cost is twenty times zero point two five, which is five. No path between these two ends can do better, because this is the shortest, most even path there is.

Step three is a cost for being near an obstacle. Smoothness on its own would keep the straight line, so a second cost has to push the path off the pot. The obstacle cost looks at each waypoint's distance to the surface of the pot, and that distance is positive outside the pot and negative inside it. The cost for one waypoint is zero when the waypoint is more than the margin away from the surface. It is small and gently rising as the waypoint comes inside the margin. Finally, it is large, and rising steadily, once the waypoint is inside the pot.

In numbers, with the distance to the surface and a five centimetre margin, if the distance is less than zero, the cost is the negative distance plus half the margin. If the distance is between zero and the margin, the cost is the square of the distance minus the margin, divided by twice the margin. Otherwise, the cost is zero.

This is the obstacle cost that CHOMP uses, and its two pieces meet smoothly at the surface, so the cost has no sudden step. For the straight first guess, seven waypoints are inside the pot or its margin, and their costs add up to five point three one six.

The program needs the distance from any point to the nearest obstacle surface, and for one round pot that is simple arithmetic. For a real scene, however, it comes from a distance field, which is a grid that stores, in every cell, the distance to the nearest occupied cell. The page on morphology and the distance transform shows how to compute one from a map of occupied cells.

Step four is moving every waypoint downhill. Because the previous steps gave two separate costs, the program has to add them into one number. The total cost is the smoothness cost plus the obstacle cost times a weight. That weight says how much a unit of obstacle cost counts against a unit of smoothness. The example uses a weight of ten.

Now the program has to find which way to move each waypoint so that the total goes down, and that direction is given by the gradient. The gradient of the cost at a waypoint is an arrow that points the way the cost rises fastest. So the program moves each waypoint a small distance the opposite way. This is called gradient descent, which means walking downhill on the cost, one small step at a time.

Each part of the cost gives its own arrow, and each of them has a plain meaning. The smoothness arrow points from the waypoint towards the middle of its two neighbours, so moving there straightens the path at that point. The obstacle arrow points straight away from the pot, and it is zero outside the margin.

A diagram here shows two arrows on one waypoint, representing a pull towards its neighbours and a push away from the pot. Specifically, it shows a waypoint after three steps. A green arrow pulls it towards a point halfway between its neighbours, while a red arrow pushes it away from the pot. Then a purple arrow is their sum, which is the step it actually takes.

The size of each step is the gradient times a small number called the step size, and the example uses zero point zero five. Too small, and the program needs thousands of steps. Too large, and waypoints jump past where they should be, so the path shakes instead of settling.

Step five is a worked example around a pot. With the cost and the gradient both in place, the program runs three hundred steps of gradient descent. A table shows the path at a few of those steps, tracking the smoothness cost, the obstacle cost, the total, the clearance, and the length of the path. The clearance is the smallest distance from the path to the pot's surface, checked all along the path and not only at the waypoints. This means a negative clearance shows that the path goes through the pot.

A diagram shows the straight guess going through the pot, and the smooth path bending round the side of the pot after three hundred steps. The straight guess is a dashed line, the paths after one, three and ten steps are pale lines, and the path after three hundred steps is a dark line bending round the side of the pot that the first guess was already nearer to.

Two phases are easy to see in the numbers, and they pull in opposite directions.

In the first few steps the obstacle term wins. So the waypoints inside the pot are pushed out hard, and the path leaves the pot after three steps. It gets longer and more bent as it goes, because the smoothness cost rises from five to eight point two five nine by step five. At that point the path has a sharp dent where it was pushed.

After that the smoothness term wins, because the obstacle cost is already close to zero, so the smoothness pull straightens the dent out. The path gets shorter again, from one hundred and eleven centimetres at step five to one hundred and five point one centimetres at step three hundred, and it spreads the bend over the whole move. After that the clearance keeps rising towards the five centimetre margin, and it ends at four point seven centimetres.

Another diagram shows the cost and the clearance at every step. The total cost falls steeply for three steps and then slowly, while the clearance crosses zero after three steps and creeps up towards the five centimetre line.

The final clearance is four point seven centimetres and not five, but that is not a mistake. The margin is part of a cost and not a hard rule, so the last few millimetres cost more in smoothness than they save in obstacle cost. If you need a hard guarantee, you either add a hard constraint, which is what TrajOpt does. Instead of that, you can check the final path and set the margin a little larger than what you really need.

The whole run takes a fraction of a second in plain Python.

Step six explains the same thing for a real arm. The example so far was flat, but a real arm works in the space of joint angles, as the planning a path page explains. So three things change.

First, each waypoint is a list of joint angles, for example six numbers for a six-joint arm, instead of an x y point. Second, the smoothness cost is the same sum of squared differences, now taken between neighbouring lists of joint angles. Finally, the obstacle cost is added up over many points on the arm's body, and not over a single point. The program places a few dozen small spheres along the links, and for each sphere it reads the distance field. Then it turns the sphere's obstacle arrow into joint-angle arrows with the arm's Jacobian. The Jacobian says how far a point on the arm moves when each joint turns a little, and the page on numerical inverse kinematics explains it with a small example.

Everything else, the weight, the step size and the loop itself, stays the same.

The pseudocode for this loop creates the waypoints evenly spaced on a straight line, then repeats the steps to move them. For each inner waypoint, it calculates a smoothness pull towards the middle of its two neighbours. It also calculates an obstacle push away from the surface, which only applies inside the margin. It combines these by adding the smoothness pull to the obstacle push multiplied by the weight, and scales it by the step size. It moves the waypoint downhill by that amount, and stops early if the total cost has stopped falling.

Crucially, the last step is to check the whole path for collisions, not only the waypoints. This matters because the cost only looks at waypoints, so a thin obstacle can sit between two of them. This means the final check must test the segments too.

The next section covers CHOMP, STOMP and TrajOpt. The previous section ran one particular optimiser, but three methods are well known, and all three are available to ROS 2 users. They all share the same core idea, which means they differ only in how they find the downhill direction, and in how they treat the rules the path must obey.

CHOMP stands for covariant Hamiltonian optimisation for motion planning. It is the method this page runs, and it uses the gradient of the cost. One extra idea gives it its name. Instead of moving each waypoint by its own arrow, CHOMP spreads each waypoint's step over its neighbours, so a push on one waypoint bends a long stretch of the path at once. In the hose example this is like pushing the hose with a flat board rather than with one finger. So the path stays smooth at every step, and fewer steps are needed.

STOMP stands for stochastic trajectory optimisation for motion planning. It does not use the gradient at all. At each step it makes a handful of noisy copies of the current path, each with small smooth random changes. Then it works out the cost of every copy. Then it moves the path towards a weighted average of the copies, with the cheaper copies weighted much more. Because it only ever asks what a path costs, STOMP works with costs that have no gradient, such as a cost that is simply one for a collision and zero otherwise, a cost that says whether a camera can see the gripper, or a cost from a simulator.

TrajOpt stands for trajectory optimisation. It treats the problem as a sequence of simpler problems. At each step it replaces the true cost with an approximation shaped like a bowl near the current path, and it solves that bowl exactly. Then it only accepts the move if the true cost really went down. Its main difference, however, is that it handles hard constraints, so rules such as keeping a clearance of at least two centimetres, keeping a joint within its limits, or keeping a cup level are kept exactly, and not just encouraged by a cost. It also checks collisions between waypoints, along the swept path of the arm, which removes the thin-obstacle problem.

A table compares the three methods. CHOMP finds the next step using the gradient of the cost, STOMP tries noisy copies, and TrajOpt solves a bowl-shaped approximation. Both CHOMP and TrajOpt need a cost with a gradient, while STOMP does not. Hard rules are only treated as extra costs in CHOMP and STOMP, but TrajOpt keeps them exactly. For collisions, CHOMP and STOMP check at waypoints, whereas TrajOpt checks along the swept path. Finally, the main computational cost for CHOMP is a distance field, for STOMP it is many cost evaluations per step, and for TrajOpt it is a more complex solver.

The next section explains where this is used on a robot arm. It lists the jobs a real arm calls these methods for.

First is smoothing a sampled path. A sampling planner such as RRT-Connect finds a route that works but zigzags, and the page on sampling-based planning shows why. That is why a common pattern is to hand that route to an optimiser as its first guess. The sampler chooses which side of each obstacle to pass, while the optimiser makes the path short and smooth. In other words, this pairs the strength of each method with the weakness of the other.

Second is a repeated move in a fixed cell. An arm that moves parts from a conveyor to a tray makes the same move thousands of times. So an optimiser started from the same guess gives the same path every time, which a random sampler cannot promise. That matters when the cell has to be checked and signed off.

Third is staying well clear, not just clear. Reaching past a glass on a table, a sampler's path may pass the glass by one millimetre. So the obstacle cost with a five centimetre margin keeps the arm away from it, which leaves room for the camera's error in where the glass is.

Fourth is adding a wish to the move. When the arm carries a cup of water, the cup should stay upright. In the same way, when it scans a shelf with a wrist camera, the camera should keep pointing at the shelf. Each wish becomes one more term in the cost, or one more constraint in TrajOpt, so the same optimiser handles it.

Fifth is reusing the last answer. When the scene changes a little between cycles, for example a box moved by two centimetres, the program starts from the path it used last time. Then only a few steps are needed, because the old path is already close. That is why GPU-based planners such as cuRobo use this to replan many times a second.

Finally, beyond collision. The same loop is used to plan a throw, to keep a welding torch at a fixed speed along a seam, or to spread effort evenly over the joints. Only the cost itself changes.

The next section covers where it works, and where it does not. This method is only ever as good as its first guess. It finds the best path near that guess, and such a path is called a local minimum. This means a path from which every small nudge makes the cost higher, even though a very different path would be cheaper.

The sharpest case is a pot centred exactly on the straight line, because then every push from the pot is exactly balanced by a push from the other side. The waypoints on the left of the pot are pushed left, and those on the right are pushed right. The middle waypoint sits at the pot's centre, where away from the pot has no direction at all, so it is not pushed anywhere.

A diagram shows this trap. After three hundred steps, the path still runs through the pot, with a negative clearance. However, if the same run is started with the middle waypoint moved up by only five millimetres, it goes round the pot and ends clear.

The nudge works fast, because after one step the middle waypoint is off the line, and after ten steps the path is clear of the pot. Real optimisers rarely meet a case this exact, but they meet others like it all the time. For example, a path may go the long way round, or be pushed into a corner between two obstacles. The usual cures are therefore to start from a sampler's path, or to start from several guesses and keep the best.

A table lists common failures and what people do about them. If the program is stuck in a local minimum, the cost stops falling while the obstacle cost is still above zero. The solution is to start from a sampler's path or several guesses. If there is a thin obstacle between waypoints, every waypoint might be clear, yet the arm clips a shelf edge. The solution is to use more waypoints and check the segments afterwards, as TrajOpt does. If the weight is too low, the path cuts through the edge of the margin or the obstacle, so you raise the weight or use a hard constraint. If the weight is too high, the path swings wide and has a sharp kink, so you lower the weight or take more steps. If the step size is too large, the cost goes up and down instead of falling, so you halve the step size. If there is a narrow gap, the path is pushed out of it and goes round, or fails. A sampler is better here, because it finds gaps by trying many points. If a cost has no gradient, the path does not move at all, which is when you use STOMP. Finally, if the distance field is stale, the path avoids where a box used to be, so you must recompute the field from the latest camera scan.

The next section lists libraries that provide trajectory optimisation. For a real project you use a library rather than writing this loop yourself.

MoveIt 2 provides the CHOMP and STOMP planner plugins for C++ and Python. This is the usual choice in ROS 2. Tesseract Planning provides the TrajOpt planner for C++, which is the maintained TrajOpt with hard constraints and swept collision checks. OMPL provides a path simplifier for C++ and Python. It is not an optimiser, but it is the cheap smoothing step MoveIt applies after a sampler. Drake provides kinematic trajectory optimisation for C++ and Python, which optimises a smooth curve through joint space with constraints. cuRobo provides motion generation in Python, running many optimisations in parallel on a graphics card. CasADi provides the Opti class for C++, Python, and MATLAB, where you write your own cost and constraints, making it good for special tasks. Finally, SciPy provides a minimize function in Python, which is enough for a small experiment.

For a first project, use what your planning framework already ships, which in ROS 2 is CHOMP or STOMP in MoveIt. So write your own only to learn, or when the cost is special enough that no library supports it.

The next section explains why to use trajectory optimisation, and what it costs. It answers four questions: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

It is a way to plan by improving a whole path at once, lowering one number that scores how long, jerky and close to obstacles the path is. It gives you a smooth path, with the clearance you asked for, and the same answer every time you ask the same question.

The obvious alternative is a sampling planner, such as RRT-Connect. A sampler is better at finding a way through a cluttered space, because it tries points all over the space instead of improving one guess. So it will find a narrow gap that an optimiser pushes the path away from. So why optimise at all? Because a sampler's path zigzags, differs every run, and passes obstacles by whatever distance it happened to find, whereas an optimiser gives the path a shape you chose, through the cost. In practice the two are used together more often than either is used alone.

Against all of that, the costs are these. You need a distance field of the scene, which takes memory and has to be recomputed when the scene changes. You also need to tune the weight and the step size, and the right values change with the task. You get no promise of finding a path when one exists. If the first guess is on the wrong side of an obstacle, the method reports a failure a sampler would have avoided. And a cost is not a rule. This means that unless you use hard constraints, as TrajOpt does, the path will trade a little clearance for a little smoothness.

The next section discusses the learned alternative. A learned collision distance gives the obstacle cost a smooth distance without a distance field, and a learned route planner gives a quick first guess, which is what this method depends on most. The exact check still tests the final path. A diffusion or flow policy replaces the optimiser instead. It learns whole stretches of motion from people's demonstrations, so it picks one real way round an obstacle rather than a blend of them. So it wins when the right motion is easier to show than to write as a cost, such as bringing the gripper round a mug's handle. The optimiser still wins when the path must be the same every run, must keep a clearance you chose, or must avoid an obstacle nobody showed the policy. This is because a diffusion policy varies by design and does not check for collisions.

The next section suggests where to read next. Numerical inverse kinematics uses the same idea, a cost made smaller step by step, to find the joint angles for one pose. Sampling-based planning finds the first guess that this method improves, and graph search does the same on a grid. The planning and search overview places this technique among the others in the chapter. Trajectory generation puts times on the finished path, so the motors know how fast to go. Morphology and the distance transform computes the distance field that the obstacle cost reads. Optimisation solvers covers the solvers that TrajOpt-style methods call. Finally, Book 3 goes deeper into planning a path, including what collision checking really checks.

The final section shows how to use it in Python. It builds the cost out of a smoothness term and an obstacle term, using SciPy for a small experiment. After it you will be able to bend a straight guess around an obstacle in about a dozen lines, and you will understand why the version you would actually ship is a MoveIt setting rather than a Python function.

The program is the pot example in two dimensions. The path is a list of waypoints, the two ends are fixed, and SciPy moves all the middle waypoints at once to make the cost smaller. SciPy works out the downhill direction itself by trying small changes, so you do not have to write the gradient.

The code defines the start, goal, and the pot's centre, radius, and margin. It creates a straight line guess of twenty waypoints. Then it defines a cost function that calculates the smoothness by summing the squared differences between steps, and calculates the clearance from the pot. It returns the smoothness plus the clearance penalty multiplied by a weight of fifty. Finally, it uses SciPy's minimize function to move the waypoints.

Run it and the cost falls from two point one two to zero point zero five seven five in one hundred and seventeen iterations, taking a fraction of a second. The straight guess ran through the middle of the pot, but the answer clears the pot by four point nine seven centimetres, and the path is one hundred and four point five centimetres long instead of one hundred. That extra four point five centimetres is what the clearance cost.

SciPy does the downhill search. It estimates the gradient, remembers the curvature it has seen, and chooses a step length, all of which the hand-written loop has to do by trial and error with a fixed step size. That is why this version converges in one hundred and seventeen iterations where the hand-written loop needed three hundred steps.

What you still have to write is the cost, and it is worth being clear that the cost is the entire method. The two terms are a complete statement of what you want: steps that are short and even, and waypoints that stay away from the pot. Change the weight of fifty and you change which of those two wins. Add a term and you add a requirement, such as keeping a cup upright or keeping a joint away from its limit. You also have to write the check at the end, because the cost only looks at waypoints, so a thin obstacle can sit between two of them and the final path must be tested segment by segment.

What you have to decide or measure are the weight, the margin and the number of waypoints. The margin of five centimetres is a distance in your own workcell, and the result shows why it is not a guarantee. The path ends at four point nine seven centimetres and not five, because the margin is part of a cost rather than a rule, so you set it a little larger than what you really need. The weight of fifty has no natural value, because it converts metres of clearance into units of smoothness, so you choose it by running the optimisation and looking at whether the path is too bent or too close. The twenty waypoints decide how finely the path can bend and how long the solve takes, and too few means a smooth curve cannot be represented at all. Finally, for a real ROS 2 arm you do not write this. You select CHOMP or STOMP in MoveIt's planning pipeline configuration, which runs the same idea on the arm's real joint space with its real collision checker, and you configure the weights in a file instead of in Python.
