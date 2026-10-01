Decisions and task logic. This chapter is about the part of a robot program that decides what the robot does next, and in what order. The other chapters of this book find the mug, plan a path to it and move the joints. Because those chapters do the work of each step, this chapter answers the questions that sit above them. Which step comes now, what happens when a step fails, and which mug goes first?

This page is the overview of the chapter. It says what the four techniques in it are for, gives each one in a line, and compares them. After that, it shows how they connect to the rest of the book and to learned models. This page is for a reader who already knows what an arm, a camera and a gripper are, but who has not met these techniques before.

The first section explains what this family of techniques is for. In the list of categories that this book is built from, it is the seventh one, which is decisions and task logic. That means deciding what the robot does next, and in what order.

A real task is never one motion, because picking up a mug and putting it in a bin takes at least eight steps. First, the camera looks for the mug, and then the arm moves above it. Then the gripper opens, lowers and closes, and a check makes sure the mug is really in the gripper. After that, the arm lifts, carries the mug to the bin and lets go, and finally it goes home and looks for the next mug.

Any of those steps can fail, and each one fails in its own way. For example, the gripper can close on nothing because the mug moved a little, or the planner can find no path because a box is in the way. The mug can also slip out on the way to the bin. This is why most of the code in a working robot is not the steps themselves. It is the code that decides what to do when a step fails.

The techniques in this chapter are the standard ways to write that code, so that it stays correct and readable as the task grows. They are all programmed rules, and none of them is trained from data. This means they need no training data at all, and it means the same technique works in every programming language.

The next part of the page covers the question this logic answers for an arm. So far, the task has been one sequence of steps that can fail. But a chapter on decisions has to answer two kinds of question, and although the two sound alike, they need different tools.

The first kind is "what now?", and here the robot must react to events as they happen, such as the grasp working, the grasp failing, or a person pressing stop. Because the answer changes from one moment to the next, the robot has to keep asking the question. A finite state machine and a behaviour tree both answer this kind, so they run the whole time the robot works and check many times a second.

The second kind is "which ones, and in what order?", and here the robot has a list of choices and wants the best set or the best order out of them. For example, which camera views see every mug, and which mug should go in which slot of a tray? Since these questions are asked once, before the work starts, or once per batch, greedy algorithms and optimisation solvers answer them instead.

The page shows a diagram with five mugs and a tray, putting all four questions on one table so the two kinds can be seen side by side. In it, a red mug is the one whose grasp just failed, so a state machine or a behaviour tree decides to try again. Blue circles show four camera views that a greedy rule chose, out of six, so that every mug is seen. While those views are chosen once, purple lines do a different job. They pair each mug with a tray slot so that the total distance is the shortest of all one hundred and twenty pairings, which the script found by trying every one.

The next section introduces the four techniques. Each one has its own page, and they split into the two kinds of question just mentioned. While the first two react to events as they happen, the last two choose the best set or the best order.

First, finite state machines describe the task as a small set of named situations, such as "grasp" or "carry". These are joined by arrows that say which event moves the robot from one situation to the next.

Second, behaviour trees describe the task as a tree of steps and checks. The tree is re-checked many times a second, and each part answers "success", "failure" or "still running", so retries and fallbacks are part of its shape rather than extra code.

Third, greedy algorithms and set cover build an answer one choice at a time, always taking the choice that looks best right now. A common use is choosing the fewest camera views that together see every object.

Finally, optimisation solvers search for the best answer to a problem written as numbers, a goal and rules. They order picks, assign objects to places and pack boxes, using libraries such as Google's OR-Tools.

The pages of this chapter are in two groups, and the group a page is in tells you how likely you are to need it. The first group, most used, holds finite state machines and behaviour trees. Nearly every arm program has one of the two, because every task has steps, retries and failures to handle. The second group, also used, holds greedy algorithms and set cover, and optimisation solvers. You need them only when a task has many choices to put in order, such as which views to take or which part goes in which pocket, and many arm programs never have that problem.

The next part of the page compares how the four techniques work. It provides a table setting them side by side, showing the question each answers, how often it runs, what goes in, and what comes out.

The first two techniques are about control flow, because they decide which step runs. A finite state machine answers "What do I do now, given what just happened?". It runs all the time, on every event. It takes in the current state and the latest event, and outputs the next state and the action it starts. A behaviour tree answers "What do I do now, and what if it fails?". It runs all the time, often ten to a hundred times a second. It takes in the world as the checks see it, and outputs the step to run now, along with a status of success, failure or running.

The last two techniques are about choice, because they decide what those steps work on. A greedy algorithm answers "Which small set of choices covers everything?". It runs once per task or batch. It takes in a list of choices and what each one covers, and outputs a set of choices, usually close to the smallest. An optimisation solver answers "What is the best order or assignment?". It also runs once per task or batch. It takes in numbers, a goal and rules, and outputs the best answer it can prove, or the best it found in time.

