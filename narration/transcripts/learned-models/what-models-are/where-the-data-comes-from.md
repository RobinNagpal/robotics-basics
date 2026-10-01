Where the data comes from. 

A model learns from examples, and the three pages before this one were about what happens to those examples. The page on how a model learns showed how the numbers inside a model are changed, one example at a time. The page inside a neural network showed what those numbers sit in, and the page on learning signals showed the kinds of learning. So this document answers the question that comes before all of them: where do the examples come from?

It is for a complete beginner, so you do not need to know anything about machine learning. You only need to remember one idea from the earlier documents: a model is shown many examples, each with a question and the right answer, and it slowly changes its numbers until its own answers match the right ones.

By the end you will know the five main places that robot data comes from, and you will know what "pretraining", "fine-tuning" and "foundation model" mean. You will also have a rough idea of how much data each kind of model needs.

The first section explains why the data matters so much. A model only knows what its examples showed it. For example, suppose every training picture shows a white mug on a wooden table. The model may then learn "a white thing on brown wood" instead of "a mug", and if you show it a blue mug on a grey table, it can fail.

So the examples must look like the jobs the robot will really do, which means they must cover the different colours, shapes, lights and positions the robot will meet. A set of examples used for training is called a dataset.

Each example in a dataset is made of two parts. The first part is what the model is given, such as a picture, and this is called the input. The second part is the right answer, such as the word "mug", and this is called the label, or the target.

Getting inputs is usually easy, because a camera takes thirty pictures every second. Getting the right answers is the hard part, since somebody, or something, has to supply them. So each section below is a different way of supplying them.

The next part of the page is about labelled pictures. The oldest way of supplying answers is also the simplest one. A person looks at each picture and writes down the answer, and this is called labelling, or annotation, while the person doing it is an annotator.

The answer can take several forms, depending on what the model must learn. First, it could be a single word for the whole picture, such as "mug". Second, it could be a box drawn around each object, with a name on each box. Third, it could be an exact outline of each object, traced pixel by pixel. Finally, it could be a few marked points, such as the rim and the handle of the mug.

Each form takes longer than the one before it. A person can give a word to a picture in a second or two, while tracing the exact outline of every object in a busy kitchen picture takes much longer. So outline datasets are usually much smaller than word datasets.

A famous example is ImageNet, which is a dataset of about 1.2 million training pictures, each labelled with one of 1,000 names, such as "coffee mug" or "golden retriever". People labelled it by hand, and for many years it was the standard test for models that recognise pictures.

Labelled pictures are how most seeing models are trained. Their weakness is cost, because every label costs a person's time, and a new object or a new kind of answer means labelling again.

The next section covers human demonstrations. A seeing model answers "what is in this picture?", but a movement model answers a different question: "what should the arm do next?". No one can easily write that answer down by hand, so instead a person shows the robot what to do, and this is called a demonstration.

The most common way to demonstrate is teleoperation, a word that means "operating from a distance". The person does not push the robot itself, but moves a controller instead, and the robot copies the controller's movements.

A popular kind of controller is a small second arm, called the leader arm, and it has the same joints as the real robot, which is called the follower arm. The person moves the leader arm by hand, while the computer reads the leader's joint angles many times a second and sends the same angles to the follower. Other controllers include a game controller, a virtual reality headset with hand controllers, and a handheld gripper that the person carries around.

The page shows a diagram of one demonstration being recorded. A person moves a leader arm, the robot copies it, and each moment is saved. At each moment the computer saves two things together: what the camera saw, and what the arm did at that moment.

While the person works, the computer records everything at each moment. First, it records the pictures from every camera. Second, the angle of every joint. Third, whether the gripper is open or closed. And finally, the command that was sent to the arm.

One complete recording of one task, from start to finish, is called an episode. For example, one episode might be "pick up the mug from the left of the table and put it on the plate", and it might last twenty seconds.

