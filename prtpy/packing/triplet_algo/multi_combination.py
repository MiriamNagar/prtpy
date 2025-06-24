from typing import List, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# from base import WeightType
WeightType = int


class MultiCombination:
    class Item:
        def __init__(self, weight: WeightType):
            self.weight = weight
            self.indices: List[int] = []

        def __repr__(self):
            return f"Item(weight={self.weight}, indices={self.indices})"

    def __init__(self, indices: List[int] = [], weights: List[WeightType] = []):
        logger.debug("MultiCombination.__init__ called")
        self.items: List[MultiCombination.Item] = []
        self.total_count = 0
        self.ctr: List[List[int]] = []

        if indices and weights:
            logger.debug(f"Initializing with indices={indices}, weights={weights}")
            self.init(indices, weights)
        else:
            logger.debug("No indices or weights provided at init")

    def init(self, indices: List[int], weights: List[WeightType]):
        logger.info("Initializing MultiCombination with given indices and weights")
        if len(indices) != len(weights):
            logger.error("Indices and weights length mismatch")
            raise ValueError("Indices and weights must have the same size!")

        self.total_count = len(indices)
        logger.debug(f"Total count: {self.total_count}")

        weight_groups = defaultdict(list)
        for i, w in zip(indices, weights):
            weight_groups[w].append(i)

        logger.debug(f"Grouped weights: {dict(weight_groups)}")

        self.items.clear()
        for weight in sorted(weight_groups.keys(), reverse=True):
            item = MultiCombination.Item(weight)
            item.indices = weight_groups[weight]
            self.items.append(item)

        logger.debug(f"Items after grouping and sorting: {self.items}")

        K = self.total_count
        B = len(self.items)

        # Initialize ctr table
        self.ctr = [[0 for _ in range(B + 1)] for _ in range(K + 1)]
        for b in range(B + 1):
            self.ctr[0][b] = 1
        for k in range(1, K + 1):
            self.ctr[k][0] = 0

        for k in range(1, K + 1):
            for b in range(1, B + 1):
                index = B - b
                curr_max = min(len(self.items[index].indices), k)
                sum_val = 0
                for c in range(curr_max + 1):
                    sum_val += self.ctr[k - c][b - 1]
                self.ctr[k][b] = sum_val

        logger.debug(f"ctr table computed (partial): {self.ctr[:min(5, K+1)]}")

    def get_choice_count(self, k: int) -> int:
        logger.debug(f"get_choice_count called with k={k}")
        if k > self.total_count:
            logger.warning(f"Requested choice count for k={k} greater than total_count={self.total_count}")
            return 0
        count = self.ctr[k][len(self.items)]
        logger.debug(f"Choice count for k={k}: {count}")
        return count

    def get_single_choice(self, k: int, case_index: int) -> List[int]:
        logger.debug(f"get_single_choice called with k={k}, case_index={case_index}")

        max_index = self.ctr[k][len(self.items)]
        if not case_index < max_index:
            logger.error(f"Invalid case_index={case_index} >= max_index={max_index}")
            raise ValueError(
                f"Invalid case index: {case_index} not below {max_index}"
            )

        result = []
        b = len(self.items)

        while k > 0:
            index = len(self.items) - b
            curr_max = min(len(self.items[index].indices), k)
            sum_val = 0
            for c in reversed(range(curr_max + 1)):
                current_count = self.ctr[k - c][b - 1]
                next_sum = sum_val + current_count
                if case_index < next_sum:
                    result.extend(self.items[index].indices[:c])
                    k -= c
                    b -= 1
                    case_index -= sum_val
                    break
                sum_val = next_sum

        logger.debug(f"get_single_choice result: {result}")
        return result
