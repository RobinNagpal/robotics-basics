<!-- section: lead | Solution 6 — a network trained from scratch -->

Solution 6, a network trained from scratch. 

This solution uses a learned model as the decider. It consists of one small network that is trained from nothing, using pictures that the simulator renders and labels for free. The network has two output heads. The first head identifies which pixels are glass, and the second head determines which specific glass each of those pixels belongs to.

As a reminder, the physical setup of the robot cell is described on the page titled the cell. That earlier page covers the layout, the two camera positions from the top and from the side, all four sensors, and the terminology used throughout this project. What follows here will only cover the details that are specific to this sixth solution.

<!-- section: introduction | Introduction -->

The introduction to this page explains how to answer problem two with a network rather than with arithmetic, and it is the only solution here that needs no depth readings at all. That matters because real glassware returns almost none, so a method that works from colour alone is the one that survives the day the simulated glasses are replaced by real ones.

The network is built in two stages, and the second reuses almost everything the first sets up. The first stage asks a question about classes, specifically whether a given pixel is glass or table. That is enough to find where the glasses are, but it is not enough to say which glass is which, because two glasses that overlap in the picture come back as one region. The second stage asks each glass pixel a different question, asking which way the middle of its own glass is. The answers are arrows, one per pixel, and counting glasses becomes a matter of counting the places the arrows point at.

Keeping both stages in one document is deliberate, because they are one network. They share a shape, a training recipe, a source of labels, and a set of traps. What differs is the last layer and what it is asked to predict, so describing them apart would mean writing the same network down twice.

By the end, you will understand why a small network is enough for a cell this narrow, and why training it from nothing beats adapting a large model here. You will also learn why the obvious measure of success rewards saying nothing at all, why an arrow has to be measured in millimetres on the table rather than in pixels, and why this whole family is blind to the one failure the problem says to watch hardest.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solution solves. Four to six glasses stand on the table. They are all the same kind, the kind is known, and they are solid, so the depth camera sees them. The job is to say which pixels belong to which glass, to give each glass a position on the table, and to give each a rough footprint width. Nothing is picked up and no shape is measured here.

Two different things defeat the obvious methods, and this solution is aimed at the second one.

The first issue is that in the picture, outlines overlap. If the camera is roughly in line with two glasses, the near one covers part of the far one and their two outlines join. 

To see why that is fatal, two words are needed. A mask is a picture the same size as the photograph in which every pixel is just yes or no, where yes means this is glass. The step that turns a mask into separate objects is called connected components, or a flood fill. You take a yes pixel nobody has visited, spread out to every yes pixel touching it, call everything you reached one object, and repeat.

The trouble is that a flood fill answers exactly one question, which is whether these pixels are joined. And joined is precisely what the two overlapping outlines are.

The second issue is that on the table, the points can be too close to group. The earlier solution for clustering on the table avoids the picture entirely. Every pixel with a depth reading becomes a point in the room, the points standing clear of the table are kept, and points closer together than a chosen grouping distance go in the same group.

That one distance has to satisfy two demands at once. It must be larger than the biggest hole inside one glass's own points, or one glass comes back as two. And it must be smaller than the strip of bare table between two glasses, or two come back as one.

At the spacing this problem guarantees, there is plenty of daylight between those two limits and the choice barely matters. As the glasses close up, the window narrows. And when two glasses touch, the window shuts completely. No grouping distance keeps them apart while also keeping each of them whole.

A diagram here shows two glasses standing close together that come back as one region. The middle panel of that picture has no seam between the two outlines for anything to find. The right panel shows what the next step is handed, which is a single object far wider than any glass of this kind can be.

The range check notices that much. But noticing is all it can do, and the reason is worth stating exactly, because it is what this solution exists to repair. Nothing in a class map says where to cut. Every pixel carries the same label, glass, and a label that is the same everywhere cannot possibly mark a boundary.

It is tempting to think a better-trained network would solve this, and it would not, because the limitation is in the shape of the output rather than in the quality of the fit. 

Semantic segmentation labels every pixel with a class. Instance segmentation labels every pixel with a class and with which object it belongs to. This problem asks for the second. A perfectly trained class map still merges touching glasses, because glass is the only value the answer has room to hold.

So the fix is not a better network. It is a different output.

<!-- section: the-main-idea | The main idea -->

The next part of the page covers the main idea behind this solution. This main idea has two halves, and the first is a claim about the robot's work cell rather than about neural networks. 

The claim is that because the cell is narrow, the network can be small. Consider how little actually varies here. There is only one class to predict, which is whether something is glass or not glass. There is only one kind of object at a time, drawn from inside that kind's plausible range of shapes. There is one camera, with one lens. There is one lighting setup, inside one simulator. Furthermore, the glasses are always upright and always solid. Almost all the variety that a general-purpose model is built to absorb simply does not occur here, so the network can be small. A small network with an endless supply of exactly labelled pictures is something you can train from nothing in an afternoon.

A diagram shows what is asked of the network: a picture goes in, and one probability per pixel comes out. The right-hand panel of the diagram is the same width and height as the input picture on the left, but every pixel holds one number between zero and one. This number says how sure the network is that this particular pixel is glass. A plot underneath follows a dashed line across one of the glasses. The number sits near zero over the table, rises to near one over the glass, and passes through the middle probabilities only in a narrow band at the rim. This is exactly where a person with a magnifying glass would not be able to say either. That narrow band is the network being honest, and later in the page, it turns out to be the reason why doubt has to be counted inside a region rather than at its edge.

The second half of the main idea is that a simple class map is not a complete answer, and the fix is to ask each pixel for an arrow instead of a label. At every glass pixel, the network predicts a short arrow pointing towards the middle of that pixel's own glass. When you add that arrow to the pixel's own position, what you have is a vote for where that glass's centre is. One glass then makes one pile of votes. Two glasses make two piles. Counting glasses simply becomes counting piles.

Another diagram shows this process in five stages, reading from left to right: the picture, the mask, the table, the votes, and the peaks. The network is involved in one stage only, and everything before and after it is arithmetic the project already has.

The rest of the page builds both of these halves up. First comes what a network is and why this one is trained from nothing, followed by its shape and the two things that shape decides. Then comes the first head of the network and the trap hiding inside its measure of success. After that is the second head, including the single most important decision in its design, which is what units the arrow is measured in, and how a cloud of votes becomes a count of glasses. Finally, the page covers what keeps the whole thing honest.

<!-- section: what-a-network-is-and-what-training-means | What a network is, and what training means -->

The next part of the page explains what a network is, and what training means. Before going further, two words need defining, because everything after this uses them.

A neural network is a program whose behavior comes from numbers fitted to examples, rather than from rules anybody wrote. Those numbers are called weights. They start as random noise, and training shows the network a picture, compares what it produced against the answer wanted, and nudges each weight in the direction that would have helped. Nobody writes the rule the network ends up applying, and nobody can read that rule back out afterwards.

The second concept is fine-tuning, which means not starting from random numbers. You take a network somebody else trained on a large collection of labeled photographs, throw away its last layer, attach your own, and carry on training. This is the standard advice everywhere, and the reason is that labeled real pictures are scarce. Because somebody has to draw around every object in every picture, a borrowed network cuts the number of labels you need by a large factor.

<!-- section: why-train-from-scratch-rather-than-borrow | Why train from scratch rather than borrow -->

The next part of the page explains why we train from scratch rather than borrow an existing network. A diagram here illustrates two ways to start a network, and shows why only one of those options is open to us. 

Two things make the usual argument for fine-tuning collapse in this situation, and it is worth being clear that only one of them is about this project's rules.

