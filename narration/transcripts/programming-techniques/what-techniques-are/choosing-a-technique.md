The title of this page is Choosing a technique. For almost every job on a robot arm, there is more than one technique that could do it. For example, you can find the table top by assuming its height, by averaging many points, or by a method that ignores bad points. Or, to find a path, you can search a grid or try random poses. So this page explains how to choose between them.

It answers one question: when two techniques could both do a job, which one should you use? It gives five things to check, and shows each one with a small example on an arm. The last of the five is whether to use a written technique at all, or a learned model instead. Every technique page later in the book answers the same five questions for its own technique, so this page is also a guide to reading those pages.

The first section covers the five questions promised in the introduction, in the order that the rest of the page takes them. First, is it fast enough for the loop it has to run in? Second, is it accurate enough for what the arm does with the answer? Third, does it still work when some readings are noisy or plain wrong? Fourth, how many parameters must you choose, and how hard are they to choose? And finally, would a learned model do this job better?

No technique wins on all five, because a fast technique is often less accurate, and a technique that ignores bad readings is often slower. So the aim is not to find the best technique in general, but to find the simplest technique that passes all five questions for your job. Simplest matters here, because a simple technique has fewer steps that can go wrong, is easier to test, and is easier for the next person to understand. So start with the simplest technique that could work, and move to a harder one only when you can point to the question the simple one fails.

The next part of the page is about speed and the time budget. The first of the five questions is whether a technique is fast enough, and the answer comes from the loop it runs in. A technique on an arm runs inside a loop, so the loop's rate sets a time budget. This is the time one run of the technique may take before the next reading arrives. You work that budget out by dividing one thousand milliseconds by the number of runs per second.

The page has a diagram showing five horizontal bars on a log scale, which means each labelled step is ten times the one before it. This lets very different times fit on the same picture. The joint position loop at one thousand times a second leaves a budget of 1.0 milliseconds. A force check at 500 times a second leaves 2.0 milliseconds. A colour camera at 30 pictures a second leaves 33.3 milliseconds. A depth camera at 15 pictures a second leaves 66.7 milliseconds. Finally, a plan made once a second may take up to 1,000 milliseconds.

The budget is for everything in that loop, not just your technique. In the camera loop, 33.3 milliseconds has to cover reading the picture, finding the mugs, working out their positions, and passing them on. So a technique that takes 30 milliseconds by itself is already too slow there.

The budgets differ by a factor of a thousand, which is why the same arm uses very different techniques in different places. The joint loop can only afford a few multiplications, such as proportional-integral-derivative control, which is usually called PID control. A planner that runs once before each move, in contrast, can afford to try thousands of poses, such as sampling-based planning.

Speed also depends on how much data there is, so it helps to ask how the time grows when the data grows. Take the brute-force way of finding, for every point in a point cloud, which other point is closest to it. That method compares each point with every other point. With one thousand points that is 499,500 pairs. With two thousand points it is 1,999,000 pairs. So twice the points means four times the work. A depth picture can have 300,000 points, and this simple method therefore becomes far too slow. A different method, like a nearest-neighbour search using a k-d tree, sorts the points into boxes ahead of time and avoids most of those comparisons. So when you judge speed, ask two things: how long one run takes on your data today, and how much longer it will take if the data grows.

Moving on to accuracy, the page asks how close is close enough. Speed is only the first question, because an answer that arrives on time is no use if it is wrong. Accuracy is how close a technique's answer is to the truth, and no technique is perfectly accurate, because its input is noisy. So the useful question is how accurate the answer needs to be for what the arm does next.

You work that out from the task, not from the technique. Here is an example. A gripper's fingers open to 80 millimetres and a mug is 70 millimetres wide. So if the gripper comes down centred on the mug, there is 80 minus 70, divided by 2, which equals 5 millimetres of room on each side. This means the mug's position must be right to within about 5 millimetres, or a finger lands on the rim.

