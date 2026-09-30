Image and point cloud processing: an overview.

This page opens the chapter on image and point cloud processing, which is the fourth of the seven families of technique in this book. These are the techniques that clean up and cut up pictures and point clouds, so that separate objects stand out from the surface they are standing on.

The page answers four questions: what this family of techniques is for, and which question it answers for a robot arm. It then says which techniques are in the family and how they differ. Last, it says how the family connects to the other families and to the learned models of Book 6.

It is for a reader who already knows what a pixel, a camera picture, a depth picture and a point cloud are. Book 2 explains all four of those in the section on finding an object in a picture. You do not need to know any of the techniques themselves yet, because each of the next five pages explains one group of them from the start.

The first section covers what this family is for. Everything in this family starts with what the camera gives the robot, which is a picture: a grid of numbers holding one small group of numbers for each pixel. A depth camera also gives a depth picture, which holds one distance for each pixel. So turning every depth pixel into a 3D point gives a point cloud, which is a long list of points that each have an x, a y and a z.

None of these tell the robot where the objects are, because a picture of a mug on a table is only 300,000 or so coloured dots. Some of those dots belong to the mug and most belong to the table, so the robot must first decide which dot is which.

The techniques in this family make that decision with written rules. A rule here is a short, exact test that the program applies to every pixel or every point. Keep the pixel if it is red enough is one such rule, and keep the point if it is more than 10 millimetres above the table is another. Nobody trains these rules on examples. Instead a person writes them, and the computer then applies them the same way every time.

The family has four jobs, done one after the other on each picture. First, pick out the pixels or points that might belong to an object, which gives a mask. A mask is a grid the size of the picture, holding 1 where a pixel passed the test and 0 where it did not. Second, tidy the mask, by removing stray specks and filling small holes. Third, trace the outline of each patch in the mask, so that its shape can be measured. Finally, group the pixels or points into separate objects, with one group per object.

A fifth job joins many pictures together, because a camera on a moving arm sees a different part of the scene in each picture. Combining the pictures into one 3D map of free, occupied and not-yet-seen space therefore lets the arm remember what it cannot see right now.

A diagram on the page shows the first four jobs on one small picture, which is 22 by 30 pixels. The first panel shows the original picture. The next panel shows a colour mask made by asking if each pixel is red. This test keeps 134 pixels, but it also keeps four specks of slightly red table and leaves a hole where a white highlight sits on the first part. The third panel shows the cleaned mask after tidying, where the specks and the hole are gone. The final panels show the outlines and the groups. Because the mask was tidied, grouping finds exactly two objects where the raw mask had held six separate patches.

The next part of the page explains the question this family answers for a robot arm. Those four jobs all serve one purpose. Every technique in this family answers some form of the same question: which pixels, or which points, belong to which object?

A robot arm asks this question before almost everything else it does, and a few examples show why. First, to pick up a part, the arm needs the part's position and size, and both are measured on the part's own pixels or points, never on the table's. Second, to place a suction cup, the arm needs a flat spot well inside the part and away from its edges, and that spot is found on the part's mask. Third, to plan a path that does not hit anything, the planner needs to know which points are obstacles, so the table and each object must be separate groups of points. And fourth, to count the parts in a tray, the program needs one group per part.

The techniques are also fast, because most of them take about a millisecond on a normal processor for a camera picture. That is why they can run on every frame of a live camera, and on the small computers inside the robot.

The chapter then splits the technique pages into two groups. Because the family has those four jobs, plus the fifth one that joins pictures together, this chapter splits it into five pages arranged in two groups. The first group is most used, which means that almost every programmed perception pipeline on a robot arm runs all three of them. The second group is also used, which means that those pages are common but are needed only for some jobs or some set-ups.

The most used pages follow the order of the jobs listed earlier. 

The first page is thresholding and colour masks. It picks out pixels by testing each one against a limit, which can be a brightness, a colour range in hue, saturation and value, or a depth range. It also covers Otsu's method, which chooses the brightness limit from the picture itself.

The second page is morphology and the distance transform. It tidies a mask by shrinking and growing it. It also measures how far each mask pixel is from the nearest edge. That is how it finds the most central point of a part, and how it helps split touching objects.

The third page is clustering. It groups pixels or points into separate objects, using connected components on a mask, and Euclidean clustering and DBSCAN on a point cloud. It also covers voxel downsampling, which thins a point cloud before the grouping, and k-means and mean shift, which find the centre of each crowd of points.

These three are the most used because each one is needed in nearly every pipeline. A mask must be made, then it must be cleaned, and then it must be split into objects before the arm can pick one of them.

The also used pages are needed less often, because most pipelines can finish without them. 

The fourth page is edges and contours. It finds where the brightness changes sharply, traces the outline of each patch, and turns an outline into a few corners or a fitted shape. It also covers the Hough transform, which finds straight lines and circles, such as a cup's rim, in broken edges. Many pipelines only need a mask's centre and size, which clustering already gives, so outlines are needed mainly when the shape itself matters.

