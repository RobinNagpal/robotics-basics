<!-- section: lead | Solution 9 — a fine-tuned instance segmenter -->

Solution 9, a fine-tuned instance segmenter. 

This approach is learned, with the model acting as the decider. It uses a standard instance segmentation network that arrives already fitted to a large collection of everyday photographs. Its training then continues on this specific work cell's own pictures, using just one class. As a result, when a picture goes in, the network outputs one mask for every glass it finds.

The physical setup of the cell is described fully on the page dedicated to the cell. That includes the layout, the two places the camera works from, which are from the top and from the side, as well as all four sensors and the terminology this project uses for them. Therefore, what follows here will only cover the details that are specific to this ninth solution.

<!-- section: introduction | Introduction -->

Solution nine, a fine-tuned instance segmenter. 

The introduction to this page explains how to answer problem two with a model that already produces the exact kind of answer the problem asks for. Problem two asks which pixels belong to which glass, and the name for that question in the wider field is instance segmentation. It does not just ask where there is glass, but rather identifies glass number one here, and separately, glass number two over there. There is a standard model for that question, and it is called Mask R-CNN. The version used here is torchvision's Mask R-CNN ResNet-50 FPN version two, and it arrives with its weights already fitted to COCO, a large collection of labelled photographs of everyday objects.

Because the model arrives fitted, the work here is not to train it but to continue training it. That is called fine-tuning, and it means keeping the numbers somebody else arrived at and nudging them on this cell's own pictures, with the list of classes cut down to a single one, which is glass. The simulator supplies those pictures and their labels for nothing, so the training set costs only the time it takes to render.

What that buys is the most direct answer in this folder. A picture goes in, and a list comes out in which each entry is one glass, with a box round it, a score saying how sure the model is, and a mask marking its pixels. There is no grouping distance to choose, no circle to fit before the glasses can be counted, and no rule saying how close two points have to be to belong together. Two glasses whose outlines join come back as two entries, because each is built separately.

What it costs is that the answer rests on a file of weights rather than on arithmetic anyone can read, and that most of those weights were fitted to photographs of a world this cell does not contain.

What running it settles is where that leaves the answer, and the answer divides by layout. On the layouts the cell's own placement rule produces, the model finds every glass and is not what limits how well a glass is placed. On layouts crowded on purpose, so that one glass really stands in front of another, it loses about a quarter of them. The later part of the page about what running it shows covers the whole of that measurement.

By the end you will understand what instance segmentation is and why a map of classes cannot do its job. You will learn how Mask R-CNN splits the work into proposing regions and then examining each one, what a backbone is, and what it means for one to arrive already fitted. The page explains why fine-tuning needs far less data than a random start, and what knowledge really carries over when the borrowed pictures are photographs and the new ones are shaded depth. Finally, you will see why two proposals covering one glass collapse into one answer, and exactly where this family of methods stops.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solution solves. Four to six glasses stand on the table. They are all the same kind, the kind is known, and they are solid, so the depth camera reads them. The job is to say which pixels belong to which glass, to give each glass a position on the table, and to give each a rough footprint width. What makes that hard is taken in four short steps below: how a picture joins two glasses together, what each of the two answers already on offer pays to get round that, and the one difficulty none of them can touch.

First, in the picture, two outlines can join. If the camera is roughly in line with two glasses, the near one covers part of the far one and their two outlines meet. From the top the same thing happens for a different reason. A glass's outline is thrown outwards away from the point directly below the camera, and the taller the glass the further out it goes. This project calls that outward stretch splay. Because the kind of glass here spans a small tapered glass at one end and a large one at the other, two glasses a normal distance apart can have outlines that overlap once splay has stretched them.

A mask is a picture the same size as the photograph in which every pixel holds nothing but yes or no, where yes means "this is glass". When two outlines meet, the yes pixels of the two glasses form one joined region. The usual way of turning a mask into objects is to spread out from a yes pixel to every yes pixel touching it, and call everything reached one object. However, this returns one object where there are two. That spreading answers only the question of whether these pixels are joined, and joined is precisely what the two outlines are.

Second, on the table, two glasses can be too close to group apart. Solution two, which clustered points on the table, avoids the picture entirely. Every pixel with a depth reading becomes a point in the room, the points standing clear of the table are kept, and points closer together than a chosen grouping distance go into one group. That one distance has to satisfy two demands at the same time. It must be larger than the biggest hole inside one glass's own points, or one glass comes back as two, and it must be smaller than the strip of bare table between two glasses, or two come back as one. At the spacing this cell guarantees there is room between those two limits, so the choice is comfortable. However, it still has to be made and justified, and it is a number the person setting the cell up owns for ever.

Third, a class map cannot say which glass is which. Solution six, a network trained from scratch, replaces the arithmetic with a small network whose first head answers a question about classes: is this pixel glass, or is it table? That head cannot solve the problem, because a label that is the same everywhere cannot mark a boundary. Every pixel of two joined glasses carries the value "glass", so there is nowhere in the output for the information that this half is a different glass from that half to live.

Finally, there is a difficulty none of these can touch. The hardest difficulty is that a glass can be missing from the picture altogether. Because a tall glass's splayed outline can cover a short glass completely, the short glass produces no pixels, and no method that reads pixels can find it. A later part of this page, about when the glasses are completely hidden, works out exactly why and says which solutions do answer it.

<!-- section: the-main-idea | The main idea -->

The next part of the page explains the main idea behind this solution. The core concept is to stop building the separating step and to borrow a model whose output is already separated.

Mask R-CNN does its work in two stages, and the shape of those two stages is the whole reason its output can hold separate objects. The first stage looks over the picture and proposes regions. These are rectangles that might contain an object, with no claim about what the object is. The second stage takes each proposed rectangle on its own, decides what class of thing is inside it, tightens the rectangle around it, and paints a mask of the object's pixels inside that rectangle only.

The important word is "inside". Because the mask for one object is predicted within that object's own rectangle, the question of which glass a pixel belongs to never has to be asked. Each answer was built in its own frame from the beginning. So, two glasses whose pixels touch in the picture produce two rectangles and two masks, and the masks are allowed to overlap without anything being confused.

