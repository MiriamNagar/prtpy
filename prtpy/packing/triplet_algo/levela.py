from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
from problem import Problem
from triplet import Triplet
from solution import Solution
from solution_checker import SolutionChecker
from multi_combination import MultiCombination
from bigindex import BigIndex
from clock import Clock
from base import (
    LEVELB_BRANCHING_TIE_ORDER,
    BACKTRACKING_POLICY,
    USE_IMPROVEMENT_HEURISTIC,
)

# from levelc import LevelC

# from solver import Solver
WeightType = int


class Solver:
    class Error(Exception):
        pass

    class NoSolution(Error):
        pass

    class ProblemTooBig(Error):
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
            self.a_cases_investigated = BigIndex(0)
            self.solution = Solution()
            self.winning_branches: List[Solver.BranchingChoiceStats] = []
            self.error_message = ""

    @staticmethod
    def solve(problem: Problem) -> "Solver. Answer":
        level_state = LevelA(problem)
        try:
            level_state.execute_algorithm()
        except Solver.Error as e:
            level_state.set_message(str(e))
        return level_state.get_answer()

    @staticmethod
    def get_current_time() -> float:
        return Clock.elapsed()


# level b
WeightType = int
from dataclasses import dataclass, field


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


class LevelB:
    class BranchImpossible(Exception):
        pass

    class Stats:
        def __init__(self, max_loops: int, t_solver_start: float):
            self.current_step_count = 0
            self.current_branching_count = 0
            self.current_backtrack_events = 0
            self.loop_states_by_depth: Dict[int, int] = defaultdict(int)
            self.loop_states_by_step_counts: Dict[int, int] = defaultdict(int)
            self.winning_branches: List[Solver.BranchingChoiceStats] = []
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

    def __init__(self, a_index_set: List[int], level_a: "LevelA"):
        # from levela import LevelA # avoid circular import at module top level
        self.level_a: LevelA = level_a
        self.a_index_set = a_index_set
        self.stats = LevelB.Stats(
            Solver.MAX_LOOPS - level_a.answer.total_loops, level_a.t_solver_start
        )
        # self.triplets = level_a.triplets_abc
        self.triplets: list[TripletInfo] = []
        self.triplet_states: List[Dict[str, int]] = []
        self.chosen_triplet_indices: List[int] = []
        # self.available_triplet_indices: List[int] = list (range(len(self.triplets)))
        self.available_triplet_indices: list[int] = []

        # local stacks
        self.stack: deque["LevelB.Step"] = deque()

        self.prepare()
        self.stats.is_backtrack_successful = self.execute_backtrack()

    def prepare(self):
        G = len(self.level_a.groups)
        # print(f" groups level a: {self.level_a.groups}\n")

        # groups
        # G = len(self.level_a.groups)
        self.groups: list[GroupInfo] = [
            GroupInfo(left_a=0, left_bc=self.level_a.group_cardinality[g])
            for g in range(G)
        ]
        self.take_options_a = [0] * G
        self.take_options_bc = [0] * G

        T = len(self.level_a.triplets_abc)
        self.triplets: list[TripletInfo] = [
            TripletInfo(triplet=(0, 0, 0)) for _ in range(T)
        ]

        for t in range(T):
            self.triplets[t].triplet = self.level_a.triplets_abc[t]
            a, b, c = self.triplets[t].triplet
            self.triplets[t].is_available = True
            self.triplets[t].equal_bc = b == c
            self.triplets[t].used_count = 0

        # apply initial counts
        for a_idx in self.a_index_set:
            g = self.level_a.group_of_item[a_idx]
            self.groups[g].left_a += 1
            self.groups[g].left_bc -= 1

        # triplets
        # self.triplets: list[TripletInfo] = []

        # for t, (a, b, c) in enumerate(self.level_a.triplets_abc):
        for t in range(T):
            a, b, c = self.triplets[t].triplet

            self.triplets[t].index_of_available = len(self.available_triplet_indices)
            self.available_triplet_indices.append(t)

            self.triplets[t].index_of_available_a = len(
                self.groups[a].available_triplet_indices_a
            )
            self.groups[a].available_triplet_indices_a.append(t)

            self.triplets[t].index_of_available_b = len(
                self.groups[b].available_triplet_indices_bc
            )
            self.groups[b].available_triplet_indices_bc.append(t)

            if self.triplets[t].equal_bc:
                continue

            self.triplets[t].index_of_available_c = len(
                self.groups[c].available_triplet_indices_bc
            )
            self.groups[c].available_triplet_indices_bc.append(t)
        # print(f"groups level b: {self. groups}\n")

    def is_solution(self) -> bool:
        return len(self.chosen_triplet_indices) == len(self.a_index_set)

    def analyze_solution(self):
        already = 0
        for step in self.stack:
            if isinstance(step, self.ApplyTriplet):
                already += 1
                a, b, c = self.triplets[step.triplet_index].triplet
                print(f".App: {a},{b},{c} already={already}")
            elif isinstance(step, self.ExcludeTriplet):
                a, b, c = self.triplets[step.triplet_index].triplet
                # print(f".Exc: {a},{b},{c}")
            elif isinstance(step, self.BranchingStep):
                if step.backtrack_happened:
                    print(
                        f"{step.step_count_start} - {step.step_count_backtrack} | "
                        f"{step.step_count_backtrack - step.step_count_start}"
                    )
                    s = step.options[-1]  # last one was the excluded
                    a, b, c = self.triplets[s.triplet_index].triplet
                    print(f"BExc: {a},{b},{c}")
                else:
                    already += 1
                    s = step.options[0]
                    a, b, c = self.triplets[s.triplet_index].triplet
                    print(f"BApp: {a},{b},{c} already={already}")

    def get_chosen_triplet_indices(self):
        return self.chosen_triplet_indices

    def execute_backtrack(self) -> bool:
        next_event_handling = 0  # next_event_handling

        def set_next_event():
            nonlocal next_event_handling
            next_event_handling += Solver.BACKTRACK_CHECK_TIME_PER_LOOPS
            if next_event_handling > self.stats.max_loops:
                next_event_handling = self.stats.max_loops

        def check_next_event():
            if self.stats.current_loops == next_event_handling:
                if self.stats.current_loops == self.stats.max_loops:
                    raise Solver.ProblemTooBig(
                        f"Timeout: branching loop count: {self.stats.current_loops}"
                    )
            elapsed = Solver.get_current_time() - self.stats.t_solver_start
            if elapsed > Solver.MAX_CASE_SECONDS:
                raise Solver.ProblemTooBig(f"Timeout: computation time: {elapsed} s")
            set_next_event()

        # try:
        while True:
            print(f"current solution: {self.chosen_triplet_indices}")
            if self.is_solution():
                print("### SOLUTION FOUND IN BACKTRACKING PHASE!")
                # addition
                self.analyze_solution()
                return True

            check_next_event()  # check_next_event

            orig_step_count = self.stats.current_step_count
            orig_branching_count = self.stats.current_branching_count
            try:
                self.main_branching_loop()  ##############
                if (
                    self.stats.current_step_count == orig_step_count
                    and self.stats.current_branching_count == orig_branching_count
                ):
                    raise Solver.NoSolution(
                        "No changes added to stack in branching loop."
                    )
            # except Solver.NoSolution:
            except self.BranchImpossible:
                if BACKTRACKING_POLICY == 0:
                    if not self.undo_until_next_branch():  ##############
                        return False
                elif BACKTRACKING_POLICY == 1:
                    return False
                else:
                    raise Solver.NoSolution(
                        "Implementation error: invalid BACKTRACKING_POLICY."
                    )

            self.stats.current_loops += 1
            depth = len(self.a_index_set) - len(self.chosen_triplet_indices)
            steps = self.stats.current_step_count - orig_step_count
            self.stats.loop_states_by_depth[depth] += 1
            self.stats.loop_states_by_step_counts[steps] += 1

            # if self.is_solution():
            #     return True

        # except Solver. ProblemTooBig as e:
        #   raise e

    def add_used_triplet(self, triplet_index: int) -> None:
        # info = self.triplets[triplet_index]
        a, b, c = self.triplets[triplet_index].triplet
        self.triplets[triplet_index].used_count += 1
        self.groups[a].left_a -= 1
        self.groups[b].left_bc -= 1
        self.groups[c].left_bc -= 1

    def remove_used_triplet(self, triplet_index: int) -> None:
        # info = self.triplets[idx]
        a, b, c = self.triplets[triplet_index].triplet
        self.triplets[triplet_index].used_count -= 1
        self.groups[a].left_a += 1
        self.groups[b].left_bc += 1
        self.groups[c].left_bc += 1

    def set_triplet_disabled(self, triplet_index: int):
        t_info = self.triplets[triplet_index]

        if not t_info.is_available:
            raise Solver.NoSolution("Implementation error: Triplet already disabled.")

        t_info.is_available = False

        # Remove from available_triplet_indices
        last = self.available_triplet_indices[-1]
        # idx = t_info.index_of_available
        self.available_triplet_indices[t_info.index_of_available] = last
        self.available_triplet_indices.pop()
        self.triplets[last].index_of_available = t_info.index_of_available

        a, b, c = t_info.triplet

        last = self.groups[a].available_triplet_indices_a[-1]
        self.groups[a].available_triplet_indices_a[t_info.index_of_available_a] = last
        self.groups[a].available_triplet_indices_a.pop()
        self.triplets[last].index_of_available_a = t_info.index_of_available_a

        last = self.groups[b].available_triplet_indices_bc[-1]
        self.groups[b].available_triplet_indices_bc[t_info.index_of_available_b] = last
        self.groups[b].available_triplet_indices_bc.pop()
        if b == self.triplets[last].triplet[1]:
            self.triplets[last].index_of_available_b = t_info.index_of_available_b
        else:
            self.triplets[last].index_of_available_c = t_info.index_of_available_b

        if not t_info.equal_bc:
            last = self.groups[c].available_triplet_indices_bc[-1]
            self.groups[c].available_triplet_indices_bc[
                t_info.index_of_available_c
            ] = last
            self.groups[c].available_triplet_indices_bc.pop()
            if c == self.triplets[last].triplet[1]:
                self.triplets[last].index_of_available_b = t_info.index_of_available_c
            else:
                self.triplets[last].index_of_available_c = t_info.index_of_available_c

        # def remove_index(lst: List, index, triplet_key):
        #     last = lst.pop()
        #     if last != triplet_index:
        #         lst[index] = last
        #         if hasattr(self.triplets[last], triplet_key):
        #             self.triplets[last].index_of_available = index

        # def remove_index(lst: List, index: int, triplet_key: str):
        #     last = lst[-1]
        #     lst[index] = last  # Write before pop
        #     lst.pop()
        #     # if last != triplet_index and hasattr(self.triplets[last], triplet_key):
        #     setattr(self.triplets[last], triplet_key, index)

        # print(f"self.groups[b].available_triplet_indices_bc: {self.groups[b].available_triplet_indices_bc}\n")
        # print(f"t_info: {t_info}\n")
        # remove_index(self.groups[a].available_triplet_indices_a, t_info.index_of_available_a, 'index_of_available_a')
        # remove_index(self.groups[b].available_triplet_indices_bc, t_info.index_of_available_b,
        #             'index_of_available_b' if b == c else 'index_of_available_c')

        # if not t_info.equal_bc:
        #     remove_index(self.groups[c].available_triplet_indices_bc, t_info.index_of_available_c,
        #                 'index_of_available_b' if c == b else 'index_of_available_c')

    def set_triplet_enabled(self, triplet_index: int):
        t_info = self.triplets[triplet_index]

        if t_info.is_available:
            raise Solver.NoSolution("Implementation error: Triplet already enabled.")

        t_info.is_available = True

        # def reinsert(lst: List, index, triplet_key):
        #     if index == len(lst):
        #         lst.append(triplet_index)
        #     else:
        #         other = lst[index]
        #         lst[index] = triplet_index
        #         self.triplets[other][triplet_key] = len(lst)
        #         lst.append(other)

        if t_info.index_of_available == len(self.available_triplet_indices):
            self.available_triplet_indices.append(triplet_index)
        else:
            other = self.available_triplet_indices[t_info.index_of_available]
            self.available_triplet_indices[t_info.index_of_available] = triplet_index
            self.triplets[other].index_of_available = len(
                self.available_triplet_indices
            )
            self.available_triplet_indices.append(other)

        a, b, c = t_info.triplet

        if not t_info.equal_bc:
            if t_info.index_of_available_c == len(
                self.groups[c].available_triplet_indices_bc
            ):
                self.groups[c].available_triplet_indices_bc.append(triplet_index)
            else:
                other = self.groups[c].available_triplet_indices_bc[
                    t_info.index_of_available_c
                ]
                self.groups[c].available_triplet_indices_bc[
                    t_info.index_of_available_c
                ] = triplet_index
                if c == self.triplets[other].triplet[1]:
                    self.triplets[other].index_of_available_b = len(
                        self.groups[c].available_triplet_indices_bc
                    )
                else:
                    self.triplets[other].index_of_available_c = len(
                        self.groups[c].available_triplet_indices_bc
                    )
                self.groups[c].available_triplet_indices_bc.append(other)

        # Handle group b
        if t_info.index_of_available_b == len(
            self.groups[b].available_triplet_indices_bc
        ):
            self.groups[b].available_triplet_indices_bc.append(triplet_index)
        else:
            other = self.groups[b].available_triplet_indices_bc[
                t_info.index_of_available_b
            ]
            self.groups[b].available_triplet_indices_bc[
                t_info.index_of_available_b
            ] = triplet_index
            if b == self.triplets[other].triplet[1]:
                self.triplets[other].index_of_available_b = len(
                    self.groups[b].available_triplet_indices_bc
                )
            else:
                self.triplets[other].index_of_available_c = len(
                    self.groups[b].available_triplet_indices_bc
                )
            self.groups[b].available_triplet_indices_bc.append(other)

        # Handle group a
        if t_info.index_of_available_a == len(
            self.groups[a].available_triplet_indices_a
        ):
            self.groups[a].available_triplet_indices_a.append(triplet_index)
        else:
            other = self.groups[a].available_triplet_indices_a[
                t_info.index_of_available_a
            ]
            self.groups[a].available_triplet_indices_a[
                t_info.index_of_available_a
            ] = triplet_index
            self.triplets[other].index_of_available_a = len(
                self.groups[a].available_triplet_indices_a
            )
            self.groups[a].available_triplet_indices_a.append(other)

        # reinsert(self.groups[a].available_triplet_indices_a, t_info.index_of_available, 'index_of_available_a')
        # reinsert(self.groups[b].available_triplet_indices_bc, t_info.index_of_available_b,
        #         'index_of_available_b' if b == c else 'index_of_available_c')

        # if not t_info.equal_bc:
        #     reinsert(self.groups[c].available_triplet_indices_bc, t_info.index_of_available_c,
        #             'index_of_available_b' if c == b else 'index_of_available_c')

    def get_max_uses_for_triplet_index(self, triplet_index: int) -> int:
        info = self.triplets[triplet_index]
        a, b, c = info.triplet
        left_a = self.groups[a].left_a
        left_bc = (
            self.groups[b].left_bc // 2
            if info.equal_bc
            else min(self.groups[b].left_bc, self.groups[c].left_bc)
        )
        return min(left_a, left_bc)

    def add_step(self, new_step: Step) -> None:
        self.stats.current_step_count += 1
        new_step.level_b = self
        new_step.perform()
        # print(f"WARNING: new step, appending stack : {new_step}")
        self.stack.append(new_step)

    def add_branching(self, options: list[Step]) -> None:
        self.stats.current_branching_count += 1
        for step in options:
            step.level_b = self
        branching_step = LevelB.BranchingStep(deque(options), self)
        branching_step.step_count_start = self.stats.current_step_count
        # branching_step = branching_step.perform()
        branching_step.perform()
        # print(f"WARNING: branching step, appending stack : {branching_step}")
        self.stack.append(branching_step)

    def main_branching_loop(self):
        # Translated from LevelB: :mainBranchingLoop in C++ Ofilecite@turn1file1@turn1file20
        G = len(self.groups)
        while True:
            triplet_retire: List[LevelB.Step] = []
            # compute max uses and retire zeros
            self.take_options_a = [0] * G
            self.take_options_bc = [0] * G
            for triplet_index in list(self.available_triplet_indices):
                max_uses = self.get_max_uses_for_triplet_index(
                    triplet_index
                )  ###############
                if max_uses == 0:
                    step = LevelB.ExcludeTriplet(triplet_index, self)
                    triplet_retire.append(step)  #############
                else:
                    a, b, c = self.triplets[triplet_index].triplet
                    self.take_options_a[a] += max_uses
                    self.take_options_bc[b] += max_uses
                    self.take_options_bc[c] += max_uses

            for step in triplet_retire:
                # if step == None:
                #     print("hiiiiiiiiiiiiii")
                self.add_step(step)

            triplet_retire.clear()

            # branch impossible checks
            # for a in range(G):
            #     if self.take_options_a[a] < self.groups[a].left_a:
            #         raise LevelB. BranchImpossible()
            # for bc in range(G):
            #     if self.take_options_bc[bc] < self.groups[bc].left_bc:
            #         raise LevelB. BranchImpossible()

            # critical applies
            def is_critical() -> bool:
                for a in range(G):
                    if (
                        self.groups[a].left_a
                        and self.take_options_a[a] == self.groups[a].left_a
                    ):
                        return True
                for bc in range(G):
                    if (
                        self.groups[bc].left_bc
                        and self.take_options_bc[bc] == self.groups[bc].left_bc
                    ):
                        return True
                return False

            if not is_critical():
                break

            # print(f"\n\nself.available_triplet_indices: {self.available_triplet_indices}\n")
            # print("hereeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            for triplet_index in list(self.available_triplet_indices):
                a, b, c = self.triplets[triplet_index].triplet
                if (
                    self.take_options_a[a] == self.groups[a].left_a
                    or self.take_options_bc[b] == self.groups[b].left_bc
                    or self.take_options_bc[c] == self.groups[c].left_bc
                ):
                    # print(f"triplet_index: {triplet_index}")
                    max_uses = self.get_max_uses_for_triplet_index(triplet_index)
                    for _ in range(max_uses):
                        self.add_step(LevelB.ApplyTriplet(triplet_index, self))
                    triplet_retire.append(LevelB.ExcludeTriplet(triplet_index, self))

            for step in triplet_retire:
                self.add_step(step)
            triplet_retire.clear()

        # choose best group ratio
        best_group_which = 0
        best_group_index = 0
        best_ratio = (0, 0)
        print(self.groups)
        for a in range(G):
            if not self.groups[a].left_a:
                continue

            if best_group_which == 0 or (
                (best_ratio[0] * self.take_options_a[a])
                < (self.groups[a].left_a * best_ratio[1])
            ):
                best_group_which, best_group_index = 1, a
                best_ratio = (self.groups[a].left_a, self.take_options_a[a])
        for bc in range(G):
            if not self.groups[bc].left_bc:
                continue
            if best_group_which == 0 or (
                (best_ratio[0] * self.take_options_bc[bc])
                < (self.groups[bc].left_bc * best_ratio[1])
            ):
                best_group_which, best_group_index = 2, bc
                best_ratio = (self.groups[bc].left_bc, self.take_options_bc[bc])

        if best_group_which == 0:
            return

        # addition
        ##########
        triplet_candidate_indices = (
            self.groups[best_group_index].available_triplet_indices_a
            if best_group_which == 1
            else self.groups[best_group_index].available_triplet_indices_bc
        )  #############

        # addition
        ##########
        # pick best triplet
        best_mu = 0
        best_ti = None
        for ti in triplet_candidate_indices:
            mu = self.get_max_uses_for_triplet_index(ti)
            if (
                (LEVELB_BRANCHING_TIE_ORDER == 0 and mu > best_mu)
                or (mu == best_mu and ti < best_mu)
            ) or (LEVELB_BRANCHING_TIE_ORDER == 1 and (mu > best_mu)):
                best_mu, best_ti = mu, ti

        if best_mu == 0:
            raise self.BranchImpossible()

        # branching apply then exclude
        steps = [
            LevelB.ApplyTriplet(best_ti, self),
            LevelB.ExcludeTriplet(best_ti, self),
        ]
        self.stats.winning_branches.append(
            Solver.BranchingChoiceStats(
                True, best_group_which == 1, best_ratio[0], best_ratio[1], best_mu
            )
        )
        print(f"best_ti: {best_ti}")
        self.add_branching(steps)

    def undo_until_next_branch(self) -> bool:
        self.stats.current_backtrack_events += 1

        while self.stack:
            # print(f"self.stack: {self.stack}\n")
            # for i, item in enumerate(self.stack):
            #     print(f"{i}: {type(item).__name__} -> {item}")

            last_step = self.stack[-1]
            last_step.undo()

            if isinstance(last_step, LevelB.BranchingStep):  # not sure
                if last_step.options:
                    # Optional debug: backtrack_weight = self.stats.current_step_count - last_step.step_count_start
                    # print(f"{backtrack_weight}\t{self.stats.current_backtrack_events}")

                    last_step.perform()
                    failing_branch = self.stats.winning_branches[-1]
                    failing_branch.apply = not failing_branch.apply
                    return True
                self.stats.winning_branches.pop()
            # not sure

            self.stack.pop()

        return False

    def get_stats(self):
        return self.stats

    def get_chosen_triplets(self) -> List[Tuple[int, int, int]]:
        # print(f"self.chosen_triplet_indices: {self.chosen_triplet_indices}")
        # print(f"triplets: {self.triplets}")
        return [self.triplets[i].triplet for i in self.chosen_triplet_indices]


