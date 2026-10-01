Grasp models. This chapter is about models that decide where and how to hold an object. A robot arm can see a mug on a table, and it can move its gripper to any point it can reach, but neither of those tells it where to put the fingers. So a grasp model is what answers that question.

This overview of the chapter answers four questions. What is a grasp model for, and what does its answer look like? What kinds are there, and how do they differ from one another? And how do grasp models connect to the other kinds of model in this book?

It is for a reader who has read the pages on what a model is and how a model learns. Because a grasp model usually starts from the same pictures, it helps to have read the seeing models overview as well. Every new word is explained where it first appears.

The first section explains what a grasp model is for. As the introduction said, grasp models decide where and how to hold an object, and this part says why that decision is hard enough to need a model.

For example, think about how you pick up a mug yourself. You do not think hard about it, but you still make several choices. You choose which part to hold, which is the handle, the body or the rim. Then you choose which way your hand comes in, either from above or from the side, and how wide to open your fingers before they close. A grasp model makes those same choices for a robot gripper.

The question it answers is this: where should the gripper go, which way should it face, and how wide should it open, so that the object stays in the gripper when the arm lifts it?

A robot arm needs this answer before it can pick anything up. For a small number of known objects a person can write the answer down by hand, and the choosing a grip document in Book 3 shows how. Instead, a grasp model is for the case where nobody can write the answer down, because the objects are new, mixed and lying in any position. The usual example of that case is a box of mixed shopping.

The next part covers what a grasp is. Since a grasp model has to answer the question above, it helps to see exactly what its answer contains. A grasp is one complete instruction for the gripper, and it has three parts.

First, a position, which is the point in space where the middle of the gripper's fingertips should end up. Second, a direction, which is which way the gripper faces as it comes in, and which way its fingers close. And finally, an opening width, which is how far apart the fingers should be just before they close.

A gripper here means the two-finger kind, called a parallel-jaw gripper because its two fingers stay parallel as they close, and each finger is called a jaw. Some pages also cover a suction cup, which holds an object by sucking air out from under a soft rubber cup.

However, different grasp models give this answer in different forms. Some give a rectangle drawn on a picture, some give a full position and direction in 3D, and some give a spot where a suction cup should go. Some do not give a grasp at all, and instead they take a grasp that something else proposed and give it a score. A diagram here shows these four kinds of answer on simple objects. From left to right, the drawing shows a rectangle on a picture seen from above, a full pose that comes in from the side, a spot on a box where a suction cup will seal, and one grip with a score of zero point nine one next to it.

The third section is about the label every grasp model learns from. Whichever of those forms a model gives, it has to learn that form from examples, and each example needs a label, which is the right answer the model should learn to give. The page on how a model learns explains this in full.

For grasp models, however, the label is almost always the same simple thing. A grasp was tried, and then somebody checked whether the object was still in the gripper after the arm lifted it. So the label is 1 if the object was still held, and 0 if it fell out. A diagram shows three grasp attempts and their labels, where each attempt ends with one number: 1 if the object stayed in the gripper, and 0 if it fell out.

Once the label is defined, those attempts can happen in two places. A real arm can try thousands of grasps on real objects, or a computer can test grasps on 3D models of objects using the rules of physics, with no robot at all. The second way is much faster, so most grasp models today learn from it. The grasp quality models page shows both ways side by side.

The next part introduces the four kinds of grasp model. Because the label is the same for all of them, the four kinds differ only in the form of their answer. So the four kinds each get their own page.

First is top-down grasp detection. The model looks at one picture taken from above and draws rectangles on it, and each rectangle says where the two jaws should close. The gripper always comes straight down.

Second is six-degree-of-freedom grasps. The model looks at a 3D picture of the scene and gives full grasps that can come from any direction. Six degrees of freedom means six numbers, which are three for the position and three for the direction.

Third is suction and affordance. The model paints a score on every part of the picture, so that for suction the score says where a cup will seal, while for affordance it says what each part of an object is for, such as "hold here" or "this part cuts".

Fourth is grasp quality models. The model is given one possible grasp and says how likely it is to work, because something else proposes the grasps and the quality model only picks the best.

The pages of this chapter are in two groups, because some of the four kinds come up far more often than the others. The first group, most used, holds six-degree-of-freedom grasps and suction and affordance, since grasp models that work in any direction are what most new arm projects reach for, and suction is the most common gripper in warehouse picking. The second group, also used, holds top-down grasp detection and grasp quality models. Top-down detection still works well for flat bins seen from above, while quality models are most often met inside a larger system, scoring the grasps another method proposes.

The fifth section compares the four kinds side by side. A table shows what each kind takes in, what it gives back, and what it is good and bad at.

For top-down grasp detection, one depth picture from above goes in, and rectangles come out showing where to close, at what angle, and how wide. This is good because it is small, fast, and runs without a graphics card, but it is bad because it only gives straight-down grasps.

For six-degree-of-freedom grasps, a point cloud of the scene goes in, and many full grasps come out, each with a score. This is good for cluttered bins and grasps from any side, but bad because it needs a strong graphics card and often has strict licences.

