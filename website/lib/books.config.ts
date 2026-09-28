// How the docs in robotics-basics/docs are grouped into mini books.
//
// Each entry in `chapters` is a top-level folder or file in docs/, named
// without its number prefix (docs/03_arm -> "arm"). A folder becomes a
// chapter and each .md file inside it becomes a section. A single top-level
// .md file becomes a chapter with one section.
//
// Anything in docs/ that is not listed here is added to the last book, so a
// new doc never silently disappears from the site.

export type Accent = 'teal' | 'violet' | 'amber';

export type BookConfig = {
  slug: string;
  number: number;
  title: string;
  subtitle: string;
  description: string;
  accent: Accent;
  chapters: string[];
};

export const BOOKS: BookConfig[] = [
  {
    slug: 'robotics-intro',
    number: 1,
    title: 'Robotics Intro',
    subtitle: 'Frames, positioning and reference',
    description:
      'Start here. What ROS is and how its pieces talk to each other, how to see a robot in RViz, and the maths of position: frames, reference points and transforms. It ends with the NumPy that robotics code is written in.',
    accent: 'teal',
    chapters: ['ros', 'rviz', 'arm', 'numpy'],
  },
  {
    slug: 'perception',
    number: 2,
    title: 'Perception',
    subtitle: 'Cameras, depth and finding objects',
    description:
      'How a camera turns the world into pixels, how to turn pixels back into points, and how a robot finds an object and measures its size and pose, with the techniques, models and licences compared.',
    accent: 'violet',
    chapters: ['camera', 'object-perception'],
  },
  {
    slug: 'frameworks',
    number: 3,
    title: 'Frameworks & Manipulation',
    subtitle: 'MuJoCo, Gazebo, MoveIt and training arms',
    description:
      'The tools and simulators the field is built on, MuJoCo and Gazebo among them, and what you do with them: gripping, moving an arm, programming and training one or two arms, worked case studies, and what changed at the frontier in 2026.',
    accent: 'amber',
    chapters: [
      'tools-and-libraries',
      'gripping',
      'arm-movement',
      'one-arm-training',
      'two-arm-training',
      'two-arm-manipulation',
      'stone-stacking',
      'frontier',
    ],
  },
];

// Display names for chapters. A chapter not listed here uses the title of its
// first document.
export const CHAPTER_TITLES: Record<string, string> = {
  ros: 'ROS Basics',
  rviz: 'RViz and the 3D View',
  arm: 'Frames, Position and Transforms',
  numpy: 'NumPy for Robotics',
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
