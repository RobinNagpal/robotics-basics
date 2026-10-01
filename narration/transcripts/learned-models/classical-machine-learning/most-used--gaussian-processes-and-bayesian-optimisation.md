Gaussian processes and Bayesian optimisation. This page explains two methods that belong together. A Gaussian process learns a smooth curve from a few examples, and it gives an error bar with every answer. Bayesian optimisation then uses a Gaussian process to decide which setting to try next, when every try is slow or costly, such as a test run on a real arm.

It answers five questions, and the sections below take them in turn. What does a Gaussian process predict, and how? What decides how smooth its curve is, and how much it trusts each measurement? Why does it get slow with many examples? How does Bayesian optimisation choose the next trial? And where does a robot arm use the two, for example to tune a controller in 15 trials instead of 100?

It is for a reader who has read the first chapter of this book, especially how a model learns. So you need to know what an example, a label and overfitting are. The chapter overview compares a Gaussian process with the other methods on one small dataset.

Every number on this page comes from a real run of a simulated dataset, so that the true answer is known exactly. But the methods themselves are real, and they are written in NumPy. Before this page, it helps to have read the page on PID control in Book 5. The Bayesian optimisation examples tune its gains, on the same simulated joint.

The first section gives the idea in one sentence. A Gaussian process predicts a number together with an error bar, by assuming that similar inputs give similar answers, and Bayesian optimisation uses those error bars to pick each next trial where the answer looks good or is still unknown.

For example, imagine you are adjusting a shower with a single knob. You try the middle and the water is too cold, then you try far to the right and it is too hot. You do not now try every position from left to right, because you can guess that the right temperature lies between your two tries, closer to the hot one, and you try there next. You also know how sure you are, since you are very sure near the positions you tried and less sure in between. A Gaussian process is that guess with its sureness written as numbers, and Bayesian optimisation is the habit of picking the next knob position from that guess.

The next section explains how a Gaussian process works. The previous section called the shower guess a number with a sureness attached, so this part says what those two numbers really are. A Gaussian process, or GP, takes a set of examples, which are inputs with a measured label for each. For any new input it gives two numbers, where the first is its best guess of the label. The second is a standard deviation, which is a typical size of how wrong that guess may be. This page draws the error bar as two standard deviations each side of the guess, so if the model is right about itself, the truth falls inside that band about 95 times in 100.

The name comes from the Gaussian, or normal, distribution, which is the bell-shaped spread of values. A GP treats the unknown curve as a random curve whose values are spread in that bell shape. It then keeps only the curves that pass close to the examples. So their average is the guess, and how much they disagree is the error bar.

You do not need to follow the maths to use a GP, because you only need to know the two things that you choose: the kernel and the noise.

The kernel is a formula that says how alike the answers at two inputs should be, given how far apart the inputs are. So it gives 1 for two identical inputs, and falls towards 0 as the inputs move apart. The most used kernel falls in a bell shape, and it has two settings. First is the length scale, which is how far apart two inputs can be and still have similar answers. Second is the signal size, which is how far the curve typically moves away from its average.

The page shows a diagram of this kernel with three length scales. With a length scale of 0.3, two inputs 0.1 apart score 0.95, which means nearly the same answer, while two inputs 0.3 apart score 0.61. Two inputs 1.0 apart score 0.00, so knowing one of them tells you nothing about the other.

The diagram also shows what the length scale means for the curve, by drawing random curves that the kernel allows before the GP has seen any example. A length scale of 0.1 allows curves that wiggle quickly, while a length scale of 1.0 allows only slow, gentle curves. So choosing the kernel is choosing what kind of curve you expect.

Then, to predict at a new input, the GP scores how alike that input is to each example, using the kernel. It then takes a weighted average of the examples' labels, with the more alike examples counting more. The error bar comes from those same scores, so if no example scores highly, the guess rests on little and the band is wide.

A real measurement is never exact, so the GP has a third setting, the noise, which is the typical size of the error in each measured label. If the noise is small, the GP believes each example and bends its curve to pass through all of them. But if the noise is larger, it lets the curve pass between examples that disagree.

You rarely set these three numbers by hand, because the usual way is to try many combinations and keep the one under which the measured examples are most likely. This measure is called the marginal likelihood, and it prefers a curve that fits the examples while also punishing a curve that is more wiggly than the examples need. So it guards against overfitting by itself, without a separate test set.

