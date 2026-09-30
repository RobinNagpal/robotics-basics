Numerical inverse kinematics.

This page explains how a program finds the joint angles that put a gripper at a chosen place, when there is no neat formula to do it. It does that with a guess-and-correct loop, so the page answers five questions about it. How does the guess-and-correct loop work? What is the Jacobian, and why does the loop need it? Why does the plain loop go wild when the arm is nearly straight? How does damped least squares, the method most solvers use, fix that? And what happens when the target cannot be reached at all?

It is for a reader who has read the inverse kinematics page in Book one. That page solves the same small arm with a triangle formula, and then introduces the guess-and-correct loop. This page picks up where that one stops. So it uses the same arm, the same target, and the same first guess, and you can compare the numbers directly.

The arm has two links lying flat, and link one is three metres while link two is two metres. The target is at an x of 2.598 and a y of 3.5, which is where the gripper sits when joint one is at thirty degrees and joint two is at sixty degrees.

The first section gives the idea in one sentence. Guess the joint angles, see how far the gripper misses the target, work out which small turn of each joint shrinks that miss, make the turn, and repeat until the miss is tiny.

Here is an everyday example of that loop. Think of parking a car close to a kerb with the help of a mirror. You do not work out the steering angle in advance. Instead you look in the mirror, see that you are forty centimetres out, turn the wheel a little, roll back, and look again. Each look tells you the miss, and you know from experience which way to turn the wheel to shrink it. In other words, you keep going until you are close enough.

A program does the same thing, and forward kinematics is its mirror, because forward kinematics says where the gripper is for any set of joint angles. The Jacobian is its experience, because the Jacobian says which way the gripper moves when each joint turns. Inverse kinematics is often shortened to I K, and this page uses that short form from here on.

The next part explains how it works. The previous section gave the whole loop in one sentence, so the steps below take it apart, in the order the program runs them.

Step one is to measure the miss. The program starts from a guess for the joint angles, and on a real robot that guess is usually the arm's current angles. Here it is zero degrees for joint one and thirty degrees for joint two, which is the same guess Book one uses.

It runs forward kinematics on the guess to find where the gripper is, and then it subtracts that position from the target. The result is the miss, which is an arrow from the gripper to the target, with an x part and a y part. Its length is how far off the gripper is, and for the first guess that length is 3.287 metres.

Step two introduces the Jacobian. Step one measured the miss, so the next question is which joint turn will shrink it, and the Jacobian is what answers that. It is a small table with one column per joint. Each column says how far the gripper moves, in x and in y, when that joint turns by one radian. It only holds for small turns, and it changes as the arm moves, so the program works it out again at every step.

Book one finds each column by turning one joint a millionth of a radian and seeing where the gripper goes. However, for this arm there is also a short formula. At thirty degrees and sixty degrees, the table has two columns. The first column shows that turning joint one by a small amount moves the gripper minus 3.5 times that amount in x, and 2.598 times that amount in y. The second column shows that turning joint two moves the gripper minus 2.0 in x, and zero in y.

Joint one swings the whole arm, so the gripper moves at right angles to the line from the base. Joint two, however, only swings the last link, so the gripper moves at right angles to that link.

The page has a diagram showing the two columns of the Jacobian drawn as arrows at the gripper, for a bent arm and a nearly straight one. On the left, with the elbow at sixty degrees, the two arrows point in clearly different directions, so together they can move the gripper any way. But on the right, with the elbow at five degrees, both arrows point almost the same way, and neither moves the gripper along the arm.

Step three is turning the Jacobian round. The Jacobian from step two answers one question, which is, if I turn the joints this much, where does the gripper go? However, I K needs the opposite question, which is how much I should turn the joints to move the gripper along the miss. So the program solves an equation where the Jacobian times the joint step equals the miss.

With two joints and two numbers in the miss, this is two equations with two unknowns, so it has one answer as long as the columns point different ways. Book one does this with the pseudo-inverse, which also works when the table is not square, and the page on NumPy explains it.