The fifth page is volumetric maps. It combines many depth pictures into one 3D map: an occupancy map of free, occupied and unknown space, and distance maps that planners read. A robot with a fixed camera and a clear table often plans straight from the latest point cloud. So the map is needed mainly when the camera moves or parts of the scene are hidden. When it is used, it is usually built for you by a library such as MoveIt.

The first two pages are read best in order, because the second page tidies the masks that the first page makes. Clustering and edges and contours can then be read in either order, since neither one depends on the other. Volumetric maps can be read on its own after the clustering page, which is where voxels are introduced.

The next section compares the techniques. A table lists seventeen techniques side by side, showing what each one takes in, what it gives back, a typical use on a robot arm, and how many numbers you usually have to choose by hand to tune it. 

The techniques take in different types of data. For example, a brightness threshold takes in a grey picture, a colour range takes in a colour picture, and a depth threshold takes in a depth picture. Other techniques take in the masks or point clouds produced by earlier steps. 

The number of parameters you have to choose by hand varies widely. Otsu's method and the distance transform require zero numbers, meaning they adapt on their own. Most techniques, like erosion, voxel downsampling, or finding contours, require just one or two numbers, such as a brush size or a voxel size. However, setting a colour range in hue, saturation and value requires choosing six numbers, which means it needs care whenever the light changes.

Two of those columns matter most when you choose. The first is what goes in, because it tells you which camera you need: a colour camera, a grey camera or a depth camera. The second is numbers to choose, because it tells you how much work it is to make the technique behave in a new setting. A technique with zero numbers adapts on its own, whereas a technique with six numbers needs care whenever the light changes.

The following part explains how the same ideas work on a point cloud. The table just described lists picture techniques and point cloud techniques together. That is possible because most of the techniques were first written for pictures, but almost all of them also have a point cloud form in which the idea is the same. The three pairs below show how a picture technique and its point cloud twin line up.

First, a threshold on a picture keeps pixels whose value is inside a range, and on a point cloud a pass-through filter keeps points whose x, y or z is inside a range, such as higher than 10 millimetres above the table. Second, opening removes lone specks from a mask, and on a point cloud an outlier removal step removes lone points that have too few neighbours. Third, connected components joins mask pixels that touch, and on a point cloud Euclidean clustering joins points that are closer together than a set distance.

A diagram shows the first and last of these on a point cloud of a table with a box and a tall cylinder on it, seen from the side. The left panel shows every point. In the right panel, a height threshold has dropped the table points, leaving them behind in light grey. Grouping the remaining points that lie closer than 15 millimetres to each other then gives exactly two groups, with 47 points on the box and 49 on the cylinder. 

The table under an object is hidden from the camera, so there are no table points there at all, and that is normal. It is also why the table has to be found first, usually by fitting a plane with random sample consensus, or RANSAC. Only then does a height threshold make any sense.

The next section covers how this family connects to the others. Because this family turns the raw numbers from the camera into masks, outlines and groups, it sits between the camera and almost everything else the robot does. That position means it both depends on other families and feeds them.

It depends on two families in particular. First, geometry and cameras turns pixels, frames and joint angles into positions you can trust. Its pinhole camera model turns a depth picture into a point cloud, and it turns a mask's middle pixel into a 3D point the arm can reach. Second, fitting and estimation gets a clean shape or a steady number out of noisy measurements. So it finds the table plane that a height threshold needs, and it fits circles and lines to the outlines this family traces.

Two other families then use its output. Searching and matching finds the closest thing and decides which thing is which. So clustering a point cloud uses nearest-neighbour search inside it, and matching each group to the object seen one frame ago uses assignment. Planning and search finds a way for the arm to get from here to there without hitting anything, so it needs the groups of points, or a volumetric map built from many pictures, as its obstacles.

Book 6 has learned models that do the same job. For example, a segmentation model gives a mask for each object straight from the picture, and a point cloud model labels each point on its own. A learned model copes with cluttered scenes, mixed colours and changing light far better than a written rule. But it needs training pictures, a bigger computer and more time for each frame, and when it fails it is much harder to see why. The page on choosing a technique explains when to switch from one to the other.

The two are often used together, because a learned model gives a rough mask and the techniques in this chapter then tidy it, measure it and split it. The morphology page shows a real example of that pairing.

The final section suggests where to read next. Since the five technique pages do not all have to be read in order, it gives a few starting points. Start with thresholding and colour masks, because it makes the masks that most of the other pages work on. Read volumetric maps when the arm must avoid obstacles that nobody put in its model. The map of techniques shows where this family sits among all seven. Book 2 runs a complete colour-and-depth example with real code in the section on finding an object in a picture, and it describes many more written methods in the page on methods you write yourself. Finally, segmentation in Book 6 is the learned model that does the same job as this whole chapter.
