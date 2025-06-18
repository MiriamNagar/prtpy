from typing import Dict
from collections import Counter
from prtpy.packing.triplet_algo.problem import Problem
from prtpy.packing.triplet_algo.solution import Solution
from prtpy.packing.triplet_algo.triplet import Triplet


class SolutionChecker:
    class WrongSolution(Exception):
        def __init__(self, msg: str):
            # addition
            self.msg = msg

            super().__init__(msg)

        # addition
        def __str__(self):
            return self.msg

    @staticmethod
    def check(problem: Problem, solution: Solution):
        triplets = solution.get_triplets()
        expected_n = problem.get_n()
        actual_n = len(triplets)

        if expected_n != actual_n:
            raise SolutionChecker.WrongSolution(
                f"Triplet count mismatch: {expected_n} vs {actual_n}."
            )

        if expected_n == 0:
            return

        target_sum = triplets[0].sum()
        for i, t in enumerate(triplets):
            if t.sum() != target_sum:
                raise SolutionChecker.WrongSolution(
                    f"Triplet sums not equal: {triplets[0]}={target_sum} vs {t}={t.sum()}."
                )

        counter: Dict[int, int] = Counter(problem.get_weights())

        for t in triplets:
            counter[t.a()] -= 1
            counter[t.b()] -= 1
            counter[t.c()] -= 1

        for w, count in counter.items():
            if count < 0:
                raise SolutionChecker.WrongSolution(
                    f"Too many occurrences in solution: weight (w) has {abs(count)} extra."
                )
            elif count > 0:
                raise SolutionChecker.WrongSolution(
                    f"Missing occurrences in solution: weight {w} missing {count} times."
                )