Later, a movement model is trained on many episodes. It is shown the picture at each moment, and the right answer is the command the person gave at that moment. The model then learns to give the same command when it sees a similar picture, and copying a person like this is called behaviour cloning. This is explained more fully on the page about behaviour cloning.

Demonstrations have one big strength, which is that they are real. The pictures come from the robot's own cameras, and the movements are movements the robot can actually make.

They also have one big weakness, which is that they are slow to collect. A person must sit at the controller for every episode, so one person can record only so many episodes in a day. The document on data and demonstration describes the rigs people use and what they cost.

The next source of data is simulation. Demonstrations are slow because a person has to make every one of them, so the next source removes the person altogether. A simulator is a program that pretends to be the real world, and it holds a 3D model of the robot, the table and the objects. It works out how they move when the robot pushes them, using the rules of physics, and it can also draw what a camera would see.

A simulator can make data very fast, because it can run many copies of the same scene at once, it never gets tired, and it never breaks a real mug. It also knows every right answer for free, because it placed every object itself, so it knows exactly where the mug is, where its handle points and which pixels belong to it. This means that nobody has to label anything in a simulated picture.

A simulator can also let a robot practise a task over and over. The robot tries something, the simulator says whether it worked, and the robot tries again, many thousands of times. Learning by trying like this is called reinforcement learning, which is explained on the reinforcement learning page.

The page then explains the gap between simulation and the real world. A simulator is never exactly like the real world. Its pictures look a little too clean, its light falls a little differently, and its mug slides a little differently from a real one, because real friction is hard to copy exactly.

A model trained only in simulation learns these small differences as if they were true, so when it meets the real world it does worse than it did in simulation. The difference between how a model does in simulation and how it does in the real world is called the sim-to-real gap.

The most common fix for that gap is called domain randomisation. Here "domain" means the look and feel of the world the model is trained in, and "randomisation" means changing that look at random.

Instead of making one simulated world as close to the real one as possible, you make thousands of different ones. In each training picture, the computer picks the table colour, the mug colour, the brightness of the lamps, the camera position and the other objects at random. It can also change the weight of the mug and how slippery the table is.

The page shows a diagram of eight simulated pictures with random colours alongside one real picture. The eight pictures on the left are all simulated, and no two look alike. The real picture on the right looks different again, but the model has already learned to ignore colour and light.

The model cannot rely on any one colour or lamp, because they keep changing. The only thing that stays the same in every picture is the shape of the mug, so the shape is what the model learns. To such a model, the real world then looks like just one more random variation.

Domain randomisation has a cost of its own, however. The model must learn to cope with far more variety than the real job needs, so it needs more training. It also cannot fix every difference, because physics that the simulator gets badly wrong, such as cloth or liquids, stays wrong however much you randomise it. The simulation and evaluation document describes the other fixes people use today.

The next section is about internet-scale data. Simulation is cheap but never quite real, so the next source is real data that nobody collected for robots. The internet holds billions of pictures, videos and pages of text, and many of the pictures come with a few words next to them, such as a caption under a photo or the text of a web page. Those words are a kind of label that nobody had to write for the purpose of training.

A well-known model called CLIP was trained on 400 million pairs of pictures and captions collected from the internet. It learned to match a picture with the words that describe it, and it was never told "this is a mug" in the careful way ImageNet was. Instead it worked that out from millions of loosely matched pictures and captions. The open-vocabulary models page explains how robots use models like it.

Text on its own is also data that models learn from. Large language models, which the language models chapter covers, learned from huge amounts of text written by people.

Internet data has three clear strengths as a source. There is an enormous amount of it, it covers almost every everyday object and word, and it costs very little to collect.

It also has two weaknesses that matter for robots. It is messy, because many captions are wrong or unrelated to the picture, and it contains almost no robot actions. So the internet can show a model what a mug looks like and what the word "mug" means, but it cannot show the model how this particular arm should move its joints to pick the mug up.

