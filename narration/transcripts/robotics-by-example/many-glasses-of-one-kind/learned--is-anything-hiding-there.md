<!-- section: lead | Solution 5 — a learned verifier over the places nobody could see -->

Solution five: a learned verifier over the places nobody could see.

This approach is a hybrid, with a machine learning model acting as a verifier. The geometry can say where an object could be hiding, but it cannot say whether one probably is. The goal is to learn that one specific decision, using numbers that the geometry has already worked out.

As a quick reminder, the physical setup is described in full on the earlier page about the cell. That page covers the layout, the two positions the camera works from at the top and the side, all four sensors, and the specific words this project uses for them. What follows here covers only what is specific to this fifth solution.

<!-- section: introduction | Introduction -->

Solution five, a learned verifier over the places nobody could see. 

The introduction to this page explains how to add a trained model to the hardest difficulty in this problem, which is that an object can be absent from a picture altogether. The programmed solutions get as far as they can go on their own. They work out where an object could have been hiding and report those places as unsearched. What they cannot do is say which of those places is likely to have something in it, and that matters because looking costs seconds and there is a budget. By the end you will understand why this particular model cannot be shown pixels even in principle, what it is shown instead, why one of its inputs comes from the problem statement rather than from the camera, and why its most useful answer is again that it cannot tell.

This approach replaces an earlier solution five, which put a verifier over the clustered groups to decide whether a group was one object or two. That solution answered a real question and it still would, but it answered the wrong one for this problem. A verifier over groups is never consulted about an object that produced no group. The pattern is kept, but it is now pointed at the decision that actually matters.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solution solves. We start from what the programmed side produces, because this solution takes its input from there and adds nothing to the perception itself. 

The earlier page on clustering on the table explained how the system places every object the pictures contain, and then does something less obvious. It works out which parts of the table could not have been seen. Because the objects that were found have known positions, widths, and heights, the region each one hides can be computed. Any patch of that region large enough to hold the smallest object of the kind is reported as an unsearched patch. The arithmetic that computes that region is not the same from the two places this cell photographs the table, and the difference decides what the verifier can usefully be asked. The later part of this page about when the glasses are completely hidden works both cases out.

So the run ends up holding a short list of places, each carrying one honest statement: an object of this kind could be standing here, and nothing would have shown it.

That statement is exactly true, but not very useful on its own, and the reason is worth being precise about. It is a statement about possibility, and what the run needs is a statement about likelihood. Every scene produces some unsearched patches, because objects always hide something behind them. Looking at all of them would spend the whole budget on places that are almost certainly empty.

It is tempting to sort the patches with a rule, such as largest first, or nearest the middle of the zone. That is worth doing, and it is worth knowing why it is not enough. 

The evidence bearing on whether something is hiding in a given patch is made up of several weak pieces at once, and none of them is decisive. A large patch can hold an object, but large patches are common. A patch cast by a very tall object is more likely to be hiding something simply because tall objects hide more of the table. A patch near the edge of the zone is less likely to hold anything, because objects are placed inside the zone and the edges see fewer of them. And a patch that two stations both failed to see is a different proposition from one that only a single station missed.

Combining several weak pieces of evidence, none of which is decisive, is the thing a threshold does worst and a fitted model does best. That is the whole argument for this solution, and it is the same argument the verifier pattern always rests on.

There is also one input worth singling out, because it does not come from the camera and it is the strongest single clue available. 

The problem statement says there are four to six objects on the table. So if the survey found four, then as many as two are unaccounted for, and every unsearched patch is suddenly much more interesting. If it found six, then nothing is missing, and every patch can be ignored however large it is.

That is a genuinely useful prior, and the programmed side makes poor use of it. Using it well means weighing how many objects are unaccounted for against how plausible each patch is, which is again the combination of weak evidence that a rule handles badly.

<!-- section: the-main-idea | The main idea -->

The next part of the page explains the main idea of this solution. The core concept is the same division of labour used by the other hybrid approaches, and it is chosen specifically so that the learned part of the system cannot do any harm.