The diagram illustrates this difference. On the left, it shows what a class map returns for two glasses whose outlines meet, which is one merged region. On the right, it shows what this solution returns, which is one separate mask per glass, resulting in two masks that happen to overlap. Only this second approach is an answer to the problem of separating the objects.

The second half of the main idea is where the numbers come from. Mask R-CNN is large, and training something that size from random numbers would need a great many labelled pictures. It does not have to be done that way, because the weights that ship with it were already fitted to COCO. Training continues from those weights on this cell's pictures, with the class list cut to one class. That is fine-tuning, and it is why a model of this size is reasonable on a laptop.

<!-- section: the-picture-the-model-is-given | The picture the model is given -->

The next part of the page explains the picture the model is given. Before going further, one fact about this cell has to be stated, because every later section depends on it and it is the single largest risk in this solution. 

The cell's renderer does not produce colour. What it produces is a depth reading for every pixel, meaning how far away the surface at that pixel is, and a glass identity for every pixel, meaning which glass the surface belongs to. The second of those is what makes the training labels free. The first is the only picture there is.

Mask R-CNN expects an ordinary colour photograph, with three channels of red, green and blue. So the code builds one. It shades the depth reading into a grey value, so that near surfaces come out at one end of the range and far surfaces at the other, and it repeats that single grey channel three times to make the three channels the model wants. The result looks like a black and white photograph.

That is a genuine difference from the pictures the weights were fitted on, and it is not a difference in the shape of the input, because the shape is exactly what the model expects. It is a difference in the statistics of the input. Real photographs have colour that varies between the channels, edges from paint and print and shadow as well as from geometry, and texture inside every surface. A shaded depth picture has none of that, its edges are all geometric, and its three channels are identical. The name for that kind of difference is the domain gap, meaning the gap between the world a model was fitted on and the world it is asked to run in.

One thing reduces the risk, and it is the whole reason this solution is worth writing. Fine-tuning does not merely use the borrowed weights; it continues training them on the pictures the model will really see. So the grey pictures are not an unfamiliar input the model has to survive at run time. They are the input it is fitted on. The domain gap therefore costs accuracy and training effort rather than costing correctness outright, and the later part of the page about what knowledge is actually being reused works out how much of the borrowing survives.

<!-- section: the-two-stages | The two stages -->

The next part of the page explains the two stages of the model. With the input settled, these two stages can be taken in order, and the reason there are two of them is a general principle rather than a detail of this specific model. Asking where all the objects are in one step over a whole picture has an answer of no fixed length and no fixed positions, which is awkward for a network whose output is a fixed block of numbers. Asking what is inside this one rectangle, and which of its pixels belong to the object, has a fixed-size answer, which a network handles comfortably. So the work is split. One stage turns the open question into a list of rectangles, and the other answers the easy fixed-size question once per rectangle. That split is what the R-CNN family of models is built around.

A diagram here illustrates this flow. It shows stage one sliding over the picture to propose many rectangles that might hold an object, and stage two cutting each rectangle out, classifying it, tightening it, and painting a mask inside it.

The first stage is called the region proposal network. It slides over the picture and, at every position, asks a small pair of questions about a set of fixed reference rectangles centred there. Those rectangles are called anchors, and they come in several sizes and several ratios of width to height, so between them they cover the shapes an object might have.

The two questions asked of each anchor are simple. The first is whether the anchor contains an object of any kind, or just background. It does not ask which class, so the first stage knows nothing about glasses and does not need to. The second is how the anchor should be shifted and resized to sit more tightly round what is in it.

The output is therefore a long list of rectangles with a rough score each, cut down to the best few before the second stage sees it. Those survivors are the proposals, each a guess saying only that something is here, and it is roughly this big.

One property of that design matters a great deal here. The proposals are produced independently of one another. Two glasses whose outlines meet sit at different positions, so different anchors fire on them and two proposals come out. Nothing has to notice a seam and nothing has to decide where to cut, because nothing ever considered them as one thing.

The second stage receives those proposals one at a time and produces three things for each.

First, it produces a class, chosen from the model's class list plus a background option. Here the list has one entry, glass, so the choice is between glass and background, which means the second stage's real job in this cell is to throw away the proposals that landed on bare table.

Second, it produces a tightened rectangle. The proposal was a shifted anchor and is only roughly right, so the second stage predicts a further adjustment, using the much better look it gets at the region's own contents.

Third, it produces a mask, and this is where instance segmentation happens. The second stage predicts, for a small grid covering the rectangle, whether each cell of that grid is part of the object or not. That grid is then stretched back up to the size of the rectangle and dropped into place in the full picture, so it is a statement about one object inside one rectangle.

One piece of machinery is worth naming, because it is what makes the mask accurate. Cutting a rectangle out of the model's internal picture means reading values at positions falling between whole pixels, and rounding those positions shifts the cut slightly. That hardly matters for deciding a class and matters a great deal for a mask, so Mask R-CNN blends the neighbouring values rather than rounding, an operation its authors named RoIAlign. The lesson generalises: a step whose error is tolerable for one output can be the dominant error for another.

<!-- section: the-backbone-and-what-it-means-for-one-to-arrive-fitted | The backbone, and what it means for one to arrive fitted -->

The next part of the page explains the backbone, and what it means for one to arrive fitted. 

Both of the stages just mentioned look at the picture, but neither looks at the raw pixels. Instead, they look at what a shared part of the model has already made of it, and that shared part is called the backbone. 

A backbone is the part of a vision model that turns a picture into a stack of feature maps. A feature map is a grid, smaller than the picture, in which every position holds not a colour, but a list of numbers describing what is in that part of the picture. These numbers might represent whether there is an edge and which way it runs, whether there is a corner or a repeating texture, and at deeper levels, whether there is something that looks like a rim. Nobody decides what those numbers mean; they are simply whatever the training process found useful.

The backbone used here is a ResNet, which is a stack of convolutions arranged so that each block adds a correction to what came before it, rather than replacing it. A convolution takes a small square window, slides it over its input, and at each position multiplies the values in the window by a fixed set of weights and adds them up. Adding corrections rather than replacing the data is what lets a very deep stack train at all.

