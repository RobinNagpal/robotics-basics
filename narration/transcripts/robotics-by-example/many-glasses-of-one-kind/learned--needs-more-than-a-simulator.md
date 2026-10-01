<!-- section: introduction | Introduction -->

Learned approaches that need more than a simulator.

This document describes one learned approach to problem two that is not built here. It is an active-vision policy, which learns from experience where to point the camera next. The page explains what that approach is and which practical condition it fails. By the end, you will understand how such a policy works, the idea inside it that is worth knowing even though it is never built, and the exact reason the machine this project runs on cannot train it.

The important thing to say first is that nothing here is wrong. A policy learned this way is a reasonable answer to this problem, and it is what a well-resourced team might reach for first. It is written up so that the choice stays visible, and so that the reason for not taking it is the honest one, which is the cost of the training rather than a view about learned methods.

It needs no different algorithm to become usable. It needs a different setup. It requires many simulated worlds running at once, so that the experience it has to collect costs hours instead of days.

<!-- section: the-test-it-had-to-pass | The test it had to pass -->

The next part of the page explains the test an approach had to pass to be included in the main overview. An approach belongs there only if everything it needs can be produced by the simulator on the machine this project runs on. There is no physical robot on a bench and no data from a real table, and the machine's own limits are particular rather than general. In practice, that comes down to three conditions.

The first condition is that it cannot use any sensor the simulator does not have. The simulator gives this cell a depth camera, contact sensors in the gripper pads, and a force sensor at the wrist. Anything else would require a purchase order rather than a design decision.

The second condition relates to the particular shape of this machine's graphics hardware. It has an integrated GPU that PyTorch reaches through its MPS backend, so models do train and run on it. What it does not have is an NVIDIA card, and therefore it has no CUDA. Anything that needs code compiled for CUDA does not run here at all. Furthermore, its memory is shared with the processor rather than being dedicated video memory. The GPU may use almost all of that memory, which is why models fit in the first place, but it is the exact same memory that everything else on the machine is using at the same time.

The third condition is that training must take hours rather than days. A method that takes a week of continuous simulation to train cannot be iterated on, and a method you cannot iterate on will not be debugged.

The approach discussed below fails the third of those conditions, and the second condition is what closes off the usual way around it.

Notice what is not among those conditions: using a weights file fitted somewhere else. A downloaded model is usable here as long as it runs here. Three other solutions in this project are built exactly that way. They involve segmenting anything and then keeping the glasses, using a fine-tuned instance segmenter, and using amodal masks for the hidden parts. 

All three of those run on this machine as it stands, through the same MPS backend, and their code is provided alongside the scores each of them achieved. So the claim that a borrowed model is usable here is a measured fact rather than just an expectation. The condition that really matters for such a model is the second one: it has to run without CUDA, and it has to fit in memory the rest of the machine is also using.

There is one note about tooling worth knowing before depending on any borrowed model, including those three. The license terms across model families differ sharply. Some of them are copyleft in a way that reaches software you only ever run as a service and never distribute. At least one popular family states one license in its documentation and a different, stricter one in its license file, and the license file is what actually counts. So for anything that might ship, reading the license file is a decision rather than a minor detail. The specific terms are not listed here, simply because they change over time.

<!-- section: an-active-vision-policy | An active-vision policy -->

The next part of the page covers an active-vision policy. 

It starts by noting that this approach fails the third condition. Everything it needs is inside the simulator, which is what makes it frustrating. The cost is throughput. It learns from episodes, where each episode is a handful of arm movements and a simulator reset, and these methods want tens of thousands of them. That comes to days of continuous simulation on one machine. The usual way around that is a simulator that steps thousands of worlds at once inside the graphics card, but those simulators are written for CUDA, so the second condition shuts that door as well. A supervised version of the same idea, which predicts whether a viewpoint will pay off rather than learning a policy, does fit the conditions, and that is covered in the main overview as the fourth solution.

This approach is learned, it acts as the decider, and it forms a closed loop by construction. A policy takes the current belief about the table and outputs where to point the camera next.

A policy is a function from what the robot knows to what it does next. Here, that means the belief about the table going in, and the next camera pose coming out. Nobody writes the rule inside it. Instead, the rule is a pile of numbers, called the weights, which are fitted from experience.

