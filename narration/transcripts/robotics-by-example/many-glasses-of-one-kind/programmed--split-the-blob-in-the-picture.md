<!-- section: lead | Solution 1 — split the blob in the picture -->

Solution one: split the blob in the picture. 

This is a programmed solution that relies on the picture the camera has already taken. The main idea is that when one group of pixels is too wide to be a single glass, the software simply cuts it into two.

Keep in mind that the physical setup is described just once, on the earlier page about the cell. That page covers the layout, the two positions the camera works from—both from the top and from the side—along with all four sensors and the terminology this project uses for them. Because of that, everything that follows here will focus only on what is specific to this particular solution.

<!-- section: introduction | Introduction -->

The introduction to this page explains one way to tell two glasses apart after the camera has already photographed them as a single shape. The problem exists because a camera flattens the world, so two glasses that stand well apart on the table can still overlap in the photograph. When that happens, the step that groups touching pixels together then reports them as one object. By the end of this document you will understand why that happens, why it happens from one camera position but never from the other, and how the bottom edge of a shape in a photograph can be read as a measurement of distance. That last idea is the whole method, and it is older than computer vision.

<!-- section: the-problem-this-solves | The problem this solves -->

The next part of the page explains the problem this solves. Before describing the problem itself, we need to define two terms that will be used again and again.

The first term is mask. A mask is a picture the same size as the camera's picture, in which every pixel holds only a yes or a no. Here, yes means that the robot believes this pixel is part of a glass, and no means that it does not. The earlier work in this project already produces this mask, so we can take it as given.

The second term is connected components. This is a standard step that reads the mask and finds groups of yes pixels that touch each other. Each of these groups is called a patch. The important thing about connected components is how little it asks. It answers only the question of whether these pixels are joined to each other. It never asks how large a group is, or whether a group is the right size to be one object.

For a single glass on an empty table, that one question is enough, because whatever is joined together is the glass. For several glasses, however, it is no longer enough. Two glasses can stand far apart on the table and still touch each other in the photograph. This happens when one of them hides part of the other, and it happens for a reason that has nothing to do with how far apart they really are.

So, the mask is correct and the grouping step is correct, but the answer is still wrong. This is worth stating plainly, because it tells us where to look for a fix. We do not need a better mask, and we do not need a better grouping rule. We need a way to notice that one patch holds two glasses, and a way to decide where to cut it.

<!-- section: where-the-problem-happens-and-where-it-does-not | Where the problem happens, and where it does not -->

The next part of the page explains where the problem happens, and where it does not. The question is when two glasses overlap in a photograph, and the first answer most people give is wrong. It matters a great deal, because the answer tells us which camera position this method belongs to.

A diagram shows the camera in this cell working from two quite different positions, which this project names "from the top" and "from the side". From the top, the arm lifts the camera high above the table and points it straight down at the glasses. From the side, the arm brings the camera down low, stands it back from one glass, and points it level, straight at that glass rather than down at the table.

There is a tempting argument that says overlap cannot happen when the camera looks straight down, and it is worth following, because seeing where it breaks is the quickest way into this problem. The argument goes like this. Two solid glasses cannot pass through each other, and the problem guarantees a smallest gap between their centres. Because of this, there is always a strip of bare table between them, and seen from straight above, that strip must be visible.

The hidden assumption in that argument is that the glasses are all of a similar size. Inside this kind they are not, and the next diagram shows what that does. 

From the top, a glass's outline is not drawn over the glass. The rim is nearer the lens than the table is, so it is drawn larger and further out from the middle of the picture, and the outline leans outwards. This project calls that splay, and the crucial property is that the taller the glass, the further out it is thrown.

So, if you put a tall glass near the middle of the picture and a short one beyond it, the tall one's outline sweeps outwards, while the short one's barely moves. The sweep can reach the short glass and pass over it, and it can pass over all of it. What that does to this method is different in kind from a merge, and it is covered later on this page in the part about when the glasses are completely hidden.

