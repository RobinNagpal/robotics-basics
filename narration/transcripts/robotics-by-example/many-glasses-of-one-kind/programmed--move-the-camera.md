<!-- section: lead | Solution 3 — move the camera -->

Solution 3, move the camera. 

This approach is programmed, and it uses a loop. Instead of working harder on the pictures you happen to have, the idea is to go and take better ones. You can choose where to stand using a rule simple enough to print.

The physical setup of the cell is described just once, on the earlier page about the cell. That page covers the layout, the two places the camera works from, which are from the top and from the side, as well as all four sensors, and the specific words this project uses for them. Because of that, what follows here will only cover what is specific to this third solution.

<!-- section: introduction | Introduction -->

Solution three, move the camera. 

This introduction explains what to do when no amount of processing can answer a question, simply because the picture never contained the answer in the first place. This happens whenever one object stands behind another, since the hidden part of the far object was never measured. The fix is to move the camera and take a better picture, and the interesting work is in choosing exactly where to move it to. 

By the end of the page, you will understand several things. First, why finding a viewpoint is a different problem from separating objects. Second, how three cheap tests can decide where the camera may stand before the expensive motion planner is asked anything. Third, why deciding whether one object blocks another turns out to be pure geometry rather than image processing. And finally, why the order in which those tests run is what makes the whole method work.

There is a second kind of request this solution now has to serve, and it arrives from a different difficulty. Sometimes there is no object to go and look at, but only a place that could not have been seen. Serving that request turns the choice of where to stand into a covering problem rather than a scoring one.

Throughout this topic, we will say object rather than glass, because nothing in this solution depends on the objects actually being glasses. The word glass is only used when referring to the cell itself.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solution solves. The problem statement asks for one set of pixels per object, a place on the table for each of them, and an honest list of the ones that could not be separated. It names two difficulties, and the point worth pressing is that these really are two difficulties, and not one problem wearing two hats. A diagram illustrates these two distinct challenges.

First, there is the merge. This happens when a camera standing in line with two objects sees their outlines overlap, so the step that groups touching pixels hands back one patch where there are two objects. Solution two, which is covered on the page about clustering on the table, answers that difficulty. It throws the pixels back onto the table as points and groups them there, so two objects a legal distance apart come apart cleanly. 

Merging happens from both places the camera works from, and the reason differs between them. From the top, it happens because the range of sizes inside one kind of object is wide. A tall object's outline is thrown outwards far enough to reach a short one standing well beyond it, even though the two are a legal distance apart on the table. The merge is still worst from the side, which means down low, standing back from the object, and looking level. This is the position the shape measurement needs anyway, and from where most in-line pairs come back as one patch. However, the merge is no longer confined there.

The second difficulty is that an object can be absent altogether, and this is the difficulty that decides most of what this solution has to do. If you push that merging mechanism one step further, the object disappears from the picture entirely, contributing no pixels at all. A later part of the page about when the glasses are completely hidden works through how that happens from each of the two places the camera works from, and what this solution does about it. 

This is not a merge and it is not a doubtful measurement. It is a missing object, and it has a property neither of the other difficulties has: there is nothing in the data to flag. Every check in this project tests something that was found, such as a fitted width against a range, a residual, or a count of stations. None of them can fire for something that produced no pixels. Solution two answers this as far as it can be answered from arithmetic. Because splay is exact and the objects that were found have known positions, widths, and heights, the region of the table that could not have been seen is computable. Any patch of it large enough to hold the smallest object of the kind is reported as unsearched.

The third difficulty is the one this solution was originally built for, which is that an object can have no clear viewpoint at all. With the coarse ring of directions the cell tries today, which offers only a handful of widely spaced spokes around each object, getting on for half of all objects have no usable viewpoint. If you refine that ring to a fine one, the figure drops to a small fraction. We counted this over hundreds of drawn arrangements, at the widest footprint the cell handles, which is the hardest case. 

The important part of that result is why most of the failures happen. The ring is too coarse, and simply has no spoke pointing at the gap. Only a minority of objects are genuinely boxed in by their neighbours. So most of the loss is a choice the cell made, and not a fact about the world. Later in this document, we will see exactly that happen to one object.

Finally, the section explains why the three difficulties need different fixes. Nothing you do to a picture fixes the second or the third difficulty, and that is why this solution is a separate thing from solution two. The difference is worth stating carefully, because it is the reason the project needs both. 

Separating objects in a picture is a question about labelling, which means deciding which pixel belongs to which thing. The information needed for that is often still in the picture, hiding in the depth readings, in the shading, or in the width of the patch. Clustering on the table recovers it, because the depth reading survives being photographed. 

Finding a viewpoint is a question about what got measured at all. The shape measurement reads an object's outline against the background, row by row, and turns rows into heights. If a second object stands in the same part of the frame, then the outline is the outline of two objects stuck together. No cleverness afterwards can recover where one stopped and the other started, because that measurement was never taken. The only fix is to take a different measurement.

So separation is about interpreting a measurement, while viewpoint is about making a good one. The two barely overlap, and a cell that answers only the first has answered only part of the problem. 

The second difficulty is a third thing again, and placing it correctly matters. Separation asks which object this is. Viewpoint asks if I can measure this object. The missing object asks whether there is an object at all, and that question cannot be asked of the data, because the data is exactly what is absent. It can only be asked of the geometry.

<!-- section: the-main-idea | The main idea -->

The next part of the page covers the main idea behind this solution. It is exactly the approach you would use yourself. If you cannot see something from where you are standing, you simply walk around until you can.

