How a model learns.

The previous page said that a model is a function learned from examples, and that a neural network is a model made of weights. This page answers the next question: how does a computer program find the right weights?

It follows one small example, a model that tells a mug from a bowl in a photo, through every step of training. Because that example is a small one, it uses no maths beyond adding, multiplying and reading a graph.

By the end you will know the words that every later page uses: example, label, loss, gradient descent, learning rate, epoch, training set, test set, overfitting, underfitting and checkpoint.

Before this page, it helps to have read about least-squares fitting, which finds the two numbers of a line by making the sum of squared errors as small as possible. Training a model does the same job for many more numbers.

The first section covers examples and labels. Training starts with a pile of examples, and for the mug-or-bowl model one example is one photo from the arm's camera.

Each example needs the right answer written next to it, and that right answer is called the label. For a photo of a mug the label is "mug", and for a photo of a bowl the label is "bowl". Usually a person looks at each photo and types the label, so this work is called labelling, and it is often the slowest part of the whole job.

A pile of examples with their labels is called a dataset. A small dataset for a job like this might have a few hundred photos, while a large public dataset can have millions. For example, ImageNet, a dataset that many seeing models learned from, has about 1.2 million training photos sorted into 1,000 kinds of object.

The label must match what you want the model to output. So if you want the model to draw a box around the mug, each label must be a box drawn by a person. In the same way, if you want the model to move the arm, each label must be the arm movement that a person made. 

Learning from examples that have labels is called supervised learning, because the labels supervise the model in the sense that they tell it the right answer every time. Most models in this book are trained this way.

The next part explains that the first guess is random. The weights are what the model has to get right, so training has to start them somewhere. Before training, the model's weights are set to small random numbers. A model with random weights still gives an output for every photo, because it is still a fixed calculation, but the output has nothing to do with the photo. It might, for example, give "mug" a score of 0.40 and "bowl" a score of 0.60 for a photo of a mug.

Training is the process of changing the weights until the outputs are right, and it repeats the same four steps. First, show the model one example. Second, let the model make its guess. Third, measure how wrong the guess is. And finally, change the weights a little, so that the guess would be a little less wrong.

The diagram on the page shows one training step. It shows an example of a mug, where the model gives the mug a score of only 0.40. A measurement called the loss shows how wrong that is, giving a value of 0.92. After each weight is changed a little, the same photo would score 0.46 for "mug", with a smaller loss of 0.78.

The first two steps are only the model doing its normal calculation, so the next two sections explain measuring the loss and changing the weights.

This brings us to measuring how wrong a guess is, which is the loss. To improve a guess, the program first needs to know how wrong the guess is, and it needs that as a single number. That number is called the loss, and a loss of zero means the guess was exactly right, while a bigger loss means the guess was more wrong.

There are several ways to calculate a loss, and the right one depends on what the model outputs.

When the model gives a score for each kind of object, a common loss looks only at the score the model gave to the right answer. If that score is 1 the loss is 0, and as that score gets smaller the loss gets bigger, faster and faster. The page has a table showing a few values, where each row is one guess for a photo of a mug. As the score the model gives to "mug" falls from 0.93 down to 0.01, the loss rises from 0.07 up to 4.61.

The loss is minus the natural logarithm of the score, but you do not need to know what a logarithm is to follow this book. The only thing that matters is the shape, which is that a confident right answer gives a loss near zero, while a confident wrong answer gives a big loss. This loss is called the cross-entropy loss.

When the model outputs a measurement instead, such as how far to open the gripper, the loss is usually simpler. It is just the difference between the model's number and the label's number, squared so that it is never negative. This is called the squared error.

So the loss turns "how wrong is this guess?" into a single number that a program can make smaller.

The next section is about changing the weights a little, using gradient descent. Now that the loss gives one number to work with, the program must change the weights so that this number goes down. It cannot try every possible set of weights, because even a small network has thousands of them.

Instead it asks one question about each weight: if this weight were a tiny bit bigger, would the loss go up or down, and by how much? The answer for one weight is called its slope, and the list of slopes for all the weights together is called the gradient.

Once it knows the slope, the program changes the weight a small amount in the direction that makes the loss go down. So if making the weight bigger raises the loss, the program makes that weight a bit smaller, and if making it bigger lowers the loss, the program makes it a bit bigger. It does this for every weight at the same time.

This method is called gradient descent, because "descent" means going down, and the thing going down here is the loss.

The diagram shows gradient descent for a model that has only one weight, so that a curve can show the loss for every value of that weight. Starting from a random weight with a big loss, each step moves the weight a little way down the curve, and the steps get shorter as the curve flattens near the lowest point.