Another diagram shows a second effect with the same cause, and in practice the two arrive together. The camera sees through a cone spreading out from the lens, so the higher up you measure that cone, the narrower the slice of the world it covers. Splay throws a tall glass outwards, and past a certain distance from the middle of the picture it is thrown clean past the edge of the frame. So a glass can be absent because something covered it, or because splay carried it out of frame, and usually it is because of a little of both.

Either way, the honest question is not whether it was hidden, but whether you could have seen it at all. Answering that question is the business of the second solution, which is on another page, because it needs the positions and heights of the glasses that were actually found.

What this page has to take from it is narrower, and it changes one step of the method. A patch of legal width can still hold two glasses. Because of this, the width check cannot be the only thing that starts the test below.

From the side, everything changes, because now a glass standing behind another glass really is behind it in the plain everyday sense. The near one hides the far one, exactly as a person standing in front of you hides someone behind them. The strip of bare table that kept the two apart from above runs away from the camera, so it cannot be seen at all.

This is not a rare corner case. Of all the pairs we deliberately stood in line with the camera, the large majority came back as a single patch.

The wide range of sizes inside one kind matters here as well, and in the same two ways. A large glass standing in front of a small one hides far more of it than a glass of its own size would, so more pairs merge. And a glass standing in line with the camera can be covered completely, which is a different case again and is dealt with later on this page.

So the rest of this document is about the camera at the side, and about nothing else.

Before we go on, one tempting picture has to be put aside, because a lot of reasoning about this problem is built on it. The picture shows two round footprints overlapping each other. No camera in this cell ever sees such a thing.

A final diagram illustrates why a standing glass is not a circle. A glass is a circle only when you look straight at the ring it makes on the table, and no camera here ever gets that view. From the top, the rim is already wider than the base, and the rim is also nearer the lens, because it has climbed most of the way up towards the camera. Both of those effects make the rim look larger, and being nearer also throws it further out from the middle of the picture. So the shape that comes back is neither a circle nor even centred on the glass. It looks more like a teardrop, leaning away from the point directly under the camera, and a glass with a small base can come back several times wider than that base. From the side, the shape is simply the glass's side view, which is tall and narrower at the bottom.

Neither of those shapes is a circle the size of the base. Any method that assumes a circle is therefore answering some other question, and not this one.

<!-- section: the-main-idea-the-bottom-edge-is-a-measurement-of-distance | The main idea: the bottom edge is a measurement of distance -->

The next part of the page explains the main idea, which is that the bottom edge is a measurement of distance. The whole method rests on this idea, and it comes from one choice about how the camera is held. 

The camera at the side is held level, which means that it looks straight ahead rather than tilted down at the table. Holding it level puts a horizon in the picture. The horizon is the row where the table would appear to vanish if the table went on for ever. It is not a physical thing in the room, and nothing in the cell is placed there. It is purely a consequence of the camera being level, and because of that it sits exactly halfway up the picture, always.

Every glass base is then drawn somewhere below that horizon row. This is the key step, so it is worth saying slowly. How far below the horizon a base is drawn depends on one thing only, which is how far away that glass is. Nothing else enters into it. 

A diagram on the page illustrates this, showing that as glasses are placed further away, their bases sit higher up in the picture. You already know this effect from photographs of roads. The near edge of a road sits low in the picture and the far edge sits higher up, closer to the horizon, even though both edges are on the same flat ground. A glass base behaves in exactly the same way, because it is also on that same flat ground.

The relationship itself is one line of arithmetic, and it is easier to remember as a shape than as a formula. The gap between a base and the horizon goes as one divided by the distance. A curve of that shape is steep close up and nearly flat far away, which has two consequences worth understanding.

The first consequence is good news. Near the camera, moving a glass back by a small amount shifts its base a long way up the picture, so the method is at its sharpest exactly where the glasses this cell cares about are standing. The second consequence sounds like bad news but is not. Far from the camera, the same move shifts the base hardly at all, so the method goes blunt in the distance. That does not matter here, because nothing that far away is going to be picked up.

There is a second lesson in that same picture, and it explains why this method looks only at the bottom of a shape. If you move a glass further away, its base climbs noticeably, but its rim barely moves. The reason is that the camera is low, at roughly the height of a glass's rim. Because of this, a rim already sits almost on the horizon, and no change in its distance moves it much further. So the top of a shape tells us almost nothing about distance, while the bottom tells us everything. That is why the whole method reads the bottom edge.

