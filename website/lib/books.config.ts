// Display text for the mini books. The structure itself comes from the
// folders in docs/: each top-level folder is a book, each folder or .md file
// inside a book is a chapter, and each .md file in a chapter is a section, all
// in the order their number prefixes give (docs/01_robotics-intro/03_arm).
//
// Books and chapters are keyed by folder name without the number prefix. A
// book not listed in BOOK_INFO still appears, titled from its folder name, and
// a chapter not listed in CHAPTER_TITLES uses the title of its first document.

export type Accent =
  | 'teal' | 'violet' | 'amber' | 'blue' | 'green' | 'rose' | 'gold' | 'indigo'
  | 'cyan' | 'slate';

export type BookInfo = {
  title: string;
  // A one- or two-word name for the header, where six full titles do not fit.
  shortTitle: string;
  subtitle: string;
  description: string;
  accent: Accent;
};

export const ACCENTS: Accent[] = [
  'teal', 'violet', 'amber', 'blue', 'green', 'rose', 'gold', 'indigo', 'cyan', 'slate',
];

// The books are grouped into parts. A part is a shelf: several books that
// belong together. The word "section" is already taken here, because a section
// is one document inside a chapter, so these groups are called parts instead.
//
// Each part lists its books by folder name without the number prefix, and the
// order below is the order they are shown in. A book that no part lists still
// appears, in a part of its own at the end, so adding a book never makes it
// disappear from the site.

export type Part = {
  slug: string;
  title: string;
  /** Two or three words for the header, where the full title does not fit. */
  shortTitle: string;
  /** One sentence saying who the part is for and what it covers. */
  blurb: string;
  books: string[];
};

export const PARTS: Part[] = [
  {
    slug: 'foundation',
    title: 'Robotics Foundation',
    shortTitle: 'Foundation',
    blurb:
      'Start here. These four books build the ground every robot arm stands on: the Python and the maths, how a camera turns the world into numbers, the simulators and frameworks the field is built on, and ROS, the software the parts talk through.',
    books: ['robotics-intro', 'perception', 'frameworks', 'ros-and-rviz'],
  },
  {
    slug: 'how-models-work',
    title: 'How Models Work',
    shortTitle: 'How Models Work',
    blurb:
      'One book, which explains the machinery. It starts with a single neuron worked out by hand and ends with the models that drive a robot arm today, so a reader who knows no machine learning at all can follow how a model is built, how it is trained, and what each family of model does inside.',
    books: ['neural-networks'],
  },
  {
    slug: 'techniques-and-models',
    title: 'Techniques and Models',
    shortTitle: 'Techniques & Models',
    blurb:
      'The methods themselves, each one explained on its own. The first book holds the techniques somebody wrote down, and the second holds the models that were fitted to examples instead. Both say where a method is the right tool and where it is not.',
    books: ['programming-techniques', 'learned-models'],
  },
  {
    slug: 'by-example',
    title: 'Robotics by Example',
    shortTitle: 'By Example',
    blurb:
      'Two problems from one work cell, each followed the whole way down. Instead of explaining a method and then showing a use for it, these books start with a table, a camera and a job to do, build six quite different answers to the same job, and measure all six against one another on the same test bench. The first book is about seeing, and the second is about moving.',
    books: ['seeing-the-glasses', 'pushing-the-glasses-apart'],
  },
];

