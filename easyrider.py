import json
import re

from collections import Counter


class BusRider:

    def __init__(self):
        self.data = None
        # accepted chars for obj["stop_type"]
        self.chars = ["S", "O", "F", ""]
        # accepted suffixes for obj["stop_name"]
        self.suffix = ["Road", "Avenue", "Street", "Boulevard"]
        # accepted format for obj["a_time"]
        self.time_format = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        # accepted format for the name of the street -> obj["stop_name"]
        self.name_format = re.compile(r'\b^[A-Z][a-z]+\b')

        # counter used for each stop point to determine if they are transfer stops
        self.lines = {}
        # var used with keys as bus lines -> obj["bus_id"]
        self.bus_stops = {}
        # var used for bus lines with wrong stop types
        self.wrong_lines = {}
        # list of starting bus points
        self.start_stops = []
        # list of transfer bus points -> at least two interconnected bus lines
        self.transfer_stops = []
        # var used to check if on-demand stops overlap other stop types
        self.on_demand_stops = set()
        # list of ending bus points
        self.end_stops = []
        # var used for finding errors in the json input
        self.error_log = {}

    def get_data(self):
        # extract data and assign to respective variables
        json_file = input()
        self.data = json.loads(json_file)

        self.bus_stops = {obj["bus_id"]: [] for obj in self.data}
        self.wrong_lines = {obj["bus_id"]: [] for obj in self.data}
        self.lines = Counter(obj["stop_name"] for obj in self.data)
        self.error_log = {key: 0 for key in self.data[0].keys()}

    def parse_data(self):
        # verify that the data types of each object's details match the doc
        # add in the error log if not
        for obj in self.data:
            for key, value in obj.items():
                if key in ("bus_id", "stop_id", "next_stop"):
                    if not isinstance(value, int):
                        self.error_log[key] += 1

                elif key in ("stop_name", "a_time"):
                    if not isinstance(value, str):
                        self.error_log[key] += 1

                elif key == "stop_type":
                    if value not in self.chars:
                        self.error_log[key] += 1

    def check_validity(self):
        # verify the name and time formats for the respective types using regex
        # add in the error log if not
        for obj in self.data:
            for key, value in obj.items():
                if key == "stop_name":
                    try:
                        value = re.split(r'(Road|Avenue|Boulevard|Street)', value)
                        name = value[0]
                        suffix = value[1]

                        if len(value) > 2 and value[-1] != "":
                            self.error_log[key] += 1

                        match = re.match(self.name_format, name)
                        if match is None:
                            self.error_log[key] += 1

                        if suffix not in self.suffix:
                            self.error_log[key] += 1

                    except IndexError:
                        self.error_log[key] += 1

                elif key == "a_time":
                    match = re.match(self.time_format, value)
                    if match is None:
                        self.error_log[key] += 1

    def find_bus_stops(self):
        # append the stop points for each bus line
        for obj in self.data:
            for key, value in self.bus_stops.items():
                if obj["bus_id"] == key and obj["stop_name"] not in value:
                    self.bus_stops[key].append(obj["stop_name"])

    def verify_bus_stops(self):
        # append the stop types for each stop point
        for obj in self.data:
            for key, value in self.wrong_lines.items():
                if obj["bus_id"] == key:
                    self.wrong_lines[key].append(obj["stop_type"])

                    # add the on-demand stop points that may overlap with other stop types
                    if obj["stop_type"] == "O":
                        self.on_demand_stops.add(obj["stop_name"])

        # verify that each bus line has a starting and ending point of the route
        for obj in self.data:
            for key, value in self.wrong_lines.items():
                if "S" not in value or "F" not in value:
                    print(f"There is no start or end stop for the line: {key}")

                # append the start and end points
                else:
                    if obj["bus_id"] == key and obj["stop_type"] == "S":
                        self.start_stops.append(obj["stop_name"])
                    if obj["bus_id"] == key and obj["stop_type"] == "F":
                        self.end_stops.append(obj["stop_name"])

    def verify_transfer_stops(self):
        # append transfer points
        for key, value in self.lines.items():
            if value > 1:
                self.transfer_stops.append(key)

    def verify_on_demand_stops(self):
        # verify if on-demand points intersect start, transfer, or end points
        common_stations_start = self.on_demand_stops.intersection(self.start_stops)
        common_stations_transfer = self.on_demand_stops.intersection(self.transfer_stops)
        common_stations_end = self.on_demand_stops.intersection(self.end_stops)

        print("On demand stops test:")
        if len(common_stations_start) > 0:
            print(f"Wrong stop type: {sorted(list(common_stations_start))}")
        elif len(common_stations_transfer) > 0:
            print(f"Wrong stop type: {sorted(list(common_stations_transfer))}")
        elif len(common_stations_end) > 0:
            print(f"Wrong stop type: {sorted(list(common_stations_end))}")
        else:
            print("OK")

    def arrival_time_check(self):
        # verify if the arrival times are in ascending order for each bus line
        stops_timing = dict.fromkeys(self.bus_stops, "00:00")
        errors_dict = dict()

        for obj in self.data:
            line_id = obj["bus_id"]
            time = obj["a_time"]
            if (int(stops_timing[line_id][0:2]) * 60
                    + int(stops_timing[line_id][3:5])) < (int(time[0:2]) * 60 + int(time[3:5])):
                stops_timing[line_id] = time
                pass
            else:
                # if the next arrival time is before or at the moment of the previous one
                # append the stop point that raised errors
                if line_id not in errors_dict:
                    errors_dict[line_id] = obj["stop_name"]
                else:
                    continue

        print("Arrival time test:")
        if len(errors_dict) == 0:
            print("OK")
        else:
            for line in errors_dict:
                print(f"bus_id line {line}: wrong time on station {errors_dict[line]}")
            return False

    def print_start_end(self):
        temp_start_stops = [*set(self.start_stops)]
        temp_end_stops = [*set(self.end_stops)]

        print(f"Start stops: {len(temp_start_stops)} {sorted(temp_start_stops)}")
        print(f"Transfer stops: {len(self.transfer_stops)} {sorted(self.transfer_stops)}")
        print(f"Finish stops: {len(temp_end_stops)} {sorted(temp_end_stops)}")

    def print_bus_stops(self):
        print("Line names and number of stops:")

        for k, v in self.bus_stops.items():
            print(f"bus_id: {k}, stops: {len(v)}")

    def print_results(self):
        print(f"Type and required field validation: {sum(self.error_log.values())} errors")

        for k, v in self.error_log.items():
            if k in ("stop_name", "stop_type", "a_time"):
                print(f"{k}: {v}")


if __name__ == "__main__":
    bus = BusRider()
    bus.get_data()
    bus.parse_data()
    bus.verify_bus_stops()
    bus.verify_transfer_stops()
    bus.verify_on_demand_stops()
