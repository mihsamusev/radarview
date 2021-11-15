import numpy as np
import utm
import json 
import os
import argparse
from radarview.trackmanager import RadarTrackManager
from radarview.radar_data_filter import RadarDataFilter


def radars_from_config(cfg):
    """ Loads radar positions and radar names form config"""
    with open(cfg["radars"], "r") as f:
        radars_list = json.load(f)
    radars =  []
    for radar in radars_list:
        if radar["filter"]:
            if radar["filter"]["active"]:
                radars.append(radar)
        else:
            radars.append(radar)
    return radars

def main(args):
    # load json file
    with open(args["config"],"r") as f:
        conf = json.load(f)

    radars = radars_from_config(conf)
    tmanager = RadarTrackManager(conf["center_roi"])
    dfilter = RadarDataFilter(radars)

    i = 0
    with open(conf["dataset"],'r') as f:
        for line in f:
            if i >= args["offset"]:
                datapoint = json.loads(line)
                datapoint = dfilter.map_ports_to_radar_names(datapoint)
                raw_detections = dfilter.filter_detections(datapoint["raw"])
                raw_detections = dfilter.add_utm(raw_detections)
                tmanager.update(raw_detections, datapoint["timestamp"])

                if i > 0 and (i % 1000) == 0:
                    print(f"Obtained {len(tmanager.complete_tracks)} complete tracks from total of {tmanager.track_count} possible tracks")
                i += 1
        print(f"Obtained {len(tmanager.complete_tracks)} complete tracks from total of {tmanager.track_count} possible tracks")

    # save tracks
    path_tracks = os.path.join(conf["tracks_output"], 'tracks.json')
    with open(path_tracks, 'w') as write_file:
        json.dump(
            {"tracks": tmanager.get_complete_tracks()}, write_file)
    print(f"Tracks are saved to:s {path_tracks}")

    # save metadata
    path_metadata = os.path.join(conf["tracks_output"], 'metadata.json')
    with open(path_metadata, 'w') as write_file:
        json.dump(
            tmanager.get_results_dict(), write_file, indent=4)
    print(f"Metadata is saved to: {path_metadata}")


if __name__ == "__main__":
    ag = argparse.ArgumentParser()
    ag.add_argument("-c","--config",required=True,
        help="path to a .json configuration file")
    ag.add_argument("-n","--nrows",default=10000, type=int,
        help="number of radar dat arows to read")
    ag.add_argument("-o","--offset",default=0, type=int,
        help="number of radar data rows to skip before reading")

    args = vars(ag.parse_args())
    main(args)