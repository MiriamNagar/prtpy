from typing import List
from .triplet import Triplet
import logging

logger = logging.getLogger(__name__)


class Solution:
    def __init__(self):
        self.triplets: List[Triplet] = []
        logger.debug("Initialized an empty Solution")

    def add(self, t: Triplet):
        self.triplets.append(t)
        logger.debug("Added triplet: %s", t)

    def get_triplets(self) -> List[Triplet]:
        logger.debug("Retrieving triplets, count: %d", len(self.triplets))
        return self.triplets

    def sort(self):
        logger.debug("Sorting triplets")
        self.triplets.sort(reverse=True)
        logger.debug("Triplets sorted")

    def to_string(self) -> str:
        logger.debug("Generating string representation of sorted triplets")
        self.sort()
        result = "".join(str(t) for t in self.triplets)
        logger.debug("Generated string: %s", result)
        return result

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return str(self)
