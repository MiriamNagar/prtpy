from .problem import Problem
from .triplet_planner import TripletPlanner
from .models import SolverData
import logging

logger = logging.getLogger(__name__)


class Solver:
    """
    High-level solver class that interfaces with the TripletPlanner to solve
    given problem instances.

    Provides a static method to run the solver algorithm and optionally
    perform a local search improvement phase.
    """

    @staticmethod
    def solve(problem: Problem, use_local_search: bool = False) -> "Solver.Answer":
        """
        Solve the given problem instance using TripletPlanner.

        Args:
            problem (Problem): The problem instance to solve.
            use_local_search (bool): If True, perform a local search heuristic
                after the main solving algorithm to improve the solution.

        Returns:
            Solver.Answer: An object containing the solution, statistics,
                and status of the solving process.
        """
        logger.info("Solver.solve called with problem: %s", problem)

        # Initialize the TripletPlanner with the given problem
        level_state = TripletPlanner(problem)
        logger.info("Initialized TripletPlanner")

        try:
            logger.info("Starting algorithm execution")
            # Run the core solving algorithm with or without local search
            level_state.execute_algorithm(use_local_search)
            logger.info("Algorithm executed successfully")
        except SolverData.Error as e:
            # If a solver-related error occurs, record its message in TripletPlanner
            # level_state.set_message(str(e))
            # logger.error("SolverData.Error encountered: %s", str(e))
            raise SolverData.Error

        # Retrieve and return the answer object with solution details and stats
        answer = level_state.get_answer()
        logger.debug("Answer returned: %s", answer)
        return answer
