from .problem import Problem
from .triplet_planner import TripletPlanner
from .models import SolverData
import logging

logger = logging.getLogger(__name__)  # module-specific logger

class Solver:
    @staticmethod
    def solve(problem: Problem, use_local_search: bool = False) -> "Solver. Answer":
        logger.debug("Solver.solve called with problem: %s", problem)

        level_state = TripletPlanner(problem)
        logger.info("Initialized TripletPlanner")

        try:
            logger.debug("Starting algorithm execution")
            level_state.execute_algorithm(use_local_search)
            logger.info("Algorithm executed successfully")
        except SolverData.Error as e:
            # logger.error("SolverData.Error encountered: %s", str(e))
            level_state.set_message(str(e))

        answer = level_state.get_answer()
        logger.debug("Answer returned: %s", answer)
        return answer