The page then gives a worked example, which is a correction to a friction model. Book 5's PID page uses a joint whose friction follows a simple rule: 0.5 newton metres of torque for each radian per second of speed. But a real joint also has friction that this rule misses, and that extra friction is strongest just after the joint starts to move and changes sign with the direction. So the robot measures the missing torque at 24 speeds and wants a curve through them. The input is the joint speed in radians per second, and the label is the missing torque in newton metres. Each measurement has noise of 0.04 newton metres.

The measurements cover speeds from minus 1.0 to 0.45 radians per second, and a few more between 1.15 and 1.4 radians per second. So there is a gap between the two groups, and nothing beyond them.

A diagram shows these 24 measurements fitted in two ways. The first way forces the noise to 0.001 newton metres, which is far below the true 0.04, so the GP must pass through every dot. To do that it chose a short length scale of 0.1 radians per second, and the curve swings wildly between the dots. Its average error against the true curve, over the measured range, is 0.804 newton metres, which is twenty times the noise.

But the second way lets the marginal likelihood choose all three settings. It chose a length scale of 0.6 radians per second, a signal size of 0.2 newton metres and a noise of 0.05 newton metres, which is close to the true 0.04. So the average error over the measured range is 0.042 newton metres.

A table reads this second GP at four speeds. At 0.0 radians per second, which is among the examples, the GP answers minus 0.054 plus or minus 0.042 newton metres, while the true value is 0.000. At 0.8 radians per second, which is in the gap, the GP answers 0.273 plus or minus 0.108, and the truth is 0.203. At 1.3 radians per second, again among the examples, it answers 0.154 plus or minus 0.053, and the truth is 0.144. Finally, at 1.9 radians per second, which is beyond all examples, it answers 0.015 plus or minus 0.278, and the truth is 0.072.

So the band is narrow among the examples and wide in the gap and beyond. At 1.9 radians per second the GP says, in effect, "I do not know", because its band covers minus 0.26 to 0.29 newton metres. A controller can use that, since it can add the learned torque only where the band is narrow.

The first row of the table shows a real weakness, because at 0.0 radians per second the truth lies just outside the band. The true friction changes sharply near zero speed, but the GP chose one length scale for the whole curve. A length scale of 0.6 is right for the gentle parts and too long for the sharp part, so the band is too confident exactly where the curve bends fastest. This will be discussed more in the section on what goes wrong.

The section ends by explaining why a GP slows down with many points. A GP keeps every example, and it compares each example with every other one, so the cost grows quickly with the number of examples. With n examples it builds a table of n times n kernel scores and solves a set of equations with it. The work to solve that grows with the cube of n, at about n cubed divided by 3 multiply-adds.

For 1,000 examples, this is about 330 million multiply-adds, which is a fraction of a second on a laptop, and the table takes 8 megabytes. For 10,000 examples, it is a thousand times the work, and the table takes 800 megabytes. For 100,000 examples, it is a million times the work of 1,000, and a table of 80,000 megabytes, which is more memory than most computers have.

So a plain GP suits hundreds to a few thousand examples, which is often all a robot has, because each example is a real measurement. For more than that, libraries use approximations. The most common one keeps a few hundred inducing points, which are a small set of stand-in examples, and compares everything with those instead.

The third section covers Bayesian optimisation, which is choosing the next trial. The previous section built a curve with an error bar, and Bayesian optimisation is what you do with that error bar when each try is slow or costly. It keeps a GP of the score against the setting, and it uses the GP's guess and error bar to pick the next setting to try. Then it runs the trial, adds the result to the GP, and repeats.

On a robot, a try is often a real run of the arm, like a step move to test controller gains, or ten grasps to test an approach. Because each run takes seconds to minutes and wears the hardware, the aim is to find good settings in tens of trials rather than thousands.

The page gives an example of tuning one gain, step by step. A joint is told to move from 0 to 0.5 radians. The proportional gain is fixed at 20, and the integral gain at 5. So the task is to find the best derivative gain between 0 and 2.

Each trial runs the move for one second and gives one score, where lower is better. The score adds three things: the average distance from the target, how far the joint overshot the target, and how much the motor torque jittered from one tick to the next. Too little derivative gain overshoots, while too much makes the torque jitter, because it multiplies the noise in the angle sensor. Each trial also has a little chance in it, because the sensor noise differs and the load changes by a few percent from run to run, as it does on a real arm.

