# Detailed Code Explanation for `multiagent/multiAgents.py`

This file explains the implemented parts in detail: what each variable contains, where lists come from, how recursion flows, and how all questions (Q1-Q5) work together.

I focus on the exact implemented logic in:
- `ReflexAgent.evaluationFunction`
- `MinimaxAgent.getAction`
- `AlphaBetaAgent.getAction`
- `ExpectimaxAgent.getAction`
- `betterEvaluationFunction`

---

## 1) Big Picture: How the Program Starts Working Together

When you run a command like:

```bash
python pacman.py -p MinimaxAgent -a depth=2
```

the following flow happens:

1. `pacman.py` loads the agent class (`MinimaxAgent`).
2. `MultiAgentSearchAgent.__init__` sets:
   - `self.depth` from `-a depth=...`
   - `self.evaluationFunction` from `evalFn` (default is `scoreEvaluationFunction`)
3. At each Pacman turn, game engine calls `agent.getAction(gameState)`.
4. Your `getAction` runs search (minimax / alpha-beta / expectimax).
5. It returns one action from: `North`, `South`, `East`, `West`, `Stop`.
6. Game applies action, moves ghosts, updates score/state, and repeats.

For Q1 (`ReflexAgent`), there is no deep search: it evaluates each immediate action and picks the best score.

---

## 2) Important Inputs and Data Types

These are the objects and values used in your code:

- `gameState` (`GameState` object)
  - full snapshot of current game: walls, food, ghosts, score, win/lose flags.

- `gameState.getLegalActions(agentIndex)`
  - returns a **list** of actions for that agent.
  - Example: `['North', 'South', 'Stop']`

- `gameState.generateSuccessor(agentIndex, action)`
  - returns a **new GameState** after that agent takes that action.

- `gameState.getNumAgents()`
  - integer: total agents (`1 pacman + number_of_ghosts`).

- `gameState.getPacmanPosition()`
  - tuple `(x, y)`.

- `gameState.getFood()`
  - `Grid` object; calling `.asList()` returns a **list of `(x, y)` food positions**.

- `gameState.getGhostStates()`
  - **list of GhostState objects**.
  - each ghost has:
    - `ghostState.getPosition()` -> `(x, y)`
    - `ghostState.scaredTimer` -> integer turns remaining scared.

- `gameState.getCapsules()`
  - **list of `(x, y)` capsule positions**.

- `manhattanDistance(pos1, pos2)`
  - returns grid distance: `abs(x1-x2) + abs(y1-y2)`.

---

## 3) Q1: `ReflexAgent.evaluationFunction` Line-by-Line Logic

### Purpose
Score one state-action pair: "If I do this action now, how good is the immediate successor state?"

### Step-by-step

1. `successorGameState = currentGameState.generatePacmanSuccessor(action)`
   - Builds the next state after Pacman does `action`.

2. `newPos = successorGameState.getPacmanPosition()`
   - Pacman's position in successor.

3. `newFood = successorGameState.getFood()`
   - Food grid in successor.

4. `newGhostStates = successorGameState.getGhostStates()`
   - List of ghost states in successor.

5. `newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]`
   - List of scared timers. (Collected for compatibility; direct per-ghost use also done below.)

6. Terminal guard:
   - If successor is win -> `+inf`
   - If successor is lose -> `-inf`

7. `score = successorGameState.getScore()`
   - Start from official game score.

8. `foodList = newFood.asList()`
   - Converts food grid to list of coordinates.

9. Food shaping:
   - `closestFoodDist = min(manhattanDistance(newPos, foodPos) for foodPos in foodList)`
   - Reward being close: `score += 2.5 / (closestFoodDist + 1)`
   - Penalize remaining food amount: `score -= 1.5 * len(foodList)`

10. Ghost split into 2 lists:
   - `activeGhostDistances` (not scared)
   - `scaredGhostDistances` (scared)

11. For each ghost:
   - get ghost position
   - compute distance to Pacman
   - append distance to active/scared list based on `scaredTimer`

12. Active ghost penalty:
   - nearest active ghost distance via `min(activeGhostDistances)`
   - if distance <= 1 -> strong penalty (`-200`) to avoid immediate danger
   - else tiny inverse-distance penalty (`-1.0/d`)

13. Scared ghost bonus:
   - nearest scared ghost distance
   - small reward `+1.0/(d+1)` to encourage chasing edible ghosts

14. Stop penalty:
   - if action is `Directions.STOP`, subtract 3

15. Return final `score`

### Why this works
- It balances survival + food progress.
- It avoids deadlocks where Pacman waits too much.
- It is cheap (fast enough for repeated action scoring each turn).

---

## 4) Q2: `MinimaxAgent.getAction` Detailed Flow

### Purpose
Choose the action that maximizes the minimax value assuming ghosts play optimally against Pacman.

### Variables and recursion contract

- `numAgents = gameState.getNumAgents()`
- Helper function: `minimax(state, depth, agentIndex)`
  - `state`: current GameState node
  - `depth`: how many full plies completed
  - `agentIndex`: whose turn now

### Base cases

Return `self.evaluationFunction(state)` when:
- `depth == self.depth`
- `state.isWin()`
- `state.isLose()`
- no legal actions for current agent

### Agent transition math

- `nextAgent = (agentIndex + 1) % numAgents`
- `nextDepth = depth + 1 if nextAgent == 0 else depth`

Meaning:
- Depth increases only after all ghosts moved and turn returns to Pacman.

### Node behavior

- If `agentIndex == 0` (Pacman):
  - initialize `value = -inf`
  - for each legal action:
    - generate successor
    - recurse
    - keep max

