Sampling-based optimisation and model predictive control. This page explains how to choose the best plan when you can score a plan but cannot take a gradient of the score. It covers three methods: random shooting, the cross-entropy method, and CMA-ES. It then covers model predictive control, which runs one of these methods again and again while the arm moves. The page answers four questions, and the first two are about the methods themselves. How does each method work, and how do they compare on the same problem? Then come the practical ones: where does a robot arm use them, and when should you use something else instead?

It is for a reader who has read the chapter overview and the page on trajectory optimisation. That page improves a path by following the gradient, which is the direction in which the cost goes down fastest. This page is about what to do instead when there is no gradient to follow. Every number and picture on this page comes from a real run of a planning and search script.

The first section gives the idea in one sentence. Sampling-based optimisation makes up many candidate plans, scores each one by simulating it, and uses the best-scoring ones to decide where to look next.

An everyday example shows the idea before any robot arm is involved. You are adjusting the shower, but you cannot see a formula for the water temperature, and you can only turn the tap and feel the result. So you try a few positions, notice which ones felt best, and then try a few more positions close to those. After a few rounds of this the water is right. You never worked out which way the temperature changes with the tap, because you only ever compared results. Sampling-based optimisation does the same thing, with a computer model in place of your hand under the water.

The next part introduces the example, which is pushing a block past a mug. The shower needed only the tap turned, so here is a robot task with far more to choose. The example is a pushing task, seen from above. A block 3 centimetres across starts at zero, zero centimetres, and the target is at twenty, four centimetres. A mug stands at ten, two centimetres, right on the straight line between them. The mug is 3.5 centimetres in radius, so the middle of the block must stay more than 5 centimetres from the middle of the mug. The diagrams on the page use a dashed circle to show that limit.

The arm does not grip the block, because it only pushes it. One action is one push, in which the pusher moves by some distance to the side and some distance forwards, at most 5 centimetres in total. A plan is a list of 8 pushes, so one plan is made of 16 numbers in all.

To score a plan, the program needs a push model, which is a rule that says where the block ends up after a push. The model on this page is deliberately simple, and it has two parts. First, the block slides 0.8 times as far as the pusher moves, because it slips. Second, it also drifts to the left by 0.15 times the push length, because the pusher meets it a little off centre.

The score of a plan is the distance from the block's final position to the target, plus 100 if the block touches the mug on the way, so a lower score is better.

This score has no useful gradient, because the plus 100 jumps from zero to 100 the moment the block touches the mug. A gradient tells you what a tiny change does, and here a tiny change either does nothing to that part of the score or makes it jump. The same is true of many scores on a robot, such as whether the grasp held, whether the camera saw the part, or any score that comes out of a physics simulator. The page on pushing and sliding in Book 3 explains why real pushing is hard to write as a formula at all.

The next section explains how it works. With the task and the score now fixed, the three methods differ only in how they choose the next batch of plans to try. They come in order below, from the simplest to the one that learns the most from each round, and then model predictive control wraps a loop around whichever one you pick.

The first method is random shooting, which tries many plans and keeps the best. Random shooting is the simplest of the three, and its name comes from firing many random shots and keeping the one that lands nearest the target. First, it makes up many random plans. Here each push is picked at random, up to 5 centimetres in any direction. Second, it runs each plan through the push model, and works out its score. Finally, it keeps the plan with the lowest score.

The first diagram shows one real run with 400 random push plans spread out around the block. Most of them wander around the start, because random pushes cancel each other out, and 83 of them hit the mug, which are shown in red. The best plan, shown in green, ends 12.1 centimetres short of the target.

Random shooting is poor here because the plan has 16 numbers. For a good plan most of those 16 must be right at the same time, and random guessing almost never manages that. However, with only 2 or 3 numbers to choose, random shooting works well.

The second method is the cross-entropy method, which narrows the search. The cross-entropy method, or CEM, repeats random shooting, but each round it moves the search towards the best plans of the round before. The name comes from statistics, and you do not need that background to use the method.

