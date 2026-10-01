3D models: an overview. 

This chapter is about neural network models that work in three dimensions. The last chapter, seeing models, worked on flat pictures, while the models in this chapter work on 3D points and whole scenes instead. So this page says what they are for, which question each kind answers for a robot arm, and how they connect to the rest of the book. 

It is for a reader who has read the first chapter about what models are. You should already know that a model takes some numbers in and gives some numbers out after learning from examples. You do not need to know anything about 3D maths. This is because the page starts by explaining the one new idea the whole chapter uses, which is the point cloud.

The first section explains what a point cloud is. Since the whole chapter rests on this one idea, it is worth building it up from a normal photo. A photo is a flat grid of small coloured squares called pixels, and each pixel says what colour something is without saying how far away that thing is. So a photo of a mug on a table tells you that the mug is there, but not whether it is thirty centimetres away or three metres away.

A depth camera is a camera that also measures distance, because for each pixel it reports how far away the surface in that pixel is. Book 2 explains how depth cameras do this, in the sensors document.

Once you know the direction of a pixel and the distance along it, you know one spot in the room. That spot can be written as three numbers: x, how far it is to the side; y, how far it is forwards; and z, how high it is. These three numbers together are called a point. Do this for every pixel and you get a large collection of points, which is called a point cloud. The word "cloud" only means that the points are scattered in space, with no fixed order and no lines joining them.

A diagram compares a photo of a mug next to the point cloud of the same scene. The photo on the left is a grid of colours. The point cloud on the right is a list of places, and each place is three numbers in metres.

A point cloud has three features that matter for the rest of this chapter. First, it only has points where the camera could see a surface, so the back of the mug has no points because the camera never saw it. Second, the points have no order, which means point number one in the list could be on the mug or on the table. Swapping two rows of the list changes nothing about the scene. Finally, a typical depth camera gives tens of thousands of points or more in one shot. The camera in Book 2's project gives one point per pixel, and it has seventy-six thousand, eight hundred pixels.

A robot arm wants points more than it wants pixels, because a pixel is only a direction while a point is a place. So the gripper has to go to a place, not to a direction.

The next part covers what 3D models are for. Now that a point cloud has a meaning, the models that work on one can be defined. A 3D model in this book is a neural network that takes 3D information in, or gives 3D information out, or both. That information is usually a point cloud, or a set of photos taken from known places around a scene.

The programmed methods in Book 2 already do some 3D work without any learning. For example, they can find the flat table in a point cloud and cut it away. They can also group the points that are left into separate objects. However, those methods only use the distances between points, and nothing else. So they cannot say that a group of points is a mug, or that a part of it is the handle. They also cannot say what the side facing away from the camera looks like.

3D models fill those gaps, because they learn from many examples what 3D shapes usually look like. Then they use that to name points, guess hidden parts, rebuild a whole scene, or attach meaning to places in 3D.

Moving on to the question they answer. Those four jobs sound different, but for a robot arm every model in this chapter answers some version of one question: What is where, in 3D, around the arm, including the parts I cannot see yet?

The arm needs the answer in 3D because its gripper moves in 3D. So a box drawn around a mug in a photo is not enough to pick the mug up. The arm also needs to know how far away the mug is, how wide it is, and where its handle points.

The next section introduces the four kinds of models in this chapter. This chapter has four pages after this one, and each of them answers a different version of that question. A diagram shows four kinds of 3D model, each answering one question about the same mug.

First, point cloud models take a point cloud and say what it is, or which object each point belongs to, and PointNet is the best-known one.

Second, shape completion takes the points of the side the camera saw and guesses the hidden back of the object.

Third, scene reconstruction takes many photos from known places and builds a whole 3D scene that can be viewed from any direction, and NeRF and Gaussian splatting are the two best-known methods.

Finally, 3D feature maps build a 3D map in which every point also carries meaning, so that the arm can be asked where the handle is in plain words.

The pages of this chapter are in two groups, because some of the four kinds come up far more often than the others. The first group, most used, holds point cloud models and scene reconstruction. Point cloud models work on what a depth camera gives you directly, so they are the ones most arm projects meet first. Scene reconstruction, instead, is used widely to build a 3D copy of a work cell or an object. The second group, also used, holds shape completion and 3D feature maps. Those two solve real problems, but fewer projects need them, and many of the models are still research code.

The next part compares the four kinds. A table puts them side by side, showing what goes into each model, what comes out, and how it is trained. For point cloud models, one point cloud goes in, and a name for the cloud or a name for every point comes out. They are trained once on many labelled point clouds. For shape completion, the points of the seen side go in, and the points of the whole object come out. This is also trained once, on many complete 3D shapes. Scene reconstruction takes many photos and where each was taken, and outputs a 3D scene you can view from anywhere. However, it is fitted again for every new scene. Lastly, 3D feature maps take photos or point clouds and a trained image model, and output a 3D map where each point carries meaning. They usually require no new training because they borrow an image model.

