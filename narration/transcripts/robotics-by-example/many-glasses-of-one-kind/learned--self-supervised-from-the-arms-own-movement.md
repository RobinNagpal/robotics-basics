<!-- section: lead | Solution 7 — self-supervised from the arm's own movement -->

Solution 7, self-supervised from the arm's own movement. 

This solution is learned, and acts as the decider. Because the arm knows exactly how it moved the camera, the geometry between two pictures of a still scene provides a free training signal.

The physical setup is described once on the page about the cell. That page covers the layout, the two places the camera works from, which are from the top and from the side, all four sensors, and the terminology this project uses for them. What follows here is only what is specific to this solution.

<!-- section: introduction | Introduction -->

Solution seven, self-supervised from the arm's own movement. 

The introduction to this page explains the one learned method here whose training would survive being moved to a real robot. The problem it addresses is that teaching a network which pixels belong to which glass normally needs somebody to draw around every glass in every picture, and that cost is where most of the expense of a learned method lives. The idea here is that the arm already knows exactly how it moved the camera, and that knowledge is enough to supervise the training by itself. 

By the end, you will understand four things. First, how movement becomes a label. Second, why the camera has to work from the side rather than the top for this to work at all. Third, how the arm can calculate in advance exactly how far it must move to settle a particular doubt. And finally, why this solution is nevertheless not the one to build for this cell.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solution solves. 

Imagine four to six glasses standing on a table. They are all of one known kind. The robotic arm has to determine which pixels in the camera image belong to which glass, assign each glass a position on the table, and honestly report any pair of glasses that it could not separate.

The main difficulty is not simply seeing the glasses, but telling one from another. Even if two glasses are a valid distance apart on the table, they will overlap in a photograph whenever the camera happens to line up with both of them. The usual method for finding objects is to take every pixel that stands above the table top and group the ones that touch. However, when glasses overlap in the image, this method groups them together and returns a single blob. To everything downstream in the system, one blob means one glass, and this mistake does not announce itself.

A machine learning method could draw the boundary between the glasses that the simple touching-pixels rule cannot. But a learned method has to be trained, and training requires the correct answer to be provided alongside each example. These correct answers are called labels, and acquiring them is where most of the cost of a learned method lies.

The diagram in this section illustrates three different ways to obtain these labels, placing them side by side. 

The first column shows the usual recipe, where a person manually draws a boundary around every object, thousands of times over. 

The second column shows what the other learned solutions in this project do. Because they run in a simulator, the simulator already knows which object produced each rendered pixel, making the labels completely free. 

The third column shows the approach used in this solution, and the difference is the main point of this entire document. Its supervision does not come from inside the simulator at all. Instead, it comes from the arm's joint encoders, which a real physical arm also has. This is a crucial advantage. Everything else learned in this project would have to be retrained from scratch, requiring new labels, on the day the code is moved to a real camera. This solution would not.

<!-- section: the-main-idea | The main idea -->

The next section covers the main idea of this solution. It rests on one fact about the robot cell that is easy to pass over. 

Because the camera sits on the wrist, the arm knows exactly how far it moved the camera between taking two pictures. This movement is not estimated from the pictures themselves. Instead, it is explicitly commanded by the system, and then read back from the joint encoders to a fraction of a millimetre. 

Once this movement is known, basic geometry dictates where each surface point must land in the second picture, depending on how far away it is. Because of this, points on one object, like a glass, will move together in the image, while points on a glass behind it will move by a different amount. That agreement between the points is the label used for training.

The rest of the page builds this concept up step by step. First, it explains the visual effect the whole method depends on. Second, it covers why the camera must be positioned in one particular way for that effect to exist at all. After that, it shows how the arm can turn the effect into a dial that it controls. Then, it explains how this agreement becomes something a neural network can output. Finally, it discusses what keeps the network's answer honest.

<!-- section: parallax-the-shift-is-one-divided-by-the-depth | Parallax: the shift is one divided by the depth -->

The next part of the page explains parallax, where the visual shift is one divided by the depth. You have likely seen this effect from a moving train, where the near fence races past the window while the far hills barely move at all.

