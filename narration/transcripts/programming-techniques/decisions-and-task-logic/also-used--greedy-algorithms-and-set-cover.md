Greedy algorithms and set cover.

This page explains greedy algorithms, together with the most useful problem they solve on a robot arm, which is set cover. It answers four questions: what does "greedy" mean for a program, how does greedy set cover choose the fewest camera views that see every object, how close to the best answer does it get, and when should you use something else instead?

It is written for a reader who has met the arm, the camera on its wrist, and the idea of a viewpoint, as in Books 1 and 2, but who has not taken an algorithms course. No knowledge of complexity theory is needed, and where the page uses a term such as "NP-hard", it explains that term in plain words first.

The page sits in the chapter on decisions and task logic, and it answers a different question from the two pages before it. While those pages, which covered finite state machines and behaviour trees, decide which step the robot does next, this page and the next one on optimisation solvers instead decide which choice to make when there are many possible choices and some are better than others.

The first section gives the idea in one sentence. Since this page is about choosing among many choices, here is the method. A greedy algorithm builds an answer one piece at a time, and at each step it takes the piece that looks best right now, without ever going back to change an earlier piece.

Here is an everyday example of the same method at work. You have a shopping list of eight items, and there are four shops in town, each selling some of the items, and you want to visit as few shops as possible. The greedy way to choose the shops is simple. First, go to the shop that sells the most items on your list, and cross those items off. Then, go to the shop that sells the most of the items that are left, and repeat until the list is empty.

That plan is quick to work out, and it is usually good, but it is not always the best plan. A later section shows a case where it visits three shops when two would have been enough.

The word "greedy" describes two properties together. First, the choice at each step uses only what is known at that step. It does not look ahead to see how this choice affects the later ones. Second, a choice, once made, is never undone. Both of those properties make a greedy algorithm fast and short, but both are also the reason why it can miss the best answer.

The next part of the page introduces set cover, which is the problem greedy is best known for. The shopping example has a name, and it is called set cover. Its general form is this: you have a list of things that must all be covered, called the universe, and you also have a collection of groups, called sets, where each set covers some of the things. The task is to choose as few sets as possible so that every thing is covered by at least one chosen set.

On a robot arm, set cover appears whenever one action serves several needs at once, and the most common case is choosing camera views. Think of a camera on the arm's wrist, looking straight down at a table. From each pose the arm can reach, the camera sees one rectangle of the table, and that rectangle is called the camera's footprint. An object is seen from a pose if it lies inside that footprint, so each candidate pose is a set, namely the set of objects it sees. The universe is then the list of objects the robot must look at, and choosing the fewest poses that together see every object is set cover.

Book 2 treats this choice in depth in the page on choosing where to look, including how to test whether one object hides another from a view. Instead, this page takes the sets as given, and looks only at how to choose among them.

Set cover is also NP-hard, which in plain words means that no method is known that always finds the smallest group of sets quickly. Instead, every known exact method takes, in the worst case, a time that grows faster than any fixed power of the number of sets. For a handful of views that does not matter, but for hundreds it does. That is why the greedy method is the usual choice.

The next section explains how greedy set cover works, step by step. Because an exact method would be too slow at scale, the greedy method for set cover is used instead, and it has three steps. First, start with every object marked as not yet seen. Second, look at every candidate view that is not chosen yet. For each one, count how many not-yet-seen objects it would see. Take the view with the highest count, and mark its objects as seen. Finally, repeat the second step until every object is seen. If no view can add a new object while some objects are still unseen, stop and report those objects as not coverable.

When two views have the same count you can take either one, but a real program takes the first one in its list, which is what the example below does.

Because those three steps are easier to follow on a real scene, the page gives a worked example with eight glasses. Eight glasses, named A to H, stand on a table 600 millimetres wide and 400 millimetres deep, and the arm can place its wrist camera over four candidate points, looking straight down. The camera is the same one used across this repository, with a 320 by 240 pixel picture and a focal length of 277.1 pixels. So at a height h above the table its footprint is h times 320 divided by 277.1 wide, and h times 240 divided by 277.1 deep. At 277 millimetres up, this is 320 by 240 millimetres, and at 180 millimetres up it is 208 by 156 millimetres.

A diagram shows four candidate views, each with a dashed rectangle for its footprint, and the red glasses inside it that the view can see. A table lists these four sets. View L is at a height of 277 millimetres and sees four glasses: A, B, C, and D. View M is at the same height in the middle and sees six glasses: B, C, D, E, F, and G. View R is on the right, also at 277 millimetres, and sees four glasses: E, F, G, and H. Finally, View S is lower, at 180 millimetres, and sees just two glasses: G and H.