All the work is in choosing where to move to, and the useful surprise is that most of that choosing is arithmetic rather than image processing. The rest of the page builds up to this one concept at a time. First, it explains the belief about the table that this method starts from. Next, it describes where the camera stands when it looks from the side. After that, it covers the three tests that decide which places to stand are allowed. Finally, it explains why the order of those tests matters more than any of them individually.

<!-- section: the-belief-this-method-starts-from | The belief this method starts from -->

The next part of the page explains the belief this method starts from. Before the arm can decide where to look next, it has to have some idea of what is on the table, and that creates a chicken-and-egg problem. You cannot predict what a viewpoint would show without knowing roughly what is there, but knowing what is there is the actual job.

A fixed survey solves this problem, and this is the one real prerequisite of the whole method. The survey assumes nothing, covers the whole zone, and hands back a coarse map of what is standing where. This solution then runs only on the doubtful entries in that map. So, it is the tail of the survey rather than a replacement for it.

A diagram here illustrates this fixed sweep, showing the camera taking positions over the work area to cover the table. The survey works from the top. The camera calculates from its own lens how much of the table one picture covers at its current flying height. Then, the system spreads out the minimum number of stations needed to cover the zone, with some overlap to spare. For this particular cell, that comes out as three stations in a line, marching away from the arm.

The useful part of a station is not the whole picture. It is the strip that both of the station's pictures share, and that strip is a good deal shorter from front to back than the picture itself. The stations are then placed close enough together that each strip overlaps the next by roughly half. This ensures that nothing ever lands only on an edge, where the view of it is worst.

As for why each station takes two pictures rather than one, the camera slides a short way sideways between them. The reason for this is worth following because it is a good example of getting depth without a depth sensor.

One picture from the top cannot say how far away anything is. All it can do is lay each outline down flat on the table. But an object stands above the table, so the laid-down point gets pushed outwards, away from the point directly below the camera.

Now, if you slide the camera sideways and take a second picture, the laid-down point moves. How far it moves depends on how tall the object is, because the top of a tall object is nearer the lens and therefore swings further than the top of a short one. So, comparing the two pictures measures the height, and once the height is known, the true position follows.

This effect is called parallax. You have likely seen it from a moving train, where the near fence races past the window while the far hills barely move at all.

<!-- section: where-the-camera-stands-when-it-looks-from-the-side | Where the camera stands when it looks from the side -->

The next part of the page explains where the camera is positioned for this side view. The extra look this solution adds is taken from the side. The arm brings the camera down low, stands it back from the object, points it level at the object, and approaches from a direction that has been cleared by three tests that follow.

How far back it stands is called the standoff, and it is worth knowing that this is not a number somebody typed in. It is worked out, and following the reasoning explains why the camera ends up where it does.

The camera is low down, at about the height of a rim, and it is looking level. So the frame has to reach downwards far enough to catch the object's foot, and upwards far enough to catch the rim of the tallest object the cell will accept. Both of those requirements are angles rather than distances, because a lens sees angles. So the question becomes how far back the camera must stand for the larger of those two requirements to fit inside half a frame. A little margin is then taken off as well, because the arm does not arrive exactly where it was sent.

Nothing in that chain is tuned. Change the lens and the standoff changes with it automatically, which is what you want from a derived number rather than a guessed one.

Two details of this cell catch people out, and both are worth knowing before anything is built.

First, the camera is not the tool. If you send the tool centre to the place where you want the camera, the camera ends up somewhere else, because it is bolted to one side of the tool. Worse, that offset turns as the wrist turns, so it is not even a fixed correction that could be applied once and forgotten.

Second, the roll has to be pinned. The shape measurement reads the object row by row, and a row means a height, so the camera must be level about its own viewing axis. Looking level along the table, the usual way of deciding which way is up gives a different roll depending on which side of the object the arm stands on, and which side the arm stands on is exactly the thing this solution varies.

<!-- section: the-three-tests | The three tests -->

The next part of the page describes the three tests that make up the heart of the method. A ring of candidate directions is listed around the doubtful object, with each direction being a place the camera could stand at the standoff distance, low down, and looking level. The ring is spread evenly all the way around. It begins from the direction that points back towards the arm's own base, because that is the direction the arm reaches most easily.

Every candidate then has to pass three tests, and a viewpoint that passes only two of them is worth nothing. The tests differ enormously in what they cost to compute, which is why the order they are run in matters.

The first test asks whether the arm can reach the viewpoint. The arm works comfortably only inside a band of distances from its own base. Nearer than that band, the arm has to fold over itself to get there. Further than it, the arm is stretched straight out with nothing left over for the wrist to point with. So, the first test drops every candidate whose standing place falls outside that band, measured flat on the table. It costs just one square root per candidate, which is to say nothing at all.

The second test asks whether another object would share the camera's frame. People often expect this to be difficult, but it is not, because of one gift this problem hands over for free: every object's footprint is a circle of known size, standing on a known plane. 

The page includes a diagram showing occlusion as geometry. It illustrates that from a camera at a given place, each object fills a certain angle of the frame, and that angle grows with the object's width and shrinks with its distance. Two objects share the frame when the angle between their centres, measured at the camera, is smaller than the sum of their two half-angles. That takes just a handful of arithmetic operations per pair of objects, and no picture is involved at all.

Judging this as an angle at the camera, rather than as a distance from the line of sight, matters more than it appears to. An object well off to one side but twice as far away fills the same part of the frame as one standing just beside the target, so a test based on sideways distance would incorrectly wave it through.

