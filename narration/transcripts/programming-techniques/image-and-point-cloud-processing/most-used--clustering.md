Clustering. This page explains how a program splits a mask or a point cloud into separate objects. It answers four questions, and the first two are about grouping things that lie close together: how a program numbers the separate blobs in a mask, and how it groups 3D points into objects by how close they are. The other two ask how DBSCAN does the same while also marking stray points as noise, and why a point cloud is usually thinned out onto a grid of small cubes before any of this runs. A later section then adds two methods that look for the centre of each crowd of points instead. Those two are k-means, which must be told how many groups there are, and mean shift, which is not.

It is for a reader who already knows what a mask and a point cloud are. A mask is a picture in which each pixel is either "object" or "not object", and the page on thresholding and colour masks makes one. A point cloud is a list of 3D points, one for each depth pixel, that a depth camera measures on the surfaces in front of it.

Clustering is the step that turns "these pixels, or these points, are not table" into "this is object 1, this is object 2 and this is object 3". Almost every programmed perception pipeline on a robot arm needs it, because the arm picks one object at a time.

The first section gives the idea in one sentence. The whole technique fits into one sentence, and the rest of this page fills that sentence in. Clustering puts two pixels or two points in the same group whenever they are close enough to each other, and it keeps doing so until every group stops growing.

For an everyday example, scatter some rice, some lentils and a few coins on a dark table and look at it from above. You see three heaps and a few loose grains, and you do not need to know what rice is in order to see those heaps. You see them because the grains in one heap touch each other, while there is bare table between one heap and the next. Clustering uses the same rule, so it does not know what the objects are, and it only knows which points are near which.

This is why clustering works on objects the robot has never seen before. It is also why it fails when two objects touch, because then there is no bare table between them.

The next part of the page explains how it works. That one rule takes three different forms, so this section covers three grouping methods and one preparation step. Connected components works on a mask, which is a grid of pixels, whereas Euclidean clustering and DBSCAN work on a point cloud, where the points have no grid. Voxel downsampling then thins a point cloud before it is clustered.

A point cloud of a table scene normally goes through two steps before clustering. First, points that are too far away are cut off. Second, the table itself is found and removed, usually with RANSAC. What is left is a set of points that are not table, and those are the points that clustering splits into objects.

The first method is connected components, which gives every separate blob in a mask its own number. Two object pixels belong to the same blob if you can walk from one to the other by stepping only on object pixels.

So the only choice left is what counts as a step. With four-connectivity you may step up, down, left or right, while with eight-connectivity you may also step diagonally. The difference matters when two blobs touch only at a corner.

The method itself is a flood fill, which is the same thing as the paint-bucket tool in a drawing program. The code for this creates a grid of zeros to hold the labels. It then scans the mask row by row. When it finds an object pixel that has not been labelled yet, it gives it a new number, and uses a queue to look at all its neighbours. If a neighbour is also an object pixel and has no label, it gets the same number and is added to the queue. This continues until the queue is empty, meaning the whole blob is found.

The diagram shows a worked example of a mask ten pixels wide and seven high, labelled both ways. Each coloured square is an object pixel, and the number on it is the label the flood fill gave it.

With four-connectivity the program finds six blobs, because three of the blobs form a diagonal line of pixels. They touch only at corners, so four-connectivity keeps them apart. With eight-connectivity the diagonal steps are allowed, so these three join into one blob and the program finds four instead. Neither answer is wrong, so the choice depends on the job. You choose eight-connectivity when a thin diagonal part, such as a wire, should stay in one piece, and four-connectivity when objects that touch only at a corner should stay apart. OpenCV and scikit-image use eight-connectivity by default, while SciPy uses four-connectivity, so check which one your library uses.

Once each blob has a number, the program can measure each one, giving its area in pixels, its bounding box and its centroid. It then throws away blobs that are too small to be an object, so this size filter removes the specks of noise left over from the threshold.

The flood fill visits each pixel a fixed number of times, so its time grows in step with the number of pixels. This means that on a camera picture it takes about a millisecond.

The second method is Euclidean clustering, which finds groups of nearby points. A point cloud has no grid, so "neighbour" cannot mean "the next pixel" any more. Instead, two points are neighbours if the straight-line distance between them is below a chosen value, and that value is called the cluster tolerance. The word "Euclidean" just means this ordinary straight-line distance.