The numbers behind the picture are these. The weight starts at minus 1.50, where the loss is 7.65. After the first step the weight is minus 0.03 and the loss is 2.77. After six steps the weight is 1.87 and the loss is 0.31, which is close to the lowest possible loss on this curve, 0.30 at a weight of 2.0.

Two things about this are worth noticing before going on. First, each step is a fixed fraction of the slope, so where the curve is steep the step is long, and near the bottom, where the curve is almost flat, the steps are short. That fraction is called the learning rate, and in this example it is 0.35. Second, the program never sees the whole curve, because it only knows the slope at the point where it is, but that is enough to know which way is down.

The learning rate is therefore something you have to choose with care. If it is too small, training takes a very long time, while if it is too big, each step jumps right over the lowest point and the loss can get worse instead of better.

A real network has millions of weights, not one, so the curve becomes a surface in millions of directions that nobody can draw. But the rule for each weight is the same: find its slope, and move it a little in the downhill direction.

The slopes for all the weights of a neural network can be worked out in one pass backwards through the layers, from the output to the input. This method is called backpropagation, and you will see the word often. In other words, backpropagation is the way the slopes are calculated, and gradient descent is what is done with them.

The next part covers doing it many times, using batches and epochs. One step of gradient descent changes the weights only a little, so training needs a great many steps.

In practice the program does not take one step per example. Instead it takes a small group of examples, for example 32 photos, works out the average loss over the group, and then takes one step for the whole group. This group is called a batch, and using a batch makes each step less affected by one unusual photo, while a graphics card can work on all 32 photos at the same time.

One pass through every example in the dataset is called an epoch. So if the dataset has 3,200 photos and each batch has 32, one epoch is 100 steps. Training usually runs for many epochs, which means the model sees each photo many times, and each time the weights change a little more.

While training runs, the program prints the average loss after each epoch, and that loss should go down quickly at first and then more and more slowly. When it stops going down, training has done most of what it can.

The next section explains keeping some examples back to form the test set. Training drives the loss down on the examples it is given, but a low loss on those examples does not prove that the model is good. The model might have learned those exact photos instead of learning what makes a mug a mug, so the only way to find out is to try it on photos it has never seen.

So before training starts, the examples are split into separate piles. First is the training set. This is the pile that gradient descent uses to change the weights, and it is usually the biggest pile, for example 80 percent of the examples. Second is the validation set. This is a smaller pile, for example 10 percent, and the model never trains on it. Instead people check the loss on it during training, to decide things such as when to stop. Finally, there is the test set. This is the last pile, for example the other 10 percent, and nobody looks at it until training is completely finished. This is the pile that gives the final, honest score.

The test set must be truly new to the model, because if the same mug on the same table appears in both the training set and the test set, the test score will be too good. For a robot, a fair test set therefore uses objects, rooms or lighting that the training set did not have.

The next part is about models that are too simple or too close, known as underfitting and overfitting. Once you have a test set, it shows two common ways for a model to go wrong.

The page shows a diagram of three curves fitted to the same points, representing a model with one input number and one output number. The filled dots are the training examples and the hollow dots are test examples that were kept back. The error for each curve is the average distance from the curve to the dots.

The first model is a straight line, which is too simple to follow the shape of the points. Its error is high on the training examples, 1.11, and high on the test examples, 1.31. This is called underfitting, and it means the model has not learned the pattern at all.

The second model is a smooth curve, and its error is low on both piles, 0.25 on training and 0.49 on test. This is the result you want.

The third model is a wavy curve that passes exactly through every training point. Its training error is 0.00, but between the training points it swings far away, and its test error, 1.64, is the worst of the three. This is called overfitting, because the model has learned the exact training examples, including their small random errors, instead of the general pattern.

Overfitting is the more common problem with neural networks, because they have so many weights that they can learn the training set exactly. The sign is always the same: the training loss keeps going down while the validation loss stops going down or starts going up.

Because overfitting is so common, people do four main things about it. First, they collect more examples, because this is the most reliable fix of the four. Second, they make more examples from the ones they have, since a photo can be turned slightly, cropped, made darker or made lighter and still show a mug. This is called data augmentation. Third, they stop training when the validation loss stops going down, which is called early stopping. And fourth, they use a smaller model, or start from a model that was already trained on a much larger dataset. This last idea is called fine-tuning.

Underfitting has the opposite fixes: a bigger model, or more training.

The next section explains what a trained model file is. When training finishes, the program saves the weights to a file, and this file is what people mean by "a trained model" or "the model weights". It is also called a checkpoint, because it is a saved state that you can load and continue from.

The file is mostly a very long list of numbers, with one number for every weight in the network. It does not contain the training photos, and it does not contain any rules written in words, so nobody can open it and read how the model tells a mug from a bowl.