<!-- section: the-four-ideas-that-make-the-method | The four ideas that make the method -->

The next part of the page explains the four ideas that make the method. We now have the main idea, so we can put the method together. It is four smaller ideas used in order, and each one depends on the one before it.

The first idea is the cheapest, and its only job is to notice trouble. A diagram here shows the merged blob of the two glasses, and the measurements that flag it as being too wide. Because this problem tells us which kind of glass is on the table, we know before the run even starts the widest that any single glass of that kind can possibly be. That is a limit on a kind, and not the size of any particular glass, which is why the project is allowed to hold it. Turning that limit into a width in pixels needs one other thing, which is how much of the world one pixel covers at the glass, and the arm knows that because it chose how far back to stand.

So the check is simple. If a patch is wider than the widest single glass of this kind could ever draw, then the patch holds more than one thing. Our merged pair is comfortably past that limit, so it is flagged.

But this check must not be used as the gate. Because the range of sizes inside one kind is wide, a large glass standing in front of a small one produces a patch of the large glass's width, which is entirely legal. The width check says nothing, and the two glasses are still there.

So the width check has exactly one job, which is to notice trouble, and it must not be given the other one of deciding whether to start the test. The bottom-edge test in the next three ideas now runs on every patch, not only on the over-wide ones. That costs almost nothing, because it is one pass along the bottom of a shape, and the two checks then fail independently, which is what you want from two checks. A patch can be flagged by being too wide, or by holding two places of contact, or by both.

One detail here is easy to mistake for a fudge, so it is worth explaining. The limit has a small amount of slack added to it, of a pixel or two. The reason is that the edge of any shape drawn on a grid of square pixels always rounds outward, so every real outline comes back slightly wider than the arithmetic predicts. The slack is therefore correcting a known effect rather than hiding an unknown one. Remove it, and the method flags every single glass it ever sees, because every single glass is a little wider than its own arithmetic says.

Notice what this first idea can and cannot do. It can tell us that a patch is wrong. It cannot tell us where to cut it, because a width is one number and a cut needs a position.

The second idea puts the main idea to work. For every column of the patch that holds any yes pixel, we take the lowest yes pixel in that column. Doing that for every column traces out the bottom edge of the shape.

Because of the horizon relationship, that bottom edge is no longer just a shape. Every point along it is a distance, read off the picture.

The third idea is the one that separates the glasses, and it follows from a physical fact rather than from image processing.

Walk along the bottom edge and collect the longest stretches where the row stays the same, give or take a pixel. Each such flat stretch is a place where something is standing on the table, because contact with a flat table at a fixed distance draws a flat line at a fixed height in the picture. A diagram shows the test itself, highlighting these flat runs of contact along the bottom edge of the shape.

Short stretches are thrown away. They are the steep sides of a glass, where the lowest yes pixel is really a piece of the side wall rather than the place where the glass meets the table, and keeping them would mean mistaking a wall for contact.

The fourth idea is the answer. If two surviving stretches sit far enough apart up the picture, there are two glasses, and we cut between them. We also get something for free that the method was not designed to give, which is the order. The lower stretch is the nearer glass, because lower means closer to the camera.

The remaining question is what far enough apart means, and the answer is the same shape of answer that appears in several of these solutions. The threshold is not tuned by trying values until the tests pass. It is pinned between two limits that are both known before the run starts, and it is placed in the gap between them. This is the same reasoning an engineer uses when choosing a measurement tolerance, where the tolerance has to be larger than the instrument's noise and smaller than the smallest real difference that must not be missed.

The upper limit is the smallest real difference the method must never miss. This problem promises a smallest gap between the centres of two glasses, and the horizon relationship turns that gap into a difference in rows. The threshold must sit below that, or a legal pair would be missed.

The lower limit is noise. An edge drawn on a grid of square pixels wobbles by about a pixel from column to column, so two stretches differing by only that much are not two glasses but one glass and some rounding. The threshold must sit above that.

