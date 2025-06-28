"""
An implementation of the algorithms in:
    "Solution of Bin Packing Instances in Falkenauer T Class: Not So Hard",
    by György Dósa, András Éles, Angshuman Robin Goswami, István Szalkai, Zsolt Tuza (2025),
    https://www.mdpi.com/1999-4893/18/2/115#

Programmer: Miriam Nagar.
Date: 2025-04.
"""

from typing import List, Any
from prtpy import outputtypes as out
from prtpy.binners import BinsArray, Binner, printbins
from prtpy.binners import BinnerKeepingSums, BinnerKeepingContents
from .triplet_algo.problem import Problem
from .triplet_algo.solver import Solver
import logging

logger = logging.getLogger(__name__)


class NoSolutionError(Exception):
    """
    Raised when no valid solution is found by the algorithm.
    """

    def __init__(self, message="No valid allocation found."):
        super().__init__(message)


class NegativeValueError(ValueError):
    """
    Raised when a negative value is encountered where only non-negative values are allowed.
    This may relate to an item's value, a bin's size, or another domain-specific quantity.
    """

    def __init__(self, source: str, value):
        """
        :param source: A string describing the source of the negative value (e.g., 'item', 'bin size').
        :param value: The actual negative value encountered.
        """
        message = f"Negative value detected: {source} has value {value}."
        super().__init__(message)


class IncorrectTotalValueError(ValueError):
    """
    Raised when the total value of items does not match the expected or required total.
    """

    def __init__(self, actual_total, expected_total):
        message = (
            f"Incorrect total value: expected {expected_total}, but got {actual_total}."
        )
        super().__init__(message)


class InvalidInputTypeError(TypeError):
    """
    Raised when an input argument is of the wrong type (e.g., not list/int/callable).
    """

    def __init__(self, param_name, expected_type, actual_type):
        message = f"Invalid type for '{param_name}': expected {expected_type}, got {actual_type}."
        super().__init__(message)