There are two ways to fit them, and the difference matters a great deal for cost. 

Reinforcement learning lets the robot try. It looks somewhere, and eventually is handed a number, called the reward, saying how well the whole attempt went. Thousands of attempts later, actions that tended to precede high reward have become more likely. Nobody ever says which individual look was good, and that is inferred from the totals, which is precisely why it takes so many attempts.

Imitation learning shows it the answer instead. You run an expert, whether a person with a joystick or a slow method already known to be right, record what the expert saw and did, and fit the policy to reproduce the choice. This is called behaviour cloning, and it is ordinary supervised learning. It needs no reward at all, and it can never beat the expert it copied.

There are two reasons why anyone does it this way, and the second is the stronger one. 

The first is speed. Scoring a viewpoint properly is expensive, while choosing one is cheap. The third solution's score casts a ray per pixel into an occupancy map for every candidate, whereas a policy does one forward pass, and you pay the cost once, offline. 

The second reason is reach. A geometric score exists only where somebody can write one down. Here they could. Where the cue is subtler, nobody can.

Here is how it would work in this scenario. 

The observation would deliberately not be the raw picture, because appearance is exactly what will not transfer out of the simulator. Instead, you feed the policy what the geometry has already produced. This includes the glass zone as a coarse grid of cells, each marked empty, occupied, or never-seen. It includes one row per cluster holding its position, its fitted width, how many stations saw it, and whether that width is inside the expected range for that kind of glass. Finally, it includes how many looks remain in the budget. That is a few hundred numbers in total, which is small enough to train on a standard processor.

The action could in principle be a camera pose, which is six numbers. In practice, do not do this. Take a fixed list of candidate poses, such as a ring of directions around the target multiplied by a few heights, and let the action be a choice among them, plus one extra action meaning stop. Making the action discrete is the sane engineering choice here, for a specific reason worth understanding. Every candidate in a fixed list can be checked once against the arm's reach and against whether any joint angles can reach it. This means the policy cannot name a pose the arm will not hold, because the impossible ones are masked out before it chooses. A continuous six-dimensional space would spend most of its exploration pointing the camera at mid-air.

The reward is the hard part, and this is where the approach becomes fragile. The obvious reward is this problem's own score sheet: a point per glass correctly separated, a point off per merged pair, and a small penalty per look so that dithering costs something. But that needs to know which glasses were really there. The simulator writes down everything it spawned, so in simulation the reward is exact. Reality has no such file. You could pay for a proxy, such as the circle fit passing, but a policy optimises exactly what you pay for. A policy paid for a passing fit learns viewpoints from which the fit passes, and not viewpoints from which the answer is right.

How long it would take is the condition this approach fails. An episode is a handful of looks, each being an arm movement of a few seconds, plus a reset. Call it some tens of seconds of wall clock time running without a display, which is a figure to measure rather than guess. Multiply that by the tens of thousands of episodes these methods want, and it is days on one process, or a fraction of that with several running in parallel. Meanwhile, a single learning step takes milliseconds. So the simulator is the bottleneck, by orders of magnitude, and every optimisation effort belongs there rather than in the learning code.

This is not a solution with feedback bolted on. It is the loop itself, and it runs in five steps. 

First, observe. Run the survey from the top, cluster the points, fit circles, and build the observation. Second, choose. The policy returns one of the candidate poses, or stop, and the ones failing reach or joint angles were masked out before it chose. Third, move. Plan and execute the movement, taking a few seconds, and if the plan fails, mask that candidate and go back to choosing. Fourth, re-observe. Take the pictures, fold the new points into the same clusters, fit again, and rebuild the observation. Fifth, stop. This happens on the stop action, or when the budget of looks runs out, with clusters still failing their fit reported as unseparated.

Two properties of that loop are deliberate. The belief is cumulative, because each look adds points to the same clustering rather than starting again. And the budget is external rather than learned, so a policy that never says stop wastes a fixed number of looks rather than running forever.

Consider a worked example. Glass A stands about halfway out across the arm's reach. Glass B stands further out, at the smallest gap from A the cell allows. B sat behind A from most of the survey stations, so the merged cluster fits a circle about twice as wide as any glass of this kind can be. 

