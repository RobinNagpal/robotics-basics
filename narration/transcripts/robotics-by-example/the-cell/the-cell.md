<!-- section: lead | The cell — the layout, the sensors, and the words -->

The cell: the layout, the sensors, and the words.

Every solution in this project works in the same room, with the same arm, the same camera, and the same table. Rather than restate those numbers in each document, they are provided here once.

Every dimension on this page is read directly from the project's own constants. A Python script imports the dimensions for the arm, the layout of the table and rack, and the shapes of the glasses, and then draws what it finds. If a number changes in the code, the pictures move with it the next time the script runs. Nothing here is typed in by hand.

<!-- section: the-layout-from-above | The layout, from above -->

The next part of the page describes the layout of the cell from above. A diagram shows this top-down view, with the robotic arm bolted to the table at the origin. Everything the arm does happens in two rectangular areas on that table. First is the glass zone, which is 320 by 360 millimeters, where glasses may stand. Second is the rack, which is 60 by 40 millimeters, where the glasses end up, placed upside down on pegs. 

Both of these rectangles sit inside a ring that the arm can reach comfortably. If it tries to work closer than 300 millimeters, it is folded over itself. If it reaches further than 780 millimeters, it is stretching straight out with no flexibility left for the wrist. This comfortable ring is a working preference, rather than a hard limit on the joints.

<!-- section: the-layout-from-the-side | The layout, from the side -->

The next part of the page looks at the layout from the side. The diagram shows the cell from this side view. 

The table top is 750 millimeters above the floor, and the arm stands on it, so every height in this project is measured from the table, not the ground. A glass's height, the camera's height, the rack's pegs: all of these are measured from the table top.

The camera is only ever put in two poses, and almost every misunderstanding in these documents comes from mixing them up. A table compares the two, which are the survey view and the level view. 

The survey view is positioned 450 millimeters above the table, looking straight down from directly overhead. Its purpose is finding everything roughly. It covers a wide area of the table, 519 by 390 millimeters, where one pixel covers 1.62 millimeters. 

The level view is much lower, at 120 millimeters above the table, and looks level at the glass from about 380 millimeters away. It is used for measuring one glass precisely, covering a smaller area of 439 by 329 millimeters, where one pixel covers 1.37 millimeters.

These two poses have three more beside them. There is a pose over the rack, one looking down the fingers, and the spot where the arm waits. All five are named and drawn in the later part of the page about where the camera stands. Older documents call our two main poses the survey pose and the side-on pose, but they are the exact same two places.

That distance of 380 millimeters for the level view is not a constant. A setting called measure standoff fixes only a minimum floor of 300 millimeters, because nearer than that, a glass fills the frame before it is all in it. The distance actually used is worked out per run from the lens and the tallest glass the cell handles, and comes to about 380 millimeters. However, the measure view height is deliberately fixed at 120 millimeters. The overhead view cannot tell how tall a glass is, which is exactly what the side view is for, so aiming at a fixed height is the only option available.

<!-- section: the-glasses | The glasses -->

The next section of the page describes the glasses. An image shows the four kinds used in the project, which are straight, tapered, stemmed, and short stemmed. Each glass is drawn at random inside its own range of proportions. No glass's size is written down anywhere in this project. It is not in a constant, not in a test fixture, and not in a mesh. The arm measures every glass during the run. What the code holds is the range the spawner draws from, which is a different thing and is what makes the tests meaningful.

Across all four kinds, the heights range from 65 to 230 millimeters, and the widths across the top range from 45 to 105 millimeters. 

The tapered kind is deliberately the widest of the four, reaching that maximum width of 105 millimeters, and it is worth knowing why. A camera looking straight down does not draw a glass's outline over the glass, because the rim is nearer the lens than the table is, so the outline leans outwards away from the point directly below the camera. The taller the glass, the further out it is thrown. When one kind holds both a short glass and a much taller one, the tall one's outline can therefore sweep over the short one and cover it completely, and the short glass then appears in no picture at all. That is the headline difficulty of the second problem, which covers handling many glasses of one kind. With a narrow range of sizes this overlap cannot happen, which is why this one range is wide on purpose rather than by accident.

