from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
from .problem import Problem
from .triplet import Triplet
from .solution import Solution
from .solution_checker import SolutionChecker
from .multi_combination import MultiCombination
import logging
from .models import SolverData, TripletSearchContext
from .triplet_backtracker import TripletBacktracker
from .base import USE_IMPROVEMENT_HEURISTIC
from .triplet_local_search import TripletLocalSearch

logger = logging.getLogger("trialgo.triplet_algo")

WeightType = int


class TripletPlanner:
    def __init__(self, problem: Problem):
        logger.debug("Initializing TripletPlanner")
        self.orig_problem = problem
        self.answer = SolverData.Answer()
        self.t_solver_start = SolverData.get_current_time()
        self.orig_weights = problem.get_weights()
        self.desired_sum = sum(self.orig_weights) // (len(self.orig_weights) // 3)
        logger.debug(f"Desired sum per triplet: {self.desired_sum}")

        self.definitely_a_indices: List[int] = []
        self.groups: List[deque[int]] = []
        self.weight_of_group: List[WeightType] = []
        self.group_cardinality: List[int] = []
        self.group_of_item: List[int] = []
        self.weight_map_desc: Dict[WeightType, List[int]] = defaultdict(list)
        self.triplets_abc_theoretical: List[Tuple[int, int, int]] = []
        self.triplets_abc: List[Tuple[int, int, int]] = []
        self.preprocess_triplets: List[Tuple[int, int, int]] = []
        self.mc_maybe_a: MultiCombination = MultiCombination()

        # addition
        self.algorithm_chosen_triplets: List[Tuple[int, int, int]] = []
        self.improvement_chosen_triplets: List[Tuple[int, int, int]] = []

    def execute_algorithm(self):
        logger.debug("Starting execute_algorithm")
        self.calculate_basic_data()
        self.calculate_equal_groups()
        self.calculate_triplet_abc()
        self.preprocess()
        self.calculate_possibles()
        self.perform_backtrack_level()
        self.finalize_solution()
        self.post_check()
        logger.debug("Finished execute_algorithm")

    def set_message(self, msg: str):
        logger.debug(f"Setting error message: {msg}")
        self.answer.error_message = msg

    def get_answer(self):
        return self.answer

    def calculate_basic_data(self):
        """
        Sort original weights descending and compute desired triplet sum.
        desired_sum = (sum(weights)) / (N/3)
        """
        logger.debug("Calculating basic data: sorting weights")
        self.orig_weights.sort(reverse=True)
        logger.debug(f"Sorted original weights: {self.orig_weights}")

    def calculate_equal_groups(self):
        logger.debug("Calculating equal groups")
        for i, w in enumerate(self.orig_weights):
            self.weight_map_desc[w].append(i)
        logger.debug(f"Weight map (descending): {dict(self.weight_map_desc)}")

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
            logger.debug(f"Group {group_index}: weight={weight}, count={len(indices)}")

    def calculate_triplet_abc(self):
        logger.debug("Calculating theoretical triplets (abc)")
        group_weights = [weight for weight, _ in self.weight_map_desc.items()]
        G = len(self.groups)
        logger.debug(f"Number of groups: {G}")

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
                    logger.debug(f"Found theoretical triplet: ({gia}, {gib}, {gic})")
                    gib += 1
                    gic -= 1

        logger.debug(f"Total theoretical triplets found: {len(self.triplets_abc_theoretical)}")

    def get_max_triplet_usage(
        self, t: Tuple[int, int, int], cardinalities: List[int] = None
    ):
        if cardinalities is None:
            cardinalities = self.group_cardinality
        a, b, c = t
        if a == b:
            if b == c:
                usage = cardinalities[a] // 2
            else:
                usage = min(cardinalities[a] // 2, cardinalities[c])
        else:
            if b == c:
                usage = min(cardinalities[a], cardinalities[b] // 2)
            else:
                usage = min(cardinalities[a], cardinalities[b], cardinalities[c])
        logger.debug(f"Max usage for triplet {t}: {usage}")
        return usage

    def preprocess(self):
        logger.debug("Starting preprocess")
        G = len(self.groups)
        occurrences = [set() for _ in range(G)]
        triplets_possible = set()
        for t in self.triplets_abc_theoretical:
            max_usage = self.get_max_triplet_usage(t)
            if max_usage > 0:
                triplets_possible.add(t)
                for g in t:
                    occurrences[g].add(t)
        logger.debug(f"Triplets possible after filtering: {len(triplets_possible)}")

        while True:
            singleton_choice_triplets = set()
            for group in range(G):
                if self.group_cardinality[group] == 0:
                    continue
                if len(occurrences[group]) == 0:
                    msg = (f"Weight cannot be part of triplet: "
                           f"{self.weight_of_group[group]} for desired sum {self.desired_sum}")
                    logger.error(msg)
                    raise SolverData.NoSolution(msg)
                elif len(occurrences[group]) == 1:
                    singleton_choice_triplets.add(next(iter(occurrences[group])))

            if not singleton_choice_triplets:
                logger.debug("No singleton choice triplets found, exiting preprocess loop")
                break

            triplets_to_erase = set()
            for t in singleton_choice_triplets:
                logger.debug(f"Appending singleton choice triplet: {t}")
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
        logger.debug(f"Triplets after preprocess: {len(self.triplets_abc)}")
        self.answer.preprocess_triplet_count = len(self.preprocess_triplets)

    def calculate_possibles(self):
        logger.debug("Calculating possibles")
        G = len(self.groups)
        max_a = [0] * G
        max_bc = [0] * G
        for t in self.triplets_abc:
            a, b, c = t
            max_uses = self.get_max_triplet_usage(t)
            max_a[a] += max_uses
            max_bc[b] += max_uses
            max_bc[c] += max_uses
        logger.debug(f"max_a per group: {max_a}")
        logger.debug(f"max_bc per group: {max_bc}")

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
                msg = "Implementation error: negative definitely_a or maybe_a"
                logger.error(msg)
                raise SolverData.NoSolution(msg)
            if definitely_a > 0:
                definitely_a_counts[g] = definitely_a
                definitely_a_cardinality += definitely_a
            if maybe_a > 0:
                maybe_a_counts[g] = maybe_a
                maybe_a_cardinality += maybe_a

        logger.debug(f"Definitely A counts: {dict(definitely_a_counts)}")
        logger.debug(f"Definitely A cardinality: {definitely_a_cardinality}")
        logger.debug(f"Maybe A counts: {dict(maybe_a_counts)}")
        logger.debug(f"Maybe A cardinality: {maybe_a_cardinality}")

        self.answer.definitely_a_cardinality = definitely_a_cardinality
        self.answer.maybe_a_cardinality = maybe_a_cardinality

        T = len(self.orig_weights) // 3 - len(self.preprocess_triplets)
        logger.debug(f"Triplets left to form (T): {T}")

        if definitely_a_cardinality + maybe_a_cardinality < T:
            msg = "Too few A-role weights available."
            logger.error(msg)
            raise SolverData.NoSolution(msg)
        if definitely_a_cardinality > T:
            msg = "Too many A-role weights required."
            logger.error(msg)
            raise SolverData.NoSolution(msg)

        maybe_a_indices = []
        maybe_a_weights = []
        for g in range(G):
            def_a_left = definitely_a_counts.get(g, 0)
            maybe_a_left = maybe_a_counts.get(g, 0)
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
                msg = "Implementation error: not all definitely_a or maybe_a used"
                logger.error(msg)
                raise SolverData.NoSolution(msg)

        logger.debug(f"Definitely A indices: {self.definitely_a_indices}")
        logger.debug(f"Maybe A indices: {maybe_a_indices}")
        logger.debug(f"Maybe A weights: {maybe_a_weights}")

        self.mc_maybe_a.init(maybe_a_indices, maybe_a_weights)

        maybe_a_choose = T - definitely_a_cardinality
        logger.debug(f"Maybe A choose count: {maybe_a_choose}")

        self.answer.maybe_a_choose = maybe_a_choose
        self.answer.a_index_set_case_count = self.mc_maybe_a.get_choice_count(maybe_a_choose)
        logger.debug(f"A index set case count: {self.answer.a_index_set_case_count}")

        # addition
        self.T = len(self.triplets_abc)
        self.G = len(self.groups)
        logger.debug(f"T (triplets count): {self.T}, G (groups count): {self.G}")

    def perform_backtrack_level(self):
        logger.debug("Starting perform_backtrack_level")
        for bi in range(self.answer.a_index_set_case_count):
            case_index = bi
            a_index_set = list(self.definitely_a_indices)

            logger.debug(f"Trying case index: {case_index}")
            logger.debug(f"Definitely A indices: {a_index_set}")

            # Add choice of maybe-A
            maybe_a_indices = self.mc_maybe_a.get_single_choice(self.answer.maybe_a_choose, case_index)
            logger.debug(f"Maybe A indices chosen: {maybe_a_indices}")
            a_index_set += maybe_a_indices
            A = len(a_index_set)  # number of triplets to be formed

            tsc = TripletSearchContext(
                self.answer.total_loops,
                self.t_solver_start,
                self.group_cardinality,
                self.groups,
                self.triplets_abc,
                self.group_of_item,
            )

            level_backtrack = TripletBacktracker(a_index_set, tsc)
            stats = level_backtrack.get_stats()
            logger.debug(f"Backtrack stats: {stats}")

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
                    self.answer.total_loop_states_by_step_counts.get(stepcount, 0) + count
                )

            if stats.is_backtrack_successful:
                logger.debug("Backtrack successful")
                self.answer.success = True
                self.answer.a_cases_investigated = case_index + 1
                self.answer.winning_branches = stats.winning_branches
                self.algorithm_chosen_triplets = level_backtrack.get_chosen_triplets()
                return

            logger.debug("Backtrack failed, trying improvement heuristic" if USE_IMPROVEMENT_HEURISTIC else "Skipping heuristic")

            if not USE_IMPROVEMENT_HEURISTIC:
                continue

            logger.debug("Running improvement heuristic")
            self.answer.a_cases_investigated = case_index + 1
            self.answer.winning_branches = stats.winning_branches

            level_improvement = TripletLocalSearch(level_backtrack.get_chosen_triplet_indices(), self.triplets_abc, self.group_cardinality)
            improvement_final_success = False

            while True:
                if level_improvement.get_final_triplet_count() == A:
                    logger.debug("Improvement successful, full solution found")
                    self.answer.success = True
                    self.algorithm_chosen_triplets = level_improvement.get_final_triplets()
                    improvement_final_success = True
                    break

                success, steps = level_improvement.perform(2, 100000)
                logger.debug(f"Improvement pass: success={success}, steps={steps}")
                if not success:
                    logger.debug("Improvement failed to proceed further")
                    break

            stats = level_improvement.get_stats()
            logger.debug(f"Improvement stats: {stats}")

            self.answer.improvement_passes = stats.passes
            self.answer.improvement_distance = stats.distance
            self.answer.improvement_node_count = stats.node_count
            self.answer.improvement_saved_count = stats.saved_count
            self.answer.improvement_skip1_count = stats.skip1_count
            self.answer.improvement_skip2_count = stats.skip2_count

            if not improvement_final_success:
                logger.error("No solution found during improvement phase")
                raise SolverData.NoSolution("No solution found - reported at C level.")
            return

        logger.error("No solution found during backtrack phase")
        raise SolverData.NoSolution("No solution found - reported at A level.")

    def finalize_solution(self):
        if not self.answer.success:
            logger.debug("Skipping finalize_solution due to failure")
            return

        logger.debug("Finalizing solution")
        final_triplets = []
        final_triplets.extend(self.preprocess_triplets)
        final_triplets.extend(self.algorithm_chosen_triplets)
        logger.debug(f"Final triplets (count {len(final_triplets)}): {final_triplets}")

        groups_copy = [list(group) for group in self.groups]

        def get_next_index(group_index):
            if group_index >= len(groups_copy):
                raise SolverData.NoSolution("Implementation error: group_index too large.")
            current_group = groups_copy[group_index]
            if not current_group:
                raise SolverData.NoSolution("Implementation error: current group already empty.")
            next_index = current_group.pop(0)
            return next_index

        solution = Solution()
        for a, b, c in final_triplets:
            a_index = get_next_index(a)
            b_index = get_next_index(b)
            c_index = get_next_index(c)
            weight_a = self.orig_weights[a_index]
            weight_b = self.orig_weights[b_index]
            weight_c = self.orig_weights[c_index]
            logger.debug(f"Adding triplet to solution: ({weight_a}, {weight_b}, {weight_c})")
            solution.add(Triplet(weight_a, weight_b, weight_c))

        self.answer.solution = solution
        logger.debug("Solution finalized and stored in answer")

    def post_check(self):
        if self.answer.success:
            logger.debug("Running post-check for solution validation")
            try:
                SolutionChecker.check(self.orig_problem, self.answer.solution)
                logger.debug("Post-check passed")
            except Exception as e:
                self.answer.success = False
                self.answer.error_message += f"SolutionCheck: {str(e)}"
                logger.error(f"Post-check failed: {e}")
