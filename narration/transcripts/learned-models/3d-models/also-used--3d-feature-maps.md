3D feature maps. This page is about 3D maps that carry meaning. In a plain point cloud, each point only says where a surface is. In a 3D feature map, each point also says what kind of thing it is part of. That means the arm can ask in words where the handle of the mug is, and get back a place in 3D. So the page answers three questions. Where does the meaning come from, and how does it get into 3D? And when is a map like this worth building, instead of simply asking an image model about the latest photo?

It is for a reader who has read the chapter overview and the page on scene reconstruction. It also helps to have read the page on open-vocabulary models, because this page uses the same image models, such as CLIP. The page explains what it needs from them.

The first section explains what a 3D feature map is. Since the introduction promised a map that carries meaning, this section says what that means exactly. A 3D feature map is a 3D map in which every point stores a list of numbers describing what the point is part of. That means the map can be searched by meaning rather than by position.

For example, a floor plan of a shop shows where the walls and shelves are, which is like a plain point cloud. Now write a label on every shelf, such as milk, bread, and soap. You can then find the bread by reading the labels, without knowing its position in advance. A 3D feature map does the same for the space around a robot arm, except that its labels are lists of numbers rather than words. That lets it answer questions in words nobody wrote down in advance, such as something to drink from.

A diagram shows a mug made of points. Each circled point has its x, y, and z coordinates, and also carries a list of numbers that says what kind of thing it belongs to.

A list of numbers like this is called a feature, which is where the page gets its name, and a real feature has a few hundred numbers in it. Two points on similar things, such as two mug handles, have similar lists. But two points on different things, such as a handle and a table, have very different lists.

The next part of the page covers what goes in and what comes out. A feature map is built once and then asked many times, so the two halves are worth separating. To build the map, three things go in. First, photos of the scene from several places. Second, the camera pose for each photo, and usually a depth picture too. On an arm with a wrist camera, the joint readings give the poses, as on the scene reconstruction page. Third, an image model that has already been trained, such as CLIP or DINO, because the map borrows all of its meaning from that model.

What comes out is the map itself, which is a point cloud, or a fitted scene like a NeRF, where every point has its feature.

To use the map, only one thing goes in, and that is a question, usually a few words such as the handle or the red cup. What comes out is a score for every point, which says how well that point matches the words. The arm then takes the points with the highest scores as its answer.

The third section explains how it works inside, in three steps. Step one gets a list of numbers for every pixel. All the meaning in the map comes from an image model, and two kinds of image model are common.

CLIP, short for contrastive language-image pretraining, is a model with two parts. One part turns a picture into a list of numbers, while the other part turns some words into a list of numbers of the same length. It was trained so that a picture and a sentence describing it get similar lists, which is why a photo of a mug and the word mug end up close together. The open-vocabulary models page explains this in more detail.

DINO is instead an image model that learned from photos alone, with no words. Its lists are very good at saying that two pixels are on the same kind of part, such as two mug handles. But it cannot compare those lists with words.

CLIP gives one list for a whole picture, while a map needs one list for every pixel. So the map builder has two choices. It either uses a version of the model made to give a list for each small patch of the picture, or it runs the model on many small crops of the photo and gives each pixel the lists of the crops it falls in.

Step two lifts the lists into 3D. Now that every pixel of every photo has a list, the next step puts those lists onto points in 3D.

A diagram shows two photos of the same spot on a mug handle. Because the same spot shows up in both photos, the map stores one point for it, with the average of its two lists.

There are two ways to do this, and the first is fusion, which works directly on point clouds. First, you use the depth picture to turn each pixel into a 3D point, as for any point cloud. Second, you give that point the pixel's own list. Finally, when the same spot shows up in another photo, you average the new list with the old one.

Averaging helps because the image model makes small mistakes that differ from photo to photo, which means the average over many views is steadier than any single view.

The second way is a feature field, and it works like a NeRF from the scene reconstruction page. A NeRF answers what colour any spot is, while a feature field also answers what list of numbers that spot has. It is fitted in the same way, because the program draws the lists from a camera pose, compares them with the image model's lists for the real photo, and then adjusts. Copying what one model knows into another model in this way is called distillation.

Step three is to ask with words. Once the map holds its lists, the software does three things to ask a question. First, it gives the words, such as handle, to the text part of CLIP, which gives back one list. Second, it compares that list with the list of every point in the map, which gives one number per point. That number is high when the two lists are alike. Third, it colours the points by that number, or simply keeps the points that score highest.

