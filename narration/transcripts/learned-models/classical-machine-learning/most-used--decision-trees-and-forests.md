The page is titled Decision trees and forests. It explains decision trees, and the two ways of joining many trees together, which are random forests and gradient-boosted trees. It answers five questions. How does one tree make a decision? How does it choose its questions? Why does a deep tree go wrong on new data? How do many trees fix that? And where does a robot arm use them?

The page assumes you have read the earlier chapter on how a model learns, so you need to know what an example, a label, a training set, a test set, and overfitting are. 

Trees are the most used learned method for tabular data, which means data that fits in a table, where each row is one example and each column is one measured number. On a robot arm, that kind of data means logged grasps, force readings, motor currents, and temperatures. Every number on this page comes from a real run of a script. The data is simulated from a made-up rule, so that the true answer is known, but the methods themselves are real, and they are written in NumPy.

The first section gives the idea in one sentence. A decision tree reaches an answer by asking a short chain of yes-or-no questions, each about one input number, and it learns which questions to ask, and in what order, from examples. 

For example, a doctor on the phone decides whether you need to come in by asking, "Is your temperature above 38 degrees? If yes, have you had it for more than three days?" Each question looks at one thing, and the answer to one question decides which question comes next. After two or three questions the doctor has an answer, and a decision tree works the same way. The difference is that nobody writes the questions, because the tree picks them itself by looking at many past cases. 

A decision tree is not the same thing as a behaviour tree, which is a hand-written plan that decides what a robot does next. The two kinds of tree share only the word "tree".

The next part of the page explains how one tree works. It follows one tree while it learns its questions from examples. The example here is a slip detector, where a robot gripper holds an object. A force sensor in each finger measures two forces, which are how hard the fingers squeeze and how hard the object pulls sideways along the finger pads. Then the program computes two features from those readings, where a feature is one input number, made from the raw readings, that the model uses.

First is the sideways ratio, which is the sideways force divided by the squeezing force, and it runs from zero to one. When it gets near the friction of the surface, the object starts to slide. Second is the shaking, which is how much the force signal shakes quickly, again from zero to one. This matters because a slide makes the force shake before the object falls out.

Each example is one short moment of a grip, and its label says "slipping" or "holding". The made-up true rule is that the object slips when the ratio is above zero point six two, or when the ratio is above zero point three eight and the shaking is above zero point five five. The script then flips eight percent of the labels at random, because real labels are never perfect, and this makes the problem fair. So it has two hundred examples to learn from, and four thousand more to test on.

The section moves on to choosing a question. A tree grows from the top, so at the start all two hundred examples sit in one group. The tree then looks for one question that splits that group into two groups that are as pure as possible, where a pure group holds only one label.

To measure how mixed a group is, trees usually use the Gini impurity. For a group with a share p of slipping examples, this is two times p times one minus p. It is zero when the group is pure, and zero point five when the group is half and half. The two hundred examples hold one hundred and six slipping and ninety-four holding, so the Gini impurity at the top is zero point four nine eight.

For a split into two groups, the tree takes the Gini impurity of each group, weights it by the group's size, and adds the two. Then it searches. First, it takes the first feature, and sorts the examples by it. Second, it tries a cut between every pair of neighbouring values, and for each cut computes the weighted Gini impurity of the two groups. Third, it does the same for every other feature in the table. Finally, it keeps the cut with the lowest value, because that cut becomes the question at this point in the tree, which is called a node.

A diagram shows this search for the first question. It shows the two hundred examples split by the best first cut, alongside a graph of the Gini impurity after every possible cut on each feature. The graph shows that cuts on the shaking barely help, because the best one, at zero point zero nine, only brings the value down to zero point four seven four. Cuts on the sideways ratio help much more. A cut at zero point two gives zero point four three eight, a cut at zero point five gives zero point three six nine, and the lowest is at zero point six one seven, which gives zero point three two three. 

So the first question is, "Is the sideways ratio above zero point six one seven?". The left group then holds one hundred and twenty-four examples, thirty-seven of them slipping, with a Gini impurity of zero point four one nine, while the right group holds seventy-six examples, sixty-nine of them slipping, with a Gini impurity of zero point one six seven.

The tree then repeats the same search inside each group, and again inside each of their groups. Each group that is not split any further is called a leaf, and a leaf's answer is the most common label of the training examples in it. Its share of slipping examples can also serve as a rough chance. This search is greedy, which means it picks the best question for this step only, without looking ahead. This is fast, but it can miss a pair of questions that would only help when they are used together.

