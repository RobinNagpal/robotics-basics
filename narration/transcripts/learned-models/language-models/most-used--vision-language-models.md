Vision-language models. This page answers one question: how can a model look at a camera picture and answer a question about it in words, and what can a robot arm do with those answers?

You should already know that a language model reads and writes tokens, and that a token is turned into a list of numbers. It also helps to know a bit about seeing models, because this page compares the two.

The first part of the page explains what it is. Here is the idea in one sentence. A vision-language model, or VLM, is a language model that can also read a picture, so you can ask it questions about what the picture shows.

Think of showing a friend a photo on your phone. You ask, "Which of these mugs is mine?" Your friend looks at the photo and says, "The red one, on the left." They used the picture and your words together, and a vision-language model does the same.

A plain language model cannot do this, because it has never seen the table. A seeing model, such as an object detector, can see the table, but it can only answer one fixed question, such as "where is every cup?", with names from a fixed list. So a vision-language model is the one that can answer a question that nobody planned for, such as "Which mug is upside down?"

Next is what goes in and what comes out. Two things go in. First, one or more pictures, such as the latest frame from the robot's camera. Second, a question or an instruction in words.

One thing comes out, and that is text. The text can be an ordinary answer, a "yes" or "no", or numbers written as text, such as the position of a point on the picture.

The diagram shows one camera picture with three different questions asked about it. The first two answers are words, while the third answer is a point, given as two pixel numbers, and an orange circle shows where that point falls on the picture. A pixel is one small dot of a camera picture, and a position on a picture is given as a count of pixels across and down.

The third kind of answer matters most for a robot arm, because words alone cannot tell a gripper where to go, while a point on the picture can. Combined with a depth camera, a point on the picture becomes a point in 3D space that the arm can reach. Some models answer with a box around an object instead of a point, and the box is also written as numbers in the text.

The next section covers how it works inside. The trick is to turn the picture into tokens, in the same way that a sentence is turned into tokens. Then the language model reads the picture tokens and the word tokens together, in one row.

The diagram shows a picture cut into sixteen patches, with the patches and the words joined into one row of tokens, and the language model answering. Here are the steps in order.

First, cut the picture into patches. The picture is cut into a grid of small squares, called patches. A real model uses a much finer grid than the drawing, because a patch is often fourteen or sixteen pixels wide, so one picture gives hundreds of patches.

Second, turn each patch into a list of numbers. A seeing network, called the vision encoder, reads all the patches, and it turns each patch into a list of numbers that describes what is in it, such as "part of a red handle". The vision encoder is itself a transformer network.

Third, make the lists fit. A small extra network, often called the projector, changes each patch's list so that it has the same length as a word token's list. After this step, the language model can read a patch in the same way as a word.

Fourth, join the row. The patch tokens go first, and then come the word tokens of the question, so the model now has one long row of tokens.

Finally, answer one token at a time. The language model reads the whole row. Then it writes the answer, one token at a time, in the same way as it writes any text. Each word token can look at every patch token, so the word "mug" in the question can find the patches that contain the mug.

A point is written in the same way as any other answer, because the model writes the digits of the two pixel numbers as ordinary tokens. It learned to do this from training examples that had points written as text.

Moving on to how it is trained. A vision-language model is trained in stages, and each stage uses a different kind of data. The page has a table listing the five usual stages in the order they happen.

In stage one, the language model alone is trained on text from the public internet, books, and code.

In stage two, the vision encoder alone is trained on hundreds of millions of pictures from the internet, each with a caption. Stages one and two are usually done by someone else, because the builders of a vision-language model start from a language model and a vision encoder that already exist. In stage two, a common method trains the vision encoder to match each picture with its own caption and not with the other captions, which teaches it which picture patches go with which words.

In stage three, the projector, and then all parts together, are trained on pictures with captions and descriptions written by people or other models.

In stage four, all parts together are trained on pictures with questions and correct answers. This stage is the one that teaches the model to answer questions instead of only writing captions, and it is called instruction tuning.