A diagram shows the same map asked two different questions. It answers handle by highlighting the handle, and where to drink from by highlighting the rim, and nobody labelled either part in advance.

The map was built only once, so after that each new question is quick, because it is only one comparison per point.

The next section is about how it is trained. Because the meaning is borrowed, most 3D feature maps need no new training of their own, and all the learning sits in the image model they borrow from.

That image model was trained long before, on a huge collection of pictures. CLIP was trained on about 400 million pictures with captions, collected from the internet, and no robot data was involved at all. So the map builder simply uses what CLIP already learned.

The map itself is then built for one scene, in one of the two ways in section three. Fusion needs no fitting at all, because it only averages, while a feature field is fitted like a NeRF, which takes seconds to minutes on a graphics card.

So there are three stages in all, and only the first is training in the usual sense. First, train the image model once, on internet pictures, although someone else has usually done this already. Second, build the map for this scene. And third, ask as many questions of it as you like.

The page then lists some well-known models. Both ways of building a map above appear in real systems, and these are the ones to know.

CLIP-Fields from 2022 fitted a small network that gives a CLIP-style list for any spot in a room, so that a robot could find objects in the room by name.

LERF, short for language embedded radiance fields, from 2023, adds CLIP lists to a NeRF, so you can type a word and see the matching part of the scene light up in 3D.

F3RM, from the 2023 paper Distilled Feature Fields Enable Few-Shot Language-Guided Manipulation, used a feature field on a robot arm. After a few demonstrations of a grasp, the arm could make the same kind of grasp on new objects, and it could be told in words which object to pick.

ConceptFusion from 2023 builds a 3D feature map by fusion as the camera moves, without any fitting, and you can ask it with words, with a click on a picture, or with a sound.

OpenScene from 2023 gives every point of a scanned room a CLIP-style list, so it can then find and outline objects by any name.

ConceptGraphs from 2023 groups the points into separate objects instead, keeping one list for each object and noting how the objects sit relative to each other.

To make this clearer, the next section gives a worked example of the command, pick up the green mug by its handle. Those systems are easier to follow once one of them runs a whole job. An arm stands at a kitchen counter with several mugs, a kettle and a sponge on it. A person then types, pick up the green mug by its handle.

First, the arm moves its wrist camera over the counter and takes about a dozen colour and depth pictures, saving its joint readings for each one. Second, the software runs the image model on each picture and builds a 3D feature map by fusion. Third, the software asks the map about green mug and keeps the points that score highest, which are the points of the green mug. Fourth, within those points only, it asks about handle, so the highest scoring points are now the handle of the green mug. Fifth, a grasp model from the grasp models chapter proposes many grasps on the mug, and the software keeps only the grasps whose fingers close on the handle points. Finally, the arm then makes the best of those grasps.

If the person next says, now wipe the counter with the sponge, the map is still there, so the software only has to ask about sponge. It does not need to look again unless something has moved.

F3RM goes one step further than this. Instead of the word handle, it learns from a few demonstrations where a person's grasp sits on a mug, and it stores the lists at the points where the fingers were. On a new mug it then looks for points with similar lists, and grasps there.

The next part covers what goes wrong. That example worked cleanly, but five things go wrong in less tidy scenes.

First is blurry edges. The image model looks at patches of pixels rather than single pixels, so the lists near an edge are a mix of both sides. A thin handle often gets a list that is partly handle and partly table, which means the map finds the right area but not the exact border. A segmentation model such as SAM can sharpen the outline afterwards.

Second is words that mean the same. The map may score mug and cup quite differently, even when a person would use them for the same thing. So people often try a few wordings and then combine the scores.

Third is where things are relative to each other. CLIP-style lists are good at saying what a thing is and weak at saying which one is on the left. So, the mug to the left of the kettle, is hard for a plain feature map. Systems such as ConceptGraphs keep a separate record of objects and their positions, and a language model reads that record to answer such questions.

Fourth, the map goes out of date. When the arm moves a mug, the map still shows it in the old place. So the software must update the part of the map that changed, or build the map again.

Finally, size. Every point carries a list of hundreds of numbers, so a map of a whole room can take far more memory than a plain point cloud. Many systems therefore shrink the lists, or keep one list per object instead of one per point.

