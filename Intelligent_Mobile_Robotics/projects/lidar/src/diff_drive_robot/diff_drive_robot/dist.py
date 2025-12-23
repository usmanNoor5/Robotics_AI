#!/usr/bin/env python3

import threading
import sys
from sensor_msgs.msg import LaserScan


class Dist:
    def __init__(self):
        self.m = threading.Lock()
        self.left = 0
        self.right=0
        self.front = 0

        self.raw = []

    def update(self, data: LaserScan):
        # these magic numbers were acquired from Alan Beadle
        # straight ahead is 540, 40 index range should be enough
        # left chosen to look slightly back to get in front of wall before turning
       

        self.m.acquire()
        self.raw = data
        # newfront = self.getmin(500, 581)
        # newleft = self.getmin(740, 851)
        # newright = self.getmin(220, 341)   # indices for right
        ranges= self.raw.ranges
        n = len(ranges)
        front = min(ranges[n//2 - 10 : n//2 + 10])   # middle of array = 180° = front
        right  = min(ranges[n//4 - 10 : n//4 + 10])   # 90°
        left = min(ranges[3*n//4 - 10 : 3*n//4 + 10]) # 270°
        back  = min(ranges[0:10] + ranges[-10:])     # 0° (start/end of array)
        self.left = left
        self.front = front
        self.right=right
        self.m.release()

    def get(self):
        self.m.acquire()
        l = self.left
        f = self.front
        r= self.right
        self.m.release()
        return (f, l,r)

    def angle_to_index(self, angle):
        return int((angle - self.raw.angle_min)/self.raw.angle_increment)

    def getmin(self, a, b):
        in_rng = lambda x: self.raw.range_min <= x <= self.raw.range_max
        vsp = [x for x in self.raw.self.raw[a:b] if in_rng(x)]
        if vsp:   # list is truthy if not empty
            return min(vsp)
        else:
            return sys.maxsize

    # angle in radians
    def at(self, angle):
        # TODO(exm): copy and paste programming, refactor later
        
        self.m.acquire()
        i = self.angle_to_index(angle)
        start = i - 40
        if start < 0:
            start = 0
        end = i + 40
        if end >= len(self.raw.self.raw):
            end = len(self.raw.self.raw) - 1
        ans = self.getmin(start, end)
        self.m.release()
        return ans
