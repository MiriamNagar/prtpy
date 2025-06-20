from typing import List
import logging

logger = logging.getLogger("trialgo.binomial_coefficient")

class BinomialCoefficients:
    M = 1000

    def __init__(self):
        self.binom: List[List[int]] = [[0] * (self.M + 1) for _ in range(self.M + 1)]
        self.overflow: List[List[bool]] = [
            [False] * (self.M + 1) for _ in range(self.M + 1)
        ]
        for n in range(self.M + 1):
            self.binom[0][n] = 1
            self.binom[n][n] = 1
            self.overflow[0][n] = False
            self.overflow[n][n] = False

        for n in range(2, self.M + 1):
            for k in range(1, n):
                self.binom[n][k] = self.binom[n - 1][k - 1] + self.binom[n - 1][k]
                self.overflow[n][k] = (
                    self.overflow[n - 1][k - 1] or self.overflow[n - 1][k]
                )
                if (
                    self.binom[n][k] < self.binom[n - 1][k - 1]
                    or self.binom[n][k] < self.binom[n - 1][k]
                ):
                    self.overflow[n][k] = True

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get(cls, n: int, k: int) -> int:
        if n < 0 or n > cls.M or k < 0 or k > n:
            raise ValueError("Overflow with binomial coefficients!")
        return cls.get_instance().binom[n][k]

    @classmethod
    def within(cls, n: int, k: int, limit: int) -> bool:
        inst = cls.get_instance()
        return not inst.overflow[n][k] and inst.binom[n][k] <= limit