Next, the page covers depth and overfitting. The search above never stops on its own, so the size of the tree has to be limited. The depth of a tree is the largest number of questions on any path from the top to a leaf, and if you let it, a tree keeps splitting until every leaf is pure. 

A diagram compares a tree of depth three with a tree that has no limit, and plots their accuracy against depth on training and new data. The tree of depth three found a specific set of questions. It first asks if the sideways ratio is at most zero point six one seven. If yes, it asks if the shaking is at most zero point five five three. If yes, it says holding. If no, it asks if the ratio is at most zero point three six nine, saying holding if yes, and slipping if no. If the answer to the very first question was no, it says slipping. 

This is close to the true rule, with cuts at zero point six one seven, zero point five five three, and zero point three six nine, against the true zero point six two, zero point five five, and zero point three eight. However, the tree with no limit grew to depth eleven, with forty-five leaves, and it gets every training example right. It does so by drawing thin boxes around each flipped label, so on new data it does worse, getting eighty-four percent right against ninety-one percent for depth three.

A table shows the pattern behind those numbers as depth increases from one to eleven. The score on the two hundred training examples rises steadily from seventy-eight percent at depth one to one hundred percent at depth eleven. But the score on four thousand new examples peaks at ninety-one point three percent at depth three, and then falls to eighty-four point three percent at depth eleven. 

Two things stand out in that table. First, depth two is no better than depth one, because its second question makes the groups purer without changing any group's answer. Only the third question changes an answer, and this is the greedy search at work. Second, the score on new data peaks at depth three and then falls, while the training score keeps rising, which is overfitting. The true rule itself only gets ninety-two percent of the new examples right, because eight percent of the labels are flipped, so the depth-three tree is almost as good as possible.

The usual limits are a largest depth, or a smallest number of examples per leaf, and the right setting is found by trying several of them on examples the tree did not train on. One tree is simple and easy to read, but it is also brittle, because a few different training examples can change its first question, and then everything below it changes too.

The third section explains random forests, where many trees vote. Because one tree is brittle, a random forest answers that by growing many deep trees, each on a slightly different version of the data, and letting them vote. Its steps are as follows. 

First, draw a new training set of the same size from the original, by picking examples at random with replacement, so that some examples are picked twice or more and some are left out. This is called a bootstrap sample. Second, grow a tree on that sample, but at each node let the tree look at only a random few of the features rather than all of them, because this makes the trees differ more from each other. Third, repeat both of those steps, for one hundred to five hundred trees in all. Finally, to answer a new case, ask every tree, and each tree gives one vote. The answer is the label with the most votes, and the share of votes serves as a rough chance.

Each tree is overfitted in its own way, because each one saw different examples. Their mistakes therefore point in different directions, so the vote cancels much of them out. But the parts they agree on are the parts that come from the true rule.

The script grew two hundred trees, where each tree looks at one of the two features at each node and grows until its leaves hold three examples or fewer. A diagram shows a forest's share of votes over the input plane, and its accuracy against the number of trees. It shows that the line where half the trees say slip follows the true rule more smoothly than any single deep tree does. For example, at a ratio of zero point five and shaking of zero point seven, eighty-four percent of trees say slip, while at a ratio of zero point five and shaking of zero point three only two percent do. At a ratio of zero point seven and shaking of zero point two, seventy-eight percent do, which is right but less sure, because a few flipped labels sit there.

The diagram also shows the score on new data against the number of trees. One tree from the forest gets eighty-seven percent right, and the two hundred single trees score eighty-one percent on average, with anything from sixty-five percent to eighty-nine percent. Their vote gets ninety-one point one percent right, which is about as good as the best single tree at ninety-one point three percent, and nobody had to choose its depth. Adding more trees never makes a forest overfit more, because it only makes the vote steadier, at the cost of more time.

The vote is an equal vote, because every tree counts the same. The next method instead gives different trees different weights.

The fourth section is about gradient-boosted trees, where each tree fixes the last one's mistakes. A forest grows its trees side by side, each one on its own, but boosting grows them one after another instead. Each new tree looks at what the trees so far still get wrong, and it tries to fix that. The trees in boosting are small, often with a depth of two to six.

The first way to boost uses sample weights, and is called AdaBoost, short for adaptive boosting. A sample weight is a number attached to each training example that says how much it counts. A tree that gets a heavy example wrong therefore pays more than one that gets a light example wrong. So the Gini search simply counts weights instead of examples. 