- Else ghost node:
  - initialize `value = +inf`
  - for each legal action:
    - generate successor
    - recurse
    - keep min

### Root action selection

- iterate over Pacman legal actions in current state
- compute minimax value of each successor
- keep action with highest value
- default starts as `Directions.STOP`

### Important autograder detail

`generateSuccessor` is called exactly in expansion loops (no unnecessary calls), so expansion-count tests pass.

---

## 5) Q3: `AlphaBetaAgent.getAction` Detailed Flow

### Purpose
Same result as minimax, but faster by pruning branches that cannot affect final decision.

### Helper signature

`alphabeta(state, depth, agentIndex, alpha, beta)`

- `alpha`: best guaranteed value found for max side so far
- `beta`: best guaranteed value found for min side so far

### Shared parts with minimax

- same base cases
- same legal action handling
- same `nextAgent` / `nextDepth` transition

### Pacman node (max)

1. `value = -inf`
2. For each action:
   - recurse child
   - update `value = max(value, child)`
   - prune if `value > beta`
   - update `alpha = max(alpha, value)`

### Ghost node (min)

1. `value = +inf`
2. For each action:
   - recurse child
   - update `value = min(value, child)`
   - prune if `value < alpha`
   - update `beta = min(beta, value)`

### Why `>` / `<` (not equality)

Autograder expects a specific explored-state set. Pruning on equality can change explored count. Using strict comparisons matches required behavior.

### Root behavior

- loop over Pacman actions
- call helper with current `alpha`, `beta`
- update best action/value
- update root `alpha`

---

## 6) Q4: `ExpectimaxAgent.getAction` Detailed Flow

### Purpose
Model ghosts as random (uniform) instead of adversarial.

### Helper signature

`expectimax(state, depth, agentIndex)`

### Base cases and transitions

Exactly same stop conditions and same `nextAgent`/`nextDepth` handling as minimax.

### Node behavior

- Pacman node (`agentIndex == 0`):
  - choose max child value (same as minimax).

- Ghost node:
  - compute expected value:
    - `probability = 1.0 / len(legalActions)`
    - sum `probability * childValue` for each action

### Root action selection

- evaluate each Pacman action by expectimax value
- return action with highest expected utility

---

## 7) Q5: `betterEvaluationFunction` Detailed Flow

### Purpose
Score a **state** (not action) so depth-2 search plays strongly.

### Inputs collected

1. win/lose checks first:
   - win -> `+inf`
   - lose -> `-inf`

2. gather state features:
   - `pacmanPos`
   - `foodList`
   - `ghostStates`
   - `capsules`
   - base `score`

### Feature terms

#### Food term
- nearest food distance reward: `+ 8.0/(d+1)`
- remaining food penalty: `- 3.0 * foodCount`

This encourages both local progress and global completion.

#### Capsule term
- nearest capsule reward: `+ 3.0/(d+1)`
- remaining capsule penalty: `- 8.0 * capsuleCount`

Capsules become strategically attractive, especially with active ghosts nearby.

#### Ghost term (per ghost)
- if ghost scared:
  - reward approaching: `+12.0/(d+1)`
- else active:
  - if `d <= 1`: heavy penalty `-500`
  - else mild risk penalty `-3.0/d`

### Return

Return final weighted score.

### Why it performs well

- strong survival pressure near active ghosts,
- consistent food completion pressure,
- opportunistic scared-ghost chasing,
- low computational overhead.

---

## 8) How Variables Become Lists (Your Specific Question)

Common list-producing lines and origins:

1. `gameState.getLegalActions(agentIndex)` -> list of action strings.
2. `newFood.asList()` / `currentGameState.getFood().asList()` -> list of food coordinate tuples.
3. `gameState.getGhostStates()` -> list of `GhostState` objects.
4. `gameState.getCapsules()` -> list of capsule coordinate tuples.
5. `[ghostState.scaredTimer for ghostState in newGhostStates]` -> list of integers.
6. Manual lists built in code:
   - `activeGhostDistances = []`
   - `scaredGhostDistances = []`
   - filled inside loop with `append(distance)`.

How to use these lists safely:
- check non-empty before `min(...)`.
- use `len(list)` for count features.
- iterate directly with `for item in list:`.

---

## 9) How to Run and Observe Each Agent

From `multiagent/` directory:

```bash
python pacman.py -p ReflexAgent
python pacman.py -p MinimaxAgent -a depth=2
python pacman.py -p AlphaBetaAgent -a depth=3 -l smallClassic
python pacman.py -p ExpectimaxAgent -a depth=3 -l minimaxClassic
python pacman.py -p ExpectimaxAgent -a depth=2 -l smallClassic -a evalFn=better
```

Autograder checks:

```bash
python autograder.py -q q1 --no-graphics
python autograder.py -q q2 --no-graphics
python autograder.py -q q3 --no-graphics
python autograder.py -q q4 --no-graphics
python autograder.py -q q5 --no-graphics
```

---

## 10) Debugging Tips if You Edit Further

1. If Q2/Q3 fails expansion count:
   - check extra/missing `generateSuccessor` calls.
2. If Q3 fails but Q2 passes:
   - check pruning conditions (`>` and `<` only).
3. If Q4 behaves like minimax:
   - check ghost node uses expected average, not min.
4. If Q5 times out:
   - keep heuristic arithmetic simple; avoid expensive path algorithms.
5. If Pacman freezes:
   - increase food pressure or reduce `STOP` preference.

---

If you want, I can also create a third markdown file with a **worked dry-run trace** of one minimax tree (with 1 Pacman + 2 ghosts) showing exact `depth`, `agentIndex`, `alpha`, `beta`, and returned values at each recursive call.
