Optimisation solvers. This page explains optimisation solvers, which are general programs that find the best choice among a very large number of choices while obeying rules you give them. It answers five questions. What do you have to tell a solver? What are linear, integer, and constraint programming, and how do they differ? How does a solver find the best answer without trying every possibility? Where does a robot arm need one? And when is a simple loop, or a greedy rule, the better tool?

This follows on from the page about greedy algorithms and set cover, because that page showed a quick rule that is usually close to the best answer. This page is instead about getting the best answer itself, and about what that costs. No mathematics beyond adding and multiplying is needed, since each term is explained where it first appears.

On a robot arm, solvers answer questions about tasks rather than about motion. For example, which part goes into which pocket of a tray, and in what order should the arm pick five objects when one of them blocks another? Or, how many of each item fit in a box before it is too heavy? These are the questions in the worked examples below.

The first section gives the idea in one sentence. Since a greedy algorithm gives up the best answer for speed, here is the tool that does not. An optimisation solver is a ready-made program that takes a description of your choices, your rules, and your score, and returns the choice that obeys every rule and has the best score.

Here is an everyday example of such a program: a school that has to make a timetable. The choices are which teacher teaches which class in which room at which hour. The rules are that no teacher is in two rooms at once, no room holds two classes at once, and every class gets its hours of each subject. The score might be the number of free gaps in the teachers' days, which the school wants to be as small as possible. But nobody writes a special program for this school. Instead, they write the choices, rules, and score in the form a timetable solver accepts, and then the solver finds the timetable.

That same split is what makes a solver useful on a robot, because you describe the task and the solver does the searching. So when the task changes, for example when a new rule says that one object must be picked before another, you add one line to the description rather than writing a new search algorithm.

The next part of the page explains what you tell a solver, and the three main kinds of solver. Because you describe the problem rather than the search, every problem you give a solver has the same three parts. The words used here are the standard ones, and every solver's documentation uses them.

First, the decision variables are the choices the solver makes. For example, "does part one go into pocket three?", with the answer one for yes and zero for no. Second, the constraints are the rules every answer must obey. For example, "each pocket holds exactly one part". Finally, the objective is the score. For example, "the total distance the arm travels", which the solver makes as small as possible.

Writing these three parts down is called modelling, and the result is called the model. So the model is the part you write, while the solver is the part you install.

There are three main kinds of solver, and they differ in what the variables and rules are allowed to look like. 

The first kind is linear programming, or LP. Its variables can be any number, including fractions. Its rules and score must be sums of variables multiplied by fixed numbers, compared using less than or equal to, equal to, or greater than or equal to. This suits blending and sharing amounts, such as how much time each arm spends on each job.

The second kind is mixed-integer linear programming, often shortened to MILP or MIP. Here, some variables must be whole numbers, often just zero or one. The rules are the same sums as in linear programming. This suits yes-or-no choices, like which part goes to which pocket, which camera views to use, or how many boxes to pack.

The third kind is constraint programming, or CP. Its variables are whole numbers chosen from a list of allowed values. It allows almost any rule, such as "all variables must be different", "A must happen before B", or "if this happens, then that must happen". This suits orders, schedules, and puzzles with many logical rules.

The word "programming" in these names is old, and it means "planning" rather than writing code. Linear programming was named in the 1940s, when a "programme" was a military plan.

A fourth kind, nonlinear optimisation, allows curved rules and scores, such as the distance between two joint positions. This is what trajectory optimisation and numerical inverse kinematics use, and those two have their own pages. This page stays with the first three, which are the ones used for task decisions.

The next section shows how it works, with three worked examples. Because the three parts of a model are easier to see on a real task, each example here is small enough that it can be solved exactly by trying every possibility. That gives a true best answer to compare against, and every number given comes from that exact search.

The first example is an assignment problem: which part goes in which pocket. Four parts, P1 to P4, lie on a table, and a kit tray at the front edge has four pockets, T1 to T4. The arm must put one part in each pocket, and the score is the total straight-line distance from each part to its pocket, in millimetres. 

The page shows a table of the distances from each part to each pocket. For example, part 2 is 130 millimetres from pocket 1 and pocket 2, but 277.3 millimetres from pocket 4. 