First, give every example the same weight, so that with two hundred examples each weight is one two-hundredth, or zero point zero zero five. Second, grow a very small tree, often with only one question, and a tree with one question is called a stump. Third, measure its weighted error, which is the total weight of the examples it gets wrong. Fourth, give the stump a say, which is a number that is large when its error is small. Fifth, raise the weight of every example it got wrong, and lower the weight of every example it got right. Then scale all weights so they add up to one. Finally, go back to the second step and grow the next stump.

At the end every stump votes, and each vote counts as much as that stump's say, which is called a weighted vote.

On the slip data, the first stump asked if the ratio was above zero point six one seven, and got forty-four of two hundred examples wrong. This is a weighted error of zero point two two, so its say was zero point six three. The weight of each example it got wrong then rose from zero point zero zero five to zero point zero one one four, while the weight of each example it got right fell to zero point zero zero three two. After this step the forty-four wrong examples hold half the total weight, which always happens in AdaBoost. So the second stump cannot ignore them, and it chose a different question, asking if the ratio was above zero point two nine eight.

Sample weights are useful outside boosting too, because every library on this page lets you pass a weight per example when you train. For example, a robot project uses this to make rare failures count more, or to make recent data count more than old data.

Gradient boosting is the method most used today, and it does the same job in a more general way. Instead of changing weights, each new tree learns the error that is left over. 

The example here is predicting grasp success. Each row is one logged grasp, with six columns: the object's weight in kilograms, its width as a share of the gripper's opening, the grip force in newtons, the friction of the surface, the approach angle away from straight down in degrees, and the room temperature. The label is "held" or "dropped". The made-up true rule depends on the holding force compared with the weight, on objects near the gripper's full opening, and on steep approach angles, while the room temperature does not matter at all. The script has six hundred grasps to learn from, of which seventy-four percent held, and four thousand more to test on.

For a yes-or-no label, the model keeps a running score for each example, and that score becomes a chance between zero and one by the same squashing step that logistic regression uses. The steps are as follows. First, start every score at the same value, which is the one that gives the overall success rate of seventy-four percent. Second, for each example, work out the gap between its label, which is one for held and zero for dropped, and its current chance. Third, grow a small tree that predicts those gaps from the six columns. Fourth, add a small share of that tree's answer to each score. Finally, go back to the second step and grow the next tree.

The name of the method comes from the second step, because the gap is the gradient of the error measure, which is the direction in which the score should move.

The share added in that fourth step is the learning rate, and it decides how much of the error one tree may fix. With a learning rate of one point zero, each tree tries to fix all of the remaining error at once, while with zero point one it fixes a tenth of it and leaves the rest to later trees.

To score the model, the script uses the log loss, which is an error measure for chances. A confident right answer costs almost nothing, while a confident wrong answer costs a lot, so a lower log loss is better. For example, a flat guess of seventy-four percent for every grasp scores zero point five six seven, and the true chances, which no model can beat, score zero point three zero two.

A diagram shows the log loss on new grasps against the number of trees for three learning rates, where each tree has a depth of three. A table gives the same results. For a learning rate of one point zero, the lowest log loss is zero point four zero seven, reached after just three trees, but after three hundred trees it rises to one point three five nine. For a learning rate of zero point three, the lowest is zero point three four eight, reached after thirteen trees, rising to zero point seven three nine after three hundred trees. For a learning rate of zero point one, the lowest log loss is zero point three four three, reached after fifty-five trees, and it is zero point four four four after three hundred trees.

A large learning rate learns fast and then overfits fast, so its best point is poor and it gets much worse with more trees. A small rate learns slowly, but it reaches a better best point and stays near it for longer. At its best, the rate zero point one model gets eighty-four point eight percent of new grasps right, against eighty-five point six percent for the true chances.

Unlike a forest, boosting does overfit if you add too many trees. So people keep some examples aside, watch the error on them as trees are added, and stop when it stops falling. This is called early stopping, and a learning rate of zero point zero five to zero point one with early stopping is a common start.

The fifth section covers feature importance, which tells you which columns mattered. The previous sections ended with hundreds of trees, which nobody can read, but a tree model can still tell you which columns it relied on. There are two common ways to measure this.

The first way adds up how much each column's questions lowered the error, over every question in every tree, and this is called the split gain. It is free, because the trees computed it while they were growing.