The file on its own is not enough to use the model, because you also need the program code that describes the network: how many layers there are, how big each one is, and how they connect. In other words, the code says which calculation to do, and the file says which numbers to use in it. When you download a model you usually get both, or you get the weights and install the code from a library.

A few file types are common, and you will see their names on model download pages. Files ending in dot p t or dot p t h are saved by PyTorch, which is the most widely used library for training neural networks. Files ending in dot safetensors hold the same kind of weights in a format that is safe to load from a stranger, because loading it cannot run any hidden program. Finally, files ending in dot o n n x use the Open Neural Network Exchange format, which stores both the network's layout and its weights, so that other programs can run the model without PyTorch.

The size of the file follows from the number of weights, because each weight is usually stored in 4 bytes. For example, ResNet-50, a well-known network for photos, has about 25 million weights, so its file is about 100 megabytes. The largest models in this book have billions of weights, which means their files are many gigabytes.

Using a trained model to get an answer is called inference, and inference only does the forward calculation, from input to output. Because it does not change the weights, it needs far less computing power than training.

The next part covers why we train this way, and what it costs. Gradient descent has now turned up at every stage of training, so this section answers why it is used rather than the obvious alternative.

The obvious alternative is to try random changes, so you would change a weight at random, keep the change if the loss went down, and undo it if not. This works for a model with a handful of weights, but with millions of weights it is hopeless, because almost every random change makes things slightly worse and you learn nothing about which way to go. Gradient descent instead uses the slope of every weight, so every step moves every weight in a useful direction. That is why it is used to train nearly every neural network in this book.

Gradient descent costs you three things in return for that speed. First, it needs a lot of arithmetic, because every step runs the whole network forwards and then works out the slopes backwards. So a large model needs a graphics card, or many of them, for hours or days. Second, it needs settings that you choose by hand, such as the learning rate, the batch size and the number of epochs. These are called hyperparameters, to tell them apart from the weights that training finds. Bad choices can make training fail, so finding good ones often takes several attempts. Finally, it only finds weights that fit the examples you gave it, so if the training set has no photos in dim light, no amount of training teaches the model about dim light. In other words, the quality of a model is limited by the quality of its data.

The page then lists where to read next. The next page is about what is inside a neural network, showing what a single neuron calculates, and the layers used for pictures and sentences. Another page explains where the data comes from, how labelled examples for a robot arm are collected, and how fine-tuning reuses a model trained on other data. There is also a glossary that defines robot-learning words, such as demonstration and checkpoint, in one place. Finally, a later page goes further into how much data robot models need today.

The final section is about using it in Python. The earlier sections described training as a loop that repeats four steps: guess, measure the loss, work out the gradient, and move every weight one small step. This section shows that loop as the Python code it really is, so that the words on this page have something concrete to point at. This is the shape of the idea rather than a finished program, because a real training script also loads data from disk and saves checkpoints.

The code starts by importing the PyTorch library and setting up a data loader with the examples and their labels, grouping them into batches of 32 and shuffling them. It then defines a simple sequential neural network, chooses the cross-entropy loss function, and sets up an optimiser with a learning rate of 0.01 to handle the step size.

Then comes the training loop. It loops for 100 epochs, and inside that, it loops over the batches of inputs and labels. For each batch, it calculates the loss by passing the inputs to the model and comparing the output to the labels. Then it drops the previous batch's gradients, works out every weight's gradient by calling backward on the loss, and moves every weight one small step by calling step on the optimiser. After the loops finish, it saves the model's dictionary of weights to a checkpoint file.

The three lines in the middle of the loop are the whole of gradient descent. Working out the gradient is done by PyTorch for every weight at once without you writing a single derivative. The step itself gets its size from the learning rate you chose. Clearing the stored gradients is necessary because PyTorch adds each new gradient to whatever is already stored, so you have to clear the store before each batch or the steps come out wrong.

The library gives you the gradients, the update rule, a choice of ready-made losses, and the batching and shuffling. It also gives you the dictionary of weights that makes up the model file.

What you collect yourself is the examples and their labels, and that is where nearly all the effort goes. You also decide how to split them, because nothing in this basic code keeps any examples back, and without a test set you cannot tell whether the model has learned or memorised.

What you have to decide is the size of the network, the learning rate, the batch size, and how many epochs to run before stopping. As explained earlier, those choices matter: too small a network underfits, too long a run overfits, and too large a learning rate makes the loss jump about instead of falling. The network in this code is a plain stack of linear layers, which suits a short list of measured numbers. A photograph needs convolutional layers instead, which are covered on the next page.