It is also worth noticing what the test deliberately does not check, which is whether the other object is nearer than the target. The shape measurement reads an outline against the background, so an object standing behind the target ruins that outline exactly as thoroughly as one standing in front of it.

There is a lovely simplification hiding in that test, and it is the most useful idea on this page. If you ask the test not about one camera place but about every direction at once, the distance drops out. 

Here is the argument. Stand a long way from a pair of objects, at some angle off the line joining them. As you move further away, the angle between the two objects measured at your eye shrinks in proportion to one over your distance. But their combined angular width shrinks in exactly the same proportion. So when you compare the two, your distance cancels out, and what is left is a statement about direction alone. The pair overlap when the sine of the angle you have turned away from their joining line is smaller than their combined width divided by the gap between their centres.

That has a pleasing geometric picture. Each neighbour casts a wedge of blocked directions, centred on the line joining the two objects, and pointing both ways along it. Standing anywhere inside that wedge means the neighbour is in your frame, whatever your distance. Standing outside it means the neighbour is not, again whatever your distance.

Now put the worst legal case into that picture. Two objects at the closest spacing the problem allows, both with the widest footprint the cell handles, have a combined width almost as large as the gap between their centres. The fraction is then close to one, so the wedge's half-angle is close to a right angle. Counting both sides of the joining line, one neighbour alone blocks something like a quarter of the whole circle of directions.

If you put four neighbours around an object, each casting a wedge of its own, and add the reach limit on top, running out of viewpoints stops being a freak event and becomes something to plan for. That is the arithmetic behind the earlier claim that getting on for half of all objects have no usable viewpoint on a coarse ring.

Finally, the third test asks whether the arm can fly there. It asks the motion planner whether a path exists that gets the arm to the pose without hitting anything. The objects the survey found are put into the planner's world as cylinders, so that a path sweeping an elbow through one is refused. This test costs far more than the other two, and it is also the only one that can fail for reasons no formula predicts, which is why it goes last.

<!-- section: why-the-order-of-the-tests-matters | Why the order of the tests matters -->

The next part of the page explains why the order of these tests matters. The order of those three tests is not just a detail of the implementation. It is the design itself. 

There is a diagram showing two different approaches, illustrating a concept of bounding before scoring. On the left of the picture is the order this solution uses. First, list every candidate pose. Next, drop the ones that are out of reach, and drop the ones whose view is blocked. Then, sort what is left, and only then call the motion planner. Because the list shrinks at every step, by the time the planner is asked anything, it is only being asked about poses that are genuinely worth flying to. It handles a handful of questions instead of a long queue of them.

On the right side of the diagram is a tempting alternative. This approach sorts the whole list by how good each pose looks, and lets the planner sort out the rest. The obvious cost of doing it this way is speed, because the expensive call to the planner is now made many times instead of just a few. But the cost that really matters is a different one.

The motion planner has no opinion about lines of sight. It will refuse a path that would sweep an elbow through a cylinder, because preventing collisions is its job. However, a camera pose that looks straight through one object at another is a perfectly good pose as far as the planner is concerned. It plans a path to it and reports success. The arm then takes a picture with two objects in it, measures them as one, and hands a confident, wrong answer downstream. A large share of the candidate poses are exactly like that.

So, the failure mode of scoring first and rejecting afterwards is that it is slow, and quietly wrong, with nothing ever throwing an error. That is the worst combination available.

The general rule behind this fix is worth remembering beyond this specific problem. You should order your tests by what they cost, putting the cheapest first, and let each test shrink the set of candidates that the next test has to look at. Arithmetic is free. Asking whether any set of joint angles puts the hand at a given pose is nearly free. The motion planner, however, is not free. And the physical robot arm itself is the most expensive thing in the building.

There is a second benefit to this ordering, and it is the more valuable one. Because the initial filter is nearly free, you can afford to list far more candidate directions than you would otherwise dare to. Generating a fine ring of many candidates costs the filter almost nothing, and it costs the planner nothing at all, because the filter throws away all but a few before the planner ever sees them. And having that fine ring of candidates is exactly what turns a situation where nearly half of all objects have no viewpoint into one where only a small fraction do. Therefore, the ordering of the tests is not merely a speed trick. It is what actually makes the method work.

<!-- section: what-is-left-to-score | What is left to score -->

The next part of the page covers what is left to score. Once the filter has run, everything that survives is safe to visit. This means that scoring only decides the order in which the surviving viewpoints are tried. This puts a strict limit on what a bad score can cost. The worst case is one wasted move, but it will never result in a wrong measurement.

For this particular cell, the score is calculated using a rule rather than a model. First, it prefers the viewpoint where the camera frame holds the doubtful object and nothing else. However, since every surviving viewpoint already satisfies this after the filter, in practice this rule only breaks ties. Next, it prefers the viewpoint that requires the least turn away from the line pointing back to the arm's base. This is because standing between the object and the base is the direction where the robot has the least reach to spare.

The textbook alternative to this approach is called information gain. To calculate information gain, you carve the room into small cubes and mark each one as free, occupied, or unknown. Then, you cast a ray for every pixel from each candidate pose, and count how much unknown volume that picture would resolve. This is all ordinary processor work, so it does not require a graphics card, and the standard implementation of the map is already kept by the motion planner anyway.

However, information gain is more than this cell needs, and the reason comes down to the shape of the doubt. Information gain is the right score to use when you do not know what you are looking for. But here, the doubt is just a short list of specific questions. For example, you might need to know if an impossibly wide patch is really one object, or if it is actually two. A score that directly answers a specific question like that will always beat a score that just measures unknown volume in general.