The range is as wide as the rest of the cell allows, and two other parts of the cell are what set its short end. A glass shorter than this minimum height no longer clears a rack peg when it is stood mouth down, and the gripper can no longer close on it where the rule for this kind says to hold it. Neither of those has anything to do with perception, which is a good illustration of something this project runs into often. A limit on what the arm can be asked to see is frequently a limit on what it can be asked to do.

<!-- section: the-sensors | The sensors -->

The next part of the page describes the sensors. The diagram shows their locations on the robot arm. There are exactly four sensors in the cell, and that is the whole list. Everything else the cell believes is just arithmetic based on these four.

First is the RGB-D camera. It is mounted on the wrist, 85 millimeters off the flange. It runs at 15 hertz and returns colour and aligned depth images at a resolution of 320 by 240. It has a field of view of 1.047 radians across, and is usable from 0.05 to 3.0 meters away.

Second is the wrist force-torque sensor. This sits between the flange and the gripper. It runs at 100 hertz and returns three forces and three torques.

Finally, there are two pad contact sensors, one in each fingertip pad. These run at 60 hertz and simply return whether that specific pad is touching something.

There is a fourth thing in the cell that is not a sensor, but is easy to mistake for one. This is an ArUco marker, 70 millimeters square, printed on the rack. It is how the camera works out where the rack is, rather than trusting that it was placed exactly.

The fact that the camera is on the wrist, rather than mounted above the table, is the single fact that shapes most of these solutions. It means the arm chooses its own viewpoints. It also means that moving the camera costs seconds of arm time. However, it means the camera's pose is known exactly from the joint encoders. This exact knowledge of the camera's position is what makes the seventh solution, which covers self-supervised learning from the arm's own movement, possible at all.

<!-- section: where-the-camera-stands-and-what-each-place-is-called | Where the camera stands, and what each place is called -->

The next part of the page explains where the camera stands, and what each place is called. 

The robotic arm has one camera, and it is mounted on the wrist. Because of this, a camera position always means a place the arm carries that single camera to. A diagram and a table in this section outline five specific places that cover the whole run. These five names are used throughout the rest of the documents, and they are the survey view, the rack view, the level view, the finger view, and the parking spot.

First is the survey view. The camera is taken up to 450 millimetres and pointed straight down to see what is on the table and roughly where it is. One picture from this height covers 519 by 390 millimetres of the table. However, a station takes two pictures 120 millimetres apart, and only the part visible in both pictures is useful. This overlapping area leaves 424 by 175 millimetres. Because the glass zone is 320 by 360 millimetres, it takes three overlapping stations in a line to cover it.

There is one honest detail to note here. The 450 millimetre height is actually where the tool is sent. The camera sits 85 millimetres to one side of the tool and 15 millimetres along the way it points. So, the camera is actually about 435 millimetres up and a hand's breadth off to the side. The code does not guess this position. Instead, it reads where the camera really was from the joint angles, and that reading is what the pair of pictures is measured against.

Second is the rack view. This uses the same height and the same straight-down aim as the survey view, but it is positioned over the middle of the rack instead of over the glasses. This happens only once, at the start of a run, and all it does is read the ArUco marker. For this view, the code does take the 85 millimetre offset out of the tool's position first, so the camera itself ends up exactly over the middle of the rack.

Third is the level view. Here, the camera comes down to 120 millimetres above the table, points level at the glass, and stands 380 millimetres back from it. This is the view used for measuring a single glass, and it is the view that the solution for moving the camera sends the arm to. 

The 380 millimetre distance is worked out by the code, not stored. The camera frame has to reach from the table at the bottom to the rim of the tallest glass the cell handles at the top. Both of those bounds are angles, so how far back that puts the camera depends on the lens. The arm can stand anywhere on a circle round the glass, and it is offered nine places on that circle, spaced 40 degrees apart. The first place it tries is straight in from its own base, because that is the shortest reach. It moves on to the next place if something is standing behind the glass, because a glass behind the target would join it in the mask and the two would measure as one wide glass. It also moves on if the pose is too far out for the arm to reach.