Euclidean cluster extraction is then the same flood fill as before, with that new meaning of "neighbour". The code starts a new group for an unlabelled point, then uses a queue to find all points within the cluster tolerance. It adds them to the group and the queue, and keeps going until the group stops growing. Finally, it throws away every group with fewer than a minimum number of points.

Finding each point within the tolerance is a radius search. Written simply, it compares the current point with every other point, which is slow for a large cloud. So real libraries build a k-d tree first, and then each search only looks at nearby points. This is explained more fully on the page about nearest-neighbour search.

The diagram shows a worked example of points left on a table after the table plane was removed, seen from above. There is a round cup, a box, a small block and seven scattered stray points, which is 323 points in all. The points on each object are about six millimetres apart, with a little random noise, and the objects are at least 43 millimetres apart. The left panel shows the points before clustering, with a ten-millimetre circle round three points of the block. The right panel shows the result, with the size of each cluster written on it.

With a tolerance of ten millimetres, the flood fill first finds nine groups: the box with 153 points, the cup with 126, the block with 37, one pair of stray points and five single stray points. A minimum size of ten points then throws away the six small groups, so the result is three clusters, which is right. These numbers come from running the code behind the picture on these points.

The third method is DBSCAN, which groups nearby points with a noise rule. Euclidean clustering has one known weakness, which is that it chains. If A is near B and B is near C, then A, B and C are one group, even if A and C are far apart, so a thin line of stray points between two objects joins them into one cluster. Such lines are common, because depth cameras make stray points along the edges of objects, and a cable or a speck of dust can lie between two parts.

DBSCAN, short for density-based spatial clustering of applications with noise, fixes this with one extra rule. It sorts every point into one of three kinds, using a radius called eps, which is the same idea as the tolerance, and a count called min pts. First, a core point has at least min pts points, counting itself, within eps. It sits in a crowded area, such as the middle of an object's surface. Second, a border point is not a core point, but it lies within eps of a core point. It sits on the edge of a crowded area. Finally, a noise point is neither. It sits alone.

Clusters then grow as Euclidean clusters do, with one change: a cluster only keeps growing from core points. So a border point joins the cluster, but the search does not continue from it, and noise points join nothing at all. The code for this first counts the neighbours for every point to find the core points. Then it runs the flood fill, but only adds a point's neighbours to the queue if that point is a core point.

The diagram shows DBSCAN run on the same 323 table points, with eps of ten millimetres and min pts of five. Filled dots are core points, open circles are border points, and crosses are noise. A red circle shows the ten-millimetre radius round one core point.

DBSCAN finds the same three clusters, of 153, 126 and 37 points. Of the 323 points, 305 are core points, 11 are border points and 7 are noise. The border points sit on the corners and outer edges of the objects, because a point there has fewer neighbours. The seven noise points are exactly the stray points that Euclidean clustering removed with its size filter, so here the two methods agree.

However, they disagree when stray points form a bridge. The next diagram shows two blocks 30 millimetres apart with a line of four stray points between them. The same 132 points and the same ten-millimetre distance give one cluster under Euclidean clustering, but two clusters under DBSCAN.

The stray points are about seven millimetres apart, so each one is within ten millimetres of the next. Euclidean clustering therefore walks along the line from one block to the other, and it reports one cluster of 132 points. DBSCAN counts neighbours first, and three of the four stray points have only three points within ten millimetres, counting themselves, which is below the min pts of five. So they are not core points, and the search cannot pass through them. This means DBSCAN reports two clusters of 65 and 66 points, and marks one point as noise.

DBSCAN's min pts looks as though it does two jobs at once, and Book 2 warns about mixing them. It is a noise filter, which decides whether a point sits in a crowded area, so it is not a size filter for whole objects. This means a program still throws away clusters that are too small, as a separate step. Book 2's section on choosing the grouping distance works through both numbers for a real camera.

The preparation step is voxel downsampling. A depth camera with 640 by 480 pixels gives up to 307,200 points per picture, and clustering them all is slow. It is also not needed, because two points one millimetre apart on the same surface tell the program nothing new. So the cloud is thinned out first.

Voxel downsampling divides space into small cubes of equal size, and each cube is called a voxel, short for volume pixel. Every cube that holds at least one point is then replaced by a single point, which is the average of the points inside it. The code calculates which cell each point falls into, groups the points by cell, and returns the average point for each occupied cell.