When the camera slides sideways, a surface moves across the picture by an amount that is the slide divided by the depth. That formula is easier to remember as a shape than as arithmetic: the shift goes as one divided by the depth. Near things move a lot, far things move a little, and things at infinity do not move at all.

A diagram on the page illustrates this with two plots. The left-hand plot graphs apparent shift against depth, drawing out that formula. Because it is one over the depth, the curve is steep close up and nearly flat far away. So, the same small difference in depth is worth a great deal of separation near the camera, and almost nothing far from it. The plot marks a hard case to show this: two glasses whose depths differ only slightly, sitting out where the curve has gone flat. Here, they separate by barely more than the noise in the matching.

The right-hand plot graphs separation against the camera's slide. This is what makes this a method rather than just an observation, and it is covered next.

<!-- section: why-the-camera-must-work-from-the-side | Why the camera must work from the side -->

The next part of the page explains why the camera must work from the side. This is the condition the whole solution depends on, and it is worth being exact about, because getting it wrong would produce a method that cannot work at all.

Parallax separates two surfaces by how far apart they are in depth. Because of this, it can only separate two glasses if the gap between them is much larger than the range of depths each glass covers by itself.

Working from the top fails that test outright, and for two separate reasons. 

The first is that two glasses of the same kind have their rims at nearly the same height, and therefore at nearly the same distance from a camera looking down at them. There is almost no depth gap between the two objects to work with.

The second reason is worse. Each glass on its own runs all the way from its rim, well up towards the camera, down to the table far below it. So each glass by itself covers a wide range of depths, and therefore a wide range of shifts. And both glasses cover the exact same wide range. Two groups of shifts lying exactly on top of each other cannot be told apart at any slide whatsoever.

It is also worth saying that working from the top does not produce the merge problem in the first place. This was checked against every legal arrangement the cell's scene generator can make, and with both glasses wholly inside one frame, none of them merged.

However, if you turn the camera on its side, the whole geometry turns with it. The station is the same one the shape measurement uses. It looks from the side, low down, standing back at the measuring standoff. 

The diagram illustrates this by showing that the scene stands still while only the camera moves. Now look at what changed. A second glass standing in line behind the first is a long way further back, much further than the width of either glass. So the gap between the two objects is now large, while the range of depths each glass covers by itself is only its own width, which is small. The two groups of shifts end up far apart, which is exactly the condition parallax needs.

The diagram shows the effect of this in two frames on the right. The near glass moves a long way across the picture, and the far one moves noticeably less. The gap between them grows, and that growth is the only thing in the two pictures that says they are two objects. They are the same kind, the same colour and the same shape, so their appearance says nothing at all here.

At each station the arm slides the camera sideways and photographs as it goes. Because a picture costs milliseconds while an arm movement costs seconds, it takes several pictures along that slide rather than just two. That costs almost nothing extra and gives many pairs per station instead of one, because every picture can be paired with every other.

That slide turns out to buy something this problem needs, and it is set out in the later part of the page about when the glasses are completely hidden. The same sideways movement that separates two glasses by depth also swings the region each glass hides behind it, so a glass covered completely at one end of the slide can be in plain view at the other.

<!-- section: the-dial-separation-grows-in-step-with-the-slide | The dial: separation grows in step with the slide -->

The next part of the page explains how the arm acts as a dial, where the separation between shifts grows in step with the slide. The right-hand plot of the picture shown earlier is what turns this from an observation into a practical method. It shows that the separation between the two groups of shifts grows in step with the slide. If you double the slide, you double the separation.

This turns the arm into a dial. If the separation is not enough, you can go and buy more of it, and you can work out in advance exactly how much you need to buy.

Here is the calculation, which is the most useful idea in this document. Because the relationship is linear, each millimeter of slide buys a fixed amount of extra separation. Therefore, you can divide the total separation you need by the separation that one millimeter buys. This gives you the exact slide needed to settle this particular doubt, and you have this answer before the arm has moved at all.

That is worth comparing with the alternative. A method whose answer to an unclear case is to run a bigger network on the same picture is trying to extract information that was never in the picture to begin with. No amount of computing puts it there. Moving does.

<!-- section: how-movement-becomes-a-training-signal | How movement becomes a training signal -->