One number tells you how easy the table is to turn round, and that number is its determinant. For this arm it is six times the sine of joint two, as the arm movement overview shows, and at thirty degrees and sixty degrees it is 5.196. It falls to zero when the elbow is straight or folded back. That pose is a singularity, which is a pose where the arm cannot move its gripper in some direction, however fast the joints turn.

Step four explains why the plain answer goes wild near a straight arm. Step three named the singularity, but the trouble starts well before the arm reaches one. As the elbow straightens, both columns of the Jacobian point almost the same way, as the earlier picture showed. This means neither of them moves the gripper along the arm, towards or away from the base. Asked to move that way, the plain answer therefore asks for a huge turn.

The program tests this directly. So it puts joint one at zero degrees and asks each method for the step that moves the gripper ten centimetres towards the base, for smaller and smaller elbow angles.

A diagram shows three curves for the joint step each method asks for as the arm straightens. The curve for the plain inverse grows as the elbow straightens, rising to 29.4 degrees at an elbow of ten degrees and to over two thousand nine hundred degrees at 0.1 degrees, while the two damped curves shrink.

A table gives some of these numbers, showing the elbow angle and the size of the joint step in degrees. At a thirty degree elbow, the plain inverse asks for 9.6 degrees, and the damped methods ask for smaller amounts like 5.5 or 2.4 degrees. But at an elbow of 0.1 degrees, the plain inverse asks for 2946.4 degrees, while the damped methods ask for less than a tenth of a degree.

To pull the gripper in by ten centimetres from a nearly straight arm, the true answer bends the elbow to 23.44 degrees. But the plain inverse asks for eight full turns of the joints in one step. Book one avoids this by capping every step at thirty degrees per joint. A cap does work, but it is a blunt tool. This is because it cuts the step to the same size whether the arm is near a singularity or far from it.

Step five introduces damped least squares. Because a cap is so blunt, damped least squares asks a slightly different question. Instead of asking which step removes the whole miss, it asks which step makes the squared miss left over, plus a penalty for the size of the step, as small as possible. The penalty is the squared step size multiplied by the square of a number called lambda.

The first part of that sum wants the miss gone, while the second part charges a price for every bit of joint turn. The number lambda is the damping, and it sets that price. Here it is measured in metres, because the miss is in metres.

When the arm is well bent, a small turn removes a lot of miss. This means the price hardly matters, and the step is close to the plain answer. When the arm is nearly straight, removing the miss along the arm would need a huge turn. So the price wins, and the step stays small. The method gives up, for now, on the direction the arm cannot move in, and moves in the directions it can.

The answer to that question has a short formula. The joint step equals the transposed Jacobian, multiplied by the inverse of a sum, and then multiplied by the miss. That sum is the Jacobian times the transposed Jacobian, plus the squared damping times the identity matrix.

With lambda at zero this is the plain answer again. But with a large lambda it becomes a small step along the transposed Jacobian times the miss, which is plain gradient descent on the squared miss, called the Jacobian transpose method. Damped least squares therefore sits between those two. The same idea, a least-squares fit with a price on large answers, appears in the page on least-squares fitting. The name Levenberg-Marquardt is used when the program also changes lambda as it goes, which step seven shows.

Step six is a worked run. It shows damped least squares with lambda at 1.0, run from the guess of zero and thirty degrees, and this time the program has no step cap at all.

The miss starts at 3.287 metres. After one step, the miss drops to 0.727 metres. By step five, it is down to 0.014 metres, and by step seventeen, the miss is just one micrometre, with the joints exactly at the target of thirty and sixty degrees.

A diagram shows the arm at every step of this run. The palest arm is the first guess, each darker arm is one step later, and purple dots trace the gripper. The first two steps do most of the work.

It finds the elbow-down answer in seventeen steps. From a different guess it would find the elbow-up answer instead, as Book one shows, because the loop always finds the answer nearest its guess.