As a model, this problem has sixteen yes-or-no decision variables. A variable is 1 if a specific part goes to a specific pocket, and 0 otherwise. There are eight rules: for each of the four parts, the sum of its variables across all pockets must equal 1, meaning it goes to exactly one pocket. And for each of the four pockets, the sum of its variables across all parts must equal 1, meaning it receives exactly one part. The score is to minimise the sum of the distances multiplied by their matching variables.

There are twenty-four ways to assign four parts to four pockets, and trying all twenty-four gives the best one. The best assignment shifts each part one pocket along, sending P1 to T1, P2 to T2, P3 to T3, and P4 to T4, for a total of 564.9 millimetres. The worst of the twenty-four is 992.7 millimetres.

But the greedy rule, which says "take the closest remaining part and pocket first", does much worse. The diagram shows that greedy takes the shortest moves first, starting with P3 to T2 at 111.8 millimetres, which is the smallest number in the table. It then matches P2 to T1 and P4 to T3. This leaves P1 with only T4, the most distant pocket, requiring a long move of 411.5 millimetres. So the total for the greedy rule is 783.3 millimetres, which is 39 per cent more than the best.

The assignment problem does have a special property, however, because it has its own exact method called the Hungarian algorithm, which is fast even for hundreds of parts. This is explained more fully on the page about assignment and matching. So in practice, you would not call a general solver for this exact problem. Instead, you would call one as soon as a rule is added that the Hungarian algorithm cannot express, such as "P2 and P3 must not go into neighbouring pockets, because the gripper cannot fit between them".

The second example is about ordering: which object to pick first, with a rule. The assignment above had no rules beyond one part per pocket, so this example adds one. Five objects, A to E, stand on the table. The arm starts at the front left corner, picks all five, and ends at a bin at the front right corner. The score is again the total straight-line travel, but now there is one rule: object C stands in front of object B and blocks the gripper's approach, so C must be picked before B.

There are one hundred and twenty possible orders, and exactly half of them, sixty, pick C before B. The page shows a diagram of three of these orders, comparing their paths. 

The shortest order of all one hundred and twenty, ignoring the rule, is A, B, C, D, E, with a travel of 1031.3 millimetres. However, this shortest order breaks the rule, so it cannot be used. The shortest allowed order, which picks C before B, is A, C, B, D, E, and it costs 111.4 millimetres more. 

Meanwhile, the nearest-first greedy rule is 57 per cent longer than the best allowed order. Its first pick, C, is 339 millimetres from the start, and A is 342 millimetres, so C wins by only 3 millimetres. Then greedy works its way to the right, and it has to come all the way back for A at the end. The longest allowed order is nearly double the shortest.

This is the point of a solver. The rule "C before B" is one line in a model, whereas in a hand-written search it is a special case you have to remember to check. And a greedy rule can respect it only by refusing to pick B early, which does nothing to make the rest of its route good.

Finding rules like "C before B" from the scene using a blocking graph is explained on the page about ordering and rearrangement. The solver's job starts where that page's job ends, because once the rules are known, it finds the shortest order that obeys them.

The third example is about packing, and it shows why rounding a fractional answer fails. Both examples above chose between whole things, and this example shows why whole-number problems are harder than fractional ones.

An arm fills a shipping box that holds at most 6 items and at most 45 kilograms. A small item weighs 5 kilograms and is worth 5, while a large item weighs 9 kilograms and is worth 8. So how many of each should go in, to make the box worth the most?

The decision variables are the number of small items and the number of large items, which must be whole numbers. The rules are that the sum of the items must be less than or equal to 6, and 5 times the small items plus 9 times the large items must be less than or equal to 45. The score is to maximise 5 times the small items plus 8 times the large items.

The diagram shows this problem plotted on a graph, where each axis counts one kind of item. Each rule is a straight line, and the allowed answers lie below both lines. The shaded area shows the allowed answers if fractions of an item were allowed, while the black dots show the twenty-five whole-number answers that obey both rules.

If fractions were allowed, the problem would be a linear program, and a linear program has a useful property: its best answer can always be found at a corner of the shaded area, where two rule lines meet. So a linear programming solver only has to look at the corners. Here the best corner is where both rules are exactly met, at 2.25 small and 3.75 large items, worth 41.25.