First, the geometry decides what is possible. It produces the patches of space, and it alone decides whether a patch is large enough to matter. If a patch is too small to hold the smallest object of that kind, it never reaches the model at all.

Second, the model decides only the order. For each patch it receives, it returns a probability that something is standing in it. However, nothing downstream is allowed to treat a low probability as proof that a patch is empty. The patch stays on the report as unsearched either way. What the probability actually changes is which patches the arm spends its looks on first.

This ordering is worth stating as a rule, because it is what makes the solution safe to add. The rule is that the model can waste a look, but it cannot cause a missed object to go unreported. A patch that the model scores low is still reported as unsearched, and the run is still honest about it.

<!-- section: why-this-verifier-cannot-be-shown-pixels | Why this verifier cannot be shown pixels -->

The next part of the page explains why this verifier cannot be shown pixels. Every other learned solution in this set has to argue for using measurements rather than raw pixels, and the argument is usually about cost and transfer. Here the argument is much shorter, and it is worth pausing on because it is unusual. The thing this model is asked about is defined by the absence of pixels.

An unsearched patch is a piece of the table that no camera could see. There is no picture of it. There is nothing to crop, nothing to feed a network, and no image at all in which the answer might be hiding. Whatever the model is shown, it cannot be the patch, because the patch was never photographed. That is not an inconvenience to be worked around; it is the definition of the thing.

So the input has to be a description of the patch and its surroundings, built from what was actually seen. This is a useful reminder about learned components in general. Before asking what a model should be shown, it is worth asking what evidence exists at all.

One qualification belongs with that argument. The absence of pixels is not the same absence in the two views. A picture taken straight down at least shows the outline of the object that does the hiding, and that outline says how far the hiding reaches. A level picture does not show even that. The later part of the page about when the glasses are completely hidden separates these two cases.

<!-- section: what-the-verifier-is-shown | What the verifier is shown -->

The next part of the page explains what the verifier is actually shown. The input is a handful of measurements, and they fall into three groups. Each group answers a different kind of question.

First, there are measurements about the patch itself. These include how much area it has, how many of the smallest object's footprints would fit inside it, how elongated it is, and how far it sits from the middle of the zone. Shape matters as well as size, because a long, thin patch of a given area is less likely to hold a round footprint than a compact one.

Second, there are measurements about what casts the patch. The verifier is shown the height and the width of the object whose outline hides it, how many objects contribute to it, and whether the patch is cast by an object or by the edge of the frame. Those matter because they say how the patch came to exist. How much the casting object's height buys it depends on which of the two views the patch came from, and that is worked out later on the page in the part about when the glasses are completely hidden.

Finally, there are measurements about the scene as a whole. There is how many objects the survey found against the number the problem allows, how much of the zone is accounted for by the objects already placed, how many stations failed to see this patch, and how many looks the budget has left. That first item is the count prior described earlier, and it is the input that ties a patch to the rest of the scene rather than treating it in isolation.

A table then lists these measurements to explain exactly why each one bears on the question. The pattern across the table is that each measurement helps weigh the physical realities of the scene to judge how likely a patch is to hide an object. For example, it notes that a patch far from the middle of the zone is less likely to hold an object, because objects are placed inside the zone, so the edges hold fewer. It points out that tall objects hide much more of the table when seen from above, meaning the patches they cast are more often occupied. It also explains that knowing how many looks the budget has left is important, because the ordering of the patches matters much more when only one look remains.

Every one of those inputs is a length, a count, or a ratio. None of them changes when the arm stands somewhere else, because they are all computed on the table rather than in a picture.

<!-- section: calibration-which-is-what-makes-the-number-mean-anything | Calibration, which is what makes the number mean anything -->

The next part of the page explains calibration, which is what makes the verifier's numbers mean anything. 

The verifier returns a probability, and before a threshold can be put on it, one specific property has to hold. This is the same property that the other learned solutions need, and for the same reason. A probability is considered calibrated when its claims come true about as often as it says they will. For example, if the model says a patch is very likely occupied, then the patches it scores that highly should usually turn out to be occupied. If it says a patch is probably empty, a fair share of those should still turn out to hold something. If this is not the case, the ordering is just an ordering of an arbitrary number.

