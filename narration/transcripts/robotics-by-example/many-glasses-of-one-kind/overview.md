<!-- section: lead | Many glasses of one kind: an overview -->

Many glasses of one kind: an overview.

Several glasses of the same kind stand on the table. The arm has to work out which pixels belong to which glass, where each one stands, and roughly how wide each one is.

It stops there. It does not measure a shape, and it does not pick anything up.

This part of the material holds the problem, while the following parts hold the answers. The robotic cell they all share—the layout, the two places the camera works from, the sensors, and the vocabulary—is described once on its own page. 

The text is divided into several main areas. First, there is the problem itself. This covers what is on the table, what is asked for, the three difficulties, and what "done" means.

Second, there is a solution overview. This is the way into the ten solutions. It covers what they share, such as what each does about a glass nobody saw, the vocabulary, and where a learned part can sit in a pipeline. It also covers what it means for a machine to choose its own next measurement instead of taking a fixed number of pictures. 

Third, the page presents the ten solutions in full. These are split by whether they contain a trained model. Three of them are programmed, meaning they are rules somebody wrote down. The other seven are learned, meaning they all have numbers fitted to examples somewhere inside them, whether the fitted part decides the answer or only puts candidates in order.

Those seven learned solutions divide again by where their numbers come from. Some are fitted from scratch on this cell's own pictures, so everything they know comes from the table in front of them. The others begin from a large model already fitted elsewhere on ordinary photographs. What that trades is knowledge of a world this cell is not. The cell can only render a grey picture shaded from depth, and such a model has to accept that in place of a photograph.

Each solution is written from the beginning, and each ends with the general methods behind it. These are the named, published techniques it is built from, with an honest note on where each one is normally the right tool and where it is not.

The ten solutions are summarized in a table, grouped by their family. The first three are programmed solutions, such as splitting the blob in the picture, clustering on the table, and moving the camera. The next two are hybrid solutions, which involve choosing the next look and checking if anything is hiding. The final five are fully learned solutions. These range from a network trained from scratch, to self-supervised learning from the arm's own movement, to using large pre-trained models like a fine-tuned instance segmenter. The table also notes which parts of these solutions were actually built into the accompanying code, such as the finding steps, veto tests, and the ranker.

Two of these solutions were originally written as two separate documents and then joined, because the second was not a different method but the same method with one part changed. Solution four was two ways of ordering the same candidates, and solution six was two output heads on one network.

Finally, the page covers one more approach that sits outside the ten. It is a good answer, but it comes with a condition where it fails. This is an active-vision policy, which learns for itself where to point the camera next, rather than being told how to rank the choices. Nothing about it needs a different algorithm, and nothing it needs is missing from the cell. What it needs is throughput. Learning a policy means resetting the table and starting again over and over, and the usual way out of that is a simulator running many worlds at once on a graphics card. Solution four is the same idea, but with the learning done by supervision instead. It only asks whether a viewpoint will be worth taking, and that approach fits the machine as it is.

<!-- section: the-short-version | The short version -->

The short version of this overview outlines three things that are hard here. They are not the same thing, and they are listed in order of how dangerous they are, rather than how obvious they are.

First, a glass can be missing from a picture altogether. The glasses are all tapered, and the range of sizes inside that kind is wide, so a tall glass and a short one can differ several times over in height. When seen from the top, a glass's outline is thrown outwards, away from the point directly below the camera, and the taller the glass, the further out it goes. Because of this, a tall glass's outline can sweep over a short one and cover it completely. Nothing in the picture says that this happened. Every check in this project is a check on something that was found, and a glass that produced no pixels produces nothing to check.

Second, glasses can merge in the picture even when they are apart on the table. Two glasses a hand's width apart will land on top of each other in a photograph when the camera happens to be in line with both. When this happens, the flood fill that works perfectly for one glass returns a single patch for two. The answer is to stop grouping in the picture and to group on the table instead, where the two are plainly apart. Fortunately, this failure is at least loud, because the resulting patch is wider than any glass of that kind can be.

Third, the camera can no longer stand wherever it likes. The first problem measured a glass by standing back from it and looking level from whichever direction the arm could reach. With a bare table, several directions always work. But with five glasses, each direction has to clear the line of sight, the arm's path, and the edge of its reach all at once. A glass can end up with no usable viewpoint at all. That is not a failure, but rather the handover to the third problem, which moves the glass.

There are also two findings from writing these up that are worth noting. The first is that most of the reports of having no usable viewpoint come from the grid of directions running out, not from the physical geometry. The clear arcs around a typical glass are mostly narrower than the step between two directions the arm currently tries. Refining that step turns a large share of those reports back into ordinary viewpoints, and it costs arithmetic and nothing else. The working for this is explained in the solution for moving the camera.

The second finding comes from the other end of the problem. Because the outline of a found glass is thrown outwards by an amount that can be computed exactly, the region of the table it could have been hiding can be computed too. So the question that looks unanswerable, which is whether a glass is missing, becomes one that is answerable. We can instead ask where a glass could have been hiding, and whether that region is big enough to hold the smallest glass of the kind. That turns silence into a finite list of places to go and look at, which forms the second half of the solution for clustering on the table.

<!-- section: where-it-sits | Where it sits -->

The next part of the page explains where this topic sits within the broader sequence. Handling many glasses of one kind is the second problem in the series. It follows the first problem, which covers moving a single glass from start to finish, and it comes just before the third problem, which deals with glasses that are standing too close to each other. For a complete overview of how everything connects, the page covering the five problems provides the full map.