The useful part is that these two limits are far apart, because the real difference is many times the noise. So the threshold is not a delicate knob. It sits comfortably in the middle of a wide window, and both ends of that window are reported when the method runs, so a wrong answer can be read and understood rather than guessed at.

Put in order, the four ideas make one flow of decisions, which the section illustrates with a flowchart. It starts with the mask that shows which pixels look like glass, and groups the pixels that touch. Then it checks if the patch is wider than one glass of this kind can be. If no, it concludes there is one glass, and there is nothing to do. If yes, it reads the bottom edge by finding the lowest lit pixel in every column. Next, it keeps the flat stretches, which are places of contact. Then it asks if two stretches are far enough apart. If yes, it cuts between them, and the lower one is the nearer glass. This outputs two masks, and which of them is nearer. If no, it says it cannot tell because the far base is hidden, and hands it to solution three, which moves the camera.

Finally, the chart uses colors to show where these steps come from. Green marks the parts this solution adds, blue marks work the project already does, and grey marks a standard library step.

<!-- section: why-we-read-flat-stretches-and-not-steps | Why we read flat stretches, and not steps -->

The next part of the page explains why we read flat stretches, and not steps. There is an obvious alternative to the third idea, and we tried it first. It failed, and understanding why it failed explains why the method is built the way it is.

The obvious test asks whether the bottom edge has a step in it. If the edge jumps up suddenly, call that jump the place where the near glass ends and the far one begins. On merged pairs this works nearly every time, which is exactly why it is tempting.

The diagram shows a control case for this, running the same test on one glass standing entirely alone. Take a wine glass, whose bowl is wider than its foot, so the bowl hangs out over the foot on both sides. In the columns above the foot, the lowest yes pixel is the foot, down near the table. In the columns just outside the foot, the lowest yes pixel is the underside of the bowl, which is much higher up. So the bottom edge jumps, and it jumps by far more than two real glasses would ever differ by, and there is only one glass there. Counting steps therefore cuts most of the single glasses it is shown into two.

Counting flat stretches does not have this problem, and the reason is physical rather than statistical. A glass may be any shape it likes, but it rests on the table in exactly one place, so its bottom edge holds exactly one flat stretch. We tried this on single glasses of all four kinds at a range of distances, and it cut none of them.

This asymmetry is deliberate, and it is the most important design decision on this page. If the method cuts one glass into two, we get two wrong answers in place of one right one, and nobody later in the chain can tell that anything went wrong. If instead the method says it cannot tell, the next step knows there is a problem and can go and take another picture. So the method is built to refuse rather than to guess.

<!-- section: what-comes-out-and-what-does-not | What comes out, and what does not -->

The next part of the page explains what comes out of this method, and what does not. 

When the method succeeds, it hands back two masks cut out of the one picture, together with information about which of the two is nearer. When the bottom edge holds one flat stretch and the patch is no wider than this kind allows, it hands back the single mask untouched. When the patch is too wide but only one flat stretch can be found, it hands back a refusal.

It is equally important to be clear about what does not come out, because believing otherwise is how a wrong answer travels downstream. No position on the table comes out of this method. Both pieces are still flat shapes inside a picture, and a shape in a picture does not sit where its glass really stands.

The two masks go on to the step that measures each glass's shape from the side. The refusal goes into the run report and to the solution that moves the camera.

The text then explains why the refusal is actually a useful output. This method has no feedback loop at all. It reads one picture, and it either answers or refuses. It cannot ask for another photograph, and it remembers nothing between pictures.

What it does give is a clean handover, because its refusal is specific rather than vague. There are exactly four outcomes. 

First, finding two stretches far enough apart means there are two glasses, and the method tells us which of them is nearer. 

Second, finding one stretch in a patch no wider than this kind allows means there is one glass that needs nothing done to it, with one caveat added below. 

Third, finding one stretch in a patch that is too wide means something quite precise. It means there is more than one glass here, and the system cannot see the second one's base from where it is standing. That is the valuable outcome, because it names what a new viewpoint has to achieve, where a vague failure would leave the next solution guessing.

