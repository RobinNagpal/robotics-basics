Image classification. This page explains the simplest seeing model, which is one that looks at a whole picture and gives it one name. It answers five questions: what such a model does, what goes in and what comes out, how it works inside, how it is trained, and when it is the right choice for a robot arm.

It is written for a reader who has already read the seeing models overview and the first chapter of this book, but you do not need to know any machine learning, because every term is explained where it first appears.

This page comes first in the chapter for a reason, since nearly every other seeing model contains an image classifier, or most of one. So the ideas here come back on every later page.

The first section explains what it is. An image classifier is a model that looks at a picture and says which one of a fixed list of names fits it best.

That fixed list is chosen before training, and each name on the list is called a class. A class can be a kind of object, such as a mug, a bowl, or a bottle, and it can also be a state, such as gripper empty or gripper holding something.

Here is an everyday example. Imagine a sorting machine for fruit, where a camera takes a photo of each piece of fruit on a belt. A person could look at each photo and say apple, orange, or lemon. So an image classifier does the same, because it looks at the photo and picks one of the three names.

The classifier gives one name for the whole picture. So it does not say where in the picture the object is, and it does not say how many objects there are either. If a photo shows two apples and an orange, a classifier still gives just one name. The object detection page covers models that find each object separately.

The next part of the page covers what goes in and what comes out.

The input is one picture, and to a computer a picture is simply a grid of numbers. Each small square of the grid is a pixel, and a grey picture has one number per pixel, which says how bright that pixel is. So the number zero means black, and the number 255 means white. A colour picture has three numbers per pixel instead, one for red, one for green, and one for blue.

The first diagram on the page shows a tiny grey picture of a mug becoming a list of numbers. The left part is the picture, 12 pixels wide and 12 pixels high, while the middle part enlarges a red square in one corner and writes each pixel's number in it. The right part is what the model is actually given, which is the same numbers, one row after another.

A real camera picture is much bigger than that. For example, a picture 640 pixels wide and 480 pixels high has 307,200 pixels, and with three colour numbers each, that is 921,600 numbers. So most classifiers first shrink the picture to a fixed size, often a square about 224 pixels wide, so that every picture gives the same count of numbers.

The output is one score for each class, where a score is a number between zero and one. So a higher score means the model is more sure that the class fits. The scores for all the classes add up to one, and the answer is the class with the highest score.

The second diagram shows a picture of a mug going in, and five scores coming out, which is one score per name. The numbers in this picture are an example rather than real output. In the example, mug has the highest score, at 0.81, so the answer is mug, while the second-highest score is for cup, which is a similar object. This is typical, because a classifier that is wrong is usually wrong in favour of a similar-looking class.

On a robot arm, the input is usually one picture from the camera, or a small part cut out of it. Then the output is used as a yes-or-no check, or to choose what to do next.

The next section explains how it works inside.

A classifier is a neural network, and it is built in layers. This means that each layer takes a grid of numbers in, does simple sums on it, and passes a new grid of numbers on to the next layer. This is explained more fully on the page about what is inside a neural network, while this section explains what the layers of a classifier do in particular.

The most common kind of classifier is a convolutional neural network, or CNN, and a CNN works in these steps.

First, the first layer slides a small square, often 3 pixels by 3 pixels, across the whole picture. At each place, it multiplies the 9 pixel numbers by 9 fixed numbers and adds them up, and this sliding sum is called a convolution. The 9 fixed numbers are called a filter, and the layer has many filters, so each one gives its own new grid.

Second, some filters give a large number where there is an edge in the picture, so one filter reacts to flat edges, another reacts to upright edges, and another reacts to curves. Nobody chooses these filters by hand, because training finds them.

Third, every few layers, the grid is made smaller. For example, each square of 2 by 2 numbers is replaced by the largest of the four, which keeps the important numbers and throws away where exactly they were.

Fourth, the next layers do the same thing again, on the smaller grids, and because they combine edges, their filters react to parts, like a round rim, a handle loop, or the neck of a bottle.

Fifth, the last layers then combine those parts, so their numbers react to whole objects, like a mug, a bottle, or a bowl.

Finally, at the very end, one small layer turns those numbers into one score per class, and a last step makes the scores positive and makes them add up to one.

The diagram here shows this build-up, from early layers reacting to edges, to middle layers reacting to parts, and last layers reacting to whole objects. The drawings in the tiles show the kind of pattern that makes each layer give a large number. Researchers have looked inside trained networks, and they found this same order again and again.

