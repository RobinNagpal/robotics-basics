<!-- section: introduction | Introduction -->

How it would be solved: the ten solutions.

The page about the problem explains what is asked for and why it is hard. This page serves as the introduction to the ten solutions. It covers what all the solutions share. This includes what each does about a glass that nobody saw, the few specific words they use, where a learned component can be placed, what it means to choose the next measurement, and the rule that every single one of them had to pass. The page ends by describing what was actually built, and where that built system can fail.

Each of the ten solutions has a full page of its own, so this introduction does not repeat their details. Later on this page, there is a table of the ten solutions that explains in a single line what each one is and which specific difficulty it attacks.

Finally, there is a note about the physical setup. The robotic cell itself is described just once, on the page dedicated to the cell. That page covers the layout, the two positions the camera works from, which are from the top and from the side, as well as all four sensors, and the specific vocabulary this project uses when talking about them.

<!-- section: where-we-are | Where we are -->

This section reviews where we are with the task. Four to six opaque glasses of one kind stand on the table. The glasses are tapered, and their range of sizes is wide. They stand at least one hundred and fifty millimetres apart between centres, which leaves a narrow strip of bare table between any two rims. 

The arm has to produce a set of pixels, a place, and a rough width for each glass. It also has to produce two honest statements: which glasses it could not separate, and where it could not have seen a glass at all. It does not pick anything up, and it does not measure a shape.

The page about the problem sets out three difficulties. First, a glass can be missing from a picture altogether. Second, glasses merge in the picture while standing apart on the table. And third, the camera can no longer stand wherever it likes. All three of these issues come from splay, which was explained on the page about the cell.

The solutions lean on one property of splay that is easy to miss. Splay is a radial scaling about the point directly below the camera. This means it multiplies the distance from that point and the size by the exact same factor. Because of this, splay never changes how wide a glass looks as an angle. It only decides how far out along its own direction the outline lands. That specific property is what turns the difficulties from things you can describe into things you can compute.

<!-- section: when-a-glass-is-completely-hidden | When a glass is completely hidden -->

The next part of the page explains what happens when a glass is completely hidden. This is the worst of the three difficulties, because every check in this project is a check on something that was found. A width can be compared against what the kind allows, a fitted circle has a residual, and a group can be asked how many stations saw it. A glass that produced no pixels gives none of them anything to fire on.

The two places the camera works from produce it in different ways, and only one of them produces it in this cell. 

First, when looking straight down, a tall glass's outline sweeps over a short one. The range of sizes inside this kind is wide enough for that to happen at the guaranteed gap between centres rather than needing the glasses closer than the cell allows, with the covering glass comfortably inside the frame. So from the top, a glass can go missing either because something covered it or because the survey never looked at that piece of table. The two are indistinguishable from the picture, and the signal worth having is therefore unsearched area rather than hidden glass.

Second, when looking level, no sweep is involved. One glass stands in front of another, which needs neither a height difference nor closeness. Two glasses six hundred millimetres apart hide each other as completely as two one hundred and fifty millimetres apart, and the one that goes is the further one, whatever its height.

How often that happens has a measured answer, and it is worth recording, because it is an easy thing to overstate. Complete covering is possible at the guaranteed gap between centres, and an arrangement that produces it can be written down. It is uncommon in the layouts the cell spawns rather than the normal case. Across a sweep of spawned scenes of the tapered kind, surveyed at the cell's own height from the three stations the cell computes, only a small share of glasses lose any pixels at all to a neighbour. A smaller share again lose every pixel at one station, and none loses them at more than one. 

And none of it arises at the height the simulation renders its top view from. That view is higher than the cell's own survey height and holds the whole zone in one frame, because the higher the camera the less splay throws each outline. That is why a run of either pipeline below never meets this case, and why the answer to it has to be argued from the geometry rather than from a failure somebody has watched happen. It stays the worst of the three difficulties because nothing in the data can flag it.

