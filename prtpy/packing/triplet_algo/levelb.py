from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
from .base import (
    LEVELB_BRANCHING_TIE_ORDER,
    BACKTRACKING_POLICY,
    USE_IMPROVEMENT_HEURISTIC,
)
import logging
from .models import SolverData, TripletInfo, GroupInfo, TripletSearchContext
from .backtrack_utils import BranchImpossible, Stats, Step, TripletBaseStep, ApplyTriplet, ExcludeTriplet, BranchingStep

logger = logging.getLogger("trialgo.triplet_algo")


# level b
WeightType = int
from dataclasses import dataclass, field


class LevelB:
    def __init__(self, a_index_set: List[int], tsc: TripletSearchContext):
        # from levela import LevelA # avoid circular import at module top level
        # self.level_a: LevelA = level_a
        self.tsc = tsc
        self.a_index_set = a_index_set
        self.stats = Stats(
            SolverData.MAX_LOOPS - self.tsc.total_loops, self.tsc.t_solver_start
        )
        # self.triplets = level_a.triplets_abc
        self.triplets: list[TripletInfo] = []
        self.triplet_states: List[Dict[str, int]] = []
        self.chosen_triplet_indices: List[int] = []
        # self.available_triplet_indices: List[int] = list (range(len(self.triplets)))
        self.available_triplet_indices: list[int] = []

        # local stacks
        self.stack: deque[Step] = deque()

        self.prepare()
        self.stats.is_backtrack_successful = self.execute_backtrack()

    def prepare(self):
        G = len(self.tsc.groups)
        # print(f" garoups level a: {self.level_a.groups}\n")

        # groups
        # G = len(self.level_a.groups)
        self.groups: list[GroupInfo] = [
            GroupInfo(left_a=0, left_bc=self.tsc.group_cardinality[g])
            for g in range(G)
        ]
        self.take_options_a = [0] * G
        self.take_options_bc = [0] * G

        T = len(self.tsc.triplets_abc)
        self.triplets: list[TripletInfo] = [
            TripletInfo(triplet=(0, 0, 0)) for _ in range(T)
        ]

        for t in range(T):
            self.triplets[t].triplet = self.tsc.triplets_abc[t]
            a, b, c = self.triplets[t].triplet
            self.triplets[t].is_available = True
            self.triplets[t].equal_bc = b == c
            self.triplets[t].used_count = 0

        # apply initial counts
        for a_idx in self.a_index_set:
            g = self.tsc.group_of_item[a_idx]
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
            if isinstance(step, ApplyTriplet):
                already += 1
                a, b, c = self.triplets[step.triplet_index].triplet
                print(f".App: {a},{b},{c} already={already}")
            elif isinstance(step, ExcludeTriplet):
                a, b, c = self.triplets[step.triplet_index].triplet
                # print(f".Exc: {a},{b},{c}")
            elif isinstance(step, BranchingStep):
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
            next_event_handling += SolverData.BACKTRACK_CHECK_TIME_PER_LOOPS
            if next_event_handling > self.stats.max_loops:
                next_event_handling = self.stats.max_loops

        def check_next_event():
            if self.stats.current_loops == next_event_handling:
                if self.stats.current_loops == self.stats.max_loops:
                    raise SolverData.ProblemTooBig(
                        f"Timeout: branching loop count: {self.stats.current_loops}"
                    )
            elapsed = SolverData.get_current_time() - self.stats.t_solver_start
            if elapsed > SolverData.MAX_CASE_SECONDS:
                raise SolverData.ProblemTooBig(f"Timeout: computation time: {elapsed} s")
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
                    raise SolverData.NoSolution(
                        "No changes added to stack in branching loop."
                    )
            # except Solver.NoSolution:
            except BranchImpossible:
                if BACKTRACKING_POLICY == 0:
                    if not self.undo_until_next_branch():  ##############
                        return False
                elif BACKTRACKING_POLICY == 1:
                    return False
                else:
                    raise SolverData.NoSolution(
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
            raise SolverData.NoSolution("Implementation error: Triplet already disabled.")

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
            raise SolverData.NoSolution("Implementation error: Triplet already enabled.")

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
        branching_step = BranchingStep(deque(options), self)
        branching_step.step_count_start = self.stats.current_step_count
        # branching_step = branching_step.perform()
        branching_step.perform()
        # print(f"WARNING: branching step, appending stack : {branching_step}")
        self.stack.append(branching_step)

    def main_branching_loop(self):
        # Translated from LevelB: :mainBranchingLoop in C++ Ofilecite@turn1file1@turn1file20
        G = len(self.groups)
        while True:
            triplet_retire: List[Step] = []
            # compute max uses and retire zeros
            self.take_options_a = [0] * G
            self.take_options_bc = [0] * G
            for triplet_index in list(self.available_triplet_indices):
                max_uses = self.get_max_uses_for_triplet_index(
                    triplet_index
                )  ###############
                if max_uses == 0:
                    step = ExcludeTriplet(triplet_index, self)
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
                        self.add_step(ApplyTriplet(triplet_index, self))
                    triplet_retire.append(ExcludeTriplet(triplet_index, self))

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
            raise BranchImpossible()

        # branching apply then exclude
        steps = [
            ApplyTriplet(best_ti, self),
            ExcludeTriplet(best_ti, self),
        ]
        self.stats.winning_branches.append(
            SolverData.BranchingChoiceStats(
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

            if isinstance(last_step, BranchingStep):  # not sure
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
