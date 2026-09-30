Nearest-neighbour search. This page explains nearest-neighbour search: given a set of points and one more point, find the point in the set that is closest to it. It answers four questions. How do you find the nearest point without measuring the distance to every point? What is a k-d tree, and how is it built and searched? What are the k-nearest and radius versions of the search for? And where does a robot arm use all of this?

The page is for a reader who knows what a point and a point cloud are, and who has read the chapter overview, so no algorithms course is needed to follow it. Instead, every step is shown with a small example on a table top, which builds and searches a real k-d tree. Nearest-neighbour search is the most used technique in this chapter, because the pages on iterative closest point and assignment and matching both call it.

The first section gives the idea in one sentence. Nearest-neighbour search finds the point in a set that is closest to a given point, and a k-d tree makes that fast by cutting space into boxes, so that most boxes can be skipped without looking inside them.

The given point is called the query, and closest usually means the ordinary straight-line distance, which is called the Euclidean distance. So, for two points on a table at x1, y1 and x2, y2, that distance is the square root of x1 minus x2 squared, plus y1 minus y2 squared.

Here is an everyday example, in which you are in a strange town and want the nearest chemist. You could look up the address of every chemist in the country and work out how far each one is, but nobody does that. Instead, you look only at the part of the map around you, because a chemist in another town cannot be the nearest one. This is what a k-d tree lets a computer do: it looks only at the parts of space that could hold the answer.

The next part of the page explains how it works, step by step. It works that idea through on a table that is 600 millimetres wide and 400 millimetres deep, seen from above. Eleven objects stand on it, named A to K, and the gripper tip is above the table at an x coordinate of 430 and a y coordinate of 300. So the question is which of those eleven objects is nearest to the gripper.

The page provides a table listing the positions of the eleven objects in millimetres. For example, object A is at 60, 300, object E is at 300, 150, and object G is at 400, 270. The example is flat, with two numbers per point, so that it fits on a page. While a point cloud from a depth camera has three numbers per point, x, y, and z, every step works the same way in three dimensions. As a result, nothing is lost by drawing the example flat.

The simplest way to answer that question measures the distance from the query to every point and keeps the smallest. This is called brute force, because it uses no cleverness, only work.

A diagram shows the eleven distances, one from the gripper to each of the objects. Object G, at 400, 270, is nearest, and its distance is the square root of 30 squared plus 30 squared, which is 42.4 millimetres. Then comes H, the second nearest, at 50.0 millimetres.

Brute force is always right, and for eleven points it is also fast, because it needs one distance check per point. So for one query against n points, that is n checks. The trouble starts when there are many points and many queries. For example, matching every point of one 3,000-point scan to its nearest point in another needs three thousand times three thousand, which is nine million checks.

Those nine million checks are what a k-d tree avoids, because it is a way of storing points so that a search can skip most of them. The name is short for k-dimensional tree, in which k is the number of coordinates each point has. So that is 2 on this flat table, and 3 for a point cloud.

The tree is built by cutting the space in two, again and again. First, sort the points by x and take the middle one, then draw a line through it, across the x direction, so that every point with a smaller x goes to the left side and every point with a larger x goes to the right side. Second, on each side, sort the points by y, take the middle one, and cut across the y direction through it. Finally, keep going, switching between x and y at each level, or x, y, and z in 3D, until every point has its own cut.

For the table, the first step sorts the eleven points by x, and the middle one of eleven is the sixth, which is E at x equals 300. That is why the first cut is the line x equals 300. Then A, B, C, D, and K go to the left side, and F, G, H, I, and J go to the right side.

The second step then works on each side. On the left, sorted by y, the middle point is C, so the left side is cut at y equals 220. On the right, sorted by y, the middle point is J, so the right side is cut at y equals 240. After that, the third level cuts by x again, and so on, until every point has its own cut.

A diagram shows the result: the table cut into boxes on the left, and the same cuts drawn as a tree on the right. Each circle in the tree is one point, and it owns one cut. So its left branch holds the points on the smaller side of that cut, and its right branch holds the points on the larger side. E is at the top, because it made the first cut, and the tree is four levels deep. Building the tree takes some work, because each level sorts the points. But it is done once, and after that every search uses the same tree.

Once the tree is built, the search walks down it towards the query and then walks back up again. On the way back, it only looks at a box if that box could hold something nearer than the best point found so far.

For the gripper at 430, 300, the search goes like this. First, it checks E. The distance is 198.5 millimetres, which is the best so far, and the gripper's x of 430 is more than E's 300, so it goes to the right branch. Next, it checks J. The distance is 125.3 millimetres, which is the new best, and the gripper's y of 300 is more than J's 240, so it goes to J's upper branch. Then it checks H. The distance is 50.0 millimetres, which is the new best again, and the gripper's x of 430 is less than H's 460, so it goes to H's left branch. Finally, it checks G. The distance is 42.4 millimetres, which is the new best, and G has no branches, so the walk down is over.

