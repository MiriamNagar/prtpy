
from typing import List
from triplet import Triplet
class Solution:
    def __init__(self):
        self.triplets: List[Triplet] = []
    
    def add(self, t: Triplet):
        self.triplets.append(t)

    def get_triplets (self) -> List[Triplet]: 
        return self.triplets
    
    def sort(self):
        self.triplets.sort(reverse=True)
    
    # This is a bit different in what it prints
    def to_string(self) -> str:
        self.sort()
        return ''.join(str(t) for t in self.triplets)
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return str(self)