"""Solve a water jug puzzle with breadth-first search and print the solution.

Usage (from the project root):
    python -m q2_water_jugs.main                              # the assignment: jugs 12, 8, 3 - measure 1
    python -m q2_water_jugs.main --capacities 5 3 --goal 4    # any other puzzle
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow "python q2_water_jugs/main.py" as well as "python -m q2_water_jugs.main"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q2_water_jugs.problem import WaterJugProblem
from q2_water_jugs.search import FAILURE, breadth_first_search, reachable_states


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Solve a water jug puzzle with breadth-first search.")
    parser.add_argument("--capacities", type=int, nargs="+", default=[12, 8, 3],
                        help="jug sizes in gallons (default: 12 8 3)")
    parser.add_argument("--goal", type=int, default=1, help="gallons to measure (default: 1)")
    args = parser.parse_args(argv)

    if any(c <= 0 for c in args.capacities) or args.goal < 0:
        print("Error: capacities must be positive and the goal cannot be negative.", file=sys.stderr)
        return 1

    problem = WaterJugProblem(args.capacities, args.goal)
    print(f"Jugs: {', '.join(str(c) for c in problem.capacities)} gallons | "
          f"goal: exactly {problem.goal} gallon(s) in any jug")
    print(f"Initial state: {problem.initial} | reachable states: {len(reachable_states(problem))}\n")

    node = breadth_first_search(problem)
    if node is FAILURE:
        print("No solution: the goal cannot be reached from the initial state.")
        return 0

    path = node.path()
    print(f"Step 0: {path[0].state}  (start)")
    for step, n in enumerate(path[1:], start=1):
        print(f"Step {step}: {n.state}  <- {problem.action_name(n.action)}")
    print(f"\nSolved in {len(path) - 1} steps (path cost {node.path_cost}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