Because the first two decide which step runs and the last two decide what those steps work on, a real robot program uses both kinds together. A behaviour tree runs the task, and one of its steps calls a greedy rule or a solver.

The next section explains when each one runs. The difference in timing is easiest to see on a single real run. The page shows a timeline of one run from a state machine that moves two mugs to a bin, where the first grasp closes on nothing. The diagram shows that the task logic is busy all the time, while the two choosers run once at the start. A coloured bar represents the state that the task logic was in at each moment, with small ticks showing that this state is checked every tenth of a second. Below that, two diamonds represent single calls made once at the start, where one chooses the camera views and the other pairs mugs with tray slots.

This timing decides how fast each technique has to be. Because task logic runs thousands of times in one task, each check must take well under a millisecond. A chooser, however, runs only once, so it can take a few hundred milliseconds, or even seconds, if that buys a better answer.

The next part of the page explains how this chapter connects to the others. Because task logic decides which step runs rather than doing the work of the step itself, the techniques here sit on top of every other chapter of this book. This means each step in a state machine or a behaviour tree calls something from one of those chapters.

First, the "detect mug" step uses the image and point cloud processing chapter to cut the mug out of the picture, and the geometry and cameras chapter to turn its pixels into a position. Second, the "is it the same mug as before?" check uses the searching and matching chapter. Third, the "move above mug" step calls the planning and search chapter to find a path, and the control and motion chapter to follow it. Finally, a "holding mug?" check often reads a steady gripper width or force from the fitting and estimation chapter.

Learned models meet this chapter in two places as well. First, a learned model can be one step inside the tree, in the place where a programmed step would otherwise sit. An object detection model can be the "detect mug" step, and a collision and failure detection model can be the "did the grasp fail?" check. While those models replace a step, the tree around them stays the same.

Second, a language model can sit above the tree instead of inside it. A language model can act as a planner that turns a spoken request into a list of steps. Even then, those steps usually run inside a state machine or a behaviour tree, because that part must be fast and must always do the same thing.

The map of the whole book, which shows where this chapter sits among the others, is on the map of techniques page.

The section on where to read next suggests starting with finite state machines, because they are the simplest way to write task logic and the next page builds on them. Then read behaviour trees, which most robot arm programs use today for the same job. Greedy algorithms and set cover, and optimisation solvers, cover the "which ones, and in what order" questions, which come up once a task has many choices in it. The book also shows behaviour trees in real code in the section on putting a task in order, and compares state machines and behaviour trees in the section on scripted logic.

The final section shows how to use this in Python. Earlier, the page said that a real program uses both kinds of technique together, so that the task logic runs the job while one of its steps calls a chooser. It also showed the difference in timing between the two. This section puts that sentence into Python. After hearing it, you will have seen a solver called once and a behaviour tree ticked many times, in the same file, and you will know which of those lines a library wrote for you.

The example empties a table of three mugs into three tray slots. It uses the SciPy library to choose which mug goes in which slot, and a library called py trees to carry the answer out.

The code first sets up a cost matrix for the travel distance in metres between each mug and each slot. It then calls a linear sum assignment solver from SciPy. This chooser runs once to pair the mugs with the slots so the total travel is smallest.

After that, the code defines a behaviour tree step to place a mug. This task logic runs many times a second and works through the plan. On every tick while the step is active, it checks if the grasp failed, returning a failure status if so. If the mug is placed, it returns success. Otherwise, it returns a running status.

The code builds a sequence of these steps for all the planned pairs, and then enters a loop that ticks the tree and sleeps until the next tick, continuing until the whole sequence succeeds.

For the costs in the example, the solver pairs mug zero with slot zero, mug one with slot one, and mug two with slot two, for a total of zero point eight five metres. The two halves of the file run at completely different rates, which is the point made earlier about timing. The solver is called once and returns in well under a millisecond here, while the tree tick runs perhaps ten to a hundred times a second for as long as the task lasts.

What the libraries do for you is narrow and worth naming. SciPy's solver finds the best pairing exactly, not approximately, so you do not write a search. The py trees library gives you the tick, the three answers, and the composite nodes that combine them, so you do not write the engine that decides which step is active.

What you still write is the work itself. The functions to check if a grasp failed, check if a mug is placed, and sleep until the next tick are your functions, and so is every leaf of the tree, because a behaviour tree library has no idea what a mug is. Building the cost matrix is yours too, and that is usually the harder half of using a solver, because the numbers have to come from somewhere real.

What you have to decide or measure is the cost numbers and the tick rate. A cost of zero point three two metres is a claim about your cell, and if you guess it the solver will confidently return the best answer to the wrong question. The tick rate has to be fast enough that the tree notices a failure before it matters and slow enough that the checks inside it finish, which means well under a millisecond of work per tick. Whether the plan is recomputed after every mug is your decision as well, because a mug that slipped may have changed the costs.
