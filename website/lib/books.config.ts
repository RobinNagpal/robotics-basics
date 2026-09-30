// Display text for the mini books. The structure itself comes from the
// folders in docs/: each top-level folder is a book, each folder or .md file
// inside a book is a chapter, and each .md file in a chapter is a section, all
// in the order their number prefixes give (docs/01_robotics-intro/03_arm).
//
// Books and chapters are keyed by folder name without the number prefix. A
// book not listed in BOOK_INFO still appears, titled from its folder name, and
// a chapter not listed in CHAPTER_TITLES uses the title of its first document.

export type Accent = 'teal' | 'violet' | 'amber' | 'blue' | 'green' | 'rose';

export type BookInfo = {
  title: string;
  // A one- or two-word name for the header, where six full titles do not fit.
  shortTitle: string;
  subtitle: string;
  description: string;
  accent: Accent;
};

export const ACCENTS: Accent[] = ['teal', 'violet', 'amber', 'blue', 'green', 'rose'];

export const BOOK_INFO: Record<string, BookInfo> = {
  'robotics-intro': {
    title: 'Robot Arm Basics',
    shortTitle: 'Basics',
    subtitle: 'Python, maths, frames, kinematics and arm types',
    description:
      'Start here if you know nothing about robots. The Python and NumPy that robot code is written in, the angles, vectors and matrices an arm needs, frames and transforms, forward and inverse kinematics, moving between poses, and the common kinds of robot arm, with the six-joint arm in detail.',
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
  'neural-network-models': {
    title: 'Neural Network Models',
    shortTitle: 'Models',
    subtitle: 'Every kind of model a robot arm uses, in plain words',
    description:
      'What a model is, how it learns and how it runs on a robot, for a reader who has never met one. Then seven families of models, each with a page per kind: models that see, that work in 3D, that choose a grasp, that move the arm, that understand words, that predict what happens next, and that make sense of touch and force.',
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
  'what-models-are': 'What Models Are',
  'seeing-models': 'Seeing Models',
  '3d-models': '3D Models',
  'grasp-models': 'Grasp Models',
  'movement-models': 'Movement Models',
  'language-models': 'Language Models',
  'world-models': 'World Models',
  'touch-and-body-models': 'Touch and Body Models',
  'what-techniques-are': 'What Techniques Are',
  'geometry-and-cameras': 'Geometry and Cameras',
  'searching-and-matching': 'Searching and Matching',
  'fitting-and-estimation': 'Fitting and Estimation',
  'image-and-point-cloud-processing': 'Image and Point Cloud Processing',
  'planning-and-search': 'Planning and Search',
  'control-and-motion': 'Control and Motion',
  'decisions-and-task-logic': 'Decisions and Task Logic',
};
