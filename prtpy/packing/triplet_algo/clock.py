import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Clock:
    _start_time = time.perf_counter()

    @staticmethod
    def print_time(fraction_digits: int = 3) -> str:
        now = datetime.now()
        base_time = now.strftime("%Y.%m.%d %H:%M:%S")
        if fraction_digits > 0:
            ns = now.timestamp() % 1
            frac = f" {ns:.{fraction_digits}f}"[1:]
            formatted = base_time + frac
        else:
            formatted = base_time
        logger.debug("Clock.print_time() -> %s", formatted)
        return formatted

    @staticmethod
    def elapsed() -> float:
        elapsed_time = time.perf_counter() - Clock._start_time
        logger.debug("Clock.elapsed() -> %.6f", elapsed_time)
        return elapsed_time

    @staticmethod
    def benchmark_self(seconds: float):
        logger.info("Starting benchmark_self for %.2f seconds", seconds)
        count = 0
        end_time = Clock.elapsed() + seconds
        while Clock.elapsed() < end_time:
            count += 1
        ratio = count / seconds
        logger.info("Clock.benchmark(): %d iterations in %.2f seconds = %.2f/sec", count, seconds, ratio)