Very often, models are not calibrated. The standard repair for this is not to build a better model, but to add a separate, tiny step afterwards. First, you fit the model. Then, you fit a small function that maps its raw scores onto honest probabilities, using data that the model never trained on. This costs a held-out dataset and about a second of computation time. It does not make a wrong answer right, but it makes the model's claim about that answer honest.

Checking calibration is straightforward here because the simulator knows exactly what it spawned. To do this, you run the pipeline over a few hundred arrangements. You collect every unsearched patch along with the probability the model gave it, and you record whether an object really was standing there. Then, you simply compare what the model claimed against what actually happened.

There is one specific thing to watch out for in this solution. Occupied patches are rare, because most of the hidden table really is empty. Because of this, a model that simply says everything is empty will score very well on accuracy, but it will be completely useless. Therefore, the measurement that matters is not how often the model is right overall. Instead, it is whether its high scores are actually enriched for occupied patches. This is exactly what a calibration plot shows, and what a simple accuracy figure hides.

<!-- section: two-thresholds-and-the-third-answer | Two thresholds, and the third answer -->

The next part of the page explains the two thresholds and the third answer. As with the other verifiers in this set, there are two thresholds rather than one, and the gap between them is the point. 

First, if a patch scores above the high threshold, it is probably occupied. It goes to the front of the queue for a look, and if the budget allows only one look, this is the patch that gets it.

Second, if a patch scores below the low threshold, it is probably empty. It is still reported as unsearched, because this is the part that must not be skipped, but it is not worth an arm movement while anything else is waiting.

Finally, if the score falls between the two thresholds, the model is essentially saying that it cannot tell. Here, that answer has a particularly clean meaning. It means the geometry and the count between them do not settle whether something is hiding, which is precisely the situation in which another picture is the only way forward.

The width of the band between the thresholds is a dial with a cost on each side. If you widen it, more patches are treated as worth looking at, which costs arm time but misses fewer objects. If you narrow it, the arm moves less, but more objects stay missed. Because a missed object is the worst failure this problem has, and extra arm time is merely slow, the band should start wide. It should only be narrowed when a scored run shows that the extra looks are finding nothing.

<!-- section: how-the-concepts-fit-together | How the concepts fit together -->

The next part of the page shows how these concepts fit together in a flowchart of the complete process. The chart uses color coding to separate the steps: blue for the work the programmed solutions already do, green for what this new solution adds, and grey for the learned model itself.

The process begins by clustering on the table and placing every object the pictures contain, which allows the system to compute what could not have been seen. Next, it checks if each unseen patch is big enough to hold the smallest object. If it is not, the patch is ignored, because nothing of this kind could fit inside it. 

If the patch is big enough, the system describes the patch, the object that casts it, and the surrounding scene. This description is fed into the verifier, which is the learned model, and the model returns one calibrated probability. 

The system then checks where this probability falls against the thresholds. If it is above the high threshold, the patch is queued first for a look. If it falls inside the middle band, it is also queued, but with a note that the geometry could not settle it. If the probability falls below the low threshold, it is reported as unsearched, but the robot does not spend a look on it. 

For the patches that were queued, the system calculates how to cover them using the fewest camera positions. The robot then moves, takes new photographs, and the cycle starts again. Meanwhile, the patches that fell below the low threshold go straight to the final report, which ultimately lists all the found objects alongside every unsearched patch.

Two things about this flow are worth pointing out. 

The first is where the model sits in the pipeline. Everything that can actually remove a patch from consideration is pure arithmetic. The size test drops the patches nothing could fit in, and the covering step decides which camera positions to use. The model only sorts what is left. Because of this, a wrong prediction from the model only costs one wasted look, or one look taken later than it should have been.