The main point of this section is that almost all of this model's weights are in the backbone, and they arrive already fitted. The two stages on top are small by comparison, so what is downloaded is mostly a general-purpose answer to what is in this part of this picture, worked out from a large collection of photographs. A diagram on the page illustrates this, showing the backbone turning a picture into feature maps that hold edges, corners, textures, and object-like parts. Reading the process from left to right, it extracts small local things such as edges and corners first, then larger composed things built out of the level below. Every level is made of numbers that somebody else's training paid for.

There is a difficulty in using a backbone for detection, and the fix for it is the other half of this model's name. 

The difficulty is that the backbone's levels trade two things against each other. Each time the grid is halved, one position stands for a larger patch of the original picture, so the deeper levels know more about context and less about exactly where anything is. A small object may be visible in the early levels, where positions are precise, and invisible in the deep ones, where it is smaller than one position. A large object is the other way round. Because of this, detection cannot use just one level. It needs precise positions for small objects and broad context for large ones at the same time.

A feature pyramid network is the standard answer. It takes the backbone's levels, starts at the deepest, and works back up. At each step it doubles the deep level's grid, adds it to the matching level from the backbone, and calls the sum that level of the pyramid. Every level is then the size the backbone produced it at, while also carrying the deep levels' sense of context. The region proposal network runs on all of them, with small anchors on the fine levels and large anchors on the coarse ones.

This matters directly here. A glass seen from the top covers a small patch of a large picture, while a glass seen from the side, at the measuring standoff, fills much of the frame. One model has to handle both, and the pyramid is why it can.

<!-- section: fine-tuning | Fine-tuning -->

The next part of the page explains fine-tuning. The backbone arrives already fitted, and this section is about what to do with that: keep those numbers and carry on training.

Training a network means showing it an example, comparing what it produced against the answer wanted, and nudging every weight in the direction that would have helped. Training from a random start means the weights begin as noise, so the nudges have to build every part of the model from nothing, including the parts that only detect edges. Fine-tuning means the weights begin somewhere useful, so the nudges have much less to do.

The page includes a diagram to illustrate this difference. It shows that training from a random start has to discover edges, corners, and textures before it can learn anything about glasses, while fine-tuning begins with those already in place and only has to learn what a glass looks like. The text notes that this picture explains the idea rather than reporting a result. Nothing in this folder fits this model from a random start, so the comparison is an expectation about how training behaves, and not two measurements set beside each other.

The text then explains why fine-tuning needs far less data. The reason is best stated in terms of what the data has to pay for. Every weight in a model is a number the training data has to determine, and if the data does not contain enough information to pin a weight down, that weight ends up fitted to accidents of the particular examples given. That is called overfitting, and it shows as a model scoring well on its training pictures and badly on new ones. So the data needed grows with the number of weights determined from nothing, and fine-tuning changes that sum. The great majority of the weights are already at values that work, so the data only has to adjust them, and the few that genuinely start from scratch are in the very last layers, where the class list changed. A training set that would be hopeless for a random start is therefore comfortable.

There is a second reason, about time rather than data. A random start spends much of its training discovering that edges matter, that corners matter, and that a smooth gradient is a curved surface, which the borrowed weights already hold.

This brings up an honest question, and it is the one that decides whether this solution is a good idea: what knowledge is actually being reused? The borrowed weights were fitted to photographs of everyday objects, and this cell's pictures are depth shaded into grey. What carries over is strong at the early levels and weak at the deep ones, and the reason is what each level holds.

First, the early levels hold edge and gradient detectors, and an edge is an edge. A depth picture is full of edges, because a glass's rim against the table behind it is a large jump in depth and therefore a large jump in grey, and a window that finds a step from light to dark in a photograph finds the same step here. Those levels transfer almost entirely, and this is where most of the benefit sits.

Second, the middle levels hold shapes and surface arrangements, like curves, corners, regions that bulge, and regions that are flat. These transfer partly. A glass rim in a shaded depth picture is a smooth closed curve with a gradient across it, and the middle levels of a model fitted on photographs already describe such curves. They were fitted on gradients caused by light rather than by distance, but the geometry producing the gradient is the same.

Finally, the deep levels hold object-like parts, and this is where the reuse is weakest. They were fitted to say things like "this looks like the handle of a cup", learned from colour and texture as much as from shape, and a shaded depth picture has neither. So they arrive describing properties the new pictures largely do not have, and fine-tuning has to move them far.

That gives an honest summary, and it has to be labelled for what it is. The borrowing is worth having, and the expectation is that it is worth less here than the usual advice implies. The second half of that is reasoning about what each level holds, and nothing in this folder tests it, because no run here fits this model from a random start and there is therefore no measured comparison between the two starts to appeal to. What the reasoning says is inherited is the machinery of turning a picture into useful local descriptions, which is the expensive and boring part, and what has to be earned is everything above it. One consequence is practical. Because the deep levels are the ones expected to move and the early ones are not, it is reasonable to nudge the early levels gently or not at all while letting the later parts change freely.

The final part of the section covers what the labels here are, and why they cost nothing. The training set is where this cell is unusually fortunate, and it is what makes fine-tuning practical rather than merely possible.

Mask R-CNN is trained on pictures in which every object is marked with a class, a rectangle, and a mask. In the ordinary case a person draws every one of those masks by hand, which is why labelled data is the scarce resource in this field.

Here nothing is drawn. The renderer already reports a glass identity for every pixel, so the mask for one glass is the set of pixels carrying that identity, the rectangle is the smallest one containing them, and the class is always "glass". Every label is a selection over an array the renderer produced anyway, so there is no annotator, no annotator's budget, and no annotator's mistakes.

That does not make the training set automatically good. The cell's own rule keeps glasses a comfortable distance apart, and a set drawn only from that rule never shows the model a pair that was hard to separate. So, the training scenes have to include pairs standing much closer than the rule allows and pairs whose outlines overlap heavily after splay, while keeping the ordinary case in proportion. The principle is worth remembering: the edge of the specification should sit somewhere in the middle of the training set, so that the model has met worse than it ever will.

<!-- section: what-comes-out-boxes-scores-and-masks | What comes out: boxes, scores and masks -->