The greedy method can now be run on those four sets. First, all eight glasses are unseen. The counts are L 4, M 6, R 4, and S 2. View M has the highest count, so greedy takes M. Glasses B, C, D, E, F, and G are now seen. Only A and H are left. Second, the counts for the views that are left are L 1 because it adds A, R 1 because it adds H, and S 1 because it adds H. They tie. Greedy takes the first, which is L. Now only H is left. Third, the counts are R 1 and S 1. Greedy takes R. Every glass is now seen.

A diagram shows these three steps, highlighting that greedy takes M first, then needs L and R for the two glasses M missed. So greedy ends up using three views, which are M, L, and R.

Since there are only four views here, a program can simply try every group of them to check the answer. That is called brute force or exhaustive search, meaning try every possibility and keep the best. It starts with groups of one view, then groups of two, and it stops at the first group that sees all eight glasses. No single view sees all eight, because the largest, M, sees six. But of the six possible pairs, L with R sees all eight. L sees A to D and R sees E to H.

So the smallest answer is two views, L and R, while greedy used three. A diagram puts these two answers side by side, showing greedy's three footprints overlapping on the left, while on the right, L and R alone cover the whole row of glasses without overlapping.

The reason greedy lost is visible there. View M is the biggest single set, so it looks like the best first choice. But M sees the middle six glasses and leaves one glass at each end, so each of those two glasses then needs its own view. While views L and R each see fewer glasses than M, they fit together without any overlap. This happens because greedy never asks how well a view fits with the others, only how many new glasses it sees right now, which is the whole weakness of a greedy choice in one example. This kind of trap is not rare in a real cell, because a camera held high sees the most, so it wins the first round, and the objects near the edges then need extra views.

Once the method is clear, it fits in a few lines of pseudocode. The code starts with a copy of the objects marked as unseen, and an empty list of chosen views. It loops while there are unseen objects. Inside the loop, it checks every view not yet chosen, counts how many unseen objects it contains, and finds the view with the highest count. If the best view adds nothing, it stops and returns the chosen views along with the objects that cannot be seen. Otherwise, it adds the best view to the chosen list, removes its objects from the unseen set, and repeats.

The exact check used above is just as short to write, but its running time is very different. It loops through group sizes from one up to the total number of views. For each size, it checks every possible group of views, and if the union of what the group sees contains every object, it returns that group. With m candidate views, the exact check can try up to two to the power of m groups. Four views means 16 groups, while sixteen views means 65,536 groups, which a computer tries in well under a second. But thirty views means over a billion groups, and forty views means more than a million million. Greedy, in contrast, looks at each view at most once per step, so it does at most m times m counts.

The next section asks how far from the best greedy can be. The example above was one scene, so two questions matter in practice. How often does greedy miss the smallest answer, and by how much?

To find out, a script built a thousand random scenes of each of three sizes, placing glasses and candidate views at random on the table, with random camera heights. For each scene, it ran greedy and also found the smallest answer by trying every group. A chart and table show the results. For scenes with 8 glasses and 8 views, greedy found the smallest answer 95.6 per cent of the time, and used one extra view 4.4 per cent of the time. For 12 glasses and 12 views, it found the smallest answer 89.8 per cent of the time. For 20 glasses and 16 views, it found the smallest answer 78.1 per cent of the time, used one extra view 21 per cent of the time, and used two extra views 0.9 per cent of the time.

Three things stand out in those numbers. First, greedy is right most of the time, and never used more than two extra views in these trials. Second, it gets worse as the scene grows. With 20 glasses it missed the smallest answer in about one scene in five. Third, on average the extra cost is small: a fifth of a view with 20 glasses.

There is also a proven limit on how badly greedy can do. If the largest set holds d objects, greedy never uses more than 1 plus a half plus a third, and so on, up to 1 divided by d, times as many sets as the smallest answer. That sum grows very slowly, roughly as the natural logarithm of d. In the example, the largest view sees six glasses, so the limit is 1 plus a half plus a third plus a quarter plus a fifth plus a sixth, which equals 2.45. Greedy used 3 views where 2 were enough, which is 1.5 times, well inside that limit. Researchers have also shown that, unless a famous open question in computer science has a surprising answer, no fast method can promise a much better limit than this one. In short, greedy is about as good as any fast method can promise to be.

But a related question often matters more on a robot. Suppose the arm has time for only two views, so which two should it take to see the most glasses? That question is called maximum coverage, and greedy is again the usual method, because you simply take the view that adds the most, twice. This is proven to see at least about 63 per cent of what the best pair would see. In the example, greedy's first two picks, M and L, see seven of the eight glasses, while the best pair, L and R, sees all eight.

