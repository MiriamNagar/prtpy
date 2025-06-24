from typing import List
import logging

logger = logging.getLogger(__name__)

class BinomialCoefficients:
    M = 1000

    def __init__(self):
        logger.info("Initializing binomial coefficient table up to M = %d", self.M)
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
                    logger.debug("Overflow detected at n=%d, k=%d", n, k)

        logger.info("Binomial table initialization complete")

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            logger.debug("Creating singleton instance of BinomialCoefficients")
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get(cls, n: int, k: int) -> int:
        if n < 0 or n > cls.M or k < 0 or k > n:
            logger.error("Invalid binomial coefficient request: n=%d, k=%d", n, k)
            raise ValueError("Overflow with binomial coefficients!")
        result = cls.get_instance().binom[n][k]
        logger.debug("Binomial coefficient get(%d, %d) = %d", n, k, result)
        return result

    @classmethod
    def within(cls, n: int, k: int, limit: int) -> bool:
        inst = cls.get_instance()
        result = not inst.overflow[n][k] and inst.binom[n][k] <= limit
        logger.debug("Binomial coefficient within(%d, %d, %d) -> %s", n, k, limit, result)
        return result