With the model and its fine-tuning described, this section is about its output, because the output is three things per object and each does a different job. For every object it believes in, the model returns a box, which is the tightened rectangle around the object. It also returns a score, a number between zero and one saying how sure the model is that this is a glass rather than background. Finally, it returns a mask, marking the object's pixels inside the box. The three arrive together, from the same second stage, on the same proposal.

The diagram for this section shows one glass producing a box, a score, and a mask together, and the same three coming out once per object, with the masks allowed to overlap. The masks in that picture overlap, and that is not an error. In a class map, overlapping would be a contradiction, because a pixel can hold only one label. Here, each mask belongs to a different object and says that this pixel is part of it. So, two masks claiming one pixel simply means the near glass covers the far one there, and nothing has to resolve it for the count to be right.

Next, the section explains what the score is good for. The score is the model's own confidence, produced by the same weights that produced the mask. Because of this, it is not an independent check and must not be treated as one. A model that is confidently wrong reports a high score, and nothing in the score could reveal that. What it is genuinely good for is three things.

The first is a threshold. Most proposals reaching the second stage are background with low scores, so keeping only the entries above a threshold is how the list becomes a list of glasses. Where the threshold sits is a trade-off. Set it low, and bare table gets reported as glass. Set it high, and faint glasses are dropped.

The second is ordering, so that the most confident glasses are dealt with first and the doubtful ones last. 

The third is triggering another look. A glass reported with a score well below the others is exactly the case where a second picture from a different place is worth the seconds it costs. The project already has the loop for that. The earlier part of the project on moving the camera works out where the camera can stand, and the part on choosing the next look decides which of those places earns the trip.

What the score does not tell you is whether the mask is right. It is about the class, so a glass whose mask is cut short by something in front of it can still be scored highly, because it plainly is a glass. That gap is what the later section on amodal masks for the hidden part exists to narrow.

<!-- section: overlapping-proposals-and-how-they-collapse-to-one | Overlapping proposals, and how they collapse to one -->

The next part of the page explains overlapping proposals, and how they collapse to one. The output is one entry per object, and this section is about why, because the first stage does not produce one proposal per object at all.

Recall that the first stage scores a set of anchors at every position. A glass in the picture does not cover exactly one anchor at exactly one position. Instead, it overlaps several anchors of similar size at neighbouring positions, and all of them score highly, because all of them really do contain most of the glass. After tightening, those proposals form a cluster of boxes almost on top of each other. 

A diagram here illustrates this. It shows several proposals landing on one glass. They are sorted by score, and each one that overlaps the best proposal by more than the allowed amount is discarded.

The standard fix for this is non-maximum suppression, and it is one of the few parts of this model that is plain arithmetic rather than learned. You sort every surviving box by its score, highest first, and keep the highest. Then you measure how much each remaining box overlaps it. This is done using the ratio of the area the two boxes share to the area they cover between them. You discard every box whose ratio is above a chosen amount, because a box overlapping that heavily is describing the same object. You then repeat this process with the highest-scoring box left, until nothing remains to consider.

Two things about it are worth noticing. The first is that the overlap ratio is its only setting, and it is a ratio of areas rather than a distance on the table. Because of this, it does not change with how far away the camera is. Unlike the grouping distance used in solution two, it is not a length that has to be justified against the geometry of the cell. 

The second thing to notice is where it can go wrong. Non-maximum suppression assumes heavy overlap means duplication, so where two different objects genuinely overlap heavily, it discards one of them. That case is real here, because perspective splay can push a tall glass's outline right over a short one's. The ratio therefore has to be generous enough to survive the cell's worst legitimate overlap, and the softer variant named in the part of the page about the general ideas behind this exists for exactly that difficulty.

<!-- section: what-this-solution-does-not-need | What this solution does not need -->

The next part of the page covers what this solution does not need. Everything so far has described what the model does, but this short section is about what it removes, because that is the clearest way to see what is being gained.

First, there is no grouping distance. You might remember that solution two has to choose one length and defend it against two opposing demands, and that choice then becomes a permanent property of the installation. Here, nothing groups points at all. 

Second, there is no circle fit needed to separate anything. Solution two uses a group's fitted width to notice when a group is really two glasses, which is how a merge is caught. Here, two glasses do not merge into one entry, so nothing has to be caught after the fact. Nor is there a separate stage turning a mask into objects, which solution six needs because its first head returns a class map.

Next, there is no rule about how close two points may be. Nothing here compares two pieces of evidence and decides whether they are near enough to be one glass. Two comparisons of place do happen, but both compare claims about one object rather than the evidence itself. One is non-maximum suppression, which reduces the proposals covering one glass to a single answer. The other brings the stations of a survey together. If two reports stand closer than the narrowest glass this kind allows, they must be one glass reported twice, because two glasses of one kind cannot physically stand that close together. Neither of these comparisons relies on a length that somebody chose, and the second is simply a physical limit on the kind of glass.

However, a measurement on the table is worth keeping for a different purpose. This is a rule the text asks for, rather than a step the accompanying code actually carries out. Each reported mask's pixels back-project to points on the table, and the arithmetic shared by every solution in this group turns them into a place and a width. The axis comes from the points at the rim, and the width comes from how far the point cloud reaches out from that axis. What that arithmetic should be asked next is whether the width falls inside the range this kind of glass can actually have. A glass whose width falls outside that range should not be believed, no matter how high its score is. The model proposes, and the geometry disposes. The text calls this the range check. In this group of solutions, nothing applies this check to this solution's reports. Of the three solutions discussed here, only the one that segments anything and then keeps the glasses refuses a report based on its width, because only its keeper was given that specific job.

Finally, one part of the prescription is not available from the shared arithmetic at all. A circle fitted to a footprint also says how badly it fitted, and that residual error acts as a second check on top of the width. Nothing in this group of solutions fits a circle, so nothing here returns such a residual. If you want a solution whose arithmetic fits a circle and reports how well it fitted, you have to look back at the earlier page on clustering on the table.

<!-- section: how-the-concepts-fit-together | How the concepts fit together -->

The next part of the page explains how the concepts fit together. Everything discussed so far forms a single pipeline, and it is worth seeing in order before looking at the failure cases, because each stage inherits what the last one produced.

