Video prediction models. This page explains world models that predict future camera pictures, and it answers four questions about them: what it means for a model to predict a picture, how a robot arm can use a predicted picture to decide what to do, why predicted pictures often come out blurry, and when this kind of model is worth its large cost.

It is written for a reader who has already read the world models overview and the page on learned dynamics models, so you should know what a model, a state, an action and a rollout are. It also assumes you know that a camera picture is a grid of numbers, one per colour per pixel, which is explained on the page about what a model is.

The first section covers what it is. A video prediction model predicts the next camera pictures from the recent pictures and, usually, the actions the arm is about to take.

A learned dynamics model needs a short list of numbers, such as the position of a cube, and somebody must measure those numbers first. A video prediction model skips that step, because it works directly on the pictures from the camera. In other words, its state is simply what the camera sees.

Here is an everyday example of the same skill, using a video of falling dominoes. Watch the first half of a video of someone knocking over a row of dominoes, and then pause the video there. You can picture the next few seconds, because the dominoes keep falling, one after another, from left to right. You did not measure any positions, and you only pictured what you would see. So a video prediction model does the same thing, one frame at a time.

A frame is one picture in a video, and a camera on a robot arm usually records between ten and thirty frames every second.

The next part of the page explains what goes in and what comes out. Now that the idea is clear, here is what actually passes in and out of such a model. A video prediction model for a robot arm takes two things in and gives one back.

First, it takes the recent frames. For example, the last three pictures from a camera above the table. Second, it takes the planned actions. For example, move the gripper right, then right again, then right again. Some models also accept a sentence instead, such as, put the red cube in the bowl. Finally, the output is the predicted future frames. For example, three pictures that show the gripper moving right and pushing the cube along.

The page includes a diagram showing three camera pictures and three planned moves going into a video model, which then draws three future pictures. The diagram shows this with tiny pictures of fourteen by fourteen pixels, so that you can see each pixel. However, real models use pictures with a few hundred pixels on each side.

The predicted pictures get blurrier the further ahead they are, because the model is less sure what will happen.

A model that takes the actions as an input is called action-conditioned, because it predicts a different future for each different action. That is what makes it a world model and not only a video generator. A video generator that ignores the action can show you a future. Instead, an action-conditioned model can show you the future that your action would cause.

The next section explains how it works inside, starting with drawing the next picture. The last section said what goes in and what comes out, so this section says what happens in between. A video prediction model has three parts, and they run in a specific order.

First, an encoder turns each recent frame into a smaller grid of numbers that describes what is in it. Seeing models use the same kind of part, and the image classification page shows how a picture becomes numbers. Second, a predictor combines those numbers with the action numbers. It works out how things in the scene will move. Third, a decoder turns the result back into a full picture, pixel by pixel.

To see further ahead, the model feeds its own predicted frame back in, like the rollout on the learned dynamics models page, and the same problem appears here: errors add up from frame to frame.

Some older models do not draw the new frame from nothing. Instead, they predict how each pixel moves, as in, this group of red pixels shifts two pixels to the right, and then they move the pixels of the last frame. So this works well for pushing, where most of the scene stays the same and only a few things move.

Most newer models are diffusion models, which build the picture in a different way. A diffusion model starts from a picture of pure random noise, like the snow on an old television. It then removes the noise a little at a time, over many passes, until a clear picture is left. At each pass, it uses the recent frames and the action to decide what the clean picture should look like. The diffusion and flow policies page explains the same method used to produce arm movements. So diffusion models draw sharp pictures, but the many passes make them slow.

The page then explains why the future comes out blurry. The future is often uncertain, even when the action is known. For example, suppose the gripper pushes a cube exactly at its middle. Sometimes the cube slides to the left, and sometimes it slides to the right, and both of those happen in the training videos.

A simple model is trained to make its picture as close as possible to the real one, on average. The safest picture, on average, is a mix of both futures: half a cube on the left and half a cube on the right. So that is what a simple model draws instead of one clear future.

A diagram illustrates this, showing the gripper pushing a cube at its middle. Because the cube slides left or right in the data, a simple model draws faint half cubes in both places. This average of the two real futures matches neither of them.

People fix this by letting the model pick one future at a time, and they do that by giving the model an extra input of random numbers. Different random numbers then make it draw different, sharp futures: one with the cube on the left, and one with it on the right. Diffusion models do this naturally, because they start from random noise. So running the model several times shows several possible futures, which is more honest than one blurry picture.

Next, the page lists four ways a robot uses the pictures. A predicted picture does not move the arm by itself, so something has to use it, and robots use video prediction in four ways.

