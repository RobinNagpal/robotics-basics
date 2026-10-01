Learned simulators. This page explains world models that predict how cloth, rope, dough, liquids, and sand move. Because these materials change shape as they move, a few numbers cannot describe them. The page answers four questions: how a model can follow a material that has no fixed shape, what happens inside such a model at each step, where its training data comes from, and when it is better than a hand-written physics simulator.

It is written for a reader who has already read the world models overview and the page on learned dynamics models, so you should know what a state, an action, and a rollout are. It also helps, but is not needed, to have read the page on point cloud models, because a learned simulator often starts from a point cloud.

The first section explains what a learned simulator is. It splits a material into many small pieces, and predicts where each piece will move next from where its neighbours are.

A simulator is a program that calculates how things move, step by step, and the simulators in Book 3, such as MuJoCo, are written by hand from the laws of physics. A learned simulator does the same job, but a neural network works out each step. That network learned how to do its job from examples of the material moving.

Here is an everyday example of the same idea, using a crowd of people leaving a stadium. Each person only looks at the few people right around them, so they step forward when there is space and slow down when someone is close in front. Nobody follows a plan for the whole crowd, and yet the crowd as a whole still flows through the exits in a sensible way. A learned simulator works in the same way, because each small piece of the material looks only at its close neighbours, and the whole material then moves sensibly.

The small pieces are called particles, and what one particle stands for depends on the material. For example, for water or sand each particle stands for a small drop or a small pile of grains. Instead, for cloth each particle is a point on the cloth, and neighbouring points are joined by threads in a grid, called a mesh.

The next part of the page covers what goes in and what comes out. A learned simulator for a robot arm takes two things in and gives one back.

First, it takes in the particles now. This is the position of each particle, and how fast it has been moving over the last few steps. A towel might be two hundred particles, while a tray of water might be thousands.

Second, it takes in what the arm is doing. The gripper is usually added as a few extra particles whose movement is known, because the robot controls it.

Finally, the output is where every particle will be one small step later. A step is usually a small fraction of a second.

On a real arm, the particles come from a depth camera, which measures how far away each pixel is. That gives a point cloud, which is a set of 3D dots on the surface of the material. The 3D models chapter explains point clouds in full, so this page takes them as given. The simulator then uses a selection of those dots as its particles.

The next section explains how it works inside, starting with turning the material into a graph. The first step joins nearby particles together, and two particles are joined if they are closer than a chosen distance, called the connection radius. For cloth, the threads of the mesh are also kept as joins.

The result is called a graph, which in this sense is not a chart. It is a set of points, called nodes, and the lines that join them, called edges. So a neural network that works on a graph is called a graph neural network, or GNN.

The page includes a diagram showing water in a tray drawn as particles. On the right side of the diagram, each particle is joined to the others close to it, and one red particle's neighbours are highlighted. The red particle is joined only to the orange ones inside a dashed circle, so only those influence it.

Because particles move and their neighbours change, the graph is built again at every step.

Next is what happens during one step, which is called passing messages. Each step has three parts, and they happen to every particle at the same time.

First, each neighbour sends a message. A small network looks at a pair of joined particles, specifically their positions and their speeds. It gives back a short list of numbers, called a message. You can think of the message as how much this neighbour pushes or pulls on me. Nobody tells the network what the message should be, because it learns whatever numbers help the prediction.

Second, the particle adds up its messages. It sums all the messages it received, and adds gravity.

Third, it moves a small step. A second small network turns the sum into a change of speed, and the program adds that to the particle's speed and moves the particle.

A diagram illustrates this process, showing one particle receiving a message from each neighbour, adding them up with gravity, and moving a small step.

So every particle does this at once, and then the whole process repeats for the next step.

The first and second parts are usually repeated several times within one step before the third part. Each repeat lets information travel one more join across the graph, so after ten repeats a particle is influenced by particles up to ten joins away. This is how a pull on one corner of a towel reaches the far corner.

The same small networks are used for every particle and every pair, and this is the key idea of the whole design. The model learns one rule for how neighbours affect each other, and it does not learn a separate rule for every particle. So a model trained on a small towel can often run on a bigger towel, which simply has more particles.