The obvious next step is to round that down to whole numbers, giving 2 small and 3 large. That obeys both rules, but it is worth only 34. The diagram shows that the best whole-number answer is actually somewhere else entirely: 0 small and 5 large, worth 40. So it is not next to the fractional answer at all.

This is why integer problems need more than a linear programming solver and a rounding step, because the best whole-number answer can be far from the best fractional one.

The next part explains branch and bound, which is how an integer solver avoids trying everything. Since rounding fails, an integer solver uses the fractional answer as a guide rather than as the answer. The standard method for doing that has four steps.

First, solve the problem with fractions allowed. This is fast, because only corners need checking. Its score is a bound: no whole-number answer can beat it. Second, if the answer is already whole numbers, it is a candidate. Keep the best candidate found so far. Third, if some variable is a fraction, such as the large items equaling 3.75, split the problem into two smaller problems: one with the extra rule that large items are less than or equal to 3, and one where they are greater than or equal to 4. Every whole-number answer is in one of the two. This split is the branch. Fourth, solve each smaller problem the same way. If a problem's fractional score is no better than the best candidate so far, drop it without looking inside. No answer inside it can win.

On the packing example, it runs like this. The whole problem, with fractions, gives 41.25, at 2.25 small and 3.75 large. The solver splits on the large count. With large items less than or equal to 3, the fractional best is 39, at 3 small and 3 large. These are whole numbers, so this is the first candidate, worth 39. With large items greater than or equal to 4, the fractional best is 41, at 1.8 small and 4 large. That could still beat 39, so it splits on the small count. With large greater than or equal to 4 and small greater than or equal to 2, no answer obeys the weight rule, so it drops it. With large greater than or equal to 4 and small less than or equal to 1, the fractional best is 40.56, at 1 small and 4.44 large. It could still beat 39, so it splits on the large count again. With small less than or equal to 1 and large exactly 4, the best is 37. That cannot beat 39, so it drops it. Finally, with small less than or equal to 1 and large greater than or equal to 5, the best is 40, at 0 small and 5 large, in whole numbers. That beats 39 and becomes the answer.

So the solver solved seven small fractional problems and proved that 40 is the best. On a problem this size, that saves nothing over checking all twenty-five dots. But on a problem with hundreds of variables, the dropping in step four is what makes the difference between seconds and years. Real solvers add many refinements to this idea, and they all rest on it.

A constraint programming solver searches differently. It keeps, for every variable, the list of values that are still possible, and each rule removes the values that can no longer work. For example, in the ordering example, "C before B" means C can never be in the last position and B can never be in the first. Removing impossible values this way is called propagation. Then, when the rules can remove nothing more, the solver tries one value for one variable, propagates again, and backs up if it reaches a dead end. Modern solvers such as OR-Tools' CP-SAT combine this with the integer methods above.

The final part of this section explains when trying everything stops working. Each example above was solved by trying every possibility, which is the right method for small problems, because it is short, it is exact, and it cannot have a bug in its search. But the trouble is how quickly the number of possibilities grows.

With n places to visit, there are n factorial orders. A plain Python loop on the machine this page was written on checked about 630,000 orders a second. The page shows a chart and a table of what that rate means for different sizes. The time to try every order grows by a factor of n at each step. 

For 5 places, there are 120 orders, taking under a millisecond. For 8 places, it takes 0.06 seconds. For 10 places, there are over 3.6 million orders, taking 5.8 seconds. For 12 places, it takes about 13 minutes. And for 15 places, there are over 1.3 trillion orders, which would take about 24 days.

A faster language would reduce the time, but it would not change the shape, because each extra place multiplies the work by the number of places. That is where a solver earns its place, since it uses bounds and propagation to skip most of the possibilities. So it can solve problems far past the point where trying everything is hopeless.

The fourth section covers where solvers are used on a robot arm. Because a solver plans a whole set of choices at once, solvers are used for decisions about a whole task, made before the arm moves or between moves. Here are the common places.

First, filling a kit tray. Which part goes into which pocket, as in the first example. Rules like "heavy parts in the bottom row" or "no two tall parts side by side" make it a job for an integer or constraint solver rather than the Hungarian algorithm.

Second, pick order with blocking rules. The order in which to clear a cluttered table, as in the second example. The rules come from the blocking graph, and the solver finds the shortest order that obeys them.