The next part of the page explains how movement becomes a training signal. We now have the effect and the control. The remaining question is how a network gets trained on it, and the answer has two halves.

The first half teaches the network to predict depth, with no depth labels at all. The network predicts a depth for every pixel of the first picture. Then that predicted depth, together with the camera movement the encoders give, says where each pixel should have landed in the second picture. So the first picture is warped into the viewpoint of the second. Every pixel is moved to where the predicted depth says it should now be.

Then, the warped picture is compared with the real second picture, pixel by pixel, on brightness. Where the warp lands on matching brightness, the predicted depth was right. Where it does not, the mismatch is what training pushes down. That comparison is called the photometric loss, and it is the whole of the supervision. It uses just two pictures and two encoder readings, and nobody labels anything.

The second half of the answer turns this agreement into groups. Once the depth is roughly right, the shift of each pixel follows from the formula, so pixels can be sorted into pairs. Two pixels whose shifts agree to within the measurement noise are a positive pair, meaning they are on the same surface. Two whose shifts differ by clearly more than the noise are a negative pair.

Now the network is asked for a second output. At every pixel it produces a short list of numbers, which is called an embedding, and the list is arranged so that two lists being close together means the two pixels belong together. Training that is called a contrastive loss, and its shape is simple. Pick a pixel, take its positive partner and a handful of negatives, and the loss is low only when the partner is closer than every one of the negatives. So it pulls a pixel and its partner together, and pushes it and its negatives apart.

The diagram shows this embedding, where every pixel becomes a point. In the right-hand panel of the picture, the pixels of the two glasses have landed in two clumps.

Note carefully what that picture does not contain, because it is the honest limit of the method. Nothing in it names a glass and nothing counts them. The embedding says which pixels belong together, and something else has to decide how many groups there are.

At run time only the embedding runs. One picture goes in, and one short list of numbers per pixel comes out. Those lists are clustered, and each cluster is a candidate region.

<!-- section: the-arithmetic-still-decides | The arithmetic still decides -->

The next part of the page explains how the arithmetic still decides the final outcome. Every candidate region goes through the ordinary arithmetic, which is unchanged from the second solution about clustering points on the table. Using the depth frame, the pixels of the candidate region become points on the table. A circle is then fitted to these points, and the region is kept only if its width is one that this kind of glass could actually have.

So, the network proposes and the arithmetic disposes. This keeps the self-supervised solution inside the same safety argument as the fully programmed ones. This safety check matters here more than usual, because a merged pair comes back from the embedding as one tidy region with no complaint at all.

<!-- section: how-the-concepts-fit-together | How the concepts fit together -->

The next part of the page explains how all these concepts fit together. The section includes a flowchart that maps out the entire process, dividing the steps into three categories: work the project already does, new steps added by this solution, and the neural network with its two training losses. Let's walk through that chain of events.

The sequence begins with the robot's existing behaviors. The arm positions the camera at the side, low down, and back at the standoff distance. It takes several photographs along one sideways slide, and reads the arm's encoders to find out exactly how far the camera moved. 

Then, the new steps and the network take over. The system warps the first picture into the second using the predicted depth. It compares the brightness of the two, which provides the first training loss to train the depth. Because of this, each pixel's shift now follows directly from its depth. The system can then assume that pixels whose shifts agree are part of one surface, and pixels whose shifts differ are not. 

This leads to the second training loss, the contrastive loss, which pulls the agreeing pixels together and pushes the differing ones apart. 

At run time, the network simply outputs an embedding, which is one short list of numbers for each pixel. The new code clusters these lists into candidate regions. 

Finally, the existing code takes over again to fit a circle to each region on the table. It checks if the width is a valid size for this kind of glass. If it is, the system reports the glass. If not, it reports the pair as unseparated and hands it on to whatever comes next.

There are two important things to notice about this chain. The first is that all of the training steps happen offline. When the robot is actually running, only the embedding survives. The second is that the boundary the embedding draws is based on where the shift changes. This means it finds the edges where the depth jumps, rather than where the brightness changes. Because it relies on physical depth instead of visual appearance, two identical glasses are no harder for this method to separate than two different ones.

<!-- section: the-feedback-loop | The feedback loop -->