The diagram shows this in 2D, seen from above, for a dense scan of a mug and a box. The left panel has 3,000 points, while the right panel has one average point for each occupied ten-millimetre cell, which comes to 68 points.

A table shows how the cell size sets the number of points left from the same 3,000. With cubes of five millimetres, 245 points remain, which is 8.2 percent of the original. With ten-millimetre cubes, 68 points remain, which is 2.3 percent. With 20-millimetre cubes, just 26 points remain, which is 0.9 percent.

Downsampling does three useful things for clustering. First, it makes clustering much faster, because there are far fewer points to search through. Second, it makes the point spacing even, so one tolerance works everywhere: near the camera the points are crowded and far away they are sparse, and the grid removes that difference. Finally, it averages away some of the depth noise as well.

It also sets a limit on the tolerance. After downsampling, the points on one surface are about one cell apart, and up to one cell diagonal apart. A cube of side ten millimetres has a diagonal of ten times the square root of three, which is 17.3 millimetres. So the cluster tolerance must be larger than that, or one object will break into several clusters. The page on singulation and pre-grasp manipulation works through this link between the cell size and the tolerance, using the settings from the Point Cloud Library's own tutorial.

Every method so far rests on one number, because the tolerance, or eps, is the setting that decides the result. It must lie between two limits. First, it must be larger than the gaps between points on one object. If it is smaller, one object breaks into many small clusters. Second, it must be smaller than the gap between two objects. If it is larger, two objects join into one cluster.

A table shows this on the 323 table points, with Euclidean clustering and a minimum size of ten. With a tolerance of five millimetres, the program keeps no clusters and drops all 323 points. At six millimetres, it keeps 11 pieces ranging from 47 down to 10 points, and drops 114 points. From eight millimetres up to 20 millimetres, it keeps exactly three clusters of 153, 126, and 37 points, and drops 7 points. At 30 millimetres, it keeps two clusters, and at 50 millimetres, everything joins into one cluster of 322 points.

At five millimetres and six millimetres the tolerance is below the point spacing, so the objects shatter. From eight millimetres to 20 millimetres the answer is right and does not change, whereas at 30 millimetres the cup and the box join, together with two stray points, and at 50 millimetres everything joins. So the wide range from eight millimetres to 20 millimetres with the same answer is what you look for when you tune, and you pick a value in the middle of it. The robot-arm-projects repository explains the same two limits for glasses on a table, in plain words, on the page about clustering on the table.

One more trick helps a great deal, because objects on a table all stand on the same plane. If the program first flattens the points onto that table plane and clusters in 2D, then the height of the objects no longer matters. So a tall object and a short one next to it are compared only by the gap between them on the table.

The next section is about finding the peaks, using k-means and mean shift. Every grouping method in the previous section uses one rule, which is that two points are in the same group if a chain of close neighbours joins them. This section covers two methods with a different rule, because they look for centres, meaning places where points crowd together. Each point then belongs to the centre it is nearest to, or to the centre it climbs to.

The two methods differ in one important way. K-means must be told how many groups to find, whereas mean shift finds the number for itself. A later section says that k-means is the wrong tool for counting objects, because on a robot the number of objects is usually the thing you want to find out. That is still true. However, there are jobs on a robot arm where the number of groups is known in advance, and there k-means is the simplest tool. There are also jobs where you want the crowded middle of each group rather than the whole group, and mean shift is made for those.

For an everyday example, imagine a school with three buses, where each child must walk to one bus stop. K-means is the planner who is told to place three stops, and the planner puts the stops where they make the total walking shortest. Mean shift is what happens with no planner at all. Each child walks towards where most other children are standing, again and again, until the children stand in a few tight crowds. So the number of crowds is whatever it turns out to be.

K-means has one setting, which is k, the number of groups, and it works in rounds. First, choose k starting centres. The simplest way is to pick k of the points at random. Second, put every point in the group of its nearest centre. Third, move each centre to the average of the points in its group. Finally, repeat the second and third steps until the centres stop moving. The code for this picks random centres, assigns each point to the nearest one, calculates the new average for each group, and loops until the centres stay in the same place.

The diagram shows a worked example on a job where k is known in advance. A camera looks at red and blue parts on a grey table, and the program must find the three colours in the picture, so that it can build a colour mask for each kind of part. Each pixel's colour has a red amount and a blue amount, each from 0 to 255. So each pixel can be drawn as one point, with its red amount across and its blue amount up. The picture has 500 pixels: 300 of table, 120 of red parts and 80 of blue parts. In each panel of the diagram, crosses are the centres and each dot is coloured by the centre it is nearest to.