<!-- section: covering-the-places-nobody-could-see | Covering the places nobody could see -->

The next part of the page explains how to cover the places nobody could see. Everything up to here answers one shape of question: an object needs measuring, so where should the camera stand to see it? This section is about the other shape, the one the missing object created: a place could not have been seen, so where should the camera stand to see the place?

The difference sounds small and is not, because it changes what a good answer looks like.

The ring of candidate directions exists because an object has a position, so searching somewhere around it, at the right distance, looking at it, is a sensible family of poses to search. An unsearched patch has no object in it. There is nothing to look at and nothing to stand around.

Worse, a patch is not a point. It has extent, and a viewpoint either sees all of it, or part of it, or none of it. So the test that matters is not whether the line of sight is clear, but whether this patch is inside this camera position's visible region. This is the same arithmetic the second solution used to find the patch in the first place, run forwards instead of backwards.

That arithmetic is already available and cheap. For a candidate camera position, the wedges the known objects hide are computable, and so is the part of the frame that falls outside the picture. What is left is the visible region for that position, and testing a patch against it is a containment test.

Now put several patches together, which is the normal case, and the shape of the problem appears.

Each candidate camera position sees some subset of the unsearched patches. The run wants every patch seen, and every camera position costs seconds. So the question is: what is the smallest set of camera positions whose visible regions between them cover every patch?

That is a classical problem, and knowing its name is worth more than solving it well. It is called set cover. Given a collection of sets and a target to cover, you choose as few of the sets as possible. It is known to be hard to solve exactly, and the useful part is that it has a simple approximate method that is provably close to the best possible. You take the candidate that covers the most patches not yet covered, and repeat until everything is covered. That is called the greedy method, and for set cover it is about as good as any simple method can be.

So the procedure for the new kind of request is short.

First, for every candidate camera position that survives the existing three tests, compute which unsearched patches it would see. Second, take the candidate that covers the most patches, and mark those as covered. Third, repeat until no patches remain, or until the budget of extra looks runs out. Whatever is still uncovered at the end is reported as unsearched, which is an honest statement about the run rather than a failure of it.

It is tempting to treat each patch separately by picking a patch, finding a viewpoint, moving the camera, and repeating. That is the loop the rest of this document describes, and for patches it is the wrong shape, for one reason that is worth seeing.

Patches are cheap to cover together and expensive to cover apart. A single well-chosen camera position often sees several patches at once, because the patches are wedges behind objects and one move can swing several wedges out of the way. A per-patch loop would pay for one arm movement per patch and get the same information for several times the cost.

That is the general lesson, and it applies whenever the thing being requested has extent rather than position. You should batch the requests before choosing the actions, and choose the action that serves the most requests. A loop that takes requests one at a time cannot see that two of them share an answer.

The cost is arithmetic and nothing else. Computing a candidate's visible region is the same wedge arithmetic already used twice, and the greedy choice is a count and a maximum over a short list.

What it is worth is worth being honest about, and the second solution measured it. In this cell the three survey stations already see every object between them, so the covering step usually finds nothing left to cover and costs no arm movements at all. Its value here is that it proves the survey was complete rather than assuming it. Its value changes the day somebody drops a station, moves the zone, or lets the objects stand closer. At that point the run starts asking for looks it can justify, instead of silently reporting fewer objects than are on the table.

<!-- section: how-the-concepts-fit-together | How the concepts fit together -->

The next part of the page explains how these concepts fit together. Put in order, they form a single loop, and this loop only ever runs on objects that the initial survey could not settle.

The section includes a flowchart showing this process. It distinguishes between what this new solution adds, the work the project already does, and the role of the motion planner. The diagram shows two distinct paths that lead to moving the robotic arm, and they arrive from different places. 

The first path starts from a place that nothing could have seen, and it never looks at an object at all. It computes what could not have been seen, and checks if there is any unsearched patch big enough to hold the smallest object. If there is, it chooses the fewest camera positions needed to cover those patches, and then moves the arm to take a picture. 

The second path starts from an object whose measurement cannot be trusted, and asks which direction to view it from. The flowchart shows a step that decides whether an object is doubtful, which is what keeps the arm from wandering around the table for no reason. An object is marked as doubtful if its fitted footprint comes out wider than any single object of this kind can possibly be, or if only one station ever saw it. Everything inside the allowed range is considered settled, and settled objects just report their mask, position, and width without ever entering the loop.

For objects that are doubtful, the system lists a fine ring of viewing directions around them. It then runs a series of tests to filter these directions. First, it drops any viewpoints that the arm cannot reach. Second, it drops any where a neighboring object would share the camera frame. If no viewpoints survive these tests, it reports that there is no viewpoint available and records which test each one failed. If there are surviving viewpoints, it sorts them with the best first, and asks the motion planner for a path. If the planner refuses every path, it again reports no viewpoint. But if a path is planned, it moves the arm, takes the picture, and measures again, looping back to check if the object is still doubtful.

Both the path for unseen places and the path for doubtful objects end at the exact same arm movement step. This shared destination is why they belong together in one single solution rather than in two.

<!-- section: the-loop-and-why-it-must-have-a-budget | The loop, and why it must have a budget -->

The next part of the page explains the loop, and why it must have a budget. 

This solution has a real feedback loop, which is what separates it from solutions one and two. It takes a measurement, works out what is still unclear, decides where it would have to look for that to become clear, goes and looks, and repeats.

