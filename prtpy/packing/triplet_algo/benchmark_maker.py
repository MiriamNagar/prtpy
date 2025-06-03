
import os
import csv
from typing import List 
from problem import Problem 
from solver import Solver 
from clock import Clock

class BenchmarkMaker:
    @staticmethod
    def perform_all():
        result_path = "result.csv"
        # header = [
        #     "N", "i", "elapsed", "prep", "A:fix", "A:N", "A:K", 
        #     "A:options", "A:first", "Bt: Step", "Bt: Branch", "Bt: Back", 
        #     "Bt: Loops", "OK", "Error", "Solution",
        #     "WinningBranches", "Winning Branches Long",
        #     "Histogram: depth", "Histogram: stepsizes"
        # ]
        header = [
            "N", "i", "elapsed", "prep", "T", "G", "A:fix", "A:N", "A:K", 
            "A:options", "A:first", "Bt:Step", "Bt:Branch", "Bt:Back", 
            "Bt: Loops", "C:Passes", "C:Dist", "C:Nodes",
            "C:Saved", "C:Skip1", "C:Skip2"
            "OK", "Error", "Solution",
            "WinningBranches", "WinningBranchesLong",
            "Histogram:depth", "Histogram:stepsizes",
        ]
        with open(result_path, 'w', newline='') as out_file: 
            writer = csv.writer(out_file, delimiter=',') 
            writer.writerow(header)
            Nvals = [60, 120, 249, 501]
            for N in Nvals:
                for index in range(20):
                    print (f"N={N} index={index}")
                    path = f"prtpy/packing/triplet_algo/Falkenauer_T/Falkenauer_t{N}_{index:02d}.txt"
                    problem = Problem()
                    problem.read_benchmark_format(path)
                    
                    t_start = Clock.elapsed()
                    answer = Solver.solve (problem)
                    t_end = Clock.elapsed()
                    elapsed = t_end - t_start

                    def map_to_string(m):
                        return ''.join(f" [{k}: {v}]" for k, v in m.items())
                    
                    def winning_branches_str(wb, long_format):
                        out = ""
                        for b in wb:
                            out += "1" if b.apply else "0" 
                            if long_format:
                                out += f"({'A' if b.is_a else 'x'}, {b.left}/{b.max_take}|{b.max_uses})"
                        return out
                    row = [
                        N, 
                        index, 
                        elapsed,
                        answer.preprocess_triplet_count,
                        answer.T,
                        answer.G,
                        answer.definitely_a_cardinality,
                        answer.maybe_a_cardinality,
                        answer.maybe_a_choose,
                        answer.a_index_set_case_count, 
                        answer.a_cases_investigated,
                        answer.total_step_count,
                        answer.total_branching_count,
                        answer.total_backtrack_events,
                        answer.total_loops,
                        answer.improvement_passes,
                        answer.improvement_distance,
                        answer.improvement_node_count,
                        answer.improvement_saved_count,
                        answer.improvement_skip1_count,
                        answer.improvement_skip2_count,
                        answer.success,
                        answer.error_message,
                        answer.solution,
                        winning_branches_str(answer.winning_branches, False), 
                        winning_branches_str(answer.winning_branches, True), 
                        map_to_string(answer.total_loop_states_by_depth), 
                        map_to_string(answer.total_loop_states_by_step_counts),
                    ]
                    writer.writerow(row)
                    out_file.flush()