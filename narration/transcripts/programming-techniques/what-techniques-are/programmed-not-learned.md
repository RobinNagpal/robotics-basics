Programmed, not learned. This is the first page of Book 5, which explains the programming techniques that robot arm software is built from. A technique here means a fixed method that a person wrote down step by step, rather than something a computer worked out for itself. Examples are the pinhole camera model, the Kalman filter, A-star search, and proportional-integral-derivative control, which is usually called PID control. Each of these has its own page later in the book.

This page answers three questions: what a technique is, how it is different from a learned model, and how this book is laid out.

It is for a reader who has never taken a course on algorithms, so it starts from the beginning. However, you should already know what a robot arm, a frame, a camera, a pixel, and a point cloud are, because Books 1 and 2 explain them. Beyond that, you do not need to know any programming language well, and you do not need any maths past adding, multiplying, and square roots.

Book 5 has a partner in Book 6, which is about neural network models. That book covers the other way of building robot software, which is models that are learned from examples. This book covers the methods that people write by hand instead. A real robot arm uses both, so this page also says how they fit together.

The first part of the page explains what a technique is. A robot arm program has many small jobs to do. For example, it must turn a pixel into a position, and it must pick which object to grab first. It must also find a path that does not hit the table, and then tell each motor how hard to push. Each of these jobs is a question with an answer, so something in the program has to work that answer out.

A technique, in this book, is a written method that finds the answer to one such question, and it takes the form of a list of steps. A person worked out those steps, wrote them down, and checked that they give the right answer. The computer then follows the steps exactly, in order, every time it runs.

Computer scientists call such a list of steps an algorithm, and this book uses "technique" and "algorithm" to mean nearly the same thing. "Technique" is a little wider, because it also covers a way of setting up a problem. For example, the pinhole camera model is a formula more than a list of steps.

Every technique has three parts. First is the input, which is what you give it, such as the positions of four mugs. Second are the steps, which are what it does with the input. For example, it might work out the distance to each mug, and keep the smallest. Finally, the output is what it gives back, such as "mug D".

A technique gives the same output every time you give it the same input. This is because nothing inside it changes from one day to the next unless a person changes it. So that fixed behaviour is the main thing that makes it different from a learned model.

Many techniques also have parameters, which are numbers that you choose before you run the technique and that stay fixed while it runs. For example, a rule that says "anything closer than 580 millimetres is an object" has one parameter, the 580. Choosing parameters well is a large part of using a technique, so the page on choosing a technique comes back to it.

To make those three parts concrete, the next section walks through a first technique from start to finish, finding the closest mug. A robot arm stands at a table with four mugs on it, and a camera has already found where each mug is. The arm should pick up the mug closest to its gripper first, because that is the shortest move. So the question this technique has to answer is which of the four mugs is closest.

All the positions are measured in millimetres on the table, as seen from above, and the gripper tip sits at an x coordinate of 250 and a y coordinate of 100. The four mugs are called A, B, C, and D. A diagram shows the gripper tip and the four mugs from above, with a line from the tip to each mug. The shortest line is 113.1 millimetres to mug D.

The technique works through the mugs one at a time. Its steps are to first start with no answer yet, and a "smallest distance so far" that is larger than any real distance. Second, take the first mug and work out its straight-line distance from the gripper tip. Third, if that distance is smaller than the smallest so far, remember this mug and this distance. Fourth, repeat the second and third steps for every other mug. Finally, the mug you remember at the end is the answer.

The distance in the second step comes from Pythagoras' rule, which says to take the difference in x and the difference in y, square each one, add them, and take the square root. For mug D, at x equals 330 and y equals 180, both differences are 80, so the two squares are 6,400 and 6,400, and they add up to 12,800. The square root of 12,800 is about 113.1, which means mug D is 113.1 millimetres from the gripper tip.

A table follows these steps one mug at a time. It shows the position and distance for each mug, whether that distance is smaller than the smallest so far, and what the technique remembers after checking it. For the first mug, mug A, the distance is 246 millimetres. This is the first one checked, so it is the smallest so far, and the technique remembers mug A. Mugs B and C are further away, so the technique ignores them and keeps remembering mug A. Then it checks mug D, which is 113.1 millimetres away. This is smaller than mug A's distance, so the technique forgets A and remembers mug D instead.

The output is mug D, and the diagram agrees, because the line to mug D is the shortest of the four.

The page then shows these same steps written as pseudocode, which is a way of writing steps that looks a little like a program but belongs to no programming language. This is meant for people to read rather than for a computer to run, and every technique page in this book gives its steps this way.

