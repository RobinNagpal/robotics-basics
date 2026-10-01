The topic is behaviour trees. This explains the behaviour tree, which is the most common way to write the task logic of a robot arm today. It answers five questions: what is a behaviour tree, how does it decide what to run tick by tick, where does a robot arm use one, when does it go wrong, and which libraries give you one ready-made. 

This follows on from the page about finite state machines, which explains states, events, retries, and the pick-and-place task. Here, the same task is written as a tree, so the two can be compared directly.

The first section is the introduction. The state machine works well for eight states, but real tasks grow. A customer might ask for a second way to grasp, a check that the bin is not full, and a stop when a person comes near. Each of those adds arrows to several states, so soon nobody can change the drawing safely. 

A behaviour tree solves this by changing the shape of the description. Instead of listing situations and the arrows between them, it lists steps and groups them with a small number of rules, such as doing them in order, or trying them until one works. This means a retry or a recovery is then one new branch in one place, and the rest of the tree does not change. 

Behaviour trees came from video games, where they control the characters. Robotics took them up because of this one property: they stay readable as the task grows. Because of this, most robot arm programs written with ROS 2 today use a behaviour tree for the top layer.

The next part gives the idea in one sentence. A behaviour tree is a tree of steps and checks that is re-checked many times a second, where each node answers "success", "failure", or "still running", and each parent node combines its children's answers by a fixed rule. 

An everyday example of this shape is making a cup of tea. You do these steps in order: boil the water, put tea in the cup, pour the water, and wait. Then, to put tea in the cup, you try these options until one works: use a tea bag, or use loose tea with a strainer. If there are no tea bags, you do not start over, because you just try the next way. And if neither way works, the whole task fails, and you know exactly which step stopped it. Those two phrases, "in order" and "try until one works", are the two main rules of a behaviour tree, and everything else is built from them.

The next section explains how it works, step by step, starting with ticks and the three answers. Unlike a state machine, a behaviour tree does not run once from top to bottom. Instead, a loop ticks the tree many times a second, often ten to a hundred times. A tick is one visit that starts at the top node, called the root, and passes down to the children. 

Every node that is ticked gives back one of three answers. First, success, meaning the step is done and it worked. Second, failure, meaning the step is done and it did not work. And third, running, meaning the step has started but is not finished yet. The third answer is what makes behaviour trees fit robots, because a move takes two seconds. So, a node that moves the arm above a mug answers "running" on every tick until the arm arrives, and then it answers "success". Meanwhile, the loop stays free, so other checks in the tree can still run on each tick.

Given those three answers, a tree is built from a small set of node kinds. First is an action, which does something in the world, such as moving above a mug or opening a gripper. It may take many ticks, so it can answer "running". Second is a condition, which is a yes-or-no check, such as asking if the robot is holding a mug. It answers at once, with "success" for yes or "failure" for no, so it never answers "running". 

Third is a Sequence, which runs its children from left to right. It moves to the next child when the current one succeeds, and it stops and fails as soon as one child fails. So, it succeeds only when every child has succeeded. Fourth is a Fallback, which tries its children from left to right. It moves to the next child when the current one fails, and it stops and succeeds as soon as one child succeeds. So, it fails only when every child has failed. Some libraries call a Fallback a Selector instead. 

Fifth is a decorator, which has one child and changes that child's answer. For example, a Retry decorator starts its child again after a failure, up to a set number of times. An Inverter swaps success and failure, and a Timeout fails its child if it runs too long. Finally, a Parallel node ticks all of its children on every tick, and it succeeds once enough of them have succeeded. 

Actions and conditions are the leaves, meaning the nodes at the bottom with no children. You write the leaves yourself, because they call the rest of your robot program, like the detector, the planner, or the gripper driver. But the Sequence, Fallback, decorator, and Parallel nodes come ready-made in every library.

Because those node kinds are easier to see on a real task, the page shows a diagram of the running example as a behaviour tree, doing the same job as the state machine on the previous page. The tree is read from the top down, and the leaves run in a specific order when everything works. 

The root of the tree is a Fallback node called "task". It first tries a "pick and place" branch. If that fails, it runs an "ask for help" branch. This one node replaces the three separate "ask for help" arrows from the state machine. The "pick and place" branch is a Sequence of four children: make sure the mug is located, grasp it with retries, move to the bin, and release. 

The "mug located" step is a Fallback. If the mug's position is already known, the condition succeeds and nothing else runs. If not, a "detect mug" action runs. The grasp step is a Sequence wrapped in a decorator that retries up to three times. The Sequence opens the gripper, moves above the mug, lowers and closes, and then checks if it is holding the mug. If the check fails, the whole Sequence fails, and the Retry starts it again from opening the gripper. Notice that there is no retry counter anywhere in the task code, because the Retry node keeps it instead. That is the extra number which the state machine had to carry by hand.