The next part of the page covers the feedback loop. Most learned components answer whatever they are asked and give no useful sign when they should not have. This one gives a sign, because the doubt has a number attached. That number is how wide the clear air is between the two groups of shifts. If the gap is wide, the answer is settled. If it is narrower than the noise in the matching, it is not settled, and the method can say so rather than guessing. 

A diagram here illustrates this deliberate-motion loop, showing how the next slide is worked out. 

This doubt is unusually actionable, because of the dial described earlier. The arm can divide the separation it needs by the separation one millimetre of slide buys, and go exactly that far. It has priced the answer before moving.

But the dial does not turn for ever, and three limits stop it. All three are arithmetic rather than opinion.

The frame is the first limit. A long slide moves everything a long way across a picture that is only so wide. The ordinary slide moves the near glass by a fraction of the frame, so the pair still shares most of it. A slide several times longer moves the near glass most of the way across, and eventually out of the picture altogether, at which point there is nothing left to compare. A glass starting in the middle of the picture reaches the edge after half a frame width of shift, and the formula says exactly how much slide that is. Past that, the camera has to be re-aimed and the rotation warped out afterwards. This is exact because the rotation is commanded too, but it is extra machinery.

The reach is the second limit. The glasses stand in a zone only so large, and the arm works comfortably only within a band of distances from its base, so a slide much wider than the zone itself simply cannot be made from some places on the table. Past a certain length this has stopped being one station with a long slide and become a second station somewhere else, which is the job of the move the camera solution rather than this one.

The budget is the third and final limit. An arm movement costs seconds while running the network costs milliseconds, so the loop has to stop when nothing is unclear, or when the budget is spent. A pair the arm could not separate is a result this problem asks for, and not a failure.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page explains what happens when the glasses are completely hidden. Everything above this point assumes that each glass puts at least a few pixels into the picture. The hardest case this problem has is the one where a glass puts in none at all. That is not a small region or a doubtful boundary. It is nothing, and nothing is what every method in this project works from, so a glass with no pixels cannot be counted, measured or reported by any of them.

Of the nine solutions this one has the most direct answer to that case, and it is worth being exact about why before saying how far the answer goes. The signal this method lives on is the difference between how far a near thing and a far thing shift when the camera moves, and that difference comes from the shift going as one divided by the depth. A glass that contributes no pixels is hidden from one place the camera stood. Move the camera and it stops being hidden. The movement that reveals it is the same movement the method already makes in order to train, so the reveal costs no extra arm time.

That is the claim. What follows is the arithmetic behind it, and it comes out differently for each of the two places this cell puts its camera, because a glass is hidden in each of them for a different reason.

First, consider when the camera is looking straight down. The plain answer is that this solution never works from the survey view. The earlier section on why the camera must work from the side shows why, and the short of it is that looking down leaves this method nothing to measure at all. So hiding that happens up there is not a case this solution handles, and pretending otherwise would be inventing a treatment for a view the method never uses.

It is still worth following how the hiding works, because it is the difficulty the whole of problem two is named after, and because the geometry turns out to say something useful about where it can happen.

A camera looking straight down does not draw a glass's outline over the glass. A horizontal slice of the glass at height z above the table is nearer the lens than the table is, so it is imaged as though it had been scaled outwards about the point on the table directly below the camera. That point is called the nadir, which is the ordinary word for the spot straight below. The scale factor is the camera's height divided by its height above the slice, which is 450 divided by 450 minus z. At the rim of a 225-millimetre glass that is 450 divided by 225, or exactly two. The rim circle therefore lands at twice its real distance from the nadir and at twice its real radius. That outward throw is called splay, and it is what lets a tall glass's silhouette reach across a neighbour that is standing well clear of it on the table.

When the splayed silhouette of the tall glass contains the whole splayed silhouette of the short one, the short glass contributes no pixels. What comes back is one patch, and it is exactly the patch the tall glass would have made standing by itself, so nothing about it looks wrong. Hiding this way needs two things together: the two glasses close to each other, and very different in height. The hidden one is always the shorter.