The first is that every network worth borrowing was fitted to real photographs. The large collections of labelled images that such networks are trained on are photographs, and so is everything trained on them, including the large general-purpose segmentation models. This project's rule is that everything a solution needs must be producible by the simulator on this machine, and a file of weights fitted to photographs of the real world is not. That is not a judgement about whether those models are good. They are excluded by where their numbers came from, and the versions of this project that do allow them are written up in a separate page about solutions that need hardware beyond a simulator.

The second reason is the one that actually matters, because it would apply even without the rule. The scarcity that fine-tuning exists to solve is not present here. Asking the simulator for a render and its per-object mask costs the same as asking for the render alone. There is no annotator, so there is no annotator's budget and no annotator's mistakes. Labels here are free.

There is also a third, smaller reason. Most ready-made networks expect a dedicated graphics card, and this machine has none. That alone would decide nothing, because plenty of them run without one, but it removes the last practical argument for borrowing.

So the answer is a random start, and it is reasonable only because of the second reason. Training from scratch on a few hundred hand-drawn labels would be a bad idea. Training from scratch on an endless supply of exact ones is not.

<!-- section: the-shape-of-the-network | The shape of the network -->

The next part of the page explains the shape of the network. The shape used here is called a U-Net. The diagram on the page illustrates how it gets this name. If you follow the operations down the left side, then back up the right side, with dashed lines connecting across the middle, the whole structure forms the shape of a U.

Let us trace the down path first. It starts with the input picture, which is four channels deep: red, green, blue, and depth. First, it applies two convolutions. A convolution takes a small square window and slides it over the picture. At each position, it multiplies the values inside the window by a fixed set of weights and adds them up. One set of weights produces one output channel, and many sets produce many channels.

Next, the network halves the image size. It uses a max pool, which keeps only the largest value out of each little block of pixels, so the picture comes out half as wide and half as tall. After that, it applies two more convolutions, this time with the channel count doubled. It halves the size again and doubles the channels again, and then halves it once more. That last, smallest, but widest layer is called the bottleneck.

Two things happen on this way down, and they pull against each other. Each halving throws away exactly where something is, because one unit now stands for a whole patch of the original picture. But each halving also means the next window covers four times as much of the original picture as it did before. So, deeper units know less and less precisely where they are looking, but they know more and more about what is around them. That trade-off is the entire reason for going down, and a later section of the page will show what happens if you do not keep it in check.

Now for the up path. A transposed convolution does the reverse of a pool. It doubles the width and height back up while narrowing the number of channels. Then come two more convolutions, another doubling, and so on, until the block of numbers is back to the size of the original picture. A final convolution uses a window of exactly one pixel. This means there is no mixing across space at all, just a weighted sum of the channels, which collapses everything down to a single channel. Finally, a function that squashes any number into the range of zero to one turns that output into a probability.

The real point of this shape lies in the skip connections. There is a problem that the up path alone cannot solve. The bottleneck at the bottom knows there is a glass roughly over there, but the halvings have destroyed the knowledge of which exact pixel its rim sits on. Doubling the size back up cannot invent that detail, because the detail was thrown away.

The solution is simply not to throw it away. Before each halving on the way down, the network keeps a copy of the block of numbers. On the way back up, it attaches that copy on as extra channels. The fine detail comes across on the copy, the sense of context comes up from below, and the convolution after the join mixes the two together. Those copies are the dashed lines shown in the diagram, and they are what the U in U-Net refers to.

This design was created by Ronneberger, Fischer, and Brox in a 2015 paper. It was originally written for microscope images, where exactly the same problem arises: you need to label every pixel, but you only have very few examples to learn from.

<!-- section: the-receptive-field-and-the-warning-it-gives | The receptive field, and the warning it gives -->

The next part of the page discusses the receptive field, and the warning it gives. There is one thing worth working out before trusting this design, and it follows directly from the trade described in the down path. It is called the receptive field, and it is how much of the original picture one unit at the bottleneck actually depends on.

It is easy to compute. Each convolution extends the field by one pixel on each side, at whatever scale it is currently working at, and each pool doubles that scale. So the field grows slowly at first and then in bigger and bigger jumps. By the time you reach the bottleneck, it covers a square patch of the original picture some tens of pixels across.

Now turn that patch into a distance on the table, using how much table one pixel covers from the height the camera flies at. Here is the warning. That patch of table is smaller than the smallest gap the cell guarantees between two glasses.

This is the kind of thing that becomes invisible once training has started, so it is worth keeping in mind. The deepest layer, which is the one layer with enough context to reason about a neighbour at all, cannot see two glasses at the same time. It is structurally incapable of the comparison you might have hoped it was making.

Adding a fourth halving fixes it. The bottleneck then works at half the scale again, and its receptive field covers a patch of table comfortably wider than the guaranteed gap. It costs about four times as many weights, for the reason given in the previous section.

Whether the extra level is actually needed is not known, and this document is not going to pretend otherwise. Two things could rescue the shallower design. First, the decoder's own convolutions widen the field further on the way back up. Second, the evidence that separates two overlapping outlines may turn out to be entirely local to the seam where they meet, in which case no unit ever needs to see both glasses at once.

It is flagged here for one reason. It is far cheaper to check this with arithmetic before training than to diagnose it afterwards, when all you have is a network that quietly never separates anything.

<!-- section: where-the-weights-sit | Where the weights sit -->

The next part of the page looks at where the weights sit in the network. A diagram illustrates this distribution, showing where the weights are concentrated and what a fourth halving of the image size would cost. 

One fact about convolutions decides the shape of the whole weight budget, and it is worth understanding rather than looking up. A convolution holds one weight per window position, per input channel, and per output channel. Because of this, the weight count of a block grows with the product of its two channel counts.

Follow what that implies. Going one level deeper doubles the input channels and doubles the output channels, so it roughly quadruples the weights in that block. Meanwhile, that block is working on a picture a quarter of the size, so it costs no more arithmetic than before.

The result is that the deep, narrow layers hold nearly all the weights. The bottleneck and the block just after it hold roughly three quarters of the total between them, while the first block, the one working on the full-size picture, holds almost none. Widening the deepest level is expensive, and widening the first is nearly free. So anyone tuning this network should spend their attention at the bottom rather than the top.

And the whole thing is small. The total comes to a few hundred thousand weights, which is a couple of megabytes stored, or under half that at reduced precision. This is a file you can commit to the repository, version alongside the code, and regenerate without thinking about it, which is exactly not true of the large pre-trained models this solution deliberately does not use.

<!-- section: the-first-head-which-pixels-are-glass | The first head: which pixels are glass -->

The next part of the page explains the first head, which decides which pixels are glass. With the shape settled, the two heads can be taken in turn, and the first is the simpler of them. It has one output channel, and it produces one number per pixel. That number is how sure the network is that the pixel is glass. Everything in this part is about that one channel, including how its success is measured, what a second input channel does and does not buy, and where it stops being enough.

Training needs a loss, which is one number saying how wrong an answer was, and which the nudging then tries to reduce. 

The obvious loss is called binary cross entropy. For a pixel that really is glass, the penalty is smaller the higher the probability the network gave it, so being sure and right costs almost nothing while being sure and wrong costs a great deal. For a table pixel, it is the same with the probability flipped. Then you average over every pixel in the picture.

That average is the trouble, and the trouble comes straight out of this cell's geometry. As the first diagram shows, a glass seen from the top takes up a small patch of a large picture, and there are only a handful of glasses. Count the pixels, and the great majority of every picture is bare table. Glass is the rare class by a wide margin.