First, to plan. The robot imagines many action sequences, predicts the pictures for each one, and picks the sequence whose final picture looks most like the goal. This is the planning method from the previous page, with pictures in place of numbers.

Second, to draw the task, then copy it. The model draws a short video of the task being done, from a sentence such as, put the red cube in the bowl. A second, smaller model then works out the arm moves that turn each picture into the next. That second model is called an inverse dynamics model. It answers the opposite question to a world model: not, what happens if I do this, but, what did I do to make this happen. A diagram shows these steps, where a sentence becomes a generated video of the task, and an inverse dynamics model reads the arm move from each pair of frames.

Third, to make training data. The model draws many videos of a task being done in new rooms or with new objects. The actions are read off with an inverse dynamics model, and the results are used to train a policy.

Finally, as a training signal. A policy learns to predict future frames while it learns to act, and the predicting part is thrown away afterwards. The overview page says more about this.

The next section is about how it is trained. The last section described how the model draws a frame, and this section says where it learns to do that. A video prediction model learns from videos: it sees the first few frames of a clip, predicts the next ones, and is corrected by the real next frames. This needs no labels written by people, because the video itself is the answer, and that is the main attraction of this kind of model.

The videos come from two sources, and most modern models use both. First, robot videos with actions. The robot records its camera and, at the same time, the actions it took, so these teach the model what each action does. However, they are slow to collect, because a real arm must do every one. Second, ordinary videos without actions. Videos of people cooking, cleaning or building things show how objects move, fall, pour and fold, and there are vastly more of these than robot videos. They teach the model how the world looks and moves, even though they carry no robot actions.

A common recipe is to train first on a large amount of ordinary video, and then to train a little more on robot video with actions, so that the model learns to follow the arm's commands. Book three's page on what is changing explains why this matters: robot demonstrations are scarce, and video is not.

Large video models are trained on far more video than any single robot lab could record, on many graphics cards, for weeks. However, small models for one task, such as pushing objects on one table, can learn from a few hours of the robot's own video.

The next part lists well-known models of this kind. These are all real, published models rather than examples invented for this page.

First, Finn, Goodfellow and Levine in 2016 trained an action-conditioned model on a large set of videos of robot arms pushing objects. It predicts how pixels move instead of drawing new ones. It is the starting point for most later work on video prediction for robot arms.

Next, Visual Foresight, by Finn and Levine in 2017, and then Ebert and others in 2018, planned pushes with such a model. A person clicks on an object in the picture and clicks where it should go. The robot searches for pushes whose predicted pictures move the clicked pixel there.

Then, SV2P, by Babaeizadeh and others in 2018, added the random input described earlier, so that it can predict several different sharp futures.

UniPi, by Du and others in 2023, draws a video of the task from a sentence, and then reads the arm moves off it with an inverse dynamics model.

SuSIE, by Black and others in 2023, predicts only one future picture, the next subgoal, by editing the current camera picture. A policy then drives the arm towards that picture.

Finally, NVIDIA Cosmos includes openly downloadable models that predict future video. Book three's simulation and evaluation document lists them with their licences. NVIDIA's GR00T-Dreams project uses a video world model to make synthetic robot training data.

The next section gives a worked example of sliding a cube to a clicked spot. Here is how Visual Foresight style planning moves a cube to a spot on the table, step by step. Notice that no part of it measures the cube's position in centimetres.

First, set the goal. A person looks at the camera picture on a screen. They click on the cube, and then click the spot where the cube should end up. Second, imagine. The planner makes up a few hundred short sequences of pushes. For each one, the video model predicts the next few pictures. Third, score. In each predicted video, the model also tracks where the clicked pixel goes. The score is how close that pixel ends to the target spot. Fourth, act. The arm does the first push of the best sequence. Finally, repeat. The camera takes a new picture, and the planner starts again from the imagining step.

The same arm can push a mug, a toy or a sponge without any change, as long as objects like them appeared in the training videos, and that is the benefit of working on pictures. However, the cost is time, because each planning round needs hundreds of predicted videos, so the arm pauses between pushes.

The next section covers what goes wrong, and what people do about it. The sections above described this kind of model at its best. This section lists the five things that go wrong in practice, and what people do about each one.

First, pictures get blurry or wrong further ahead. Errors add up from frame to frame, and uncertain futures blur. So people predict only a short time ahead, replan often, and use models that draw one sharp future at a time.

Second, objects change or disappear. A model may let a cube melt into the table, turn a red cube orange, or make the gripper pass through an object. This happens because it learned what videos usually look like, not the rules that objects must obey. So people check the prediction with other models, keep predictions short, and train on more robot video of close contact.