The second important point is that every patch reaches the report, whatever the model said about it. The probability changes the queue, but it never changes the record. This is the property that makes the solution safe. In this problem, the worst possible failure is a missing object that nobody knows about, and no score the model produces can ever bring that about.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page explains what happens when the glasses are completely hidden. The rest of this document takes one situation for granted, which is an object that contributes no pixels at all. That is the difficulty this solution exists for, so it is worth being exact about it, and being exact splits it in two. The cell photographs the table from two places, and the arithmetic that hides an object is different in each. Which of the two produced a patch decides what the verifier can be asked about that patch, so the two are worth separating before the worked example puts numbers on one of them.

The objects in this cell are drinking glasses, and this section says glass rather than object throughout, because every number in it was measured on one of the project's own glass shapes rather than reasoned about in the abstract.

The two places are set out in full on the page about the cell. The survey view is the camera 450 millimeters above the table looking straight down, which is what finds the glasses in the first place. The level view is the camera 120 millimeters above the table, standing 380 millimeters back from one glass and looking level at it, which is what measures that glass once it has been found. This section calls them looking straight down and looking level.

First, consider when the camera is looking straight down. Start with why a standing glass does not photograph as its footprint.

The camera is 450 millimeters above the table and points straight down. Call that height H, and call the point on the table directly below the lens the nadir. Take a horizontal slice of a standing glass at a height z above the table. That slice is nearer the lens than the table is, so it is imaged as though it had been scaled about the nadir by a factor of H divided by the quantity H minus z. Both the slice's distance from the nadir and its radius are multiplied by it. At a height of 450 millimeters, a slice 225 millimeters up has a scaling factor of 2.0, so it appears twice as far from the nadir as it really is, and twice as wide. This project calls that outward throw splay, and the earlier page on clustering on the table works through its consequences for the geometry.

Splay is what lets one glass reach over another, and the reaching is worth following with real numbers.

Take the largest glass this kind allows, 229 millimeters tall and 103 millimeters across the rim, and stand it 200 millimeters from the nadir. Its rim is thrown out by a factor of 2.04, so its outline does not sit over the glass. The outline runs from 175 millimeters to 513 millimeters from the nadir, and it covers a wedge 29.8 degrees wide.

Now stand the smallest glass the kind allows, 94 millimeters tall and 84 millimeters across, 150 millimeters further out along the same line from the nadir. That 150 millimeters is the closest two glasses ever stand in this cell. Because the short glass is short, its own rim is thrown out by only 1.26. Its whole outline therefore falls inside the tall glass's outline, and it contributes not one pixel.

What comes back is a single group, and the circle fitted to it is 103 millimeters across. That is the tall glass's own width and it sits inside the kind's range of 65 to 105 millimeters, so nothing about the group looks wrong. The picture is one legal glass where there are two.

Three properties of this case are worth having separately, because the second case below has none of them.

First, it needs both closeness and a large difference in height. The difference in height is the gap between the two throws above, 2.04 against 1.26. The closeness shows up in how far out the pair has to stand before the swallowing happens at all. At 150 millimeters apart, the tall glass has to stand at least 178 millimeters from the nadir. At 200 millimeters apart it has to stand 260 millimeters out, and at 250 millimeters apart, 342 millimeters out. This needs the camera at one end of the glass zone and the pair at the far corner of it, because the zone is only 320 by 360 millimeters.

Second, the hidden glass is always the shorter one. The scaling factor grows with height, so a shorter glass is never thrown far enough to reach over a taller one, however close the two stand.

Finally, it depends on where the pair lies about the nadir. Splay throws both outlines away from the same point, so what matters is whether the pair lies along a radius from that point or across one. The same two glasses, the same 150 millimeters apart, turned across the radius instead of along it, both come back, because the short one's outline clears the tall one's entirely.

This leaves the verifier with a geometric hint, which is the whole difference between this case and the next one. The survey reads depth, so the tall glass's height is measured and the scaling factor follows from it by arithmetic. The outline says the same thing a second way. Its outer edge is the rim thrown out by 2.04 and its inner edge is the base thrown out by almost nothing, so the ratio between them is the splay factor. Either route gives the wedge and the stretch of it that nothing could see. For the pair above, that comes to about 43,000 square millimeters of table.

