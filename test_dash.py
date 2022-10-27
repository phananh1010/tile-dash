# This is a simple script showing how to customize DASH algorithm for tile-based streaming using GPAC framework


import datetime
import types
import sys
import time

import libgpac as gpac


print("Welcome to GPAC Python !\nVersion: " + gpac.version + "\n" + gpac.copyright_cite)

#parse our args
mem_track=0
gpac.init(mem_track)


class MyCustomDASHAlgo:
    def on_period_reset(self, type):
        print('period reset type ' + str(type))

    def on_new_group(self, group):
        print('new group ' + str(group.idx) + ' qualities ' + str(len(group.qualities)) + ' codec ' + group.qualities[0].codec);

    def on_rate_adaptation(self, group, base_group, force_low_complexity, stats):
        if group.SRD.x == 0 and group.SRD.y == 0:
            print(f'We are adapting on group_idx:{group.idx},  active quality: {stats.active_quality_idx}')
            if stats.active_quality_idx != -2:
                return -2
            else:
                return len(group.qualities) - 1
        return len(group.qualities) - 1

    def on_download_monitor(self, group, stats):
        print('download monitor group ' + str(group.idx) + ' stats ' + str(stats) );
        return -1


mydash = MyCustomDASHAlgo()

#define a custom filter
class MyFilterSession(gpac.FilterSession):
    def __init__(self, flags=0, blacklist=None, nb_threads=0, sched_type=0):
        gpac.FilterSession.__init__(self, flags, blacklist, nb_threads, sched_type)

    def on_filter_new(self, f):
        print("new filter " + f.name);
        if f.name == "dashin":
            f.bind(mydash);

    def on_filter_del(self, f):
        print("del filter " + f.name);

#create a session
fs = MyFilterSession(0)

f1 = fs.load_src(f"http://129.174.114.121/dash/coaster2/coaster2_10x5.mpd")
f2 = fs.load("dashin")
f3 = fs.load("tileagg")
#load a sink
f4 = fs.load("inspect:interleave:false:deep:dur=10:buffer=2000")#:speed=0.45")

f2.set_source(f1)
f3.set_source(f2)
f4.set_source(f3)

#run the session in blocking mode
btime = time.time()
fs.run()

print(f'Done, executing time: {time.time() - btime}')
fs.print_graph()
fs.delete()
gpac.close()