Now compare two techniques against that 5 millimetres. A technique that is right to within 1 millimetre passes easily, while a technique that is right to within 10 millimetres fails, however fast it is. And a technique that is right to within 0.1 millimetres is no better for this job than the 1 millimetre one, so the extra time it probably costs buys nothing.

Accuracy also adds up along a chain, because the mug's position passes through the camera model, the camera's calibration, the transform to the base, and the arm's own joints. Each one adds a little error. If each of four steps adds 2 millimetres, the total can reach 8 millimetres, which is more than the 5 millimetres of room. Calibration is about removing the largest of these errors. When you judge accuracy, ask how much error the next step can accept. Then check the whole chain against that number, not just one technique.

The next section is about robustness to noise and bad readings. The accuracy question assumed that the readings are merely noisy, but some readings are worse than that. A technique is robust if it still gives a good answer when some of its input is bad. There are two kinds of bad input: noise, which is a small error on every reading, and an outlier, which is a reading that is completely wrong.

Many simple techniques handle noise well and outliers badly. Here is an example. A depth camera looks along the straight edge of a table and measures 24 points along it. The edge truly rises 0.5 millimetres for every 1 millimetre along it, and starts at a height of 40 millimetres, so most readings are close to that line. However, five of them are 60 to 90 millimetres too low, because of a reflection.

The page shows a diagram of this. There are blue points along a straight line, and five red crosses far below it. A grey dashed line is fitted to all 24 points and is dragged down by the five wrong readings. A green line comes from a robust method that ignores them and lies on the good points.

Those two lines come from two techniques that answer the same question in different ways. The grey dashed line is least squares on all 24 points. It finds the line with the smallest sum of squared differences. It gives a slope of 0.472 and a starting height of 28.3 millimetres. At the far end of the edge, 300 millimetres along, it says the height is 169.8 millimetres. The truth is 190.0 millimetres, so it is about 20 millimetres too low.

The green line is random sample consensus, usually called RANSAC. It tries many lines, each through two points chosen at random. For each line it counts how many points lie within 8 millimetres of it. It keeps the line that the most points agree with, and then fits it again to just those points. Here 19 of the 24 points agree. It gives a slope of 0.505 and a starting height of 38.5 millimetres. At 300 millimetres it says 190.1 millimetres.

Least squares is pulled down because squaring makes large differences count a great deal, and each outlier is 60 to 90 millimetres off, so its square is very large. RANSAC is not pulled down, because it never lets the outliers vote for the final line.

This does not make RANSAC always better. It is slower, because it tries many lines, and it is random, so two runs can give slightly different answers. It also needs two parameters that least squares does not. So if your readings have noise but no outliers, least squares is faster and just as good. When you judge robustness, look at real readings from your own camera, and ask whether there are outliers, how many of them there are, and how far off they are. Then test the technique on those readings, not on clean ones.

The previous section ended with the two parameters that RANSAC needs, so the next section looks at how much tuning a technique needs. A parameter is a number you choose before a technique runs, and tuning is the work of choosing those numbers. Every parameter is a question someone has to answer, and has to answer again when the scene changes.

Here are the parameters needed by some common techniques. A simple depth rule might have one, such as a 580 millimetre limit. The RANSAC line has two: the 8 millimetre distance that counts as agreeing, and how many lines to try, which was 200. A PID controller has three per joint, so eighteen on a six-joint arm. A colour mask has six: a low and a high limit for each of three colour numbers.

A parameter is easy to tune if it has a physical meaning you can measure. For example, the 580 millimetre limit is easy, because you measure the table's distance and subtract a margin. A parameter is hard to tune if it has no clear meaning, or if it interacts with other parameters, because changing one PID number changes how the other two behave.

Parameters also go stale. The 580 millimetre limit is right for only one table height. Move the camera 50 millimetres higher, and every depth reading grows by about 50 millimetres, so the limit is wrong. In the same way, a colour mask tuned in the morning may fail in the evening light. When you judge tuning, count the parameters and ask of each one: can I measure it, or must I guess and test it? And what change in the scene would make it wrong?

