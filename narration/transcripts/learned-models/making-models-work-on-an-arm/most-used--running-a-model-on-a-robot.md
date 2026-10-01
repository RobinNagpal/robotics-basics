Running a model on a robot. 

The earlier documents in this chapter were about making a model: what it is, how it learns and where its examples come from. This document is about what happens next, when a finished model is put on a real robot arm and used. 

It answers six questions, and they follow one after another. What is the difference between training a model and using it? How fast must a model be? Why do models run on a graphics card? Why are big models slower? What does it mean when a model is sure, and why can it be sure and wrong? And what else must sit around a model to keep the arm safe? 

It is written for a complete beginner, so you only need to know what a robot arm and a camera are, and you should have read the previous page on what a model is. Nothing else is assumed.

The first section explains that training and using are two different jobs. A model has two lives, and almost everything in this document follows from the difference between them. 

The first life is training, during which the model is shown many examples and its numbers are changed a little at a time until its answers are good. Training happens once, or at most a few times, and it usually happens on powerful computers in a data centre far away from the robot, where it can take hours, days or even weeks. 

The second life is using the model, and by then its numbers are fixed. The robot gives the model an input, such as a camera picture, and the model gives back an answer, such as "there is a mug at this spot". Using a trained model to get an answer in this way is called inference, which is a word that simply means working something out. 

During inference the model does not learn at all, so if it gives a wrong answer its numbers do not change, which means it will give exactly the same wrong answer the next time it sees the same picture. To fix it, somebody must collect new examples and train the model again. 

Because the two lives are so different, they need different things from a computer. Training needs a great deal of computing power and memory, but it does not need to be quick, since nobody is waiting for any single step of it. Inference needs much less computing power for each answer, however it must be quick, because the robot really is waiting for that answer. The rest of this document is about inference.

The next part asks how fast is fast enough. Since inference must be quick, the next question is how quick. The time a model takes to give one answer is called its latency, and it is measured in milliseconds, where a millisecond is one thousandth of a second. 

How much latency is acceptable depends entirely on the job, because three jobs on a robot arm run at very different speeds. 

A typical camera takes 30 pictures every second, which is one new picture every 33 milliseconds, so a model that looks at every picture must finish within 33 milliseconds or it falls behind. 

The control loop is the part of the robot's software that tells the motors what to do, because it reads the joint sensors, works out a small correction and then sends a new command to each motor. Many arms run this loop hundreds of times a second, so at 500 times a second each pass has only 2 milliseconds to finish in. 

Deciding the next step of a task, such as "now pick up the mug", happens much less often than either of those, so taking a second or more to decide is usually fine, because the arm is still busy doing the current step while the decision is made. 

A diagram in the text shows one tenth of a second, during which the control loop ticks fifty times while the camera takes only three pictures. It shows that a small model finishes well within each picture's time, a medium one only just keeps up, and a large one is still busy at the end. 

This is why a neural network is almost never placed inside the control loop itself, since it is usually far too slow to answer every 2 milliseconds. Instead the work is split between two parts. The model runs at its own slower speed and gives a goal, such as a target position or a short list of the next few movements, and then a simple, fast, programmed controller follows that goal at hundreds of steps a second. Some movement models are designed around this idea. The page on action chunking shows one that gives a whole chunk of movements at once, so that it needs to be asked less often. 

Latency is not the only kind of speed, because throughput is how many answers a model gives each second. A slow model can sometimes have good throughput by working on several pictures at the same time, however a robot usually cares about latency instead, since it needs the answer about this picture now.

Moving on to processors, the page covers the CPU and GPU. Meeting those time budgets depends on which processor the model runs on. A computer has a main processor called the CPU, or central processing unit, and a CPU has a small number of powerful workers called cores, usually between a few and a few dozen of them. Each core can do almost any job very quickly, one step after another, which is why the CPU runs the operating system, the robot's programs and the control loop. 

Many computers also have a GPU, or graphics processing unit. A GPU was first built to draw pictures on a screen. Drawing a picture means doing the same small sum for millions of pixels. So a GPU has thousands of simpler cores, and they all do the same kind of sum at the same time, on different numbers. 

A neural network, inside, is mostly one kind of work. It multiplies a very large number of numbers together and adds up the results. The document on the inside of a neural network showed why. Every one of these multiplications is small and independent of the others. That is exactly the kind of work a GPU was built for. So a GPU can often run a neural network many times faster than a CPU can. 

This is why training almost always uses GPUs, and why most robots that run models carry one. There are small computers made for robots that include a GPU, such as NVIDIA's Jetson boards. Some laptops and desktop computers, such as Apple's Mac computers, have the CPU and GPU on one chip and can run smaller models well. There are also chips built only for neural networks. They are often called NPUs, or neural processing units, or accelerators. 

