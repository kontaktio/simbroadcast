#!/usr/bin/env python
import heapq
import random
from argparse import ArgumentParser
from functools import total_ordering


@total_ordering
class BeaconBcast(object):
    def __init__(self, beacon_id, interval, scheduled_at=None):
        self.id = beacon_id
        self.interval = interval
        self.adv_scheduled_at = scheduled_at or random.uniform(0.0, interval) + random.uniform(0.0, 0.01)

    def get_next(self):
        return BeaconBcast(self.id, self.interval, self.adv_scheduled_at + self.interval + random.uniform(0.0, 0.01))

    def __eq__(self, other):
        return self.adv_scheduled_at == other.adv_scheduled_at

    def __lt__(self, other):
        return self.adv_scheduled_at < other.adv_scheduled_at

    def __repr__(self):
        return '{}: {:.3f}'.format(self.id, self.adv_scheduled_at)


class BroadcastSimulator(object):
    BLE_ADV_DURATION = 0.001

    def __init__(self):
        self._beacons = []
        self._beacons_noticed = set()

    def add_beacon(self, interval):
        b = BeaconBcast(len(self._beacons), interval)
        heapq.heappush(self._beacons, b)

    def add_beacons(self, interval, amt):
        for i in range(len(self._beacons), len(self._beacons) + amt):
            heapq.heappush(self._beacons, BeaconBcast(i, interval))

    def run(self, duration, scan_prob=0.25):
        time = 0
        bfirst = heapq.heappop(self._beacons)
        while time < duration:
            bnext = heapq.heappushpop(self._beacons, bfirst.get_next())
            colliding = [bfirst]
            while bfirst.adv_scheduled_at + self.BLE_ADV_DURATION > bnext.adv_scheduled_at:
                colliding.append(bnext)
                try:
                    bnext = heapq.heappushpop(self._beacons, bnext.get_next())
                except IndexError:
                    # all beacons popped
                    bnext = None
                    break

            if len(colliding) == 1 and random.uniform(0, 1.0) < scan_prob:
                previously_noticed = len(self._beacons_noticed)
                self._beacons_noticed.add(colliding[0].id)
                if len(self._beacons_noticed) > previously_noticed:
                    print '{:.3f} noticed: {}'.format(time, len(self._beacons_noticed))
            else:
                pass

            if bnext is not None:
                bfirst = bnext
            else:
                bfirst = heapq.heappop(self._beacons)
            time = bfirst.adv_scheduled_at

        heapq.heappush(self._beacons, bfirst.get_next())

        print 'noticed {} of {} beacons ({:.1f}%)'.format(len(self._beacons_noticed), len(self._beacons),
                                                          100.0 * len(self._beacons_noticed) / len(self._beacons))


def main():
    SCAN_PROB_DEFAULT = 0.25
    s = BroadcastSimulator()
    p = ArgumentParser('simbroadcast.py',
                       description='Simulates multiple beacons broadcasting simultaneously in one location. Helps '
                                   'answer question: how many beacons can single scanner register?')
    p.add_argument('-n', type=int, required=True,
                   help='Amount of broadcasting beacons')
    p.add_argument('-i', '--interval', type=float, required=True,
                   help='Broadcasting interval in seconds')
    p.add_argument('--scan_prob', type=float, default=SCAN_PROB_DEFAULT,
                   help='Probability that given, not colliding boradcast will be successfully scanned. Default: '
                        '{:.2f} (Note that this default value is not supported by any experiments yet)'
                   .format(SCAN_PROB_DEFAULT))
    p.add_argument('duration', type=int, metavar='DURATION', help='Scanning duration')
    args = p.parse_args()
    s.add_beacons(interval=args.interval, amt=args.n)
    s.run(duration=args.duration, scan_prob=args.scan_prob)


if __name__ == '__main__':
    main()