It describes where to search with two lists of numbers. The mean is the middle of the search, with one value for each of the 16 numbers of a plan. The spread then says how far from the mean to look, again one value for each number.

It starts with a mean of zero pushes and a spread of 3 centimetres. Then it makes 50 plans by adding random amounts to the mean, scaled by the spread. It scores all 50, and keeps the best 5. These are called the elites. It sets the new mean to the average of the 5 elites, and sets the new spread to how much the 5 elites differ from each other. Then it goes back to making 50 new plans, and stops after a set number of rounds.

The diagram for this method shows three rounds of the cross-entropy method. In round 1 the plans spread everywhere. By round 4 they bend below the mug, and by round 8 they form a tight bundle ending at the target.

A table gives the real numbers from that run, showing how the spread shrinks and the plans get closer to the target over 8 rounds. In round 1, the spread is 3 centimetres, and the best plan is 15.1 centimetres from the target. By round 8, the spread has shrunk to 0.44 centimetres, and the best plan is just 1.0 centimetre from the target.

The spread shrinks every round, and that is how CEM focuses on the good plans. It is also its weakness, because if the spread shrinks before the mean has reached a good place, the search stops moving. On this run CEM got to 1.0 centimetre, but on other runs it stopped further away, as the next comparison shows.

The third method is CMA-ES, which also learns the shape of the search. CMA-ES stands for covariance matrix adaptation evolution strategy, and it is the answer to that early narrowing. It keeps a mean and a spread, like CEM, but it adds two things on top.

First, it learns which numbers should change together. In a push plan, pushes 3 and 4 often need to turn left together, and CEM gives each number its own spread, so it cannot say that. CMA-ES instead keeps a table, called the covariance matrix, that says how each pair of numbers should move together. The search cloud can then stretch along a slanted direction instead of only along the axes.

Second, it keeps a separate step size. If the last few rounds all moved the mean the same way, the step size grows, so the search moves faster. If the moves were back and forth, the step size shrinks instead. This stops the search from freezing too early, which is CEM's weakness.

The maths behind these updates is much longer than the idea, so in practice you use it from a library, as a later section shows. The script uses the standard settings, which for a plan of 16 numbers means 12 plans per round.

The next part compares the three methods on the same budget. Now that all three methods have been described, the fair way to compare them is to give each one the same number of plan scores. Here each method scored 400 plans, and each ran 20 times with different random seeds. A seed is the number that starts a random number generator, so each seed gives a different run.

A chart and a table show the median best score against the number of plans scored. Random shooting ends with a median distance of 9.2 centimetres from the target. The cross-entropy method ends at 5.3 centimetres. CMA-ES is the best, ending at just 0.2 centimetres from the target.

On this problem CMA-ES is clearly the best, while CEM beats random shooting but often narrows too early, and this matches common practice. CEM is popular because it is ten lines of code, and because it works well on short plans with a good starting guess, which is exactly the situation inside model predictive control. CMA-ES is instead the usual choice for a longer one-off search, such as tuning a set of gains.

This leads to model predictive control, which plans, does one step, and looks again. All three methods above score their plans in a model, so a plan is only ever as good as that model. The real block is never exactly like the model. To show this, the script uses a real block that slides only 0.65 times as far as the pusher and drifts 0.30 times the push to the left. The planner does not know this, because it still uses the model's 0.8 and 0.15.

Model predictive control, or MPC, deals with this by re-planning all the time, in four steps. First, it looks at where the block really is now. Second, it plans a short sequence of pushes from there with the model. Here the plan is 5 pushes, found by CEM. Third, it does only the first push of the plan, and throws the rest away. Finally, it goes back to the first step.

The short plan is called the horizon, and each new plan starts from the last plan, shifted by one push, so it already starts close to a good answer. This is called a warm start, and it is why CEM is enough inside MPC.

