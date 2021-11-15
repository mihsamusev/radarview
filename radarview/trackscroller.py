import numpy as np
import matplotlib.pyplot as plt

class TrackScroller:
    def __init__(self, axesPos, axesVel, dataset, filter_state):
        self.axesPos = axesPos
        self.axesVel = axesVel
        self.dataset = dataset
        self.i = 0
        self.iMin = 0
        self.filter_state = filter_state
        self.filtered_dataset = [t for t in self.dataset if self.is_valid_track(t)]
        self.iMax = len(self.filtered_dataset) - 1

    def is_valid_track(self, track):
        if track["road"] not in self.filter_state["roads"]:
            return False
        if track["type"] not in self.filter_state["types"]:
            return False
        stops = "with" if track["idle_count"] > 0 else 'without'
        if stops not in self.filter_state["stops"]:
            return False
        return True

    def describe_track(self, track):
        print((
            f"Track {track['id']}: {track['type']} at road "
            f"{track['road']} {track['length']:.1f} m long with "
            f"{track['idle_count']}/{len(track['phistory'])} stops"))

    def clean_axes(self, ax, tag):
        lines = [line for line in ax.lines if line.get_gid() == tag]
        for line in lines:
            ax.lines.remove(line)

    def update_axes(self, track):
        # position axes
        self.clean_axes(self.axesPos, "position")
        x, y = zip(*track["phistory"])
        self.axesPos.plot(x,y,"r-x",gid="position")
        self.axesPos.plot(x[0],y[0],"ro", markersize=8, gid="position")
        self.axesPos.plot(x[-1],y[-1],"rv", markersize=8, gid="position")

        # velocity axes
        self.clean_axes(self.axesVel, "velocity")
        t = np.array(track["timestamps"]) / 1000
        t = t - t[0]
        u, v = zip(*track["vhistory"])
        speed = (np.array(u) ** 2 + np.array(v) ** 2) ** 0.5
        self.axesVel.plot(t, speed, "r-x",gid="velocity")
        self.axesVel.set_xlim(0, np.max(t))

        self.axesVel.set_title(f"Track {self.i}/{self.iMax}")
        plt.draw()

    def next(self, event):
        if self.i < self.iMax:
            self.i += 1
            track = self.filtered_dataset[self.i]
            self.update_axes(track)
            self.describe_track(track)

    def prev(self, event):
        if self.i > self.iMin:
            self.i -= 1
            track = self.filtered_dataset[self.i]
            self.update_axes(track)
            self.describe_track(track)


