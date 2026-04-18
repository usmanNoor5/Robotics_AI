# Assignment 2 (Multi-Agent Search) - Fail-Proof Implementation Guide

This document explains a safe, step-by-step plan for solving each question in `multiAgents.py` and passing all autograder tests without breaking anything.

## 1) Fail-Proof Plan (Do This First)

1. Keep all edits inside `multiagent/multiAgents.py` only.
2. Do **not** rename classes, methods, arguments, or imports.
3. In Q2-Q4, always use:
   - `self.depth`
   - `self.evaluationFunction`
   - `gameState.getLegalActions(agentIndex)`
   - `gameState.generateSuccessor(agentIndex, action)`
4. Respect agent order exactly:
   - Pacman is `agentIndex = 0`
   - Ghosts are `1..N-1`
5. Count depth by **plies** (one Pacman move + all ghost moves = one depth unit).
6. End recursion immediately if:
   - `state.isWin()`
   - `state.isLose()`
   - search depth limit reached
   - no legal actions
7. Never generate successors unnecessarily (important for autograder expansion-count tests).
8. For alpha-beta (Q3), do **not** prune on equality (`>` and `<`, not `>=` and `<=`).
9. After each question, run its autograder before moving on.
10. Run full checks at the end:
    - `python autograder.py -q q1 --no-graphics`
    - `python autograder.py -q q2 --no-graphics`
    - `python autograder.py -q q3 --no-graphics`
    - `python autograder.py -q q4 --no-graphics`
    - `python autograder.py -q q5 --no-graphics`

## 2) Q1 - Reflex Agent (State-Action Evaluation)

### Goal
Pick the best immediate action by scoring successor states smartly.

### How to Think
- Reflex agent is not planning deeply.
- It evaluates each legal action from the current state.
- Good behavior needs a balance of:
  - getting closer to food,
  - avoiding dangerous ghosts,
  - chasing scared ghosts when safe,
  - avoiding pointless `STOP`.

### Stable Feature Set
- Start from `successorGameState.getScore()`.
- Add reward for closer food: `1 / (distance_to_closest_food + 1)`.
- Add penalty for remaining food count.
- Penalize being very close to active ghosts (strong penalty at distance <= 1).
- Slight reward for approaching scared ghosts.
- Penalize `Directions.STOP`.

### Common Mistakes
- Forgetting to use successor info (`newPos`, `newFood`, `newGhostStates`).
- Over-penalizing ghosts so much that Pacman never eats.
- Ignoring food count (agent loops).

## 3) Q2 - Minimax (Adversarial Search)

### Goal
Implement correct multi-ghost minimax for any number of agents.

### Core Logic
- Pacman node (`agentIndex == 0`): maximize value.
- Ghost node (`agentIndex >= 1`): minimize value.
- Recursively rotate agent index with:
  - `nextAgent = (agentIndex + 1) % numAgents`
- Increase depth only when control returns to Pacman.

### Correct Depth Rule
- One depth increment happens after the **last ghost** moves and next agent is Pacman.

### Common Mistakes
- Incrementing depth on every agent move (wrong).
- Hardcoding one ghost.
- Using action-evaluation logic from Q1 instead of state evaluation.
- Calling `generateSuccessor` too many/few times.

## 4) Q3 - Alpha-Beta Pruning (Optimized Minimax)

### Goal
Same minimax values as Q2, fewer explored states.

### Core Logic
- Keep minimax structure from Q2.
- Track bounds:
  - `alpha`: best value found so far for max.
  - `beta`: best value found so far for min.
- Prune when:
  - max node value `> beta`
  - min node value `< alpha`

### Autograder-Specific Rule
- Do **not** prune on equality.
- Preserve natural action order from `getLegalActions` (no reordering).

### Common Mistakes
- Using `>=` or `<=` for pruning.
- Reordering children.
- Returning wrong value when pruning.

## 5) Q4 - Expectimax (Stochastic Ghosts)

### Goal
Model ghosts as random agents (uniform policy), not adversarial minimizers.

### Core Logic
- Pacman node: maximize.
- Ghost node: expectation (average of child values).
- For ghost with `k` legal actions, each action has probability `1/k`.

### Common Mistakes
- Accidentally using min instead of expected value.
- Not handling empty legal actions.
- Incorrect depth/agent transitions.

## 6) Q5 - Better Evaluation Function (State Heuristic)

### Goal
Build a strong state evaluator for depth-2 expectimax.

### Good Heuristic Ingredients
- Base game score.
- Food pressure:
  - reward closeness to nearest food,
  - penalize many remaining foods.
- Capsule pressure:
  - reward closeness to capsules,
  - penalize remaining capsules.
- Ghost handling:
  - heavy penalty if active ghost is too close,
  - reward approaching scared ghosts.
- Terminal states:
  - `+inf` for win,
  - `-inf` for lose.

### Performance Principle
- Use simple distance features (Manhattan distance) and lightweight arithmetic.
- Avoid expensive pathfinding inside evaluation to keep games fast.

## 7) What Was Implemented

All required methods were completed in `multiagent/multiAgents.py`:
- `ReflexAgent.evaluationFunction` (Q1)
- `MinimaxAgent.getAction` (Q2)
- `AlphaBetaAgent.getAction` (Q3)
- `ExpectimaxAgent.getAction` (Q4)
- `betterEvaluationFunction` (Q5)

## 8) Verification Results (No-Graphics Autograder)

- Q1 passed: `4/4`
- Q2 passed: `5/5`
- Q3 passed: `5/5`
- Q4 passed: `5/5`
- Q5 passed: `6/6`

This confirms the implementation is working and each question passes its tests.

## 9) Safety Checklist Before Submission

- Only `multiAgents.py` changed for code logic.
- No function/class names were altered.
- No unrelated project files were modified.
- Autograder runs cleanly for all required questions.

If you keep following this document, you should remain safe from the most common breakages in this assignment.