Being seen in part is a different matter, and the same sweep settles it the other way about. Nearly every glass is cut by the edge of the picture at one station or another, and most glasses have no station at all that returns a whole footprint. Roughly one in six have exactly one. So a circle fitted at a single station usually rests on an arc rather than on a whole disc, and an arc gives a footprint too small and displaced, with a width the kind allows and a small residual, which nothing in one picture objects to. That is why the method of asking the stations to agree, explained earlier, is load-bearing. It is also why using amodal masks for the hidden part, covered in a later section, repairs an ordinary failure rather than a rare one.

Every solution document ends with a section called "when the glasses are completely hidden". They do not agree, and the disagreement is the useful part. 

A table then compares how the ten solutions handle a completely hidden glass, splitting the results into looking straight down and looking level. The overall pattern is that most solutions fail entirely, answering "no" for both views, because a completely covered glass leaves no evidence in the picture. For instance, a network trained from scratch gives the cleanest "no", noting that zero pixels cast zero votes. However, a few rows show partial success depending on the camera angle. Solution two can partly handle looking straight down by bounding where a glass could be, but it fails when looking level because the blocked strip never closes. Solution seven shows the reverse; it fails looking down, but succeeds looking level because the revealing pictures are already being taken.

<!-- section: the-words | The words -->

The next part of the page explains the terminology used. The words mask, patch, and cluster mean what they did on the earlier page about the cell. Three more terms run through all ten solutions.

The first is connected components, also called a flood fill. This turns a mask into separate objects. It takes a glass pixel that nobody has visited, spreads to every glass pixel touching it, calls that patch one object, and repeats. It only answers the question of whether these pixels are joined, which is why two glasses that touch in a picture come back as one.

The next term is a point cloud. This is every pixel with a depth reading turned into a point in the room. The pixel gives the direction, the depth gives how far along it the point lies, and the camera's pose gives where the direction starts.

The last term is segmentation. This word is used for three different jobs, and only one of them answers this problem. The diagram shows these three different approaches. 

First, detection puts a rectangle around each object, so pixels where two rectangles overlap belong to both. Second, semantic segmentation labels every pixel as either glass or not glass, but nothing says which glass is which, so two overlapping glasses become one region. Finally, instance segmentation labels every pixel with a class and with which specific object it belongs to, so five glasses come back as five separate masks. This problem asks for instance segmentation, and anything less has not answered it.

<!-- section: three-families-and-what-hybrid-means | Three families, and what "hybrid" means -->

The next part of the page explains three families of solutions, and what the word "hybrid" means in this context. 

The first family is programmed solutions. Here, you state the rule and the computer applies it. There is no training data, no weights file, and no graphics card required. It runs in about a millisecond, works on an object it has never seen, and when it fails, you can usually find out why just by printing one number. Its limit is that somebody has to be able to write the rule down.

The second family is learned solutions. In these, the behaviour comes from numbers fitted to examples, so the system can do things that nobody knows how to state as a rule. It pays for this capability with the need for a training set, a weights file that has to be kept in step with the world, hardware to run it, and an answer that cannot explain itself.

The third family is hybrid solutions. This uses both approaches together, arranged so that the learned part sits inside something checkable.

When looking at any hybrid system, the important question is not how much of it is learned, but where the learned part sits. This is because its position decides what happens when the model is wrong, and a model is sometimes wrong by construction. As an accompanying diagram illustrates, where the learned part sits decides exactly what happens when it makes a mistake. There are four main ways this can be arranged.

First, the learned part can act as the decider. The model's answer is the answer. A wrong answer is acted on, because nothing downstream is in a position to disagree.

Second, it can act as a proposer. The rules hand the hard cases to the model and check its suggestion. A wrong suggestion is rejected by arithmetic, and the system falls back to what it had.

Third, the model can act as a ranker. The rules generate every candidate and reject the unsafe ones, leaving the model to only order the survivors. A bad ordering costs one wasted attempt and nothing worse.

Finally, it can act as a verifier. The rules act and the model checks what happened. A wrong check costs one extra measurement.

In those last three arrangements, the learned part's mistakes are limited by something that does not need the model to be right. A better model makes failures rarer, but it is only the arrangement that puts a ceiling on how bad they get.

A hybrid is usually cheaper than a fully learned solution, not dearer, because the learned piece has one narrow job. Learning to answer "is this one object or two?" needs a small fraction of the data that a task like "find all the objects" needs, and it trains on an ordinary laptop.