A sweep of 201 settings shows the answer that the method does not know: the best gain is 0.69, with a score of 11.02. But a gain of 0 scores 24.09, and a gain of 2 scores 21.85.

The loop that finds a setting like that works in a sequence. First, run a few trials spread over the range, which here are 0.10, 1.00 and 1.90. Second, fit a GP to the scores you have so far. Third, for every gain in the range, work out how promising a trial there would be. This number is called the acquisition function. Fourth, run the next trial where the acquisition is largest. Fifth, go back to the second step, until the trial budget is spent. Finally, keep the best setting that the loop found.

A diagram shows three steps of this process. After 3 trials, the best score so far is 13.75, at a gain of 1.00. The GP knows little between the trials, so the band is wide and the acquisition is high on both sides of 1.00. It picks 0.89. The fourth trial, at 0.89, scores 12.62, so the GP now leans left and picks 0.70, and that trial scores 10.93. After 5 trials the GP has found the dip, so it picks 0.64, just beside the best. After 6 trials it picks 1.38, because that area was still unsure and the GP checks that nothing better hides there. After 7 trials it picks 0.72. After 8 trials, the best measured score is 10.77, at a gain of 0.72.

So eight trials found a gain within 0.03 of the best one on a 201-point sweep. The best measured score, 10.77, is even lower than the swept best of 11.02, but that is not a better gain. It is one lucky trial, because the chance in each run happened to help. This is why the GP has a noise setting, and why a careful user re-runs the kept setting a few times before trusting its score.

The third step of that loop left the acquisition function undefined, so the page fills it in. The acquisition function turns the GP's guess and error bar into one number per setting, and two of them are used most.

Expected improvement, or EI, asks: if I try here, by how much will I beat my best score so far, on average? A setting scores high if the guess is already better than the best so far. It also scores high if the band is wide, because a wide band leaves room for a much better result. A setting whose whole band is worse than the best so far scores almost zero.

Upper confidence bound, or UCB, asks a simpler question: how good could it be here, if I am optimistic? So it takes the guess and moves it by a set number of error bars in the good direction. The name comes from problems where a higher score is better, so for a score where lower is better, as here, it is the guess minus the error bar. A setting wins if it looks good, or if it is so unsure that it might be good. The number of error bars sets the balance, because more error bars send trials to unexplored places, while fewer send them close to the best so far.

The balance between the two aims has a name: exploration, which is trying where the model is unsure, against exploitation, which is trying where the model is already hopeful. Both acquisition functions weigh those two aims, and in the one-gain run they agreed closely. After 3 trials expected improvement picked 0.89, while the bound with two error bars picked 0.83.

Most controllers have more than one gain, so the page shows tuning the proportional and derivative gains together. The proportional gain may lie between 2 and 200, and the derivative gain between 0.02 and 5. Both are searched on a log scale, where each step multiplies the gain by the same factor. People often do not know a gain's size to within a factor of ten, so a log scale spreads the trials fairly.

A sweep of 1,681 settings shows the landscape, where the best score is 10.83. Only 3.2 percent of the settings score within 1 of that, and the worst scores 76.1.

The script ran three methods, each with 15 trials, 20 times over with different chance. Both Bayesian optimisation runs start with 4 random trials and then let the GP choose the other 11, and the UCB run uses one error bar. The third method runs all 15 trials at random settings.

A diagram shows a typical run of Bayesian optimisation on this two-gain landscape. The first 4 trials, at random, land in poor places, but from trial 5 on the GP moves into the valley of good scores and stays there. So it keeps a proportional gain of 8.0 and a derivative gain of 0.07, whose true score is 11.39. That is not the sweep's best setting, but the valley is long, and settings along it score nearly the same.

A table gives the result after all 15 trials, averaged over the 20 runs. Bayesian optimisation with UCB averaged 11.44, and its worst run was 12.40. Bayesian optimisation with expected improvement averaged 11.78, but its worst run was 18.22. Random trials averaged 12.75, with a worst run of 15.92.

Bayesian optimisation with UCB reached 12.67 after 8 trials, while random trials needed all 15 to reach 12.75. So on this problem it saved about half the trials, and on a real arm, where each trial takes a minute and a person must watch, that matters.

