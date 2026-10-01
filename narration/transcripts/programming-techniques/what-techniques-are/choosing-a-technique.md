Choosing a technique. For almost every job on a robot arm there is more than one technique that could do it. For example, you can find the table top by assuming its height, by averaging many points, or by a method that ignores bad points. Or, to find a path, you can search a grid or try random poses. So this page explains how to choose between them.

It answers one question: when two techniques could both do a job, which one should you use? It gives five things to check, and shows each one with a small example on an arm. The last of the five is whether to use a written technique at all, or a learned model from Book 6 instead.

It is for a reader who has read the pages on programmed, not learned, and the building blocks. Every technique page later in the book answers the same five questions for its own technique, so this page is also a guide to reading those pages.

The first section covers the five questions. The introduction promised five things to check, so here they are, in the order that the rest of this page takes them. First, is it fast enough for the loop it has to run in? Second, is it accurate enough for what the arm does with the answer? Third, does it still work when some readings are noisy or plain wrong? Fourth, how many parameters must you choose, and how hard are they to choose? And finally, would a learned model do this job better?

No technique wins on all five, because a fast technique is often less accurate and a technique that ignores bad readings is often slower. So the aim is not to find the best technique in general, but to find the simplest technique that passes all five questions for your job.

Simplest matters here, because a simple technique has fewer steps that can go wrong, is easier to test, and is easier for the next person to understand. So start with the simplest technique that could work, and move to a harder one only when you can point to the question the simple one fails.

The next section is about speed, and the time budget. The first of the five questions is whether a technique is fast enough, and the answer comes from the loop it runs in. A technique on an arm runs inside a loop, as the building blocks page explained. So the loop's rate sets a time budget, which is the time one run of the technique may take before the next reading arrives. You work that budget out by dividing one thousand milliseconds by the number of runs per second.

The page shows a diagram with five horizontal bars on a log scale, ranging from one millisecond for the joint loop to one thousand milliseconds for a plan made once a second. The joint position loop at one thousand times a second leaves 1.0 milliseconds. A force check at five hundred times a second leaves 2.0 milliseconds. A colour camera at thirty pictures a second leaves 33.3 milliseconds. A depth camera at fifteen pictures a second leaves 66.7 milliseconds, and a plan made once a second may take up to one thousand milliseconds.

The scale along the bottom is a log scale, which means that each labelled step is ten times the one before it. This lets a one millisecond bar and a one thousand millisecond bar fit on the same picture.

The budget is for everything in that loop, not just your technique. In the camera loop, 33.3 milliseconds has to cover reading the picture, finding the mugs, working out their positions and passing them on. So a technique that takes 30 milliseconds by itself is already too slow there.

The budgets differ by a factor of a thousand, which is why the same arm uses very different techniques in different places. The joint loop can only afford a few multiplications, such as proportional-integral-derivative control, or PID control. A planner that runs once before each move, in contrast, can afford to try thousands of poses, such as sampling-based planning.

Speed also depends on how much data there is, so it helps to ask how the time grows when the data grows. Take the brute-force way of finding, for every point in a point cloud, which other point is closest to it. That method compares each point with every other point, so with one thousand points that is 499,500 pairs, while with two thousand points it is 1,999,000 pairs. So twice the points means four times the work. A depth picture can have 300,000 points, and this simple method therefore becomes far too slow. The nearest-neighbour search page shows how a k-d tree, which sorts the points into boxes ahead of time, avoids most of those comparisons.

So when you judge speed, ask two things: how long one run takes on your data today, and how much longer it will take if the data grows.

The third section asks about accuracy, and how close is close enough. Speed is only the first question, because an answer that arrives on time is no use if it is wrong. Accuracy is how close a technique's answer is to the truth, and no technique is perfectly accurate, because its input is noisy. So the useful question is how accurate the answer needs to be for what the arm does next.

