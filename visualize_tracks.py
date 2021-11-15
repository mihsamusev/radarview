import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import json
from radarview.trackscroller import TrackScroller
import argparse

# parse arguments
ag = argparse.ArgumentParser()
ag.add_argument("-c","--config", required=True, help="path to configuration file")
ag.add_argument("-d","--data", required=True,help="path to data with complete tracks")
ag.add_argument('-r','--roads', nargs='+', default=["A1","A2","B"],help="which roads to limit to")
ag.add_argument('-t','--types', nargs='+', default=["truck","car"],help="which vehicle types to limit to")
ag.add_argument("-s","--stops", nargs="+", default=["with","without"], help="which states to include")
args = vars(ag.parse_args())

# load json file
with open(args["config"],"r") as f:
    conf = json.load(f)

# load nad plot background image
img = plt.imread(conf["background_image"])
xmin, xmax = conf["easting_range"]
ymin, ymax = conf["northing_range"]

fig, (axPos, axVel), = plt.subplots(1, 2)
axPos.imshow(img, extent=[xmin, xmax, ymin, ymax])
axPos.set_xlim(xmin, xmax)
axPos.set_ylim(ymin, ymax)
axPos.set_aspect('auto')
axPos.axis("off")
axPos.set_position([0.01, 0.03, 0.45, 0.87])
axVel.set_position([0.53, 0.07, 0.45, 0.83])
axVel.set_xlabel("time (s)")
axVel.set_ylabel("speed (m/s)")

# pre load 100 measurements from json file
with open(args["data"],"r") as data_file:
    dataset = json.load(data_file)["tracks"]

# create control over data
filter_state = {
    "roads": args["roads"],
    "types": args["types"],
    "stops": args["stops"]
    }
datacontrol = TrackScroller(axPos, axVel, dataset, filter_state)

axprev = plt.axes([0.01, 0.92, 0.1, 0.07])
axnext = plt.axes([0.12, 0.92, 0.1, 0.07])
bnext = Button(axnext, 'Next')
bprev = Button(axprev, 'Previous')
bnext.on_clicked(datacontrol.next)
bprev.on_clicked(datacontrol.prev)
plt.show()
