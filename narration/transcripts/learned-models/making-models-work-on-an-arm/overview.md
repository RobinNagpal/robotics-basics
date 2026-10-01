Making models work on an arm.

The seven chapters before this one each describe a family of models, including what they take in, what they give back, and how they are trained. This chapter is about what happens after that, because having a model is not the same as having a working robot. You have a model that works in a notebook, which here means a program on a computer that is right on a set of test pictures, and the question this chapter answers is how you get from there to a model that works on a real robot arm, every day.

This page is the chapter overview. It says what the chapter is for, lists its four pages in their two groups, and then says how the chapter connects to the frontier pages in Book three. It is for a reader who has read the first chapter of this book about what models are, and at least one of the family chapters. You should know what training, a test set, and fine-tuning mean. If you do not, the pages on learning signals and where the data comes from explain them.

The first section explains what this chapter is for. A model that works in a notebook has passed exactly one test, because it gave the right answers on pictures that were deliberately kept back from training. That is a good start, however it is only a start, since a robot arm asks much more of a model than a set of held-back pictures ever does.

On an arm, the model sees your objects, in your light, from your camera, and it may never have seen any of those during training. It must also answer within a fixed time, many times a second, while the arm is still moving. When it is wrong, the arm does something in the real world, so a wrong grasp can break a mug or hit a person, which is a cost that a wrong answer in a notebook never carries. Finally, it must keep working long after the first good demonstration, on the hundredth try and on a different day.

So the gap between a model working in a notebook and working on the arm is really four separate questions. First, does the model know your objects? Second, is it fast enough, and does it fit into the robot's loop? Third, does it really work, and how does it fail? And finally, does it know when it is unsure? Each page of this chapter answers one of them.

The next part of the page introduces the four pages. The page includes a diagram showing four boxes in a row, representing the steps between a model that works in a notebook and one that works on the arm. These steps are fine-tuning, running a model on a robot, evaluation and failure, and finally, uncertainty and confidence. The diagram shows these in the order a project usually meets them, and a model has to pass all four before the arm can rely on it.

Like every chapter in this book, this one splits its pages into two groups. The most-used group holds the steps that nearly every project with a model on an arm goes through, whereas the also-used group holds a step that many projects need but not all of them. 

The page provides a table listing the four pages and the questions they answer. There are three pages in the most-used group. The first is fine-tuning, which answers how to teach a downloaded model your own objects and your own robot, using a small amount of your own data. The second is running a model on a robot, which answers how fast the model must be, what computer it runs on, and how it fits into the loop that drives the arm. The third is evaluation and failure, which answers how to measure whether the model really works on the arm, and how to find and sort the ways it fails. There is one page in the also-used group, called uncertainty and confidence. It answers how the robot can tell when the model is unsure, and what it should do then.

The three most-used pages follow one model through a whole project, so they are best read as one story. Fine-tuning adapts the model to your objects, then running it on the robot puts it inside the loop that drives the arm, and evaluation finally checks whether the result is good enough while showing you where it breaks. The also-used page then adds one more safeguard, because it lets the robot stop, look again, or ask a person when the model is not sure, instead of acting on a guess.

The next section explains in what order to read them. Since the three most-used pages follow one model through a project, you should read them in order, and each one also uses the words that the page before it introduced. Fine-tuning comes first because adapting a downloaded model is usually the first thing a project does to it, and evaluation comes last because you can only measure a model once it is already running on the arm.

Read the uncertainty page when your robot must decide by itself whether to act on an answer, which is the case for most robots that work near people or handle objects that break. It builds on the fifth section of the page about running a model on a robot, which shows that a model can be sure and wrong at the same time.

If you use only written techniques and no learned models, then you do not need this chapter at all. Book five covers those techniques instead, and its safety monitoring page is the written check that sits around any model as well.

The next part of the page covers how this chapter connects to Book three. This chapter explains ideas rather than current results, so it has a partner elsewhere in the documentation. Book three's frontier chapter records what actually happened to robot arm manipulation in 2026, including which models exist, which data they were trained on, and how they were measured. This chapter explains the ideas you need in order to read those pages, whereas those pages tell you what is true today.

Each page here has a partner there. First, fine-tuning explains how to adapt a model. Its partner pages are the foundation models document, which lists the large models you might adapt and download, and the data and demonstration document, which describes how demonstrations for fine-tuning are recorded. 

Second, running a model on a robot explains why speed and computer matter. Its partners are the hardware document, listing the computers people actually put next to an arm, and a page on working without a graphics card, which says what runs on a laptop. 

Third, evaluation and failure explains how to measure a model. Its partner is the simulation and evaluation document, which lists the benchmarks people report and explains why two published numbers are often not comparable. 

Finally, uncertainty and confidence has no single partner page, but the frontier overview's section on how to read a claim applies the same caution to published results that this page applies to one model's answer.

For where to read next, fine-tuning is the first page of this chapter. The map of models shows where this chapter sits in the whole book, and the frontier overview in Book three is where to go for the models, data, and results that are current today.

The final section of the page is about using it in Python. The four questions discussed earlier are each answered by their own page, so this section shows the few lines of code they all sit around: loading a trained policy, asking it once, and timing how long the answer took. 

The page shows a short Python script. It starts by importing the time module, PyTorch, and a policy class from the LeRobot library. It then downloads a trained policy from the Hugging Face Hub using a pre-trained method, and sets the policy to evaluation mode. Next, it builds an observation dictionary from the robot's cameras and joint sensors. The page notes that each value in this dictionary must be a PyTorch tensor with a batch dimension in front, even for just one picture. After setting up the observation, the script starts a timer. It tells PyTorch not to track gradients, asks the policy to select an action based on the observation, and finally prints how many milliseconds that one answer took.

LeRobot gives you the policy class and the weights. Downloading it gets the trained numbers and the settings they were trained with. Asking it to select an action hands back one movement per call. Even for a policy that predicts a whole chunk of movements at a time, it keeps the rest of the chunk and gives them out one by one. Because LeRobot changes quickly, you should check the import path in its own documentation against the version you install.

What you have to write yourself is everything around those few lines. You build the observation dictionary from your own cameras and joints, in the shape the policy was trained on. You also write the safety checks, the trial log, and what the arm does when the model is wrong, because none of that comes with the model. 

What you have to decide is what each of this chapter's four pages is about. Fine-tuning decides whether this downloaded policy needs teaching your objects first. Running a model on a robot decides whether the milliseconds that the script prints are small enough for your loop, and on which computer. Evaluation and failure decides how many real trials it takes before you believe the policy works. And uncertainty and confidence decides when the arm should not act on the action at all.
