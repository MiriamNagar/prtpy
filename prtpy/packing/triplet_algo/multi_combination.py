from typing import List, Tuple
from collections import defaultdict
from bigindex import BigIndex

# from base import WeightType
WeightType = int


class MultiCombination:
    class Item:
        def __init__(self, weight: WeightType):
            self.weight = weight
            self.indices: List[int] = []

    # def __init__(self):
    #     self.init({}, {})

    def __init__(self, indices: List[int] = [], weights: List[WeightType] = []):
        self.items: List[MultiCombination.Item] = []
        self.total_count = 0
        # self.ctr: List[List[BigIndex]] = []
        self.ctr: List[List[int]] = []
        if indices and weights:
            self.init(indices, weights)

    def init(self, indices: List[int], weights: List[WeightType]):
        if len(indices) != len(weights):
            raise ValueError("Indices and weights must have the same size!")
        self.total_count = len(indices)
        weight_groups = defaultdict(list)

        for i, w in zip(indices, weights):
            weight_groups[w].append(i)

        # print(f"weight_groups: {weight_groups}\n")

        self.items.clear()

        for weight in sorted(weight_groups.keys(), reverse=True):
            item = MultiCombination.Item(weight)
            item.indices = weight_groups[weight]
            self.items.append(item)

        # print(f" items (MultiCombination): {self.items}\n")

        K = self.total_count
        B = len(self.items)
        # self.ctr = [[BigIndex(0) for _ in range(B + 1)] for _ in range(K + 1)]
        self.ctr = [[0 for _ in range(B + 1)] for _ in range(K + 1)]
        for b in range(B + 1):
            # self.ctr[0][b] = BigIndex(1)
            self.ctr[0][b] = 1
        for k in range(1, K + 1):
            # self.ctr[k][0] = BigIndex (0)
            self.ctr[k][0] = 0
        for k in range(1, K + 1):
            for b in range(1, B + 1):
                index = B - b
                curr_max = min(len(self.items[index].indices), k)
                # sum_val = BigIndex(0)
                sum_val = 0
                for c in range(curr_max + 1):
                    sum_val += self.ctr[k - c][b - 1]
                self.ctr[k][b] = sum_val

        # print(f"ctr: {self.ctr}\n")

    def get_choice_count(self, k: int) -> BigIndex:
        if k > self.total_count:
            # return BigIndex(0)
            return 0
        return self.ctr[k][len(self.items)]

    def get_single_choice(self, k: int, case_index: BigIndex) -> List[int]:
        if not case_index < self.ctr[k][len(self.items)]:
            # raise ValueError(f"Invalid case index: {case_index.to_decimal()} not below {self.ctr[k][len(self.items)].to_decimal()}")
            raise ValueError(
                f"Invalid case index: {case_index} not below {self.ctr[k][len(self.items)]}"
            )
        result = []
        b = len(self.items)

        while k > 0:
            index = len(self.items) - b
            curr_max = min(len(self.items[index].indices), k)
            # sum_val = BigIndex(0)
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
        return result