A newer kind of classifier is the vision transformer, or ViT, which cuts the picture into small squares, called patches, often 16 pixels by 16 pixels. Then it turns each patch into a list of numbers. After that, each patch's numbers are updated by looking at all the other patches, and this step is called attention. After many such layers the model gives the scores. A vision transformer needs more training pictures than a CNN, but with enough pictures it is often more accurate.

The part of the network before the last layer is called the backbone, while the last layer, which gives the scores, is called the head. This split matters, because a backbone trained for classification has learned edges, parts, and objects, so other seeing models can reuse that backbone and change only the head.

The next section is about how it is trained.

Training needs many pictures, and each picture needs a label, which is the correct class written down by a person.

The most famous collection of labelled pictures is ImageNet, and the part of it used in a yearly research contest has about 1.2 million training pictures, split into 1,000 classes. Those classes include many animals and everyday objects, such as coffee mug, water bottle, and screwdriver.

Training itself then works in five steps. First, the network starts with random numbers in its filters, so its answers are random too. Second, it is shown a small batch of pictures, for example 32 of them. Third, for each picture it gives its scores, and a program then measures how wrong they are, where the answer counts as very wrong if the correct class got a low score. Fourth, the program nudges every filter number a tiny amount, in the direction that makes the answers less wrong. Finally, this repeats with the next batch, and so on, many times through all the pictures.

This nudging is explained in more detail on the page about how a model learns.

Training from nothing on ImageNet takes many hours on many graphics cards, so a robot project almost never does that. Instead it starts from a network that someone else already trained on ImageNet, replaces the head with a new one for its own classes, such as gripper empty and gripper holding something, and then trains a little more on its own pictures, which is called fine-tuning.

Fine-tuning works with far fewer pictures, often a few hundred per class, because the backbone already knows edges and parts, and those are the same in every picture. So only the head has much left to learn. Book 2 shows the same idea for a detector in the section on why 80 pictures are enough for fine-tuning.

The next part of the page lists well-known models. It helps to see those ideas in real classifiers, and these are ones that people use or build on. Each of them is also used as a backbone inside other seeing models.

First is AlexNet. It was a CNN that won the ImageNet contest in 2012 by a wide margin, because it showed that neural networks trained on graphics cards beat hand-written methods for pictures. Few people use it today, but it started the change.

Second is ResNet, a CNN from Microsoft Research from 2015. It added skip connections, which pass a layer's input straight on to a later layer. These made it possible to train much deeper networks, so ResNet is still a common backbone.

Third is MobileNet, a family of small CNNs from Google. They are built to run fast on phones and small computers, so they suit a robot with no graphics card.

Fourth is EfficientNet, a family of CNNs from Google that comes in many sizes, from small and fast to large and accurate, so you can pick one that fits your computer.

Fifth is ViT, the vision transformer, which came from Google in 2020. It showed that a transformer, first built for text, also works well on pictures.

Finally, ConvNeXt is a CNN from Meta that copied design ideas from transformers, and it showed that a CNN built in the modern way can match them.

The next section covers where image classification is used on a robot arm.

A classifier is useful on an arm when the question has one answer for the whole picture, so here is a worked example of exactly that.

A robot arm picks cups from a shelf and puts them in a dish rack. However, the gripper sometimes closes and misses the cup, and the arm should notice this before it moves to the rack.

First, a small camera on the wrist points at the gripper fingers. Second, after the gripper closes, the program takes one picture. Third, a classifier with two classes looks at the picture: holding a cup, and empty. Fourth, if empty gets the higher score, the arm opens the gripper and tries again. Finally, if holding a cup gets the higher score, the arm moves to the rack.

To build this, a person records a few hundred pictures of each case, including different cups, different light, and different places on the shelf. Then they fine-tune a small network, such as a MobileNet, on those pictures.

There are other common uses on an arm. One is checking whether a task worked, for example by asking if the drawer is open or closed. Another is sorting parts into bins by kind, when a camera sees one part at a time. It is also used for checking the quality of a part, which means answering good or scratched. Finally, it is used for naming an object that another model has already found, because a detector finds a box, and the program can cut out that box and give it to a classifier trained on finer classes, such as ten kinds of screw.

The next section explains what goes wrong. Simple as it is, a classifier can fail in several ways, and each one has a common fix.

First, it always picks a class, even when none of them fits, so if you show a mug-or-bowl classifier a photo of a shoe, it still says mug or bowl. The fix is to add a class such as something else and train it on many unrelated pictures. Instead, you can refuse any answer whose top score is below a chosen number, such as 0.7, and that chosen number is called a threshold.