Now the search walks back up and asks, at each cut, whether the other side is worth a look. At H, the other side is empty, so nothing there needs checking. At J, the other side is everything below y equals 240, and the gripper is at y equals 300, so anything below that line is at least 60 millimetres away. Since the best so far is 42.4 millimetres, nothing on that side can beat it, and I and F are skipped without measuring them. At E, the other side is everything left of x equals 300, and the gripper is at x equals 430, so anything there is at least 130 millimetres away. That means all five points there, A, B, C, D, and K, are skipped.

The answer is G at 42.4 millimetres, the same as brute force, but the search measured 4 distances instead of 11. A diagram shows the order of the checks, and the boxes that were skipped. A dashed circle has the radius of the best distance found. Since a grey box lies wholly outside that circle, it cannot hold anything nearer than the point already found.

The saving grows with the number of points. Matching every point of a 3,000-point scan to a second scan took 44,425 checks with the tree, about 15 per query, against nine million by brute force. As a rule of thumb, a search in a well-balanced tree of n points checks a number of points that grows like the number of times you can halve n, not like n itself.

The search described so far returns a single point, and two variants of it are used as often as that plain one.

The first is k-nearest-neighbour search, which returns the k closest points instead of one. The walk through the tree is the same, except that it keeps a list of the k best points found so far. Then it skips a box only if the box is further away than the worst of those k.

The second is radius search, which returns every point within a set distance of the query, for example every point within 40 millimetres. As a result, this time the search skips a box only if the box is further away than the radius.

The two answer different questions, and a diagram shows the difference on a cloud that is crowded on the left and thin on the right. In the crowded patch, a 40-millimetre radius holds 88 points, and the 8 nearest points all lie within 10.9 millimetres. In the thin patch, the same radius holds no points at all, and the 8 nearest points reach out to 83.6 millimetres.

So use k nearest when you need a fixed number of points, for example at least a few points to fit a plane through. Use a radius instead when the distance itself means something, for example when points closer than 5 millimetres belong to the same object. Some libraries also offer a mix of the two: the k nearest, but none further than a radius.

The page then provides pseudocode for these steps. Rather than reading the code line by line, here is what it does. The tree-building function takes a list of points and the current depth. It finds the axis to cut on by alternating between coordinates, sorts the points along that axis, and picks the middle point to store at the current node. It then calls itself to build the left branch with the points before the middle, and the right branch with the points after the middle.

The nearest-neighbour search function takes a node, the query point, and the best point found so far. It measures the distance from the query to the node's point and updates the best point if this one is closer. Then it calculates the gap between the query and the cut line along the current axis. It uses this gap to decide which side of the cut the query is on, and searches that near side first. The one step that makes the tree fast happens next: it checks if the absolute value of the gap is less than the best distance found so far. If it is, the far side might hold something nearer, so it searches the far side too. If the gap is larger, the whole far side is skipped without a single distance being measured.

The radius search function works similarly, but it adds any point within the radius to a list of found points, and it checks both sides of the cut if the gap is smaller than the radius.

The next section explains where this is used on a robot arm. Nearest-neighbour search sits inside many other steps, and these are the common places.

First, it is used to find the surface direction at each point of a cloud. To grip a mug, the arm needs to know which way its surface faces at the grip point, and that direction is called the normal. The software takes the 20 or 30 nearest points around a point, fits a small flat patch through them, and takes the direction straight out of the patch. This is done for every point of the cloud, so it needs one k-nearest search per point.

Second, it is used for growing clusters of points into objects. After the table plane is removed, the points that are left belong to the objects on it. A radius search then groups every point with the points within, say, 10 millimetres of it, and those groups with their neighbours, until each group is one object.

Third, it helps in removing stray points. A depth camera gives some points that float in the air, away from any surface, so a point whose nearest neighbours are all far away is probably one of these and can be removed.

Fourth, it is used for aligning a model to a scan. Every round of iterative closest point finds, for each model point, the nearest scan point.

Fifth, it is used for matching a detection to a known object. When a camera sees an object and the software keeps a list of objects it already knows, the nearest known object is the first guess of which one it is.

Sixth, it helps in choosing the nearest object to pick, or the nearest free spot to place. A robot clearing a table often takes the object nearest to the gripper first, to keep each move short.

Seventh, it is used for looking up a stored answer. Some programs store many past situations with the action that worked. For a new object, they describe it with a list of numbers and look up the nearest stored one, so here the points have many coordinates, not three.

