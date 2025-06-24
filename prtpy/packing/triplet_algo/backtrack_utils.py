from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
import logging
from .models import SolverData

logger = logging.getLogger("trialgo.triplet_algo")


# level b
WeightType = int
from dataclasses import dataclass, field



class BranchImpossible(Exception):
        pass

class Stats:
    def __init__(self, max_loops: int, t_solver_start: float):
        self.current_step_count = 0
        self.current_branching_count = 0
        self.current_backtrack_events = 0
        self.loop_states_by_depth: Dict[int, int] = defaultdict(int)
        self.loop_states_by_step_counts: Dict[int, int] = defaultdict(int)
        self.winning_branches: List[SolverData.BranchingChoiceStats] = []
        self.is_backtrack_successful = False
        self.current_loops = 0
        self.max_loops = max_loops
        self.t_solver_start = t_solver_start

class Step:
    def __init__(self, level_b: Optional["LevelB"] = None):
        self.level_b = level_b

    def perform(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError

class TripletBaseStep(Step):
    def __init__(self, triplet_index: int, level_b: Optional["LevelB"] = None):
        super().__init__(level_b)
        self.triplet_index = triplet_index

class ApplyTriplet(TripletBaseStep):
    def perform(self) -> None:
        # print("in perform ApplyTriplet")
        self.level_b.add_used_triplet(self.triplet_index)  ############
        self.level_b.chosen_triplet_indices.append(self.triplet_index)

    def undo(self) -> None:
        self.level_b.remove_used_triplet(self.triplet_index)  ############
        self.level_b.chosen_triplet_indices.pop()

class ExcludeTriplet(TripletBaseStep):
    def perform(self) -> None:
        self.level_b.set_triplet_disabled(self.triplet_index)  ############

    def undo(self) -> None:
        self.level_b.set_triplet_enabled(self.triplet_index)  ############

class BranchingStep(Step):
    def __init__(
        self, options: deque["LevelB.Step"], level_b: Optional["LevelB"] = None
    ) -> None:
        super().__init__(level_b)
        self.options = options

        # addition
        # for finding long backtracks
        self.step_count_start = 0
        self.step_count_backtrack = 0
        self.backtrack_happened = False

    def perform(self) -> None:
        self.options[0].perform()

    def undo(self) -> None:
        self.options[0].undo()
        self.options.popleft()

        # addition
        self.backtrack_happened = True
        self.step_count_backtrack = self.level_b.stats.current_step_count