The random start here is poor, because it picks one red pixel and two blue pixels, and no table pixel at all. After the first round, the orange centre has moved from its starting position towards the middle, because most of its group was table pixels. The blue centre has also moved, pulled towards the table. After three rounds the centres have settled into the middle of the three colours, and a fourth round changes nothing, so the method stops. The groups then hold exactly 120, 80 and 300 pixels, which is one group per real colour.

A start can be so poor that k-means stops at a wrong answer. Out of ten different random starts on these pixels, eight give the right answer, while the other two end with two centres inside one colour and one centre between the other two colours. The fix is simple, because you can run k-means several times from different starts and keep the answer with the smallest spread, which is the sum, over all pixels, of the squared distance to their centre. Libraries do this for you, and they also choose the starts more carefully, with a method called k-means plus plus that picks starting centres far apart from each other.

The next diagram shows what happens when k itself is wrong, and each panel keeps the best of ten starts. With k equals two, the blue parts are lumped in with the table, and the spread is 640,122. With k equals three, each colour is one group, and the spread drops to 108,302. With k equals four, the grey table is cut into two halves, and the spread drops again, to 89,061. So a smaller spread does not mean a better answer, because the spread always falls as k grows, until every pixel is its own group. The usual sign of the right k is where the spread stops falling steeply. So here the fall from 640,122 to 108,302 counts as a big drop, while the fall from 108,302 to 89,061 is a small one.

Mean shift has one setting too, but it is a distance rather than a count, and it is called the bandwidth or the window. The method treats the points like a hilly landscape, where the ground is highest where the points are most crowded. So from each point it climbs uphill until it reaches a top, which is called a peak. First, put a round window of the chosen radius on a starting point. Second, move the window's centre to the average of all points inside the window. Third, repeat that step until the window stops moving. Where it stops is a peak. Fourth, do this from every point. Peaks that end up very close together are one peak. Finally, each point belongs to the peak it climbed to.

The average of the points in the window always lies a little further into the crowd than the window's centre, because more points sit on the crowded side. This means every step moves uphill. The code loops over every point, finding the points within the window, moving to their average, and stopping when the step size is tiny. It then checks if this new peak is close to one it already found, and either merges it or adds it to the list.

The diagram shows a worked example, in which a grasp model looked at a table with a mug, a box and a small block. It proposed 150 grasp centres, seen from above and measured in millimetres: 70 round the mug, 45 round the box, 20 round the block and 15 scattered at random. The arm wants one grasp per object, at the middle of each crowd of proposals.

The picture follows one climb, with a window of radius 30 millimetres, and it starts between the mug and the block. The average of the points in the first window is a small step towards the mug. The next window holds more mug points, so the next step is bigger. After a couple more steps, the window stops moving. The mug's proposals were spread round a specific point, and the peak is within two millimetres of it.

Run from all 150 points with the same 30-millimetre window, mean shift finds seven peaks, and the three largest are reached from 72, 49 and 23 points. They lie at the centres of the mug, the box, and the block. The other four peaks are reached from only one or two points each. This is because they are stray proposals with no crowd round them, so a size limit throws them away, just as with the earlier methods.

The window is the one number that matters here, and the next diagram runs the same points with three different windows. Coloured dots belong to peaks reached from ten or more points, and grey dots belong to the small peaks.

A table gives the full result for six windows. With a ten-millimetre window, mean shift finds 20 peaks, and five of them are reached from ten or more points, meaning the mug and the box each split in two. With windows of 20, 30, 45, and 60 millimetres, it consistently finds exactly three large peaks. With a 90-millimetre window, it finds only one peak, located between the objects.

A window from 20 millimetres to 60 millimetres gives the three right crowds, and that wide, steady range is what you look for, as with the tolerance for Euclidean clustering. A window that is too small splits one crowd into several, whereas a window that is too large joins everything into one peak, which may lie on bare table between the objects.

K-means therefore fits the jobs where the number of groups is fixed in advance by the job itself. First, finding the colours of a known set of parts. As in the example, k-means finds the k main colours in a picture. Their centres give the colour ranges for the masks on the thresholding page, and they adapt when the light changes. Second, choosing k spread-out options. A planner may want five different approach directions, or four camera viewpoints, out of hundreds of candidates. K-means on the candidates gives k groups, and the program takes the best candidate from each. Finally, splitting a pile you have already counted. If a weighing scale or a barcode says the tray holds exactly three parts, k-means with k equals three splits the tray's points into three groups, even where connected components sees one blob.