The eighth section asks why you would use this rather than asking about each photo, and what it costs. Since those problems are real, it is worth setting out what the map buys you. A 3D feature map is a 3D map where every point carries a list of numbers borrowed from an image model. It does let the arm find things and parts in 3D by name, including names nobody planned for.

The obvious alternative is to skip the map and use the latest photo on its own. You ask an open-vocabulary model, such as Grounding DINO, to draw a box around the green mug. Then you read the depth picture inside that box to get the 3D points.

So why build a map instead? First, the map remembers what is out of view, so if the green mug is behind the kettle in the latest photo then the map still knows where it is from an earlier photo. Second, many views are steadier than one, because the average over a dozen photos is less likely to be wrong than any single photo. Third, it gives 3D directly, whereas a box on a photo covers some background too, so the depth inside the box includes points that are not the mug. And fourth, it answers many questions from one build, and each question is fast because it needs no new photos.

What it costs you comes in four parts. First, time to build, because the arm has to look from several places first. Second, memory and a graphics card, since hundreds of numbers per point add up. Third, it goes out of date, so in a scene where things move often the latest photo is more honest than an old map. And fourth, it is only as good as the image model, because if CLIP does not know the name of a part then the map does not either.

So a 3D feature map suits a scene that stays mostly still while the arm does several jobs in it, such as tidying a table. For one quick pick in a scene that keeps changing, asking about the latest photo is simpler.

The next section discusses the written alternative. There is no written alternative for the meaning itself. This is because the link between words and what things look like comes from an image model trained on millions of pictures with captions. However, the map underneath does have a written form. Volumetric maps combine many depth pictures into one 3D map. They merge the many readings of each small cube into one answer, just as the fusion step on this page does with lists of numbers. Then clustering groups the points above the table into objects, so that a written program can keep a list of where each object is. That is enough when the robot only needs to know where things are, and not what they are called.

The page then suggests where to read next. The page on open-vocabulary models explains CLIP, Grounding DINO and SAM, which are the image models these maps borrow from. The scene reconstruction page explains the NeRF fitting that feature fields build on. The page on language models as planners shows how a language model breaks a request such as tidy the table into steps, each of which can be a question to a map like this. The foundation models page in Book 3 covers the large models that link words, pictures and arm movements in one network. Finally, you can go back to the chapter overview to see how this page fits with the other three.

The final section is about using it in Python. The page has explained that a 3D feature map is built once and then asked many times, and that asking means comparing a phrase against the list of numbers held at every point. This section shows the asking half in Python, because that is the half you can run today with installed libraries. After reading it you will know where the line falls between what is packaged and what is research code.

The code uses the Hugging Face transformers library to load CLIP. It passes a phrase, such as the handle of a mug, into the model, which turns it into a list of 512 numbers. Then, it uses the Open3D library to load a point cloud, and loads a matching list of 512 numbers for each point in that cloud. To find the best match, it calculates the dot product between the phrase's numbers and the points' numbers, and prints out the point with the highest score.

What is packaged for you out of the box is CLIP itself, and that is the part that carries the meaning. You get a text side and an image side that were trained to land in the same 512 numbers, so comparing a phrase with a picture is a dot product and nothing more. Open3D handles the cloud. Together those cover the asking part of the code.

What you still have to write yourself is the building, and that is where the work is. The point features in the code have to come from somewhere, and getting them involves a step CLIP does not do. CLIP gives one list of numbers for a whole picture, not one per pixel. So the well-known systems mentioned earlier use a changed version of CLIP, or the per-patch outputs of DINOv2, to get a list for each part of each picture. Then they lift those lists into 3D with the camera poses and the depth. Systems like F3RM, ConceptFusion, OpenScene and LERF are the code that does this, and all four are research repositories rather than installable packages, so you clone one and adapt it rather than importing it.

What you have to decide is which image model to borrow the meaning from, because the map can only be as good at telling parts apart as that model is, and CLIP is noticeably weaker on parts of objects than on whole objects. You also decide how much memory to spend, since 512 numbers for each of 200,000 points is about 400 megabytes in single precision. Real systems either reduce the length of each list or keep one list per object rather than per point, as ConceptGraphs does. Finally you decide what score counts as a match, because the dot product always returns a best point even when nothing in the scene matches your words at all.
