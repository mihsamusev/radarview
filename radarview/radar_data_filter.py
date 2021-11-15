from scipy.spatial import distance_matrix
import math
import copy
import numpy as np
import re


class RadarDataFilter:
    def __init__(self, radars):
        self.radars = radars
        self.radar_names = [r["name"] for r in radars]

    def filter(self, dataset):
        # remove those with tag cycle or positive speed (away from radar)
        to_remove = [d for d in dataset if d["x_speed"] > 0 or d["vehicle_class"] == "bicycle"]
        for r in to_remove:
            dataset.remove(r)

        # convert dataset
        dataset = self.convert_xy_to_utm(dataset)

        A1ttyS0 = [d for d in dataset if d["radar"] == "A1, ttyS0"]
        A1ttyS3 = [d for d in dataset if d["radar"] == "A1, ttyS3"]
        A1merged = self.get_merged_dataset(A1ttyS0, A1ttyS3, tol=2)
        
        A2ttyS1 = [d for d in dataset if d["radar"] == "A2, ttyS1"]
        A2ttyS4 = [d for d in dataset if d["radar"] == "A2, ttyS4"]
        A2merged = self.get_merged_dataset(A2ttyS1, A2ttyS4, tol=2)

        B = [d for d in dataset if d["radar"] == "B, ttyS2"]

        return {"A1": A1merged, "A2": A2merged, "B": B}

    def is_point_in_polygon(self, x, y):
        # skimage has good implementation
        pass

    def get_merged_dataset(self, dataset1, dataset2, tol=1):
        # get position arrays
        pts1 = [[d["x_pos"], d["y_pos"]] for d in dataset1]
        pts2 = [[d["x_pos"], d["y_pos"]] for d in dataset2]

        # find intersection and difference
        common = self.find_same_measurements(pts1, pts2, tol=tol)
        unique1 = set(range(len(pts1))).difference(common[0])
        unique2 = set(range(len(pts2))).difference(common[1])

        # put together
        out = []
        for i in unique1:
            out.append(dataset1[i])

        for i in unique2:
            out.append(dataset2[i])

        for i in range(len(common[0])):
            matched = copy.deepcopy(dataset1[common[0][i]])
            matched["id"] = "-1"
            matched["radar"] = "A1"
            matched["x_pos"] = 0.5 * (dataset1[common[0][i]]["x_pos"] + dataset2[common[1][i]]["x_pos"])
            matched["y_pos"] = 0.5 * (dataset1[common[0][i]]["y_pos"] + dataset2[common[1][i]]["y_pos"])
            matched["x_speed"] = 0.5 * (dataset1[common[0][i]]["x_speed"] + dataset2[common[1][i]]["x_speed"])
            matched["y_speed"] = 0.5 * (dataset1[common[0][i]]["y_speed"] + dataset2[common[1][i]]["y_speed"])
            out.append(matched)
        
        return out

    def find_same_measurements(self, array1, array2, tol=1):
        out = [[],[]]
        if len(array1) != 0 and len(array2) != 0:
            D = distance_matrix(array1, array2)
            out = np.where(D <= tol)
        return out

    def convert_xy_to_utm(self, dataset):
        new_dataset = copy.deepcopy(dataset)
        for i, d in enumerate(new_dataset):
            matching_radar = [radar for radar in self.radars if radar['name'] == d["radar"]]
            if len(matching_radar) == 1:
                angle = math.radians(90 - matching_radar[0]["azimuth"])
                x_global_utm = matching_radar[0]["easting"] + d["x_pos"] * math.cos(angle) - d["y_pos"] * math.sin(angle)
                y_global_utm = matching_radar[0]["northing"] + d["x_pos"] * math.sin(angle) + d["y_pos"] * math.cos(angle)
                x_speed_global = d["x_speed"] * math.cos(angle) - d["y_speed"] * math.sin(angle)
                y_speed_global = d["x_speed"] * math.sin(angle) + d["y_speed"] * math.cos(angle)
                new_dataset[i]["x_pos"] = x_global_utm
                new_dataset[i]["y_pos"] = y_global_utm
                new_dataset[i]["x_speed"] = x_speed_global
                new_dataset[i]["y_speed"] = y_speed_global
        return new_dataset

    def add_utm(self, dataset):
        new_dataset = []
        for d in dataset:
            matching_radar = [radar for radar in self.radars if radar['name'] == d["radar"]]
            if len(matching_radar) == 1:
                angle = math.radians(90 - matching_radar[0]["azimuth"])
                d["x_pos_utm"] = matching_radar[0]["easting"] + d["x_pos"] * math.cos(angle) - d["y_pos"] * math.sin(angle)
                d["y_pos_utm"]  = matching_radar[0]["northing"] + d["x_pos"] * math.sin(angle) + d["y_pos"] * math.cos(angle)
                d["x_speed_utm"] = d["x_speed"] * math.cos(angle) - d["y_speed"] * math.sin(angle)
                d["y_speed_utm"] = d["x_speed"] * math.sin(angle) + d["y_speed"] * math.cos(angle)
                new_dataset.append(d)
        return new_dataset

    def filter_detections(self, dataset, exclude_cat=["bicycle"],
            max_pos=(200, 200), max_speed=(50, 3), approach_only=True):
        to_remove = [d for d in dataset if 
            d["vehicle_class"] in exclude_cat or
            d["x_speed"] > 0 or 
            np.fabs(d["x_speed"]) >= max_speed[0] or
            np.fabs(d["y_speed"]) >= max_speed[1] or
            np.fabs(d["x_pos"]) >= max_pos[0] or
            np.fabs(d["y_pos"]) >= max_pos[1]
            ]
        for r in to_remove:
            dataset.remove(r)
        return dataset

    def leave_only_approaching_cars(self, dataset):
        # remove those with tag cycle or positive speed (away from radar)
        to_remove = [d for d in dataset if d["x_speed"] > 0 or 
            np.fabs(d["x_speed"]) > 50 or np.fabs(d["y_speed"]) > 2 or 
            d["vehicle_class"] == "bicycle"]
        for r in to_remove:
            dataset.remove(r)
        return dataset

    def map_ports_to_radar_names(self, dataset):
        for d in dataset["raw"]:
            if d["radar"] not in self.radar_names:
                found_ports = re.search(r":origin_port, ([\d]{5})",d["radar"])
                if found_ports is None:
                    continue
                else:
                    port = int(found_ports.groups()[0])
                    matching_name = [r["name"] for r in self.radars if r["ethernet_port"] == port]
                    if len(matching_name) == 1:
                        d["radar"] = matching_name[0]
        return dataset