First, a depth picture comes out of the renderer. It is shaded into a grey picture with three identical channels, because that is the exact shape of input the model expects. 

Next is the backbone. Its weights were originally fitted to photographs and were then nudged, or fine-tuned, on this specific cell's pictures. The backbone turns that three-channel image into a stack of feature maps. 

Then, the feature pyramid mixes the context from the deep levels back into the fine levels. This ensures that small glasses seen from the top and large glasses seen from the side are both described well. 

After that, the region proposal network runs over every level of the pyramid. It returns many proposals, which are rectangles that might hold an object. Because one glass might generate many overlapping proposals, non-maximum suppression is used to reduce the clusters describing one glass down to one rectangle each. 

The second stage of the model takes each surviving rectangle. It decides whether the contents are a glass or just background, tightens the rectangle around the object, and paints a pixel-level mask inside it. What comes out of the network is a list where each entry represents one glass, complete with a bounding box, a confidence score, and a mask. 

Finally, the pipeline moves to the physical world. Each mask's pixels are back-projected onto the table, and shared arithmetic turns them into a physical place and a width. The range check prescribed in this document then looks at that width and refuses any entry whose width is impossible for this kind of glass.

There are three main things worth holding on to from this process. 

First is the two-stage shape of the model. This structure is what makes the output hold separate objects. Because a mask is predicted strictly inside its own rectangle, it cannot be confused with a neighbour's mask. This means the hardest part of the overlapping object problem is answered simply by the shape of the output, rather than by a specific processing step that had to be got right. 

Second are the borrowed weights. These pre-trained weights are what make a model of this size trainable here. However, they are expected to be worth less than usual because the pictures rendered by this cell are not real photographs. Fine-tuning has to close most of that gap, meaning what actually survives from the borrowed weights is mostly the early, general feature detection. This expectation comes from reasoning about what each level of the backbone holds, rather than from anything explicitly measured in this folder. 

Finally, the range check is what has to keep the whole system honest. No matter how confident the model is, that confidence cannot overrule a measured physical footprint that no glass of this kind could possibly have. This is a strict rule that you must apply, and not something the run already does automatically.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page discusses what happens when the glasses are completely hidden. A glass can be missing from a picture altogether. It is standing on the table, it is solid, the depth camera is pointed straight at the part of the table it stands on, and not one pixel of it comes back. This is the most dangerous difficulty in the problem, and this solution's answer to it is short and absolute.

The way it happens from a top-down view is through splay. A glass's outline is thrown outwards away from the point directly below the camera, and the taller the glass, the further out it goes. The kind of glass used here has a tall end more than twice the height of its short end, so a tall glass's outline is stretched much further than a short one's. Standing the short glass beyond the tall one, along the line running out from the point below the camera, lets the tall glass's stretched outline cover it entirely. From the side it is plainer. The near glass is in the way, and because it is nearer it is drawn larger, so a glass directly behind it disappears however far behind it stands.

Because of this, a glass with no pixels generates no proposal. The first stage scores anchors by what is inside them, and what is inside every anchor covering the hidden glass's place is the tall glass in front of it and the table around it. Nothing in that patch of the picture came from the hidden glass, so the anchors there describe the tall glass. The second stage receives one proposal, correctly calls it a glass, and paints a correct mask over the tall glass's pixels.

Furthermore, nothing in the output is wrong. There is no low score, because the one glass found really is a glass and the model is right to be sure. There is no impossible width either, because the surviving pixels back-project to the tall glass's own real footprint. Splay decides which pixels exist and not where they land, so every pixel returns to its own true place on the table. Every check this solution prescribes is a check on something that was found, and there is nothing to check. 

A diagram here illustrates this dead end, showing that a completely covered glass produces no pixels, meaning no anchor sees it, no proposal is made, and no amount of fine-tuning can create one.

This leads to the point that no amount of fine-tuning helps. This is worth settling exactly, because more training is the first thing anyone suggests. Take the scene with the hidden glass and the same scene with that glass taken away. The renderer produces the same depth picture for both, pixel for pixel. A model is a function of its input, so no model of any size, trained by any method, can return different answers for two identical inputs. What differs between the two scenes left no trace in the input, so this is a fact about the input rather than about the model.

There is one qualification, and it is the subject of the next solution rather than a way out of this one. A model can be trained to mark the part of an object that something else is covering, which is called amodal segmentation. The page on amodal masks for the hidden part does exactly that with this same architecture. However, amodal completion extends evidence, so it needs some of the glass to be visible to extend from. With no pixels there is nothing to extend, and a model asked to mark a glass that might be behind this one would be inventing a scene rather than reading a picture.

So this solution cannot handle the completely hidden case and must hand it on. What it hands on is not a glass but a region, specifically the part of the table it could not have seen. Three solutions share that work. First, working out the region is arithmetic on splay and on the glasses that were found. This belongs to the section on clustering on the table, which computes the blind region for a camera position and reports each part of it large enough to hold a glass as an unsearched patch. Second, deciding which of those patches is worth spending a picture on belongs to the page about whether anything is hiding there, which learns that one judgement from numbers the geometry has already produced. Finally, moving the camera and taking the picture belongs to the section on moving the camera, which turns a request for a different view into a pose the arm can reach.

This solution contributes the masks those three argue from, and none of the argument.

<!-- section: a-worked-example | A worked example -->

The next part of the page walks through a worked example. Everything here follows from the cell as described and from the pipeline above. 

Imagine a scene where five glasses of one kind stand on the table. Two of them stand much closer together than the cell's rule allows, roughly along the line running out from the point below the camera, so splay stretches the taller one's outline over part of the shorter one's. In the picture from the top, their two outlines join into one region with no seam along it. The other three stand clear.

If we look at what solution two would return, the two close glasses are near enough that the chain of points crosses the strip between them, so they come back as one group spanning both glasses and the gap. A circle fitted to it is far wider than any glass of this kind can be, so the range check fires. It fires correctly, and on a group it has no way to divide. The run reports four glasses and one doubtful group.

In this solution, however, the region proposal network finds anchors firing on all five glasses, including both of the close pair. This happens because the two sit at different positions and different anchors cover them. Non-maximum suppression reduces each glass's cluster of proposals to the best one, and the second stage calls each of the five survivors glass rather than background, tightens its rectangle, and paints a mask inside it. The two masks of the close pair overlap where the taller glass covers the shorter one, and that is allowed.

