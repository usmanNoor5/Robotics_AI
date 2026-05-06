# Humanoid Robot Research Paper Reading Checklist

# 1. General Research Paper Checklist
(Things to check in almost every robotics/AI paper)

---

# Basic Understanding

## Problem Statement
- What exact problem are they solving?
- Why is it important?

## Main Contribution
- What is actually new?
- New model?
- Better control method?
- Better dataset?
- Better hardware?
- Faster inference?
- Safer locomotion?

## Paper Type
- Theory paper
- Benchmark paper
- Hardware paper
- AI/VLA paper
- Reinforcement learning paper
- Control systems paper
- Full humanoid system paper

---

# Implementation & Reproducibility

- GitHub/code available?
- Dataset available?
- Pretrained weights available?
- Simulation files available?
- ROS/Isaac/Gazebo/MuJoCo support?
- Hardware specs mentioned?
- Training configs provided?
- Is the paper reproducible?

---

# Model / Algorithm Details

## Architecture Used
- Transformer
- Diffusion
- CNN
- RL policy
- VLA
- Behavior cloning
- Hybrid controller

## Training Method
- Supervised learning
- Reinforcement learning
- Imitation learning
- RLHF
- Self-supervised learning

## Input Modalities
- RGB
- Depth
- LiDAR
- IMU
- Force sensors
- Audio
- Language commands

## Outputs
- Joint torques
- Trajectories
- End-effector pose
- Whole-body motion
- Action tokens

## Performance
- FPS
- Latency
- GPU requirements
- Real-time inference speed

---

# Equations & Mathematics

- What equations are central?
- Are they clearly explained?
- Is the math practical or only theoretical?
- Loss functions?
- Kinematics/dynamics equations?
- Optimization functions?
- Stability constraints?
- Control equations?

## Important Humanoid Equations
- Whole-body control equations
- Inverse kinematics
- ZMP/stability equations
- MPC equations
- RL reward functions

---

# Results & Evaluation

- Quantitative results?
- Real-world videos?
- Comparison with baselines?
- Failure cases shown?
- Ablation studies?
- Accuracy vs speed tradeoff?
- Robustness tests?

---

# Environment & Testing

- Simulation only?
- Real robot only?
- Sim-to-real transfer?

## Simulator Used
- MuJoCo
- Isaac Sim
- Gazebo
- PyBullet

## Environment Complexity
- Flat ground
- Stairs
- Uneven terrain
- Dynamic obstacles
- Human interaction

---

# 2. Humanoid Robot Specific Checklist

---

# Robot Details

- Robot name
- Degrees of Freedom (DOF)
- Actuators used
- Sensors used
- Battery life
- Payload capacity
- Size/weight
- Compute hardware
  - Jetson
  - RTX GPU
  - onboard PC

---

# Locomotion Analysis

- Walking speed
- Running capability
- Turning stability
- Stair climbing
- Recovery from pushes
- Balance control
- Dynamic vs static walking
- Terrain adaptability

## Important Metrics
- Falls frequency
- Energy efficiency
- Stability margin

---

# Motion Quality

- Slow scripted motions?
- Natural human-like movement?
- Dynamic athletic motion?
- Reactive movement?
- Dexterity?
- Whole-body coordination?

---

# Manipulation Capabilities

- Can it use hands?
- Finger DOFs?
- Grasp planning?
- Bimanual tasks?
- Fine manipulation?
- Tool use?

## Example Tasks
- Picking objects
- Opening doors
- Folding clothes
- Cooking
- Warehouse tasks

---

# AI / VLA Specific Things

# Language Understanding
- Natural language understanding?
- Long-horizon planning?
- Multi-step task execution?

# Vision-Language-Action Pipeline
- Vision encoder used?
- LLM used?
- Action representation?
- End-to-end or modular pipeline?

# Dataset
- Human teleoperation?
- Motion capture?
- Internet-scale data?
- Real robot demonstrations?

# Generalization
- Works in unseen environments?
- Handles unseen objects?
- Recovers from disturbances?
- Performs zero-shot tasks?

---

# Real-World Deployment

- Continuous testing?
- Factory/home testing?
- Safety systems?
- Human interaction?
- Long-term autonomy?

---

# Hardware Reliability

- Motor overheating?
- Battery drain?
- Joint failures?
- Hardware wear?
- Thermal limits?

---

# Safety

- Collision avoidance?
- Safe torque limits?
- Human-aware motion?
- Emergency stop system?
- Fall mitigation?

---

# Compute Requirements

- Training GPUs?
- Inference GPUs?
- Onboard compute?
- Cloud dependency?
- Can it run on embedded systems?

---

# What Makes a Strong Humanoid Paper?

Usually strong humanoid papers have:
- Real robot experiments
- Dynamic motion
- Generalization
- Robustness
- Fast inference
- Reproducibility
- Open-source implementation
- Real-world tasks
- Failure analysis
- Sim-to-real transfer

---

# Biggest Red Flags 🚩

- Only simulation results
- No real videos
- No comparison with baselines
- No latency/inference info
- Cherry-picked demos
- No failure cases
- No hardware details
- No training details
- Extremely controlled environments
- No reproducibility/code

---

# Practical Reading Strategy

1. Read abstract
2. Read conclusion
3. Look at figures/videos
4. Check GitHub
5. Check robot hardware
6. Check training pipeline
7. Check datasets
8. Check real-world experiments
9. Check limitations/failure cases
10. Deeply read equations and methodology