The fifth question is when to switch to a learned model. This asks whether a written technique is the right kind of tool at all. The alternative is a model learned from examples. The main thing that decides is how much the scene varies. If the objects, their places and the light are the same every time, a written rule can describe them exactly. However, if they change a lot, a rule cannot list every case.

The page shows a diagram with a line of arm jobs, from going to a pose taught by hand on the left, to folding a towel on the right. The left third is marked for written techniques, and the right third for learned models. Jobs on the left, such as finding the flat table top, are done well by written techniques. Jobs on the right, such as grasping objects never seen before, are usually done better by learned models. Jobs in the middle often use both.

There are signs that a written technique is running out. First, you keep adding special cases, and each one breaks another. Second, you cannot describe the failures in words, but can only say it looks wrong. Third, one set of parameters cannot suit all the scenes you see in a day. And finally, the thing to recognise has no simple shape or colour, such as a mug of any kind or a good place to grab a towel.

On the other hand, there are signs that a written technique is still the right choice. First, the job is geometry or arithmetic, such as a transform or a camera model. Second, the answer must be exact, and you must be able to check it. Third, it must run in a millisecond, on a small processor. And finally, you have no examples to learn from, or cannot afford to collect them.

Most arms mix the two. A learned model does the part that needs variety, such as object detection to find the mugs in a colour picture. Written techniques, meanwhile, do the parts that need exactness: turning pixels into positions, planning the path and driving the motors. So when you switch, you usually replace one step in the chain, not the whole chain.

Now that all five questions have been described, the next section gives a worked choice to show how they work together. The job is to find the height and tilt of the table top from a depth camera on the arm's wrist. Every later step uses the table top, because it tells the arm how low the gripper can go, and it lets the program remove the table points so that only the objects are left.

There are four candidates for the job, running from a hand measurement to a learned model. The page uses a table to run the five questions on each candidate.

The first candidate is to measure the table once by hand, and write the height into the program. This is fast, and needs no tuning, but it fails the robustness question because it fails as soon as the table or camera moves.

The second candidate is to fit a plane to all the depth points with least squares. This is fast and needs no tuning, but it is not accurate or robust, because the mugs on the table act as outliers and pull the plane up.

The third candidate is to fit a plane with RANSAC, which ignores points that are not on the plane, such as mugs. This passes all five questions. It is fast enough for a downsampled cloud, accurate, and robust because the mugs are treated as outliers. It just needs a distance and a number of tries for tuning.

The fourth candidate is to use a learned segmentation model that labels which pixels are table. This is usually fast enough with a graphics card, and is robust on scenes like its training data. However, it costs training data and time, and it still needs a plane fit afterwards to get the height as a number.

So candidate 3, RANSAC, is the usual choice for this job.

The page then collects the five questions into a checklist. For each question, it gives what to measure, and the sign that the technique fails it.

For the first question, "Fast enough?", you measure the time for one run on real data, and the loop's budget. The sign that it fails is that the loop misses its rate, so the arm jerks or the picture lags behind.

For "Accurate enough?", you measure the error against a known truth, such as a ruler or a marker. It fails if the gripper lands off-centre by more than its room allows.

For "Robust?", you measure the answer on real readings, including shiny, dark or cluttered scenes. It fails if one bad reading moves the answer a long way.

For "Easy to tune?", you check the number of parameters, and whether each can be measured. It fails if it works after tuning but fails the next day.

And for "Written or learned?", you measure how many special cases you have written, and how varied the scene is. It fails if each fix breaks another case.

Every technique page in the book has a section on where the technique is useful and where it is not, which answers these five questions for its own technique, and names what people use instead when the technique fails.

The final section suggests where to read next. The map of techniques is the next page, which lists all 34 techniques in the book and places them on one arm task. There is a page on RANSAC that explains the robust fit in full. A page on running a model on a robot shows the time budget from the learned side. And a page on making it work is about testing perception on real scenes, which is how you answer the robustness question in practice.