A diagram compares a plan made once against MPC. On the left, a plan is made once and carried out blind. It was planned with CMA-ES for all 8 pushes. In the model the plan ends 0.07 centimetres from the target. However, the real block slides less and drifts more, so it ends 5.4 centimetres from the target. Nothing corrected that error, because nothing ever looked at the real block.

On the right is MPC instead. It re-plans before every push. Its distance to the target after each push steadily dropped from 17.8 centimetres down to 0.3 centimetres, and it stayed within 0.7 centimetres for the last three pushes. The model was wrong every time, but each error was small and was corrected at the next look.

MPC for the block uses a slightly different score from the one-off plan. It adds up the distance to the target after every push, not only the last one, so the block gets there soon and then stays. It also adds a cost for coming within 1.5 centimetres of the mug's limit, and that margin is there because the model is not exact. Without it, a plan that passes the mug by a millimetre in the model can touch it in reality.

This is the same MPC that the page on controlling the move in Book 3 describes: solve a short optimisation from where you are now, do the first command, throw the rest away, and solve again. Book 3 also lists the solvers that use gradients, such as acados and Crocoddyl, while this page is the version for scores without a gradient.

The page then provides the pseudocode for putting the two together, with CEM first and then the MPC loop that calls it.

The cross-entropy method starts with a spread containing one value per number in a plan. For a set number of rounds, it generates a batch of plans by adding random normal numbers scaled by the spread to the mean. It clips each push to what the arm can do, and scores each plan by simulating it from the current state using the model. It finds the elites, which are the plans with the lowest scores, and updates the mean to their average, and the spread to how much they differ from each other. It then returns the best plan seen.

The MPC loop then uses this. It starts with a mean of zero pushes for the whole horizon. It loops until the task is done. Inside the loop, it measures the real world state, calls the cross-entropy method to get a plan, and does only the first push of that plan on the real arm. It then updates the mean by taking the plan, removing its first push, and adding a zero push at the end.

Random shooting is simply this cross-entropy method with one round and a very wide spread. CMA-ES instead replaces the two update lines with its own updates for the mean, the covariance matrix and the step size.

The next part discusses using a learned model inside MPC. The MPC above scored its plans with a push model written by hand, in which the block slides 0.8 times as far as the pusher and drifts 0.15 times to the left. Sometimes nobody can write such a model, and then the model can instead be learned from records of the arm pushing the block. The planner itself does not change at all when this happens. CEM, the horizon of 5 pushes, the warm start, the score and doing only the first push all stay the same. Instead, only the prediction step inside the scoring function is replaced. The page on learned dynamics models in Book 6 explains how such a model is built and trained.

A single learned model carries a danger that a written one does not, because the planner searches for the plan with the best predicted score. Where the model has seen no records its predictions are only guesses, and the planner is drawn to any guess that looks good. So the usual choice is an ensemble, which is several copies of the network, each trained from different random starting numbers on its own resampled copy of the records. Where the records are dense the copies agree, and where there are none they disagree. The planner therefore uses the copies' average as the prediction, and adds a cost for how far apart they end up. This keeps the plans where the model knows what happens.

The scoring code changes to roll the plan forward through each copy of the ensemble. It finds the middle, which is the average of the paths, and the spread, which is how far the paths are from the middle, added up over the horizon. The score is then the score of the middle path, plus a weight multiplied by the spread.

The example runs on a real block that differs from the written model in two ways. First, every push has 0.15 centimetres of random scatter. Second, a push longer than 3 centimetres starts to turn the block, so it drifts a further 0.3 centimetres for every centimetre beyond 3 centimetres. The arm records 200 random pushes, each at most 3 centimetres long, and five small networks learn from them. Each copy's average training error is about 0.18 centimetres, which is about the size of the scatter.