Third, it looks right but the physics is wrong. A predicted video can look convincing while the cube moves too far or too little, and for a robot the distance matters more than the look. The frontier document on simulation and evaluation notes that no published evidence yet shows these models are accurate enough about contact to plan with.

Fourth, it is slow. A large diffusion model can take seconds or more to draw a short clip on a powerful computer, which is far too slow for an arm that must react many times a second. So people use smaller models, predict fewer pixels, or use the model only during training and not on the robot.

Finally, the camera moves. If the camera is on the arm's wrist, the whole picture changes with every move. This is harder to predict than a fixed camera above the table, so many systems use a fixed camera for that reason.

The next part explains why you would choose this kind of model, and what it costs. The last section listed what goes wrong, so this section says when this kind of model is still worth choosing. The obvious alternative is a learned dynamics model that works on a few measured numbers, and it is small and fast. However, it needs a way to measure those numbers, and it cannot describe things that have no short list of numbers, such as a crumpled towel or a pile of beans.

A video prediction model needs no measurement at all, so it works for any object the camera can see. It can also learn from ordinary video, which is available in enormous amounts. That is why the largest companies in the field are building very large video world models.

But there are costs. First, computing power. Large video models need powerful graphics cards to train and to run. Book three notes that Cosmos needs substantial NVIDIA hardware. Second, speed. Drawing pictures is slow, so planning with them is slow. Third, trust. A picture that looks right can be wrong in the details that matter to the arm, such as a few centimetres of sliding. Finally, detail you do not need. The model spends its effort drawing every pixel, including the colour of the table and the shadows, which the robot rarely needs. Latent world models avoid this by predicting a short code instead of a picture.

The next section discusses the written alternative. This page has assumed all along that the model draws pictures, but a robot can avoid pictures altogether. So the written alternative measures the object instead of drawing it. The camera finds the cube with thresholding and colour masks, and a written model of pushing predicts how it will move. Book three's section on quasi-static planar pushing is that model. The planning loop described earlier is written code either way. Sampling-based optimisation and model predictive control tries many sequences of moves, does the first move of the best one, and plans again.

The written way wins for rigid objects that the camera can measure, because it is fast and its predictions can be checked. The video model wins when the objects have no short description, or when one model must handle many kinds of object.

The page then suggests where to read next. The next page covers learned simulators, which follow cloth, liquids and other soft materials piece by piece. The page on latent world models keeps the idea of learning from pictures but predicts a short code, which is much faster. Vision-language-action models are the large robot policies that some video world models are trained together with. The tracking and motion page explains optical flow, which is the idea of how each pixel moves, used by early video prediction models. And for the current state of the field, you can read Book three's section on simulation and evaluation.

The final section is about using it in Python. This page has described models that draw the next camera pictures. Of the four kinds in this chapter, this is the only one you can download ready-made and run today, so this section shows how. After it you will know how to get a predicted video out of a model, and, just as importantly, what that video will not tell you.

The model is NVIDIA's Cosmos, mentioned earlier, and the library is diffusers, from Hugging Face, which is the same library people use for picture-drawing models in general. You install the required packages, which include diffusers, transformers, accelerate, and torch. The page shows a code example, which is the Image to World example from the library's own documentation, with the prompt changed to a robot scene.

In the code, it imports the necessary tools and loads the Cosmos Predict two point five model onto a graphics card. It then passes in a single real picture of a table for the prediction to start from, along with a text prompt saying, a robot arm pushes the red cube to the right across the table. It asks the model to generate ninety-three frames, and then exports those frames to a video file.

Now read that code against the earlier section on what goes in and what comes out, because the difference matters. The action goes in as a sentence, not as numbers, so this model is not action-conditioned in the sense that section described. It shows you a future that matches your words, and it cannot show you the future that a particular three-centimetre push would cause. Every openly downloadable video world model in 2026 works this way, and the action-conditioned models that Visual Foresight planned with are research code from individual papers, with no package to install. So you can generate video today, and you cannot plan pushes with it today.

The pretrained model gives you an enormous amount: everything about how objects fall, slide, bend and cast shadows, learned from more video than you could ever record.

What you write is the sentence, the loop that calls the model, and anything that reads the predicted frames. That last part is a whole model of its own, because turning predicted pictures into arm commands needs the inverse dynamics model discussed earlier, and nothing above provides one.

What you decide is whether the cost is worth it. Loading the model onto a graphics card is not optional, because this model needs a large NVIDIA graphics card, and one call takes a long time compared with an arm's control loop. So people use these models to make training data overnight, not to decide the next push.