So a network can lower the average a long way without learning anything at all. Imagine it starts by saying "maybe" to every pixel. Now let it learn exactly one thing, which is to say "not glass" everywhere. The table pixels, which are the great majority, now cost almost nothing each. The glass pixels cost a great deal each, but there are few of them. Work the weighted average through, and it has fallen substantially. The network has been rewarded for producing an empty picture, and this is at its worst early in training, when there is nothing better on offer and this is the easiest improvement available.

Two standard fixes exist, and this design uses both.

The first is to weight the rare class up. You multiply every glass pixel's contribution by the ratio of the two class sizes, so that the glass pixels and the table pixels contribute equally to the total. Now, saying nothing is glass is no longer an improvement at all.

The second fix is to add a loss that measures overlap rather than counting pixels. The Dice coefficient is twice the number of pixels that both the answer and the truth call glass, divided by the total number either of them calls glass. It is one for a perfect match, zero when they share nothing, and it has no term for the table at all. Using one minus Dice alongside the weighted cross entropy is the usual recipe, introduced by Milletari and colleagues in 2016.

The right-hand panel of the diagram and the accompanying table show why this second fix is needed, by scoring three answers two ways. If the network says "table" everywhere, its pixel accuracy is high, but its Dice score is zero. If every mask is a few pixels too thin, the pixel accuracy is higher still, but the Dice score is noticeably below perfect. If the answer is exactly right, both scores are perfect. 

Pixel accuracy gives a useless answer a high score, and a visibly wrong one an even higher score, because what it is mostly reporting is how many table pixels were correctly called table, and that is the easy part. Dice gives the useless answer zero, because the two masks share nothing, and it notices the thin masks, because they share less than they should.

The lesson generalises far beyond this page: a score that rewards saying nothing will be optimised by a network that says nothing.

Next is the depth channel, and what it does not buy for free. Depth is one of the four input channels, and that needs stating plainly, because it means this solution does not get "works without depth" for free.

A network handed depth will lean on it, because depth is by far the easiest signal in the picture, and the colour path will then never develop at all.

This property is worth wanting. If the glasses ever become real glass, the depth camera stops returning anything useful through them, and every method that groups points in the room loses its input at once. A colour-only method survives that day.

It is earned rather than given, by a trick called modality dropout. On some of the training pictures, the depth channel is replaced with nothing. After that, the same weights run on colour alone. They run less accurately, because the depth channel was carrying real information and dropping it costs something, but they run. What share of pictures should have their depth removed is a choice rather than a measurement, and what is right here is not known.

One further detail matters for the same reason. The depth channel is scaled into the same range as the colour channels, and it is deliberately not converted into a height above the table. Converting it would hand the network the very clue the clustering solutions use, and it would make the colour-only claim hollow.

The final part of this section explains why the network knows which pixels are glass, but not which glass. This is the limitation named in the introduction, and it is structural rather than a matter of training harder.

The second diagram illustrates the point. Its middle panel shows one region where every pixel is correctly labelled glass, but there is no way whatever to ask it which glass.

A per-pixel class map is called semantic segmentation. This problem asks for instance segmentation, which means one mask per object. So on its own, this solution does not answer the problem, and the separating has to be added somewhere.

There are two cheap places to add it. First, a second output channel could predict each object's boundary, so that regions can be cut along the predicted seam. Second, a pair of channels could predict, at every glass pixel, the offset to the centre of its own object.

Offsets fail more gently, and the reason is worth remembering as a general principle. A seam has to be predicted correctly along its whole length, and one missing pixel rejoins two objects completely. Offsets are one vote per pixel, so a few wrong votes are simply outvoted by the many right ones. Solution eight is that idea in full.

<!-- section: the-second-head-which-glass-each-pixel-belongs-to | The second head: which glass each pixel belongs to -->

The next part of the page explains the second head, which decides which glass each pixel belongs to. The previous section ends where the problem starts asking which glass is which, so this is where the second head comes in. It keeps the network's shape and its training recipe almost unchanged, and replaces the single output channel with a pair of them, holding the two components of an arrow. Nothing else about the network changes, which is the reason these two stages belong in one document.

What follows is why an arrow can be predicted pixel by pixel at all, what units it has to be measured in, why nothing has to find a boundary, and how a cloud of arrows becomes a count of glasses.

The first thing to notice is how much work has already been done before the network is consulted, and it means the network is asked a much smaller question than it might have been. 

Because the table's height is known and the glasses are opaque, a depth reading comes back for every glass pixel. The arithmetic from the second solution already turns each such pixel into a point in the room and drops it onto the table. So every glass pixel already has a position on the table, worked out from its depth reading, the lens, and the recorded camera pose.

That shrinks the network's job to one question: how far, and in which direction, to my own glass's footprint centre?

There is a second thing that is free for the same reason. The mask is free. Nothing has to be learned to decide whether a pixel is a glass pixel, because the existing test already says so. That test simply checks if the point behind the pixel stands clear of the table and below the tallest glass the cell accepts. The network therefore needs only two output channels, one for each direction of the arrow, and it never spends any capacity on the easy question.

This decision to vote in distances on the table, rather than in the picture, is what the whole solution rests on, so it is worth going through slowly. 

A diagram illustrates the difference between voting in pixels and voting in table millimetres. Its left panel shows the trouble with arrows measured in pixels. The same glass, with the same real displacement, photographed from twice as far away, is half as many pixels across. So a network predicting arrows in pixels has to learn how that number shrinks with distance. In other words, it has to learn the camera before it can learn anything about glasses.

And it is not only a problem between one picture and the next, which is the part people usually notice. Consider a single picture taken from the top. The table is the full camera height away from the lens, while the rim of a tall glass has climbed most of the way towards it. So the correct arrow in pixels varies by a large factor within one photograph. Measured on the table, it does not vary at all.

There is a second benefit, and it is the one that makes a small network plausible. Measuring the arrow on the table puts a hard limit on what the network ever has to predict. An arrow runs from a pixel to the centre of its own glass, so the longest arrow that can ever occur is half the widest footprint the cell handles, whatever the distance, and whatever the angle. Every training target is therefore a pair of numbers inside a small, known box. A target that is bounded and does not depend on the camera is far easier to fit than an unbounded one.

Another diagram shows arrows from the pixels of one object, and then of two. The right-hand panel of this picture is the whole argument, and it is worth visualizing carefully. 

When there are two glasses, the two sets of pixels touch. There is no gap anywhere along the seam between them. And it does not matter, because what changes at the seam is not the pixels, but the direction the arrows point. The pixels on the left half point left, the pixels on the right half point right, and the seam between them is not something anything has to find.

Nothing has to find a boundary, so nothing can get one wrong. That single sentence is why this method survives touching glasses when nothing else here does.

The method is also robust in a way that a boundary method is not. A glass seen from the top casts one vote for every pixel of its outline, which is well over a thousand votes. A handful of those pointing the wrong way are a handful of strays among thousands, and a pile of thousands does not notice them. Compare that with predicting a seam, where one missing pixel along the seam rejoins two objects completely.

There is one more consequence of voting in table distances, and it pays off later. Because a vote is a place on the table rather than a place in a picture, votes from two photographs taken from two different places land in the same frame, and they can be pooled with no matching step at all. That is what makes both the second picture of each pair and the feedback loop cheap.

Each glass should make one tight pile of votes, so the remaining question is simply where the votes pile up. 

The method for that is called mean shift. You put a circular window down on one vote, move the window to the average position of the votes inside it, and repeat until it stops moving. Each move is a step uphill towards thicker votes. Run it from every vote, and the votes whose windows stop in the same place belong to one pile.