Since Sequence and Fallback do most of the work, their rules are easiest to see on small cases. The page illustrates three examples of a parent combining its children's answers. In the first case, a Sequence's second child fails, so the Sequence fails too and never ticks the third child. In the second case, a Sequence's second child is still running, so the Sequence answers "running" and will tick that child again next time. In the third case, a Fallback's first child fails, so it tries the second child. The second child works, so the Fallback succeeds without ticking the third child. 

The two rules mirror each other. A Sequence goes on after success and stops at failure, while a Fallback goes on after failure and stops at success. However, both of them pass "running" straight up to their own parent.

To show how this runs in practice, the page includes a diagram of a small behaviour tree engine ticking the pick-and-place tree ten times a second. The diagram shows every node's answer on every tick of one run. It looks like a grid where each row is a node, indented under its parent, and each column is one tick. A grey cell means the node was not ticked at all on that tick. 

In this run, each action takes a fixed number of ticks, ranging from two ticks to open the gripper, up to twenty ticks to move to the bin. The check to see if the mug is held fails on the first try and succeeds on the second. Here is what happens. 

On tick one, the check for whether the mug pose is known fails, because no picture has been taken yet. So the "mug located" Fallback ticks "detect mug", which answers "running". On tick four, "detect mug" succeeds. In the same tick, the "pick and place" Sequence moves on to its second child, and "open gripper" starts. A Sequence moves to its next child as soon as one succeeds; it does not wait for the next tick. 

Ticks five to twenty-six run the first grasp, moving above the mug and then lowering and closing. On tick twenty-six, the check for holding the mug fails. The grasp Sequence fails. The Retry node counts one failure and answers "running", so nothing above it notices. Ticks twenty-seven to forty-nine run the second grasp. On tick forty-nine, the check for holding the mug succeeds. The Retry succeeds, and the move to the bin starts in the same tick. Finally, on tick seventy, the release action succeeds. The "pick and place" branch succeeds, and so does the root. The loop stops. 

The whole task took seventy ticks, which is seven seconds, and each grasp try took twenty-three ticks. The actions add up to twenty-five ticks, but each new action starts in the tick its predecessor finishes, which saves one tick at each of the two joins. 

If the same tree runs with all three grasps failing, the third failure comes on tick seventy-two. The Retry gives up and fails, so "pick and place" fails, and the root Fallback ticks "ask for help" in the same tick. The root then answers "success", because one of its children succeeded. So here, "success" means the task was handled, rather than the mug is in the bin, and the log is what shows which way it went.

Once the node kinds are clear, the whole engine is one short function that calls itself on the children, plus a loop. The page provides pseudocode for this logic. It defines a tick function that takes a node. If the node is a condition, it returns success if true, or failure if false. If the node is an action, it does a little more of the action and returns running, success, or failure. 

If the node is a Sequence, it loops through each child starting from the one that is currently active. It ticks the child. If the child returns running, the Sequence remembers this child and returns running. If the child returns failure, the Sequence resets to the first child and returns failure. If it gets through all children successfully, it resets and returns success. A Fallback works exactly the same way, but with success and failure swapped. 

If the node is a Retry with a limit, it ticks its child. If the child fails, it adds one to a failure count and resets the child. If the failures are still below the limit, it returns running. If it hits the limit, it resets the count and returns failure. If the child succeeds, it resets the count and returns success. Finally, a main loop runs ten times a second, ticking the root node and stopping only when the answer is no longer running.

The main advantage of a behaviour tree only shows when the task changes. Suppose you find that most failed grasps happen because the mug sits too near the edge of the tray, where the fingers hit the wall. The fix is to nudge the mug towards the centre and look again before the next try. 

In a behaviour tree, that fix is one new branch. The page shows a diagram of the grasp part before and after this change. The new version adds a Fallback called "grasp or recover". It first tries the grasp, and if the grasp fails, it runs a "recover" Sequence. This recovery nudges the mug to the centre, detects it again, and then fails on purpose. That last failure makes the Retry node count one try and start again, now with the mug in a better place. Nothing outside these new nodes changed at all. In a state machine, by contrast, the same change would need a new "nudge" state, a new arrow out of "check grasp" into it, and a new arrow from it back to "detect".

The Sequence just described checks if the mug is located once, and then does not look at it again while the grasp runs, which is usually right. But some checks must be made on every single tick. For example, a safety check such as ensuring no person is in the work area must stop a move the moment it fails, not after the move ends. 