Finally, the fourth outcome is the one the wide range of sizes adds, and it is not a refusal at all. A glass can be covered so completely that neither the width nor the bottom edge shows anything, and then this method returns one glass without hesitating. That outcome, and what has to be done about it, is the subject of the later part of the page about when the glasses are completely hidden.

<!-- section: when-the-glasses-are-completely-hidden | When the glasses are completely hidden -->

The next part of the page explains what happens when the glasses are completely hidden. 

Everything above this point has assumed that each glass puts at least a few pixels into the picture. This section is about the case where one of them puts in none. It is the case the wide range of sizes inside a single kind makes possible, and it is not a harder version of the merging problem. It is a different problem, and the honest summary of it is short. This solution does not handle it, and it cannot even notice it. A merge leaves a patch that is too wide, which something can see. A glass that contributes no pixels leaves one patch of a perfectly legal width, belonging to the glass in front of it, which nothing inside this picture can see. So the method returns one glass, without hesitating, and the count it passes on is one too low.

The two camera positions produce this case in two quite different ways, and the difference decides what can be done about each. From the top it is caused by the outward lean of a tall glass's outline, and it needs the two glasses to be close together and very different in height. From the side it is plain line of sight, and it needs neither. They are taken in turn.

Start with what happens when the camera is looking straight down. From the top, the arm holds the camera 450 millimetres above the table and points it straight down, which is the view this project surveys the table from.

Consider what that camera does to one standing glass. A horizontal slice of the glass at a given height above the table is nearer the lens than the table is, by exactly that height. So the slice is drawn as though it had been scaled about the point directly under the camera. The scaling factor is the camera's height above the table, divided by that height minus the height of the slice. This is the ratio derived earlier for how far out a glass is reported to be, applied here one slice at a time. The scaling moves the slice's centre away from the point under the camera and makes its radius larger, both by the same factor. At the rim of a 225 millimetre glass, the factor is 450 divided by 450 minus 225, which is exactly two. The rim circle is therefore drawn twice as far out from the point under the camera as it really is, and twice as wide. This outward lean is called splay, and it is what lets a tall glass's outline reach over a neighbour standing beyond it.

When the splayed outline of a tall glass contains the whole splayed outline of a shorter one, the shorter one contributes no pixels at all. What comes back is one patch, belonging to the tall glass, of an entirely legal width. A diagram illustrates this, showing a tall glass covering a short one in the survey picture, and then showing the same two glasses turned a quarter turn, where the short glass is no longer covered.

Here is one arrangement that does it. Both glasses are of the same tapered kind and both sizes are inside the range that kind allows. The tall one is 225 millimetres high and stands 200 millimetres out from the point under the camera. The short one is 95 millimetres high and stands 160 millimetres further out along the same line, which is comfortably past the 150 millimetres this problem guarantees between two centres. None of the short glass's 3448 pixels reaches the picture. The patch that comes back measures 325 millimetres across the table, where a single glass of this kind standing in that spot could draw 340 millimetres, so no width check can object to it.

Now move the short glass the same 160 millimetres across that line instead of along it, and leave the tall glass where it was. All 2891 of its pixels come back, in a patch of its own. Splay throws everything directly away from the point under the camera, so it can only hide along a line out from that point.

That is the first of four conditions, and together they make this a narrow arrangement rather than a common one. First, the pair has to lie within about six degrees of the line out from the point under the camera. Second, the two glasses have to be close together. At 200 millimetres out, the tall glass covers the short one at 160 millimetres of separation and fails to at 170 millimetres. Third, they have to differ a great deal in height, and the glass that disappears is always the shorter one, because across every arrangement tried a glass never covered another of its own height and a short glass never covered a tall one. Finally, the glass doing the hiding has to stand well out from the point under the camera, because splay grows with distance from it. At the closest spacing this problem allows, nothing is covered at all until the tall glass is 180 millimetres out.