The second way is permutation importance, which means taking the test examples, shuffling one column so that its values land on the wrong rows, and measuring how much worse the model gets. A column the model needs makes it much worse, while a column it does not need changes nothing.

A diagram shows both measures for the rate zero point one model. It shows that the width as a share of the opening, the grip force, and the object's weight matter most, because shuffling each of them raises the log loss by about zero point twenty-seven to zero point thirty-one. The friction matters a little less, and the approach angle less again.

The room temperature is the lesson here, because it had no effect in the true rule. Yet it got four percent of the split gain, since a tree can always find some cut on a noisy column that helps a little on the training data. Shuffling it did nothing at all, because the log loss changed by only minus zero point zero zero four. So the split gain can give credit to a useless column, and permutation importance on test data is the more honest check. Neither one says that a column causes success, because they say only what this model used.

The sixth section explains how it is trained, meaning what data you need and how much. A tree model needs a table, where each row is one example and each column is one number that the robot can measure at the moment it must decide. The label is the answer you want, which can be slip or hold, success or failure, or a number.

Trees need little preparation of the data. Columns can have very different units, such as kilograms next to degrees, because each question looks at one column on its own, so you do not need to scale the columns. Some libraries also handle missing values and columns of categories, such as the kind of gripper.

How much data you need depends on how many columns and how complicated the true rule is. As a rough guide, a few hundred rows are enough for a useful model with five to ten columns, as in this page's examples. Thousands of rows let boosted trees find finer patterns. With under about one hundred rows, a single shallow tree or logistic regression is safer.

Training takes seconds on an ordinary computer for tables of this size. Keep separate test examples, and if the rows come from runs over time, test on a later run than you trained on. Otherwise you test on examples very like the ones the model has already seen, and the score looks better than it is.

The seventh section describes where trees are used on a robot arm. Because trees want a table of measured numbers, and a robot arm logs exactly that, trees turn up in five places on an arm. 

First, classifying contact and slip from force features. This is the first example, where a window of force readings becomes a few numbers, such as the sideways ratio, the shaking, and how fast the force is changing. A small tree or forest then says slip or hold in well under a millisecond. 

Second, predicting grasp success from simple features. A robot logs every grasp, including the object's size and weight, the grip force, the approach angle, and whether it held. Boosted trees then learn which grasps tend to fail, so the robot can raise the force or pick another grasp before it tries. 

Third, ranking candidate grasps. A grasp planner proposes several grasps, and the model gives each one a chance of success, so the robot tries the highest first. The script ranked six grasps on the same mug with the rate zero point one model. A table lists them in the model's order, which exactly matches the true order. The top ranked grasp is a narrow grip at thirty-five newtons and fifteen degrees, which the model gives a ninety-eight percent chance of success. The lowest ranked grasp is near full opening at twenty-five newtons and five degrees, which the model gives a three percent chance. The chances at the bottom are too low, because few training grasps look like these ones, but for ranking it is the order that matters and not the chance itself. 

Fourth, spotting faults in logs. Motor currents, temperatures, and tracking errors, labelled with past faults, train a model that flags a joint going wrong. 

Finally, choosing between a few actions. From a few numbers about the scene, a tree can pick which of several hand-written grasp or push routines to run. A small tree can also be printed and read, so people can check which routine it will choose.

The eighth section lists what goes wrong, and the usual fix for each problem. 

A single deep tree overfits, because it gets every training example right and new ones wrong. The fix is a depth limit or a smallest leaf size, chosen on held-out data, or using a forest instead of one tree.

Boosting overfits too, if you add too many trees, so the fix is a small learning rate with early stopping.

Trees cannot answer beyond their data, because each leaf gives an answer it saw in training. For a number to predict, a tree never goes above the largest label or below the smallest, so its prediction goes flat beyond the last example. The fix is to collect data over the whole range the robot will meet, or to use a method that follows a trend, such as linear regression.

Trees draw boundaries as staircases. Each question cuts along one column, so a diagonal boundary becomes many small steps. The fix is to give the tree the right feature, which here is the ratio, instead of the two raw forces. This means choosing good features matters more for trees than any setting does.

Rare labels get ignored, because if two percent of grasps fail, a model that always says "held" is already ninety-eight percent right. The fix is to give the rare examples larger sample weights, and to judge the model by how many failures it catches rather than by the share it gets right.

The chances are rough, because a forest's share of votes and a boosted model's chance are often too sure or not sure enough. So if the robot acts on the number itself, check it against real outcomes first.