A loop needs three things, and something with only two of them is not a loop. First, it needs something to be unsure about, which the width check from solution two provides. Second, it needs somewhere to go that might help, which the filtered candidate directions provide. If the filter returns nothing at all, then that fact is itself the answer. Finally, it needs a budget, because otherwise it never stops.

The budget is easier to reason about with the right unit, and the natural unit here is one station-equivalent. This means one plan, one move, one settle, and the pair of pictures the parallax needs. That is about what one more survey station costs, which saves us having to invent a number for what a movement costs. The survey from the top is three of these units, and each extra look is one more.

What a unit costs in seconds is the one thing here that has to be measured rather than argued about. A diagram of the budget shows why it does not much matter which of the plausible values the cost turns out to be. Whatever ceiling the whole perception step has to fit under, dividing that ceiling by the cost of a unit gives the number of units we can afford. Across the whole plausible range of unit costs, that number stays in the same neighbourhood.

When you set the options against it, the choice makes itself. The survey on its own fits comfortably, however expensive a unit turns out to be. The survey plus a small cap of extra looks is a little over twice the survey alone, and still fits at every plausible unit cost. A slightly larger cap fits only if a unit turns out to be cheap. Letting every object have its full allowance of looks breaks the ceiling at every unit cost, so it is never an option.

So the run-wide cap is set at the largest budget that fits whatever a unit turns out to cost. Going one step higher would be a bet on the timing measurement coming out at the cheap end, and there is a good reason not to place that bet. The objects that most want a second look are the crowded ones, and crowding is exactly what removes their viewpoints. Because of this, the extra budget is the part most likely to be spent on looks that get refused before the camera even moves.

Alongside the run-wide cap goes a per-object cap, so that one object cannot eat the whole budget by itself. Without it, one stubborn cluster pulls look after look and the run never ends. A cluster is usually stubborn because of where its neighbours are standing, which no number of looks will change.

The loop stops when nothing is doubtful, or when the budget is spent. Whatever is still doubtful then is reported as doubtful, and not guessed at. A report that says two objects could not be separated, and explains why, is a result. A report that guesses is a failure that looks like a result.

One measurement is worth recording from the very first version. You should count how many extra looks were spent, and how many of them changed the answer. A loop whose extra looks never change anything is a loop worth deleting, and you cannot know which kind you have built until you count.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page explains what happens when the glasses are completely hidden. The second difficulty is that an object can be absent altogether. This section works out what has to be true for a glass to contribute no pixels at all, how that differs between the two places the camera works from, and what this solution does about it. Everything is measured using the cell's own camera and the cell's own kind of glass, which is why it refers to a glass rather than an object.

Start with what this solution does about it, because the answer is smaller than the rest of the page might lead you to expect. 

The loop runs on doubtful objects. An object is doubtful because it was found and then failed a check, and being found is also what gives the ring of candidate directions something to be a ring around. A glass that produced no pixels was never found. So it fails no check, it is never marked doubtful, no ring is ever listed for it, and none of the three tests is ever asked about it. This solution cannot notice a completely hidden glass, and it cannot choose a viewpoint for one.

What it can act on is a place. The second difficulty ends with solution two turning the geometry of the objects that were found into the region of the table that could not have been seen, and reporting a large enough patch of that region as unsearched. What that leaves is a request this solution has to serve, and it is a different request from the one it was built for. A doubtful object has a position, so the viewpoints worth trying are the ones round it. An unsearched patch has no object in it at all, so what is wanted is any viewpoint from which the patch itself can be seen. Serving that request is what the earlier part of the page about covering the places nobody could see works through.

So the handling of a completely hidden glass is a handover in both directions. Noticing that one might be there belongs to solution two, whose arithmetic is the only thing in the project that can make a claim about a glass that produced no pixels. Going to look belongs here, through the covering step. And a patch that no reachable viewpoint covers is reported rather than guessed at, which is the same handover to problem three that the rest of this document ends in.

The two places the camera works from produce complete hiding in two quite different ways, and they want different cures. 

First is when the camera is looking straight down. This is the survey view, with the camera 450 millimetres above the table. The hiding follows from what that view does to a standing glass. 

The point on the table directly below the camera is called the nadir. A horizontal slice of a glass at height z is imaged as though that slice had been scaled outward from the nadir by a factor of the camera's height divided by that height minus z. The reason is that the slice is nearer the lens than the table is, so it covers more of the frame. At a camera height of 450 millimetres, a rim 225 millimetres up has a factor of 450 divided by 450 minus 225, which is two point zero. The rim circle appears at twice its real distance from the nadir and at twice its real radius. That outward stretch is called splay, and it runs along the radius from the nadir, because that is the direction the scaling moves things in.

Now take the merge and push it one step further. If a tall glass's outline reaches a short one it merges with it, which is loud, because the patch is then wider than any glass of the kind can be. But if the outline covers the short one entirely, the short glass contributes no pixels at all. What comes back is one patch of one entirely legal width, and nothing about it is wrong.

Three things have to be true together for that to happen. First, the two glasses have to stand close together. Second, they have to differ a lot in height, because splay is what carries the tall one's outline over the short one and a short glass splays hardly at all, which is also why the hidden one is always the shorter of the two. Finally, the pair has to lie along a radius from the nadir, because splay runs radially. The same two glasses lying across a radius do not hide each other at all, and that is the lever this solution pulls.

