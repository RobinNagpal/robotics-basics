Finite state machines.

This page explains the finite state machine, which is the oldest and simplest way to write the logic that decides what a robot does next, and it answers five questions. What is a state machine, and how does it run step by step? Where does a robot arm use one, when does it stop being a good idea, and which libraries give you one ready-made?

It is written for a reader who has read the chapter overview and who knows what an arm, a gripper and a camera are, but it does not assume any course on algorithms. The running example is a pick-and-place task, where the arm moves mugs from a table to a bin and tries again when a grasp fails.

The first section is the introduction. A robot arm program must always know what it is doing right now. Is it looking for a mug, is it moving, or is it waiting for the gripper to close? That answer decides what the program does with the next piece of news, because the news that the gripper has closed means one thing while the arm is grasping and nothing at all while it is carrying.

A finite state machine is a way to write all of this down so that nothing is left to chance. First you list every situation the robot can be in, and then, for each situation, you list the pieces of news that matter and where each one leads. After that a very small loop follows your list.

State machines are everywhere in robots, often where you do not see them, because the gripper driver, the controller's safety modes and the start-up of a camera are all state machines. So learning to read one is useful even if you later write your task logic with a behaviour tree.

The next part gives the idea in one sentence. Since the program has to know what it is doing, a finite state machine is a fixed list of named situations, called states, and a table that says which event moves the program from one state to the next.

Here is an everyday example of the same idea, a washing machine with states such as filling, washing, rinsing, spinning and done. It is always in exactly one of them, and events move it on: the drum is full, the timer ran out, the door was opened. The door-opened event means stop and wait while washing, but it means nothing when the machine is done. So the machine does not need to remember the whole past, because knowing its current state is enough to decide what to do with the next event.

The word finite means that the list of states is fixed and has an end, so the program cannot invent a new state while it runs.

The next section explains how it works, step by step, starting with states, events and transitions. Once the idea is clear, a state machine turns out to have only three parts.

First, a state is a named situation, such as grasp. The machine is in exactly one state at a time. While it is in a state, it usually does one thing: in grasp, it closes the gripper.

Second, an event is a piece of news from outside, such as gripper closed or no path found. Events come from sensors, from other programs, or from a timer.

Third, a transition is a rule of the form: in state A, event E moves the machine to state B. It is drawn as an arrow from A to B, with E written on it.

All the transitions together form the transition table, which is a lookup. Given the current state and an event, it gives back the next state. So if the table has no entry for that pair, the event is simply ignored in that state.

One state is also marked as the start state, and some states can be marked as final states, where the machine stops.

Because those three parts are easier to see on a real task, the page shows a diagram of a state machine for the pick-and-place running example. It has eight working states arranged in a circle, a final state called done, and a state called ask for help.

The normal path runs clockwise, from detect through approach, grasp, check grasp, lift, carry, release and home, and then back to detect for the next mug. Meanwhile an orange arrow over the top shows the retry, and three red arrows lead to ask for help.

Here is what each of those states does in turn.

The detect state runs the camera and the detector, and turns the mug's pixels into a position. The event is mug found or no mug left.

The approach state plans a path to a point above the mug, and follows it. The event is arrived, or no path if the planner fails.

The grasp state lowers the gripper and closes it. The event is gripper closed.

The check grasp state reads the gripper's finger width. A mug is 80 millimetres wide, so a width near 80 millimetres means holding. A width near zero means the fingers closed on air, so the event is empty.

The lift, carry, release and home states move the arm up, move to the bin, open the gripper, and go back to the home pose. The carry state can also give a dropped event, if the finger width suddenly drops to zero.

The machine has thirteen transitions in all, and eleven of them are plain entries in a table. But the other two are the retry arrow and the tries equals three arrow, which need a counter.

A plain state machine has no memory beyond its current state, but the retry rule needs to know how many times the grasp has already failed. So the machine carries one extra number, a counter called tries.

A transition can then have a guard, meaning a condition that must be true for the arrow to be taken, and it can also have an action, meaning a small change made when the arrow is taken. So the two arrows out of check grasp on the event empty are these. First, if the event is empty and tries is less than three, the machine goes back to detect, and adds one to tries. Second, if the event is empty and tries equals three, it goes to ask for help.