The next part of the page explains self-supervised learning. The methods above all need somebody to supply the right answer, whether that is a person, a simulator or a caption writer. Self-supervised learning is a trick that makes the right answer come from the data itself.

Here is the first example, which uses a picture. Take a picture and cover some patches of it with grey squares, then ask the model to guess what was under them. The right answer is the part of the picture you covered, so you already have it, and no person had to label anything.

To guess well, the model must learn what things usually look like, such as that a mug handle is curved and that a table edge is straight. That knowledge is useful later for other jobs, such as finding mugs.

Here is a second example, which uses text instead. Take a sentence, hide the next word, and ask the model to guess it. For example, "Put the red mug in the..." The right answer, "sink", was in the sentence all along. Large language models learn mainly in this way, one word at a time.

A third example uses video instead of still pictures. Show the model the first frames of a clip and ask it to guess the next frame, and the real next frame is the right answer. World models are often trained like this.

The name "self-supervised" means that the data supervises itself, because it supplies both the question and the answer. This matters because it means any picture, any video and any text can be used, not only the ones a person has labelled.

The next section is about pretraining, then fine-tuning. Now that you have seen the five sources, this section says how they are used together. Most models used on robots today are not trained in one go, but in two separate steps.

The first step is pretraining, in which a model is trained on a very large, general dataset, often from the internet and often with self-supervised learning. It learns general things: what objects look like, what words mean, and how things usually move. Pretraining is expensive, because it can use many powerful computers for weeks, so usually a large company or a research lab does it once and then shares or sells the result.

The second step is fine-tuning, in which you take the pretrained model, with all the numbers it has learned, and train it a little more on a small dataset for your own job. For a robot arm, this small dataset is often a few hundred demonstrations recorded on your own robot. Fine-tuning changes the numbers only a little, so it is much cheaper than pretraining, and it can often run on one computer in hours or days.

The page shows a diagram of pretraining on a large general pile of data, then fine-tuning on a small pile of robot data. The same network appears twice in the picture. Fine-tuning keeps what pretraining learned and changes only a small part of it, shown by red lines.

This two-step method works because most of what the robot needs is general. Knowing what a mug looks like, from any angle and in any light, is the same skill for every robot, and only the last part, how this arm moves to this mug, is special to your robot. So the expensive general part is learned once, from cheap general data, while the cheap special part is learned from a little expensive robot data.

An everyday example is a person who already speaks English and starts a new job in a kitchen. They do not need to learn English again, so they only need to learn where the pans are kept and how this kitchen does things, which takes days rather than years.

The next part of the page explains what a foundation model is. A foundation model is a large model pretrained on a very large, broad dataset, so that many different jobs can be built on top of it by fine-tuning or by simply asking it. The name was made popular by a 2021 report from Stanford University, and it is called a "foundation" because other models and products are built on it, the way a house is built on its foundation.

For example, CLIP is a foundation model for pictures and words, and the large language models behind chat assistants are foundation models for text. In robotics, people now build vision-language-action models, which take in camera pictures and a spoken or typed instruction and give out arm movements. They usually start from a foundation model for pictures and words, and are then trained further on large collections of robot demonstrations. The vision-language-action models page explains them. The foundation models document lists the ones that exist in 2026.

One large robot dataset shows how these collections are built. Open X-Embodiment gathered more than a million robot episodes from 22 different kinds of robot, which many labs had recorded separately. Pooling them gave one dataset large enough to pretrain on.

Being a foundation model does not make a model always right, because it only means that the model starts from a broad base. So it still needs to be tested on your robot, and it still often needs fine-tuning.

The next section is about how much data each kind needs. The amount of data a model needs depends on the job and on whether it starts from a pretrained model, and exact numbers vary a great deal from one model to the next. The page includes a table giving rough sizes to show how the kinds compare. 