One of the verifier's inputs is how many of the smallest object's footprints would fit in a patch, and this patch shows why that input has to be computed carefully. The smallest glass of the kind has a footprint of 3,300 square millimeters, and 43,000 divided by 3,300 is thirteen. Only six of them actually fit, because circles do not tile and this patch is a long wedge rather than a compact blob. The input is meant to say how many glasses could be standing there, so it has to be the packed count and not the ratio of the areas.

Nothing in the picture says a glass is standing in that patch. What the picture does say is how much room there is, where the room is, and what shape it has, and those are numbers a model can be fitted on. Keep hold of that, because the next case does not have it. A diagram here shows the tall glass swallowing the short one from above. The survey hands back one group of one legal width, and the patch left over has a wedge, a reach, and an area that were all read off the picture.

Now consider when the camera is looking level. The level view differs in every respect that matters, and the reason is that nothing is thrown anywhere.

The camera comes down to 120 millimeters above the table, stands 380 millimeters back from the glass it is measuring, and points level. A glass in front of another glass covers it, and that is the whole mechanism. There is no scaling about a point, so none of the three conditions above applies.

Take the narrowest glass this kind allows, 197 millimeters tall and 65 millimeters across. Standing 380 millimeters from the camera, it blocks a wedge 9.8 degrees wide. By 231 millimeters behind it, that wedge is already 105 millimeters across, which is the widest glass the kind allows. So from 231 millimeters behind the near glass outwards, the blocked strip can hide a glass of any size this cell puts on the table.

Now put the largest glass the kind allows, 229 millimeters tall and 103 millimeters across, 300 millimeters behind it and in line with the camera. On its own, that glass would fill 3,073 pixels of the 320 by 240 frame. Behind the near glass, it fills none of them. The picture the camera returns is identical, pixel for pixel, to the picture it would return with the far glass taken off the table altogether.

Three things follow, and each is the opposite of what held above.

First, distance between the two glasses buys nothing. Two glasses of the same size, one behind the other in line with the camera, hide each other exactly at 150 millimeters apart and exactly at 300 millimeters apart. Hiding here is a question of angle rather than of separation. So the cell's rule that two glasses never stand closer than 150 millimeters center to center does not remove this case, although it does keep two glasses standing side by side from merging into one shape.

Second, the glass that is lost is the further one, not the shorter one. Being tall is no protection. In the pair above, the glass that disappears is the taller of the two by 32 millimeters and the wider of the two by 38 millimeters. What decides whether it disappears completely is how much of the frame the near glass fills, and the next point is why that is so heavily in the near glass's favor.

Finally, being nearer is worth more than being large. The near glass is magnified relative to the far one by the ratio of their distances from the camera, which here is 680 over 380, or 1.79. That is why a glass 65 millimeters across covers one 103 millimeters across. The near glass may also be shorter than the one it hides, though not by any amount. Of the glasses drawn for this check, the shortest one that still covers that 229 millimeter glass completely is 181 millimeters tall. Below that, the near glass covers the lower part of the far one and its rim shows above.

The strip itself can still be computed, and it is not small. Over the 360 millimeter depth of the glass zone, the near glass blocks about 32,500 square millimeters of table, with room for four of the kind's smallest footprints. But every one of those numbers comes from the near glass's position and its size, which the survey and the measurement between them already knew. The level picture contributed none of them and could not have, because it is the same picture whether that strip holds a glass or nothing. A diagram of this view shows that the picture with both glasses standing and the picture with the far one taken away are the same picture, and the strip of table the verifier is handed was computed entirely from what was already known.

This leaves the verifier with nothing from that picture. Two pictures that differ by no pixels cannot carry two different sets of inputs, so no measurement taken on a level picture can tell a patch with a glass in it from the same patch empty. Every number the verifier is given about such a patch has to come from somewhere else, and there are three places it can come from. The survey looked from above and from three stations, and it may have placed the far glass already. The count of objects found against the number the problem allows is the input described earlier on the page, and it says how seriously to take the set of patches at all. And the level views already taken from other angles each blocked a different strip, so between them they narrow where an unaccounted-for glass can be.

