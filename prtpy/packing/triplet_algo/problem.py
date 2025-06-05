from typing import List

WeightType = int


class Problem:
    def __init__(self):
        self.weights: List[WeightType] = []

    def read(self, path: str):
        try:
            with open(path, "r") as file:
                self.weights = [int(line.strip()) for line in file if line.strip()]
        except FileNotFoundError:
            raise RuntimeError(f"Problem input file not found: {path}")
        self.check()

    def read_benchmark_format(self, path: str):
        try:
            with open(path, "r") as file:
                lines = [int(line.strip()) for line in file if line.strip()]
        except FileNotFoundError:
            raise RuntimeError(f"Problem input file not found: {path}")

        if len(lines) < 2:
            raise RuntimeError(
                "Benchmark file must contain at least two lines for N and triplet sum."
            )

        N = lines[0]
        triplet_sum = lines[1]
        self.weights = lines[2 : 2 + N]
        self.check()
        self.check_triplet_sum(triplet_sum)

    def check_triplet_sum(self, triplet_sum: WeightType):
        actual = sum(self.weights)
        expected = triplet_sum * (len(self.weights) // 3)
        if actual != expected:
            raise RuntimeError(
                f"Total sum mismatch, actual vs expected: {actual} vs {expected}"
            )

    def check(self):
        if any(w <= 0 for w in self.weights):
            raise RuntimeError(f"Non-positive weight found in: {self.weights}")
        if len(self.weights) % 3 != 0:
            raise RuntimeError(
                f"Weight count not a multiple of three: {len(self.weights)}"
            )

    def get_weights(self) -> List[WeightType]:
        return self.weights

    def get_n(self) -> int:
        return len(self.weights) // 3

    def to_string(self) -> str:
        return "[" + ",".join(str(w) for w in self.weights) + "]"