A third diagram shows these vote clouds, and the windows sliding to their peaks. The left two panels show the raw signal: one thick patch of votes for one glass, and two patches for two. The right panel shows several windows started at several different votes, each walking uphill and stopping, with dashed circles marking each window where it came to rest.

So counting glasses has become counting distinct stopping places. The important property of mean shift here is what it does not need to be told. Unlike other grouping methods, nothing has to say how many piles to expect. That matters a great deal, because in this problem the count is the answer.

There is exactly one number to choose, which is the window radius, and it is pinned at both ends before anything is run. This is the same shape of argument used for the grouping distance in the second solution.

The floor is the spread of the votes themselves. The votes for one glass do not land on a single point. They scatter around the true centre, and that scatter can be measured on held-out renders where the truth is known. A window much smaller than that scatter fits inside one pile, so it climbs some local lump within the pile rather than the pile as a whole, and one glass then comes back as several peaks.

The ceiling is the closest two centres can ever be. The worst case is two of the narrowest glasses this kind allows, pressed rim to rim. Their centres are then one footprint apart and nothing can bring them closer. A window whose radius reaches much more than half of that covers both centres at once, and the two piles merge into one.

There is comfortable room between those two limits, and the chosen radius sits inside it. It is worth seeing what a careless choice would cost, because the failure is quiet. A window large enough to span the narrowest possible centre gap swallows two centres whole, so it would merge exactly the pairs this solution exists to separate. And it would do so silently, because a merged pile looks perfectly tight and complains about nothing.

One practical note. Running a window from every single vote means comparing every vote with every other vote on every step, and with tens of thousands of votes that is far more arithmetic than the job needs. Seeding the windows from a few hundred votes drawn at random fixes it, because a pile of thousands is found just as reliably from a sample of it, and every vote is still assigned at the end by which peak it is nearest, so nothing is lost.

<!-- section: the-network-and-its-training | The network and its training -->

The next part of the page explains the network and its training. 

The network takes four channels the size of the picture. These are the three colour channels and the height above the table. It returns two channels of the same size, which hold the two parts of the arrow. Height is used rather than raw depth for the same reason the arrow is measured on the table: height means the same thing from every viewpoint, and raw depth does not.

Its shape is the same encoder-and-decoder design used in solution seven. This design repeatedly halves the picture while widening it, so that later layers see a large part of the scene. Then it doubles the picture back to full size. Each level on the way down is copied across to the matching level on the way up, so that fine detail is not lost.

Seeing a large part of the scene is exactly what this task needs, because a pixel cannot possibly know where its glass's middle is by looking only at itself. It has to see enough of the glass around it to tell which way the middle lies. 

For the same reason, the receptive-field warning given earlier applies here with more force rather than less. That warning is that the deepest layer of a shallow network may cover a smaller patch of the table than the task needs, and here the task needs each pixel to see the whole of its own glass. The size and depth of this network are therefore not settled, and working out whether they are sufficient is something to measure rather than to assert.

When it comes to the loss function, there are two important choices inside it. First, the network is scored by how far each predicted arrow is from the true one, using a loss that behaves differently for small and large mistakes. It scores a small mistake by its square, and a large one by its size. Squaring the small errors makes the fit precise where it is nearly right, and not squaring the large ones stops a handful of wild pixels from dominating every update. Pixels near an edge, where a pixel may genuinely belong to either glass, are exactly the wild ones.

The second choice inside the loss is not a minor detail either. The loss is applied over glass pixels only. Most pixels in a picture from the top are table, and a table pixel has no correct arrow at all, because there is no object for it to point at. So the loss is multiplied by the mask before it is added up, and the network is scored only where the question has an answer.

Generating the training labels costs nothing, and this is what makes the whole thing practical. The labels are arithmetic, not human annotation. The simulator already knows, for each object, which pixels are which and where each object stands. So for a pixel inside one glass's mask, the target arrow is that glass's footprint centre minus the pixel's own position on the table. It is a subtraction rather than a judgement. Because there is no human annotator, there are no annotator's mistakes, and there is no limit on how many scenes can be made beyond the time it takes to render them.

There are two things about the training set that decide whether it works. 

The first is to spawn the hard case. The cell's own rule keeps glasses a comfortable distance apart, and a training set drawn only from that rule never once shows the network a pair that a page of clustering code could not already separate. So the teaching has to happen on pairs standing far closer than the rule allows, and on pairs that are actually touching. But you must keep the easy cases too, in proportion, because otherwise the network quietly learns that there is always a pair to find.

The second thing is to randomise everything that is not shape. A simulator will render the same table under the same light for ever, and a network given a constant will use it as a clue. A technique called domain randomisation, introduced by Tobin and colleagues, is used here. It varies the lighting, the textures, the glass tint, the camera pose, the exposure, the picture noise, the depth noise and dropout, and the number and placement of the glasses. By varying all of this, shape is the only thing left that predicts the answer. This matters even though the system will only ever run inside one simulator, because this cell's own lighting and table will change during the project's life.

<!-- section: domain-randomisation | Domain randomisation -->

The next part of the page explains domain randomisation. The diagram shows six different renders of the exact same arrangement of glasses. Across the six pictures, things like lighting, colours, and textures change wildly, but the physical shapes and positions of the objects are deliberately held still. 

Here is the failure this prevents. A simulator will normally render a table, under a specific light, with a specific shade of grey, for ever, in exactly the same way. If every training picture has the table at the same shade, then the network is free to learn a rule like, glass means the pixels that are not that shade of grey. That rule scores perfectly on every training picture, and on every held-out picture too, because the held-out pictures came out of the exact same renderer. But then somebody changes the world file, or adds a light, and the model falls over for a reason that appears in none of the numbers.

Domain randomisation is the fix, and it is blunt. You vary everything you are not trying to teach, scene by scene, over a range wider than anything you expect to meet. The network then cannot use any of the varied things as a shortcut, because none of them is reliable. What is left constant is the shape and position of the objects, so that is what it has to learn. This idea comes from a 2017 paper by Tobin and colleagues.

This matters even though this cell only ever runs in one simulator, because the world file will change during the project's life. A model that has quietly keyed on a texture breaks silently the day somebody changes that texture, and randomising is how you find that out during training instead of afterwards.

What would be varied, scene by scene, includes several things. First is the light, meaning its direction, intensity, colour, and how many sources there are. Second is the table, meaning its colour and texture. Third are the glasses, meaning their tint, their shininess, and each one's proportions drawn independently from its kind's plausible range. Next, the camera pose is jittered slightly around the nominal place it looks down from, because the arm's own positioning is not exact. You would also vary the exposure and the sensor noise. Finally, you would vary the arrangement itself, with four to six glasses placed anywhere in the zone.

One thing is worth randomising past the specification, which is the minimum separation between glasses. The cell guarantees a certain gap, but training with pairs standing much closer than that makes the guaranteed gap an ordinary case in the middle of the range, rather than the very hardest thing the network ever saw. As a general rule, the edge of the specification should sit somewhere in the middle of the training set, so that the model has seen worse than it will ever meet.

However, one thing would not be varied, which is the camera's lens. The focal length and the picture size are facts about the camera this cell has, and not nuisances to be made robust against. Teaching the network to cope with lenses it will never meet spends its limited capacity on nothing. The same goes for the glasses standing upright on a flat table, because that is the task rather than an accident of the data.

<!-- section: the-arithmetic-still-decides | The arithmetic still decides -->

The next part of the page explains how the arithmetic still decides the final outcome. One thing has not changed from solution two, and it is deliberate. 

Each pile's voters, which are the pixels at their own positions on the table, are fitted with a circle. This returns a centre, a width, and a fit error. A pile whose fitted width falls outside the range that this kind of glass can be is not reported as a glass, whatever the votes may say.

