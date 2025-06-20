from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, List, Set, Dict, Optional, Any
import heapq
import levela
import logging

logger = logging.getLogger("trialgo.heuristic")


@dataclass
class Stats:
    passes: int = 0
    distance: int = 0
    node_count: int = 0
    saved_count: int = 0
    skip1_count: int = 0
    skip2_count: int = 0


@dataclass
class TripletInfo:
    triplet: Tuple[int, int, int]
    used_count: int = 0


@dataclass
class GroupInfo:
    left: int = 0
    triplets: Set[int] = field(default_factory=set)


class LevelC:
    def __init__(
        self, orig_chosen_triplet_indices: List[int], level_a: levela.LevelA
    ) -> None:
        self.orig_chosen_triplet_indices = list(orig_chosen_triplet_indices)
        # initialize triplets
        T = len(level_a.triplets_abc)
        self.triplets: List[TripletInfo] = [
            TripletInfo(level_a.triplets_abc[t], 0) for t in range(T)
        ]

        # initialize groups
        G = len(level_a.groups)
        self.groups: List[GroupInfo] = [
            GroupInfo(level_a.group_cardinality[g]) for g in range(G)
        ]
        # assign triplet indices to groups
        # for t, info in enumerate(self.triplets):
        for t in range(T):
            # a,b,c = info.triplet
            a, b, c = self.triplets[t].triplet
            self.groups[a].triplets.add(t)
            self.groups[b].triplets.add(t)
            self.groups[c].triplets.add(t)

        # apply original chosen
        for t in self.orig_chosen_triplet_indices:
            self.triplets[t].used_count += 1
            a, b, c = self.triplets[t].triplet
            self.groups[a].left -= 1
            self.groups[b].left -= 1
            self.groups[c].left -= 1

        self.stats = Stats()

    class Node:
        __slots__ = (
            "parent",
            "prev",
            "triplet_index",
            "is_add",
            "infeas_count",
            "extra_items",
            "group_left",
            "triplet_used_count",
        )

        def __init__(
            self,
            parent: LevelC,
            prev: Optional[LevelC.Node] = None,
            is_add: bool = False,
            triplet_index: int = 0,
        ) -> None:
            self.parent = parent
            self.prev = prev
            self.triplet_index = triplet_index
            self.is_add = is_add
            # inherit mutable state or start fresh
            if prev is None:
                self.infeas_count = 0
                self.extra_items = 0
                self.group_left: Dict[int, int] = {}
                self.triplet_used_count: Dict[int, int] = {}
            else:
                self.infeas_count = prev.infeas_count
                self.extra_items = prev.extra_items
                self.group_left = dict(prev.group_left)
                self.triplet_used_count = dict(prev.triplet_used_count)
                a, b, c = parent.triplets[triplet_index].triplet
                if is_add:
                    self.addTriplet(triplet_index)
                    self._adjust_group(a, -1)
                    self._adjust_group(b, -1)
                    self._adjust_group(c, -1)
                else:
                    self.removeTriplet(triplet_index)
                    self._adjust_group(a, +1)
                    self._adjust_group(b, +1)
                    self._adjust_group(c, +1)

        def __lt__(self, other: LevelC.Node) -> bool:
            # fewer infeas, then more extra_items, then group_left dict comparison
            if self.infeas_count != other.infeas_count:
                return self.infeas_count < other.infeas_count
            if self.extra_items != other.extra_items:
                return self.extra_items > other.extra_items
            return sorted(self.group_left.items()) < sorted(other.group_left.items())

        def _adjust_group(self, g: int, delta: int) -> None:
            base = self.parent.groups[g].left
            left = self.group_left.get(g, base)
            new = left + delta
            if delta < 0 and new < 0:
                self.infeas_count += 1
            if delta > 0 and new <= 0:
                self.infeas_count -= 1
            if new == base:
                self.group_left.pop(g, None)
            else:
                self.group_left[g] = new
            self.extra_items += -delta

        def addTriplet(self, t: int) -> None:
            base = self.parent.triplets[t].used_count
            count = self.triplet_used_count.get(t, base)
            self.triplet_used_count[t] = count + 1

        def removeTriplet(self, t: int) -> None:
            base = self.parent.triplets[t].used_count
            count = self.triplet_used_count.get(t, base)
            self.triplet_used_count[t] = count - 1

        def getTripletUsedCount(self, t: int) -> int:
            return self.triplet_used_count.get(t, self.parent.triplets[t].used_count)

        def getGroupLeft(self, g: int) -> int:
            return self.group_left.get(g, self.parent.groups[g].left)

        def applySolutionOnParent(self) -> None:
            # collect path
            path: List[LevelC.Node] = []
            node = self
            while node.prev:
                path.append(node)
                node = node.prev

            for n in reversed(path):
                t = n.triplet_index
                if n.is_add:
                    self.parent.triplets[t].used_count += 1
                    a, b, c = self.parent.triplets[t].triplet
                    self.parent.groups[a].left -= 1
                    self.parent.groups[b].left -= 1
                    self.parent.groups[c].left -= 1
                else:
                    self.parent.triplets[t].used_count -= 1
                    a, b, c = self.parent.triplets[t].triplet
                    self.parent.groups[a].left += 1
                    self.parent.groups[b].left += 1
                    self.parent.groups[c].left += 1
            self.parent.stats.distance += len(path)

    def perform(self, max_infeas_count: int, max_steps: int) -> Tuple[bool, int]:
        self.stats.passes += 1

        T = len(self.triplets)
        G = len(self.groups)

        # priority queue and membership
        nodes_remaining: List[LevelC.Node] = []
        nodes_all_keys: Set[Any] = set()

        # helper to fingerprint a node
        def key(n: LevelC.Node):
            return (
                n.infeas_count,
                -n.extra_items,
                frozenset(n.group_left.items()),
                frozenset(n.triplet_used_count.items()),
            )

        # root
        root = LevelC.Node(self)
        heapq.heappush(nodes_remaining, root)
        nodes_all_keys.add(key(root))
        nodes_all_count = 1

        for step_count in range(max_steps):
            if not nodes_remaining:
                self.stats.node_count = step_count + 1
                self.stats.saved_count = nodes_all_count
                return False, step_count

            node = heapq.heappop(nodes_remaining)

            if node.infeas_count == 0 and node.extra_items > 0:
                node.applySolutionOnParent()
                self.stats.node_count = step_count + 1
                self.stats.saved_count = nodes_all_count
                return True, step_count

            # build next triplets
            next_triplets: Set[int] = set()
            is_add = node.infeas_count == 0
            if is_add:
                for g in range(G):
                    if node.getGroupLeft(g) > 0:
                        next_triplets |= self.groups[g].triplets
            else:
                for g, left in node.group_left.items():
                    if left < 0:
                        next_triplets |= self.groups[g].triplets

            # expand
            for t in next_triplets:
                if not is_add and node.getTripletUsedCount(t) == 0:
                    continue
                nxt = LevelC.Node(self, node, is_add, t)
                if nxt.infeas_count > max_infeas_count:
                    self.stats.skip1_count += 1
                    continue
                k = key(nxt)
                if k in nodes_all_keys:
                    self.stats.skip2_count += 1
                    continue
                heapq.heappush(nodes_remaining, nxt)
                nodes_all_keys.add(k)
                nodes_all_count += 1

        self.stats.node_count += max_steps
        self.stats.saved_count += nodes_all_count
        return False, max_steps

    def getFinalTripletCount(self) -> int:
        return sum(info.used_count for info in self.triplets)

    def getFinalTripletIndices(self) -> List[int]:
        return [
            t for t, info in enumerate(self.triplets) for _ in range(info.used_count)
        ]

    def getFinalTriplets(self) -> List[Tuple[int, int, int]]:
        return [self.triplets[t].triplet for t in self.getFinalTripletIndices()]

    def getStats(self) -> Stats:
        return self.stats