For this, libraries offer a reactive Sequence, which starts from its first child on every tick instead of from the one that was running. So a condition placed first is re-checked every tick, and if it fails while a move is running, the Sequence fails and tells the running action to stop. Stopping a running action this way is called halting it, so each action you write must handle a halt, for example by telling the arm controller to stop smoothly. In the BehaviorTree.CPP library, this node is called a ReactiveSequence, while in the py_trees library, the same choice is the memory setting of a Sequence, where setting memory to false makes it reactive.

The nodes also need to pass data to each other, because detecting the mug finds a position, and moving above the mug needs that position. A behaviour tree keeps such data in a blackboard, which is a shared table of named values. Here, the detect action writes the value for the mug pose, the move action reads it, and the condition checking if the pose is known simply checks whether that value is set. The blackboard is also what keeps the nodes independent, because the move action does not need to know which node found the mug. So you can swap the detector without touching the move at all.

The fourth section covers where a behaviour tree is used on a robot arm. Because a tree decides which step runs rather than doing the work itself, behaviour trees usually sit at the top of the program, above perception, planning, and control. They are used for the overall task, like pick and place, or longer jobs such as loading a machine, where each step has its own retries and fallbacks. They are used for choosing a grasp, where a Fallback tries grasping from above, then from the side, then pushing the object away from the wall and trying again. 

They are used for planning with a backup, where a Fallback asks the planner for a path with a short time limit, and if that fails, asks again with a longer one or a different planner. This is because a second try can find a path the first missed, as explained on the page about sampling-based planning. They are used for perception with a backup, trying a fast colour mask first, and if it finds nothing, running a slower learned detector. 

They are used for safety checks during motion, using a reactive Sequence to re-check that the work area is clear and force is below a limit on every tick, halting the move when either fails. They are used on mobile arms; for instance, the ROS 2 navigation stack runs its navigation as a behaviour tree, and an arm on a mobile base often uses one tree for driving and another for the arm. Finally, they are used under a language model, where the model can choose which subtree to run from a spoken request, while the tree still does the running.

The fifth section explains where a behaviour tree is useful, and where it is not. The uses just mentioned all ask for the same thing, because a behaviour tree is useful when the task has many steps and many ways to recover. It is then easy to add a new recovery, to reuse a subtree in two places, and to watch the tree run in a viewer, while each leaf can be tested on its own. 

But it goes wrong in a few common ways. The page provides a table listing these problems, the signs you would see, and what people do instead. 

The first problem is when an action blocks the tick by waiting for a move to end before returning. The sign is that the whole tree freezes during each move, and safety checks or the stop button stop working. The fix is to make actions start the work and return "running" at once, letting the work run on its own. 

The second problem is when a running action is not halted properly. You will see a move keep going after its branch failed, or the next move start while the last is still running. The fix is to write and test a halt step for every action. 

The third problem is using the wrong kind of Sequence. If you use one with memory for a safety check, it won't be re-checked during a move. If you use a reactive one for steps, a finished step might start again when an earlier condition flickers. The fix is to use a reactive Sequence only for true "must stay true" checks, and a Sequence with memory for steps. 

The fourth problem is reading "success" as "the job worked". The log might say success, but the mug is still on the table because the "ask for help" branch succeeded. The fix is to log which branch succeeded, or write the outcome to the blackboard. 

The fifth problem is putting too much data on the blackboard. Nodes end up depending on values written far away, and a change in one branch breaks another. The fix is to keep blackboard names few and clear, and pass values through each node's declared inputs and outputs. 

The sixth problem is letting the tree grow into one huge file, making it impossible to find where a behaviour is decided. The fix is to split it into named subtrees, each in its own file. 

Finally, if the task changes every day, not just its recoveries, someone will have to rewrite the tree for each job. In that case, the alternative is a task planner, or a language model that picks subtrees.

A behaviour tree is also not the right tool for the lowest levels. A gripper driver or a controller's safety modes have few, clear states and must be checked by hand, so a finite state machine is better there. Behaviour trees also do not choose the best order or set, since that is the job of greedy algorithms and optimisation solvers, which a tree can call as one action.

The sixth section lists libraries that provide behaviour trees, since the engine is the same for every task and you rarely write it yourself. The table lists several well-known options. 

The most used library in ROS 2 is BehaviorTree.CPP, which uses C++ for the leaves and XML for the trees, meaning the tree can change without rebuilding. It includes nodes like Sequence, Fallback, ReactiveSequence, RetryUntilSuccessful, and Parallel. There is also Groot2, a graphical editor that draws and edits BehaviorTree.CPP trees, showing the tree running live with each node coloured by its answer. 