Splay runs outwards from the nadir, so where the pair sits relative to the nadir is what decides whether it hides. A pair lying along a radius from the nadir hides. The same pair turned across a radius does not. Sliding the camera sideways moves the nadir, which swings the splay, which ends the hiding.

A diagram shows two glasses of the kind's extreme sizes, projected through the overhead camera at four positions along one slide. It stands the tallest glass the kind allows, 230 millimetres, 200 millimetres out from the nadir, and the shortest it allows, 90 millimetres, a further 150 millimetres out along the same radius. 150 millimetres is the closest two glasses in this cell are ever allowed to stand. Where the camera already is, the short glass is entirely inside the tall one's outline. A slide of 48.5 millimetres outward along that radius brings the first points of its outline clear, and a slide across the radius does it in 76 millimetres. Both are shorter than the 120 millimetres the arm slides at a station anyway.

But the diagram also draws the frame the picture actually covers as a dashed rectangle, and that is what settles the case. The hidden glass sits between 207 and 294 pixels from the centre of a picture whose own corner is only 200 pixels out, so it is off the edge of the frame. That is not a quirk of this one arrangement. Taking the kind at its extremes, meaning the tallest and widest glass over the shortest and narrowest, at the closest spacing the cell allows, which is the arrangement most likely to hide, the closest a completely covered glass can ever sit to the centre of an overhead picture is 258 pixels. The splay that covers the short glass is the same splay that has already carried it out of shot.

So this kind of hiding never happens to a glass that was in the picture to begin with. It is a question of survey coverage rather than of occlusion, and the cell answers it with the three overlapping stations the survey already runs. Where a glass is genuinely missing from a survey picture, the case is handed to the geometric argument in solution two, which reasons about where a glass could be standing unseen instead of waiting for its pixels. This solution hands that case on and does not pretend to it.

Next is when the camera is looking level. This is the view the method does use: 120 millimetres above the table, looking level, standing back 380 millimetres from the glass being measured. Hiding here needs no splay. It is plain line of sight. The near glass's outline covers the far one's, and that is the whole of it.

Two things follow, and both are the opposite of the overhead case. First, putting the two glasses further apart buys nothing. A far glass standing 250 millimetres behind the near one contributes no pixels, and neither does the same glass at 300 millimetres behind, or at 500 millimetres behind, because it shrinks in the picture as fast as it moves out of line. Second, the hidden one is the further one whatever its height. The near glass is nearer, so it is magnified in the picture, and a short glass in front can cover a taller glass behind.

A second diagram shows four real level-view frames along one 120-millimetre slide, and the count of the far glass's pixels that reach the picture at every slide in between. The pair shown is an ordinary one. The near glass is 181 millimetres tall and the far one 216 millimetres, so the taller of the two is the one that disappears. At the camera's own position not one of the far glass's 1749 pixels reaches the picture.

Now slide the camera, and watch which way the hiding breaks. Both glasses move across the picture, but the near one moves faster, because the shift goes as one divided by the depth and the near one is at 380 millimetres while the far one is at 680 millimetres. The near glass's shift grows 0.32 pixels faster per millimetre of slide than the far glass's, which is exactly the quantity this method was built to measure. The far glass comes out from behind the near one at the rate that difference sets, and it comes out at the base first, where the near glass tapers inwards.

The numbers show that the far glass's first pixel arrives after 48 millimetres of slide, it has fifty pixels by 55 millimetres, and half of it is in the picture by 86 millimetres. The arm slides 120 millimetres at a station regardless, and by the end of that slide 1542 of the far glass's 1749 pixels are in plain view. Because the arm photographs several times along the slide rather than twice, the frames in which the glass appears are already taken and already labelled with the encoder reading that says where the camera was.

That is one pair. Across every arrangement of the project's own glasses in which the far one contributes no pixels at all, which is 75 of them, the first pixel arrives somewhere between 0.5 and 67 millimetres of slide, and fifty pixels between 7 and 71.5 millimetres. The longest slide any of the 75 needs for fifty pixels is 71.5 millimetres, and the station slides 120 millimetres anyway. So for the level view the answer is not that the method could uncover a hidden glass if it were asked to. It is that it has already done so, in pictures it took for another purpose.

