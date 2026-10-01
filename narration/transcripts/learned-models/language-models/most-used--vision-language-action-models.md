Vision-language-action models. 

This page answers one question: how can one model take a camera picture and a sentence, and move a robot arm to do what the sentence says?

This is for a reader who has read the two previous pages on language models as planners and vision-language models. So you should already know what a token is, and how a picture is cut into patches. It also helps to have read the movement models overview, which explains the words policy, observation, and action, because this page uses those words in the same way.

This page explains how these models work, but it does not try to list the newest ones. For that, read the page on foundation models and generalist policies, which records what each laboratory has released or shown, as of September 2026.

The first section explains what it is. Here is the idea in one sentence. A vision-language-action model, or VLA, is a vision-language model that has been taught to output arm movements as well as words.

Think of asking a person to put the mug in the bowl. They do not write a plan first, and they do not say where the mug is, because they look, understand, and move all at once. So a VLA tries to do the same in one model.

The two pages before this one split the job into parts. A planner chose the steps, a vision-language model found the mug and checked the result, and other models and ordinary code did the moving. A VLA replaces all of those parts with one network. So it is a policy, in the sense of the movement models chapter, because it turns an observation into an action, many times a second. What makes it different from the other policies in that chapter is where it starts, since it starts from a vision-language model that already knows what mugs and bowls are, and what the words mean.

The next part covers what goes in and what comes out. Three things go in, each time the model runs. First, one or more camera pictures, often one from above the table and one from a small camera on the wrist. Second, the instruction, in words, such as "put the mug in the bowl". And third, the arm's current joint angles, read from the sensors in the joints.

One thing comes out, which is the next movements of the arm. Depending on the model, a movement is given as target joint angles, or as how far to move and turn the gripper, and it also says whether the gripper should open or close. Most VLAs output a short sequence of movements each time they run, not just one.

The instruction stays the same for the whole task, while the pictures and the joint angles change every time the model runs. So the model sees the result of its last movement before it chooses the next one.

The next section explains how it works inside. The starting point is a vision-language model, as described on the previous page. The picture is cut into patches, the patches and the words become one row of tokens, and a transformer reads the row. That model already knows a great deal about everyday objects, but what it cannot do is say "move 3 millimetres to the left". So there are two main ways to teach it that.

The first way was shown by Google's RT-2 in 2023, and it writes each movement as text. The model then outputs a movement in exactly the same way that it outputs a word. 

There is a diagram showing how this works. It shows a movement cut into eight parts, each written as one of 256 steps, giving a string of numbers like 1, 128, 91, 241, 5, 101, 127, and 217. A movement of the gripper has several parts, because it moves along three directions, called x, y, and z, and it turns about three directions, called roll, pitch, and yaw. It also opens or closes, and RT-2 adds one more part that says whether the task is finished. Each part has a smallest and a largest allowed value, and that range is cut into 256 equal steps, numbered 0 to 255. So the model does not need to write an exact distance, and it only needs to name the step, such as step 128, which is near the middle and means almost no movement. A whole movement therefore becomes eight numbers, just like the string in the diagram.

The benefit is that no new part is needed, because the model already writes numbers as tokens. So the training simply adds examples in which the right answer to a picture and an instruction is a string of eight numbers. OpenVLA, the first open VLA, uses the same idea.

The drawback is that 256 steps is coarse, and the model writes the numbers one token at a time. Writing one token takes about as long as writing one word in a chat window. So a model that writes eight tokens for every movement is slow.

The second way keeps the vision-language model for the understanding, and adds a second, smaller network that only produces movements. This smaller network is called the action expert, and models like pi-zero from Physical Intelligence, GR00T from NVIDIA, and SmolVLA from Hugging Face all work this way.

A diagram illustrates what happens in four steps. It shows what goes in, then ten random points being moved step by step into a smooth path of gripper positions. First, the vision-language model reads the pictures and the instruction once, and then passes its internal numbers to the action expert. Second, the action expert starts from random numbers, which in the diagram are ten random points, and each point is one future position of the gripper. Third, the action expert moves every point a little towards where it should be, and it does this a few times, for example ten times. At each step it uses the numbers from the vision-language model, so it knows where the mug and the bowl are. Finally, after the last step, the points form a smooth path from where the gripper is now to where it should go next.

This method of starting from random numbers and moving them step by step is called flow matching. The page on diffusion and flow policies explains it in more detail, and why it copes well when a task can be done in more than one way.

The benefit is that the output is smooth, exact numbers rather than 256 coarse steps. The action expert is also small, so it is quick to run.

Both ways are slow compared with an arm, because an arm's controller wants a new target many times a second, while a large model may take a noticeable part of a second to run once.

So the fix is to output a short sequence of movements each time, instead of one. This sequence is called a chunk, and the arm works through the chunk while the model is already working out the next one.

A diagram compares the two approaches using two timelines. In the top timeline, the model sends one command each time it finishes, and the arm waits in between, creating pauses. In the bottom timeline, each run of the model gives a chunk of eight commands, spread over the time of the next run, so the arm gets a steady flow of commands with no pauses. The movement is also smoother, because the commands in one chunk come from one decision. The page on action chunking transformers explains chunks in detail.