export const BOOK_INFO: Record<string, BookInfo> = {
  'robotics-intro': {
    title: 'Robot Arm Basics',
    shortTitle: 'Basics',
    subtitle: 'Python, maths, frames, kinematics and arm types',
    description:
      'Start here if you know nothing about robots. The Python and NumPy that robot code is written in, the angles, vectors and matrices an arm needs, frames and transforms, forward and inverse kinematics, and the common kinds of robot arm, with the six-joint arm in detail.',
    accent: 'teal',
  },
  perception: {
    title: 'Perception',
    shortTitle: 'Perception',
    subtitle: 'Cameras, depth and finding objects',
    description:
      'How a camera turns the world into pixels, how to turn pixels back into points, and how a robot finds an object and measures its size and pose, with the techniques, models and licences compared.',
    accent: 'violet',
  },
  frameworks: {
    title: 'Frameworks & Manipulation',
    shortTitle: 'Frameworks',
    subtitle: 'MuJoCo, Gazebo, MoveIt and training arms',
    description:
      'The tools and simulators the field is built on, MuJoCo and Gazebo among them, and what you do with them: gripping, moving an arm, programming and training one or two arms, worked case studies, and what changed at the frontier in 2026.',
    accent: 'amber',
  },
  'ros-and-rviz': {
    title: 'ROS and RViz',
    shortTitle: 'ROS',
    subtitle: 'The robot software stack and its 3D viewer',
    description:
      'What ROS is and how its programs talk to each other, one small program per idea, then a camera, an arm and the two together. It ends with RViz, the 3D viewer that shows you what the robot thinks is happening.',
    accent: 'blue',
  },
  'programming-techniques': {
    title: 'Programming Techniques',
    shortTitle: 'Techniques',
    subtitle: 'The algorithms robot arm software is built from',
    description:
      'The written, language-independent techniques behind seeing, planning and moving: camera geometry, pose from points and calibration, matching and registration, least squares, RANSAC and filters, masks, clustering and 3D maps, sampling-based planning, inverse kinematics and MPC, PID, dynamics and safety monitoring, and state machines and behaviour trees. Each chapter puts the most used techniques first. Each page says where a technique is used on an arm, where it fails, and which library already does it.',
    accent: 'green',
  },
  'seeing-the-glasses': {
    title: 'Seeing the Glasses',
    shortTitle: 'Seeing',
    subtitle: 'One perception problem, answered six ways and measured',
    description:
      'Several glasses of one kind stand on a table, and the arm has to work out which pixels belong to which glass. This book follows that single question the whole way down: what the camera can and cannot see, why a glass standing behind another is in no picture at all, and six quite different ways to answer it. One is a written rule with nothing fitted to anything, one is a small network trained in this cell from nothing, and four start from weights somebody else fitted to photographs of the everyday world. All six are built, and all six are scored on the same test bench, so the differences between them are measured rather than argued. The programs are in the repository, and each solution names the folder it was built in.',
    accent: 'cyan',
  },
  'pushing-the-glasses-apart': {
    title: 'Pushing the Glasses Apart',
    shortTitle: 'Pushing',
    subtitle: 'One manipulation problem, answered six ways and measured',
    description:
      'The glasses stand too close together for the gripper to reach between them, so the arm has to drag them apart without knocking any of them over. This book answers that six ways, from a single fixed nudge with nothing learned at all, through a model that ranks pushes the geometry proposed, to a borrowed robot foundation model fine-tuned on this cell. All six are built and scored on one bench, and the result is worth the reading: nothing learned beats the written rule here, the one learned method that wins is the one that learned the quantity the geometry gets wrong, and every method that learns something topples at least one glass where the geometry topples none.',
    accent: 'slate',
  },
  'neural-networks': {
    title: 'Neural Networks and AI Models',
    shortTitle: 'Networks',
    subtitle: 'How a model works and how it is trained, from nothing',
    description:
      'For a reader who knows some maths, some science and some programming, and nothing at all about machine learning. It starts with why some jobs cannot be written as rules, works one neuron out by hand, and builds up through layers, loss, gradient descent and backpropagation to the transformer, which nearly every model in use now is made of. It then explains each family in turn: pretraining and fine-tuning, diffusion and flow matching, models that see, language and vision-language models, learning from outcomes, the policies that move an arm, and world models. It ends with what it takes to run a model on a real robot and judge honestly whether it works.',
    accent: 'indigo',
  },
  'learned-models': {
    title: 'Learned Models',
    shortTitle: 'Models',
    subtitle: 'Every kind of learned model a robot arm uses, in plain words',
    description:
      'What a model is, how it learns and where its data comes from, for a reader who has never met one. Then classical machine learning, from regression and decision trees to Gaussian processes and movement primitives, and seven families of neural network models: models that see, that work in 3D, that choose a grasp, that move the arm, that understand words, that predict what happens next, and that make sense of touch and force. It ends with fine-tuning, running, testing and trusting a model on a real arm.',
    accent: 'rose',
  },
};

// Display names for chapters. A chapter not listed here uses the title of its
// first document.
export const CHAPTER_TITLES: Record<string, string> = {
  'python-and-numpy': 'Python and NumPy',
  maths: 'Angles, Vectors and Matrices',
  arm: 'Frames, Position and Transforms',
  kinematics: 'Forward and Inverse Kinematics',
  'arm-types': 'Joints and Types of Arm',
  ros: 'ROS Basics',
  rviz: 'RViz and the 3D View',
  camera: 'Cameras',
  'object-perception': 'Object Perception',
  gripping: 'Gripping',
  'arm-movement': 'Arm Movement',
  'tools-and-libraries': 'Tools and Libraries',
  'one-arm-training': 'Programming and Training One Arm',
  'two-arm-training': 'Two-Arm Training',
  'two-arm-manipulation': 'Two-Arm Manipulation',
  'stone-stacking': 'Case Study: Stone Stacking',
  frontier: 'The Frontier',
  'what-learning-means': 'What Learning From Data Means',
  'inside-a-network': 'Inside a Neural Network',
  'how-training-works': 'How Training Works',
  'making-training-work': 'Making Training Work',
  'turning-the-world-into-numbers': 'Turning the World Into Numbers',
  'the-transformer': 'The Transformer',
  'pretraining-and-adapting': 'Pretraining and Adapting',
  'models-that-generate': 'Models That Generate',
  'models-that-see': 'Models That See',
  'language-and-multimodal-models': 'Language and Multimodal Models',
  'learning-from-outcomes': 'Learning From Outcomes',
  'models-that-act': 'Models That Act',
  'starting-your-own-model': 'Starting a Model of Your Own',
  'using-a-model-for-real': 'Using a Model For Real',
  'what-models-are': 'What Models Are',
  'seeing-models': 'Seeing Models',
  '3d-models': '3D Models',
  'grasp-models': 'Grasp Models',
  'movement-models': 'Movement Models',
  'language-models': 'Language Models',
  'world-models': 'World Models',
  'touch-and-body-models': 'Touch and Body Models',
  'classical-machine-learning': 'Classical Machine Learning',
  'making-models-work-on-an-arm': 'Making Models Work on an Arm',
  'what-techniques-are': 'What Techniques Are',
  'geometry-and-cameras': 'Geometry and Cameras',
  'searching-and-matching': 'Searching and Matching',
  'fitting-and-estimation': 'Fitting and Estimation',
  'image-and-point-cloud-processing': 'Image and Point Cloud Processing',
  'planning-and-search': 'Planning and Search',
  'control-and-motion': 'Control and Motion',
  'decisions-and-task-logic': 'Decisions and Task Logic',
  'the-cell': 'The Cell Everything Happens In',
  'the-problem': 'The Problem',
  'the-test-bench': 'The Test Bench',
  'the-six-solutions': 'The Six Solutions',
  'the-results': 'The Results',
};