Now the part that is not solved, because it is the honest limit of all this. A hidden glass does not announce itself. The arm has no reading that says a glass is missing. It has a picture with one silhouette in it, and a picture with one silhouette in it is exactly what a table holding one glass produces. So the arm cannot price this the way the dial prices an unclear pair: there is no separation to divide by, because there is no second thing yet. It can only slide far enough on the chance that something is there, and the budget for that is finite, because an arm movement costs seconds while a picture costs milliseconds.

Worse, the slide the arm does make was chosen for a different job. Its length and its direction were picked to separate a pair the arm can already see, and a slide that is right for that is not necessarily a slide that uncovers a glass the arm cannot see. The region a near glass hides is a wedge pointing away from the camera, and sliding sideways swings that wedge; but it swings it one way, and a glass hiding on the far side of the wedge has to wait longer. Put the far glass 20 millimetres off the line of sight instead of exactly on it and it is still completely hidden, but now one direction of slide uncovers it after 22 millimetres while the other takes 72.5 millimetres. Push it 30 millimetres off the line and the two figures are 9.5 millimetres and 86.5 millimetres. The arm has no way to know which of those two cases it is in, because the thing that would tell it is the glass it cannot see.

So the plain verdict is that this solution handles the hidden case only partly. Where the camera looks level, which is where the method works, it handles the case genuinely and cheaply, and the evidence is already in the pictures it took to train on. Where the camera looks straight down it handles nothing, and hands the case to solution two and to the survey's overlapping stations. And in neither view can it promise that a glass it has not seen will be revealed by a slide it chose for another reason, which is the case the move-the-camera solution exists to take on, because that solution reasons about viewpoints before it spends them.

<!-- section: a-worked-example | A worked example -->

To see how this works in practice, the next part of the page walks through a worked example that follows one pair of glasses through the method.

Imagine the camera stands at the side. It is low down, level, and standing back from the near glass at the measuring standoff. A second glass of the same kind stands a good distance further back along the same line of sight. It is positioned slightly to one side, so it is not perfectly hidden behind the first.

In the first picture, the near glass is closer to the lens, so it is drawn noticeably wider than the far one, even though the two are the same size in the room. Because the sideways offset is small and the far glass shrinks with distance, its center sits only a little to the side of the near one's center. As a result, the two silhouettes overlap, and the mask comes back as a single blob.

If you measure that blob against the near glass's scale, it is wider than any glass of this kind can be. So, the arithmetic already knows the blob is not one glass. What it does not know is where to cut, which is the whole difficulty.

Now consider the second picture, taken at the other end of the slide. We run both pictures through the network and look at how far each pixel moved.

The pixels of the near glass all moved a lot, because the shift goes as one over the depth, and the near glass is close. They do not all move by exactly the same amount, because the front face of the glass is nearer than its central axis and so moves a little more. This means they occupy a narrow band of shifts rather than a single value.

Meanwhile, the pixels of the far glass all moved much less, and likewise occupy their own narrow band.

Crucially, the two bands do not touch. There is clear air between them because the depth gap between the two glasses is much larger than the depth spread within either one. This is exactly the condition that working from the side was chosen to create. Because the bands are separate, every pixel in the blob belongs unambiguously to one band or the other.

The network was fitted so that pixels whose shift agrees share a direction in the embedding space. Because of this, the two bands land in two separate places there, and clustering hands back two regions.

The boundary between them runs along the silhouette of the near glass, where it crosses in front of the far one. This is an occlusion edge, and not a brightness edge. So the fact that the two glasses are identical in color, shape, and material costs nothing at all. This is the point of the whole method: it draws a line that no brightness-based rule could ever see.

Both regions then go through the ordinary check, and are accepted only if both fitted widths land inside the expected range for that kind of glass. Two plausible circles means two glasses are reported. One implausible circle means the region is rejected and the pair is reported as unseparated. Since the problem explicitly asks for this outcome when things cannot be resolved, reporting them as unseparated is a valid result, and not a failure.

<!-- section: what-it-needs | What it needs -->

The next part of the page outlines what this solution needs to work. 

First, from the robot cell itself, it requires hardware that already exists. It needs the wrist camera, and it needs the camera pose, which is read from the joint encoders using the robot's own description of itself. 