Mean shift, by contrast, fits the jobs where you want the crowded middle and the count is unknown. First, merging many proposals into a few. A grasp model, an object detector run on several frames, or several camera views each give many nearby guesses for the same object. Mean shift turns each crowd of guesses into one answer at its middle, as in the example. Second, finding vote peaks. Some pose models let every pixel of an object vote for where the object's centre is. Mean shift finds the peak of those votes. It is the same job as finding the peak in the Hough transform's vote table, without a table of cells. Finally, following a coloured object in a video. OpenCV's mean shift and CamShift climb a picture that holds, for each pixel, how well its colour matches the object. Started at the object's last position, the window climbs to its new position in each frame.

K-means fails in four ways. With the wrong k, objects merge or split, as in the picture earlier. From a poor start it can also stop at a wrong answer, and you would see a different answer on each run, so use k-means plus plus starts and several runs. It expects groups that are round and of similar size. So a long thin object such as a pen gets split, and a big group steals points from a small one next to it. Finally, a few far-away points pull a centre away from its crowd, because every point counts in the average. So for objects on a table, the flood-fill methods are usually the better choice.

Mean shift fails in three ways. With a poor window, peaks split or merge, as the table showed. It is also slow on large clouds, because each step of each climb searches all the points, so it is run on a few hundred proposals rather than on 300,000 camera points. So downsample first, or start climbs only from a grid of seed points. Finally, a peak can lie between two objects when the window is large, as in the 90-millimetre example. So always check a peak against the points near it before sending the arm there.

OpenCV provides k-means, with a setting for k-means plus plus starts and several runs, as well as mean shift and CamShift for following an object in a video. scikit-learn provides k-means, which uses k-means plus plus and several runs by default, a mini-batch version for very many points, and mean shift, with a function to suggest a window from the data. SciPy also provides k-means.

The next section covers where clustering is used on a robot arm. Both families of method serve the same need, because clustering is used wherever a program has "not background" and needs "separate objects".

First, the table-top pick pipeline. Take the depth picture as a point cloud, downsample it, remove the table plane with RANSAC, cluster the rest, and pick the cluster nearest the gripper. This is the most common programmed perception recipe for arms. Book 2 describes it, and the tools and libraries page shows it as real Open3D code.

Second, counting objects. The number of clusters is the number of objects. A tray check can compare it with the number of parts that should be there.

Third, splitting a colour mask into objects. After an HSV threshold finds red pixels, connected components splits them into one blob per red block, and the program measures each blob's centre.

Fourth, checking whether objects touch. If two objects the robot knows are there come back as one cluster, they are closer than the tolerance. The arm can then push them apart before it grasps, as the singulation page describes.

Fifth, removing noise before other steps. DBSCAN's noise points, or clusters below the minimum size, are thrown away before fitting shapes or computing grasps. This stops a stray point from moving an object's centre.

Sixth, building a map of obstacles. A motion planner often keeps the scene as a grid of occupied voxels. Voxel downsampling is the same operation, and the voxels it produces can be passed straight to the collision checker used by the sampling-based planners. The page on volumetric maps explains how such a map is built from many depth pictures.

Finally, grouping detections over time. When several camera views each see an object, their 3D centres form small groups in space. Clustering those centres gives one position per object, ready for assignment and matching.

The next section explains where it works, and where it does not. All of those uses share the same conditions, because clustering works best when objects stand apart on a known surface, the depth measurements are good, and the objects are about the same size. So it fails in a few common ways. A table lists what goes wrong, what you would see, and what people use instead.

If objects touch or stand closer than the tolerance, one cluster is twice the expected size, or has a strange shape. Instead, push them apart first, use the distance transform and watershed on the morphology page, or use a learned segmentation model.

If the tolerance is smaller than the point spacing, one object comes back as many small clusters. To fix this, raise the tolerance above the voxel diagonal, or use a finer voxel size.

If stray points bridge two objects, the two objects join under Euclidean clustering. Instead, use DBSCAN with a minimum points setting that stray points cannot reach, or a statistical outlier filter before clustering.