The next part of the page lists where greedy choices are used on a robot arm. Greedy set cover is only one greedy algorithm among many, because the same "take the best-looking choice now" rule appears all over robot-arm software. Here are the common places where it does.

First, choosing a fixed set of camera views offline. As described in Book 2, you take the candidate that sees the most target points, remove those points, and repeat. It runs once at a desk, and then the chosen poses are tested on the arm.

Second, covering patches that could not be seen. A glasses-picking project uses greedy set cover when some patches of the table are hidden behind glasses. Each candidate camera position sees some of the hidden patches, and the program takes the one that sees the most, repeating until every patch is seen or the budget of extra looks runs out.

Third, deciding the order to visit places. Nearest-neighbour ordering is greedy: go next to the closest place not yet visited. Book 2 measured it, finding that on average it costs four to ten per cent more travel than the best order, and in the worst trial 48 per cent more.

Fourth, removing duplicate detections. An object detector gives several boxes for one mug. The clean-up step, called non-maximum suppression, is greedy, because it keeps the box with the highest confidence, removes the boxes that overlap it, and then repeats. This is explained in Book 6.

Fifth, matching detections to tracked objects. Greedy matching pairs the closest detection and track first, then the next closest, and so on, which is fast. But it can make a wrong pair when two objects pass close to each other. The page on assignment and matching compares it with the exact Hungarian method.

Sixth, picking from clutter. A bin-picking cell often picks the object with the highest grasp score first, or the object on top of the pile first. That is a greedy order. It works well because the scene changes after each pick, so a long plan would be out of date anyway.

Finally, online next-best view. When the robot looks, thinks, and then chooses the next pose, it usually takes the pose that would reveal the most unknown space. That is maximum coverage, one view at a time.

The next section explains where greedy is good enough, and where it is not. All the uses above have something in common, because greedy is a good choice when a small loss does not matter, when the problem is too big to solve exactly, or when the scene changes so often that a perfect long plan would be wasted. But it is a poor choice when each extra action is expensive and the problem is small enough to solve exactly.

A table lists the common ways greedy goes wrong on an arm.

If one large set overlaps many small ones, you will see greedy's views overlap a lot, and each extra view adds only one or two objects. Instead, try every group if there are fewer than about 20 candidates, or use an integer program.

If each view has a different cost, such as a long arm move, greedy might pick a view that sees many objects but is far away. Instead, use weighted greedy, choosing by new objects per second of arm travel, not by new objects alone.

If there are ties between views, different runs might pick different views for the same scene. You should break ties by a fixed rule, such as the shortest arm move.

If the order must obey rules, such as "C before B", a greedy nearest-neighbour ordering might visit a blocked object first. Instead, use a blocking graph or a solver with constraints.

If two tracks and two detections are close together, tracked identities can swap when objects pass each other. Instead, use the Hungarian method.

If no candidate sees some object at all, the loop will find no view that adds anything. You should report the object as unseen, add candidate poses, and ensure you do not loop forever.

The weighted form deserves one more sentence. If moving to a view costs time, divide each view's count of new objects by its cost, and then take the view with the highest ratio. This is the standard greedy method for weighted set cover, and it keeps the same proven limit.

So two signs tell you that greedy is probably good enough. First, the number of chosen views is small compared with the number of candidates, and removing any one chosen view leaves an object unseen. Second, when you run the exact search on a few saved scenes, it agrees with greedy or finds only one view fewer. But if the exact search often finds a smaller answer on your real scenes, that is the sign to switch.

The next section covers libraries that provide it. Greedy set cover is about fifteen lines of code in any language, so most projects write it themselves. This means libraries matter more for the exact alternative, and for the other greedy steps listed earlier.

For greedy set cover, your own code using a simple loop is the usual choice, and there is nothing to install. To solve set cover exactly as an integer program, you can use Google OR-Tools in C++, Python, Java, or C#. SciPy in Python also solves it exactly as a mixed-integer linear program. For routing, OR-Tools builds a first route greedily and then improves it. NetworkX in Python provides greedy approximations for graph problems, including a visiting order. For removing duplicate detection boxes, OpenCV and torchvision both provide greedy non-maximum suppression. And for the exact alternative to greedy matching, SciPy provides linear sum assignment.

The next part summarizes why to use greedy, and what it costs.

First, what it is. A greedy algorithm makes the best-looking choice at each step and then never goes back on it. So greedy set cover repeatedly takes the set that covers the most things not yet covered.

