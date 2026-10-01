<!-- section: introduction | Introduction -->

The problem: many glasses, seen from few viewpoints. 

Several glasses stand on a table. They are all the same kind, and the system knows what kind they are. The robotic arm photographs them, and its task is to work out exactly which pixels belong to which glass. This is the entire problem. The arm does not pick anything up, and it does not measure a shape. The process simply ends with a set of pixels for each glass, along with a specific place on the table for each one. 

This page explains the three difficulties that make this task much harder than photographing just a single glass. You will see why the hardest of these three challenges is not that two glasses might run together in a picture, but rather that one of the glasses can be absent from the picture altogether.

<!-- section: what-is-on-the-table | What is on the table -->

The next part of the page describes what is on the table. There are four to six glasses, all of one kind, drawn at proportions picked at random from within that kind's range. They stand upright and are opaque. The drying rack is in its usual place, and nothing else changes from the first problem. It uses the same cell, the same camera, and the same table.

Two properties of this arrangement do the work in this problem, and both are deliberate. 

First, the kind of glass is tapered, and its range of sizes is wide. Tapered means the rim is wider than the base, so the glass opens outwards as it rises. The range runs from a small tapered glass at one end to a large one at the other, and the tall end is more than twice the height of the short end. This is the widest range of any kind of glass in this cell, and the next section will explain what that width causes.

Second, the glasses stand apart. There is a guaranteed smallest gap between the centres of any two glasses. This gap is wide enough that even the two widest glasses of the kind leave a clear strip of bare table between their rims, meaning no two glasses ever touch. Separating glasses that touch is covered later, in the third problem.

<!-- section: what-is-asked-for | What is asked for -->

The next part of the page outlines what the system is asked to produce. For each glass on the table, it needs to output three things. First, a mask, which means identifying exactly which pixels in which picture belong to that specific glass and not to another. Second, a position on the table, measured from the base of the robotic arm. And third, a rough width of the glass's footprint.

In addition to those three things, there is something that problem one never had to produce. The system must provide an honest statement of which glasses it could not separate, and why. If the arm cannot tell a pair of glasses apart, that is considered a valid result rather than a failure, and this result becomes the input for problem three.

Finally, there is a fourth overall requirement for this problem, which follows from a difficulty that is explained further down the page. The system must provide an honest statement of where it could not have seen a glass at all. This is an important distinction, because stating where the system is blind is not the same thing as merely listing the glasses it successfully found.

<!-- section: the-three-difficulties | The three difficulties -->

The next part of the page covers the three difficulties of this problem. They are ordered here by how dangerous they are, which is not the order in which they are easiest to notice.

The first and worst difficulty is that a glass can be missing from a picture altogether. This is caused by the wide size range of the glasses, and it is dangerous because nothing in the picture says it happened. 

To see why it happens, start with what a camera looking straight down does to a tall object. The table is the furthest thing from the lens, and a glass's rim is the nearest, because the rim has climbed most of the way from the table towards the camera. Nearer things are drawn larger and further out from the middle of the picture. So a glass's outline is not drawn directly over the glass. Instead, it leans outwards, away from the point directly below the camera, and the taller the glass, the further out it is thrown. This project calls that effect splay.

Now put a wide range of heights inside one kind of glass. A tall glass's outline is thrown a long way outwards. A short glass standing beyond it is thrown hardly at all. Because of this, the tall glass's outline can sweep outwards over the short one and cover it completely. 

When that happens, the picture looks perfectly innocent. It holds one glass of an entirely legal width, with a clean outline, and nothing about it is wrong. The survey simply returns fewer glasses than are actually standing on the table.

Two things make this worse than it first sounds. 

First, every check in this project is a check on something that was actually found. A width can be compared against the range the kind allows. A fitted circle has a residual error. A group can be asked how many camera stations saw it. None of those exist for a glass that produced no pixels, so none of them fires.

Second, the same cause also pushes glasses out of the frame. Splay throws a tall glass outwards, and past a certain distance from the middle of the picture, it is thrown past the edge. So a glass can be absent because something covered it, or because splay carried it out of frame, and usually it is because of a mixture of the two. The outcome is identical, which means the honest question is not whether it was hidden, but whether the camera could have seen it at all.

That question has a surprisingly good answer, and it is the reason this difficulty is worth having in the problem. Splay is exact arithmetic, and the glasses that were found have known footprints and known heights. So the region of the table that could not have been seen from a given camera position is computable. An unknowable question about whether something is missing becomes a checkable one, asking where something could have been hiding.

The second difficulty is that glasses merge in the picture even when they are apart on the table. A diagram here illustrates how overlapping in the picture does not mean the glasses are touching in reality. 

In the first problem, the system finds a glass by taking the pixels that stand above the table top and grouping the ones that touch. With one glass, that is enough. With several, it is not, because two glasses that are nowhere near each other can still land on top of each other in a picture if the camera happens to be in line with both. The grouping step then returns one blob, and one blob means one glass to everything downstream.

The wide size range makes this more common than it was, for the same reason as before. A tall glass's outline is thrown outwards far enough to reach a shorter one, so the two need not be anywhere near each other for their outlines to touch.

