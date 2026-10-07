"""Tests for Q2 - water jug problem and breadth-first search.

Run from the project root:
    python -m unittest discover -v
"""

import json
import unittest
from pathlib import Path

from q2_water_jugs.problem import WaterJugProblem
from q2_water_jugs.search import (
    FAILURE,
    Node,
    breadth_first_search,
    depth_first_tree_search,
    expand,
    reachable_states,
)

PUZZLES = json.loads(
    (Path(__file__).resolve().parent.parent / "test_data" / "puzzles.json").read_text(encoding="utf-8")
)


def replay(problem, actions):
    """Apply a sequence of actions from the initial state; return every state visited."""
    states = [problem.initial]
    for action in actions:
        assert action in problem.actions(states[-1]), f"{action} not applicable in {states[-1]}"
        states.append(problem.result(states[-1], action))
    return states


def states_within(problem, steps):
    """All states reachable in at most `steps` actions (independent of breadth_first_search)."""
    layer = {problem.initial}
    seen = set(layer)
    for _ in range(steps):
        layer = {problem.result(s, a) for s in layer for a in problem.actions(s)} - seen
        seen |= layer
    return seen


class TestFormulation(unittest.TestCase):
    """States, actions and the transition model for the assignment's jugs (12, 8, 3)."""

    def setUp(self):
        self.p = WaterJugProblem()

    def test_initial_state_and_goal(self):
        self.assertEqual(self.p.initial, (0, 0, 0))
        self.assertFalse(self.p.is_goal((0, 0, 0)))
        self.assertTrue(self.p.is_goal((1, 8, 3)))
        self.assertTrue(self.p.is_goal((0, 1, 0)))
        self.assertTrue(self.p.is_goal((0, 0, 1)))

    def test_fill(self):
        self.assertEqual(self.p.result((0, 0, 0), ("Fill", 0)), (12, 0, 0))
        self.assertEqual(self.p.result((5, 2, 1), ("Fill", 2)), (5, 2, 3))

    def test_empty(self):
        self.assertEqual(self.p.result((12, 8, 3), ("Empty", 1)), (12, 0, 3))

    def test_pour_everything_when_it_fits(self):
        self.assertEqual(self.p.result((0, 2, 0), ("Pour", 1, 2)), (0, 0, 2))

    def test_pour_until_the_other_jug_is_full(self):
        self.assertEqual(self.p.result((12, 0, 0), ("Pour", 0, 1)), (4, 8, 0))
        self.assertEqual(self.p.result((4, 8, 0), ("Pour", 0, 2)), (1, 8, 3))

    def test_actions_from_empty_jugs_are_only_fills(self):
        self.assertEqual(self.p.actions((0, 0, 0)), [("Fill", 0), ("Fill", 1), ("Fill", 2)])

    def test_actions_from_full_jugs(self):
        actions = self.p.actions((12, 8, 3))
        self.assertEqual(actions, [("Empty", 0), ("Empty", 1), ("Empty", 2)])

    def test_there_are_twelve_actions_when_every_jug_is_partly_full(self):
        self.assertEqual(len(self.p.actions((5, 4, 1))), 3 + 3 + 6)

    def test_pouring_never_creates_or_loses_water(self):
        for state in reachable_states(self.p):
            for action in self.p.actions(state):
                new = self.p.result(state, action)
                if action[0] == "Pour":
                    self.assertEqual(sum(new), sum(state))

    def test_no_action_overflows_or_goes_negative(self):
        for state in reachable_states(self.p):
            for action in self.p.actions(state):
                new = self.p.result(state, action)
                self.assertNotEqual(new, state, "every applicable action must change the state")
                for amount, capacity in zip(new, self.p.capacities):
                    self.assertTrue(0 <= amount <= capacity, f"{state} {action} -> {new}")

    def test_size_of_state_space(self):
        # 13 * 9 * 4 = 468 possible tuples, but only 314 can actually be reached
        self.assertEqual(len(reachable_states(self.p)), 314)

    def test_action_names(self):
        self.assertEqual(self.p.action_name(("Fill", 0)), "Fill 12")
        self.assertEqual(self.p.action_name(("Empty", 2)), "Empty 3")
        self.assertEqual(self.p.action_name(("Pour", 0, 1)), "Pour 12->8")


