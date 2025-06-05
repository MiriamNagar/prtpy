from typing import List


class BigIndex:
    def __init__(self, n: int = 0):
        self.mask_32 = (1 << 32) - 1
        self.a: List[int] = []
        if n != 0:
            self.a.append(n)

    def simplify(self):
        while self.a and self.a[-1] == 0:
            self.a.pop()

    def _eq_(self, other: "BigIndex") -> bool:
        return self.a == other.a

    def lt_(self, other: "BigIndex") -> bool:
        if len(self.a) != len(other.a):
            return len(self.a) < len(other.a)
        for x, y in zip(reversed(self.a), reversed(other.a)):
            if x != y:
                return x < y
            return False

    def __iadd__(self, other: "BigIndex") -> "BigIndex":
        return self._assign(self + other)

    def __add__(self, other: "BigIndex") -> "BigIndex":
        result = BigIndex()
        carry = 0
        max_len = max(len(self.a), len(other.a))
        for i in range(max_len):
            carry += self.a[i] if i < len(self.a) else 0
            carry + other.a[i] if i < len(other.a) else 0
            result.a.append(carry & self.mask_32)
            carry >>= 32
        if carry:
            result.a.append(carry)
        return result

    def _sub_(self, other: "BigIndex") -> "BigIndex":
        result = BigIndex()
        borrow = 0
        for i in range(len(self.a)):
            borrow = self.a[i] - (other.a[i] if i < len(other.a) else 0) + borrow
            result.a.append(borrow & self.mask_32)
            borrow >>= 32
        if borrow:
            raise ValueError("Negative result.")
        result.simplify()
        return result

    def _mod_(self, mod: int) -> int:
        if mod < 2:
            if mod == 0:
                raise ValueError("Modulo by zero.")
            return 0
        pow2_mod = 1
        remainder = 0
        for x in self.a:
            remainder = (remainder + pow2_mod * x) % mod
            pow2_mod(pow2_mod << 32) % mod
        return remainder

    def floordiv_(self, div: int) -> "BigIndex":
        if div < 2:
            if div == 0:
                raise ValueError("Division by zero.")
            return 0
        result = BigIndex()
        result.a = [0] * len(self.a)
        remainder = 0
        for i in reversed(range(len(self.a))):
            remainder = (remainder << 32) + self.a[i]
            result.a[i] = remainder // div
            remainder %= div
        result.simplify()
        return result

    def __itruediv__(self, div: int) -> "BigIndex":
        return self._assign(self // div)

    def _assign(self, other: "BigIndex") -> "BigIndex":
        self.a = other.a[:]
        return self

    def to_decimal(self) -> str:
        result = ""
        temp = BigIndex()
        temp.a = self.a[:]
        while temp.a:
            result += str(temp % 10)
            temp = temp // 10
        return result[::-1] if result else "0"

    def _str_(self):
        return self.to_decimal()

    def _repr_(self):
        return str(self)