This failure is at least loud. The blob is wider than any glass of the kind can be, so something can notice. But noticing is not separating, and the projection has thrown away the information needed to separate them, which is knowing which pixels were near the camera and which were far. The fix is not a better grouping rule. It is to stop grouping in the picture.

The third and final difficulty is that the camera can no longer stand wherever it likes. A diagram shows the limited areas where the camera is allowed to stand once there are several glasses on the table. This difficulty is easy to miss when reading the first problem, because the first problem simply does not have it.

The first problem measures a glass by standing the camera back from it, looking level, and photographing its outline. It tries several directions around the glass and takes the first one the arm can reach. With one glass on a bare table, several always work.

With five glasses, each direction has to clear three separate things at once. First, there is the line of sight, because another glass behind the target lands in the same picture and the two then measure as one object. Second, there is the arm, because the camera is on the wrist. Putting it somewhere means putting the whole arm somewhere, and the path there may cross a glass that is in the way. Finally, there is the reach, because standing well back from a glass already near the edge of the working area puts the camera outside it.

Each of those alone is survivable. Together they can leave a glass with no usable viewpoint at all, which is not a failure of perception but a physical fact about where the glasses are standing. The only way out of it is to move something.

<!-- section: what-the-difficulties-do-to-the-solutions | What the difficulties do to the solutions -->

The next part of the page looks at what these difficulties do to the solutions. 

The three difficulties are not independent, and the connection between them is the reason this problem is worth solving carefully. The second difficulty can be answered inside one picture, or at least inside one station's pair of pictures, because the information needed is still there in the depth readings. The first and third cannot. A glass that produced no pixels cannot be recovered by any amount of work on the pixels that exist, and a glass with no clear viewpoint cannot be measured from the viewpoints available.

So the answer to this problem is not one method. It is a combination. It requires a way to place what was seen, a way to work out what could not have been seen, and a way to go and look again. Any solution that supplies only the first of those has answered the easy difficulty.

<!-- section: what-is-deliberately-not-in-this-problem | What is deliberately not in this problem -->

The next part of the page outlines what is deliberately not included in this problem. 

First, the problem does not involve identifying the type of glass. The glasses are all of the same kind, and that kind is already known. Identifying different kinds of glasses is covered later, in problem four.

Second, it does not involve measuring a shape. Measuring a shape requires a view from the side, and figuring out whether that side view is even available is exactly what this current problem is trying to solve. Once this problem determines which glasses can be seen from which viewpoints, the actual measuring is handled exactly as it was in problem one.

Third, there is no physical interaction. The problem does not involve grasping, lifting, or placing the glasses in a rack.

Finally, the problem does not involve moving anything. If two glasses cannot be visually separated from any viewpoint the camera can reach, the system simply reports that fact and stops. The task of actually moving the glasses apart is left for problem three.

<!-- section: what-done-means | What "done" means -->

The next part of the page explains what it means for a run to be considered done. A run is done when every glass on the table has a mask, a position, and a rough width. It is also done when every glass that could not be separated from its neighbour is listed along with the reason why. Finally, every region of the table that could not have been seen must be listed as unsearched, rather than quietly treated as empty.

Once a run is done, it is scored against the simulator's own record of what it spawned. The report is allowed to read this record, but the arm is not. There are several numbers worth watching in this score. First, look at how many glasses were found compared to how many were put out. Second, how many were missed, meaning they were on the table but in no report at all. Third, how many were merged, where two real glasses are reported as one. Fourth, how many were split, where one real glass is reported as two. You also need to watch how far the reported position of each found glass is from its true position. Next, watch how many glasses had no usable viewpoint, which serves as the handover to problem three. Finally, look at how much of the zone was reported as unsearched, and whether anything was actually standing there.

The number to watch hardest is the count of missed glasses, which has taken that top spot from merged glasses. A split glass looks wrong immediately, because both halves are too small to be glasses. A merged pair looks like one large glass, which is worse, because everything downstream believes it. But a missed glass leaves no trace at all. There is no bad number to find, no failed check, and nothing in the run to read. The only defence against a missed glass is to have worked out, in advance, where a glass could have been hiding.

<!-- section: a-note-on-the-cells-own-settings | A note on the cell's own settings -->

The next part of the page adds a brief note on the cell's own settings. The range of sizes and the guaranteed gap described here are the ones the cell actually uses. Both of these, along with the file that holds them, are recorded on the page about the cell. The tapered kind of glass is the widest of the four kinds on purpose, because a narrow range of sizes cannot produce the first difficulty at all.

The short end of that size range is set by two parts of the cell that have nothing to do with perception. First, if a glass is any shorter, it will no longer clear a rack peg when it is stood mouth down. Second, the gripper can no longer close on it at the specific spot where the rule for this kind of glass says to hold it. Because of this, the hardest arrangement this problem can be given is exactly the hardest one that the rest of the robotic arm can still work with, which is the right place for the limit to come from.

<!-- section: how-it-would-be-solved | How it would be solved -->

The next part of the page addresses how this problem would be solved. A full explanation is provided on the separate page that gives an overview of the solutions.