class TestNodeAndExpand(unittest.TestCase):
    def test_expand_creates_one_child_per_action(self):
        p = WaterJugProblem()
        root = Node(p.initial)
        children = list(expand(p, root))
        self.assertEqual([c.state for c in children], [(12, 0, 0), (0, 8, 0), (0, 0, 3)])
        for child in children:
            self.assertIs(child.parent, root)
            self.assertEqual(child.path_cost, 1)
            self.assertEqual(child.depth, 1)

    def test_path_and_solution(self):
        root = Node((0, 0, 0))
        a = Node((12, 0, 0), root, ("Fill", 0), 1)
        b = Node((4, 8, 0), a, ("Pour", 0, 1), 2)
        self.assertEqual([n.state for n in b.path()], [(0, 0, 0), (12, 0, 0), (4, 8, 0)])
        self.assertEqual(b.solution(), [("Fill", 0), ("Pour", 0, 1)])
        self.assertEqual(root.solution(), [])


class TestBreadthFirstSearch(unittest.TestCase):
    def test_assignment_puzzle(self):
        p = WaterJugProblem((12, 8, 3), 1)
        node = breadth_first_search(p)
        self.assertIsNot(node, FAILURE)
        self.assertEqual(node.solution(), [("Fill", 0), ("Pour", 0, 1), ("Pour", 0, 2)])
        self.assertEqual(node.state, (1, 8, 3))
        self.assertEqual(node.path_cost, 3)

    def test_assignment_solution_is_shortest(self):
        p = WaterJugProblem((12, 8, 3), 1)
        self.assertFalse(any(p.is_goal(s) for s in states_within(p, 2)), "no solution in 2 steps")
        self.assertEqual(len(breadth_first_search(p).solution()), 3)

    def test_initial_state_is_already_a_goal(self):
        node = breadth_first_search(WaterJugProblem((12, 8, 3), 1, initial=(1, 0, 0)))
        self.assertEqual(node.state, (1, 0, 0))
        self.assertEqual(node.solution(), [])

    def test_unsolvable_puzzle_returns_failure(self):
        self.assertIs(breadth_first_search(WaterJugProblem((4, 6), 1)), FAILURE)

    def test_every_puzzle_in_test_data(self):
        for puzzle in PUZZLES:
            with self.subTest(puzzle["name"]):
                p = WaterJugProblem(puzzle["capacities"], puzzle["goal"])
                node = breadth_first_search(p)
                if not puzzle["solvable"]:
                    self.assertIs(node, FAILURE)
                    self.assertFalse(any(p.is_goal(s) for s in reachable_states(p)))
                    continue
                self.assertIsNot(node, FAILURE)
                states = replay(p, node.solution())          # the plan really works
                self.assertTrue(p.is_goal(states[-1]))
                self.assertEqual(states[-1], node.state)
                self.assertEqual(len(node.solution()), puzzle["shortest_steps"])
                self.assertEqual(node.path_cost, puzzle["shortest_steps"])
                if puzzle["shortest_steps"] > 0:                # nothing shorter exists
                    shorter = states_within(p, puzzle["shortest_steps"] - 1)
                    self.assertFalse(any(p.is_goal(s) for s in shorter))


class TestHeuristic(unittest.TestCase):
    """Supports answer 2b."""

    def setUp(self):
        self.p = WaterJugProblem()
        self.states = reachable_states(self.p)

    def true_cost(self, state):
        return len(breadth_first_search(WaterJugProblem(initial=state)).solution())

    def test_values(self):
        self.assertEqual(self.p.heuristic((1, 8, 3)), 0)
        self.assertEqual(self.p.heuristic((4, 8, 0)), 1)
        self.assertEqual(self.p.heuristic((0, 0, 0)), 2)

    def test_heuristic_is_admissible(self):
        for s in self.states:
            self.assertLessEqual(self.p.heuristic(s), self.true_cost(s), s)

    def test_heuristic_is_consistent(self):
        for s in self.states:
            for a in self.p.actions(s):
                s2 = self.p.result(s, a)
                self.assertLessEqual(self.p.heuristic(s),
                                     self.p.action_cost(s, a, s2) + self.p.heuristic(s2))

    def test_gallon_distance_is_not_admissible(self):
        # "how many gallons is the closest jug away from 1" overestimates, e.g. (5, 4, 3)
        def distance(s):
            return min(abs(amount - 1) for amount in s)
        self.assertEqual(distance((5, 4, 3)), 2)
        self.assertEqual(self.true_cost((5, 4, 3)), 1)
        overestimates = [s for s in self.states if distance(s) > self.true_cost(s)]
        self.assertEqual(len(overestimates), 22)


class TestCompleteness(unittest.TestCase):
    """Supports answer 2c: not every search algorithm is guaranteed to reach the goal."""

    def test_tree_search_dfs_loops_forever(self):
        node, expansions = depth_first_tree_search(WaterJugProblem(), max_expansions=10_000)
        self.assertIs(node, FAILURE)
        self.assertEqual(expansions, 10_000)

    def test_bfs_is_complete_on_the_same_problem(self):
        self.assertIsNot(breadth_first_search(WaterJugProblem()), FAILURE)


if __name__ == "__main__":
    unittest.main()
