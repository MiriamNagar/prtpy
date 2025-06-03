
from typing import Dict, List 
from problem import Problem 
from solution import Solution 
from bigindex import BigIndex 
from levela import LevelA 
from clock import Clock

class Solver:
    class Error (Exception): 
        pass
    class NoSolution (Error):
        pass
    class ProblemTooBig (Error):
        pass
    
    MAX_LOOPS: int = 1_000_000_000_000 
    MAX_CASE_SECONDS: float = 1000.0
    BACKTRACK_CHECK_TIME_PER_LOOPS: int = 1000

    class BranchingChoiceStats:
        def __init__(self, apply, is_a, left, max_take, max_uses): 
            self.apply = apply
            self.is_a = is_a
            self.left = left
            self.max_take = max_take 
            self.max_uses = max_uses

    class Answer:
        def __init__(self):
            self.preprocess_triplet_count = 0 
            self.definitely_a_cardinality = 0
            self.maybe_a_cardinality = 0
            self.maybe_a_choose = 0
            self.a_index_set_case_count = BigIndex(0)
            self.total_step_count = 0
            self.total_branching_count = 0
            self.total_backtrack_events = 0 
            self.total_loops = 0

            # additional params
            self.total_loops = 0
            self.improvement_passes = 0
            self.improvement_distance = 0
            self.improvement_node_count = 0
            self.improvement_saved_count = 0
            self.improvement_skip1_count = 0
            self.improvement_skip2_count = 0
            self.T = 0
            self.G = 0
            # end of edition

            self.total_loop_states_by_depth: Dict[int, int] = {}
            self.total_loop_states_by_step_counts: Dict[int, int] = {}
            self.success = False
            self.a_cases_investigated = BigIndex (0) 
            self.solution = Solution()
            self.winning_branches: List [Solver. BranchingChoiceStats] = []
            self.error_message = ""
    
    @staticmethod
    def solve (problem: Problem) -> 'Solver. Answer':
        level_state = LevelA (problem)
        try:
            level_state.execute_algorithm()
        except Solver. Error as e:
            level_state.set_message(str(e)) 
        return level_state.get_answer()

    @staticmethod
    def get_current_time() -> float:
        return Clock.elapsed()