A diagram shows the same two glasses from each of the three survey stations. From the first nadir, the short glass is swallowed whole. From the second, it is a crescent. From the third, nearly all of it is visible. Every silhouette in that picture is a real projection of one of the project's own glass outlines through the cell's own camera, so the pixel counts on it are counted rather than asserted. The pair is a 225 millimetre glass 102 millimetres across the rim and a 95 millimetre glass 67 millimetres across, standing 150 millimetres apart, which is the closest the problem lets two glasses stand. With the tall one 190 millimetres out from the first station's nadir and the short one along the same radius beyond it, the short glass contributes none of the 3310 pixels it would contribute on its own. Slide the nadir 45 millimetres sideways and the first of its pixels comes back. From the next station's nadir, 92.6 millimetres along, 789 of them are in the picture. From the one after that, 3629 of 3642 are, and the patch is then wider than any glass of the kind can be, which is the ordinary merge, and the width check catches it.

The covering has a threshold as well as a direction, and the threshold is the awkward part of this mechanism. It begins only once the tall glass stands 176.6 millimetres out from the nadir. Nearer in than that, some part of the short glass always shows. And 176.6 millimetres out is further than the picture reaches. In the arrangement just described, the tall glass's rim images 234 pixels from the centre of a picture that ends 160 pixels out, and the short glass's rim images 265. Take both glasses to the ends of the kind's size range, the tallest and widest beside the shortest and narrowest, and the covering starts 150.5 millimetres out, where the rim still images 190 pixels from that same centre. So inside a single picture from this camera, one glass never covers another completely. At the distances the covering would need, what removes the short glass from the picture is the edge of the frame.

The zone makes that firmer. Even at the ends of the size range the short glass has to stand 300 millimetres out from the nadir, and no point in the zone lies more than 316 millimetres from any station's nadir, or more than 241 millimetres from the middle station's. So the arrangement is available only from the two outer stations, only at the far corner of the zone, and only with the biggest glass the kind allows standing beside the smallest.

None of that makes the mechanism idle, because what matters downstream is that the glass is absent from the picture, and the frame produces that just as thoroughly as the covering does. What it does settle is which cure is the right one. Both cases are cured by the same move, and it is a move this cell already makes before any of this runs, which is to look from another nadir. The three survey stations stand 92.6 millimetres apart so that their shared strips overlap by about half, and a consequence of that spacing is that a pair lying along a radius from one nadir lies across a radius from the next. So the answer from the top is the station layout, which this solution inherits rather than chooses, and then the covering step for whatever solution two still reports as unsearched. There is nothing here for a ring of candidate directions to do.

The second way hiding happens is when the camera is looking level. This is the measuring view, with the camera 120 millimetres above the table, standing 380 millimetres back from the glass it is measuring, pointing level at it. It is the pose the shape measurement needs, and it is the pose this solution flies to.

Hiding here needs no splay, and it needs no difference in height. The near glass's outline simply covers the far one's, which is what a line of sight does. The far glass is covered completely whether it stands 300 millimetres behind the near one or 800 millimetres behind it. More distance between the two makes the hiding more complete rather than less, because the far glass shrinks in the frame as it goes further away while the near one does not change at all. That is the sharpest difference from the view from above, where the whole mechanism turned on how far out from the nadir the pair stood.

The glass that loses pixels is the further one, whatever the two heights are. And because the near glass is the nearer of the two it is magnified in the picture, so even a near glass much shorter than the far one covers a useful part of it.

A second diagram shows a glass hidden behind another in the measuring view, the step round that brings it back, and what a short glass in front still costs a tall one behind. The first two pictures are the same two glasses as before, 300 millimetres apart, with the camera at its standoff from the near one. In line with the pair, the far glass contributes none of the 840 pixels it would contribute on its own. Step 6.0 degrees round the near glass and its first pixel appears. Step 19.8 degrees and the picture holds two patches, with the far glass whole. Standing further back helps at none of those angles, which is why the cure here is a step round rather than a step out.

The third picture is the same pair the other way about, with the 95 millimetre glass in front and the 225 millimetre glass 300 millimetres behind it. The far glass keeps 2145 of its 2901 pixels. The 756 it loses are all at the bottom and they include its base. Because the shape measurement turns rows into heights, the row where a glass meets the table is what fixes how far away it stands. A measurement of that far glass would be wrong about where it stands while most of it is in plain view.

This is the one place where this solution does act on complete hiding, and it acts by prevention rather than by cure. Test two asks whether another object would share the frame, judged as an angle at the camera. For this pair it refuses every direction up to 23.9 degrees, which is four degrees past the angle at which the two silhouettes actually come apart. So the filter throws away every viewpoint that would hide one known glass behind another, and it does it before the planner is asked about any of them.

That protection is worth stating precisely, because it is complete in one direction and empty in the other. For glasses the survey found, this solution will not create a hidden glass by flying somewhere careless. Against a glass the survey never found, it offers nothing at all, because a glass that is not in the belief about the table is not in the world the wedge test reasons about. When the arm goes to measure a doubtful glass and an unknown one is standing behind it, the picture that comes back looks exactly like a picture of one glass.

<!-- section: a-worked-example | A worked example -->

The next part of the page walks through a worked example. It follows two objects through the method, one that has a viewpoint and one that has none. It is described in terms of what happens rather than what is measured.

Five objects stand in the zone, arranged at the closest spacing the problem allows, so that the method is shown its hardest legal case rather than a comfortable one. Object A stands in the middle of the zone on the near side, which puts it in the middle of the arm's reach. Object B is between A and the far corner, comfortably out from the base. Object C is in the near corner, closest to the arm, near the inner edge of the reach. Object D is out along the far edge, away from B, and comfortably out. Finally, object E is in the far corner of the zone, near the outer edge of the reach. 

