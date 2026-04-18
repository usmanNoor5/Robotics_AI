# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance
from game import Directions
import random, util

from game import Agent
from pacman import GameState


class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """

    def getAction(self, gameState: GameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [
            index for index in range(len(scores)) if scores[index] == bestScore
        ]
        chosenIndex = random.choice(bestIndices)  # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState: GameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

        if successorGameState.isWin():
            return float("inf")
        if successorGameState.isLose():
            return float("-inf")

        score = successorGameState.getScore()
        foodList = newFood.asList()

        if foodList:
            closestFoodDist = min(
                manhattanDistance(newPos, foodPos) for foodPos in foodList
            )
            score += 2.5 / (closestFoodDist + 1)
            score -= 1.5 * len(foodList)

        activeGhostDistances = []
        scaredGhostDistances = []
        for ghostState in newGhostStates:
            ghostPos = ghostState.getPosition()
            distance = manhattanDistance(newPos, ghostPos)
            if ghostState.scaredTimer > 0:
                scaredGhostDistances.append(distance)
            else:
                activeGhostDistances.append(distance)

        if activeGhostDistances:
            nearestActiveGhost = min(activeGhostDistances)
            if nearestActiveGhost <= 1:
                score -= 200
            else:
                score -= 1.0 / nearestActiveGhost

        if scaredGhostDistances:
            nearestScaredGhost = min(scaredGhostDistances)
            score += 1.0 / (nearestScaredGhost + 1)

        if action == Directions.STOP:
            score -= 3

        return score


def scoreEvaluationFunction(currentGameState: GameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()


class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn="scoreEvaluationFunction", depth="2"):
        self.index = 0  # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)


class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.

        Here are some method calls that might be useful when implementing minimax.

        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1

        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action

        gameState.getNumAgents():
        Returns the total number of agents in the game

        gameState.isWin():
        Returns whether or not the game state is a winning state

        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        numAgents = gameState.getNumAgents()

        def minimax(state, depth, agentIndex):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth

            if agentIndex == 0:
                value = float("-inf")
                for action in legalActions:
                    successor = state.generateSuccessor(agentIndex, action)
                    value = max(value, minimax(successor, nextDepth, nextAgent))
                return value

            value = float("inf")
            for action in legalActions:
                successor = state.generateSuccessor(agentIndex, action)
                value = min(value, minimax(successor, nextDepth, nextAgent))
            return value

        bestValue = float("-inf")
        bestAction = Directions.STOP
        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = minimax(successor, 0, 1 % numAgents)
            if value > bestValue:
                bestValue = value
                bestAction = action

        return bestAction


class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        numAgents = gameState.getNumAgents()

        def alphabeta(state, depth, agentIndex, alpha, beta):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth

            if agentIndex == 0:
                value = float("-inf")
                for action in legalActions:
                    successor = state.generateSuccessor(agentIndex, action)
                    value = max(
                        value, alphabeta(successor, nextDepth, nextAgent, alpha, beta)
                    )
                    if value > beta:
                        return value
                    alpha = max(alpha, value)
                return value

            value = float("inf")
            for action in legalActions:
                successor = state.generateSuccessor(agentIndex, action)
                value = min(
                    value, alphabeta(successor, nextDepth, nextAgent, alpha, beta)
                )
                if value < alpha:
                    return value
                beta = min(beta, value)
            return value

        alpha = float("-inf")
        beta = float("inf")
        bestValue = float("-inf")
        bestAction = Directions.STOP

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = alphabeta(successor, 0, 1 % numAgents, alpha, beta)
            if value > bestValue:
                bestValue = value
                bestAction = action
            alpha = max(alpha, bestValue)

        return bestAction


class ExpectimaxAgent(MultiAgentSearchAgent):
    """
    Your expectimax agent (question 4)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        numAgents = gameState.getNumAgents()

        def expectimax(state, depth, agentIndex):
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = (agentIndex + 1) % numAgents
            nextDepth = depth + 1 if nextAgent == 0 else depth

            if agentIndex == 0:
                value = float("-inf")
                for action in legalActions:
                    successor = state.generateSuccessor(agentIndex, action)
                    value = max(value, expectimax(successor, nextDepth, nextAgent))
                return value

            probability = 1.0 / len(legalActions)
            value = 0
            for action in legalActions:
                successor = state.generateSuccessor(agentIndex, action)
                value += probability * expectimax(successor, nextDepth, nextAgent)
            return value

        bestValue = float("-inf")
        bestAction = Directions.STOP
        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = expectimax(successor, 0, 1 % numAgents)
            if value > bestValue:
                bestValue = value
                bestAction = action

        return bestAction


def betterEvaluationFunction(currentGameState: GameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: Uses a weighted linear combination of game score, nearest-food
    distance, remaining food and capsules, and ghost pressure. It strongly avoids
    active ghosts at close range while rewarding reachable scared ghosts.
    """
    if currentGameState.isWin():
        return float("inf")
    if currentGameState.isLose():
        return float("-inf")

    pacmanPos = currentGameState.getPacmanPosition()
    foodList = currentGameState.getFood().asList()
    ghostStates = currentGameState.getGhostStates()
    capsules = currentGameState.getCapsules()

    score = currentGameState.getScore()

    if foodList:
        closestFoodDist = min(
            manhattanDistance(pacmanPos, foodPos) for foodPos in foodList
        )
        score += 8.0 / (closestFoodDist + 1)
        score -= 3.0 * len(foodList)

    if capsules:
        closestCapsuleDist = min(
            manhattanDistance(pacmanPos, capsulePos) for capsulePos in capsules
        )
        score += 3.0 / (closestCapsuleDist + 1)
        score -= 8.0 * len(capsules)

    for ghostState in ghostStates:
        ghostPos = ghostState.getPosition()
        ghostDist = manhattanDistance(pacmanPos, ghostPos)
        scaredTime = ghostState.scaredTimer

        if scaredTime > 0:
            score += 12.0 / (ghostDist + 1)
        else:
            if ghostDist <= 1:
                score -= 500
            else:
                score -= 3.0 / ghostDist

    return score


# Abbreviation
better = betterEvaluationFunction