The pseudocode takes the gripper position and a list of mug positions as input. It sets the best mug to none, and the smallest distance to infinity, which stands for a number larger than any real distance so the first mug is always smaller than it. It then loops through each mug in the list. Inside the loop, it calculates the distance using the square root of the sum of the squared differences in x and y. If this distance is less than the smallest distance seen so far, it updates the smallest distance and records this mug as the best one. After checking all the mugs, it returns the best mug as the output.

This technique has a name of its own, because it is the simplest form of nearest-neighbour search, which means finding the item closest to a given point. It works the same way for 4 mugs or for 40,000 points in a point cloud. With 40,000 points, however, it becomes slow, so the page on nearest-neighbour search shows faster ways to do it.

The next part of the page explains that you can write the same steps in any language. The closest-mug technique was written as pseudocode rather than as code, and that was deliberate, because the techniques in this book are language independent. That means the steps do not depend on which programming language you use. The same steps therefore work in Python, in C++, in Rust, or on paper with a calculator, and only the spelling changes.

The page shows the same steps written in Python, using the built-in math library to calculate the square root of the sum of the squares, and then again in C++, which is the other language that robot software is most often written in. Both programs have a starting value, a loop over the mugs, a distance calculation, a comparison, and a result. So they are the same pseudocode spelled two ways, and, when called with the four mugs from the example, the Python version returns D, which is the answer the table worked out by hand.

This is why the book teaches techniques as steps and not as code. Once you understand the steps, you can read them in any language, and you can also recognise them inside a library. Most of the time you will not write a technique yourself, since you will call a library that already has it, such as OpenCV for pictures or Open3D for point clouds. Each technique page therefore ends with a table of the libraries that provide it, and the name of the function to call.

The next section compares written rules to a trained model. There are two ways to build the software that answers a question for a robot. The first way is to write the steps yourself, which is a technique and is what this book is about. People call software built this way programmed.

The second way is to let a computer find the steps for you. You collect many examples of inputs, each with the right output written next to it. A program then adjusts millions of numbers inside a model until the model gives the right outputs for those examples. This adjusting is called training, and software built this way is called learned, which Book 6 explains, starting with the page on what a model is.

To show where a written rule is strong and where it is weak, the page gives an example of a job done by a rule. A depth camera looks straight down at a table and, for each pixel, reports how far away the surface is in millimetres. The table is 600 millimetres from the camera, so anything standing on the table reads closer than that. A simple written rule for finding objects is therefore that a pixel is part of an object if its depth reading is more than zero and less than 580 millimetres. The 580 is the rule's one parameter, and it leaves 20 millimetres of room for the camera's small errors. The "more than zero" part is there because the camera writes zero when it gets no reading at all.

A diagram shows two bar charts of depth readings along one row of pixels. On the first chart, five pixels on a mug read between 503 and 512 millimetres. This is below the 580 millimetre limit, so the rule successfully finds the mug. On the second chart, the camera gets no reading through a clear glass and writes zero, so the rule finds nothing and misses the glass.

On the mug, the rule works well. It is fast, because it costs one comparison per pixel, and it is exact, because you can point at any pixel and say why it was chosen. It also needed no examples at all, since a person worked the 580 out from the table's known distance.

On the glass, the rule fails. Light passes through glass instead of bouncing back, so the depth camera gets no reading there, and the rule was never told what to do about that. Book 2 describes this problem in the section on the depth hole, for glass and chrome. You could write a second rule for holes in the depth picture, but then a shadow also makes holes, so you need a third rule. Each new rule fixes some cases and breaks others.

A learned model would handle this differently, because you would show it many colour pictures of glasses, each with the glass outlined by a person. It would then learn what glasses look like, including their edges and reflections, without anyone writing a rule about light.

A table compares the two ways across several points. For a programmed technique, a person writes the steps, you need an understanding of the problem to start, and it often runs in under a millisecond. You can also see exactly why it gave an answer, step by step. For a learned model, a program writes the steps from examples, and you need many examples with the right answers to start. It is slower, often taking tens of milliseconds on a graphics card, and you mostly cannot see why it gave an answer. The table also notes that while a programmed technique usually does not work on things you did not plan for, a learned model often will, if they look like the examples. Finally, you fix a mistake in a programmed technique by changing a step or a parameter, whereas you fix a learned model by adding more examples and training again.

Most real robot arms use both ways together. The common pattern is that a learned model finds the mugs in the colour picture. After that, programmed techniques do everything else. They turn pixels into positions, fit the table plane, plan the path, and drive the motors. Books 2 and 3 show this pattern many times, for example in the pages on methods you write yourself and programmed methods for one arm.

This raises a question a beginner often asks, which the next section answers: why learn techniques when models exist? Learned models can do so much, so why spend time on hand-written techniques?

The first reason is that a robot arm cannot run without them. Even a robot built around a large learned model still needs a camera model to turn pixels into positions, and transforms to move between the camera's frame and the arm's frame. It also needs a controller to turn joint targets into motor currents, a thousand times a second. None of these three parts is usually learned, so they have to be written by hand.