If point density varies a lot, for example between near and far objects, far objects break up, or near objects join. Instead, use voxel downsampling first, or use HDBSCAN, which is a version of DBSCAN that adapts to density.

If the table plane was not fully removed, every object joins the table's leftover edge into one large cluster. To fix this, remove points a few millimetres above the plane as well, and crop to the work area.

For glass or shiny objects, the object has few or no depth points, so it is missing or broken into pieces. Instead, look for the hole in the depth picture, as Book 2 describes, or use a colour picture with a trained model.

Finally, if one object has two parts with a gap, such as a mug and its handle, the handle becomes its own small cluster. To fix this, merge clusters whose bounding boxes overlap, or use a larger tolerance if objects stand far apart.

The next section lists libraries that provide it. Because those failures are well known, so are the methods themselves, and every method on this page is available in well-known libraries.

OpenCV, used from C++, Python, and Java, provides connected components to label a mask, and can also return each blob's area, bounding box and centroid. It also provides k-means, mean shift, and CamShift.

SciPy, in Python, provides connected components on a NumPy array of any number of dimensions, so it also works on a voxel grid.

scikit-image, in Python, provides labelling and measuring for each blob.

Open3D, in Python and C++, provides DBSCAN on a point cloud, returning a label for each point with minus one for noise. It also provides voxel downsampling with one average point per voxel.

The Point Cloud Library, or PCL, in C++, provides Euclidean clustering with a tolerance, a minimum size and a maximum size, using a k-d tree for the radius search. It also provides voxel downsampling, and clustering with extra rules like similar colour or surface direction, so touching objects can sometimes be split.

Finally, scikit-learn, in Python, provides DBSCAN and its density-adapting version, HDBSCAN, on any array of points. It also provides k-means and mean shift.

The next section asks why clustering, and what it costs. With the libraries in hand, the remaining question is when to reach for clustering at all. So this section answers the four standard questions: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

Clustering is a set of flood-fill rules that group pixels or points by how close they are. Connected components does it on a grid of pixels, while Euclidean clustering does it on 3D points with a distance. DBSCAN then adds a rule that keeps stray points out, and voxel downsampling prepares the points so that the other steps run fast.

What it does for you is split "not background" into separate objects without knowing what those objects are. So it works on a part the robot has never seen, on the first day, with no training data at all. It has one main setting, the distance, and that setting can be worked out from the camera's point spacing and the smallest gap between objects.

There are two obvious alternatives. The first is k-means, which is the clustering method most people meet first, and it must be told how many groups to find. On a robot, the number of objects is usually the thing you want to find out, so k-means is the wrong tool for that job. However, Euclidean clustering and DBSCAN find the number for themselves. K-means is still useful when the number of groups is fixed by the job, such as the colours of a known set of parts. The second alternative is a trained segmentation model or point cloud model.

Against all that, clustering merges objects that touch, and nothing in the method itself can fix that. You must choose the tolerance, the minimum size and the voxel size, and they depend on each other and on the camera's distance from the table. It also needs good depth, so glass and shiny metal are hard. And a radius search on a large cloud is slow unless you downsample first and use a k-d tree.

The next section looks at the learned alternative. That second alternative is worth a closer look, because two kinds of model in Book 6 do this job. A segmentation model gives one mask per object in the colour picture, and the depth points inside each mask become that object's points. A point cloud model names every 3D point directly. Either one can split objects that touch, which clustering cannot do, and it can also say what each object is. However, a model needs labelled training data and a computer that can run it, and it only knows the kinds of object it was trained on. So choose clustering when objects stand apart, or when the robot can push them apart, and choose a model when touching objects are the normal case. Book 6's Gaussian mixture models are the learned cousin of k-means: each cluster becomes a soft, stretched blob, and every point gets a chance of belonging to each cluster instead of one hard answer.

The final section suggests where to read next. The previous page is edges and contours. It traces the outline of each blob that connected components finds. The page on morphology and the distance transform tidies a mask before labelling it, and can split two touching blobs that clustering would merge. The page on nearest-neighbour search explains the k-d tree and the radius search that make clustering fast. The page on RANSAC removes the table plane before clustering. The chapter overview compares all the techniques in this chapter. Book 2's section on methods you write yourself goes deeper into choosing the grouping distance for a real camera, and the section on singulation and pre-grasp manipulation covers what the arm does when objects touch. Finally, the diagrams on this page are drawn by Python scripts in the documentation folder, which can be run to print the exact numbers used in the examples.