For comparison, the page shows the plain pseudo-inverse from the same guess, with no step cap. Its first step folds the elbow to 175 degrees, almost flat against link one, so the miss gets bigger, jumping to over four metres. But it recovers, and it finishes sooner, in seven steps. Near the answer the plain method is the fastest there is, because it removes the whole miss at every step. So damped least squares gives up some of that speed in order to keep every step safe.

Another diagram shows the miss at every step for three methods, on a reachable target and on one out of reach. On the left, the pseudo-inverse and damped least squares both reach a miss below a micrometre, while the Jacobian transpose is still 3.2 centimetres off after forty steps. On the right, the target is out of reach, the damped method settles at the best pose, and the pseudo-inverse jumps about.

Step seven covers a target out of reach, and choosing the damping. The target at an x of 6 and a y of 0 is six metres from the base while the arm is only five metres long, so no answer exists at all. The best the arm can do is point straight at it, with a miss of one metre.

From a guess of ten and twenty degrees, damped least squares with lambda at 1.0 gets there in a few steps and stays there. The arm is straight, and the miss is exactly one metre. The plain pseudo-inverse, however, never settles, because after one hundred steps its miss is over seven metres and its joint angles have wound up to hundreds of degrees.

The right damping is therefore a trade, and a table shows what five values do. It lists the damping lambda, the steps to reach the easy target, and what happens when the target is out of reach. With a small damping of 0.05, it takes seven steps for the easy target, but for the out of reach target it jumps about with a miss near seven metres. With a large damping of 2.0, it takes forty-four steps for the easy target, and settles straight with a one metre miss for the out of reach target.

So small damping is fast when the target is easy and wild when it is not, while large damping is safe and slow. The row for a damping of 0.5 is worth a second look, because it swaps every step between two poses with the same miss. A program that only checks whether the miss is small would see a steady 1.175 metres. This means it would not notice that the arm is being told to swing back and forth.

The usual answer is to change the damping as the loop runs, which is the Levenberg-Marquardt method. After a step that makes the miss smaller, the program keeps the step and halves lambda. But after a step that makes the miss larger, it throws the step away, doubles lambda and tries again. Starting from a lambda of 1.0, it reaches the easy target in five kept steps, and settles on the straight pose for the out-of-reach target in nine.

The nearly-straight case shows the difference most clearly. So start the arm almost straight, and ask for a point ten centimetres towards the base. The plain pseudo-inverse gets there in sixteen steps, but one step turns a joint by over eight thousand degrees, so a real joint with limits would have hit them on the first step. Damped least squares with lambda at 1.0 never turns a joint more than 0.9 degrees in one step, but it needs 119 steps, because near the singularity it moves very cautiously. With lambda at 0.5 it needs 36 steps, and no step is over 3.0 degrees. Levenberg-Marquardt needs only eight kept steps.

Step eight is about having more joints than the task needs. Now add a third link, one metre long, and ask only for the gripper's position and not for its angle. Then three joints meet two numbers, so the arm is redundant, which means it has endless answers, as Book one explains. The Jacobian is now two rows by three columns, and the same formula still works, because the Jacobian times its transpose is still a two by two table.

Damped least squares with lambda at 0.5 reaches the point from two different starting guesses, but chooses very different poses and gripper angles. This is because the loop does not pick the best answer, since it picks one near the guess, with small joint turns. So when the gripper angle matters, you must add it to the miss as a third number, and then the arm is no longer redundant.

A real six-joint arm works the same way, only with bigger tables. Its miss has six numbers, three for position and three for rotation, and its Jacobian has six rows and one column per joint. The page on rigid transforms explains how a rotation miss is written as three numbers.

