from typing import Tuple
import logging

logger = logging.getLogger("trialgo.triplet")


class Triplet:
    def __init__(self, v1: int, v2: int, v3: int):
        self.set(v1, v2, v3)

    def get(self):
        return self.t

    def a(self) -> int:
        return self.t[0]

    def b(self) -> int:
        return self.t[1]

    def c(self) -> int:
        return self.t[2]

    def sum(self) -> int:
        return self.a() + self.b() + self.c()

    def __lt__(self, other: "Triplet") -> bool:
        return (self.a(), self.b(), self.c()) < (other.a(), other.b(), other.c())

    def set(self, v1: int, v2: int, v3: int):
        values = sorted([v1, v2, v3], reverse=True)
        self.set_ordered(values[0], values[1], values[2])

    def set_ordered(self, a: int, b: int, c: int):
        self.t: Tuple[int, int, int] = (a, b, c)

    def __str__(self):
        return f"{{{self.a()}, {self.b()},{self.c()}}}"

    def __repr__(self):
        return str(self)