The second reason is that techniques are exact where exactness matters. A transform from the camera to the base is plain arithmetic, so it is either right or wrong, and you can check it with a ruler. A learned model instead gives answers that are usually close. For a gripper with 5 millimetres of room on each side of a mug, "usually close" is not always good enough.

The third reason is cost, because a technique needs no training data and no graphics card, and it often runs in well under a millisecond on an ordinary processor. It is also easier to test, since you can reason about every step.

The fourth reason is understanding, because a learned model is often described as replacing a technique. A movement model replaces a planner and a controller, and a grasp model replaces a hand-written grasp search. You cannot judge whether the replacement is better unless you know what it replaced.

Techniques cost you something too, because they need a person who understands the problem well enough to write the steps. They also break when the world does something the person did not plan for, as the glass did earlier. And each parameter, such as the 580 millimetre limit, has to be chosen and then checked again whenever the scene changes.

So the advice in this book is the same as in Books 2, 3, and 6. If a written technique does the job reliably, use it, and switch to a learned model only where the world is too varied for rules. The page on choosing a technique explains how to tell which case you are in.

Now that the difference between a technique and a learned model is clear, the next section says what the rest of the book covers. The book sorts the techniques used on robot arms into seven categories, and each category answers a different question for the arm. Each category has its own chapter, and every chapter starts with an overview page.

Inside each chapter, the technique pages are split into two groups, because some of them matter more than others. The most used group holds the techniques that nearly every arm program needs, or that matter most. The also used group holds techniques that are used often, but only for some tasks or some kinds of arm. So if you are short of time, read the most used group of each chapter first.

The page includes a table listing the seven categories and all 34 technique pages. It shows the category name, what it does, and the techniques split into the most used and also used groups. For example, the first category is geometry and cameras, which turns pixels, frames, and joint angles into positions you can trust. Its most used techniques include the pinhole camera model and rigid transforms. Another category is fitting and estimation, which gets a clean shape or a steady number out of noisy measurements, using techniques like least-squares fitting and the Kalman filter. A third example is planning and search, which finds a way for the arm to get from here to there without hitting anything, using methods like sampling-based planning and trajectory optimisation.

Below the table, the page explains a few abbreviations used in it. RANSAC stands for random sample consensus, which is a way to fit a shape while ignoring readings that are plainly wrong. PID stands for proportional-integral-derivative, and MPC stands for model predictive control, which means planning a short way ahead, taking the first step, and then planning again.

Before those seven chapters comes this first chapter, which explains the ideas that every later page uses. It has four pages. First is this page, programmed, not learned. Second is the building blocks, which explains the six ingredients that almost every technique is made from, such as frames, arrays, graphs, noise, cost functions, and loops. Third is choosing a technique, which explains how to judge a technique by its speed, accuracy, and tuning, and when to use a learned model instead. Finally, the map of techniques puts all seven categories and all 34 technique pages on one page, placed on one arm task.

The next section explains how to read this book. You should read this first chapter straight through, because each page uses words that the page before it explained.

After that, the seven category chapters can be read in any order. Each one starts with an overview page that says what the category is for and lists its techniques. Each later page in a chapter covers one technique, and those pages sit in the two groups described above, with the most used group first. Every technique page follows the same order. First, it explains what question the technique answers, in one sentence, with an everyday example. Second, it explains how it works, step by step, with a small example worked out with real numbers, and the steps as pseudocode. Third, it shows where it is used on a robot arm. Fourth, it explains where it works well, where it fails, and what people use instead when it fails. Fifth, it lists which libraries already provide it, and the name of the function to call. Sixth, it explains why you would choose it over the obvious alternative, and what it costs you. Finally, it tells you where to read next.

If you want the whole picture first, read the map of techniques next, and then come back to the building blocks.

The pseudocode in this book follows the same few rules as the closest-mug example earlier. The equals sign stores a value under a name, and indented lines belong to the line above them. "For each" repeats, "if" decides, and "return" gives the output. Words in plain English stand in for anything that would take many lines of code, such as "square root of".

A real worked example of many of these techniques on one arm is the pick-glasses project in the robot-arm-projects repository. It uses nearest-neighbour search, the distance transform, clustering, and a greedy choice of camera views to find and pick up drinking glasses, and the technique pages mention it where it helps.

The final section suggests where to read next. The building blocks is the next page, which explains the ingredients that almost every technique uses. The page on what a model is, which is the first page of Book 6, explains learned models, the other half of robot arm software. The page on methods you write yourself in Book 2 shows many programmed perception techniques at work, with code. Finally, the page on programmed methods for one arm in Book 3 shows how written methods drive a whole arm task.