Then the arrow for holding sets tries back to zero, so that the next mug starts fresh.

Going back to detect, rather than only to grasp, is a deliberate choice. A grasp often fails because the mug is not quite where the camera said it was, so looking again is what fixes it.

A state machine with extra numbers such as tries is sometimes called an extended state machine, and almost every real one is of this kind.

Since the machine is easier to trust once you have seen it run, the page provides a table showing a worked run with real numbers. The script runs that exact machine on two mugs. The first grasp on mug one closes on nothing, while every other grasp works. Each state takes a fixed time, ranging from zero point two seconds to check a grasp, up to two point five seconds to carry the mug.

The table shows the start of that run, row by row. It starts at zero seconds in the detect state, which ends at zero point four seconds with the mug found event, moving the machine to the approach state. It proceeds normally through approach and grasp, but at three point four seconds, the check grasp state ends with the empty event. The tries counter becomes one, and the next state is detect.

The machine then successfully detects, approaches, grasps, and checks the grasp again. This time the event is holding, the tries counter goes back to zero, and the machine moves to lift, carry, release, and home.

Mug two then takes the same path without the failure, so the run visits twenty-one states in all and ends in the done state at twenty-two point eight seconds. A diagram shows this whole run as a timeline, with a horizontal bar for the time spent in each state. You can see an early drop to check grasp followed by a jump back up to detect, which is the failed grasp and its retry. Because of this, mug one reaches the bin at eleven seconds, and mug two at twenty point four seconds.

You can also read the cost of one failure straight off the table. The retry repeated detect, approach, grasp and check grasp, which comes to three point six seconds. So without the failure, mug one would have been in the bin at seven point four seconds.

Once the table and the counter are settled, the whole machine is just a table and a loop. The loop waits for an event, looks up the next state, and then starts that state's action. The page provides pseudocode written for this machine.

It starts by defining a table that maps a state and an event to a next state. For example, detect and mug found maps to approach. Then it sets the initial state to detect, sets tries to zero, and starts the action of the state.

After that, a loop repeats until the state is done or ask for help. Inside the loop, it waits for the next event. If the state is check grasp and the event is empty, it adds one to tries. If tries is less than three, the next state is detect; otherwise, it is ask for help. For all other state and event pairs, it looks up the next state in the table. If the state is check grasp and the event is holding, it resets tries to zero. If the event is not in the table, it ignores it and keeps waiting. Finally, it updates the state and starts the new action.

Two details matter once this is written in real code. First, starting the action must not block the loop, because the action, such as a long move, runs on its own and sends an event when it ends. This means the loop stays free to receive other events, such as a stop button. Second, every state that waits for something should also have a timeout, meaning a timer that sends its own event, such as took too long, if the expected event never comes.

The machine allowed three tries, and that limit is a real decision which is easy to reason about with numbers. Say one grasp works seventy percent of the time, and that each try is independent of the last. Then the chance that all of n tries fail is zero point three multiplied by itself n times, so the chance of success within n tries is one minus zero point three to the power of n.

A diagram shows a curve rising as the retry limit goes from one to five. One try picks seventy percent of mugs, while two tries pick ninety-one percent, three pick ninety-seven point three percent, and five pick ninety-nine point eight percent. So each extra try helps less than the one before it. Real failures are also often not independent, because if a mug is lying on its side, every try fails in the same way. So a limit of two or three tries, followed by asking for help, is common.

The machine has only nine states, but a plain state machine grows badly as states are added. Suppose you add a stop button that must work in every state. Then you need a new arrow from each of the eight working states to a new stopped state, and to resume you need eight more arrows back, one to each state. A diagram shows this problem. On the left, a stop button is drawn flat, creating a tangle of arrows from every state.

The fix, shown on the right, is a hierarchical state machine, also called a nested state machine. Here the eight working states sit inside one parent state called working, and a transition drawn from the parent applies to every state inside it. So a single arrow now handles stop pressed from anywhere in the machine. A history marker, drawn as a circle marked H, means go back into whichever inner state the machine was in last, so one arrow also handles resume.

Nested states are the main tool for keeping a state machine readable, and drawings in this style are called statecharts, which most state machine libraries support.