Second, it needs data. Specifically, it requires pairs of pictures from each station, with the encoder reading logged beside every one. What it does not need is just as important. It requires no masks, no per-object labels, and absolutely no spawn record. That last absence is the point of the solution. 

Third, it uses no borrowed weights. Nothing is downloaded, and nothing was fitted to photographs of the real world. Because of this, the whole system can be built entirely inside the simulator, even on a machine that does not have a dedicated graphics card. 

Fourth, in terms of time, training takes hours rather than days. This assumes a small network working on small pictures of a single kind of object under one lighting setup. However, that time estimate is uncertain until the system is actually run, so it should be measured rather than just believed. 

Finally, one distinction is worth stating plainly, because it is easy to lose. The simulator keeps a record of what it spawned. This record is used to score the final result, but it is never used to train it. That distinction is the whole point of this solution.

<!-- section: where-the-idea-comes-from | Where the idea comes from -->

The next part of the page explains where the idea comes from. Several lines of work meet here, and the nearest relative is worth knowing because it shows what this cell gets for free.

The closest living relative is learning depth and camera motion together, with no labels. A system called SfMLearner, published by Zhou and colleagues in 2017, trains two networks at once from ordinary video. One guesses the depth, the other guesses how the camera moved, and both are checked by warping one frame into the next and comparing the brightness. Monodepth2, published by Godard and colleagues in 2019, improves the recipe, though under a licence that allows reading and research rather than use in a product.

Both of those systems have to estimate the camera motion, and that estimate is where a large part of their error lives. Here, the motion is not estimated. It is commanded. So half of the hard problem in that literature does not exist in this cell.

Another influence is motion segmentation, which is the classical form of the grouping idea. Layered models go back at least to Wang and Adelson's 1994 paper on representing moving images with layers. That approach assumes the objects move. Here they do not; the camera does. But relative motion is relative motion, so the same reasoning applies.

This concept goes back even further to the Gestalt psychologists, who called grouping by shared motion common fate. A flock of birds is one flock because the birds turn together.

Finally, contrastive learning is how that grouping becomes something a network can output. SimCLR by Chen and colleagues, and MoCo by He and colleagues, are the standard references. Both train on whole pictures rather than on pixels, but the loss has the same shape, and it is a dozen lines of code rather than a library.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page covers where this method is strong and where it breaks. 

The strengths come directly from where the supervision comes from. First, it learns a boundary nobody can write down, because the line it draws is where the depth jumps rather than where the brightness changes. Second, labels are free and endless, since every pair of pictures the arm ever took is one. Third, colour does not matter, so two identical glasses are no harder to handle than two different ones. Fourth, the doubt carries a number. Because the separation grows in step with the slide, the arm can work out exactly how far it must move to settle a question. Finally, there is a strength that no other learned solution here can claim: it transfers to real hardware unchanged. A real arm has joint encoders and a wrist camera, which is all this method needs.

The weaknesses divide into what the signal cannot reach, what the method cannot say, and why it is nevertheless not the thing to build here.

What the signal cannot reach comes first, and a diagram here illustrates where this signal runs out. Because only the camera moves, parallax is the only signal, which means that underneath, this is a detector for sudden changes in depth dressed up as a learned model. Two glasses at the same distance from the camera separate by nothing at all. Furthermore, a small difference in depth out where the one-over-depth curve has gone flat buys almost no separation, however far the camera slides. Because the two glasses are the same kind, there is no clue in how they look either. The brightness comparison also needs variation in brightness, and it is weakest exactly where the glasses are plainest.

What the method cannot say comes second. It says which pixels go together, but not how many glasses there are. Something still has to choose the number of groups, and choosing too few is exactly the merge this problem fears. A glass that contributes no pixels at all is a case of its own, and the part of the page about when the glasses are completely hidden is where this is answered. A merged pair comes back as one tidy region with no complaint, so the circle-fit check afterwards is not optional. And changing the lighting or the kind of glass leaves the learned embedding describing a cell that no longer exists.

Why it is not the thing to build here comes third, and it is the honest conclusion. The cell already has a depth camera, which measures directly what parallax is being trained to infer. So this solution does not earn its place in this problem. It earns it at problem four, where the kinds of glass are open, or on the day depth readings fail on real glassware.