So, the network proposes and the geometry disposes. That is what keeps this solution inside the same safety argument as the programmed ones. A learned component decides which pixels group together, and an arithmetic check decides whether the result is believable.

<!-- section: how-the-concepts-fit-together | How the concepts fit together -->

The next part of the page explains how all these concepts fit together. Everything discussed so far forms a single pipeline, and it is worth seeing the whole process in order before looking at the failure cases, because each stage inherits whatever the previous stage got wrong.

First, a picture goes in. The network, whose shape was chosen so that a unit near the output can see a large part of the scene, produces two things at every pixel. It outputs a probability that the pixel is glass, and an arrow pointing towards the middle of that pixel's own glass. The probability is thresholded to create a mask. Then, every mask pixel that has a depth reading is back-projected into a physical point on the table. The arrow, which was predicted in millimetres on the table rather than in pixels, is added to that point to cast a vote. These votes pile up, creating one pile per glass. A technique called mean shift finds these piles without needing to be told how many glasses to expect. The centre of each pile gives the position of a glass. The spread of the pile provides a confidence score, which comes for free, and the pixels that voted into that pile make up that specific glass's mask.

There are three important things to hold on to about this chain.

The first is the decision about units, which is what makes the whole approach work. If the arrow were measured in pixels, it would mean something different at every distance and under every amount of perspective splay. The same glass would demand a different answer from the network in every picture. By measuring the arrow in millimetres on the table, it becomes a fact about the glass itself, rather than a fact about where the camera happened to be.

The second is the decision about the loss function, which is the part that most often goes wrong. Because most pixels in these pictures belong to the table, a measure of success that simply counts pixels would reward a network for saying nothing is glass at all. The fix for this is to score the overlap of the predicted shape against the true shape, rather than just counting the pixels.

Finally, the decision to use arithmetic is what keeps the whole system honest. The network makes a proposal, but the fitted circle and the known range of widths for that kind of glass make the final decision. If a pile of votes implies a footprint that no glass of this kind could possibly have, it is rejected by a simple rule that nobody had to train.

<!-- section: the-feedback-loop-and-where-doubt-has-to-be-counted | The feedback loop, and where doubt has to be counted -->

The next part of the page covers the feedback loop, and where doubt has to be counted. 

A per-pixel model has a measure of doubt built into its output, which most methods do not. It does not return a simple mask. Instead, it returns a confidence map, providing a probability at every single pixel. The diagram illustrates this by showing a confidence map where interior doubt marks a specific region that needs to be photographed again.

Thresholding that map to create a mask throws the doubt away. Keeping the map, however, gives the feedback loop something to run on. We can call a pixel doubtful when its probability is neither clearly glass nor clearly not glass, because the network genuinely cannot say.

From this map, two things can then be read off: how much doubt surrounds a region, and exactly where that doubt sits.

Measuring how much doubt there is needs care, because the obvious way of measuring it does not work, and this is the most useful practical idea in this document. The rim of the region has to be removed before anything is counted. Every region has a doubtful rim a couple of pixels wide, because at the edge of any object, some pixels really are half glass and half table. That uncertainty is the correct answer rather than a failure. But it is not small, either. For a glass-shaped region, a rim that thin is already a noticeable fraction of the whole region before anything has gone wrong at all.

Worse, that fraction depends on the region's shape rather than on its trouble. A long, thin region has more perimeter for each unit of area than a fat one, so it looks more doubtful simply for being thin. Counting doubtful pixels over a whole region therefore mostly measures perimeter against area, which tells you nothing about whether the answer is right.

So, you must erode the region first, which means shaving a thin collar off its outside, and count only what is left. A glass the network is sure about then has essentially nothing uncertain inside it. And doubt in a band across a region's middle is the signature of a second glass behind it. After the erosion, that band is the only thing left there.

That gives the loop both of the things it needs. A region far more doubtful than its neighbours is one to photograph again. And the band of doubt gives the direction to look from, because the band marks where one object's edge crosses another, meaning the two objects are stacked across it.

The loop needs a third thing, which is a budget. Moving the arm and letting it settle costs seconds, while taking a picture costs milliseconds, and one pass of a network this small costs tens of milliseconds at most. The expensive thing is the movement, by a factor of thousands. So the loop caps the extra looks it will take per doubtful region, and when the budget is spent, it reports the region as doubtful rather than guessing.

<!-- section: doubt-measured-from-the-votes-themselves | Doubt measured from the votes themselves -->

The next part of the page explains how doubt is measured from the votes themselves. The doubt here is free, which is unusual and is one of the best reasons to prefer this design. How far a pile's votes sit from its own peak, on average, is a per-glass confidence, and it costs exactly one line of code to compute.

It does need calibrating once. To do this, you run the trained network over held-out renders where the truth is known, and record what that spread looks like when the answer is right. Every threshold used below is then a multiple of that measured figure, rather than a constant somebody just chose.

A diagram here shows three shapes of vote cloud and what each one should make the arm do. There are three shapes of cloud and three actions, and the important point is that the shape says not only whether to look again, but where.

First, a tight pile, at or below the held-out figure, is one glass. The system fits the circle, checks the width against the range for that kind of glass, reports it, and moves on.

Second, two knots inside one pile means the votes have split into two tight lumps. That indicates two glasses, and it has already said where both of them are. So, the system proposes the split, and then checks it. It accepts the split only if both fitted circles land inside the kind's range. If only one of them does, the split is not believed, and the pair is reported as doubtful rather than being guessed at.

Finally, one broad smear, with no lump sharper than the rest, is the network saying it does not know. Re-running the grouping will not manufacture an answer that is not in the data.

That last case is where the feedback loop starts, and the smear dictates which picture to take next. A smear almost always has a long axis, and that axis is the direction along which the evidence is thin. So, the camera needs to look across it, square to the long axis, from the side at the measuring standoff. Notice that there is no search over candidate viewpoints here at all. The vote cloud names the direction by itself, and the geometry the project already has turns that direction into a reachable pose.

There is a fourth case, which is checked separately because the spread does not catch it. A second diagram plots the number of votes and the vote spread against how much of a glass is visible, showing what happens when a glass is heavily hidden. A hidden glass votes only from a crescent down its visible side, and those votes can agree very closely with each other while being wrong together. Because of this, a pile built from a small fraction of the votes a whole glass should give is doubtful on count alone, no matter how tight it looks. 

This is the one check that catches confident agreement between witnesses who all stood in the same wrong place, and it is worth having for exactly that reason. The two curves in the diagram are shapes to expect rather than exact measurements, and both thresholds are figures to calibrate on held-out renders.

Taking a second picture brings both benefits and costs. Because the votes are places on the table and the camera pose is known, the new picture's votes go into the exact same plane as the old ones. There is no matching problem to solve, and no pairing of regions between views. The piles simply gain more voters from a better angle. That is a direct consequence of voting in table coordinates, and it would not be available at all if the arrows were measured in pixels.

The cost is arm motion, which is by far the most expensive resource in this cell. Because of this, the loop is capped at a small number of extra looks per doubtful pile. If a pile is still doubtful after that, it is reported as an unseparated pair, along with its position and its reason, and handed over to problem three. 

That is considered a result rather than a failure. The rule the whole project runs on applies here too: anything doubtful is reported, and never guessed.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page explains what happens when the glasses are completely hidden. A glass can be missing from a picture altogether. It is standing on the table, it is solid, the depth camera is pointed straight at the part of the table it is on, and not one pixel of it comes back. This section works out what this solution does about that. It is for anyone deciding how much of the second problem this solution can be asked to carry on its own, and the answer has two halves that point in opposite directions, so it is worth going through both.

