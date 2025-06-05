from typing import Tuple

WeightType = int


class Triplet:
    def __init__(self, v1: WeightType, v2: WeightType, v3: WeightType):
        self.set(v1, v2, v3)

    def a(self) -> WeightType:
        return self.t[0]

    def b(self) -> WeightType:
        return self.t[1]

    def c(self) -> WeightType:
        return self.t[2]

    def sum(self) -> WeightType:
        return self.a() + self.b() + self.c()

    def __lt__(self, other: "Triplet") -> bool:
        return (self.a(), self.b(), self.c()) < (other.a(), other.b(), other.c())

    def set(self, v1: WeightType, v2: WeightType, v3: WeightType):
        values = sorted([v1, v2, v3], reverse=True)
        self.set_ordered(values[0], values[1], values[2])

    def set_ordered(self, a: WeightType, b: WeightType, c: WeightType):
        self.t: Tuple[WeightType, WeightType, WeightType] = (a, b, c)

    def __str__(self):
        return f"{{{self.a()}, {self.b()},{self.c()}}}"

    def __repr__(self):
        return str(self)