class LevelA:
    def __init__(self, problem: Problem):
        self.orig_problem = problem
        self.answer = Solver.Answer()
        self.t_solver_start = Solver.get_current_time()
        self.orig_weights = problem.get_weights()
        self.desired_sum = sum(self.orig_weights) // (len(self.orig_weights) // 3)
        self.definitely_a_indices: List[int] = []
        self.groups: List[deque[int]] = []
        self.weight_of_group: List[WeightType] = []
        self.group_cardinality: List[int] = []
        self.group_of_item: List[int] = []
        self.weight_map_desc: Dict[WeightType, List[int]] = defaultdict(list)
        self.triplets_abc_theoretical: List[Tuple[int, int, int]] = []
        self.triplets_abc: List[Tuple[int, int, int]] = []
        self.preprocess_triplets: List[Tuple[int, int, int]] = []
        # self.backtrack_chosen_triplets: List[Tuple [int, int, int]] = []
        self.mc_maybe_a: MultiCombination = MultiCombination()

        # addition
        self.algorithm_chosen_triplets: List[Tuple[int, int, int]]
        self.improvement_chosen_triplets: List[Tuple[int, int, int]]

    def execute_algorithm(self):
        self.calculate_basic_data()
        self.calculate_equal_groups()
        self.calculate_triplet_abc()
        self.preprocess()
        self.calculate_possibles()
        self.perform_backtrack_level()
        self.finalize_solution()
        self.post_check()

    def set_message(self, msg: str):
        self.answer.error_message = msg

    def get_answer(self):
        return self.answer

    def calculate_basic_data(self):
        """
        Sort original weights descending and compute desired triplet sum.
        desired_sum = (sum(weights)) / (N/3)
        """
        self.orig_weights.sort(reverse=True)

    def calculate_equal_groups(self):
        for i, w in enumerate(self.orig_weights):
            self.weight_map_desc[w].append(i)

        # print(f"weight_map_desc: {self.weight_map_desc}\n")

        self.groups = []
        self.weight_of_group = []
        self.group_of_item = [0] * len(self.orig_weights)
        self.group_cardinality = []

        for group_index, (weight, indices) in enumerate(self.weight_map_desc.items()):
            self.weight_of_group.append(weight)
            self.groups.append(deque(indices))
            for idx in indices:
                self.group_of_item[idx] = group_index
            self.group_cardinality.append(len(indices))
            print(f"Group {group_index}: {weight}")
        # print(f"groups: {self. groups}\n")
        # print(f"weight_of_group: {self.weight_of_group}\n")
        # print(f"group_of_item: {self.group_of_item}\n")
        # print(f"group_cardinality: {self.group_cardinality}\n")

    def calculate_triplet_abc(self):
        # group_weights = self.weight_of_group
        group_weights = [weight for weight, _ in self.weight_map_desc.items()]
        G = len(self.groups)
        for gia in range(G):
            gib = gia
            gic = G - 1
            while gib <= gic:
                total = group_weights[gia] + group_weights[gib] + group_weights[gic]
                if total > self.desired_sum:
                    gib += 1
                elif total < self.desired_sum:
                    gic -= 1
                else:
                    self.triplets_abc_theoretical.append((gia, gib, gic))
                    gib += 1
                    gic -= 1
        # print(f"triplets_abc_theoretical: {self.triplets_abc_theoretical}\n")

    def get_max_triplet_usage(
        self, t: Tuple[int, int, int], cardinalities: List[int] = None
    ):
        if cardinalities is None:
            cardinalities = self.group_cardinality
        a, b, c = t
        if a == b:
            if b == c:
                return cardinalities[a] // 2
            else:
                return min(cardinalities[a] // 2, cardinalities[c])
        else:
            if b == c:
                return min(cardinalities[a], cardinalities[b] // 2)
            else:
                return min(cardinalities[a], cardinalities[b], cardinalities[c])

    def preprocess(self):
        G = len(self.groups)
        occurrences = [set() for _ in range(G)]
        triplets_possible = set()
        for t in self.triplets_abc_theoretical:
            if self.get_max_triplet_usage(t) > 0:
                triplets_possible.add(t)
                for g in t:
                    occurrences[g].add(t)
        # print(f"triplets_possible: {triplets_possible}\n")
        # print(f"occurrences: {occurrences}\n")

        while True:
            # singleton_choice_triplets = {
            #     next(iter(occurrences[g]))
            #     for g in range(G)
            #     if self.group_cardinality[g] > 0 and len(occurrences[g]) == 1
            # }
            singleton_choice_triplets = set()
            for group in range(G):
                if self.group_cardinality[group] == 0:
                    continue
                if len(occurrences[group]) == 0:
                    raise Solver.NoSolution(
                        f"Weight cannot be part of triplet: {self.weight_of_group[group]} for desired sum {self.desired_sum}"
                    )
                elif len(occurrences[group]) == 1:
                    singleton_choice_triplets.add(next(iter(occurrences[group])))

            # print(singleton_choice_triplets)
            if not singleton_choice_triplets:
                break
            triplets_to_erase = set()
            for t in singleton_choice_triplets:
                # print(f"appending songle triplet: {t}")

                self.preprocess_triplets.append(t)
                for g in t:
                    self.group_cardinality[g] -= 1

                for g in t:
                    for tt in list(occurrences[g]):
                        if self.get_max_triplet_usage(tt) == 0:
                            triplets_to_erase.add(tt)

            for t in triplets_to_erase:
                for g in t:
                    occurrences[g].discard(t)
                triplets_possible.discard(t)
        self.triplets_abc = list(triplets_possible)
        # print(f"triplets_abc: {self.triplets_abc}\n")
        self.answer.preprocess_triplet_count = len(self.preprocess_triplets)

    def calculate_possibles(self):
        G = len(self.groups)
        # print(f" groups length: {G}")
        max_a = [0] * G
        max_bc = [0] * G
        for t in self.triplets_abc:
            a, b, c = t
            max_uses = self.get_max_triplet_usage(t)
            max_a[a] += max_uses
            max_bc[b] += max_uses
            max_bc[c] += max_uses
        definitely_a_counts = defaultdict(int)
        maybe_a_counts = defaultdict(int)
        definitely_a_cardinality = 0
        maybe_a_cardinality = 0

        for g in range(G):
            if self.group_cardinality[g] == 0:
                continue
            definitely_a = max(self.group_cardinality[g] - max_bc[g], 0)
            maybe_a = min(max_a[g], self.group_cardinality[g]) - definitely_a
            if definitely_a < 0 or maybe_a < 0:
                raise Solver.NoSolution(
                    "Implementation error: negative definitely_a or maybe_a"
                )
            if definitely_a > 0:
                definitely_a_counts[g] = definitely_a
                definitely_a_cardinality += definitely_a
            if maybe_a > 0:
                maybe_a_counts[g] = maybe_a
                maybe_a_cardinality += maybe_a

        self.answer.definitely_a_cardinality == definitely_a_cardinality
        self.answer.maybe_a_cardinality == maybe_a_cardinality

        # print(f"definitely_a_counts: {definitely_a_counts}\n")
        # print(f"definitely_a_cardinality: {definitely_a_cardinality}\n")
        # print(f"maybe_a_counts: {maybe_a_counts}\n")
        # print(f"maybe_a_cardinality: {maybe_a_cardinality}\n")

        T = len(self.orig_weights) // 3 - len(self.preprocess_triplets)
        # print(f" processed triplets length: {len(self.preprocess_triplets)}\n")
        # print(f"T: {T}\n")
        if definitely_a_cardinality + maybe_a_cardinality < T:
            raise Solver.NoSolution("Too few A-role weights available.")
        if definitely_a_cardinality > T:
            raise Solver.NoSolution("Too many A-role weights required.")

        maybe_a_indices = []
        maybe_a_weights = []
        for g in range(G):
            # print(f"g: {g}")
            # def_a_left= definitely_a_counts.get(g, 0)
            def_a_left = definitely_a_counts[g]
            # print(f"def_a_left: {def_a_left}")
            # maybe_a_left = maybe_a_counts.get(g, 0)
            maybe_a_left = maybe_a_counts[g]
            # print(f"maybe_a_left: {maybe_a_left}")
            for idx in self.groups[g]:
                if def_a_left:
                    self.definitely_a_indices.append(idx)
                    def_a_left -= 1
                elif maybe_a_left:
                    maybe_a_indices.append(idx)
                    maybe_a_weights.append(self.weight_of_group[g])
                    maybe_a_left -= 1
                else:
                    break
            if def_a_left or maybe_a_left:
                raise Solver.NoSolution(
                    "Implementation error: not all definitely_a or maybe_a used"
                )

        self.mc_maybe_a.init(maybe_a_indices, maybe_a_weights)

        # print(f"definitely_a_indices: {self.definitely_a_indices}\n")
        # print(f"maybe_a_indices: {maybe_a_indices}\n")
        # print(f"maybe_a_weights: {maybe_a_weights}\n")

        maybe_a_choose = T - definitely_a_cardinality
        # print(f"maybe choice number: {maybe_a_choose}\n")

        self.answer.maybe_a_choose = maybe_a_choose
        # self.answer.definitely_a_cardinality = definitely_a_cardinality
        # self.answer.maybe_a_cardinality = maybe_a_cardinality
        self.answer.a_index_set_case_count = self.mc_maybe_a.get_choice_count(
            maybe_a_choose
        )
        # addition
        self.T = len(self.triplets_abc)
        self.G = len(self.groups)
        # print(f"a_index_set_case_count: {self.answer.a_index_set_case_count}\n")

    def perform_backtrack_level(self):
        # from levelb import LevelB # deferred import to avoid circular dependency
        # addition
        for bi in range(self.answer.a_index_set_case_count):
            # for bi_int in range(int(self.answer.a_index_set_case_count.to_decimal())):
            # bi = BigIndex (bi_int)
            case_index = bi
            a_index_set = list(self.definitely_a_indices)

            # # print
            # temp_list = []
            # for i in a_index_set:
            #     temp_list.append(self.orig_weights[i])
            # print(f"must be a: (temp_list)")

            a_index_set += self.mc_maybe_a.get_single_choice(
                self.answer.maybe_a_choose, case_index
            )
            A = len(a_index_set)  # number of triplets to be formed

            # # print
            # for i in self.mc_maybe_a.get_single_choice(self.answer.maybe_a_choose, bi):
            #     print(f"assumed as a: {self.orig_weights[i]}\n")

            level_backtrack = LevelB(a_index_set, self)
            stats = level_backtrack.get_stats()

            self.answer.total_step_count += stats.current_step_count
            self.answer.total_branching_count += stats.current_branching_count
            self.answer.total_backtrack_events += stats.current_backtrack_events
            self.answer.total_loops += stats.current_loops

            for depth, count in stats.loop_states_by_depth.items():
                self.answer.total_loop_states_by_depth[depth] = (
                    self.answer.total_loop_states_by_depth.get(depth, 0) + count
                )
            for stepcount, count in stats.loop_states_by_step_counts.items():
                self.answer.total_loop_states_by_step_counts[stepcount] = (
                    self.answer.total_loop_states_by_step_counts.get(stepcount, 0)
                    + count
                )

            if stats.is_backtrack_successful:
                self.answer.success = True
                self.answer.a_cases_investigated = case_index + 1
                self.answer.winning_branches = stats.winning_branches
                self.algorithm_chosen_triplets = level_backtrack.get_chosen_triplets()
                return

            # if not USE_IMPROVEMENT_HEURISTIC:
            #     continue

            # print("USE_IMPROVEMENT_HEURISTIC")

            # self.answer.a_cases_investigated = case_index + 1
            # self.answer.winning_branches = stats.winning_branches

            # level_improvement = LevelC(
            #     level_backtrack.get_chosen_triplet_indices(), self
            # )
            # improvement_final_success = False

            # while True:
            #     if level_improvement.getFinalTripletCount() == A:
            #         self.answer.success = True
            #         self.algorithm_chosen_triplets = (
            #             level_improvement.getFinalTriplets()
            #         )
            #         improvement_final_success = True
            #         break
            #     success, steps = level_improvement.perform(2, 100000)
            #     if not success:
            #         break

            # stats = level_improvement.getStats()
            # self.answer.improvement_passes = stats.passes
            # self.answer.improvement_distance = stats.distance
            # self.answer.improvement_node_count = stats.node_count
            # self.answer.improvement_saved_count = stats.saved_count
            # self.answer.improvement_skip1_count = stats.skip1_count
            # self.answer.improvement_skip2_count = stats.skip2_count

            # if not improvement_final_success:
            #     raise Solver.NoSolution("No solution found - reported at C level.")
            # return

        raise Solver.NoSolution("No solution found - reported at A level.")

        # # raise Solver.NoSolution("No solution found by backtrack.")
        # raise Solver.NoSolution("No solution found - reported at A level.")

    def finalize_solution(self):
        if not self.answer.success:
            return

        # print(f"preprocess_triplets: {self.preprocess_triplets}")
        # print(f"algorithm_chosen_triplets: {self.algorithm_chosen_triplets}")
        # Merge all triplets
        final_triplets = []
        final_triplets.extend(self.preprocess_triplets)
        final_triplets.extend(self.algorithm_chosen_triplets)

        # Make a copy of the groups
        groups_copy = [list(group) for group in self.groups]

        def get_next_index(group_index):
            if group_index >= len(groups_copy):
                raise Solver.NoSolution("Implementation error: group_index too large.")
            current_group = groups_copy[group_index]
            if not current_group:
                raise Solver.NoSolution(
                    "Implementation error: current group already empty."
                )
            next_index = current_group.pop(0)
            return next_index

        print(f"final_triplets: {final_triplets}")
        # Construct the solution
        solution = Solution()
        for a, b, c in final_triplets:
            a_index = get_next_index(a)
            b_index = get_next_index(b)
            c_index = get_next_index(c)
            weight_a = self.orig_weights[a_index]
            weight_b = self.orig_weights[b_index]
            weight_c = self.orig_weights[c_index]
            solution.add(Triplet(weight_a, weight_b, weight_c))

        self.answer.solution = solution

    def post_check(self):
        if self.answer.success:
            try:
                SolutionChecker.check(self.orig_problem, self.answer.solution)
            except Exception as e:
                self.answer.success = False
                self.answer.error_message += f"SolutionCheck: {str(e)}"


# from clock import Clock

# path = f"prtpy/packing/triplet_algo/Falkenauer_T/Falkenauer_t60_01.txt"
# problem = Problem()
# problem.read_benchmark_format(path)

# t_start = Clock.elapsed()
# # answer = Solver.solve(problem)

# # level_state= LevelA(problem)
# # try:
# #     level_state.execute_algorithm()
# # except Solver.Error as e:
# #     level_state.set_message(str(e))
# # answer = level_state.get_answer()
# answer = Solver.solve(problem)

# t_end = Clock.elapsed()

# elapsed = t_end - t_start

# print(f" elapsed: {elapsed}\n")
# # solution = answer.solution.copy
# # print (f" solution: {answer.solution}")
# answer.solution.sort()
# for t in answer.solution.get_triplets():
#     print(t)

# # from typing import List, Tuple, Dict, Optional
# # from collections import deque
# # from solver import Solver
# # from triplet import Triplet
