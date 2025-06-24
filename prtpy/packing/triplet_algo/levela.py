from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
from .problem import Problem
from .triplet import Triplet
from .solution import Solution
from .solution_checker import SolutionChecker
from .multi_combination import MultiCombination
import logging
from .models import SolverData, TripletSearchContext
from .levelb import LevelB

logger = logging.getLogger("trialgo.triplet_algo")

WeightType = int


class LevelA:
    def __init__(self, problem: Problem):
        self.orig_problem = problem
        self.answer = SolverData.Answer()
        self.t_solver_start = SolverData.get_current_time()
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
        
        # self.tsc = TripletSearchContext()

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
                    raise SolverData.NoSolution(
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
                raise SolverData.NoSolution(
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
            raise SolverData.NoSolution("Too few A-role weights available.")
        if definitely_a_cardinality > T:
            raise SolverData.NoSolution("Too many A-role weights required.")

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
                raise SolverData.NoSolution(
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
            tsc = TripletSearchContext(self.answer.total_loops, self.t_solver_start, self.group_cardinality, self.groups , self.triplets_abc, self.group_of_item)

            level_backtrack = LevelB(a_index_set, tsc)
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
            #     raise SolverData.NoSolution("No solution found - reported at C level.")
            # return

        raise SolverData.NoSolution("No solution found - reported at A level.")

        # # raise SolverData.NoSolution("No solution found by backtrack.")
        # raise SolverData.NoSolution("No solution found - reported at A level.")

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
                raise SolverData.NoSolution("Implementation error: group_index too large.")
            current_group = groups_copy[group_index]
            if not current_group:
                raise SolverData.NoSolution(
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
# # except SolverData.Error as e:
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