The point worth taking away is why the hard pair came apart. Nothing separated them. There was never a joined region for anything to divide, because the two glasses were separate proposals before either had a mask.

Next, each mask's pixels are back-projected onto the table and the shared arithmetic turns them into a place and a width. All five widths fall inside the range this kind allows, so the range check would pass all five, and five glasses are reported, each with a place and a width. The run reports them without asking the question, though. Nothing in this folder compares this solution's widths against the kind's range, so an impossible width would be reported too.

Now consider the case this solution cannot answer. Add a sixth glass, at the short end of the kind's range, standing beyond the tallest glass along the line running out from the point below the camera. It stands close enough that the tall glass's stretched outline covers it completely. The depth picture holds no pixel of it, so no anchor covering its place holds anything of it, so no proposal is made and no entry appears. Five entries come back, all correct, all legal, and all confident.

Because nothing in this solution's output raises a question, the question has to come from elsewhere. The blind-region arithmetic in solution two takes the five reported glasses, works out for each the wedge of table its own outline could have hidden, and reports any part of that region large enough to hold the smallest glass of this kind as an unsearched patch. Solution five judges that patch worth a look, solution three finds a pose the arm can reach with a clear line of sight into it, and the arm takes one more picture. In that picture the sixth glass has pixels, so it has anchors, so it has a proposal.

<!-- section: what-running-it-shows | What running it shows -->

The next part of the page explains what running the model shows. The worked example covered what should happen, and this part covers what actually happens when the fine-tuned model is run on scenes that no part of its training ever saw. 

Two kinds of layout are scored, and they have to be kept apart because the answer is not the same on each. The first kind are the spawned layouts. These are the ones the cell's own placement rule produces, with the separation that the rule guarantees between glasses. The second kind are the crowded layouts. These are built on purpose to put one glass in front of another. In these scenes, the glasses stand along a line running out from the point below the camera. They are placed closer together along that line than the rule allows, and at the tightest spacing, they are close enough for two bodies to meet, with the tall glasses in front of the short ones. Every scene is surveyed from all three stations, exactly as the cell surveys it.

What comes back is judged by the same scorecard the project's other pipelines are judged by, and four of its terms are used here. A glass is considered found when one report covers it, and missed when none does. Two glasses are merged when one report covers both, and one glass is split when two reports share it. The scorecard also measures how far each reported place sits from where the glass really stands, which this section calls the place error.

On the spawned layouts, the model finds every glass. Not one is missed, nothing that is not a glass is reported, no two glasses arrive as one report, and no glass arrives as two. The proposals it cannot call either way are handed on rather than guessed at, and none of them costs a glass, because every glass is found anyway.

A result that clean invites a question. How much of the place error that remains is the model's doing? That can be settled rather than argued, because the renderer's own exact masks can be handed to the same arithmetic with no model in the way at all.

Doing that barely improves the answer. The median place error moves by a fraction of a millimetre, and the worst case does not move at all. So what remains of the error belongs to the arithmetic and to the geometry of looking from the top, and not to the segmenter, and no better model can take it away.

The cause is the one this document already gives for a mask that stops early, with the edge of the picture doing the cutting rather than another glass. Most glasses are cut by the frame's edge at one station or another, because the stations are spread along the zone, so part of the zone lies at or past each frame's edge. Perspective splay throws the rim of a glass standing near that edge further out still, pushing it over the boundary. A footprint cut short back-projects to an arc rather than to a whole disc, and the middle of an arc is not the middle of the glass. The earlier page about clustering on the table runs into the same limit with no model anywhere near it and works the geometry out in full. That is the plainest sign that this is a fact about the view rather than about the network's weights.

Crowding the glasses is a different matter, and it is where this solution's limit shows. On the crowded layouts, it finds about three quarters of the glasses, merges a couple of pairs into one report, and its worst place error is close to twice its worst on a spawned layout. Nothing it reports is invented. No report lands where no glass stands, and what it cannot settle it hands on, so the glasses it loses are lost by silence rather than by a wrong answer.

A perfect segmenter would not repair most of that. The renderer's own exact masks on the same crowded scenes find about four glasses in five, because a glass with no pixels at a station leaves nothing for any method to propose from. So the gap between this solution and perfection on a crowded line is real, and it is much smaller than the gap between a crowded line and an ordinary table. Crowding is what costs the glasses, and the segmenter is what costs the smaller part of them.

<!-- section: running-it-yourself | Running it yourself -->

The final part of the page explains how to run the code yourself. The code for this solution lives with the other two borrowed-model solutions. They share a single folder and a single environment, which are described in the project's readme file.

Setting up the environment and fetching the weights is done just once, using a setup command. After that, fine-tuning and testing are each handled by a single command where you specify the solution name, which is Mask R C N N. There is a command to train the model, one to test it, and one to run a crowded test.

The standard test command scores the model on held-out layouts of the kind the cell's own placement rule produces. The crowded test command scores it on crowded layouts, where glasses stand along a line extending out from under the camera and really do stand in front of each other. This second test is what supports every claim made in this document about a partly hidden glass.

There is one more command that needs no solution name, because it runs no model. It is a floor command. It takes the renderer's own masks and hands them to the same arithmetic and the same survey. This establishes the performance floor, which was used as a baseline earlier on the page when discussing how the model is not what limits the answer.

Finally, the section details the hardware used. The machine is an Apple M4 with a ten-core integrated graphics processor and memory shared between it and the main processor. PyTorch reaches that graphics processor through its M P S backend, so the code selects M P S when it is available and falls back to the main processor otherwise. There is no Nvidia card and no Cuda used here. The shared memory is the reason a model of this size fits at all, because the graphics processor can use nearly all of the machine's memory.

<!-- section: what-it-needs | What it needs -->

The next part of the page explains what this solution needs. This is one of the more demanding solutions in this folder to set up, and it is worth being plain about that before anyone starts. 

First, it needs a deep learning framework and the environment to run it in. This is a large dependency for a cell whose recommended answer is just a page of arithmetic. 