That asymmetry is the reason for separating the two cases. Looking straight down, the patch has a measured size, a measured shape, and a measured cast, so the verifier's questions about the patch have answers. Looking level, those same questions have no answers, and the whole weight falls on the group of inputs about the scene as a whole, which are how many objects are unaccounted for, how much of the zone the objects already placed account for, and how many stations failed to see this patch.

The practical consequence is small and worth writing down before any of this is trained. One model serves both cases, and it has to, because the patches arrive in one list. But a patch from a level view arrives with its patch-description inputs carrying almost nothing, and a model fitted mostly on overhead patches will learn to lean on exactly those. So the training set has to hold both kinds in the proportion the run will meet them, and the inputs about the scene as a whole are the ones that must not be dropped for looking weak on average.

<!-- section: a-worked-example | A worked example -->

The next part of the page walks through a worked example. 

The survey has finished. It found four objects, and the problem allows four to six, so as many as two may be unaccounted for. That fact alone raises the stakes on everything below.

The blind-region arithmetic returns three patches large enough to hold the smallest object of the kind. The budget allows one extra look.

The first patch lies behind the tallest object in the scene, on the far side from the arm. It is compact rather than elongated, it could hold two of the smallest footprints side by side, it sits well inside the zone, and two of the three stations failed to see it. Every piece of evidence points the same way.

The second patch is larger in area but a long thin sliver, squeezed between the edge of the frame and the outline of a middling object. Its area would suggest it is the best candidate. However, its shape says a round footprint would not fit comfortably anywhere in it, and one station saw most of it.

The third patch is compact and reasonably large, but it lies right at the edge of the zone, where objects are rarely placed, and only one station missed it.

A rule that sorted by area would take the second patch, which is the sliver. A rule that sorted by how many stations missed it would take the first, which happens to be right, but would have taken the sliver too if the sliver had been missed twice.

What the verifier does with these is combine the pieces. The first patch scores high because it is compact, roomy, central, missed twice, and there are two objects unaccounted for. The second scores low despite its area, because the shape and the single-station miss both count against it. The third lands in the middle, because central placement is the one thing it lacks.

So the single look goes to the first patch. The arm moves to a camera position from which that patch is visible. This position is chosen by the covering step, which also checks whether the same position happens to see either of the others. The camera takes the picture, and the clustering runs again over everything.

Both endings are worth following. If an object is standing in that patch, it is found, the count reaches five, and the two remaining patches are re-computed from the new set of objects, which usually shrinks them. If the patch turns out to be empty, that is not a wasted look. The patch leaves the unsearched list, the count still stands at four, and the remaining patches become more suspicious rather than less, because there are still two objects unaccounted for and fewer places left for them to be.

That second ending is the one that shows why the count prior is worth having. A verifier that looked at each patch in isolation would learn nothing from an empty result. One that knows how many objects are unaccounted for learns something from every look, whichever way it goes.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page looks at where this learned verifier is strong and where it breaks down. 

The strengths come from the narrowness of its job and from where it sits in the system. Because it answers just one question over a handful of inputs, it needs very few examples, it trains in seconds, and it can be inspected simply by printing its inputs beside its answer. Its training labels are also free, because the simulator knows exactly what it spawned and therefore knows whether each patch was actually occupied. It cannot cause the failure this problem cares most about, because every patch reaches the final report whatever score it gets. And it degrades gracefully to the programmed solutions. With no model at all, the patches are looked at in whatever order the geometry suggests, which is exactly what solutions two and three do together.

The weaknesses divide into three areas: what the model cannot see, what is hard about training it, and whether it is worth building at all.

First, what it cannot see is an inherited problem. The model reasons about patches computed from the objects that were actually found, so an object hidden behind an object that was itself hidden lies completely outside its reach. No amount of training fixes that, because the patch the model would need to be asked about was never computed in the first place.

