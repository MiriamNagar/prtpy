from typing import List
import logging

logger = logging.getLogger(__name__)

WeightType = int

class Problem:
    def __init__(self):
        self.weights: List[WeightType] = []
        logger.debug("Problem instance created")

    def read(self, path: str):
        logger.info("Reading problem from file: %s", path)
        try:
            with open(path, "r") as file:
                self.weights = [int(line.strip()) for line in file if line.strip()]
            logger.debug("Weights loaded: %s", self.weights)
        except FileNotFoundError:
            logger.error("Problem input file not found: %s", path)
            raise RuntimeError(f"Problem input file not found: {path}")
        self.check()

    def read_benchmark_format(self, path: str):
        logger.info("Reading benchmark format from file: %s", path)
        try:
            with open(path, "r") as file:
                lines = [int(line.strip()) for line in file if line.strip()]
            logger.debug("Benchmark lines read: %s", lines)
        except FileNotFoundError:
            logger.error("Benchmark input file not found: %s", path)
            raise RuntimeError(f"Problem input file not found: {path}")

        if len(lines) < 2:
            logger.error("Benchmark file too short: %d lines", len(lines))
            raise RuntimeError(
                "Benchmark file must contain at least two lines for N and triplet sum."
            )

        N = lines[0]
        triplet_sum = lines[1]
        self.weights = lines[2 : 2 + N]
        logger.debug("Parsed N=%d, triplet_sum=%d, weights=%s", N, triplet_sum, self.weights)
        self.check()
        self.check_triplet_sum(triplet_sum)

    def init(self, weights: List[int], binsize: int):
        logger.info("Initializing Problem with weights and binsize")
        self.weights = weights
        self.binsize = binsize
        logger.debug("Weights: %s", weights)
        logger.debug("Binsize: %d", binsize)
        self.check()
        self.check_triplet_sum(self.binsize)

    def check_triplet_sum(self, triplet_sum: WeightType):
        actual = sum(self.weights)
        expected = triplet_sum * (len(self.weights) // 3)
        logger.debug("Checking triplet sum: actual=%d, expected=%d", actual, expected)
        if actual != expected:
            logger.error("Triplet sum mismatch: %d vs %d", actual, expected)
            raise RuntimeError(
                f"Total sum mismatch, actual vs expected: {actual} vs {expected}"
            )
        logger.info("Triplet sum check passed")

    def check(self):
        logger.debug("Performing weight checks: %s", self.weights)
        if any(w <= 0 for w in self.weights):
            logger.error("Non-positive weight found: %s", self.weights)
            raise RuntimeError(f"Non-positive weight found in: {self.weights}")
        if len(self.weights) % 3 != 0:
            logger.error("Weight count not divisible by 3: %d", len(self.weights))
            raise RuntimeError(
                f"Weight count not a multiple of three: {len(self.weights)}"
            )
        logger.info("Basic weight checks passed")

    def get_weights(self) -> List[WeightType]:
        return self.weights

    def get_n(self) -> int:
        return len(self.weights) // 3

    def to_string(self) -> str:
        return "[" + ",".join(str(w) for w in self.weights) + "]"