You work that out from the task, not from the technique. Here is an example. A gripper's fingers open to 80 millimetres and a mug is 70 millimetres wide. So if the gripper comes down centred on the mug, there is 80 minus 70, divided by 2, which equals 5 millimetres of room on each side. This means the mug's position must be right to within about 5 millimetres, or a finger lands on the rim.

Now compare two techniques against that 5 millimetres. A technique that is right to within 1 millimetre passes easily, while a technique that is right to within 10 millimetres fails, however fast it is. And a technique that is right to within 0.1 millimetres is no better for this job than the 1 millimetre one, so the extra time it probably costs buys nothing.

Accuracy also adds up along a chain, because the mug's position passes through the camera model, the camera's calibration, the transform to the base, and the arm's own joints. Each one adds a little error, so if each of four steps adds 2 millimetres, the total can reach 8 millimetres, which is more than the 5 millimetres of room. The calibration page is about removing the largest of these errors.

When you judge accuracy, ask: how much error can the next step accept? Then check the whole chain against that number, not just one technique.

The fourth section is about robustness to noise and bad readings. The accuracy question assumed that the readings are merely noisy, but some readings are worse than that. A technique is robust if it still gives a good answer when some of its input is bad. The building blocks page described two kinds of bad input. First is noise, which is a small error on every reading. Second is an outlier, which is a reading that is completely wrong.

Many simple techniques handle noise well and outliers badly. Here is an example. A depth camera looks along the straight edge of a table and measures 24 points along it. The edge truly rises 0.5 millimetres for every 1 millimetre along it, and starts at a height of 40 millimetres, so most readings are close to that line. However, five of them are 60 to 90 millimetres too low, because of a reflection.

The page shows a diagram of these points. There are blue points along a straight line, and five red crosses far below it representing the outliers. A grey dashed line is fitted to all 24 points and is dragged down by the five wrong readings. A green line comes from a robust method that ignores them and lies on the good points.

Those two lines come from two techniques that answer the same question in different ways.

The grey dashed line is least squares on all 24 points. It finds the line with the smallest sum of squared differences, which is the cost function from the building blocks page. It gives a slope of 0.472 and a starting height of 28.3 millimetres. At the far end of the edge, 300 millimetres along, it says the height is 169.8 millimetres. The truth is 190.0 millimetres. It is about 20 millimetres too low.

The green line is random sample consensus, or RANSAC. It tries many lines, each through two points chosen at random. For each line it counts how many points lie within 8 millimetres of it. It keeps the line that the most points agree with, and then fits it again to just those points. Here 19 of the 24 points agree. It gives a slope of 0.505 and a starting height of 38.5 millimetres. At 300 millimetres it says 190.1 millimetres.

Least squares is pulled down because squaring makes large differences count a great deal, and each outlier is 60 to 90 millimetres off, so its square is very large. RANSAC is not pulled down, because it never lets the outliers vote for the final line.

This does not make RANSAC always better. It is slower, because it tries many lines, and it is random, so two runs can give slightly different answers. It also needs two parameters that least squares does not, as the next section shows. So if your readings have noise but no outliers, least squares is faster and just as good. The least-squares fitting and RANSAC pages compare them in detail.

When you judge robustness, look at real readings from your own camera, and ask whether there are outliers, how many of them there are, and how far off they are. Then test the technique on those readings, not on clean ones.

The next section asks how much tuning it needs. The previous section ended with the two parameters that RANSAC needs, so this section looks at parameters in general. A parameter is a number you choose before a technique runs, and tuning is the work of choosing those numbers. Every parameter is a question someone has to answer, and has to answer again when the scene changes.

Here are the parameters needed by some of the techniques this book has already mentioned. First, the depth rule on the first page has one: the 580 millimetre limit. Second, the RANSAC line just discussed has two: the 8 millimetre distance that counts as agreeing, and how many lines to try, which was 200. Third, a PID controller has three per joint, so eighteen on a six-joint arm. Finally, a colour mask in the thresholding and colour masks page has six: a low and a high limit for each of three colour numbers.