That last condition settles the matter for this cell, because it costs more than it buys. A tall glass standing 200 millimetres out has its own outline thrown 309 pixels from the middle of the picture, and the frame is 320 pixels wide, so the edge of the frame is only 160 pixels from the middle. The glass doing the hiding is therefore cut by the edge of the frame, and a patch that touches the edge of the frame is reported as cut off rather than measured. This agrees with the count made earlier on the page. Of the 24 legal arrangements that put both glasses wholly inside one survey frame, not one of them merged.

There is a plainer reason as well why this solution has nothing to offer from the top. The whole method reads the bottom edge of a shape against a horizon, and a camera pointing straight down has no horizon. So from the top this solution is neither asked the question nor able to answer it. Deciding whether a glass could have been hiding in a survey picture belongs to the second solution, which works it out from the positions and heights of the glasses that were found.

Now consider what happens when the camera is looking level. From the side the arm brings the camera down to 120 millimetres above the table and stands it 380 millimetres back from the glass it is measuring, pointing level rather than down. That is the view this whole solution works in.

Hiding here needs no splay and no difference in height. It is line of sight in the everyday sense. The near glass's outline covers the far one's, the way a person standing in front of you hides someone behind them.

Two things follow, and both are the opposite of what happens from the top. The first is that the distance between the two glasses buys nothing. Two glasses of this kind standing 300 millimetres apart and in line with the camera cover each other completely, and they still do at 600 millimetres apart. The second is that which glass disappears is settled by which one is nearer, and not by which one is taller. And because the near glass is nearer, it is drawn larger, so a short glass in front can cover the lower part of a tall glass behind it. A diagram shows two glasses in line with the level camera, demonstrating that the near one's outline covers the far one regardless of their heights.

Take the first case. A 225 millimetre glass stands 380 millimetres from the camera, and another of the same height stands 300 millimetres behind it, directly in line. None of the far glass's 2901 pixels reaches the picture. What comes back is one patch, 75 pixels wide, against the 77 pixels the widest glass of this kind could draw from 380 millimetres, so the width check says nothing. Its underside holds one level stretch, so the bottom-edge test says nothing either. The patch is one glass wide and has one place of contact, so this method returns one glass and is right about everything it was asked. It was simply not asked the right question.

The second case is sharper, and it shows what the method is actually short of. Put the 95 millimetre glass in front and the 225 millimetre one 300 millimetres behind it. Now 2145 of the far glass's 2901 pixels do reach the picture, because it stands up above the near glass's rim. The answer does not change. The patch is 49 pixels wide, which is legal, and its underside still holds one level stretch, because the base of the far glass is behind the near one. What this method needs from a second glass is not pixels but a base, and the base is the first part of a glass that a nearer glass covers.

This is why the refusal described earlier does not protect you here. When two glasses are of similar size, some part of the far one's base usually shows, so the method either splits the pair or refuses and asks for another viewpoint. When one glass covers another completely, nothing about the picture looks wrong, so there is nothing to refuse. The refusal protects you only when the evidence is visibly incomplete, and this is the case where it is not.

So what does this solution hand off, and to whom? By itself, nothing, and that is the uncomfortable part of the answer. It cannot raise the case because it cannot see it. The check that catches a completely hidden glass has to be made somewhere that knows where the glasses that were found are standing and how tall they are, and that is the second solution, which asks whether there is a piece of table where a glass could have stood and still produced nothing. Once something has said that a glass may be missing, the third solution supplies the cure, by standing the camera somewhere the missing glass is no longer behind anything. This solution's whole part in that is to be honest about what its count means. It reports the glasses it could see, and it must never be read as reporting how many glasses are there.

<!-- section: a-worked-example | A worked example -->

The next part of the page walks through a worked example of this method. It describes what happens in a specific case, rather than just what is measured.

Imagine two glasses of the same kind standing on a table. They are tumbler-shaped, meaning their rims are wider than their bases. The camera is positioned at the side, low down and level, standing back from the nearer glass at the usual measuring distance. The second glass is further back along the same line of sight, but slightly off to one side. That small sideways offset is the only reason any part of the second glass's base is visible at all.

When the camera looks at this setup, what comes back is a single patch of pixels. When this patch is measured across, it is clearly wider than the widest glass of this kind could appear from this distance. Because of this, the width check flags the patch.

