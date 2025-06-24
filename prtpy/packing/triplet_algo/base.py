
# // in case of a tie at the branching step (relevant due to advanced indexing):
# // - 0 : choose the one with the lower index
# // - 1 : choose whichever index comes in the mixed array
TRIPLET_BACKTRACKER_BRANCHING_TIE_ORDER = 0

# // when the current branch is impossible:
# // - 0 : backtrack to the previous step, and try the next branch
# // - 1 : give up current A-set, exit branching at current triplets
BACKTRACKING_POLICY = 1

# // use improvement heuristic
# // - 0 : no
# // - 1 : yes
USE_IMPROVEMENT_HEURISTIC = 1