A second table explains when a robot arm reaches for each kind. If the arm needs to know which points are the mug and which are the table, use a point cloud model. If it needs to grasp an object from a side the camera cannot see, use shape completion. If it needs to see a shiny or see-through object that a depth camera misses, use scene reconstruction. And if it needs to find the red cup or the handle from a spoken or typed request, use a 3D feature map.

The training differences in the first table matter more than they look. Point cloud models and shape completion are trained once and then used on new objects, but scene reconstruction is different. A NeRF or a Gaussian splat is fitted to one scene, so it has to be fitted again when the scene changes, and the scene reconstruction page explains why.

The next section explains how 3D models connect to the other chapters. Since 3D models are only one family, it helps to see where they sit. The book lists seven families of model, and each one has a one-line job. Seeing models turn a picture into names, boxes, outlines, poses or depth. 3D models work on 3D points and whole scenes instead of flat pictures. Grasp models decide where and how to hold an object. Movement models decide how the arm should move, moment by moment. Language models understand words, and connect words to pictures and actions. World models predict what will happen next if the arm does something. Touch and body models make sense of touch, force and the arm's own body.

3D models sit between seeing and grasping, so they take in from one side and give out to the other.

They take from seeing models, because a depth model can turn a plain photo into a point cloud, and an outline from segmentation can pick out which points belong to one object. 3D feature maps lift the numbers of an open-vocabulary model into 3D.

They give to grasp models, since most grasp models that choose a full 3D grasp take a point cloud as input, and many of them are built on a point cloud model inside.

They give to movement models, because some policies take a point cloud of the scene as their input instead of a photo.

They give to language models, and a 3D feature map is one way to turn "the cup on the left" into a place the arm can reach.

Finally, world models can predict how points will move when the arm pushes something, which is the same kind of input used to look ahead. This is all shown on the map of models page, which displays all seven families together.

The page then suggests where to read next. It recommends starting with point cloud models, because the other three pages in this chapter build on its idea of a model that reads points directly. If you want the deeper, non-learned side of 3D first, Book 2 covers it. The one-box project makes a point cloud from a depth camera, step by step. Programmed methods finds objects in a point cloud without any model at all. And models that measure compares 3D reconstruction methods by how accurate they are, and lists their licences.

The final section is about using it in Python. The first section explained the point cloud, and every model in this chapter takes one or produces one. So before any of those models can run, something has to make a point cloud out of what the camera gives you. This section shows that step in Python, because it is the one piece of code that all four of the following pages assume you already have.

Open3D is the library for it. It is a package for reading, building and handling 3D data, and it is used here rather than writing the geometry yourself because the projection is fiddly to get right and Open3D's version is also much faster.

The page shows a short Python script. First, it loads a depth picture, which holds one distance per pixel in whole millimetres. Next, it sets up the camera's lens numbers, which come from calibrating it once. These include two focal lengths and the pixel the lens looks straight through. Then, it uses Open3D to create a point cloud from the depth image and the camera numbers. During this step, it scales the depth units into metres and throws away anything further away than three metres. After that, it thins the cloud out by down-sampling it into small cubes called voxels. Finally, it extracts the x, y, and z coordinates of every point in metres.

What the library gives you out of the box is the whole of that conversion, plus the steps that usually follow it. Open3D reads and writes the common 3D file formats, thins a cloud out by voxel, finds the table as a flat plane, splits the rest into separate clumps, estimates the direction each surface faces, and lines two clouds up with each other. None of that is a neural network, which is the point worth taking from this section: Open3D is the plumbing that every learned model in this chapter sits on top of, and a great deal of real 3D robot code is nothing but this.

What you still have to write yourself is the camera's numbers and the meaning. The six numbers for the camera come from calibrating your own camera, and the cloud that comes out is in the camera's frame, so moving it into the arm's frame is your code. Beyond that, a point cloud on its own says only where surfaces are, and turning "where surfaces are" into "that is the mug and here is where to hold it" is what the rest of this chapter is about.

What you have to decide is how much detail to keep. The voxel size in the code keeps one point per five-millimetre cube, which cuts a three hundred thousand point camera frame down to a size a model can read. A larger value is faster but loses small features such as a thin handle. You also decide the depth cutoff, because points from the far wall are usually noise for a table-top task. These two numbers change the answer of every model that follows, so they are worth setting deliberately rather than by default.