Second, what it does for you. It turns a problem that has no known fast exact method into a loop that finishes in a fraction of a millisecond for any cell-sized problem. And it gives an answer that is usually the smallest and is never far from it, because in the random trials it used at most two views more than needed, and usually none.

Third, why greedy rather than the obvious alternative. The obvious alternative is to compute the best answer exactly, either by trying every group or with an integer programming solver. Choose greedy when the exact answer is not worth what it costs. Trying every group becomes slow at about 25 to 30 candidate views, because the number of groups doubles with each candidate. A solver has no such wall at cell sizes, but it is a dependency to install, learn, and run. On many arms the scene also changes after every move, so the robot re-plans anyway, and one extra view now and then costs less than any of that. But the reverse also holds: when there are fewer than about 20 candidates, trying every group is short, exact, and fast, so there is no reason to accept greedy's loss.

Finally, what it costs you. It costs a guarantee, because greedy can use more views than needed, and it does not tell you when it has done so. It also costs predictability when views tie, unless you fix the tie-break rule. And a greedy order cannot respect a rule such as "C before B" unless you add that rule to the loop by hand.

The next section discusses the learned alternative. There is no learned model in Book 6 that replaces greedy set cover, because the problem is only counting which views see which objects. Greedy already solves it in a fraction of a millisecond with a proven limit, and an exact solver is there when greedy is not good enough. Instead, where learning appears around greedy choices, it supplies the scores that greedy ranks. A grasp quality model scores each candidate grasp, and a bin-picking cell then takes the highest score first. A detector's confidences decide in the same way which box non-maximum suppression keeps. A language model as planner also chooses one step at a time, but it chooses which task step to do next from a request in words, not which set of views covers every object.

The page then suggests where to read next. The page on optimisation solvers solves ordering, assignment, and packing problems exactly, and shows where greedy loses by 39 to 57 per cent on small tasks. The page on assignment and matching compares greedy matching with the Hungarian method. The page on graph search explains A-star, which also looks at the most promising place first, but, unlike a greedy choice, still finds the best path. The page on choosing a technique sets out how to weigh speed against accuracy in general. Book 2's page on choosing where to look covers the geometry of views, such as distance, angle, reach, and occlusion. And Book 3's page on ordering and rearrangement covers the order in which to move objects.

The final section shows how to use it in Python. Earlier, the page wrote greedy set cover as pseudocode and ran it by hand on the eight glasses, and said that most projects write it themselves because there is nothing to install. This section keeps that promise and gives the real Python, so that you can run the example and get the same three views back.

The code defines a dictionary of views, where each candidate view is paired with a set of the glasses it sees. It also defines a set of all eight objects. The greedy set cover function takes these objects and views. It creates a set of unseen objects and an empty list of chosen views. Then it loops while there are unseen objects. Inside the loop, it calculates the gain for each unchosen view, which is the number of still-unseen glasses it would add. It finds the view with the highest gain, breaking ties by taking the first view listed. If the best gain is zero, it returns the chosen views and the remaining unseen objects. Otherwise, it appends the best view to the chosen list, removes its glasses from the unseen set, and repeats.

That is the whole technique. When run on the example, it returns views M, L, and R, which is the same answer worked out by hand, and it leaves nothing unseen.

The exact check is nearly as short, because Python's itertools library has a combinations function that produces the groups for you. It loops through group sizes from one up to the total number of views. For each size, it checks every combination of views. If the union of the sets in a combination covers all the objects, it returns that group. When run on the example, it returns views L and R, the two-view answer. So the two functions together reproduce the result: greedy used three views where two were enough. The page also explains why you cannot simply always use the exact version, because the number of groups it tries doubles with every extra view.

No library does either job for you, and that is the honest answer for this page. The only library call used is itertools combinations, which is in Python's own standard library and only lists the groups. The part that matters is the views dictionary, and nothing on this page computes it. Working out which glasses a camera pose really sees is geometry, and that work is done in Book 2's page on choosing where to look. Building the sets is almost always harder than covering them.

What you have to decide is small but real. The tie-break rule is yours, and the code takes the first view in the dictionary, which means the order you insert the views changes the answer whenever two views add the same number of glasses. What counts as "seen" is yours as well. The sets in the example treat a glass inside the footprint as seen, but a glass at the very edge of the picture, or one hidden behind another, may not be, and that decision belongs in the geometry rather than in this loop. Finally, you decide which of the two functions to call. With eight glasses and eight views, greedy found a smallest answer in 95.6 per cent of a thousand random scenes, but with twenty glasses it missed in about one scene in five, and at those sizes the exact version is still fast enough to run.