A CPU can still run a small model. For a small model that answers only a few times a second, a CPU is often good enough, and it avoids the cost, heat and power use of a GPU.

The next section is about model size and speed. Whichever processor you use, the model's own size decides much of its speed. The size of a model is usually given as the number of numbers inside it, and those numbers are called parameters, or weights. A small seeing model may have a few million of them, whereas a large language model may have many billions. 

Every parameter is used at least once each time the model gives an answer, so more parameters mean more multiplications, and more multiplications take more time. That is why bigger models are usually slower. 

Bigger models also need more memory, because every parameter must be stored in the memory of the chip that runs the model. If each parameter takes 2 bytes, then a model with 1 billion parameters needs about 2 gigabytes just to hold its numbers, and a model with 7 billion parameters needs about 14 gigabytes, which a small robot computer may simply not have. 

Bigger models are often better, though, because they hold more knowledge and cope better with unusual pictures. Choosing a model size is therefore a trade, and what you want is the largest model that still answers fast enough on the computer your robot actually has. 

There are four ways to make a model smaller or faster. First, you can use a smaller version. Many well-known models come in several sizes, such as small, medium and large, so you pick the one that fits. Second, you can store each number with fewer bits. This is called quantisation. Each parameter is rounded to a less exact number that takes less memory. The model gets smaller and faster, and usually only a little less accurate. Third, you can train a small model to copy a big one. This is called distillation. The large model gives answers, and a small model is trained to give the same answers. Finally, you can use a smaller picture. A model that looks at a picture half as wide and half as tall has a quarter as many pixels to process. 

Each of these four costs some accuracy, so you check how much it costs by testing the smaller model on exactly the same tasks as the large one.

The next part explains how sure the model is, and why it can be sure and wrong. Speed is not the only thing a robot needs from a model, because it also needs to know how far to trust the answer. Many models give a number with each answer that says how sure the model is, and that number is called the confidence, or the score. It usually runs from 0 to 1, so a score of 0.96 next to the word "mug" means the model is very sure it sees a mug. 

The score is useful, because a robot can ignore answers with a low score, or go and look again from another angle. 

However the score is not a promise, since a common kind of model can only choose from the names it was trained on. Suppose a model was trained to tell apart just three things: "mug", "bottle" and "box". Its scores for those three always add up to 1, so it has no way at all to say "none of these". When it is then shown something it has never seen, such as a shoe, it must still share its score between "mug", "bottle" and "box", and it may well give most of that score to one of them. 

A diagram here shows made-up scores from a model that knows only mug, bottle and box, when it is shown a mug, a bowl and a shoe. The model is right and sure about the mug, but it is equally sure about the bowl and the shoe, where it is wrong. 

A model is most trustworthy on pictures that look like its training examples, and a picture unlike any of them is called out of distribution, which simply means out of the range of things it was trained on. On such pictures the score can be high for no good reason at all, and a new kind of object, strange lighting, a dirty camera lens or a reflection in a window can each cause it. 

People do several things about it. First, they add an extra answer such as "nothing I know" and train the model with examples of it. Second, they check the score against other information. For example, a depth camera can confirm that there really is an object of the right size at that spot. Third, they adjust the scores after training, so that a score of 0.9 really is right about 9 times in 10 on test pictures. This is called calibration. Finally, they test the model on pictures from the real place where the robot will work, not only on the pictures it was trained on. 

None of these four makes the score perfect, so a robot should treat a model's answer as a good guess rather than a fact, and the rest of the system must always be ready for that guess to be wrong.

The next section shows that the model is one part of a loop. Because a model's answer is only a good guess, it is never the whole system. A model on its own does not move anything, so it sits inside a loop together with other parts, where each part does one job and then passes its result on. 

The sequence goes like this. First, the camera takes a picture. Second, the model looks at the picture and gives an answer, such as "the mug is here, and it is best held by its body from above". Third, safety checks look at the answer and decide whether it is sensible. Fourth, the planner works out a path for the arm from where it is now to the mug. It makes sure the path does not hit the table or anything else. Fifth, the controller turns the path into motor commands, hundreds of times a second, and the arm moves. Finally, the world changes, because the mug has moved or the gripper has closed, so the camera takes a new picture and the whole loop starts again. 

A diagram illustrates this loop. It shows that if the safety checks do not accept the model's answer, then the arm does not move on it at all, and instead the arm stops or the model is asked again. 

The planner and the controller are often not neural networks, because they are usually programs written by people from the geometry of the arm. Other pages in the book cover planning a path and controlling the move. Some models do more than one of these jobs at once. A vision-language-action model takes the picture and gives arm movements directly, doing the job of the model and the planner together. Even then, a programmed controller and safety checks still sit between it and the motors.