Fourth is the finger view. This position is not chosen at all. It is simply wherever the camera ends up once the fingers are around the glass. That puts it 135 millimetres back from the glass's axis, 85 millimetres off to one side, at whatever height the grip was fixed at, looking along the fingers. Everything before this point aimed the fingers using pictures taken half a metre away. This is the one look taken from where the fingers actually are, and at this close range, a millimetre on the table is worth many pixels. It is used to check if the glass is between the pads or beside them, and its only purpose is for shifting sideways onto the glass before the fingers close.

Finally, there is the parking spot. This is 500 millimetres out from the base and 450 millimetres up, looking straight down. The arm goes here when it has finished its tasks, or when it has given up on something. This keeps it out of the way and ensures the next move starts from a known place where the arm waits with nothing to do.

Sometimes, other documents talk about cameras this cell does not actually have, like one bolted above the table or one standing at the edge looking across. If you need to name a place that is not one of the five standard views, you describe it with three things, in this exact order: the spot, the height, and the aim.

First, the spot is where on the table the camera stands over or beside. For example, over the middle of the glass zone, over the rack, at the near edge of the table, or beside the glass. 

Second, the height is given in millimetres above the table top, because every height in this project is. The standard landmarks are zero for table level, 120 for the level view, and 450 for the survey view. A fraction is fine when the exact number does not matter, so you could say half the survey height to mean 225 millimetres. 

Third, the aim describes the camera's angle, such as looking down, looking level, looking at a slant of 30 degrees, or looking along the fingers.

So, a camera at the near edge of the table, at table level, looking level, describes the fixed side camera that some of the solutions weigh up. And saying over the middle of the glass zone, 450 millimetres up, looking down, is just the survey view written out the long way.

<!-- section: the-words | The words -->

The next part of the page defines the words used throughout the text, several of which mean different things elsewhere.

First is the survey. This is the opening move of a run. The arm flies the camera over the glass zone, looking straight down from a height of four hundred and fifty millimetres, and takes pictures from several stations until every part of the zone has been seen. It answers what is on the table and roughly where it is, but it does not answer how big the glass is.

A station is one place where the camera is parked during the survey. At each station, the camera takes two pictures one hundred and twenty millimetres apart. This distance is called the baseline, and the apparent shift between the two pictures gives the depth. Stations overlap by thirty-five per cent of a frame, so if a glass is cut off at the edge of one picture, it is well inside another.

Next is standoff. This is how far the camera is from the thing it is looking at, and the word is used almost always for the side-on pose.

The nadir is the point on the table directly under the camera. This is only meaningful in the survey pose. Things directly under the camera are seen honestly, but things off to the side are seen at an angle, which matters more than it sounds.

The consequence of that angle is called splay. It is worth explaining this slowly, because almost every distance the survey reports is made wrong by it. 

Start with what the camera can see. When a glass is off to the side, the camera sees it from above and a little from the side. The base of the glass is hidden because the bowl sits over it. What the camera actually sees is the widest part of the glass, which is usually the rim. 

Now, a single picture taken from above cannot tell how tall anything is, so the survey assumes that everything it sees is lying flat on the table. It draws a straight line from the lens, through the widest part of the glass, and takes the point where that line meets the table as the place where the glass is standing. Because the widest part is well above the table, the line carries on past the glass and lands further out. The first diagram illustrates why splay happens, showing this line projecting from the camera, past the rim of the glass, and hitting the table at a false, more distant position.

You can calculate the size of the mistake using similar triangles. Call the camera's height capital H, and the height of the widest part of the glass lowercase h. That sloping line makes two right-angled triangles, one inside the other. The big one runs all the way down to the table, and the small one stops at the height of the widest part. Because both triangles have the same angle at the lens, their sides are in the same ratio. This means the reported distance equals the true distance multiplied by capital H, divided by the result of capital H minus lowercase h.