Expected improvement did well on average, but one of its 20 runs ended at 18.22, because that run never found the valley in its 15 trials. No acquisition function is best on every problem, and with 15 trials one unlucky run can happen. So a common fix is to run the kept setting a few more times, and to compare it with the hand-tuned gains before accepting it.

The fourth section explains how a GP is trained, and how much data it needs. The previous section spent its examples one trial at a time, so this part says how many a GP needs in general. A GP needs a table of examples, where an input may be several numbers and each input has one measured label. Training means choosing the kernel's settings and the noise, by the marginal likelihood, and after that the examples themselves are the model. Adding an example means refitting, which is quick while the examples number in the hundreds.

A GP works well from very few examples, because the friction curve used 24 and the one-gain tuning used 8. So with 2 to 5 inputs, a few tens of examples often give a useful curve. It works less well with many inputs, because each input needs its own length scale and the space to fill grows fast. So Bayesian optimisation is usually used with up to about 10 or 20 settings, since beyond that the GP cannot learn the landscape from a few tens of trials.

Before fitting, scale each input to a similar range, for example 0 to 1, and subtract the average from the labels. In the two-gain example, the script also takes the logarithm of the PID score, because a few very bad settings, with scores up to 76, would otherwise squash the differences between the good ones.

The fifth section lists where the two methods are used on a robot arm. Since a GP wants few examples with few inputs, six jobs on an arm look exactly like that. First is tuning controller gains on the real arm. This is the main example, where a PID loop or an impedance controller has gains that a model gets roughly right and the real arm gets exactly right. Bayesian optimisation runs a short test move, scores it, and picks the next gains, often reaching good gains in 15 to 30 trials.

Second is tuning grasp approach settings. A pick routine has settings that no model predicts well, like how far above the object to pause, how fast to descend, or how hard to close. Each trial is a batch of grasps, scored by how many held, and Bayesian optimisation picks the next batch's settings.

Third is learning a small correction to the arm's dynamics. This is the worked example of friction, where a formula gives the torque each joint should need, but a real arm needs a little more or less. A GP learns that difference from logged motion, and the controller adds the learned torque as feed-forward, using the error bar to add less where the GP is unsure.

Fourth is learning a whole small dynamics model to plan with. Methods like PILCO learn a GP model of how a system moves from a few minutes of real data, and then improve a controller inside that model, using the error bars to avoid trusting the model where it has no data.

Fifth is correcting a sensor, such as learning a depth camera's error at each distance. Finally, choosing where to measure next. The error bar shows where the model knows least, so a robot mapping a surface's height or a sensor's error can measure next where the band is widest.

The sixth section covers what goes wrong. Seven things happen often enough to be worth looking for. First, one length scale for the whole curve. A curve that is gentle in one place and sharp in another gets one compromise length scale, and the band is then too narrow at the sharp part. You can fix this by giving the GP an input that makes the sharp part gentler, or by adding a written formula for the known part and letting the GP learn only the rest.

Second, the noise is set wrong. Too little noise makes the curve chase every dot, while too much noise makes the curve flat and ignores real bumps. So let the marginal likelihood choose, and check the chosen noise against what you know about the sensor.

Third, trusting the band beyond the data. Far from all examples, the GP returns to its average, with a wide band. The band is honest there, but the guess is not a prediction at all, so do not act on a guess whose band is wide.

Fourth, too many inputs. Bayesian optimisation over 30 settings does not work in 30 trials, so choose the few settings that matter most and fix the rest by hand.

Fifth, unsafe trials. Bayesian optimisation happily tries a gain that makes the joint shake, because that area is unsure. On a real arm, limit the search range to gains you know are safe, stop any trial that trips a limit, and give it a bad score. Safe Bayesian optimisation only tries settings that the GP is confident will stay within a safety limit.

Sixth, chance in each trial. One lucky trial can look like the best setting, so re-run the kept setting and let the GP's noise setting absorb the chance.

Finally, the world changes. Gains tuned with one gripper may be wrong with another, so re-tune whenever the hardware changes.