A diagram shows the forward slide and sideways drift against push length. Inside the grey band of recorded pushes, up to 3 centimetres, the five learned copies sit on the real block's line, and they are closer to it than the written model is. At 3 centimetres they end 0.05 centimetres apart on average. Beyond 3 centimetres, where there are no records, they spread apart, reaching 0.30 centimetres apart at 5 centimetres. None of them knows about the extra drift, so that spread is the only warning the planner ever gets. The written model is off everywhere.

Each version of MPC then ran 60 times on the real block, with 12 pushes per run. A table and a diagram compare the results. The written push model ended with a median distance of 0.6 centimetres from the target, but 22 of the 60 runs touched the mug, and 72 percent of the pushes were longer than 3 centimetres.

The learned ensemble using only the average was no better. It ended 0.6 centimetres from the target, 26 runs touched the mug, and 58 percent of pushes were longer than 3 centimetres. It was accurate where it had records, but the planner still chose long pushes, where it was only guessing.

With the learned ensemble plus a cost of 0.5 per centimetre of spread, the planner chose fewer long pushes. The runs that touched the mug fell to 13 of 60, and the median distance was 0.5 centimetres. However, sixty runs is only just enough to show this, because the 95 percent confidence intervals barely overlap. The page on evaluation and failure in Book 6 explains these intervals.

The weight on the spread is itself a setting to choose, and too much of it makes the planner timid. With a weight of 2 instead of 0.5, only 4 of 60 runs touched the mug, but only 4 of 60 ended within 1 centimetre, and the median run ended 3.9 centimetres short. In other words, the planner refused the long pushes it needed. PETS, described on the Book 6 page, is the standard published version of this method, and the mbrl-lib library provides it.

The fourth section covers where this is used on a robot arm. The pushing example is one case of a wider pattern, because sampling-based optimisation is used wherever a program can simulate a plan but cannot differentiate the result. Here are the concrete places it turns up on an arm.

First, pushing and sliding objects. An arm may push a mug out of the way before a grasp, or slide a box against a wall. The contact is hard to model with a clean formula, so a sampled plan through a rough model, corrected by MPC, is common.

Second, MPC with a learned model. The learned dynamics models in Book 6 plan with CEM and MPC through a neural network. The network has a gradient, but it is often unreliable, and CEM only needs the network's predictions.

Third, tuning controller gains. The gains of a PID controller can be scored by running a test move and measuring the overshoot and the settling time, so CMA-ES can tune a handful of gains this way, in simulation or on the real arm.

Fourth, choosing a grasp. Grasp quality models use CEM to refine grasp candidates towards the ones the model scores highest.

Fifth, paths with costs that have no gradient. STOMP, mentioned on the trajectory optimisation page, is sampling-based optimisation applied to a whole path. MPPI, or model predictive path integral control, is the same weighted-average idea used inside MPC.

Finally, fitting a model to measurements. When a simulator has unknown settings, such as friction, CMA-ES can choose the settings that make the simulator match recorded data, which is one approach to system identification.

The fifth section explains where it is useful, and where it is not. All of those uses rely on the same small requirement, because these methods need only one thing, which is a way to score a plan. That makes them easy to apply, but it also means they know nothing about the problem beyond the scores they see.

A table lists common problems, the signs you would see, and what people do instead.

If there are too many numbers in a plan, scores stop improving and plans look random. Instead, people use a shorter horizon, fewer numbers per push, or a gradient method.

If CEM narrows too early, every run stops at a different, mediocre plan. Instead, people use more plans per round, a minimum spread, or CMA-ES.

If scoring is slow, each plan takes seconds, so a search takes hours. Instead, people run many plans at once on a graphics card, or use a cheaper model.

If the model is wrong, the plan looks perfect in simulation and fails on the arm. Instead, people use MPC, which re-plans from the real state, and add a margin around obstacles.

If MPC is too slow for the control rate, the arm waits between pushes, or jerks. Instead, people use fewer plans, warm starts, or use MPC only for the slow outer loop.

If a score has a smooth, known gradient, sampling takes far more evaluations than needed. Instead, people use trajectory optimisation or a solver.

