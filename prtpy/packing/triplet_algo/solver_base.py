
# solver_base.py
class SolverError (Exception):
    pass
class NoSolution(SolverError):
    pass
class ProblemTooBig (SolverError):
    pass

MAX_LOOPS = 1_000_000_000_000
MAX_CASE_SECONDS = 1000.0
BACKTRACK_CHECK_TIME_PER_LOOPS = 1000

class BranchingChoiceStats:
    def __init__(self, apply, is_a, left, max_take, max_uses):
        self.apply = apply
        self.is_a = is_a
        self.left = left
        self.max_take = max_take
        self.max_uses = max_uses