The seventh section lists the libraries you would use, rather than writing a Gaussian process yourself. Scikit-learn provides a Gaussian process regressor with kernels like the bell shape and the noise. It chooses the settings by the marginal likelihood and is good for up to a few thousand examples. GPyTorch provides Gaussian processes on PyTorch, with approximations for large data and graphics-card support. BoTorch is Bayesian optimisation on top of GPyTorch, from Meta, providing the GP models and acquisition functions. Ax is Meta's platform built on BoTorch, which runs the whole loop for you. Optuna is a popular tuning library that offers a GP-based sampler. And GPy is an older, well-known Gaussian process library in Python.

The eighth section explains why you would choose these methods and what they cost. A Gaussian process draws a smooth curve through a few examples and gives an error bar with every answer. Bayesian optimisation uses it to choose each next trial when trials are costly. It learns from tens of examples, not thousands, and tells you where it is unsure. For tuning, it saves trials, needing about half as many as random search for the same result.

For a curve from few examples, the obvious alternative is ridge regression or a small neural network. But ridge regression needs you to choose the curve's shape and gives no error bar, while a network needs far more examples. So choose a GP when examples are few and the error bar matters.

For tuning, the alternatives are hand tuning, a grid of settings, and random trials. Hand tuning is fast for one gain but slow for several. A grid spends many trials on poor settings, and random trials are only good when trials are cheap. So choose Bayesian optimisation when each trial is expensive and there are fewer than about 10 or 20 settings.

The costs are that you must choose a kernel, which is a guess about the kind of curve, and you must write a score that truly says what "good" means, because the optimiser finds any gap in it. The GP also slows down beyond a few thousand examples, and the method gives no guarantee, because the kept setting still needs checking and the search range must be safe.

The ninth section looks at the written alternative, because Book 5 does both of these jobs without learning at all. For tuning, Book 5 tunes PID gains by hand in a fixed order, or works out impedance damping from a formula. The written way wins when a formula or a skilled person gets close in a few tries. Bayesian optimisation wins when several settings interact, when the score is something only a real trial can measure, and when a person's time is the scarce thing.

For learning a correction to the arm's motion, Book 5 fits the numbers in a physics formula by least squares. It wins whenever the formula has the right shape, because it needs fewer examples and behaves sensibly far from the data. A GP is for what is left over when the formula is known to miss something. So the usual choice is both: the physics formula first, and a GP on what it gets wrong.

For search in general, Book 5's sampling-based optimisation tries many settings and narrows the search around the best. It needs no model of the score and wins when a trial is cheap, as in a simulator. So Bayesian optimisation wins when each trial is a run of the real arm.

The tenth section suggests where to read next. You can read about nearest neighbours and locally weighted regression, which also predicts from the examples nearest the new input. Linear and logistic regression covers ridge regression, the simpler alternative for a curve. The page on uncertainty and confidence explains how a robot turns an error bar into a decision. Learned arm models covers corrections to the arm's dynamics with larger models. Reinforcement learning policies learns a whole controller by trial, when there are far too many settings for Bayesian optimisation. And Book 5's system identification is the physics-first way to learn the arm's numbers.

The final section shows how to use it in Python. It puts the libraries together so you can fit a Gaussian process to the trials you have run and work out where to run the next one.

The code imports the Gaussian process regressor and kernels from scikit-learn. It creates a kernel by adding a Matern kernel, which sets the length scale, to a WhiteKernel, which sets the noise level. It then fits the model to the gains and scores from the trials so far. The library chooses the kernel's settings for you by maximising the marginal likelihood, and you can print what it chose.

To find the next trial, the code predicts the guess and the error band for a grid of candidate settings. It then calculates the upper confidence bound. Because the score on this page is one where lower is better, the optimistic value at each setting is the guess minus two error bars, and the next trial goes where that is smallest. The two is the number of error bars that sets the balance between trying near the best result so far and trying where the model is unsure.

The library gives you the matrix algebra, which is the part that slows down as the number of points grows. It also shifts and scales the scores internally. What you have to write is the loop around this code. You run the trial on the arm, turn the run into one score, append the setting and the score, and fit again. That scoring function is the part that decides whether the whole method works.

What you have to decide is the kernel, and it is the one real choice here. The Matern kernel is the usual first pick for physical measurements because it allows a slightly rougher curve than the bell shape does, and real hardware rarely responds as smoothly as the bell shape assumes. You also decide the noise level and the number of error bars. If you would rather not write the loop at all, libraries like BoTorch and Ax run it for you.