The next section is about how it is trained. A VLA is trained in three stages, one after another. The first stage is the vision-language model's own training, from the previous page, while the next two stages use robot data.

A demonstration is one recording of the task being done well. A person usually drives the robot through the task, and the robot records the camera pictures and joint angles many times a second. Each recording also has a sentence that says what the task was. The page on where the data comes from describes how demonstrations are recorded.

The first of the two robot stages is to train on many robots. The model is trained on a large pool of demonstrations, from many laboratories and many kinds of robot arm, and the training teaches it to output the recorded movement for each recorded picture and sentence. For example, OpenVLA was trained on 970,000 demonstrations from a shared pool called Open X-Embodiment, while the pi-zero models were trained on 10,000 hours or more of robot data. Some laboratories also mix in the internet pictures and questions from the vision-language model's own training, because this keeps the model from forgetting what it knew about objects and words.

The second robot stage is to fine-tune on your robot and your task. The model from the previous stage is trained a little more, on demonstrations of your task on your robot. This extra training is called fine-tuning, and it usually needs far fewer demonstrations, often tens to hundreds.

Robot demonstrations are slow and expensive to record, because each one needs a robot and a person, and this is the main limit on the whole field. So in 2026 several laboratories started to replace part of the robot data with video of people doing everyday tasks with their own hands. NVIDIA's GR00T N1.7, for example, was trained on 20,000 hours of such video alongside robot demonstrations. The data and demonstration document covers this in depth.

The next part lists well-known models of this kind. These are the VLAs you will meet most often. The size of a model is given as its number of parameters, and a parameter is one of the adjustable numbers inside the network that training sets. More parameters usually means a more capable model, and one that needs a bigger computer.

First is RT-2, from Google in 2023, which was the first well-known VLA. It introduced the trick of writing movements as tokens, but it was never released, so nobody outside Google can run it.

Next is OpenVLA, from Stanford and others in June 2024, which was the first VLA that anyone could download. It has 7 billion parameters and was trained on 970,000 robot demonstrations, and it writes movements as tokens, one movement at a time. It is under the MIT licence.

Then there are pi-zero and pi-zero-point-five, from Physical Intelligence, which add a flow-matching action expert to a vision-language model. Pi-zero was announced in October 2024 and released in February 2025, and they are among the strongest models that you can download. But they need an NVIDIA graphics card to run.

Another is GR00T N1.7, from NVIDIA in April 2026, which has 3 billion parameters and a flow-matching action expert. It was trained on robot demonstrations and on human video, and it also needs an NVIDIA graphics card.

Finally, SmolVLA, from Hugging Face in June 2025, has 450 million parameters. It is small enough to run on an ordinary computer, including a Mac, so it is the usual starting point for a beginner with a small arm.

Newer and stronger models exist, such as pi-zero-point-seven from Physical Intelligence and Gemini Robotics 2 from Google DeepMind, but neither of them can be downloaded. The frontier document lists what you can download today, with the licence of each one.

The next section gives a worked example: teaching a small arm to put a mug in a bowl. Here is SmolVLA on a small learning arm, such as the SO-101. The arm has a camera above the table and a camera on the wrist, and the software is LeRobot, a free library that records demonstrations, trains models, and runs them.

First, you record demonstrations. You move a second, identical arm by hand, and the robot arm copies it. This setup is called a leader arm and a follower arm. You put a mug in a bowl a few dozen times, and each time you place the mug and the bowl somewhere different. LeRobot records both camera pictures and the joint angles, with the sentence "put the mug in the bowl".

Second, you fine-tune. You start from the SmolVLA model that Hugging Face trained on many robots, and train it further on your recordings. SmolVLA's authors say this can be done on a single ordinary graphics card.

Third, you run it. Each time the model runs, it reads the two pictures, the joint angles, and the sentence, and then outputs a chunk of joint targets. The arm's controller moves through the chunk, and the model runs again with new pictures.

Finally, you check the result. The model does not report whether it succeeded, because it simply keeps outputting movements. So you add a check, such as a vision-language model asking "Is the mug in the bowl?", or a person watching.

Then try things that you did not record at all. Put a different mug on the table, or say "put the cup in the bowl" instead of "mug". A model that started from a vision-language model has a better chance with these than a policy trained from nothing, because it already knows that a cup and a mug are alike. It is still not certain to work, so the only way to know is to try each change several times and count the successes.

The next part discusses what goes wrong, and what people do about it. VLAs are the newest kind of model in this book, and their limits are important. The following points give the main ones, with what people do about each. The frontier document gives the evidence for each.

First, they do not control force. A VLA outputs positions, not forces. So it is good at tasks where the position is what matters, and weak at tasks where pressing gently or firmly matters. Google's own figures for Gemini Robotics 2 show this: 92 per cent success at unscrewing a light bulb, but 36 per cent at screwing one in. People put a force-aware controller underneath the VLA for contact tasks. The touch and body models chapter covers the models that sense force.

Second, they cannot refuse. A VLA always outputs a movement, even when it has never seen anything like the scene in front of it, because it has no way to say "I do not know". So the arm's ordinary safety limits must stay switched on, and a separate check decides when to stop.