Start with what makes this solution's position unusual. Every other method on these pages separates two glasses by finding something between them, like a gap in the picture, a strip of bare table, or a seam. This one finds nothing between them. Each glass pixel votes for where its own glass's centre is, and it casts that vote whether or not anything can be told apart anywhere. So a glass that is partly covered still speaks. Its surviving pixels vote for the right centre, and they do not have to be joined to each other, or to make a recognisable shape, or to lie on any particular part of the glass.

A large glass standing in front of a small one hides much more of it than a glass of its own size would, so a glass can be left with only a crescent of itself in the picture, at the gap the cell guarantees. That is uncommon rather than the normal case, because it wants a crowded line of glasses running out from the point below the camera. But it is the case voting is unusually good at, so it is worth putting a number on how good.

First, the arithmetic needs very few votes. A vote is the pixel's own place on the table plus the arrow to its own glass's centre, so every vote is an estimate of the same point, and averaging several of them shrinks the scatter. Against the held-out spread of six millimetres this document calibrates everything else against, five votes put the peak within four point six millimetres of the true centre nineteen times in twenty, and twenty votes put it within two point three millimetres.

Second, finding a pile that small is the harder half. The windows are started from a few hundred votes drawn at random, as the part about choosing the one window size describes, and a pile only gets a window started in it if one of those seeds lands in it. In a picture holding about seventeen thousand votes, a pile of twenty is found by three hundred seeds thirty per cent of the time. A pile of a hundred is found eighty-three per cent of the time, and a pile of three hundred, which is under two per cent of the picture, is found ninety-nine point five per cent of the time. That floor is a choice rather than a law. Seeding a window at every vote removes it entirely, at the price of the arithmetic that made the sampling worth doing.

Finally, the vote count check refuses to believe a pile that small anyway. That is deliberate and it is argued in the section on having too few votes, whatever the spread. A crescent's votes agree with each other and are wrong together.

So the honest figure is a few hundred pixels, which is well under a tenth of a glass, for voting to find a hidden glass and place it to a millimetre or two.

None of which helps when the number is nought. A glass that is covered completely owns no pixels, so it casts no votes, so there is no pile to find, no spread to be loose and no count to be short. The vote map simply has one peak where two glasses are standing, and nothing in it is wrong. Both of this solution's own alarms are measurements of votes, and there are no votes to measure.

That is a limit rather than a bug, and it is the same limit every method here that works from pixels runs into. This solution cannot handle the completely hidden case and must hand it on. What it hands on is not a glass but a region, which is the part of the table it could not have seen. Working out that region is arithmetic on splay and on the glasses that were found, and it belongs to the page on clustering on the table. Deciding which of those places is worth spending a picture on belongs to the page about whether anything is hiding there. Moving the camera and taking that picture belongs to the page on moving the camera.

It is worth settling whether more training would help, because it is the first thing anyone suggests, and the reason it cannot is worth being exact about.

Take the scene with the hidden glass and the same scene with that glass removed. The two produce the same picture, pixel for pixel. No function of the picture can tell them apart, whatever its shape and however it was fitted, because the thing that differs between the two scenes left no trace in the input. This is the one limitation in this document that is a fact about the input rather than about the model.

There is a qualification that deserves working out rather than waving at, because it is the obvious objection. A network can be trained to mark part of an object it cannot see. The name for that is amodal segmentation, which means predicting an object's whole extent rather than only the visible pixels of it. It is ordinary rather than exotic; it is what lets a person report one cat behind a railing instead of five slices of cat. The silhouette of a tall glass is sometimes consistent with something standing behind it, so a network could in principle learn to mark that, and the simulator can supply the label to train it on.

The first head described earlier does not do that. It has one output channel and it is trained against the mask the simulator returns for what the camera can see, so the only thing it can learn to mark is glass that is visible. Making it amodal would take three things. First, ask the simulator for each glass's mask with the other objects taken away, which costs no more than the visible mask. Second, train against that instead. Third, accept that the mask now claims pixels whose evidence is some other object's surface, so the circle fitted to those pixels is a prediction rather than a measurement.

Even then it would not answer this section's question, and the reason is the same one as before. Amodal completion extends evidence, so it needs some of the object to be visible to extend from. With no pixels at all there is nothing to extend, and a model asked to mark a glass that might be behind this one would be inventing a scene rather than reading a picture. The same limit is written down for the hardware version of the idea, on the page about needing more than a simulator, and the right machinery for a guess about a scene is not a segmenter at all.

The two parts below work out how a glass comes to be covered in each of the cell's two views, because the geometry is different in each and so is the handful of pixels that survives when the covering is not quite complete.

When the camera is looking straight down, the survey looks from four hundred and fifty millimetres above the table top. The table is the furthest thing from the lens and a glass's rim is the nearest, because the rim has climbed most of the way from the table towards the camera, and anything nearer the lens is drawn larger and further out from the middle of the picture.

The arithmetic is exact. A slice of a standing glass at height z is drawn as though it had been scaled about the point directly below the camera by a factor k. This factor k equals the camera's height above the table top, divided by that height minus z. At the survey height, a slice two hundred and twenty-five millimetres up has a factor of four hundred and fifty divided by two hundred and twenty-five, which is two. Its circle is drawn at twice its real distance out from that point, and at twice its real radius. This project calls that outward stretch splay.

Now take two glasses of the one kind, both drawn from the project's own range. One is two hundred and twenty-three point eight millimetres tall with a rim one hundred and two point nine millimetres across, so its rim is scaled by one point nine nine. The other is ninety-three point eight millimetres tall with a rim eighty-three point six millimetres across, so its rim is scaled by one point two six. Stand the tall one two hundred and five millimetres out from the point below the camera and the short one one hundred and fifty millimetres further out along the same line. One hundred and fifty millimetres is the closest two glasses ever stand, so this is an ordinary arrangement rather than a contrived one.

The tall glass's splayed outline then contains the short glass's outline entirely. Nought of the short glass's four thousand, six hundred and sixty-nine pixels reach the picture.

What comes back is one patch of sixteen thousand, seven hundred and eighty-one pixels. Those pixels back-project to a footprint one hundred and three millimetres across, and the widest this kind of glass can be is one hundred and five millimetres, so the patch is an entirely legal width and nothing about it looks wrong. It is worth being clear about why the patch measures one hundred and three millimetres when its outline in the picture spans three hundred and twenty-five millimetres. Splay decides which pixels exist; it does not decide where they land. Each pixel's depth reading puts it back at its own true place on the table, so the tall glass's pixels come back as its own real footprint.

Hiding this way needs two things at once. The two glasses have to be close together, and they have to differ a lot in height, because the scale factor grows with height and it is the difference in scale that lets one outline sweep over the other. The hidden glass is therefore always the shorter one.

It also depends on where the pair is standing relative to the point below the camera, because splay runs outwards from that point and nowhere else. A table in the text shows what happens if you keep the two glasses one hundred and fifty millimetres apart and swing the short one about the tall one, away from the line running out from the camera. At zero degrees, and at eight degrees, nought of its roughly four thousand seven hundred pixels reach the picture. At twelve degrees, eighty-seven pixels survive. By twenty degrees it is six hundred and sixty-three, and at thirty degrees it keeps two thousand, one hundred and seven. At ninety degrees, all four thousand and forty-three of its pixels reach the picture. The whole-glass count changes a little as it swings because moving the glass changes how large it is drawn.

A pair lying along that line hides. The same pair lying across it does not hide at all. And the change between the two is quick: the short glass goes from invisible at eight degrees to keeping nearly half of itself at thirty.