The next section lists where state machines are used on a robot arm. Because a state machine is small and easy to check, they appear at every level of a robot arm system.

First is the task itself. The pick-and-place machine is a real pattern. Small cells with one fixed job, such as moving parts from a conveyor to a tray, often use exactly this kind of machine.

Second is the gripper. A gripper driver is usually a state machine with states such as open, closing, holding, opening and fault. The holding state is entered when the fingers stop before they are fully closed. The task logic reads this state as its holding mug check.

Third is the controller's safety modes. An arm controller is always in a mode such as idle, running, paused, protective stop or emergency stop. The rules for moving between these are strict, and they are written as a state machine so that they can be checked by hand.

Fourth is starting up software parts. In ROS two, a managed node, also called a lifecycle node, is a program with the fixed states unconfigured, inactive, active and finalized. A camera driver can be configured, then activated only when the arm is ready. The launch system moves each node through these states in order.

Fifth is a guarded move. A move that stops on contact has states such as moving, contact and holding still. The event force above ten newtons moves it from the first to the second. This is explained more fully on the page about impedance and force control.

Sixth is following an object. A tracker for a moving mug can be in searching, tracking or lost. It goes from tracking to lost when no detection has matched for, say, five frames.

Finally, talking to a device. Reading a message byte by byte from a serial force sensor is a state machine with states such as waiting for header, reading length, reading data and checking the sum.

The next part discusses where a state machine is useful, and where it is not. All the uses just mentioned are small, because a state machine works well when the number of states is small and the robot really is in one clear situation at a time. It is then easy to draw, easy to test and easy to check by hand, since every possible situation is written down, so you can ask of each state: what happens if the stop button is pressed here?

But it stops working well as soon as the task grows. The page provides a table of usual problems, the signs you see on the robot, and what people use instead.

The first problem is too many arrows. Each new recovery needs arrows from several states, and the drawing becomes a tangle. The sign is that adding one feature means changing many states, and bugs appear in states you did not touch. Instead, people use nested states, or a behaviour tree, where a recovery is one new branch.

The second problem is an event arriving in a state that has no arrow for it. The sign is the arm stopping and waiting forever, or ignoring a real fault. The fix is a default rule that logs every ignored event, and a timeout on every waiting state.

The third problem is a counter not being reset at the right time. The sign is that after a few failures on earlier mugs, every new mug goes straight to ask for help. The fix is to reset counters on the arrow that ends the attempt, as the holding event does here, and to test that path.

The fourth problem is when two things must happen at once, such as carrying a mug while watching the force. The sign is that the machine can only be in carry or check force, not both. Instead, people use parallel regions in a statechart, or a parallel node in a behaviour tree.

The fifth problem is when the same steps are needed in two places, such as detect before picking and before placing. The sign is that states are copied, and the copies drift apart. Instead, people use nested machines that can be reused as one state, or behaviour tree subtrees.

The final problem is when the task changes every day. The sign is that someone must redraw the machine for each new job. Instead, people use a task planner, or a language model as a planner that picks the steps.

A rough guide is this: up to about ten states a flat state machine is often the clearest choice, but beyond that you should use nested states or move to a behaviour tree. The number of possible arrows grows with the square of the number of states.

The next section covers libraries that provide state machines. You can write a small state machine yourself, but a library adds nested states, a viewer that draws the machine while it runs, and tested handling of timeouts and stop requests. The page lists several well-known ones.

For Python and ROS, there is SMACH, which is the classic ROS task state machine. It supports nested machines and running states side by side, and a viewer shows the active state. For C++, Python, and ROS two, there is YASMIN, a newer library with a web viewer. FlexBE works for Python, ROS, and ROS two, letting you build state machines in a graphical editor and watch them while the robot runs. SMACC two provides nested and parallel state machines for C++ and ROS two.

For plain Python, not tied to robots, there is a library called transitions, which is good for learning and small device drivers. For C++, Boost dot MSM and Boost dot Statechart are general libraries; Boost dot MSM builds the transition table when the code is compiled, so it is very fast. Finally, for ROS two managed nodes in C++ or Python, the lifecycle node provides the fixed start-up state machine described earlier.