Two of the candidate directions lie along the line joining A and B, which are the worst possible directions. At every height they fail on reach alone, because standing back from A along that line puts the camera either folded in against the base or stretched out past the far limit. So they never even reach the policy. 

The policy picks the candidate square across the line joining A and B. After one movement taking a few seconds, the cluster resolves into two discs, both with widths inside the kind's range. The policy says stop, and the episode collects its reward.

Now for the comparison that matters. The third solution's arithmetic chose that exact same viewpoint, before the planner was asked anything at all, and it can say why. It knows that from the blocked direction, B would cover a large part of the width of the frame directly behind A. The policy chose the same pose and can say nothing at all about its reasons beyond a number. They give the same answer, and only one of the two can be audited.

To build this, the approach needs a training environment wrapped around the existing cell, where resetting spawns four to six glasses, stepping moves the arm and re-runs perception, and the reward reads the spawn record. That wrapper is the real work, because it must reset the simulator thousands of times without leaking processes. It also needs a standard reinforcement-learning library, and days of machine time. It does not need labelled pictures, and it needs nothing the machine's own graphics cannot run. What the machine cannot supply is the simulator time.

What it is good at is run-time speed, because choosing is one forward pass, which is microseconds against the seconds a movement costs. It can also use cues nobody wrote down, where a viewpoint pays off for reasons the circle fit misses. And it optimises the thing itself, meaning merges and splits, where information gain is only a proxy for them.

What it is bad at, first, is that it cannot explain itself, and here that is practical rather than philosophical. This problem says the failure to watch hardest is the merged pair, because it looks plausible downstream. A policy that stops one look early produces exactly that failure, and reports confidence while doing it. 

It is also more machinery than this problem has earned. What it would learn is computable: the kind of glass is known, the range of widths is known, and occlusion is a line-of-sight test. Where a geometric score exists and is auditable, a network trades the explanation for a speed-up, and here the explanation is worth more.

Its failure modes are worth naming, because two of them are expensive to discover. 

First is reward hacking. Charge too much per look and the policy stops at once and eats the merge penalty. Charge too little and it burns its whole budget every run. That balance is not derivable, and each attempt at it costs another training run.

Second is drift out of the simulator. This is milder here than for tasks involving contact, because there is no friction, no deformation, and no impact. What matters is straight lines from camera to object, which the simulator gets right. Feeding clusters rather than pixels removes most of the appearance gap too. But the policy also learned this simulator's depth noise and the way its readings drop out at glancing angles. A real camera that loses the far rim of a glass at a steep angle shifts every observation the policy ever sees.

Third is silent staleness. Change the kind of glass, the lighting, or the list of candidate directions, and the weights describe a cell that no longer exists, while the tests still pass.

Finally, real glassware removes the input altogether, because the observation is built from clusters, and clusters come from depth that real glass does not return.

This approach would be the right choice when the doubt stops being a short list. Here, one known kind of glass and a known range of widths make the question of one glass or two a matter of arithmetic, which is auditable. The fourth problem has several kinds of glasses, some never measured, and the union of their ranges is wide enough that the circle fit stops deciding much. A policy that had learned which looks resolve ambiguity would have something real to offer there.

One shape is worth keeping even so. The third solution's score is a working expert and it runs in simulation for free. Doing behaviour cloning against it gives a fast policy with no reward design at all, at the price of a policy that can only approach what it copied, having lost the explanation that made the original worth having.

<!-- section: what-to-take-from-it | What to take from it -->

The final part of the page covers what to take from it. One pattern is worth carrying away from this approach, because it applies well beyond this project.

A learned component is safe or unsafe depending on where in the pipeline it sits, and not on how good its model is. A policy of this kind sits at the least safe end, because the policy decides and nothing checks it. What it outputs is a camera pose, and a pose carries no width to compare against the range this kind of glass allows. The solutions in this folder that borrow weights sit further back in the pipeline, because each of them outputs a mask. A mask becomes a circle on the table, and a circle is a number that arithmetic somewhere else can refuse.

So the question to ask of any learned component is not how accurate it is, but rather, what checks it, and would that check notice this particular way of being wrong? That question is what the main overview's solutions are arranged around, and it is the thing to hold on to if this approach is ever built.