It shows that labelled pictures for a new seeing model trained from scratch need hundreds of thousands to millions of pictures. However, fine-tuning a pretrained seeing model on your objects only needs hundreds to a few thousand pictures. Demonstrations for one task on one robot need tens to hundreds of episodes, while pretraining a general robot model needs hundreds of thousands to millions of episodes from many robots. Simulated examples are used in the millions or more because they are cheap. Finally, internet pictures, captions, text and video are used in the hundreds of millions or more to train foundation models.

Two patterns stand out from the numbers in the table. First, cheap data is used in huge amounts, and expensive data is used in small amounts. Second, fine-tuning a pretrained model needs far less data than training from nothing. That is the main reason pretraining is so widely used.

The next part asks, why not just collect robot data? The obvious alternative to all of this is simple: record lots of real demonstrations on your own robot, and train on nothing else. Real data is exactly right for the real job, with no sim-to-real gap and no messy captions.

For one narrow task, this approach really does work. Some movement models learn one task, such as putting a battery into a slot, from about fifty demonstrations recorded on that robot.

But it stops working as soon as you want variety. To handle every mug, every table and every kitchen, you would need to demonstrate on every one of them, and a person can record only so many episodes in a day. So people mix the sources: internet data and self-supervised learning for general knowledge, simulation for volume, and real demonstrations for the final, exact skill.

That mix of sources has costs of its own. Pretrained models are large, and large models are slower to run on a robot, which is what the next chapter, Running a model on a robot, is about. You also depend on whoever did the pretraining, and on the licence they chose. And a model built from many sources is harder to understand when it fails, because you did not see most of the data it learned from.

The page then lists where to read next. The next document is about running a model on a robot, and it explains what happens after training, when the model is used. The map of models then shows every kind of model in this book and what data each one uses. The page on how a model learns explains what the model does with each example. For much more detail on teleoperation rigs and open robot datasets, there is a document on where manipulation data comes from. For simulators and the sim-to-real gap, there is a page on simulation, world models and evaluation. Finally, the page on learned methods for one arm shows how these kinds of data are used to teach one arm a task.

The final section is about using it in Python. This page was about where examples come from, and the earlier section said how many of them each kind of model needs. There is one line of Python that decides whether the test score you get from those examples means anything at all, and this section is about that line. It shows the shape of the idea rather than a technique, because splitting data is something you do before any model is chosen.

Robot data arrives as demonstrations, and one demonstration is hundreds of frames recorded a few milliseconds apart. Neighbouring frames look almost identical, so if you split the frames at random, nearly every test frame has an almost identical twin in the training set. The model then scores well on the test set without having learned anything that transfers to a new demonstration.

The page shows a short Python script using the scikit-learn library. First, it shows the wrong way to split robot data, where frames of one demonstration land randomly in both the training and testing sets. Then it shows the right way, using a function called GroupShuffleSplit. It uses an identifier to say which demonstration each row came from, ensuring that whole demonstrations go entirely to the training side or entirely to the testing side.

Both functions come from scikit-learn, which is the standard Python library for the older machine learning methods and is described in chapter 2. Here it is used only for the split, which works the same whether the model that follows is a random forest or a neural network. The code fixes the random shuffling so the same split comes back every time you run the script, and that is what lets you compare two models fairly.

The library gives you the shuffling, the proportions, and the guarantee that no demonstration identifier appears on both sides. It also gives you other functions for the same idea repeated several times over.

What you have to collect is the data itself, and what you have to record is the demonstration identifier. That is the part people forget, because once the frames from many demonstrations have been stacked into one array without a column saying which recording each came from, nothing can recover it afterwards. The same applies to the simulated data discussed earlier, where the group is usually one randomised scene rather than one demonstration.

What you have to decide is what a group means for your job. If the arm was taught by three different people, you may want to test on a person the model has never seen. If it worked in four bins of parts, testing on an unseen bin tells you more than testing on unseen frames. As mentioned earlier, robot data is expensive, and a split like this is how you get an honest answer out of the little you have.