Finally, if there is a hard safety limit, sometimes a plan breaks the limit. Instead, people use a separate safety check, as Book 3 says MPC cannot replace a safety stop.

This last point is the one that matters most, because a sampled plan satisfies a rule only as far as its score punishes breaking it, and only in the model. So anything that must never happen needs its own check outside the optimiser.

The sixth section lists libraries that provide it. Because the methods themselves are small, CEM is short enough that most people write it themselves, as the pseudocode shows. CMA-ES is longer, so a library is the safer choice there. The page lists several well-known libraries.

For Python, pycma provides the reference CMA-ES by its author. Optuna includes a CMA-ES sampler inside a tuning framework, which is handy for gains. Nevergrad is a collection of gradient-free optimisers, including CMA. For C++, MuJoCo MPC includes a Predictive Sampling planner, which Book 3 recommends for building intuition. For sampling MPC on a graphics card, pytorch_mppi provides it for any model you give it. Finally, mbrl-lib provides CEM and MPC for learned dynamics models in Python.

For a first try, write CEM in NumPy around your own model and score. Then move to pycma when the plan has more than a handful of numbers and CEM stops improving.

The seventh section explains why to use sampling, and what it costs. With the methods, the uses and the libraries covered, this section answers the four questions for sampling-based optimisation: what it is, what it does for you, why it rather than the obvious alternative, and what it costs.

It is a family of methods that choose a plan by scoring many candidate plans in a model and moving the search towards the best ones. MPC then wraps it in a loop that re-plans from the real state after every step. Together they let an arm act well with only a rough model and a score, even when the score jumps, as it does when a block touches a mug.

The obvious alternative is a gradient method, such as the trajectory optimiser of this chapter. When a smooth gradient exists, a gradient method needs far fewer evaluations, and it scales to hundreds of numbers. However, it cannot use a score that jumps, a simulator it cannot look inside, or a learned model whose gradient is unreliable, while sampling can use all three. So choose sampling when the score has no useful gradient and the plan has tens of numbers rather than thousands. Choose a gradient method instead when the cost is smooth and you can write it down.

The second alternative is to plan once and then carry the plan out blind. That is cheaper, but the earlier MPC comparison shows what happens, because a plan that was perfect in the model missed by 5.4 centimetres on the real block. MPC costs a new search at every step, and in return it corrects that error for free.

The costs come in five parts. First is the sheer number of evaluations, because one decision takes hundreds or thousands of model runs. Second is that the result is random, so two runs give different plans. Third is that there is no guarantee of the best plan, only of a good one. Fourth is a dependence on the model, which MPC reduces but does not remove. Fifth is the settings you must choose, which are the number of plans, the number of elites, the horizon and the spread. On this page's problem, the choice of method alone changed the result from 9.2 centimetres to 0.2 centimetres.

The eighth section covers the learned alternative. Using a learned model inside MPC keeps the search and learns only the prediction, but the other learned alternative replaces the search itself. A policy that learns without a model, such as a reinforcement learning policy, turns the state straight into the next action in one pass, with no rollouts at each step. So it wins when each decision must be fast and the task stays fixed. However, Book 6 says it needs far more attempts to learn, and it learns only one task, while MPC with a model can push the block to a different mark tomorrow just by changing the score. So choose MPC when the goal changes, or when the search fits in the time between steps.

The final section suggests where to read next. The page on trajectory optimisation covers the gradient methods, and STOMP, the sampling method for whole paths. The page on controlling the move in Book 3 covers MPC in practice, and the gradient-based MPC libraries. The page on learned dynamics models in Book 6 explains the learned model that CEM and MPC most often plan through. The page on pushing and sliding in Book 3 explains the physics behind the pushing example on this page. The page on optimisation solvers covers the exact solvers for problems that can be written as equations. Finally, the page on PID control explains the gains that CMA-ES is often used to tune.
