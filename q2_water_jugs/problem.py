"""Q2 - Water Jug problem formulation.

Formal problem definition, following AIMA 4th ed. Section 3.1.1:
    - a set of states, and the INITIAL state
    - ACTIONS(s): the actions applicable in state s
    - RESULT(s, a): the transition model
    - IS-GOAL(s): the goal test
    - ACTION-COST(s, a, s'): the cost of an action

State  : a tuple (a, b, c) = gallons currently in the 12-, 8- and 3-gallon jugs.
Initial: (0, 0, 0) - all jugs empty.
Goal   : any jug holds exactly 1 gallon.
Actions: Fill(i) from the faucet, Empty(i) onto the ground, Pour(i, j) from jug i into jug j.
"""

from __future__ import annotations


class Problem:
    """Abstract search problem (same interface as the textbook's PROBLEM)."""

    def __init__(self, initial):
        self.initial = initial

    def actions(self, state):
        raise NotImplementedError

    def result(self, state, action):
        raise NotImplementedError

    def is_goal(self, state) -> bool:
        raise NotImplementedError

    def action_cost(self, state, action, result) -> int:
        return 1


class WaterJugProblem(Problem):
    """Jugs with the given capacities, a faucet, and the ground.

    The defaults are the assignment's puzzle: jugs of 12, 8 and 3 gallons,
    starting empty, and the goal of measuring exactly 1 gallon.
    """

    def __init__(self, capacities=(12, 8, 3), goal=1, initial=None):
        self.capacities = tuple(capacities)
        self.goal = goal
        if initial is None:
            initial = (0,) * len(self.capacities)
        super().__init__(tuple(initial))

    def actions(self, state):
        """ACTIONS(s): every Fill, Empty and Pour that changes the state.

        Actions that would do nothing (filling a full jug, emptying an empty
        jug, pouring from an empty jug or into a full one) are not applicable.
        """
        jugs = range(len(self.capacities))
        actions = []
        for i in jugs:
            if state[i] < self.capacities[i]:
                actions.append(("Fill", i))
        for i in jugs:
            if state[i] > 0:
                actions.append(("Empty", i))
        for i in jugs:
            for j in jugs:
                if i != j and state[i] > 0 and state[j] < self.capacities[j]:
                    actions.append(("Pour", i, j))
        return actions

    def result(self, state, action):
        """RESULT(s, a): the transition model."""
        new = list(state)
        if action[0] == "Fill":
            _, i = action
            new[i] = self.capacities[i]
        elif action[0] == "Empty":
            _, i = action
            new[i] = 0
        elif action[0] == "Pour":
            _, i, j = action
            amount = min(state[i], self.capacities[j] - state[j])
            new[i] -= amount
            new[j] += amount
        else:
            raise ValueError(f"unknown action: {action}")
        return tuple(new)

    def is_goal(self, state) -> bool:
        """IS-GOAL(s): some jug holds exactly the goal amount."""
        return self.goal in state

    def heuristic(self, state) -> int:
        """h(s) for answer 2b: 0 at a goal, 1 if one action reaches a goal, else 2.

        Admissible (never overestimates) and consistent, since every action costs 1.
        """
        if self.is_goal(state):
            return 0
        if any(self.is_goal(self.result(state, a)) for a in self.actions(state)):
            return 1
        return 2

    def action_name(self, action) -> str:
        """Readable action name using jug sizes, e.g. 'Pour 12->8'."""
        size = self.capacities
        if action[0] == "Pour":
            return f"Pour {size[action[1]]}->{size[action[2]]}"
        return f"{action[0]} {size[action[1]]}"