The final part of this section is the pseudocode. It shows the full loop, with Levenberg-Marquardt damping and joint limits. The code takes a target, a guess, an initial damping, a tolerance, and limits for steps and time. It starts by measuring the miss. Then it enters a loop that repeats until the miss is smaller than the tolerance, or it runs out of steps or time. Inside the loop, it calculates the Jacobian, works out the step using the damped least squares formula, and adds the step to the current joints, clamping them to the joint limits. It then measures the new miss. If the new miss is smaller, it accepts the new joints, updates the miss, and halves the damping because things are going well. If the new miss is larger, it rejects the step and doubles the damping to be more careful, stopping entirely if the damping gets too large. Finally, it returns the joints if it succeeded, or a failure message along with the best joints and the final miss if it did not.

Two things in the last lines matter. First, the loop must say when it failed and how far off it was. Second, not found is not the same as no answer exists, which a later section comes back to.

The next section describes where this is used on a robot arm. Section two built the loop up step by step, so this section lists the jobs a real arm calls it for.

First, turning a grasp into joint angles. A grasp model or a detector gives a gripper pose in the camera frame. Then the program moves that pose into the arm's frame and calls I K. The result is the goal a planner then plans to, and this is the most common I K call in a pick-and-place program.

Second, checking many grasps before moving. A grasp model may offer fifty candidate grasps. So the program runs I K on each one, throws away the ones with no answer, and scores the rest by how far the answer is from joint limits and from a singularity. Book three describes this check in the page on reaching and reachability.

Third, straight-line moves. To move the gripper straight down onto a part, the program splits the line into small steps and calls I K at each one, seeded with the answer from the step before. This is how MoveIt's Cartesian path function works. However, near a singularity the I K step fails, and the line stops short, as the page on planning a path warns.

Fourth, jogging and following. An operator may jog the gripper with a joystick, or the arm may follow a moving target seen by the wrist camera. In either case the program runs one step of this loop every control cycle, for example five hundred times a second. The miss is replaced by the wanted gripper velocity, and damped least squares keeps the joints from spinning up when the arm passes near a singularity. In ROS 2, MoveIt Servo does this job, and it slows the motion down as the arm nears a singularity.

Fifth, pointing a camera. To look at a point on the table with a wrist camera, the miss is how far the camera's centre line is from the point. That is only two numbers, so a six-joint arm has spare joints, and the loop picks a pose near the current one.

Sixth, finishing a learned guess. A learned I K model gives an answer that is close but not exact. So the numerical loop, seeded with that answer, finishes the job in a step or two. Book six describes this in the page on learned motion planners.

Finally, inside other planners. Trajectory optimisation turns an obstacle push on a point of the arm into joint turns with the same Jacobian, as the page on trajectory optimisation explains.

The next section covers where it works, and where it does not. Section three listed the jobs this loop does well, so this section lists the ways it fails, what causes them, the signs you see, and what people do about them.

If the arm is near a singularity with no damping, a joint might jump hundreds of degrees in one step, or the arm lurches. People fix this with damped least squares or Levenberg-Marquardt.

If the target is out of reach, the loop uses all its steps and the miss stays the same. The fix is to check reach first, and report the final miss, not just that it failed.

If the damping is too low for a hard target, the miss jumps up and down, or two poses swap every step. You should raise the damping, or change it as you go.

If the damping is too high, it takes many steps, and the solver times out on targets it should reach. You should lower the damping, or change it as you go.

If a joint limit is in the way, the answer is clamped at a limit and the miss stops shrinking. The fix is to restart from other guesses.

If the guess is on the wrong side, an answer is found, but with the elbow or wrist the other way. You can seed with the current angles, or try several seeds and pick the nearest.

If a time limit is too short, it might say no solution for a pose that does have one. You should raise the limit when surveying, or try several seeds.

Finally, if only one answer is returned, the planner might fail later because that pose leads nowhere. People use an analytic solver, or several seeds, to list the choices.

The time limit row deserves a sentence of its own, because MoveIt's default solver, K D L, stops after 0.05 seconds. As the reaching and reachability page explains, unreachable from such a solver means only that it was not found in fifty milliseconds from these guesses. That is why TRAC-I K runs two solvers at once and takes whichever answers first, and why many programs try several random guesses.