Next, the bottom edge of the patch is read by finding the lowest yes pixel in each column. Most of the short stretches of pixels are discarded because they are just the side walls of the glasses. After discarding those, two flat stretches survive. One of these flat stretches lies to the left and sits lower in the picture, while the other lies to the right and sits higher up. According to the horizon relationship, a lower position in the picture means the object is nearer. Therefore, the left stretch is the base of the nearer glass, and the right stretch is the base of the further glass.

These two stretches are separated by an amount that is many times larger than the natural wobble in the edge, so they comfortably pass the separation threshold. Even more useful than that, the separation exactly matches what the horizon relationship predicts for those two distances. That agreement is the real check. It proves that the two stretches are not merely different, but they are different by the exact amount that the geometry says they should be.

So, the system concludes that the answer is two glasses. It makes a cut between the two stretches, assigning the left piece to the nearer glass and the right piece to the further one. This entire process is very fast, taking only the time needed to walk through a small array twice. However, what the method has still not produced is any actual position on the table.

<!-- section: where-the-idea-comes-from | Where the idea comes from -->

The next part of the page explains where the idea comes from. Nothing here was invented for glassware, and it helps to know which older ideas are being used, because that tells you when the method will and will not travel to another problem.

Splitting one patch into separate objects is an old problem, and the standard tool for it is the watershed algorithm applied to the distance transform. The idea is to treat the patch as a landscape. For every foreground pixel, you work out how far it is from the nearest background pixel, which makes the middle of a blob deep and its edges shallow. Then you find the deepest points, flood outwards from each one as if pouring water, and build a wall where two floods meet. For touching cells under a microscope, or coins on a scanner, this is the right answer.

Here it is the wrong answer, and it fails for a structural reason rather than because some number needs adjusting. A diagram in the text illustrates why the distance transform cannot help. In a short, round object, the deepest point is a single peak in the middle. Two such objects give two peaks, and the wall lands neatly between them. However, a standing glass seen from the side is several times taller than it is wide, and its distance from the outside is limited by its half-width, and by that same half-width all the way up. So its deepest part is not a peak at all. It is a ridge, like the line along the top of a roof. When two such ridges overlap they join into one ridge, only one starting point survives, and there is nothing left to flood from.

We measured this across all four kinds on every merged pair we could produce. The watershed method split only a handful of them and left the rest joined. No choice of threshold repairs that, because the problem is the shape of the landscape and not where the water line is put.

The method this page uses instead is not new either. It is the ground-plane constraint, which says that if you know how high the camera is above a flat surface, then the row where an object meets that surface tells you how far away the object is. In work on detecting pedestrians, the place where a person meets the ground is called the foot point. Mapping a whole picture onto the ground in this way is called inverse perspective mapping, a technique described by Mallot and colleagues in 1991. The best-known explanation of why this is so useful is a paper by Hoiem, Efros and Hebert called Putting Objects in Perspective, whose argument is that a known ground plane plus a known camera height turns a picture into a measurement.

What is a little unusual here is the job we give it. Normally people use it to work out how far away something is, or to throw away a detection whose apparent size does not match its distance. We use it to separate two objects instead, on the grounds that two contact rows inside one patch mean two glasses. It is the same arithmetic doing a different job. This cell also happens to be an easy case for it, because the table is flat and level, its height is known, it is fixed to the same frame as the arm, and everything of interest stands on it.

A third tool, which belongs elsewhere in the order, is GrabCut. This is the other tool people often reach for, and it answers a different question from this one. Given a rough box around an object, it separates the object from the background by modelling the colours of each, and then smooths the result. It is genuinely useful when a threshold has left a ragged edge. But it never decides how many objects are present. Give it a box around two merged glasses and it returns a tidier outline of the same merged pair. So it belongs after this method, and not instead of it.

As a final note, the companion robotics basics notes have nothing on the ground-plane family. That is a real gap, because it is the cheapest way to get depth out of one camera and it needs no trained model at all.

<!-- section: where-it-is-strong-and-where-it-breaks | Where it is strong and where it breaks -->

The next part of the page covers where this method is strong and where it breaks. 