Finally, importance is misread when a useless column gets credit. So use permutation importance on test data, and do not read it as cause and effect.

The ninth section covers libraries, because nobody writes the Gini search by hand in a real project. The page lists four real libraries for trees. Scikit-learn is the place to start, providing one interface for every method on this page, including decision trees, random forests, AdaBoost, gradient boosting, and permutation importance. XGBoost provides fast, widely used boosted trees and can train on a graphics card. LightGBM is very fast on large tables. CatBoost handles columns of categories with little preparation. 

All of them take a sample weight argument when fitting, which is how you pass the per-example weights. Scikit-learn has an export text function that prints a single tree as questions. XGBoost and LightGBM also have C interfaces, so a trained model can run inside a C plus plus robot program.

The tenth section asks why use trees, and what they cost. Trees are models that answer with a chain of one-column questions, and a forest or a boosted model adds up hundreds of those chains. They turn a table of logged numbers into a yes-or-no answer, a chance, or a predicted number, with little tuning and little preparation of the data.

The obvious alternative is a small neural network. But on a table of a few to a few dozen measured numbers, boosted trees usually match or beat a network. They need no scaling of the columns, they have fewer settings that matter, and they train in seconds without a graphics card. You can also read one small tree, or at least ask a forest which columns it used. A network wins when the input is raw, such as a picture, a point cloud, or a long force signal, because trees need someone to turn those into a short list of meaningful numbers first.

The second alternative is logistic regression, which weights and adds the columns. It is simpler, it follows trends beyond the data, and its weights are easy to read. Trees win when columns matter only in some cases, for example when the approach angle matters only above thirty degrees, because a weighted sum cannot draw that without help.

As for what trees cost, they need good features, because it was the ratio, and not the two raw forces, that made the slip tree work. They cannot answer beyond the range of their training data. A forest or boosted model of hundreds of trees is no longer easy to read. Their chances need checking before the robot relies on the numbers. Finally, boosting needs early stopping, and every tree model needs its settings checked on held-out data.

The eleventh section looks at the written alternative, because hand-written rules do the same jobs without learning at all. For slip, the rule comes from physics, because an object slides when the sideways force is more than the friction times the squeezing force. You can smooth the force readings, take how fast they change, and turn them into a flag with thresholds that do not flicker. For contact, guarded moves stop the arm when the measured force passes a set limit.

A hand-written rule is itself a tiny decision tree, so the difference between the two is only who writes the questions. The written rule wins when the physics is known and steady, for example with rigid objects of a known friction, because it needs no data and is easy to check. The learned tree wins when the thresholds depend on things you cannot measure well, such as wet or dusty surfaces, or when many columns interact. So a common middle way is to train a small tree, print it, and then check or adjust its questions by hand.

The next section suggests where to read next. Linear and logistic regression is the simpler method to try first. Gaussian processes and Bayesian optimisation gives an answer with an error bar, which trees do not. Nearest neighbours and locally weighted regression answers by looking up similar past examples. Support vector machines were the common classifier for small tables before trees took over. Other pages cover slip detection with networks on raw signals, and how to test a model fairly before the robot relies on it.

The final section shows what using it in Python looks like. It explains that a random forest, which is hundreds of trees voting, takes just one line of code. The code imports the models from scikit-learn. It defines the feature names, then creates and fits a decision tree classifier, a random forest classifier, and a gradient boosting classifier. It prints the tree as text, prints the forest's feature importances, and prints the predicted chances.

The export text function is worth running once, because it prints the tree as an indented list of questions with your own column names in it. That is the readability mentioned earlier, and it is real only for a shallow single tree, since three hundred trees cannot be read.

The library gives you all of the arithmetic on this page. The Gini search, the bootstrap sampling and the vote, and the residual fitting are all handled automatically when you fit the model. Setting early stopping to true holds some rows back and watches for the point where the score on them stops improving. Every one of these classes also takes a sample weight argument, which is the first way to boost.

What you have to collect is the input data and the labels, and what you have to build are the feature columns. A tree chooses among the columns you hand it and never combines two of them into a new one, so that combining is your job and no setting of the library replaces it.

What you have to decide is the maximum depth, which ties directly to overfitting, the number of estimators, which is how many trees to grow, and the learning rate for the boosted model. More trees in a forest do not make it overfit and only cost time, so the depth and the learning rate are the two settings actually worth searching over. You search them against rows the model has not trained on, and when the rows come from runs over time, those held-back rows should come from a later run.