Second, it needs a downloaded file of weights, which is fetched once by the setup command. That file is large, it is not something to commit alongside the code, and the project does not produce it, so it comes from outside and is taken on trust.

Third, it needs a training set. The renderer produces and labels this for nothing, including the hard arrangements that the cell's own rule would never generate. That is the genuinely cheap part, and it is what makes fine-tuning reasonable here. 

Fourth, it needs time on the machine, though far less time than starting from random weights would require.

Finally, once the model is fine-tuned, it needs a file of weights that is kept in step with the world. If you change the camera, the lighting, the way depth is shaded into grey, or the range of sizes a kind of object is drawn from, the file becomes quietly out of date in a way that no test of the code will notice. 

Against all of that, what the solution needs at run time is modest. One pass over one picture takes a fraction of a second, which is nothing beside the seconds an arm movement costs. Therefore, the cost of this solution sits almost entirely in building it, rather than in running it.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page looks at where this solution is strong and where it breaks. 

First, it answers the question actually asked. The problem asks for instances, and this model's output is instances. Every other method discussed here answers a different question and then adds machinery to convert it, and every piece of that machinery is somewhere a mistake can be made.

Second, it separates glasses whose outlines join. Two glasses that meet in the picture are treated as two proposals before either has a mask, so there is no joined region and nothing to divide.

Third, it has nothing to tune. There is no grouping distance, no seam threshold, and no rule about how close two points may be. Its two settings, the score threshold and the overlap ratio, are plain numbers with obvious meanings, and neither is a length that has to be justified against the geometry of the cell. It also handles both views with one model, because the feature pyramid lets the same weights describe a glass that is small from the top and large from the side.

Fourth, its masks stop where the visible pixels stop, and what that costs has been measured. A glass partly covered by another gets a mask of only the part the camera can see. On the layouts the cell's own rule produces, that costs nothing beyond what the view itself costs. Every glass is found, and placed as well as the renderer's own exact masks place it. On a crowded line, however, it costs a great deal. About a quarter of the glasses are not reported. Although some of those produced no pixels at any station and could not have been reported by anything, the model loses more of them than exact masks lose, and its worst place error is close to twice its worst on an ordinary table. Why a mask cut short does that much damage is unchanged and still worth knowing. Such a mask back-projects to an arc rather than a whole footprint, so the width comes out too small and the place comes out beside the glass rather than under it. The width can still be one this kind allows, so even the range check this document prescribes would pass it. In this folder there is no such check on this solution's reports to pass, which makes the failure quieter still. It is a quiet failure either way, and the later page on amodal masks for the hidden part recovers most of what it costs. On crowded layouts it finds about one glass in ten more than this solution does and cuts the worst place error by about a quarter, while on ordinary layouts the two score alike.

Fifth, it is blind to a glass hidden completely. No pixels means no proposal, which means no entry, no low score, and nothing to check. That is a fact about the input rather than about the model, and the previous section works it out in full.

Sixth, its answer cannot explain itself. When the second solution's fitted circle is wrong, you can print one number and see why. When this model is wrong, you can only look at the picture and guess. Every quantity inside it is a block of numbers with no meaning anybody assigned, so debugging is a matter of examples rather than of reasoning, and the range check this document prescribes is what has to make that tolerable.

Seventh, its weights are a second copy of the world, and most of them came from somewhere else. The code says what the cell is, but the weights say what the cell looked like on the day they were fitted, on top of what a large collection of photographs looked like. Keeping that in step is a maintenance job the programmed solutions do not have, and the part that came from outside cannot be regenerated here at all.

Finally, the domain gap is real and it is not removed. Fine-tuning does fit the model to shaded depth pictures, so it runs on the pictures it was fitted on, which is the important thing. What remains is an expectation rather than a result. The borrowing is thought to be worth less than the usual advice implies, because the deep levels arrive describing a world of texture and colour this cell does not have. Nothing here measures it, because measuring it would mean fitting the same model from a random start and comparing the two, and that run does not exist in this folder.

<!-- section: the-general-ideas-behind-this | The general ideas behind this -->

The next part of the page explains the general ideas behind this solution. Nothing here was invented for glassware. Every component is a standard piece of the modern detection toolkit. What is specific to this cell is only the choice of one class, the source of the labels, and the shaded depth pictures.

First is region-based detection, which works by proposing regions and then examining them. The general idea is to answer an open question by turning it into many closed ones. Rather than asking a network to name every object at once, it finds regions that might hold an object and asks a fixed question about each region on its own. The original R-CNN method, published by Girshick and colleagues in 2013, did this with an external region finder. Fast R-CNN made the examining stage share one pass over the picture. Then, Faster R-CNN replaced the external finder with a small network of its own, so that the whole thing became one model. 

This approach is used wherever accuracy matters more than speed and objects must be reported individually, such as in inspection, medical imaging, aerial survey, and any counting task. It is rarely the right choice when the answer is needed many times a second on limited hardware, because examining each region separately costs more than the one-pass detectors that predict boxes straight from a grid. You can read more about this by looking up object detection.

Next is Mask R-CNN, which puts a mask inside each region. This adds a third output to the examining stage, alongside the class and the tightened bounding box. The third output is a small grid saying which parts of the box are the object. The authors of Mask R-CNN, published in 2017, also showed that the cut-out step has to read positions between whole pixels by blending rather than rounding. The variant used here is a ResNet-50 Feature Pyramid Network version two, which is the same design but with a modernised training recipe. 

Mask R-CNN is used wherever objects of one class touch or overlap and have to be reported separately. Examples include counting cells under a microscope, counting fruit on a tree, picking parts out of a bin, and exactly the job being done here. It is rarely right when a class map is all that is wanted, because the region machinery is then pure cost.

The third idea is feature pyramid networks, which handle every scale at once. A deep backbone produces levels that are precise about position but poor about context near the input, and the reverse near the output. A feature pyramid network builds a path back from the deep levels to the shallow ones. It adds each deep level into the matching shallow one, so that every level ends with both properties, and the detector runs on all of them. 

This technique is used in nearly every modern detector. It is the standard answer whenever the objects in a picture vary a great deal in size, which they do here because the same glass is small from the top and large from the side. It is rarely necessary when every object is about the same size in every picture, where a single level does the job for less arithmetic.

