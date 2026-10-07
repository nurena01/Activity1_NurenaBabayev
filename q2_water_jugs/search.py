"""Q2 - Search algorithms.

NODE and EXPAND follow AIMA 4th ed. Section 3.3 (Figure 3.7), and
breadth_first_search follows Figure 3.9 BREADTH-FIRST-SEARCH line by line.
"""

from __future__ import annotations

from collections import deque

FAILURE = None


class Node:
    """A node in the search tree: a state plus how we got there."""

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = 0 if parent is None else parent.depth + 1

    def path(self) -> list["Node"]:
        """The nodes from the root down to this node."""
        node, nodes = self, []
        while node is not None:
            nodes.append(node)
            node = node.parent
        return nodes[::-1]

    def solution(self) -> list:
        """The sequence of actions from the initial state to this node."""
        return [node.action for node in self.path()[1:]]

    def __repr__(self):
        return f"<Node {self.state}>"


def expand(problem, node):
    """EXPAND (Figure 3.7): generate the child nodes of node.

    function EXPAND(problem, node) yields nodes
        s <- node.STATE
        for each action in problem.ACTIONS(s) do
            s' <- problem.RESULT(s, action)
            cost <- node.PATH-COST + problem.ACTION-COST(s, action, s')
            yield NODE(STATE=s', PARENT=node, ACTION=action, PATH-COST=cost)
    """
    s = node.state
    for action in problem.actions(s):
        s2 = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s2)
        yield Node(state=s2, parent=node, action=action, path_cost=cost)


def breadth_first_search(problem):
    """BREADTH-FIRST-SEARCH (Figure 3.9).

    function BREADTH-FIRST-SEARCH(problem) returns a solution node or failure
        node <- NODE(problem.INITIAL)
        if problem.IS-GOAL(node.STATE) then return node
        frontier <- a FIFO queue, with node as an element
        reached <- {problem.INITIAL}
        while not IS-EMPTY(frontier) do
            node <- POP(frontier)
            for each child in EXPAND(problem, node) do
                s <- child.STATE
                if problem.IS-GOAL(s) then return child      # early goal test
                if s is not in reached then
                    add s to reached
                    add child to frontier
        return failure
    """
    node = Node(problem.initial)
    if problem.is_goal(node.state):
        return node
    frontier = deque([node])          # FIFO queue
    reached = {problem.initial}
    while frontier:
        node = frontier.popleft()     # POP takes the oldest (shallowest) node
        for child in expand(problem, node):
            s = child.state
            if problem.is_goal(s):
                return child
            if s not in reached:
                reached.add(s)
                frontier.append(child)
    return FAILURE


def depth_first_tree_search(problem, max_expansions=10_000):
    """Depth-first TREE search (no reached set), used to support answer 2c.

    Without remembering visited states, DFS can loop forever between the same
    states. max_expansions stops the demonstration; it returns
    (node or FAILURE, number of expansions).
    """
    frontier = [Node(problem.initial)]  # LIFO stack
    expansions = 0
    while frontier and expansions < max_expansions:
        node = frontier.pop()
        if problem.is_goal(node.state):
            return node, expansions
        expansions += 1
        # reversed() so the first action in ACTIONS(s) is tried first
        frontier.extend(reversed(list(expand(problem, node))))
    return FAILURE, expansions


def reachable_states(problem) -> set:
    """Every state that can be reached from the initial state (size of the state space)."""
    reached = {problem.initial}
    frontier = deque([Node(problem.initial)])
    while frontier:
        for child in expand(problem, frontier.popleft()):
            if child.state not in reached:
                reached.add(child.state)
                frontier.append(child)
    return reached
