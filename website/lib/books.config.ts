// Display text for the mini books. The structure itself comes from the
// folders in docs/: each top-level folder is a book, each folder or .md file
// inside a book is a chapter, and each .md file in a chapter is a section, all
// in the order their number prefixes give (docs/01_robotics-intro/03_arm).
//
// Books and chapters are keyed by folder name without the number prefix. A
// book not listed in BOOK_INFO still appears, titled from its folder name, and
// a chapter not listed in CHAPTER_TITLES uses the title of its first document.

export type Accent = 'teal' | 'violet' | 'amber';

export type BookInfo = {
  title: string;
  subtitle: string;
  description: string;
  accent: Accent;
};

export const ACCENTS: Accent[] = ['teal', 'violet', 'amber'];

export const BOOK_INFO: Record<string, BookInfo> = {
  'robotics-intro': {
    title: 'Robot Arm Basics',
    subtitle: 'Python, maths, frames, kinematics and arm types',
    description:
      'Start here if you know nothing about robots. The Python and NumPy that robot code is written in, the angles, vectors and matrices an arm needs, frames and transforms, forward and inverse kinematics, moving between poses, and the common kinds of robot arm, with the six-joint arm in detail.',
    accent: 'teal',
  },
  perception: {
    title: 'Perception',
    subtitle: 'Cameras, depth and finding objects',
    description:
      'How a camera turns the world into pixels, how to turn pixels back into points, and how a robot finds an object and measures its size and pose, with the techniques, models and licences compared.',
    accent: 'violet',
  },
  frameworks: {
    title: 'Frameworks & Manipulation',
    subtitle: 'MuJoCo, Gazebo, MoveIt and training arms',
    description:
      'The tools and simulators the field is built on, MuJoCo and Gazebo among them, and what you do with them: gripping, moving an arm, programming and training one or two arms, worked case studies, and what changed at the frontier in 2026.',
    accent: 'amber',
  },
  'ros-and-rviz': {
    title: 'ROS and RViz',
    subtitle: 'The robot software stack and its 3D viewer',
    description:
      'What ROS is and how its programs talk to each other, one small program per idea, then a camera, an arm and the two together. It ends with RViz, the 3D viewer that shows you what the robot thinks is happening.',
    accent: 'teal',
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
};
