from typing import Dict
from collections import Counter
from .problem import Problem
from .solution import Solution
from .triplet import Triplet
import logging

logger = logging.getLogger(__name__)


class SolutionChecker:
    class WrongSolution(Exception):
        def __init__(self, msg: str):
            self.msg = msg
            super().__init__(msg)

        def __str__(self):
            return self.msg

    @staticmethod
    def check(problem: Problem, solution: Solution):
        logger.debug("Starting solution check.")
        
        triplets = solution.get_triplets()
        expected_n = problem.get_n()
        actual_n = len(triplets)
        
        logger.debug(f"Expected triplet count: {expected_n}, Actual triplet count: {actual_n}")
        
        if expected_n != actual_n:
            error_msg = f"Triplet count mismatch: expected {expected_n}, got {actual_n}."
            logger.error(error_msg)
            raise SolutionChecker.WrongSolution(error_msg)

        if expected_n == 0:
            logger.info("No triplets expected and none found. Solution check passed trivially.")
            return

        target_sum = triplets[0].sum()
        logger.debug(f"Target sum for all triplets: {target_sum}")

        for i, t in enumerate(triplets):
            t_sum = t.sum()
            if t_sum != target_sum:
                error_msg = (
                    f"Triplet sums not equal at index {i}: "
                    f"first triplet sum = {target_sum}, current triplet sum = {t_sum}."
                )
                logger.error(error_msg)
                raise SolutionChecker.WrongSolution(error_msg)

        counter: Dict[int, int] = Counter(problem.get_weights())
        logger.debug(f"Initial weights counter: {counter}")

        for t in triplets:
            counter[t.a()] -= 1
            counter[t.b()] -= 1
            counter[t.c()] -= 1

        logger.debug(f"Weight counter after subtracting triplets: {counter}")

        for w, count in counter.items():
            if count < 0:
                error_msg = f"Too many occurrences in solution: weight {w} has {-count} extra."
                logger.error(error_msg)
                raise SolutionChecker.WrongSolution(error_msg)
            elif count > 0:
                error_msg = f"Missing occurrences in solution: weight {w} missing {count} times."
                logger.error(error_msg)
                raise SolutionChecker.WrongSolution(error_msg)
        
        logger.info("Solution check passed successfully.")