def backtrack_method(binner: Binner, binsize: float, items: List[Any]) -> BinsArray:
    """
    Algorithm 1 from the paper: Complete backtracking search for fair item allocation.

    Given a list of items and a number of bin, returns an allocation of items
    to bins such that the allocation satisfies a triplet item allocations and each triplet sum
    is equal to the bin size. does so using backtrack method.

    Parameters:
        items: List of items to be allocated.

    Returns:
        A list of lists, where each inner list contains the items allocated to one bin.


    >>> from prtpy import BinnerKeepingContents
    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 400, 100, 490, 310, 200, 470, 330, 200]))
    Bin #0: [500, 400, 100], sum=1000
    Bin #1: [470, 330, 200], sum=1000
    Bin #2: [430, 310, 200], sum=1000

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[501, 400, 100, 490, 310, 200, 470, 330, 200]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[400, 350, 250]))
    Bin #0: [400, 350, 250], sum=1000

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 400, 100, 200, 300]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 500, 500]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[
    ...     369, 334, 297, 447, 302, 251, 409, 339, 252, 402,
    ...     333, 265, 399, 347, 254, 462, 277, 261, 465, 280,
    ...     255, 412, 313, 275, 444, 305, 251, 403, 308, 289,
    ...     468, 270, 262, 426, 314, 260, 411, 307, 282, 382,
    ...     361, 257, 396, 340, 264, 396, 304, 300, 473, 267,
    ...     260, 475, 269, 256, 376, 366, 258, 423, 319, 258
    ... ]))
    Bin #0: [475, 269, 256], sum=1000
    Bin #1: [473, 267, 260], sum=1000
    Bin #2: [468, 270, 262], sum=1000
    Bin #3: [465, 280, 255], sum=1000
    Bin #4: [462, 277, 261], sum=1000
    Bin #5: [447, 302, 251], sum=1000
    Bin #6: [444, 305, 251], sum=1000
    Bin #7: [426, 314, 260], sum=1000
    Bin #8: [423, 319, 258], sum=1000
    Bin #9: [412, 313, 275], sum=1000
    Bin #10: [411, 307, 282], sum=1000
    Bin #11: [409, 339, 252], sum=1000
    Bin #12: [403, 308, 289], sum=1000
    Bin #13: [402, 333, 265], sum=1000
    Bin #14: [399, 347, 254], sum=1000
    Bin #15: [396, 340, 264], sum=1000
    Bin #16: [396, 304, 300], sum=1000
    Bin #17: [382, 361, 257], sum=1000
    Bin #18: [376, 366, 258], sum=1000
    Bin #19: [369, 334, 297], sum=1000
    """
    logger.info(f"Starting backtrack_method with {len(items)} items and bin size {binsize}")
    problem = Problem()
    problem.init(items, binsize)

    logger.info("Problem initialized. Solving with backtracking...")
    result = Solver.solve(problem)

    bins = binner.new_bins(len(items) // 3)
    logger.info("Creating bins and assigning triplets...")
    for bin_i, triplet in enumerate(result.solution.get_triplets()):
        for item in triplet.get():
            binner.add_item_to_bin(bins, item, bin_i)
    logger.info(f"Backtrack solution completed with {len(bins)} bins.")
    return bins


def local_search(binner: Binner, binsize: float, items: List[any]) -> BinsArray:
    """
    Algorithm 2 from the paper: Local search heuristic for fair item allocation.

    Given a list of items and a number of bin, returns an allocation of items
    to bins such that the allocation satisfies a triplet item allocations and each triplet sum
    is equal to the bin size. does so using local_search method.

    >>> from prtpy import BinnerKeepingContents
    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 400, 100, 490, 310, 200, 470, 330, 200]))
    Bin #0: [500, 400, 100], sum=1000
    Bin #1: [470, 330, 200], sum=1000
    Bin #2: [430, 310, 200], sum=1000

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[501, 400, 100, 490, 310, 200, 470, 330, 200]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[400, 350, 250]))
    Bin #0: [400, 350, 250], sum=1000

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 400, 100, 200, 300]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[500, 500, 500]))
    Traceback (most recent call last):
    ...
    NoSolutionError: No valid allocation found.

    >>> printbins(backtrack_method(BinnerKeepingContents(), binsize=1000, items=[
    ...     369, 334, 297, 447, 302, 251, 409, 339, 252, 402,
    ...     333, 265, 399, 347, 254, 462, 277, 261, 465, 280,
    ...     255, 412, 313, 275, 444, 305, 251, 403, 308, 289,
    ...     468, 270, 262, 426, 314, 260, 411, 307, 282, 382,
    ...     361, 257, 396, 340, 264, 396, 304, 300, 473, 267,
    ...     260, 475, 269, 256, 376, 366, 258, 423, 319, 258
    ... ]))
    Bin #0: [475, 269, 256], sum=1000
    Bin #1: [473, 267, 260], sum=1000
    Bin #2: [468, 270, 262], sum=1000
    Bin #3: [465, 280, 255], sum=1000
    Bin #4: [462, 277, 261], sum=1000
    Bin #5: [447, 302, 251], sum=1000
    Bin #6: [444, 305, 251], sum=1000
    Bin #7: [426, 314, 260], sum=1000
    Bin #8: [423, 319, 258], sum=1000
    Bin #9: [412, 313, 275], sum=1000
    Bin #10: [411, 307, 282], sum=1000
    Bin #11: [409, 339, 252], sum=1000
    Bin #12: [403, 308, 289], sum=1000
    Bin #13: [402, 333, 265], sum=1000
    Bin #14: [399, 347, 254], sum=1000
    Bin #15: [396, 340, 264], sum=1000
    Bin #16: [396, 304, 300], sum=1000
    Bin #17: [382, 361, 257], sum=1000
    Bin #18: [376, 366, 258], sum=1000
    Bin #19: [369, 334, 297], sum=1000
    """
    logger.info(f"Starting local_search with {len(items)} items and bin size {binsize}")
    problem = Problem()
    problem.init(items, binsize)

    logger.info("Problem initialized. Solving with local search...")
    result = Solver.solve(problem, use_local_search=True)

    bins = binner.new_bins(len(items) // 3)
    logger.info("Creating bins and assigning triplets...")
    for bin_i, triplet in enumerate(result.solution.get_triplets()):
        for item in triplet.get():
            binner.add_item_to_bin(bins, item, bin_i)
    logger.info(f"Local search completed with {len(bins)} bins.")
    return bins


if __name__ == "__main__":
    import doctest

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Running doctests for triplet algorithms...")
    (failures, tests) = doctest.testmod(report=True)
    logger.info(f"Testing complete: {failures} failures, {tests} tests")
    print("{} failures, {} tests".format(failures, tests))