Put the cell's numbers into that formula. Capital H is four hundred and fifty millimetres. If you take a real glass from the spawner whose widest part is one hundred and sixty point seven millimetres up, the multiplication factor is four hundred and fifty divided by two hundred and eighty-nine point three, which equals one point five five five. Problem one measured exactly this. A glass standing one hundred and fifty-seven millimetres from the nadir was reported at two hundred and forty-four millimetres, which is eighty-seven millimetres out.

Three things follow from that formula, and all three matter later. 

First, the error is proportional, not fixed. It is zero directly under the camera and grows with distance, so you cannot correct it by simply subtracting a constant. 

Second, a taller glass is pushed further. The factor depends on the height of the glass, lowercase h, so two glasses standing side by side are moved by different amounts. One correction applied to the whole picture cannot fix both. 

Finally, the outline grows as well as moving. Every point of the glass is scaled by the same factor, so the reported outline is bigger than the real one. This is why a glass seen from above looks like a teardrop leaning away from the nadir, rather than a circle. The second diagram shows what splay costs, illustrating this stretched teardrop shape and the positional shift.

None of this is a fault in the camera or the code. It is simply what a single picture from one point can tell you, and no more. It is also the reason the survey's job is stated as finding roughly where things are, and the reason the arm carries the camera round to the side before it measures anything.

Moving on to image processing terms, a mask marks every pixel as either glass or not glass. A patch, or a blob, is one group of touching marked pixels, which is what a connected components function returns. One patch is not necessarily the same as one glass, which is the whole of the first difficulty in problem two.

A silhouette is the outline of one glass in one picture. It is not a circle in either pose. From above, it is the teardrop leaning away from the nadir, and from the side, it is the glass's profile.

A cluster is a group of three-dimensional points that belong together. They are formed by their physical distance in the room, rather than by being next to each other in the picture.

Finally, the word footprint. Read this one slowly, because two different quantities get called by the same name. 

The first is the contact patch. This is where the glass actually touches the table, which is twenty-five to ninety-five millimetres across over the four kinds of glass. 

The second is the flattened disc. This is what you get when every point of a glass is dropped straight down onto the table. It represents the glass's widest part and is forty-five to one hundred and five millimetres across. 

Most of the documents mean the second definition, the flattened disc. That is what the process for clustering on the table groups together, what a circle is fitted to, and what limits how close two glasses can stand. The exception is solution one, which explains how to split the blob in the picture; its contact runs read the first definition. Wherever a number matters, the documents will say which one they mean.

<!-- section: every-constant-and-where-it-lives | Every constant, and where it lives -->

The next part of the page lists every constant and where it lives. It notes that numbers live with their subject and nowhere else, so the provided table acts as a directory rather than a second copy of the data. 

The table outlines various physical dimensions, coordinates, and sensor specifications for the cell. For each item, it gives the value and names the specific layout or dimension file where it is defined in the code. For example, it shows that the table top is seven hundred and fifty millimetres above the floor, which is defined in the table layout file. The comfortable reach of the arm is between three hundred and seven hundred and eighty millimetres, found in the arm dimensions file. It also lists hardware details, such as the camera having a resolution of three hundred and twenty by two hundred and forty, a field of view of one point zero four seven radians, and a frame rate of fifteen hertz, which are located in the wrist camera configuration file. Other constants in the directory cover the rack area, survey heights, gripper openings, and the minimum separation between glasses.

Finally, the section points out two useful numbers that are derived rather than stored, meaning they are recomputed every run. 

First is the focal length in pixels, which turns every angle into pixels. This is calculated as three hundred and twenty divided by two, all divided by the tangent of one point zero four seven divided by two. This results in a value of approximately two hundred and seventy-seven point one. 

Second is the side-on standoff distance, which is about three hundred and eighty millimetres, measured from the lens to the tallest glass.

<!-- section: where-to-go-next | Where to go next -->

The final part of the page outlines where to go next. There are three main areas to explore. First is the map of the five problems. Second is problem one, which covers handling a single glass from start to finish. Finally, there is the page on problem two, which explains how to deal with many glasses of one kind.