<!-- section: the-general-ideas-behind-this | The general ideas behind this -->

The next part of the page covers the general ideas behind this approach. This solution's distinguishing feature is where the supervision comes from. It does not come from a human, and it does not come from the simulator's spawn record. Instead, it comes from geometry the arm already knows. This places the approach in a well-developed literature, with four distinct ideas worth knowing.

The first idea is self-supervised learning, where labels come from the structure of the data itself. Rather than paying a human to annotate anything, you construct a task whose answer is already implied by the data. For example, you might ask a model to predict a held-out part of the data from the rest, or require two different views of the same thing to agree. The supervision is then free and unlimited, and the model learns representations that are useful for the task you actually care about. This is used in domains where unlabelled data is abundant and labels are expensive, such as language, audio, and video. It is also highly useful in robotics, where the robot's own sense of its position acts as a label generator that never tires. However, it is rarely the right choice for problems where the invented task can be solved by a shortcut that avoids the understanding you actually wanted. In fact, designing a task with no shortcut is the hardest part of the field. You can find more about this by looking up self-supervised learning.

The second idea is using geometry as supervision, specifically through the epipolar constraint. If a camera's movement between two pictures is known, then the position of a surface point in the first picture determines exactly where it must appear in the second picture, as long as you know its depth. That rule is the epipolar constraint. It is powerful because it converts a depth guess into a checkable prediction. You can warp one picture into the other using your depth guess, and then simply see how well the two pictures match. This concept is used for three-dimensional reconstruction, visual odometry, and mapping. It appears anywhere a moving camera has to recover the scene, which includes most of mobile robotics and all of photogrammetry. It is rarely right, however, for textureless, transparent, or reflective surfaces, because the matching process has nothing to lock onto. It also fails for scenes where the objects themselves move between the two pictures, because that breaks the assumption that the scene is still. This topic is covered more fully in literature on structure from motion and epipolar geometry.

The third idea builds on this to get self-supervised depth from a single camera, using what is called the photometric loss. You train a network to predict depth without using any depth labels at all. Instead, you use the network's predicted depth and the known camera motion to warp one video frame into another. The loss is simply the difference between the warped frame and the real one. A system called SfMLearner, introduced by Zhou and colleagues, established this form, and a later system called Monodepth2 by Godard and colleagues fixed most of its practical failures. This technique is widely used for driving and drone footage, where you have hours of video with known or estimable motion, but depth sensors are absent or expensive. The code in this solution uses an easy version of this idea, because the camera motion does not need to be estimated from the pictures; it is read exactly from the robot's joint encoders. Like the epipolar constraint, this method struggles with textureless scenes or independently moving objects. The classic version also struggles when you need absolute scale from a single camera, because it can only recover depth up to an unknown scale factor. Fortunately, the arm's known sliding motion removes that problem here.

Finally, the fourth idea is optical flow and motion segmentation, based on the concept of common fate. Points on one rigid object move together in the picture, while points on a different object at a different distance do not. This is the Gestalt principle of common fate, and it is one of the very few segmentation cues that needs no appearance model at all. It works perfectly on two identical objects, which is exactly why it is used here. Measuring this per-pixel motion is called optical flow, a field that runs from the classic Lucas and Kanade method of 1981 to modern learned methods like RAFT. It is used for video segmentation, tracking, and any situation where objects are hard to tell apart by their appearance. However, it is rarely right when nothing moves relative to anything else. That leads to the exact failure case described earlier: if two glasses are at the exact same distance from the camera, they will have no relative motion to group them by.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page explains where this approach sits among the other solutions. It competes with the other two learned deciders, leans on the method for clustering on the table for the arithmetic that checks its answers, and loops in the same way as the method for moving the camera.

What separates it from all of them is one property, and it is worth being clear that this property is about the future rather than about the immediate problem. Every other learned solution here is trained on labels the simulator provides, so every one of them would have to be retrained from scratch on the day the code meets real hardware. This one would not, because its supervision comes from the joint encoders, which a real arm also has.

So, the honest place for this solution is as the learned method to reach for when the project leaves the simulator, and not as the method to reach for right now.