A parameter is easy to tune if it has a physical meaning you can measure. For example, the 580 millimetre limit is easy, because you measure the table's distance and subtract a margin. A parameter is hard to tune if it has no clear meaning, or if it interacts with other parameters, and changing one PID number changes how the other two behave.

Parameters also go stale, because the 580 millimetre limit is right for only one table height. Move the camera 50 millimetres higher, and every depth reading grows by about 50 millimetres, so the limit is wrong. In the same way, a colour mask tuned in the morning may fail in the evening light.

When you judge tuning, count the parameters and ask of each one: can I measure it, or must I guess and test it? And what change in the scene would make it wrong?

The sixth section covers when to switch to a learned model. The fifth question is whether a written technique is the right kind of tool at all. The page on programmed, not learned showed a written rule failing on a glass. Book 6 explains the alternative: a model learned from examples.

The main thing that decides is how much the scene varies. If the objects, their places and the light are the same every time, a written rule can describe them exactly. However, if they change a lot, a rule cannot list every case.

The page shows a diagram with a line of arm jobs, from "go to a pose taught by hand" on the left to "fold a towel" on the right. The left third is marked for written techniques and the right third for learned models. Jobs on the left, such as finding the flat table top, are done well by written techniques. Jobs on the right, such as grasping objects never seen before, are usually done better by learned models. Jobs in the middle often use both.

There are four signs that a written technique is running out. First, you keep adding special cases, and each one breaks another. Second, you cannot describe the failures in words. You can only say "it looks wrong". Third, one set of parameters cannot suit all the scenes you see in a day. And fourth, the thing to recognise has no simple shape or colour, such as "a mug of any kind" or "a good place to grab a towel".

On the other hand, there are four signs that a written technique is still the right choice. First, the job is geometry or arithmetic, such as a transform or a camera model. Second, the answer must be exact, and you must be able to check it. Third, it must run in a millisecond, on a small processor. And fourth, you have no examples to learn from, or cannot afford to collect them.

Most arms mix the two. A learned model does the part that needs variety, such as object detection to find the mugs in a colour picture. Written techniques, meanwhile, do the parts that need exactness: turning pixels into positions, planning the path and driving the motors. So when you switch, you usually replace one step in the chain, not the whole chain.

The seventh section gives a worked choice: finding the table top. Now that all five questions have been described, this section runs them on one real job to show how they work together. The job is to find the height and tilt of the table top, from a depth camera on the arm's wrist. Every later step uses the table top, because it tells the arm how low the gripper can go, and it lets the program remove the table points so that only the objects are left.

There are four candidates for the job, and they run from a hand measurement to a learned model. Candidate one is to measure the table once by hand, and write the height into the program. Candidate two is to fit a plane to all the depth points with least squares. Candidate three is to fit a plane with RANSAC, which ignores points that are not on the plane, such as mugs. Candidate four is to use a learned model that labels which pixels are table, such as a segmentation model.

The page includes a table that runs the five questions on each candidate. Candidate one, measured by hand, is fast enough with no work at run time, and needs no tuning, but it is only accurate while nothing moves, and fails the robustness question as soon as the table or camera moves. Candidate two, least squares on all points, is fast enough and needs no tuning, but it is not accurate or robust because the mugs pull the plane up. Candidate three, the RANSAC plane, passes all five questions. It is fast enough at camera rate for a downsampled cloud, it is accurate, and it is robust because the mugs are treated as outliers. It requires tuning a distance and a number of tries, and does not need learning. Finally, candidate four, learned segmentation, is usually fast enough with a graphics card, but it is only as good as its labels and still needs a plane fit for the height. It is robust on scenes like its training data, but it requires training data and training time.