Industrial arm controllers also have their own ways to write state machines. For example, many programmable logic controllers, the small computers that run factory cells, use a graphical language called Sequential Function Chart, which is a state machine drawn as steps and transitions.

The next section explains why to use a state machine, and what it costs. It answers four questions: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

A state machine is a fixed list of states and a table of transitions between them. This means it gives you a complete, written list of every situation the robot can be in, and of what each event does in each one. That in turn makes the behaviour easy to check, because you can test it state by state, and you can show the drawing to someone who does not read code.

The first obvious alternative is plain code, meaning a long function with if statements and loops. For three steps with no failures, that is simpler. But the state then lives in which line of code is running, so you cannot ask the program what it is doing now, and you cannot stop it cleanly in the middle. A state machine, in contrast, makes the state a named value that you can print, log and check.

The second obvious alternative is a behaviour tree, which handles retries and fallbacks by its shape and so grows more gracefully. Choose a state machine when the situations are few and clearly separate, and when you must be able to prove what happens in each one, as in a safety mode or a device driver. Choose a behaviour tree for a task with many steps and many ways to recover.

The costs are these. You must list every state and every arrow in advance, and the number of arrows then grows fast as you add features, because each new recovery touches several states. Extra memory, such as the retry counter, also lives outside the drawing and so is easy to forget. And the machine only ever reacts to the events that you planned for.

The next part discusses the learned alternative. Because a state machine only handles the situations you listed, the learned alternative is a language model as a planner, which chooses the robot's steps from a request in plain words and fills in steps the person never said. It wins when the request changes from one day to the next and nobody can list every request in advance.

A state machine still wins for a task that stays the same, because it is free to run, fast, and does the same thing every time, and you can check what happens in every state. Even with a planner, a checker in ordinary code is usually put between the planner and the robot. More often, learned models feed a state machine instead of replacing it. For example, a learned collision and failure detection model can send the empty or dropped event, and force and slip models can catch a slip before the mug falls.

The section on where to read next points to the page on behaviour trees, which writes the same pick-and-place task as a tree and compares the two. It also mentions the chapter overview, the building blocks page which explains loops that run at a fixed rate, and the programmed methods page which compares state machines with behaviour trees.

The final section shows how to use it in Python. It turns the earlier pseudocode into Python using the transitions library, because it is plain Python with no ROS installation behind it, making it easy to run.

The code defines a list of states, such as idle, moving above, descending, closing, lifting, and failed. It then defines a list of transitions. For example, the trigger start moves the source state idle to the destination state moving above. The trigger arrived moves moving above to descending.

For the retry logic, it defines two rules for the slipped trigger from the closing state. The first rule has a condition called has tries left, and a before action called use a try. If the condition is met, it moves back to moving above. The second rule for slipped simply moves to failed. Because the first matching rule wins, the retry is tried before giving up.

The code then creates a task class with a tries left counter set to three. It includes methods for the condition to check if tries are left, and the action to subtract a try. It also has a method named on enter moving above, which sends the goal to the arm. Finally, it creates the machine, linking the task object, the states, and the transitions, and sets the initial state to idle. When you trigger the start event, the state becomes moving above.

What the library does for you is the bookkeeping around the table. It keeps track of the state, adds one method to your object per trigger, and refuses a trigger that is not legal from the current state by raising an error. This turns a whole class of bug into an immediate complaint instead of a silent wrong move. It also runs the guards and callbacks, and calls a method when a state begins, which is where the arm is actually told to do something.

What you still write is everything the robot does. Each on enter method is yours, and so is the code that decides when an event has happened, because nothing in the library watches the arm. The library also does not run a loop. Something of yours has to call the trigger methods, normally from a timer at a fixed rate that checks the arm's state and fires the matching trigger.

What you have to decide or measure is the shape of the machine and the numbers in it. The list of states is a design decision. Up to about ten states, a flat machine like this one stays clear, and beyond that you nest it or move to a behaviour tree. The retry count is a number you choose, ending at two or three tries because each extra try helps less than the one before it, and because repeated failures on the same mug are usually not independent. Every event also needs a test behind it with a threshold you measured, such as how close counts as arrived and how small a gripper width counts as slipped. Finally, you need a timeout on every state that waits for the outside world, because waiting forever is the failure that a missing arrow produces.