Second, it can learn the background instead of the object. Suppose every holding-a-cup picture was taken in the morning and every empty picture in the afternoon. The network might then learn the light rather than the cup. The fix is to vary the light, the background, and the place in both classes when you collect the pictures.

Third, it fails on pictures that look different from its training pictures, so a classifier trained on clean photos may fail when the camera lens is dirty or the light is dim. This problem is called a domain gap, and the fix is to include such pictures in training. People also change their training pictures on purpose, making copies that are darker, blurred, or slightly turned, which is called data augmentation.

Fourth, the score is not an honest chance, because a score of 0.95 does not mean the model is right 95 times out of 100, and networks are often too sure of themselves. The fix is to test the model on pictures it did not train on, and to choose the threshold from what you measure there.

Finally, it cannot say where or how many, so if the picture holds two objects the answer is still one name. When where or how many matters, you need object detection instead.

The next part of the page discusses why you would choose classification, and what it costs.

Now that you have seen what a classifier does and where it fails, this section answers the four questions for it: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

It is a network that gives one name to one picture. So it gives you a yes-or-no check, or a choice among a few states, from a single picture.

The obvious alternative is a hand-written rule, for example, if more than 500 pixels in the gripper area are white, a cup is there. Rules like this are quick to write and need no training pictures, but they break when the cup is a different colour, or when the light changes. A classifier trained on varied pictures keeps working in those cases. So choose a rule when the scene is controlled and simple, and choose a classifier when it varies.

The other alternative is a detector, which also names objects and says where they are. However, a detector needs a box drawn around every object in every training picture, which takes much longer to label, and it is also bigger and slower. So if you only need one answer for the whole picture, a classifier is simpler and cheaper.

The costs are these. You need a few hundred labelled pictures per class, taken in the conditions the robot will actually meet. Then you also need a computer that can run the network, although a small classifier runs well without a graphics card. Finally, you must accept that it will sometimes be wrong, so the robot needs a safe action for a wrong answer, such as simply trying again.

The next section is about the written alternative.

A trained network is not the only way to answer a yes-or-no question about a picture, because Book 5 answers some of them with a written rule. The page on thresholding and colour masks explains how to check that the gripper holds something, by counting the depth pixels nearer than the fingertips. The page on edges and contours explains how to name the shape of a flat part, such as a triangle or a hexagon, by counting the corners of its outline. The written rule wins when the scene is controlled and the answer depends on one thing you can measure, such as a height, a colour, or a number of corners. The classifier wins instead when the answer depends on how things look in general, such as scratched or good, or when the light and the objects vary.

The page then suggests where to read next.

The next page is object detection, which adds boxes, so that the robot knows where each object is. The page on segmentation goes one step further and marks the exact pixels of each object. The page inside a neural network explains layers and sums in more detail. The page on how a model learns explains training. The seeing models overview compares all seven kinds of seeing model. Finally, Book 2's section on models that find objects lists backbones you can download, with their licences.

The final section is about using it in Python.

The page has explained the backbone, the scores, and the fine-tuning that every other seeing model reuses. This section runs a real classifier, because it is the shortest piece of model code in the whole book. After reading it you will be able to get names and scores for a picture in three lines, and you will see why a classifier alone is rarely enough for a robot arm.

The code uses a helper called a pipeline from the Hugging Face transformers library. This pipeline puts the preparation of the picture, the network, and the reading of the scores behind one call. The code imports the pipeline, then sets up a classifier using a ResNet-50 model. It passes an image file to the classifier, and because the answers come back sorted with the most likely first, it loops through the top three guesses and prints the label and the score for each one.

What the pretrained model gives you out of the box is the 1,000 classes of ImageNet, which are mostly animals, plants, and everyday things. The pipeline also does the small steps that are easy to get wrong, because it resizes the picture to 224 by 224 pixels, subtracts the mean and divides by the standard deviation that this model was trained with, turns the scores into numbers that add up to one, and sorts them. Those steps are why a wrong answer is so often a preparation mistake rather than a model mistake, and here you cannot make it.

What you still have to write yourself begins with the fact that a classifier says nothing about where. It gives one name for the whole picture, so on a robot arm it is useful only when you have already cut out one object, for example from a box a detector gave you, or when the camera always sees exactly one part in a fixture. Cropping the picture to that one object is your code, and so is everything the name is then used for.

What you have to decide is how many of the sorted guesses to trust and how low a score you will accept. A classifier always names something, because it must choose one of its classes, so a picture of a brake disc gets a confident wrong answer rather than no answer. So you set a score below which you treat the answer as unknown. You also decide whether to fine-tune, and for a robot the answer is almost always yes, because your classes are your own parts and not the 1,000 classes of ImageNet.