<!-- section: feedback-choosing-what-to-measure-next | Feedback: choosing what to measure next -->

The next section discusses feedback, and specifically, choosing what to measure next. It points out that the number of measurements does not have to be decided in advance. A diagram illustrates this by contrasting an open-loop pipeline with a closed-loop one, showing how a robot can decide what to measure next rather than just measuring once.

In an open-loop pipeline, the system takes a fixed number of pictures, works everything out, and acts. If an object turns out to be unclear, it stays unclear, and everything downstream inherits that doubt without being told. A closed loop, however, takes a picture and works out what is not yet settled. It asks itself where it would have to look for the situation to become clear, goes and looks there, and repeats the process.

A closed loop needs three things to function, and with only two, it is not really a loop. First, it needs a measure of doubt that separates what is settled from what is unsure, rather than always just producing an answer. Second, it needs actions that could reduce that doubt, along with some way of guessing which action would actually help. Finally, it needs a budget, because every extra look costs time moving the robot arm. The loop stops when nothing is unclear or when the budget is spent, and it reports what is still doubtful rather than making a guess.

This reverses the usual instinct. The resource to save here is not computation. It is the number of times the arm has to move. A physical move costs seconds, while running any of these computational models only costs milliseconds.

<!-- section: the-rule-every-solution-passed | The rule every solution passed -->

The next part of the page explains the rule that every solution had to pass to be included. A solution is listed here only if everything it needs can be produced by the simulator on the machine this project runs on. This means no NVIDIA card, and therefore no CUDA, no robot on a bench, and no real-world data. The machine does have a graphics processor, built into its main chip and sharing one pool of memory with the processor beside it. PyTorch reaches that graphics processor through its MPS backend, which is why a model of moderate size both trains and runs here. So, what is ruled out is anything that needs code compiled for NVIDIA's cards, rather than anything that needs a graphics processor at all. The four conditions this comes to, and the good answers that fail them, are detailed on the page about the approaches that need more than a simulator.

Two consequences are worth seeing coming. First, the rule pushes the learned solutions towards small models trained from scratch on synthetic data, moving away from the usual advice to fine-tune a large model. For a cell with one kind of object, one lighting setup, and one camera, that is less of a sacrifice than it sounds. Second, the first three solutions need nothing added to the environment, while everything from the fourth onward begins by adding a dependency, and the learned ones add a large one.

One of those conditions has an exception, and it is worth naming rather than stepping around. The condition is that nothing an approach needs may come from outside the simulator. Solutions eight, nine, and ten each download a file of weights fitted elsewhere, so they do not meet this rule. They are listed because everything else about them runs on this machine, and because a large model fitted elsewhere is the first thing a team with a real camera would reach for. Leaving it out would hide a real option. 

However, the exception has a price. Those weights were fitted on photographs, while the cell renders a grey picture shaded from depth, so the model is asked about pictures unlike the ones it learned from. Furthermore, reproducing a result means fetching the exact same file rather than running the training again from a random start, so the file has to stay available and stay the same. The three documents for those solutions explain what that costs in their own terms.

<!-- section: the-ten-in-two-folders | The ten, in two folders -->

The next part of the page introduces the ten solutions, which are split into two groups based on whether they contain a trained model. 

Three of the solutions are entirely programmed, meaning they are just rules somebody wrote down. The other seven are learned. This means they all have numbers fitted to examples somewhere inside them, whether those numbers were fitted here or somewhere else, and whether the fitted part actually decides the answer or only puts candidates in order.

A table then summarizes all ten solutions, showing their family, where the model sits, the core idea, and the specific problem they attack. The list begins with the three programmed solutions. For example, the first solution simply splits a blob in the picture by assuming each flat stretch along a patch's bottom edge is a glass standing on the table, which attacks the problem of glasses merging together visually. 

Next are two hybrid solutions, where the model sits as a ranker or verifier. One uses a learned score to choose the best next camera look to spend the budget on, and the other weighs weak clues to guess if an unsearched patch hides a glass. 

The final five solutions are fully learned, where the model acts as the decider. These range from a small network trained from scratch to find and separate glasses, to fine-tuning a large instance segmenter to handle merged glasses without needing a written grouping rule.