To predict a whole fold or a whole pour, the simulator runs many steps in a row, feeding each result back in. This is the rollout from the learned dynamics models page. So learned simulators often run hundreds of steps, because each step is short. Errors add up here too, and a later section says what people do about it.

The next section explains how the model is trained. A learned simulator needs examples of the material moving, with the position of every particle at every step, and there are two places to get them.

The first place is a hand-written simulator that is very accurate but slow. Engineers already have careful simulators for cloth, fluids, and sand, and these can take a long time to compute each step, but they give the exact position of every particle. So the learned simulator watches thousands of runs and learns to copy them. It predicts one step, is compared with the careful simulator's next step, and is corrected.

The second place to get examples is the real world itself. The robot pokes, pinches, or lifts the material while a depth camera records it, and this teaches the model the real material rather than a simulated one. However, it is harder, because a camera cannot say which dot in one frame is the same bit of material as which dot in the next frame. So the training compares the predicted shape with the real shape as a whole. For each predicted dot, it asks how far is the nearest real dot.

Because the data is cheap, training on simulated runs is common. Then a small amount of real data is often added, so that the model matches the real material.

The page then lists some well-known models of this kind. These are all real, published models rather than examples invented for this page.

First is Interaction Networks from 2016, which introduced the idea of predicting how objects move from messages between pairs of objects. Most later learned simulators build on it.

Second is DPI-Net from 2019, which applied the idea to particles of rigid objects, soft objects, and fluids, and used it to plan how to manipulate soft objects.

Third is Graph Network-based Simulators, or GNS, from 2020. It learned to simulate water, sand, and a sticky, goo-like material from a careful simulator. It showed that one simple design works for very different materials.

Fourth is MeshGraphNets from 2021, which works on meshes, such as cloth flapping in wind. Its authors reported that it ran faster than the careful simulator it learned from.

Fifth are RoboCraft from 2022 and RoboCook from 2023, which used learned particle simulators on real robot arms to shape plasticine and dough. RoboCook used several tools to make dumplings.

Finally, VCD from 2021 learned a graph model of the visible part of a cloth and used it to plan how to smooth a crumpled cloth.

The next section gives a worked example of folding a towel in half. Here is how a learned simulator helps an arm fold a small towel, step by step.

First, see the towel. A depth camera above the table gives a point cloud of the towel. The program picks about two hundred of those dots as particles and joins neighbours into a mesh.

Second, choose candidate moves. A fold is a pick and a place: grab a point on the towel, lift it, and put it down somewhere else. The planner makes up many candidates, such as grabbing the left corner and putting it on the right corner.

Third, simulate each one. For each candidate, the learned simulator runs the gripper particles along the move and predicts the towel's shape at the end.

Fourth, score each one. The goal is a towel folded neatly in half, so the score compares each predicted shape with that goal shape.

Fifth, do the best move. The arm grabs the chosen corner and moves it.

Finally, look again. The camera takes a new point cloud, and if the fold is not neat, the planner runs again from the real shape.

A diagram shows a towel lying flat, then predicted with one corner lifted, then predicted folded in half. These are the simulator's predictions at three moments during one planned fold, before the arm has moved at all.

In principle a hand-written simulator could do the third step too. However, it would need the towel's stiffness, weight, and friction, which nobody has measured. Instead, the learned simulator learned how this kind of towel behaves from watching it.

The next section covers what goes wrong, and what people do about it. It lists five things that go wrong in practice.

First, errors add up over hundreds of steps. Water can slowly lose volume, and cloth can slowly stretch. So people add small random changes to the particle positions during training, and the model then learns to correct small errors instead of making them bigger.

Second, the camera cannot see every part. When a towel is folded, the bottom layer is hidden under the top, and a point cloud shows only the top. So people keep track of particles from earlier frames, or they model only what the camera can see, as the VCD model does. The shape completion page covers guessing the hidden part of an object.

Third, many particles make it slow. A tray of water with thousands of particles and hundreds of steps is a lot of work for every candidate move. So people use fewer, larger particles and plan only a few candidate moves.

Fourth, rigid objects need care. A metal cup made of particles may slowly bend, because nothing in the network forces it to stay rigid. So some models treat rigid objects separately, and they move all of an object's particles together.