Fourth is transfer learning and fine-tuning, which means starting from somebody else's numbers. You take a model fitted on a large general task, keep its weights, replace the last layers with ones shaped for the new task, and continue training on the new data. It works because the early layers of a vision model learn things common to all vision, like edges, corners, gradients, and textures. Only the later layers learn things specific to the original task. Researchers measured this directly in 2014, showing how transferability falls away with depth. This is the effect described earlier on the page in the part about what knowledge is actually being reused. The weights borrowed here come from COCO, a large collection of photographs of everyday objects labelled with masks. 

Transfer learning is used whenever labelled data for the real task is scarce, which is almost always. It is rarely the right choice when labels are free and plentiful and the new pictures look nothing like the borrowed ones. In that case, the borrowed weights bring knowledge of a world you do not have, while also forcing your model to be the size somebody else chose. That is the argument made on the linked page about a network trained from scratch. This solution takes the other side of that argument deliberately, to find out what the borrowing is worth here. This is explained more fully in general resources on transfer learning.

The fifth idea is non-maximum suppression, which keeps one answer per object. When many overlapping claims describe the same thing, you sort them by confidence, keep the best, discard everything overlapping it too heavily, and repeat the process on what is left. The procedure is old and appears wherever detectors do, with an efficient formulation given by Neubeck and Van Gool in 2006. A softer variant, called Soft-NMS, reduces an overlapping box's score rather than deleting it. It exists precisely for scenes where two different objects really do overlap heavily. 

Non-maximum suppression is used in every detector that produces more candidates than objects, which is all of them, and also in corner finding, peak picking, and line detection. It is rarely right without care in crowded scenes, because it cannot tell duplication from genuine overlap. This cell is one of the awkward cases, since splay can push one glass's outline right across another's.

Finally, there is average precision, a way of measuring a detector honestly. A detector's output is a list with scores, so measuring it is not a simple matter of counting right answers. The standard measure sweeps the score threshold from high to low and records precision against recall. Precision is the share of reported objects that are real, and recall is the share of real objects that were reported. The area under that curve is the average precision. This summarises the whole trade-off in one number and so does not depend on where the threshold happens to sit. Whether a reported object matches a real one is decided by the overlap between their masks. The form in general use was set out for the PASCAL Visual Object Classes challenge in 2010 and carried into COCO.

This measurement is used for every detection and instance segmentation benchmark there is, and it is right whenever a method returns a ranked list and the operating point is not fixed in advance. However, it is rarely the right measure on its own here, and the reason matters. Because it averages over everything, a method that finds most glasses well and misses the rarest and most dangerous case still scores well. The failure this problem says to watch hardest is a glass that produced no pixels, and that failure moves this number very little. The lesson is the same one drawn in solution six about pixel accuracy: a score that averages over easy cases will be optimised by a model that is good at easy cases. You can find more on this by looking up precision and recall.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page looks at where this fine-tuned instance segmenter sits among the other solutions. It sits between two other approaches that answer the same question but borrow different amounts of outside work.

First, compare it to the solution that trains a network from scratch. That approach builds a small network from nothing using labels provided by the simulator. Because it produces a class map, which cannot separate individual instances, it has to add an extra separating stage on top. This fine-tuned solution, on the other hand, asks directly for instances and gets them, so no separating stage is needed. In exchange, the network trained from scratch is tiny. It is just a few hundred thousand weights that can be saved right alongside the code and regenerated without a second thought. This solution is a large downloaded file that cannot be regenerated locally. The trained-from-scratch network also uses a different mechanism involving arrows, which works well even when two glasses actually touch. That touching scenario is not untested here. In crowded layouts where glasses stand so close along one line that their bodies meet, this fine-tuned solution is scored on them. It finds about three quarters of the glasses and merges a couple of pairs into a single report. So, the choice between them is not simply that borrowing is better. It is a choice between immediate capability and having a model that the project fully owns.

Compared to the solution that segments anything and then keeps the glasses, the trade-off runs the other way. That approach borrows more and trains less. Its segmenter is used exactly as downloaded, and the only thing it learns is a small decision about which of the proposed segments are actually glasses. That requires almost no training data, but it brings the largest domain gap of the three learned solutions, because nothing about the borrowed weights is ever adjusted to the specific pictures this robot cell renders. This fine-tuned solution trains more, adjusting its weights to the actual input. That is why its domain gap costs accuracy rather than correctness. If the question is how little training you can get away with, the segment-anything approach wins. If the question is which model has actually seen the cell's pictures, this fine-tuned solution is the winner.

Next, compare it to the solution that predicts amodal masks for the hidden parts of the glasses. The difference there is exactly one target, and nothing else. It uses the exact same architecture, but is asked to mark each glass's entire silhouette, rather than only the part the camera can see. When measured, that extra completion step buys an advantage in exactly one place. On crowded layouts, the amodal solution finds about one glass in ten more than this one, and it cuts the worst placement error by about a quarter. However, on the layouts the cell actually produces, the two solutions score identically, right down to the same worst case. This shows that completing the hidden parts buys nothing when nothing is standing in front. Therefore, this fine-tuned solution is the simpler of the two and gives up nothing on an ordinary table, while the amodal solution is what a crowded table requires.

Against the programmed approach that clusters on the table, the comparison is the same one every learned solution faces. On any day the depth readings work, the clustering solution is better in almost every way that matters. It is a page of arithmetic rather than a massive file of weights, it needs no training set, it can explain its own failures, and it can explicitly say where it has not looked. This fine-tuned solution also relies on depth, because depth shaded into grey is the only picture the renderer makes, so it does not buy any independence from the depth camera. What it does buy is that no length parameter has to be chosen, and no merged clusters have to be caught after the fact.

Finally, what none of these appearance-based solutions can do is notice when a glass is completely absent from the picture. That failure is answered by geometry rather than by appearance. The clustering approach works out where a glass could have been hiding. Another solution decides which of those hiding places is worth the trip to look. A third solution turns that decision into a pose the robot arm can reach. This fine-tuned segmenter simply supplies the masks that those three geometric solutions argue from; it does not make the argument itself.