A diagram shows the short glass under the tall one's splayed outline, and then the same pair swung twelve degrees. In the straight-line case, there is just one peak where two glasses are standing, and the peak that is there is in exactly the right place with an entirely believable width behind it. Swung twelve degrees, the short glass keeps eighty-seven pixels, which is under two per cent of itself, appearing as a thin crescent along one edge. A window started in those votes comes to rest one point one millimetres from where the glass really stands. A boundary method has nothing to work with there, because there is no boundary between the two outlines to find. Voting does not need one.

One measurement is worth recording about which pixels survive, because it decides how hard the network's job is. Looking straight down, the mouth of the glass is visible and it is the part nearest the lens, so it is the first thing a covering outline takes. What is left is a strip of far wall and far rim. Those survivors sit on average forty-one point seven millimetres out from their own glass's centre, on a rim radius of forty-one point eight millimetres, against twenty-nine point four millimetres averaged over the whole glass. They are the most extreme pixels the glass has, which means their arrows are the longest the network is ever asked to predict.

When the camera is looking level, the measuring view is different in kind. The camera stands one hundred and twenty millimetres above the table top and three hundred and eighty millimetres back from the glass it is looking at, and it looks level. A level camera throws nothing outwards, so splay plays no part at all. What happens here is plain line of sight: the near glass is in the way.

Put the short glass straight behind the tall one and it disappears, and the distance between them buys nothing whatever. Nought of its pixels survive at one hundred and fifty millimetres apart, nought at three hundred millimetres, and nought at six hundred millimetres. The reason is that the near glass is nearer, so it is drawn larger. The tall glass, one hundred and two point nine millimetres across, is seventy-five pixels wide in the picture at the standoff, while the short glass, eighty-three point six millimetres across, is thirty-four pixels wide at three hundred millimetres behind it.

So the hidden glass here is the further one, whatever its height. Swap the two round and the magnification works the same way. The near short glass is sixty-one pixels wide in the picture against the far tall glass's forty-two, so it covers twenty-six per cent of that glass, hiding the lower part of it up to about the height of its own rim.

A second diagram shows the far glass straight behind the near one, and then the same pair with it stepped thirty millimetres aside. When straight behind, there is one peak where two glasses stand, and again there is nothing wrong with it: eight thousand, six hundred and twenty-eight votes, a fitted footprint one hundred and two millimetres across, and a tight pile. Step the far glass thirty millimetres to one side and seventy-six of its one thousand pixels survive, as a strip down the edge of the near glass's outline, and a window started in those votes comes to rest zero point six millimetres from the truth.

The survivors sit differently here, and the difference is smaller than it sounds. Looking level, the lens is below the rim of anything tall, so there is no mouth to lose in the first place, and the strip that survives sits thirty-five point five millimetres out from its own centre against thirty-one point eight millimetres over the whole glass. Looking straight down, the surviving pixels were the most extreme the glass had; from the side they are barely more extreme than average.

What the two cases share is the thing that matters to the network. Whichever view it is, the pixels that survive are a crescent down one edge, and every pixel of that crescent sees the same one-sided part of the glass. So their arrow errors agree with each other rather than cancelling, which is exactly what the count check in the section on having too few votes exists to catch. The arithmetic earlier in this section is therefore a floor on what is possible and not a promise about what a trained network will do.

And when the crescent is empty, none of that applies. There is no strip, no pile, no spread and no count. The only remaining question is a geometric one about where a glass could have been standing unseen, and this solution does not answer it.

<!-- section: a-worked-example | A worked example -->

The next part of the page walks through a worked example to show how this works in practice. Everything in this example follows from the work cell's own constants and nothing else.

First, consider the scale. When seen from the top, one pixel covers a millimetre or two of the table. This means a glass's footprint is a few tens of pixels across, and its outline covers a disc of that width, which adds up to well over a thousand pixels. That means there are over a thousand votes per glass, and this is the crucial number to keep in mind for everything that follows.

Next, look at the case that defeats simple clustering. Imagine two glasses of one kind standing much closer together than the cell normally allows, so that the strip of bare table between their rims is narrower than the grouping distance used in solution two. The chain of pixels crosses that strip, so the two sets of points come back as a single group. This group spans both glasses plus the gap between them, making it far wider than any single glass of this kind can be. So, solution two's range check fires correctly, but it fires on a blob that it has no way whatever to divide.

Now look at what the votes do in this same situation. The pixels of the two glasses are exactly as merged as before, because nothing has changed about them. However, their votes are not merged. Each glass's pixels point inwards at their own glass's centre. Because of this, the votes land in two distinct piles, and their separation is the full centre-to-centre distance. This is comfortably more than the mean-shift window can span, so the two piles stay two. Both piles are tight, with a spread that falls inside the held-out figure, and circle fits on the two sets of voters come back inside the expected range for that kind of glass. 

So, from a picture where the pixels themselves never came apart, the system successfully finds two glasses, two positions, two masks, and two widths. That is the entire idea of this solution in one example.

But there is also a case that defeats voting. Suppose you stand one glass mostly behind another, so that only a crescent down one side of it is ever visible from the top. This hidden glass contributes only a small fraction of the votes it should. Worse, every single one of those votes comes from that same crescent. As a result, the votes agree with each other, but they are wrong in the exact same direction, which is exactly what a one-sided view does. The pile of votes lands noticeably off the true centre, and its spread comes out to be several times larger than the held-out figure. 

Notice that the vote count and the spread both complain, independently, and that neither of them is the network's own opinion of itself. They are direct measurements of the votes.

Because the spread is over the threshold, the system has to fix it. The arm takes one more picture. It moves to take this from the side, standing back at the measuring standoff, looking level, and looking across the line joining the two glasses. Standing that much closer, each pixel covers far less area, so the glass fills much more of the frame than it did from the top. This gives more pixels on the glass, from a direction where nothing is in front of it. In this new view, its votes come back to a normal spread, and the peak lands exactly where it should.

Finally, consider what this fix costs in time. Running the network on a picture costs milliseconds, but moving the arm to the new pose and letting it settle costs seconds. The whole design of the loop follows from that ratio: compute freely, and move rarely.

<!-- section: what-it-needs | What it needs -->

The next part of the page explains what this solution needs. It is the most demanding solution in this folder to set up, so it is worth being plain about what that means before anyone starts. 

First, it needs a deep learning framework and the environment to run it in. This is a large dependency for a cell where the recommended answer is just a page of arithmetic. 

Second, it needs a training set. The simulator renders and labels this for nothing. This is the one genuinely cheap part, and it is what makes training from scratch reasonable here at all. 

Third, it needs hours rather than minutes of that rendering, and a similar amount of time again for training, on the machine this project runs on. 

Finally, once trained, it needs a file of weights that must be kept in step with the world. If you change the lighting, the camera, or the range of sizes a kind of object is drawn from, the file becomes quietly out of date in a way that no test of the code will notice.

Against all that, what the solution needs at run time is small. One pass of a small network over a small picture takes only milliseconds. This is nothing compared to the seconds an arm movement costs, so the cost of this solution is entirely in building it, rather than in running it.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page covers where this network is strong and where it breaks. 

First, it needs no depth readings. This is its most important strength, and it is the reason this document exists. Every programmed solution in this project rests on the depth camera returning points on a glass, but real glassware returns almost none. A method that works from color alone is the one that survives contact with real glass.

Second, it separates glasses that touch. Nothing here has to find a boundary, so nothing can get a boundary wrong. Every other method on these pages needs a gap of some kind, whether that is a gap in the picture, a strip of bare table, or a seam. When two glasses touch, there is no gap anywhere to find. This is the only method that does not care.