Third, they are upset by small changes near the gripper. A 2026 study found that these models cope well with a whole object being hidden, but get much worse when small details at the point of contact change. They are also upset when a camera picture arrives late. So you test with the lighting, objects, and cameras you will really use.

Fourth, they need work on each new robot. A model that works on its builders' robot may need new demonstrations and fine-tuning before it works on yours. Treat "works with no extra training" as "worked on the authors' robot".

Fifth, they succeed less often than the videos suggest. Published success rates for the best models are often between one-half and three-quarters on hard tasks, while a factory needs close to every attempt to succeed. So people add a success check, a retry, and a person who can take over.

Sixth, you cannot easily tell why they failed. A pipeline of separate models lets you see which part went wrong. A VLA is one network, so a failure has no obvious cause. Recording every run, with its pictures, is the usual fix.

Finally, they need a large computer. Except for the smallest ones, VLAs need an NVIDIA graphics card with many gigabytes of memory. The frontier document lists what runs on a Mac.

The next section asks why use a vision-language-action model, and what it costs. A VLA is one network that turns camera pictures, an instruction, and joint angles into arm movements. It lets one model handle many tasks and many objects, including some it has not been shown on your robot, because it inherits knowledge about objects and words from a vision-language model.

There are two obvious alternatives to using a VLA at all. The first is a pipeline of separate parts: a planner, a seeing model, a grasp model, and a motion planner. Each part can be tested on its own, and a failure can be traced to one part. The second is a small policy trained from nothing on one task, such as an action chunking transformer. It is much smaller, it can be trained on a Mac, and on one fixed task it often works just as well.

So the VLA earns its place when the objects and the instructions keep changing, and you cannot write or train a separate part for each case. For one fixed task, the small policy or the pipeline is usually the better choice.

It costs you a large graphics card, a pile of demonstrations for fine-tuning, and a model whose failures are hard to explain. It also costs certainty: the success rates of today's best VLAs are well below what a production line needs.

The next part covers the written alternative. The written alternative is a pipeline made only of ordinary code. A behaviour tree holds the order of the steps and the retries. Pose from points finds a known object, and sampling-based planning moves the arm to it. Book 3's programmed methods page shows these parts working together on one arm.

The written pipeline wins for one fixed task with known objects, because each part can be tested on its own, and it does the same thing every time. But the VLA wins when the objects and the instructions keep changing.

The next section is where to read next. The page on foundation models and generalist policies is the record of the current state of the art, and it covers every important VLA as of September 2026, with what it can do, what it cannot, and whether you can download it. The pages on action chunking transformers and diffusion and flow policies explain the two ideas that VLAs borrowed from the movement models chapter. The world models chapter is the next chapter, because some of the newest robot models predict the next camera picture as well as the next movement. Finally, the page on learned methods in the frameworks book compares VLAs with the other ways of training one arm.

The final section is about using it in Python. This page has described a model that turns a picture and a sentence into the movement of an arm. This section shows what that looks like in Python, and after it you will know how few lines stand between a camera picture and a movement, and how much sits behind those lines.

The model used is OpenVLA, from earlier on the page. It is used here because it is published as an ordinary Hugging Face model, so the transformers library loads it in the same way as the vision-language model on the previous page. The code example is from OpenVLA's own documentation, with the instruction changed.

The code first imports the necessary libraries, including PyTorch and the Hugging Face transformers library. It then loads the OpenVLA model and its processor, sending the model to the graphics card. Next, it opens an image of a table and sets up a text prompt. The prompt asks what action the robot should take to put the mug in the bowl. The code passes the prompt and the image through the processor to prepare the inputs, and finally calls a predict action function on the model to get the movement.

Three details in that code are worth explaining. The prompt has a fixed shape, with "In:" before the instruction and "Out:" at the end, because that is the shape OpenVLA was trained on, and a different wording gives worse movements. Then the predict action function does the work of writing the movement as tokens, and this method turns those tokens back into numbers for you. Finally, an argument named unnorm key names the recorded dataset whose ranges are used to turn those numbers back into real distances, because the model itself only ever works in the range 0 to 255.

The pretrained model therefore gives you the seeing, the understanding of the words, and the choice of movement, all in one. That is a great deal, and it is the whole argument of this page.

What you still write is a loop and a driver. You take the picture from the camera, you run the code to get the action, you send the action to the arm's controller, and then you do it all again with a new picture. Nothing in the code talks to a robot, because the action is only an array of numbers, and turning those numbers into joint commands is your program's job. You also write the success check, because, as mentioned earlier, the model never stops by itself.

What you decide is harder than any of that. You decide whether to fine-tune, and on how many demonstrations, because a model that works on its builders' robot often does not work on yours. You decide the hardware, since sending the model to the graphics card in the code is not a detail: OpenVLA has 7 billion parameters and needs an NVIDIA graphics card, so it does not run on a Mac. For a small arm on ordinary hardware, the usual route is SmolVLA through LeRobot, which is driven from the command line rather than from Python, and which records the demonstrations for you as well.