Finally, it is used for checking a planned path for collisions. A motion planner asks, for many points along the arm, how far the nearest obstacle point is, and a k-d tree over the obstacle cloud answers each of these quickly. Sampling-based planning also uses nearest-neighbour search to find the nearest node already in its tree.

In all of those places, nearest-neighbour search is exact and fast, as long as the points have only a few coordinates. The search has limits, though, and each limit shows up in a way you can recognise. The page lists the common problems, the signs you see, and what people use instead.

If the nearest point is still far away, you might see a matched point that is 50 millimetres away when the objects are 20 millimetres apart. Instead, people use a maximum distance, rejecting any match further than a set limit.

If there are many coordinates per point, such as 128 numbers describing a patch of surface, the tree search is barely faster than brute force. Instead, people use an approximate search, which is allowed to miss the true nearest point now and then. This happens because in two or three dimensions a box that is far from the query is easy to skip. With 128 coordinates, almost every box is close to the query along at least one coordinate, so almost none can be skipped. The tree then checks nearly every point, and its extra work makes it slower than brute force.

If the cloud changes every frame, building a new tree each time takes longer than the searches. Instead, people use a voxel grid, which cuts the space into equal cubes, or they use brute force on a graphics card.

If points have very different densities, a fixed radius returns hundreds of points in one place and none in another. Instead, people use k nearest, or the mix of k nearest and a radius.

If x, y, and z measure different things, such as position in metres and colour from 0 to 255, the nearest point is decided almost only by the colour. Instead, you should scale each coordinate so that they are comparable before building the tree.

Finally, if there are only a few points and a few queries, the tree takes longer to build than brute force takes to answer. Instead, just use brute force, because it is simpler and fast enough below a few hundred points.

None of this has to be written from scratch, because almost every point cloud and maths library has a k-d tree. The page lists well-known ones. In Python, SciPy provides a KDTree class which is the easiest start, and scikit-learn offers a NearestNeighbors class that chooses brute force or a tree for you. Open3D has a KDTreeFlann class in both Python and C++, which includes a hybrid search for the k nearest within a radius. In C++, the Point Cloud Library uses k-d trees for its normal estimation and clustering. Nanoflann is a fast and small C++ library contained in a single header file, used inside many other libraries. FLANN stands for Fast Library for Approximate Nearest Neighbors, offering exact or approximate searches. For millions of points with many coordinates, FAISS runs on a graphics card. Finally, OpenCV provides matchers that use brute force or FLANN to match image feature descriptors.

Those libraries hide the details, so the next section steps back and answers four questions: what the technique is, what it does for you, why you would choose it over the obvious alternative, and what it costs.

Nearest-neighbour search finds the closest point in a set to a query point. With a k-d tree, it does this while measuring only a small fraction of the points. It lets the software answer "what is next to this point?" hundreds of thousands of times per camera picture, which is what normals, clustering, cleaning, and iterative closest point all need.

The obvious alternative is brute force, which measures every distance, and it is simpler, needs no building step, and is always exact. That is why it is the right choice for a few hundred points or fewer, or for a single query. The tree wins instead when there are many queries against the same set. The second alternative is a voxel grid, which cuts space into equal cubes and looks only in the cube around the query and its neighbours. A grid is quicker to build, and it is good when the points are spread evenly. But it is poor when the density varies, because the cube size cannot suit both the crowded and the thin places.

The costs are these: building the tree takes time, so a tree is worth building only when it will answer many queries. A tree built on one frame's cloud is out of date on the next frame, so a live pipeline builds a new tree every frame. The tree must be rebuilt, not just updated, if many points change, and it helps only for points with a few coordinates. So for long lists of numbers, such as image feature descriptors, you need an approximate search, and you accept that it will sometimes return the second-nearest point.

Since this whole page describes a hand-written method, the obvious question is whether a learned model could take it over. No learned model does, because the search gives the exact answer to a plain question, and a network could only guess that answer. Instead, learned models use the search themselves. For example, point cloud models like PointNet++ collect the points within a small distance of each centre, and DGCNN links each point to its nearest neighbours. So both of those models run this search inside the network. The k-nearest neighbours learning method is built on it too: it predicts by copying the answers of the most similar stored examples.

The final section explains where this topic leads next. Iterative closest point uses nearest-neighbour search in every round to line a model up with a scan. The topic of assignment and matching shows why taking the nearest is not enough when two objects compete for one partner. Clustering uses radius search to group points into objects. Least-squares fitting fits the plane through each point's neighbours to get its normal. And tracking and association uses nearest neighbour with a gate to match objects over time.
