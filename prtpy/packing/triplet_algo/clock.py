import time
from datetime import datetime


class Clock:
    _start_time = time.perf_counter()

    @staticmethod
    def print_time(fraction_digits: int = 3) -> str:
        now = datetime.now()
        base_time = now.strftime("%Y.%m.%d %H:%M:%S")
        if fraction_digits > 0:
            ns = now.timestamp() % 1
            frac = f" {ns:.{fraction_digits}f}"[1:]
            return base_time + frac
        return base_time

    @staticmethod
    def elapsed() -> float:
        return time.perf_counter() - Clock._start_time

    @staticmethod
    def benchmark_self(seconds: float):
        count = 0
        end_time = Clock.elapsed() + seconds
        while Clock.elapsed() < end_time:
            count += 1
        ratio = count / seconds
        print(f"Clock.benchmark(): {count} / {seconds} = {ratio}")