Finally, new materials break it. A model trained on cotton towels may not know how a silk scarf moves. So people train on a range of materials, or they give each particle a few numbers describing the material.

The next section explains why you would use this kind of model, and what it costs. It weighs the problems just mentioned against the alternatives.

The obvious alternative is a hand-written simulator for cloth or fluids, and such simulators do exist and are very accurate, as long as they are given the right material numbers. However, for a real towel or real dough nobody knows those numbers, and the simulator also cannot easily start from a real point cloud. A learned simulator instead starts from the point cloud and learns the real material's behaviour, and it is often faster. Because it is a neural network, a program can also work out how a small change in the move would change the result. This lets a planner improve a move step by step, instead of only trying moves at random.

The second alternative is a video prediction model, which also needs no material numbers of any kind. However, it predicts pictures, and a picture of a towel does not say where each part of the towel is in 3D. A robot needs 3D positions to grab a corner, and the particles of a learned simulator give it those positions directly.

The page then lists what a learned simulator costs you.

First, a good 3D view. You need a depth camera and a way to turn its point cloud into particles.

Second, training data for your material. This is usually a careful simulator and some real recordings.

Third, computing time. It takes many particles and many steps for each candidate move.

Finally, limited reach. It knows the materials it was trained on, and it struggles with parts it cannot see.

The next part of the page is about the written alternative. It asks when a hand-written physics simulator, given the right material numbers, is enough. The simulators section in Book 3 describes the ones people run. The system identification page in Book 5 explains how to measure the numbers inside a physical model from the real thing. It works when there are a few numbers, such as a joint's friction or a finger's stiffness. That page itself notes that cloth, soft objects, and tangled cables have no small set of numbers that fits.

So the written simulator wins for rigid objects and for materials whose numbers are known, while the learned simulator wins for a real towel or real dough. In both cases, the planning in the towel-folding example is written code, of the kind the page on sampling-based optimisation and model predictive control explains.

The section on where to read next suggests several pages. The next page covers latent world models, which predict a short code instead of particles or pictures. The page on point cloud models explains the 3D dots that a learned simulator starts from. The scene reconstruction page covers building a whole 3D scene from pictures. The touch sensing models page covers the sense that tells a gripper how soft a material is when it holds it. Finally, for the hand-written simulators that learned simulators are compared with, you can read the simulation and evaluation section in Book 3.

The final section is about using it in Python. It writes one step of joining particles and passing messages in code, so you will know what a learned simulator actually is as code, which is smaller than the idea suggests.

There is no pretrained cloth or water model to download, so this is a model you build and train yourself. The library that makes that reasonable is PyTorch Geometric, which adds graphs to PyTorch. It gives you the two parts that are tedious to write by hand: finding which particles are close enough to be joined, and collecting every particle's messages.

The code defines a step for a cloth model. It sets up two small neural networks: one to create the messages, and one to update the particle's speed. It creates two hundred random particles to represent twenty centimetres of towel, each with three positions and three speeds. It then uses a function called radius graph to join particles that are closer than three centimetres together. Finally, it runs the step to get the change in speed.

The three parts of a step are all there. The radius graph function builds the graph from the current positions, which is the rebuilding that happens at every step. Then the message network decides what one neighbour tells another. It is given the difference between the two positions rather than the two positions themselves, so that the same rule works anywhere on the table. Finally, the messages are added up, and the update network turns the sum into a change of speed.

PyTorch Geometric gives you the graph building and the message collecting, and nothing about cloth. The two small networks start from random numbers and know nothing until they are trained.

What you write is the rest of the simulator. You turn the depth camera's point cloud into particles, you add gravity and the gripper, you repeat the message step several times before moving anything, and you run many steps in a row for a whole fold. You also write the training, which compares your predicted shape against a recorded one.

What you decide is the connection radius and the number of particles, and these two numbers decide whether the model is useful. A radius that is too small lets a towel tear apart, while one that is too large makes every step slow. The published code for these models is usually a folder inside a research repository that you clone and read, rather than a package you install, so those numbers are read off a paper rather than given to you by a library.
