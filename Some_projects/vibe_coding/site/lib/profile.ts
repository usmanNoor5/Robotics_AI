export const profile = {
  name: "Muhammad Usman Noor",
  headline: "Computer Vision • Machine Learning • ROS2",
  location: "Lahore, Punjab, Pakistan",
  contact: {
    email: "musmannoor2004@gmail.com",
    phone: "+923296566668",
    linkedin: "https://www.linkedin.com/in/muhammad-usman-noor-b2a497236",
  },
  summary:
    "I’m passionate about designing intelligent robotic systems that bridge the physical and digital worlds. With hands-on experience across embedded systems, autonomous navigation, and AI-driven perception, I specialize in building full‑stack robotics solutions—from simulation to deployment.",
  focusAreas: [
    "ROS2, SLAM, A*, sensor fusion, Gazebo, RViz",
    "Jetson Nano/Orin, Pixhawk, LiDAR, depth cameras (D435i)",
    "YOLOv8, OpenCV, object tracking, stereo depth",
    "Supervised learning (scikit-learn, TensorFlow), optimization",
    "LLMs, transformers, prompt engineering for robotics workflows",
    "Python, C++, Flutter, Linux",
  ],
  topSkills: [
    "Convolutional Neural Networks (CNN)",
    "Large Language Models (LLM)",
  ],
  experience: [
    {
      company: "CCRIPT Agency",
      role: "Computer Vision Engineer",
      start: "Feb 2026",
      end: "Present",
      location: undefined,
      highlights: [],
    },
    {
      company: "Neuralogic",
      role: "Computer Vision Engineer",
      start: "Feb 2026",
      end: "Present",
      location: undefined,
      highlights: [],
    },
    {
      company: "Upwork",
      role: "Robotics Developer",
      start: "Sep 2025",
      end: "Present",
      location: undefined,
      highlights: [],
    },
    {
      company: "Pakistan Engineering Council",
      role: "Registered Engineer",
      start: "May 2025",
      end: "Present",
      location: undefined,
      highlights: [],
    },
    {
      company: "Wild Robotics",
      role: "Software Developer",
      start: "Sep 2025",
      end: "Mar 2026",
      location: "Islamabad",
      highlights: [
        "Worked on the UR20 robotic arm using ROS2 and Gazebo Harmonic.",
        "Developed a custom ROS-based library to simulate vacuum gripper physics in Gazebo Harmonic.",
        "Integrated and configured MoveIt 2 for motion planning, kinematics, and arm control.",
      ],
    },
    {
      company: "AA Robotics",
      role: "Developer and Team Lead",
      start: "Jun 2022",
      end: "Oct 2024",
      location: "Lahore, Punjab, Pakistan",
      highlights: [
        "Designed and developed drones, unmanned aircraft systems, and ground robots integrating hardware + software.",
        "Used ROS for navigation, sensor integration, and mission control for real-time decision-making and maneuvering.",
        "Built custom flight controllers, optimized embedded systems, and implemented AI-based perception for aerial/ground operations.",
      ],
    },
  ],
  education: [
    {
      school: "National University of Sciences and Technology (NUST)",
      degree: "Master in Robotics & AI",
      field: "Robotics and AI",
      start: "Sep 2025",
      end: "May 2027",
    },
    {
      school: "University of Engineering and Technology, Lahore",
      degree: "B.S.c Mechatronics and Control Engineering",
      field: "Robotics and AI",
      start: "Oct 2021",
      end: "May 2025",
    },
  ],
} as const;

export type Profile = typeof profile;