Finally, stage five is for robots. All parts together are trained on robot camera pictures with questions, points, and success labels. This stage is optional, and it is what makes a robot vision-language model. General models are good at "what is in this picture?", but they are weaker at robot questions, such as "Where exactly is the handle?", "Did the grasp work?" and "How far through the task is the robot?" So robot laboratories add examples of exactly these questions, and the examples come from recordings of robots at work. People or other models then write the questions and the correct answers.

The next part lists well-known models of this kind. Many vision-language models exist, but these are the ones you will meet most often in robot work.

First is LLaVA, from 2023. It was an early open research model. It showed that a small projector between an existing vision encoder and an existing language model, plus some question-and-answer training, is enough to get a working vision-language model. So many later open models follow the same recipe.

Second is PaLM-E, from Google in 2023, which was one of the first to feed robot camera pictures into a large language model and use the answers to plan robot tasks.

Third is PaliGemma, from Google in 2024. It is a small open vision-language model, and it matters for robots because the vision-language-action model pi zero is built on top of it.

Fourth is Molmo, from the Allen Institute for AI in 2024. It is an open model that was trained to answer by pointing at places in the picture. Pointing is the kind of answer that a robot arm can use most directly.

Fifth is Qwen-3-VL, from Alibaba's Qwen team. It is a family of open vision-language models in several sizes.

Finally, Gemini Robotics ER 2, from Google DeepMind in July 2026, is a vision-language model trained for robot work. It plans, points, and watches video to check whether a step worked. Google reports 91.3 per cent success at finding the moment in a video when something happened, and 57.4 per cent at saying how far through a task a robot is. You use it through Google's online service; you cannot download it.

The page then gives a worked example of fetching the right mug. A single arm stands at a table with two mugs, a bowl and an apple, and a camera looks at the table from the front. A person then says: "Put my red mug in the bowl."

First, the robot finds the target. It sends the camera picture to the vision-language model with the question "Point to the handle of the red mug." The model answers with a point, in pixels.

Second, it turns the point into 3D. The robot reads the depth camera at that pixel, and with the camera's known position this gives a 3D point on the handle.

Third, it chooses the grasp and moves. A grasp model chooses how to hold the mug near that point. Ordinary motion planning moves the arm there, closes the gripper, and carries the mug over the bowl. The vision-language model is not used during the movement, because it is too slow.

Finally, it checks after each step. After each step, the robot asks the vision-language model: "Is the red mug in the bowl?" It asks the same question each time, and waits for "yes".

The diagram shows four camera frames of the mug being moved into the bowl, with the answers "no", "no", "no", and "yes" below them. The answer stays "no" while the mug is on the table, in the air, and on its way, and it turns to "yes" only after the mug is in the bowl. Checking whether a step worked is called success detection, and it is one of the most common uses of a vision-language model on a robot, because it replaces a check that someone would otherwise have to program by hand for every task.

If the answer is still "no" after the last step, the robot does not simply stop. It tells a planner what happened, and the planner writes the next steps.

The next section is about what goes wrong, and what people do about it. A vision-language model is good at "what" and weaker at "exactly where" and "exactly how much". There are several common failures, and a usual fix for each one.

First, it is not precise about position. A point from the model can be several pixels off, which can be enough to miss a small handle. The fix is to use the point only to choose the object, and then measure the object with a depth camera and a seeing model that outlines it exactly.

Second, it miscounts, and mixes up left and right. Counting many small objects, and telling left from right, are known weak points. Left and right are also ambiguous, because the camera's left may be the robot's right. The fix is to ask for points instead of words, and to do the counting and the left-right logic in ordinary code.

Third, it says things that are not there. Like a language model, a vision-language model can hallucinate, which means it describes an object that is not in the picture. The fix is to ask for a point, and then check with the depth camera that something is really there.

Fourth, it says "yes" too easily. For success detection, a wrong "yes" is worse than a wrong "no", because the robot moves on and the mistake is hidden. The fixes are to ask from two camera views, to ask the question in the opposite form as well, such as "Is the bowl empty?", and to back the answer with a measurement, such as the weight on a scale or how far the gripper closed.