Third, it is unusually good at finding partly hidden glasses. Even if only a crescent of pixels survives, those pixels still vote towards the right center, and the votes do not have to be joined to each other or make a recognizable shape. Because one kind of vote spans everything from a small tapered glass to a large one, a glass can be left with only a crescent of itself even at the gap the cell guarantees. While this is uncommon rather than the normal case, it is exactly the situation that voting handles best.

On the other hand, the network is blind to a glass that is hidden completely. If there are no pixels, there are no votes, which means no pile, no spread, and no short count. This is a fact about the input rather than about the model, and the previous section worked it out in full.

Another weakness is that its answer cannot explain itself. When a mathematically fitted circle is wrong, you can print one number and see exactly why. When a network is wrong, you can only look at the picture and guess. The arithmetic wrapped around the network is what makes that lack of transparency tolerable.

Finally, its weights are a second copy of the world. The code says what the cell is, but the weights say what the cell looked like on the day they were fitted. Keeping those two in step is a maintenance job that the programmed solutions simply do not have.

<!-- section: the-general-ideas-behind-this | The general ideas behind this -->

The next part of the page covers the general ideas behind this approach. It uses mainstream deep segmentation and mainstream voting, both shrunk down. Every component is standard, and most of them are ten years old. Two things here are unusual: the decision to train from a random start on synthetic data rather than fine-tune something large, and the decision to have one network answer a question about classes and a question about instances from the same shared body.

The first idea is semantic segmentation, which means producing a class label for every pixel rather than drawing a box around an object. The idea became practical with fully convolutional networks, introduced by Long, Shelhamer, and Darrell, which replaced a classifier's final layers with convolutions so that a picture of any size maps to a label map of the same size. 

It is used for medical imaging, satellite and aerial pictures, driving scenes, and industrial inspection. It is useful anywhere the extent of a thing matters more than a box around it. It is rarely right for counting or separating individuals, because a class label has nowhere to record which object a pixel belongs to, so two touching things of the same class come back as one region. That is the limitation this solution runs into, and that solution eight removes.

The next concept is the encoder-decoder with skip connections. The network repeatedly halves the resolution while widening the channels, and then doubles it back up. On the way down, it copies each level across to the matching level on the way up, so that detail lost going down is available coming back. This is the U-Net, designed by Ronneberger, Fischer, and Brox for biomedical images with very few training examples, which is exactly why it suits a small synthetic dataset. 

It is used for labelling every pixel when data is limited, such as cell and organ segmentation, defect detection, and depth estimation, and it remains the default architecture for a small segmentation problem. It is rarely right for problems needing a broad understanding of a scene or many classes, where a large pretrained network earns its size, because a small network knows only what its receptive field and its training set contained.

Then there are overlap losses, which score the shape rather than the pixel count. Cross-entropy averages over pixels, so on a picture that is mostly background, a model can score well by predicting background everywhere. Dice and intersection-over-union losses score the overlap between the predicted and the true regions instead. As Milletari and colleagues showed, they are usually added to cross-entropy rather than used in place of it. 

They are used wherever one class is far rarer than the other, which covers most medical and industrial segmentation. They are rarely enough on their own, because an overlap score says nothing about how confident the individual pixels were, which is exactly the information the feedback loop in this document runs on.

The next idea is domain randomisation, which means training on variation instead of realism. Following Tobin and colleagues, the approach is to vary everything you are not trying to teach, over a range wider than reality, so that the model cannot key on any of it. 

It is used wherever training data comes from a simulator and has to work somewhere else, which is most of robotics. It is rarely sufficient on its own for fine visual judgements, because randomising appearance makes a model ignore appearance, and sometimes appearance is the signal.

Next is the choice between training from scratch and fine-tuning a large model. This is the choice this whole document turns on. Fine-tuning wins whenever labels are scarce, which is almost always. Training from scratch wins in the narrow case where labels are free, the problem is small, and the borrowed weights would bring knowledge of a world you do not have. This cell is that narrow case, and it is worth noticing how rare that is rather than generalising from it.

The next concept is the Hough transform, which uses local evidence for a global claim. A single edge pixel cannot say where a shape is, but it can vote for every shape that would explain it. Add up the votes, and the peaks are the shapes really present. Hough's 1962 patent did this for straight lines in bubble-chamber photographs, and the generalised Hough transform, published by Ballard in 1981, extended it to any shape at all by replacing the equation with a lookup table of offsets. 

It is used for finding shapes in noisy, cluttered pictures where much of the outline is missing, such as lines, circles, and ellipses in inspection, document analysis, and lane finding. Voting is naturally robust to things being hidden, because the visible part still votes correctly. It is rarely right for shapes with many parameters, because the table of votes grows explosively with them, and it is also poor when a learned detector is available and the shape has no clean equation.

Building on this is learned voting, which replaces the lookup table with a model. Hough forests, introduced by Gall and Lempitsky in 2009, first replaced the hand-built table of offsets with a learned one, so that patches vote for an object centre and a fitted model decides how. The neural descendants apply the same structure to points and pixels. VoteNet has points from a depth sensor vote for object centres, and PVNet has pixels vote for landmark points when working out an object's orientation, specifically because voting survives things being hidden. 

These are used for finding objects and their orientation when much is hidden and the scene is cluttered, such as bin picking and crowded scenes, because a method needing the whole object visible fails there while a method needing only a fraction does not. They are rarely right for objects with no well-defined centre, or where the offsets are large compared with the picture, because then the number the network has to predict grows and the votes scatter.

Next is using per-pixel offsets as a way to separate objects. The general problem this solves is that a class map has nowhere to record which object a pixel belongs to. Predicting an arrow per pixel, towards its own object's centre, is one of two standard answers. The other is to have the network give each pixel a made-up identity code and group those codes instead, which is called associative embedding, introduced by Newell and colleagues. Offsets fail more gently than predicting boundaries, and the comparison is worth remembering as a general principle. One bad pixel in a seam rejoins two objects, whereas one bad vote is simply outvoted.

The final idea is mean shift, which finds peaks without being told how many there are. Slide a window to the average of the points inside it, and repeat until it stops moving. Every starting point that ends in the same place belongs to one peak, as described by Comaniciu and Meer in 2002. Unlike methods that divide data into a fixed number of groups, it does not need the count in advance, which is the whole point here, because the number of groups is the answer. 

It is used for finding peaks when the count is unknown, such as tracking, colour segmentation, and exactly this job of turning a cloud of votes into objects. It is rarely right for data with many dimensions, where it is slow and the window size becomes impossible to choose, and it is poor for groups of very different densities, where one window size cannot serve both.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page explains where this network sits among the other solutions. This solution and the programmed ones answer the same question from opposite directions, and the comparison is sharper than it first looks.

On any day the depth readings work, the programmed method of clustering on the table is better in every way that matters here. It is a page of arithmetic rather than a file of weights, it needs no training set, it explains its own failures, and it places a glass more accurately than this does. Preferring a network on such a day would be choosing the harder tool for a job the easier one already does.

The day this solution earns its place is the day the depth readings stop, which is the day the glasses become real glass. Then the programmed methods lose their input entirely, and this one loses nothing, because it never used depth in the first place. The other such day is the day two glasses are allowed to touch, since that is the case no gap-finding method can answer at all.

What it cannot do, on any day, is notice a glass that is absent from the picture. That failure is answered by geometry rather than by appearance. The method of clustering on the table works out where a glass could have been hiding. The method of moving the camera acts on that argument by choosing somewhere else to stand, and the approach of asking if anything is hiding there is the learned version of deciding which hiding place is worth the trip. This solution contributes the masks those three argue from, and none of the argument.