Second, what is hard about training it is the rarity problem described earlier in the part about calibration. Occupied patches are in the minority, so the training set is unbalanced. This makes standard accuracy a useless measure, and the model will drift towards always saying a patch is empty unless the loss function and the scoring both account for that imbalance.

Finally, whether it is worth building at all is an honest question, and the answer for this specific robot cell is probably not yet. Solution two measured how often objects are actually hidden from every station, and the answer was never, because the three survey stations see every object between them. So in this cell, the unsearched patches are nearly always empty, the geometry's own ordering is good enough, and a model would just be sorting a list that rarely matters.

What would change that calculation is any of three things: dropping a survey station, widening the zone, or letting the objects stand closer together. All three of these make hidden objects real rather than theoretical, and at that point the ordering starts deciding whether objects are actually found. The thing to do before building this model is therefore to measure how often a patch is occupied, exactly as the earlier solution five said to measure the size of its ambiguous band first.

<!-- section: where-the-idea-comes-from | Where the idea comes from -->

This section explains where the idea comes from. The pattern used here is old and well named, and three distinct ideas sit behind it.

The first idea is to use a cheap, exact test first. The principle is to arrange the work in order of cost, so that a cheap, exact method handles everything it can, and an expensive or learned method is consulted only on what is left over. When the second stage checks the first, it is usually called a verifier. When it simply runs on whatever survived the first stage, it is called a cascade. The best-known example of this is the Viola-Jones face detector, which made real-time detection possible by rejecting almost every part of an image using just a handful of arithmetic operations.

This approach is used wherever there is a large, easy majority of cases and a small, hard minority. However, it is rarely the right choice when the cheap stage cannot be made both fast and safe. This is because whatever the first stage wrongly discards, no later stage will ever see. In our problem, the first stage is the patch-size test. It is safe because it is exact: a patch that is too small to hold the smallest object genuinely cannot hold one.

The second idea is classification with a reject option, which means allowing a model to decline to make a decision. Instead of forcing every input into a specific class, you allow a third answer: decline, and hand the case over to something else. In this solution, that something else is an arm movement. The rule for when to decline is old and simple, dating back to a nineteen-seventy paper by Chow. It says to decline when the best probability falls below a threshold, and that threshold is set by comparing the relative cost of making an error against the cost of refusing to decide.

This technique is used wherever being wrong is expensive and a fallback option exists. It is rarely the right choice if declining simply means failing. But here, declining just means moving the arm to look, which is cheap, so the reject option easily earns its place.

The third and final idea is about priors, and why the count matters. This is the most general idea, and the one least often used well. A prior is simply information you already had before you took a measurement. Combining that prior correctly with the measurement is what turns a raw reading into a belief.

In this problem, the count of four to six objects is exactly that kind of prior. It tells you nothing about any individual patch of space, but it tells you everything about how seriously to take the set of patches as a whole. If you have already found six objects, the patches are irrelevant. If you have only found four, you know that two objects must be somewhere.

The general lesson here is worth carrying forward. When a learned component seems to need more evidence than the sensors can provide, it is always worth asking what the specification of the problem already guarantees. In this case, the specification supplied the strongest single input that the model has.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page explains where this solution sits among the other solutions. It sits on top of two programmed ones and adds nothing to either. Solution two finds the objects and computes the patches. Solution three covers the patches with camera positions and performs the movement. This solution only decides which patches are worth the covering step's attention first.

Against the other learned solutions, the comparison is about which difficulty each one attacks. Solutions seven and eight replace the perception itself, and neither of them can help here, because a model that labels pixels has no pixels to label. Solutions four and six order candidate viewpoints for a doubtful object, which is a different request from a suspect place. This solution is the only learned component in the set pointed at the difficulty the problem statement says to watch hardest.

This makes its honest position slightly awkward and worth stating plainly. It is aimed at the most important difficulty, and it is also the one whose value most depends on a measurement nobody has taken yet.