Objects A and B stand at the smallest legal gap, and so do B and E, while every other pair is a little further apart. Every footprint is taken at the widest the cell handles, because a wide footprint casts a wider wedge of blocked directions, which again is the hardest case.

First, consider object A, which has a viewpoint. A diagram shows a plan view of the three tests, featuring a ring of every direction around A. Each direction is a place the camera could stand at the standoff distance, and they are coloured by what they fail. Grey marks the directions where the standing place falls outside the arm's comfortable reach. Red marks the directions where another object would share the picture. Green marks the directions that pass both. The crosses, circles and stars on the ring are the directions the cell actually tries on its coarse ring.

Some candidates fail on reach alone. The direction that would put the camera between A and the arm's own base is the obvious casualty, because it lands close in to the base, well inside the inner edge of the comfortable band, where the arm would have to fold over itself. At the other extreme, the directions that would put the camera on the far side of A, out past B, land beyond the outer edge, where the arm is stretched straight and has nothing left over to point the wrist with. None of these ever reach the line-of-sight test, which is exactly the point of the ordering. The cheapest test spends the least and removes a good share of the candidates.

Most of what remains is blocked. Standing one way, both B and C land in the frame. Swing round and it is B and E instead. Swing further and D appears. Further still and C is back. Each neighbour is casting its own wedge, and the wedges overlap.

A couple of candidates survive. They are sorted by how far the arm has to turn away from the line back to its own base, because that line is where the arm has the most reach in hand, so the planner is asked about the better of the two first. If it plans, the arm flies there, takes the picture, and we are done. If it refuses, say because an elbow would sweep through B, the planner is asked about the other one. If that fails too, then A has no viewpoint, and A is reported rather than guessed at.

Following the same arithmetic through for all five objects gives a clear pattern. There is a long list of candidates, roughly half are removed by reach, most of the rest are removed by line of sight, and only a few are left for the planner. The planner is the expensive test, and it is asked the fewest questions.

One detail is worth noticing, because it is the first hint of the real problem. The direction exactly square to the line joining A and B, which is the one you would reach for by hand because it looks at A with B safely off to the side, is not one of the directions the coarse ring offers. The nearest one it does offer is some way off it, and happens to work this time. So it is the ring, and not the geometry, that decided the outcome.

Next, consider object E, which has no usable viewpoint. Another diagram shows object E in the left panel. Some of its directions fall outside the arm's reach, the rest are blocked by neighbours, and none survives. So on the coarse ring the cell uses today, E is handed to problem three.

But look at the ring itself. There is a stretch of green on it, which is a narrow arc of directions from which E could be seen perfectly well. The coarse ring simply has no spoke pointing into that arc, and steps straight over it. Object E is stranded by the ring, and not by the geometry.

That is not an isolated accident, and it is the important result on this page. Measure the clear arc for each of the five objects and the arcs vary enormously. One of them is so wide that any ring would hit it, while others are only a few degrees across. A coarse ring is guaranteed to find the wide arc and finds the narrow ones only by luck, depending on where its spokes happen to fall.

The fix is free, and it is the second benefit of bounding before scoring. Because the filter is pure arithmetic, the ring can be made as fine as you like, with dozens of directions instead of a handful, and the planner still only ever sees the few survivors.

The right panel of the diagram counts what that buys, over hundreds of arrangements of four to six objects drawn in the zone under the problem's own spacing rule. Refining the ring from coarse to fine cuts the share of objects with no usable viewpoint down to a small fraction of what it was. And the narrower the footprints, the more completely the problem disappears, because a slim object casts a narrow wedge.

Two things follow from that. First, most of the loss is the ring, and refining the ring costs nothing but arithmetic, which makes it the single cheapest improvement available here and the first thing to do.

Second, it never reaches zero. In the middle panel, object S stands well out from the base with four neighbours round it, and its ring has no clear direction at all, at any fineness whatsoever. No ring helps, because the wedges its neighbours cast cover the whole circle between them. Something has to move.

That is the handover to problem three, and it is a result rather than an error. The right output is the object, the reason, and a stop, and never an attempt made anyway. This is the rule the whole project runs on. A refused object is a result, and a fallback that has the arm try regardless is how neighbours get knocked over.

<!-- section: where-the-idea-comes-from | Where the idea comes from -->

The next part of the page explains where the idea comes from. This solution is an example of a named research programme rather than a trick. The idea that a camera should be moved on purpose rather than read passively has forty years of literature behind it, and there are five ideas that make up the standard vocabulary.

First is active perception, which means treating the sensor's pose as something to choose. Classical vision takes a picture as given and asks what can be recovered from it. Active perception and active vision, concepts introduced in nineteen eighty-eight, turn that round, so that the observer controls the sensor and the question becomes, where should I look next? Problems that cannot be answered from one viewpoint are often easy from two. It is used for robots with the sensor on a movable body, such as arms, mobile bases, drones and pan-tilt heads, and for inspection, where an object has to be checked from several sides anyway. It is rarely right for fixed installations where moving is impossible, or where moving is slow compared with the value of the answer, such as a conveyor line running at speed or a static security camera.

Second is next-best-view planning, which means scoring viewpoints before visiting them. You list candidate poses, predict what each would reveal, take the best one, and repeat until the gain stops being worth the movement. The first version of this was published by Connolly in nineteen eighty-five, and the field has run on variations of it since. It is used for three-dimensional reconstruction and inspection, where coverage is the goal and the object is unknown, such as scanning a part, mapping a room, or exploring with a drone. It is rarely right for scenes small and known enough that a fixed sweep covers everything anyway, because planning a viewpoint costs thought while visiting three fixed ones may cost less. This cell sits on that line, which is why the score here is a printed rule rather than a calculation of information.

