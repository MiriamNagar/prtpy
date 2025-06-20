from .benchmark_maker import BenchmarkMaker
from .clock import Clock
import logging

logger = logging.getLogger("trialgo.main")


if __name__ == "__main__":
    print("main() start!\n")
    main_start_t = Clock.elapsed()

    # try:
    print("Performing all benchmark tests...")
    BenchmarkMaker.perform_all()
    print("Done!\n")
    # except Exception as exc:
    #     print (f"Standard exception: {exc}")
    main_end_t = Clock.elapsed()
    main_elapsed = main_end_t - main_start_t
    print("main() end!")
    print(f"Total time elapsed: {main_elapsed} seconds.")
