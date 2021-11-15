import numpy as np
from scipy.spatial import distance
from shapely.geometry import Point, Polygon
import re
from copy import deepcopy

class Track:
    def __init__(self, timestamp, position, velocity, vehicleType, road, radar):
        self.id = -1
        self.missing = 0
        self.time = [timestamp]
        self.phistory = [position]
        self.vhistory = [velocity]
        self.type = vehicleType
        self.road = road
        self.radar = radar

    def addMeasurement(self, timestamp, position, velocity):
        self.missing = 0
        self.time.append(timestamp)
        self.phistory.append(position)
        self.vhistory.append(velocity)

    def length(self):
        length = 0
        for i in range(1, len(self.phistory)):
            p0 = self.phistory[i-1]
            p1 = self.phistory[i]
            length += distance.euclidean(p0, p1)
        return length

    def idleTime(self):
        idle_count = 0
        for (vx, vy) in self.vhistory:
            if vx == 0 and vy == 0:
                idle_count += 1
        return idle_count

    def get_dict(self):
        out = {
            "id": self.id,
            "missing": self.missing,
            "type": self.type,
            "road": self.road,
            "radar": self.radar,
            "length": self.length(), 
            "idle_count": self.idleTime(),
            "timestamps": self.time,
            "phistory": self.phistory,
            "vhistory": self.vhistory
        }
        return out

class RadarTrackManager:
    def __init__(self, validation_roi, max_missing=2):
        self.tracks = dict()
        self.max_missing = max_missing
        self.track_count = 0 
        self.complete_tracks = []
        self.validation_roi = validation_roi
        
        self.lengths = []
        self.types = dict()
        self.roads = dict()
        self.pass_by_count = 0
        self.total_length = 0
        self.total_length_complete = 0

    def update(self, data, timestamp):
        datadict = {f'{d["id"]}_{d["radar"][-1]}': d for d in data}
        trackedIDs = self.tracks.keys()
        measuredIDs = datadict.keys()

        updateIDs = set(trackedIDs).intersection(measuredIDs)
        missingIDs = set(trackedIDs).difference(updateIDs)
        newIDs = set(measuredIDs).difference(updateIDs)

        for ID in updateIDs:
            position = [datadict[ID]["x_pos_utm"], datadict[ID]["y_pos_utm"]]
            velocity = [datadict[ID]["x_speed_utm"], datadict[ID]["y_speed_utm"]]
            self.tracks[ID].addMeasurement(timestamp, position, velocity)

        for ID in newIDs:
            position = [datadict[ID]["x_pos_utm"], datadict[ID]["y_pos_utm"]]
            velocity = [datadict[ID]["x_speed_utm"], datadict[ID]["y_speed_utm"]]
            vehicleType = datadict[ID]["vehicle_class"]
            radar = datadict[ID]["radar"]
            road = re.findall("^[A-Q][\d]{0,1}",radar)[0]
            self.tracks[ID] = Track(timestamp, position, velocity, vehicleType, road, radar)
            self.tracks[ID].id = ID
            self.track_count += 1

        for ID in missingIDs:
            self.tracks[ID].missing +=1
            if self.tracks[ID].missing > self.max_missing:
                l = self.tracks[ID].length()
                self.total_length += l
                if self._is_valid_track(self.tracks[ID]):
                    self.complete_tracks.append(self.tracks[ID].get_dict())
                    self._update_statistics(self.tracks[ID])
                    self.total_length_complete += l
                del self.tracks[ID]

    def _update_statistics(self, track):
        # length
        self.lengths.append(track.length())

        # roads count dictionary
        if track.road in self.roads:
            self.roads[track.road] += 1
        else:
            self.roads[track.road] = 1

        # types count dictionary
        if track.type in self.types:
            self.types[track.type] += 1
        else:
            self.types[track.type] = 1

        # contains stopping
        if track.idleTime() == 0:
            self.pass_by_count += 1

    def _is_valid_track(self, track, min_length=100):
        is_long_enough = track.length() >= min_length

        # did track finish in the intersection
        last_pt = Point(track.phistory[-1][0], track.phistory[-1][1])
        poly = Polygon(self.validation_roi)
        is_finished = poly.contains(last_pt)
        return (is_long_enough and is_finished)

    def print_tracks(self):
        print("tracker state:")
        for key, value in self.tracks.items():
            print((
            f"    ID: {value.id:<10} "
            f"missing: {value.missing:<10} "
            f"last point: [{value.phistory[-1][0]:<10.2f}, {value.phistory[-1][1]:<10.2f}] "
            f"last speed: [{value.vhistory[-1][0]:<10.2f}, {value.vhistory[-1][1]:<10.2f}]"))

    def get_results_dict(self):
        return {
            "tracks_per_category":self.types,
            "tracks_per_lane":self.roads,
            "total_length_all_tracks": self.total_length,
            "total_length_complete_tracks": self.total_length_complete,
            "percent_complete_tracks": self.total_length_complete / self.total_length,
            "pass_by_count": self.pass_by_count,
            "mean_track_length": np.mean(self.lengths),
            "max_track_length": np.max(self.lengths),
            "min_track_length": np.min(self.lengths),
            "std_track_length": np.std(self.lengths)
        }

    def get_complete_tracks(self):
        return deepcopy(self.complete_tracks)