Two of the entries in this list are actually documents that were written separately and then joined. This happened because, in each pair, the second was not a completely different method, but the same method with just one part changed.

For instance, the fourth solution was originally two ways of ordering the same candidates. Both ways keep the candidate generation and vetoes from the programmed camera-moving solution, and both replace only the rule that sorts the survivors. One uses a learned estimate of how much doubt a look would remove, and the other uses a learned estimate of whether the answer would change. Because they agree completely about what is allowed and differ only about what is preferred, they are now combined into one document describing a ladder with two rungs.

Similarly, the sixth solution was two heads on one network. The same shape, training recipe, and source of labels produce a class map when the last layer has one output channel, and one mask per glass when it has two. Describing them apart would have meant writing the exact same network down twice.

Finally, the last three learned solutions sit apart from the other two that let a model decide the answer. Solutions six and seven fit every number they use inside this specific cell, using pictures the simulator drew. This means the model is small and there is nothing else to it. 

Solutions eight, nine, and ten, however, start from a large model fitted somewhere else. They keep the written-down part as small as it will go. The finding is done by borrowed weights, and what is fitted here is either a small keeper over what that model proposes, or a short continuation of its training. This is a different trade-off, rather than a strictly better one. Weights fitted inside this cell describe exactly the pictures the cell produces. But the borrowed models were fitted on real photographs, while the cell can only render a grey picture shaded from depth. Because of this, the last three solutions carry a domain gap, which is a difference between the pictures a model learned from and the pictures it is asked about. A network trained here from scratch does not have this gap.

<!-- section: the-decision-what-was-built | The decision: what was built -->

The next part of the page covers the decision about what was actually built. 

Two pipelines were built, and both are scored on the same fifty held-out scenes drawn by the simulation. The one this project takes forward is the learned pipeline. Its documentation explains how it works and why, how to train it, and how to look at what each model is taught and answers.

The learned pipeline has three steps. 

First is the find step, where a network called TopNet carries out the sixth solution. Each glass pixel votes for the middle of its own glass, and the votes are counted. The place and width of each glass then come from the voting pixels' depth readings, using arithmetic. 

Second, it chooses where to look from the side, considering twenty-four places around each glass. Geometry vetoes the places out of reach, the places where the camera would stand inside another glass, and the places with a glass squarely in the way. This uses the arithmetic tests of the third solution, without asking the motion planner. A learned ranker orders what is left. It sits in the ranker position of choosing the next look, so a wrong order wastes a look and nothing more. If the best score is under zero point five, the glass is handed over to the third problem. 

Finally, the third step is to measure. A network called SideNet reads the height and sixteen widths straight off the side picture. This is the first problem's job, done here by a model.

The programmed twin takes the same three steps using rules. It uses the second solution's clustering on the table to find the glasses. It uses the same veto with a written rule to order the places, and it uses a silhouette measurement that is checked and tried from up to three places.

A table compares the two pipelines across these three steps. For the find step, both pipelines find all two hundred and fifty glasses, with the programmed rules achieving a slightly better median position error of zero point two millimetres compared to the learned pipeline's zero point four millimetres. For choosing where to look, the programmed rules get a clean first place slightly more often and hand over fewer glasses. For the measure step, the programmed rules are much more accurate, with a median height error of zero point eight millimetres and a worst case of two point three millimetres, while the learned pipeline has a median error of five point four millimetres and a worst case of thirty-six millimetres. 

Overall, the learned pipeline finds glasses as well as the rules do, but measures them worse. The documentation explains why.

Next, the section lists what is not built. Neither pipeline includes the second half of the second solution, which is the blind-region arithmetic that says where nobody could have seen a glass. Neither includes the third solution's covering step or its check with the motion planner. And neither includes the survey from several stations. Instead, both take one overhead picture from seven hundred and fifty millimetres, which is high enough that the whole glass zone is in frame. 

No test scene needed these missing parts to find every glass. However, they are what should be added first when the cell changes, for the reasons explained next.