For suction and affordance, a colour or depth picture goes in, and a score for every pixel comes out. This is good for flat-faced objects and knowing which part to hold, but bad for objects with no flat face or parts it has not seen labelled.

Finally, for grasp quality models, a picture plus one proposed grasp goes in, and one number comes out, which is the chance it holds. This is good at choosing the best of many grasps, but slow when there are many grasps to check.

Two words in that table need explaining, and both of them come from Book 2. A depth picture is a picture where each pixel holds a distance from the camera instead of a colour, while a point cloud is a list of 3D points on the surfaces the camera saw. The camera basics page in Book 2 explains both.

The four kinds are often joined together rather than used alone. For example, a six-degree-of-freedom model proposes grasps and a quality model scores them, or a suction model and a finger-grasp model run side by side and the robot uses whichever gives the better score.

The next section covers what a grasp model does not know. The table just mentioned listed what each kind is bad at, but there is one gap they all share. A grasp model learned one thing only, which is whether the object stayed in the gripper, so it knows nothing else at all. Three examples show what that gap leaves out.

First, it does not know which part must not be touched, so it may pick the blade of a knife simply because the blade is easy to hold. Second, it does not know what happens next, so it may hold a mug by the rim, which is fine for lifting but makes it impossible to pour. And third, it does not know your arm, so it may choose a grasp that your arm cannot reach, or one that is wider than your gripper can open.

So the usual answer is to treat the model's grasps as suggestions rather than decisions. Other checks then throw away the ones that are unreachable, that would hit something, or that break a rule about the task. The six-degree-of-freedom page shows this filtering in a picture, while Book 3's models that grasp page gives the checks in order.

The seventh section explains how grasp models connect to the other kinds. Since those extra checks come from elsewhere, a grasp model is only one step in a longer chain. Here is the whole chain for picking up a mug.

First, a seeing model finds the mug in the camera picture, often as an outline around its pixels. Second, a 3D model turns the depth picture into a point cloud, and it may guess the back of the mug that the camera cannot see. Third, a grasp model chooses where the gripper should go on the mug. Fourth, a movement model, or an ordinary motion planner, moves the arm to that grasp without hitting anything. Finally, a touch and body model checks that the mug is really held and is not slipping.

A language model can sit in front of this chain and turn "pick up the red mug" into the choice of which mug. Some newer models join the third and fourth steps into one, so that a vision-language-action model, for example, goes from a picture and a sentence straight to arm movements and never gives a separate grasp. Those models are covered in the vision-language-action models page.

Even so, a separate grasp model is still the common choice in real work, because it gives an answer that a person can look at, check and filter before the arm moves.

The next part suggests where to read next. You should start with top-down grasp detection, because it is the simplest kind and the easiest to picture. For the full list of real grasp models, their licences, and which ones run without an NVIDIA graphics card, read Book 3's models that grasp. For grasps you can compute by hand, without any model, read choosing a grip. For what happens after the fingers close, read holding on. To see where grasp models sit among all the kinds in this book, go back to the map of models.

The final section is about using it in Python. Earlier, it was mentioned that all four kinds of grasp model give back the same kind of answer, which is a list of grasps with a score on each one. This section shows what that list actually looks like in Python, so that after reading it you will know which part of the work a grasp model does for you, and which part is still yours.

The nearest thing to a standard format for that list is the Grasp Group class from the grasp net API library, the package that comes with the Grasp Net One Billion dataset. Many six-degree-of-freedom models save their output in exactly this form, so it is a fair picture of what you receive.

The page shows a short Python script using this library. The code loads a file containing the grasps exactly as the model saved them, with one row per grasp. It then filters out the grasps that are too wide for the robot's gripper, and sorts the remaining ones by their score. Next, it loads a calibration matrix that measures the distance from the camera to the robot's base, and uses it to transform the grasps so they are measured from the base instead of the camera. Finally, it takes the best grasp and prints its score, width, position, and rotation.

The library gives you the format and the arithmetic. It knows how to read and write the file, how to sort by score, how to drop overlapping grasps, and how to move every grasp into another frame when you hand it a transform. It also draws the grippers for you, which is how most of the pictures of grasps in papers are made.

What it does not give you is anything about your robot. You have to produce the point cloud or the depth picture in the first place, which means a working depth camera. You have to measure the camera to base transform yourself, by the calibration procedure described in Book 5's rigid transforms page, and a calibration that is one centimetre out will miss the object by one centimetre no matter how good the model is. You have to check that the arm can actually reach the pose and get there without hitting the table, because the grasp model never looked at the arm. And you have to write the motion that approaches the grasp, closes the fingers and lifts.

The decisions that are yours are the score cut-off below which you refuse to try, the number of grasps you keep and in what order you attempt them, and what to do when the first attempt fails. The hardest decision is whether to use a downloaded model at all. Every trained grasp model in this chapter learned the geometry of one particular gripper, and as explained earlier, that matters: a model trained on a gripper that opens to ten centimetres will happily propose grasps that your six centimetre gripper cannot make. Filtering by width, as the code does, removes the worst of those, but it does not fix a model that learned to place its fingers where your fingers are shaped differently. If your gripper is unusual, you will have to retrain, and retraining needs the simulator and the dataset that the original authors used.