Third, sharing work between two arms. Which arm picks which object, and in what order, so that both finish early and never reach into the same space at the same time. The "same space at the same time" rule is a scheduling rule, which constraint programming handles well.

Fourth, palletising and box packing. Which box goes where on a pallet, subject to weight, size, and stacking rules, as in the third example but with positions as well as counts.

Fifth, choosing camera views exactly. This is the set cover problem written as an integer program: one yes-or-no variable per view, one rule per object stating "at least one chosen view sees it", and the score being the "number of views chosen". This finds the true smallest set when a greedy algorithm is not good enough.

Sixth, scheduling tool changes and machine loading. When the arm serves several machines, which job to load next so that no machine waits, and when to change the gripper.

Finally, allocating a time budget. A linear program can split a fixed cycle time between inspection, picking, and placing, when each has a known effect on the score.

Nonlinear solvers, which are a different family, also run inside motion planning, because they smooth a path in trajectory optimisation and find joint angles in numerical inverse kinematics.

The next section explains where a solver is useful, and where it is not. The uses above all share one condition, because a solver is useful when there are many choices, when the rules matter, and when the difference between a good answer and the best one is worth real time or money. But it is less useful when the problem is tiny, when the scene changes after every move, or when the model leaves out something important.

The page provides a table of common situations, what you would see, and what to do instead. 

If the problem is tiny, such as fewer than about eight objects, you will see the solver take longer to start than a loop takes to try every order. Instead, try every possibility in a plain loop.

If the scene changes after every pick, you will see the best order being recomputed each time, and only its first step is used. Instead, use a greedy rule, or a solver with a short time limit.

If the model leaves out a rule, such as a joint limit or a collision, you will see that the solver's best answer cannot be carried out on the arm. Instead, add the rule to the model, and check each answer with the motion planner before moving.

If straight-line distance stands in for arm travel time, you will see that the "shortest" order is not the fastest on the real arm. Instead, measure move times between places and use those in the model.

If the problem is large and the time budget short, you will see the solver run until its time limit and return its best answer so far, without proof. Instead, accept a good answer by setting a time limit and starting from a greedy answer.

If rules contradict each other, the solver will report that no answer exists. Instead, find the smallest set of clashing rules; some solvers can report this.

Finally, if the rule is really a preference, such as "try to pick red first", you will get no answer, or a poor one, because a wish was written as a hard rule. Instead, move the preference into the score with a weight.

One sign is worth knowing in particular. If the solver returns an answer that the arm cannot carry out, the fault is almost never in the solver but in the model. This is because a solver finds the best answer to the problem you wrote, not to the problem you meant.

The sixth section lists libraries that provide solvers. Optimisation solvers are large, well-tested programs, so almost nobody writes their own. The page lists several well-known ones. Google OR-Tools is available in C++, Python, Java, and C sharp. Its CP-SAT solver is the usual first choice for assignment, ordering, and scheduling with logical rules. It also provides a linear solver interface, a routing model for visiting orders, and a fast exact assignment solver. In Python, SciPy provides linear and mixed-integer programs with no extra install, as well as exact assignment. HiGHS is a fast open-source linear and integer solver available in C++, Python, and others. PuLP and Pyomo are Python tools for writing models and handing them to solvers. MiniZinc is a standard language for constraint models. And CasADi is used for nonlinear optimisation, like trajectories. Commercial solvers such as Gurobi and CPLEX are also widely used, and they are often faster on very large integer problems, so the modelling tools mentioned can call them.

The next section summarizes why to use a solver, and what it costs. 

First, what it is. An optimisation solver is a general program that finds the best answer to a problem you describe as choices, rules, and a score. The three main kinds are linear programming for fractional amounts, integer programming for yes-or-no and whole-number choices, and constraint programming for orders and logical rules.

Second, what it does for you. It separates what you want from how to search for it. You write the task, and then a tested program does the search, with bounds that let it skip most of the possibilities. So it gives the best answer, or else tells you how far its answer can be from the best, and new rules are one line each. In the examples above, the solver's answer beat the greedy rule by 39 per cent on the tray and by 57 per cent on the pick order.