Third is occupancy mapping and ray casting, which is a way of reasoning about what is hidden. You divide space into cells, mark each one free, occupied or unknown, and trace rays from a candidate camera to see which unknown cells it would resolve. OctoMap, published by Hornung and colleagues in twenty thirteen, is the standard implementation, using a tree structure that keeps the memory use tolerable. It is used for mobile robots and drones, where finding out what you have not seen yet is the whole task, and it is the layer underneath most next-best-view scoring. It is rarely right for a small scene of a few known objects, where a handful of geometric tests answer the same question exactly and far more cheaply. A grid fine enough to be useful over this cell's zone runs to millions of cells, all to decide what one wedge test per neighbour already settles exactly.

Fourth is set cover, which means choosing the fewest actions that between them do everything. This is the idea the covering section rests on, and it is worth knowing by name because it turns up constantly once you start batching requests. The problem is stated like this. You have a target made of many pieces, and a collection of actions where each action covers some of the pieces, and you want the fewest actions that between them cover every piece. That is set cover. Here the pieces are the unsearched patches and the actions are the camera positions, but the same shape appears in choosing which tests to run, which sensors to install, and which items to stock. 

Two facts about set cover are the useful ones. First, it is hard to solve exactly, so nobody should spend effort trying on a problem this small. Second, the obvious greedy method, which is to repeatedly take whatever covers the most pieces still uncovered, is provably close to the best possible. This is an unusually comfortable position to be in, because the easy method is also the right one. It is used for facility placement, test selection, sensor placement and camera placement, which is this case exactly. It is rarely right when the actions interact, meaning when taking one changes what another would cover, because then the sets are not fixed and the greedy argument stops applying. Here they do not interact, because the objects do not move between looks.

Finally, there is bounding a search by feasibility before scoring it. This last idea is not a vision method at all but a structural pattern, and it is the one most often got wrong. You must put the hard constraints inside the search rather than filtering afterwards. Listing viewpoints, ranking them by how much they would reveal, and only then discovering that the arm cannot reach them is how a cell becomes slow and unreliable with nothing ever erroring.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page covers where this method is strong and where it breaks. 

The strengths of this method follow from the fact that moving the camera is cheap and safe. It fixes merges that were caused by where the camera happened to be standing, and changing where it stands costs seconds while carrying no risk at all to the glassware. It can be audited completely, because a refusal names which of the three tests each candidate direction failed. This means "no viewpoint" is a statement you can check rather than a shrug. And it costs nothing when it is not needed, because settled objects never enter the loop, so a scene with no doubt in it runs exactly as it did before.

It has also become the only place in the project that can act on a place rather than an object, which is what the missing-object difficulty requires. That is worth listing as a strength rather than as an extra job, because the alternative is a run that quietly reports fewer objects than are on the table.

The weaknesses divide into what it spends, what it assumes, and where it stops.

What it spends is arm time, which is the cell's dearest resource. If you give every object its full allowance of looks, the extra travel dwarfs the original survey, which is why the budget exists. It is also heavier than it strictly needs to be, since the filter on its own gets most of the benefit, and the loop around it wants a better measure of doubt than a width check.

What it assumes is that the survey's footprints are right, and this is the subtlest weakness on the page. The line-of-sight test predicts what is hidden from the survey's own footprint circles. So if the survey measured a footprint badly, then the prediction is wrong, and the arm is confidently sent to a viewpoint that turns out not to be clear after all.

The covering step inherits exactly the same weakness, and one worse than it. It works out the unsearched patches from the objects that were found, so an object hidden behind an object that was itself hidden lies outside its reasoning altogether. In this cell that does not arise, because no object is hidden from every station, but it is the thing to watch the day the station layout changes.

It also assumes depth readings work. Real glassware reads badly on a depth camera, so with no depth there is no belief about the table for any of this to reason about.

Where it stops is at three places. First, without the per-object cap it thrashes on one stubborn object. Second, the planner can refuse every survivor, in which case all the cheap arithmetic was for nothing. Finally, some objects have no clear direction at any ring fineness at all, which is problem three's business and a result rather than an error.

This method is the right choice when a viewpoint is cheap to score and expensive to visit, and when the doubt has a name you can state. Both of those stop being true at problem four, where a score based on unknown volume starts to earn its weight. The order to build it in is the filter first, with a fine ring, because that is a page of arithmetic and it captures most of the benefit, and then the loop afterwards.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page explains where this approach sits among the other solutions. It answers different difficulties compared to the method of clustering on the table, so the two are partners rather than rivals. Clustering determines which pixels belong to which object and where each one stands, and it works out which places it could not have seen. Moving the camera supplies the two things clustering cannot get for itself: a better picture of a doubtful object, and a view of a place nothing has looked at.

Those two strengths together are why the recommended answer to this problem is a combination of the methods, rather than a choice between them. Clustering alone is confidently wrong when it comes to a hidden object. This solution alone has nothing to reason from, because it needs the footprints and heights that clustering produces. Neither is a solution to problem two on its own.

This approach is also the baseline underneath the later solutions that replace only its score. Solutions four and six keep this exact structure. They generate candidates, filter them with arithmetic, and then order what survives. They change only how the ordering is decided. So, understanding this method is what makes the explanations for those two later solutions short.