The strengths of this method all follow from how little it needs. It is effectively free. The work is a small amount of array arithmetic, it adds no new library, and against the seconds that every movement of the arm costs, its own cost never appears in the accounts at all. It never invents a glass, because across every single glass we tested it on, of all four kinds and at a range of distances, it produced no wrong split. It hands back the order of the two glasses as well as the split, which is a genuine extra, because the nearer glass is the one worth measuring first. Every step it takes can be printed as a number, so a wrong answer is something you can read rather than a mystery. And it needs no depth readings at all, which matters more than it first appears. On real glassware, a depth camera returns a glass-shaped hole rather than a reading, because the beam passes through the glass instead of bouncing back, so every method that groups points in three dimensions stops working while this one carries on.

The weaknesses divide into one real limit and several assumptions. 

The real limit is that the method cannot see a base that is hidden. A diagram showing where the method works and where it cannot illustrates that it split somewhat over half of the merged pairs we gave it, and the pattern of successes is a cliff rather than a slope. Once the further glass is offset sideways by more than a small amount, roughly half a glass's width, it split every merged pair without exception, and below that offset it split almost none. There is nothing in the middle to tune, because the underlying question is not a matter of degree. Either some part of the far glass's base is visible, or none of it is.

That limit cannot be closed by better processing, and a second diagram illustrates what a split does not buy. When the far glass stands almost exactly behind the near one, its base is hidden, and no amount of work on this one picture will bring it back. Such a pair has to go to the solution that moves the camera.

The wide range of sizes inside one kind makes that limit harder still, and in a way worth stating separately, because it is the difference between an incomplete answer and a wrong one. That case is covered later on the page in the part about when the glasses are completely hidden, and it is the one place where this method answers rather than refuses.

The assumptions are worth stating because they are true in this cell and are still assumptions rather than facts about the world. The method assumes the table is flat, level, and at a known height. A table a few millimetres out of level moves the horizon by about a pixel, which sits inside the noise and is harmless, but a genuinely sloping table would not be harmless at all, because then the horizon would no longer be a single row. The method also only works with the camera at the side, looking level, and that is a real restriction rather than a formality, because a tall glass can cover a short one from the top as well. What happens then is explained in the later section about when the camera is looking straight down.

Two failure modes are worth knowing in advance. First, a glass cut off by the edge of the picture has a bottom edge that simply stops at the boundary. The flat-stretch test survives that, but the width check does not, because a cut-off shape is narrower than its glass, so a patch touching the edge should be reported as cut off rather than measured. Second, anything else standing inside the same patch is counted, because the method finds places of contact rather than glasses. For example, the foot of the drying rack inside the same patch would read as one more place of contact. The circle fit in solution two is the guard against that.

Finally, the method gives no position, and this is a limit rather than an oversight. Both pieces are still flat shapes in a picture. Seen from the top, the leaning-outward effect makes a glass appear to stand much further out than it really does, and the earlier work measured that error as overstating the distance by more than half. A mask is not a place.

<!-- section: where-it-sits-among-the-other-solutions | Where it sits among the other solutions -->

The next part of the page explains where this method sits among the other solutions. 

The right way to think of this method is as a first pass for the camera at the side, and not as a rival to the solution that clusters points on the table. The two approaches answer different questions. Splitting the blob tells you how many glasses are inside a patch and which of them is nearer. Clustering tells you where each glass is on the table. Where depth readings work, clustering is the answer, and this method is a cheap cross-check. Where depth readings do not work, this method is what remains.

Its natural partner is the solution that moves the camera. Moving the camera supplies the one thing this method cannot get for itself, namely a place to stand from which the hidden base is no longer hidden. So when this solution cannot split a pair, that is not a complaint. It is a clear and specific request to stand somewhere else and look again.

The best time to use it is first, whenever the camera is at the side, because it is free and it separates most of the pairs that line up. It is also the right choice whenever there is no depth to work with, as is the case with real glass. Finally, it is worth keeping as a second opinion even where clustering works, because it fails in different situations from the methods that reason about distance. Two methods that fail differently but agree with each other are worth more than either of them alone.