The next part details the safety checks around a model. Because a model can be wrong, and sure while it is wrong, the rest of the robot must not trust it blindly, which is why most real systems wrap a model in simple checks written by people. These checks are plain rules, so anyone can read them and know exactly what they do, which is the opposite of a model's numbers. 

A table lists common checks and what they stop from going wrong. For example, checking if the score is above a set level, such as 0.8, stops the robot from acting on a guess the model itself was unsure about. Checking if the target is inside the area the arm is allowed to reach stops the arm from reaching off the table or towards a person. Checking if a second sensor, such as a depth camera, agrees stops the robot from acting on a mug that the model imagined. Checking if the planned path is clear of known obstacles stops the arm from hitting the table, a wall or itself. Checking if the speed and force are below set limits stops a fast or hard movement that could hurt someone or break something. Checking if the model answered in time stops the arm from acting on an old picture after the mug has moved. And finally, checking if the gripper is really holding something after grasping stops the robot from carrying on as if the grasp worked when it did not. 

The speed and force limits usually live inside the controller or in the arm's own safety system rather than in the robot's main program, because that way they still work even if the main program has a mistake in it. Most industrial arms also have an emergency stop, which is a large red button that cuts power to the motors straight away. 

When a model is new, people also test it slowly at first. They run the arm at low speed with a person watching and a hand near the emergency stop, and they start with soft objects on an empty table. Only when the model has done well many times do they let it run faster.

The next section asks why use a model at all, and what it costs. Given everything a model costs, it is worth asking why anyone uses one. The obvious alternative to a neural network is a programmed rule, such as "the mug is the largest red patch in the picture". A programmed rule is fast and runs easily on a CPU, and it is never sure and wrong in a surprising way, because you can read it and see exactly what it does. 

The problem is that such a rule breaks as soon as the world changes, since a blue mug, a red plate or a shadow over the mug can each defeat "the largest red patch". A model trained on many varied examples copes with those changes far better, which is why models are used for jobs where the world varies a lot, such as recognising objects, choosing grasps and following spoken instructions. 

The cost is everything else in this document. A model needs a computer fast enough to run it, often with a GPU, and it needs to be small enough to answer in time. Its answers come with a score that you cannot fully trust, and it needs programmed checks around it, because nobody can read its numbers and know what it will do on a picture it has never seen. 

So most robots mix the two approaches rather than choosing between them. A model does the part that has to cope with variety, such as finding the mug, while programmed parts do everything that must be exact and safe, such as planning the path, driving the motors and checking the limits. The programmed methods document describes those parts.

The page then suggests where to read next. The next page is about evaluation and failure, showing how to tell whether the model is good enough to leave running. Other pages cover the map of models, showing where every kind of model sits in the loop; where the data comes from before a model is trained; movement models that work closest to the control loop; collision and failure detection; comparisons of real seeing models you can download; and working without a GPU, which explains what you can do on a computer with no NVIDIA graphics card, such as an Apple Silicon Mac.

The final section is about using it in Python. Earlier, the page gave the time budget of 33 milliseconds per camera picture, and the first safety check, which is to act only on answers the model scored highly. This section measures the first and applies the second, because both of them are a few lines of code around a call you already have. After reading it, you will be able to say whether a model is fast enough on the computer your robot actually has. 

The page shows a short Python script using the Ultralytics library to run a YOLO model. The code imports the time library, loads the model, and sets up an empty list to record the times. Then, it loops through pictures from the camera one at a time. For each picture, it records the start time, asks the model for a result, and calculates how many milliseconds the whole process took, adding that time to the list. Inside the loop, it also applies the safety check by keeping only the results where the model's confidence score is greater than 0.8. Finally, it sorts the list of times and prints out the middling time, the slowest time, and the budget of 33 milliseconds. 

Ultralytics gives you the model, the download, the resizing of your picture and the answer, so the only line that is yours is the timing around it. Each result also carries its own speed record, which includes the milliseconds the network itself took. That number is smaller than the one this snippet prints, because the Python timer also counts the resizing before and the sorting of boxes afterwards. It is the larger number that has to fit inside 33 milliseconds, because that is the time your program really spends. 

What you have to write yourself is the camera loop, and what happens to the sure results afterwards. Reporting the slowest time as well as the middling one is also yours to remember, and it matters more than it looks. A model that answers in 20 milliseconds almost always, and in 90 milliseconds once a second, still drops a picture every second, so a single average would have hidden the problem. 

What you have to decide is the score limit, the picture size, and the model size. All three trade accuracy against time, as explained earlier, so measure them on the computer that will sit next to the arm and not on your laptop. Do not choose the score limit as a round number, because the page on uncertainty and confidence shows how to work it out from what a mistake would cost instead.