The next section lists libraries that provide it. Because the failures above are well known, the libraries have already dealt with them.

K D L, or the Orocos Kinematics and Dynamics Library, is used in C++ and Python, and provides solvers for Newton steps, Levenberg-Marquardt, pseudo-inverse and weighted damped least squares. MoveIt 2 uses K D L as its default I K plugin.

TRAC-I K is a C++ library that runs a Newton solver and an optimisation solver together, acting as a drop-in MoveIt plugin.

Pick I K is a C++ MoveIt plugin that serves as the maintained modern alternative inside MoveIt.

Pinocchio, for C++ and Python, gives you the pieces to write the damped loop yourself.

Drake treats I K as an optimisation, with extra constraints such as collision distance.

The Robotics Toolbox for Python provides a Levenberg-Marquardt solver that is good for learning and teaching.

I K Py is a small Python library that reads a URDF and is easy to try.

CuRobo for Python solves thousands of I K problems at once on an NVIDIA graphics card.

Finally, NumPy and Eigen provide enough matrix maths to write the loop yourself.

For a ROS 2 arm, start with the solver MoveIt already uses, and switch to TRAC-I K or pick I K if it fails on poses you know are reachable. Write your own loop only when you need it inside a control cycle, or when the miss is not a pose at all, as in the camera-pointing example.

The next section explains why numerical inverse kinematics is used, and what it costs. With the libraries named, this section answers four questions: what it is, what it does for you, why use it rather than the obvious alternative, and what it costs.

It is a loop that finds joint angles for a target by repeatedly measuring the miss and correcting it with the Jacobian. Damped least squares is the version that stays calm near singularities and when the target is out of reach. It gives you joint angles for any arm that has forward kinematics, whatever its shape, and for any kind of target you can write as a miss.

The obvious alternative is an analytic solver, which is a formula worked out for one arm design, like the triangle formula in Book one. Tools such as I K Fast generate such formulas automatically for many six-joint arms. A formula is faster, it lists every answer, and it says for certain when there is none. Book one measured it at about 332 times faster on this arm. So why use a loop? Because many arms have no formula. This includes arms with seven joints, arms whose wrist axes do not meet at one point, and any arm whose task is not a plain pose. The loop needs only forward kinematics, so the same code serves every arm.

Against all of that, the costs are these. The loop finds one answer, the one nearest its guess, and it does not tell you that others exist. This means it needs a sensible guess to start from. It is slower than a formula, and its time is not fixed, because easy targets take a few steps while hard ones may run out of time. It cannot tell that no answer exists from not found yet. It also has settings, the damping and the time limit, whose right values depend on the arm and the task. In short, damped least squares removes the worst failure, which is the wild jump near a singularity, at the price of slower progress near one.

The next section covers the learned alternative. Section six weighed this loop against an analytic formula, but there is a third option as well. A learned I K solver, described in Book six's page on learned motion planners, is a network trained on many pairs of joint angles and the gripper poses forward kinematics gives for them. It answers in one pass, and some, such as I K Flow, give many different answers at once, which helps when a seven-joint arm needs a choice of poses. But its answer is close, not exact, so it is used as the starting guess for this loop, which finishes the job in a step or two, as section three showed. For one target at a time, the loop alone is still the usual choice, because it is exact, needs no training, and works on a new arm without retraining. A learned arm model does a different job. It learns the small bends and gear play that make the real tool miss the pose that forward kinematics predicts.

The final section suggests where to read next. The page on trajectory optimisation uses the same step-by-step lowering of a cost, but for a whole path instead of one pose. The planning and search overview places this technique among the others in the chapter. The page on least-squares fitting explains the least-squares idea that damped least squares is built on. The page on rigid transforms explains the poses and rotations that a full six-number miss is made from. P I D control is what turns the joint angles this page finds into motor commands. Book one has the formula method and the first version of this loop in its inverse kinematics page. Finally, Book three covers singularities in the page on reaching and reachability, and the libraries in the tools and libraries page.
