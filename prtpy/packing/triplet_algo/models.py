from typing import List, Tuple, Dict, Optional, Deque
from .solution import Solution
from collections import defaultdict, deque
from .clock import Clock
from dataclasses import dataclass, field
from dataclasses import dataclass


@dataclass
class SolverData:
    MAX_LOOPS: int = 1_000_000_000_000
    MAX_CASE_SECONDS: float = 1000.0
    BACKTRACK_CHECK_TIME_PER_LOOPS: int = 1000

    class Error(Exception):
        pass

    class NoSolution(Error):
        pass

    class ProblemTooBig(Error):
        pass

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
            self.a_index_set_case_count = 0
            self.total_step_count = 0
            self.total_branching_count = 0
            self.total_backtrack_events = 0
            self.total_loops = 0

            # additional params
            self.improvement_passes = 0
            self.improvement_distance = 0
            self.improvement_node_count = 0
            self.improvement_saved_count = 0
            self.improvement_skip1_count = 0
            self.improvement_skip2_count = 0
            self.T = 0
            self.G = 0
            # end of edition

            self.total_loop_states_by_depth: Dict[int, int] = defaultdict(int)
            self.total_loop_states_by_step_counts: Dict[int, int] = defaultdict(int)
            self.success = False
            self.a_cases_investigated = 0
            self.solution = Solution()
            self.winning_branches: List[SolverData.BranchingChoiceStats] = []
            self.error_message = ""
            
    @staticmethod
    def get_current_time() -> float:
        return Clock.elapsed()
    

@dataclass
class GroupInfo:
    left_a: int = 0
    left_bc: int = 0
    available_triplet_indices_a: list[int] = field(default_factory=list)
    available_triplet_indices_bc: list[int] = field(default_factory=list)


@dataclass
class TripletInfo:
    triplet: tuple[int, int, int]
    is_available: bool = True
    equal_bc: bool = False
    used_count: int = 0
    index_of_available: int = 0
    index_of_available_a: int = 0
    index_of_available_b: int = 0
    index_of_available_c: int | None = None


Triplet = Tuple[int, int, int]

@dataclass
class TripletSearchContext:
    total_loops: int
    t_solver_start: int
    group_cardinality: List[int]
    groups: List[Deque[int]]
    triplets_abc: List[Triplet]
    group_of_item: List[int]