Fifth, it misses small details. The picture is cut into patches, and a detail smaller than a patch, such as a thin crack or a lid that is almost closed, can be lost. The fix is to crop the picture around the object and ask again.

Finally, it is slow. A large model takes from a fraction of a second to a few seconds per answer. That is fine for "which mug?" and "did it work?", but it is far too slow to steer the arm while it moves.

The next part discusses why to use a vision-language model, and what it costs. A vision-language model reads a picture and a question, and answers in words or points. It lets a robot find an object from a description, and check its own work, without anyone writing a special program for each object or each task.

The obvious alternative is an object detector trained on a fixed list of object names. A detector is much faster, because it answers in milliseconds, where a vision-language model takes seconds. It is also more precise about position, small enough to run on the robot's own computer, and it always gives an answer in the same form. So if your robot only ever handles the same five kinds of object, a detector is the better choice. The next step up is an open-vocabulary model, which finds objects from any name, but still only answers "where is this?". The vision-language model earns its place when the question itself changes, as in "the mug that is upside down", "the one with the chipped rim", or "did the lid close?".

But it costs you speed, hardware and certainty in return. A useful model needs a large graphics card or a paid online service, and it answers in seconds, not milliseconds. Its answers are also not guaranteed, so anything that matters has to be checked with a measurement.

The next section covers the written alternative. There is no full written alternative, because no written program can answer a question that nobody planned for. But the two jobs a vision-language model does most on an arm do have written versions. To pick out an object by a fixed property, such as "the red mug", thresholding and colour masks is fast and exact, while to check that a step worked, a measurement is more reliable. Sensor streams turns how far the gripper closed, or the weight on a scale, into a clean yes or no.

The written way wins whenever the question is fixed and a colour or a sensor reading answers it. But the vision-language model wins when the question itself changes.

The page then suggests where to read next. It mentions the page on vision-language-action models, which takes a vision-language model and teaches it to output arm movements as well as words. The page on open-vocabulary models covers the smaller models that find objects from words. The page on language models as planners shows how the answers from this page are fed back into a plan. The page on models that find compares finding models in more depth, including when a large model is worth its cost. Finally, for the robot models built on vision-language models today, it suggests reading the page on foundation models and generalist policies.

The final section is about using it in Python. The worked example asked a vision-language model "Is the red mug in the bowl?" after every step. This section shows that same question being asked in Python. Of everything in this book, it is the easiest thing to try, because a pretrained vision-language model answers a question about a photograph with no training, no robot and no simulator. After this section you can point one at a picture on your own computer and read its answer.

The code uses the transformers library from Hugging Face, and its pipeline feature, which is the shortest route to a working model. A pipeline here is one object that holds the processor and the model together, so that you hand it a picture and a question and it hands you text.

The code imports the library, opens an image file representing the camera frame, and sets up a message containing the image and the text question, "Is the red mug in the bowl? Answer yes or no." It then passes this message and the image to the pipeline, and prints the generated text that comes back.

The pretrained model gives you the whole of the internal workings explained earlier: the vision encoder that cuts the picture into patches, the projector that makes the patches look like words, and the language model that reads them together and writes the answer. None of that is trained by you, and none of it is written by you.

What you write is everything around it. You capture the picture from the camera, you choose the wording of the question, you decide when to ask it, and you turn the text that comes back into something your program can act on. That last part matters more than it looks, because the model answers in words, so "Yes, the mug is in the bowl" and "yes" are both possible replies to the same question, and your code has to accept both.

What you decide is which model to run and where. A small model such as the one in the code has 256 million parameters, so it runs on an ordinary computer with no graphics card, and it is often good enough for a yes-or-no check. A larger open model, or a paid online service, answers more accurately and points more precisely, but it needs a graphics card or money for every question. You also decide what to do about the failure where the model says "yes" too easily, because no choice of model removes that, and only a second question or a real measurement does.
