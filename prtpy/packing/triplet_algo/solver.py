from .problem import Problem
from .levela import LevelA
from .problem import Problem
from .models import SolverData


class Solver:
    @staticmethod
    def solve(problem: Problem) -> "Solver. Answer":
        level_state = LevelA(problem)
        try:
            level_state.execute_algorithm()
        except SolverData.Error as e:
            level_state.set_message(str(e))
        return level_state.get_answer()
