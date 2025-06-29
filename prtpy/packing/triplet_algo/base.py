# Constants controlling solver behavior and heuristics

# In case of a tie when deciding which branch to take during triplet backtracking:
# - 0 : Choose the triplet with the lower index (deterministic order).
# - 1 : Choose whichever index appears first in the mixed array (may depend on input order).
TRIPLET_BACKTRACKER_BRANCHING_TIE_ORDER = 0

# Policy to apply when the current branch in backtracking is impossible:
# - 0 : Backtrack to the previous step and try the next alternative branch there.
# - 1 : Abandon the current A-set (subset) entirely and exit branching at the current triplets.
BACKTRACKING_POLICY = 1

# Flag to enable or disable the heuristic improvement phase after backtracking:
# - 0 : Disable heuristic improvement.
# - 1 : Enable heuristic improvement to possibly improve the found solution.
USE_IMPROVEMENT_HEURISTIC = 1