For Python, there is py_trees, which uses the same ideas and calls a Fallback a Selector. It is good for learning and small projects. There is also py_trees_ros, which connects py_trees to ROS 2 topics, services, and actions, and includes a viewer. 

Finally, the Nav2 navigation stack in ROS 2 is written in C++ and is the best-known real behaviour tree in ROS 2, making it a good example to read, even though it is not an arm library. Both BehaviorTree.CPP and py_trees offer a blackboard, decorators for retries and timeouts, and a way to print or log the tree's answers on each tick.

The seventh section summarises why to use a behaviour tree and what it costs. A behaviour tree is a tree of actions and checks, grouped by Sequence, Fallback, and a few other ready-made nodes, and ticked many times a second. This gives you a task that can react to failures, retry, try alternatives, and stop safely, written in a shape that stays readable as the task grows. 

The obvious alternative is a finite state machine, which is simpler for a handful of clear situations and easier to prove correct. But each new recovery adds arrows to several states. In a behaviour tree, a recovery is one new branch, and a whole subtree can be reused in another task. The retry counter lives in a Retry node, not in your own code. That is why most robot arm programs choose a tree for the task layer and keep state machines for drivers and safety modes. 

The costs are that you must learn a new way to think. This includes steps that answer "running", ticks, and the difference between a Sequence with memory and a reactive one. Every action must be written so that it does not block and can be halted. "Success" at the root does not always mean the job worked, so you need good logging. You also add a library, and with BehaviorTree.CPP, a second language, XML, that a newcomer must read. Finally, a tree only ever does what you drew, because it does not plan a new task on its own.

The eighth section discusses the learned alternative. A behaviour tree can be compared directly with a language model as a planner, which chooses the order of the robot's steps from a request in plain words. The planner earns its place when the request changes from one day to the next and nobody can list every request in advance. For a task that never changes, such as the same box packed the same way every day, the tree is the better choice, because it is free to run, fast, and always does the same thing. 

A vision-language-action model goes further and turns pictures and an instruction straight into arm movements, but its success rates are still well below what a production line needs. In practice, the two meet. A language model picks a subtree, and a learned model, such as one for collision and failure detection, can serve as a condition like asking if a grasp failed.

The ninth section suggests where to read next. The page on finite state machines writes the same task as states and arrows, so reading the two side by side is the fastest way to see the difference. The chapter overview shows how task logic fits with choosers, like greedy algorithms and optimisation solvers. Other parts of the book provide real code for putting a task in order, a comparison with scripted logic, and a project that uses a behaviour tree to sequence a job.

The final section shows how to use a behaviour tree in Python. It shows a leaf node in a file, together with the few lines that build a tree around it, so you know what the library hands you and what every leaf costs you. The example uses the py_trees library because it can be shown as a short Python snippet, unlike BehaviorTree.CPP which requires C++ and XML. 

The code defines a custom action class to close the gripper. It has an initialise method that runs once when the leaf becomes active, sending a command to close the gripper with a specific width and force. It has an update method that runs on every tick while the leaf runs. This checks if the gripper closed on nothing, returning failure if so, or returning success if the gripper is still. Otherwise, it returns running. It also has a terminate method that stops the gripper when the leaf stops for any reason. 

Below this class, the code builds the tree. It wraps the close gripper action in a Retry decorator set to three attempts. Then it creates a Sequence with memory turned on, and adds four children to it: moving above the mug, descending, the retry grasp, and lifting. Finally, it creates the tree and runs a loop that ticks the tree, prints the status, and sleeps until the next tick, stopping only when the root succeeds. 

What the library does for you is the engine and the vocabulary. Ticking the tree walks it, works out which leaf is active, and combines the answers. The Retry decorator holds the counter, so you do not add one to your own code. The library also calls initialise and terminate at the right times, which stops a half-finished grasp from being left running. 

What you still write is every leaf, and that is most of the work. The functions to command and check the gripper are yours, and so are the other move actions, which follow the same shape. A leaf must never block, so a move is started in initialise and only checked in update. The loop and its timing are yours too, because py_trees does not provide a clock. 

Finally, you have to decide or measure three things. First is the memory setting, which changes whether a Sequence resumes where it left off, or starts again to become reactive. Second is the tick rate, which must be fast enough to notice a failure in time, but slow enough that every check finishes inside one tick. Third is the thresholds inside your leaves, such as the gripper width and closing force, which are measurements from your specific hardware rather than numbers to copy.