A third folder holds the three solutions that borrow weights. Nothing from solutions eight, nine, and ten is in either pipeline, because each of those is a whole alternative to the find step rather than a part missing from it. Therefore, these three are built and scored on their own in a pretrained folder. That folder surveys from the cell's own height, from the three stations the cell computes, which makes its numbers different in kind from the two pipelines just discussed. It scores each solution twice: once on the layouts the cell's placement rule produces, and once on layouts built on purpose to put one glass in front of another.

A second table shows these results for finding glasses from the top. The first row makes the rest of the table readable by showing a baseline that is not a solution at all. It uses the renderer's own exact masks, handed to the same arithmetic and judged by the same scorecard, to show what any segmenter could manage at best. The table compares this baseline against solution eight, which segments anything, solution nine, which is fine-tuned, and solution ten, which is amodal.

Three things follow from this data. 

First, on the layouts the cell's own rule produces, the model is not what limits the answer. The fine-tuned segmenter sits within half a millimetre of what exact masks give and shares their worst case exactly. This means what is left of the error belongs to the arithmetic and to the geometry of looking from the top. 

Second, completing the hidden part earns its place only where something really stands in front. Solutions nine and ten are indistinguishable on ordinary layouts, but on crowded ones, solution ten finds about one glass in ten more, which is as many as the renderer's own exact masks find. 

Finally, a borrowed model with almost nothing fitted behind it finds the fewest glasses on an ordinary table, and is the only row here that never merges two of them. This is a trade-off worth seeing stated in one line.

<!-- section: where-what-was-built-can-fail | Where what was built can fail -->

The next part of the page looks at where what was built can fail. 

First, nothing says where a glass could have been missed. The single overhead picture captures the entire zone, and no test scene actually lost a glass. However, the problem specifically asks for the places that could not have been seen, and the pipeline does not generate this list. If the zone ever widens or the glasses get taller, a missing glass will leave no trace. The second half of solution two provides the fix for this.

Second, the single high picture hides the actual purpose of a survey. The reason no scene lost a glass is that both pipelines take one overhead picture from high enough that the whole glass zone is in frame, and nothing covers anything else. If the area were surveyed instead from the cell's own height, three stations would be needed to cover the zone. From that lower height, most glasses are cut by the edge of a station's picture. A footprint cut by the frame back-projects to an arc rather than a complete circle. The page on clustering on the table measures how often this happens, and the third folder shows the cost. On an ordinary table, the edge of the picture, rather than a neighbouring glass, is what determines how far a found place sits from the true location.

Third, glasses that could not be separated are not reported, even though the problem asks for that list too. The votes either split two glasses or they do not, and nothing in the system compares a found glass's width against what its type allows.

Fourth, SideNet's answer is not checked. It gets one picture and no retry. When the Ranker's first choice is spoiled, which happens thirteen times out of two hundred and forty-five on the test scenes, the spoiled picture is measured as if it were clean. The programmed twin catches this with a width check and tries the next place instead.

Fifth, heights come out about three percent short. The pipeline's measure function passes the sixteen levels on as the glass's profile, and a profile's height is its top level. This top level sits at ninety-seven percent of the height that SideNet predicted.

Sixth, two hundred examples is simply too few. SideNet pulls unusual glasses towards the average, meaning its worst errors happen when the tallest stemmed glasses are read as being too short. The Ranker's first choice is clean two hundred and thirty-two times out of two hundred and forty-five, compared to two hundred and nineteen for a random allowed place, showing that it has learned very little.

Seventh, the veto does not ask the motion planner. A place can pass the veto even if the arm's path to it crosses a glass. This is also true of the programmed twin.

Eighth, everything is learned from a perfect depth camera. Both pipelines run only on the simulated pictures for problem two, rather than in Gazebo. These simulated pictures show opaque glasses with a depth reading on every single pixel. Real glass gives almost no depth readings, yet all three models are provided with depth information.

Finally, two glasses that genuinely touch are the business of problem three. Voting is the method that could separate them, but no test scene actually has glasses touching.

<!-- section: how-it-would-be-solved | How it would be solved -->

The next part of the page focuses on how it would be solved. It provides connections to a few related topics, including the page about the problem, the page discussing the ones that need more than a simulator, and the page for problem three, which covers moving them apart.