Third, why a solver rather than the obvious alternative. There are two obvious alternatives, and each wins in its own range. The first is trying every possibility in a loop, which is exact and has no dependency, so below about eight to ten items it is the better choice. But the solver wins past that, because the loop's time grows by a factor of n for every extra item. The second alternative is a greedy rule, which is fast and simple, and it wins when the scene changes after every move, because a perfect long plan would then be thrown away anyway. The solver wins instead when a plan is followed for many steps or many cycles, or when the rules are what make the task hard. This is because a greedy rule cannot plan around a rule, and it can only refuse a choice that breaks one.

Finally, what it costs you. It costs a dependency, and time spent learning to model. Writing a good model is a skill, because the same problem can be written in ways that solve in a second or not at all. It also costs predictability of run time, because a hard problem can take much longer than an easy one of the same size, so a robot needs a time limit and a fallback answer. And it costs trust in the model, because the answer is only as good as the rules and the costs you wrote. So straight-line distances, missing collision rules, and hard rules that should have been preferences all show up as answers the arm cannot use.

The eighth section discusses the learned alternative. No learned model finds the best assignment, order, or packing under hard rules. This is because a network gives no proof that its answer obeys every rule, or of how far it is from the best, while a solver gives both. The nearest learned model is a language model as planner, which turns a request in plain words into a sequence of steps. It wins when the task itself changes from day to day and is easier to say than to write as a model, but it can write steps that sound right and are wrong, so its plan needs a checker in ordinary code. A common design uses both: the language model writes the goal and the rules, and a solver finds the order.

The page then lists where to read next. The page about greedy algorithms and set cover is the fast approximate alternative. The page on assignment and matching explains the Hungarian algorithm. Trajectory optimisation uses nonlinear optimisation to shape an arm's path. Behaviour trees show how the plan a solver produces is carried out step by step. The chapter overview compares all the decision techniques. And the page on ordering and rearrangement explains where ordering rules come from, and why the plan should be recomputed after every move.

The final section shows how to use solvers in Python. It writes the kit-tray assignment model in Python twice, to show when a short call is enough and when you need a longer one.

The first version is the short call. It uses SciPy's linear sum assignment function, which solves assignment exactly, and for a bare assignment problem it is all you need. The code defines the distances in a matrix, passes it to the function, and prints the result. It pairs each part with the pocket of the same number, which is part 1 to pocket 1, part 2 to pocket 2, and so on, for a total of 564.9 millimetres. That is the best of the twenty-four possibilities, and it is the same answer found earlier by trying them all.

The second version is longer, and it is used as soon as a rule appears that assignment alone cannot express, such as "part 2 and part 3 must not go into neighbouring pockets". The short call cannot help here, but OR-Tools CP-SAT can, because you write the rules yourself. 

The code creates a model, defines the boolean variables for each part and pocket, and adds the rules that each part goes to one pocket and each pocket takes one part. Then it adds the extra rule preventing part 2 and part 3 from being in neighbouring pockets. Because CP-SAT works in whole numbers, the distances are scaled to tenths of a millimetre before being set as the score to minimise. The solver is given a time limit of five seconds, and it solves the model. 

With that extra rule, the best total rises from 564.9 millimetres to 619.4 millimetres, and the solver swaps part 1 and part 2 so that part 2 sits in pocket 1 while part 3 stays in pocket 3. The cost of the rule is therefore 54.5 millimetres, and knowing that number is often the reason to write the model at all.

What the libraries do for you here is genuinely most of the job. CP-SAT runs the branch-and-bound search, proves that no better answer exists, and reports optimal when it has done so, or feasible when it ran out of time with an answer in hand. You never write a search.

What you still write is the model, and every line of it is a claim about your cell. The variables, the rules, and the score are yours. So is the distance matrix, and building it is usually the larger task, because those numbers have to come from real positions rather than from a guess. You also write what happens when the solver reports that the problem is infeasible, which means your rules contradict each other and which the arm has to survive.

What you have to decide or measure is the scale, the time limit, and the score itself. CP-SAT accepts only whole numbers, so a distance in millimetres with one decimal has to be scaled, and scaling too coarsely quietly changes which answer is best. The time limit matters because on a large model a solver without one keeps searching for proof long after it has a good answer, so setting a budget and accepting the best answer found inside it is the normal choice. Finally, the score is a decision and not a fact: minimising distance is not the same as minimising time, and if what you care about is the cycle time, then the numbers in that matrix should be measured travel times.