As the table shows, candidate 1 is simplest, but it fails the robustness question the first time someone moves the table. Candidate 2 fails because the mugs on the table are outliers from the table's point of view. Candidate 3 passes all five, with two parameters that have a physical meaning. Candidate 4 would also work, but it costs training data, and it still needs a plane fit afterwards to get the height as a number.

So candidate 3, RANSAC, is the usual choice for this job. Book 2 uses exactly this approach in the section on removing the plane, then clustering.

The eighth section provides a checklist. The five questions collect into a checklist that tells you what to measure to answer each question, and the sign that the technique fails it.

For the first question, "Fast enough?", you measure the time for one run on real data, and the loop's budget. The sign that it fails is that the loop misses its rate; the arm jerks or the picture lags behind.

For "Accurate enough?", you measure the error against a known truth, such as a ruler or a marker. The sign of failure is that the gripper lands off-centre by more than its room allows.

For "Robust?", you measure the answer on real readings, including shiny, dark or cluttered scenes. It fails if one bad reading moves the answer a long way.

For "Easy to tune?", you measure the number of parameters, and whether each can be measured. It fails if it works after tuning and fails the next day.

Finally, for "Written or learned?", you measure how many special cases you have written, and how varied the scene is. It fails if each fix breaks another case.

Every technique page in this book has a section on where the technique is useful and where it is not, and that section answers these five questions for its own technique. It also names what people use instead when the technique fails.

The next section suggests where to read next. The map of techniques is the next page. It lists all 34 techniques in this book and places them on one arm task. The page on RANSAC explains the robust fit from section 4 in full. The page on running a model on a robot in Book 6 shows the time budget from the learned side. And the section on making it work in Book 2 is about testing perception on real scenes, which is how you answer the robustness question in practice.

The final section is about using it in Python. The checklist turned the five questions into things to measure. This section shows how to measure the first two of them in Python, because speed and accuracy are the two that give you a number, and a number is what settles an argument between two techniques. After this section you should be able to run a candidate technique on your own data and write down how many milliseconds it takes and how many millimetres it is out by.

Only the Python standard library and NumPy are needed, since the time dot perf counter function gives a clock that counts steadily and NumPy summarises a list of errors.

The page shows a short Python script. It defines a function to measure the milliseconds per run of a technique. It runs the technique once first so start-up work is not counted, then records the start time. It runs the technique in a loop for a set number of repeats, such as two hundred, and calculates the average time per run in milliseconds. It then compares this to the time budget, for example checking a RANSAC plane fit against a 33.3 millisecond budget for a 30 Hertz camera. For accuracy, the script takes a list of answers and a list of measured truths in millimetres. It uses NumPy to calculate the absolute errors, and then prints the mean error, the 95th percentile error, and the maximum error.

The libraries do very little here, and that is the point. The time dot perf counter function returns a number of seconds from a clock that never jumps backwards, which an ordinary wall clock can do, and NumPy gives you the mean, a percentile and the worst case of a list of errors in one line each. Everything else is yours.

What you still write yourself is all of the work. You write the technique, you collect the test scenes, and you write the loop that runs one against the other. You also have to obtain the truths, and there is no library for that, because a truth comes from a ruler, a printed marker at a known place, or a part held in a fixture. The third, fourth and fifth questions have no measuring code at all, since robustness means gathering shiny, dark and cluttered scenes on purpose, and counting parameters means reading the technique's own documentation.

What you have to decide is more interesting. The number of repeats matters because one run tells you almost nothing: the first run pays for memory allocation, and a single timing on a laptop varies by tens of percent. The time budget comes from the rate of the loop the technique sits in, which the speed section set out, and that rate is your design choice rather than a fact. The pass mark in millimetres comes from how much room the gripper has, which the accuracy section explains. Finally, you have to decide which of the three accuracy numbers to believe, and the honest answer is usually not the mean, because the mean hides the one scene where the technique failed completely. A high percentile or the maximum is what will decide whether the arm drops something.
