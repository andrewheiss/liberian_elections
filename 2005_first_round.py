#!/usr/bin/env python3
# --------------
# Load modules
# --------------
import csv
import re
from collections import defaultdict, OrderedDict
import sys

# via http://stackoverflow.com/a/4127426/120898
class OrderedDefaultdict(OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else ()
        return self.__class__, args, None, None, self.iteritems()

# -----------------------
# Election file details
# -----------------------
election_year = 2005
election_round = 1
election_county = "Maryland"


# -------------------------------
# Convert raw wide CSVs to long
# -------------------------------
# Load CSV file
f = open("2005/1st round/Raw CSVs/MarylandByPollingPlace.csv")
csv_file = csv.reader(f)


# ------------------------
# Group rows by precinct
# ------------------------
# The raw CSVs consist of 30ish rows for each precinct (which correspond to one
# page in the PDF. This separates each precinct into a dictionary with each of
# the sub-rows saved as a list.
# raw_results = defaultdict(list)
raw_results = OrderedDefaultdict(list)
entry_num = -1

for row in csv_file:
    if "Precinct:" in row[0]:
        entry_num += 1

    raw_results[entry_num].append(row)


# ---------------------------------
# Extract data from each precinct
# ---------------------------------
# Arguments:
#   raw: a list of lists from raw_results
#   j: index to be used for clean_results

# TODO: Track the last list of senate and house candidates and districts, so that if there aren't any, use their names
senate_district_last = ""
house_district_last = ""
senate_cands_list_last = []
house_cands_list_last = []

def strip_empty(x):
    return(list(filter(None, x)))

def parse_precinct(raw, j):
    # Yeah, globals are lazy and super evil, but I don't want to make
    # this into a full blown class, so ¯\_(ツ)_/¯
    global senate_district_last
    global house_district_last
    global senate_cands_list_last
    global house_cands_list_last

    clean_results[j]["election_year"] = election_year
    clean_results[j]["election_round"] = election_round
    clean_results[j]["election_county"] = election_county

    # Check if there are only presidential results
    only_pres = False if raw[2][0] == "" else True

    # First two rows have polling place and turnout data
    prec_metadata = [raw[i] for i in range(0, 2)]

    # Separate the remaining rows
    # When there are just presidential results, election metadata is
    # only on row 3, with the rest of the data on rows 4-end
    # When there are presidential, senate, and house results, election
    # metadata is on rows 3-4, with the rest on 5-end
    if only_pres:
        elec_metadata = raw[2]
        actual_data = [raw[i] for i in range(3, len(raw))]
    else:
        elec_metadata = [raw[i] for i in range(2, 4)]
        actual_data = [raw[i] for i in range(4, len(raw))]

    # Save precinct information
    clean_results[j]["precinct"] = prec_metadata[0][0].replace("Precinct: ", "")
    clean_results[j]["polling_place"] = prec_metadata[0][2].strip()
    clean_results[j]["address"] = prec_metadata[1][0]

    # Strip out the columns with polling place data and collapse columns by
    # removing empty cells
    # TODO: Get turnout demographics someday, but they're tricky to parse
    turnout = [strip_empty(row[3:]) for row in prec_metadata]

    if only_pres:
        # Presidential-only pages put the turnout number in a separate cell
        actual_turnout = turnout[0][1].strip()
    else:
        actual_turnout = turnout[0][0].replace("Total: ", "").strip()

    # Save the turnout numbers
    clean_results[j]["registered_voters"] = actual_turnout

    # Get election district information
    if only_pres:
        # If there are only presidential results, use the last senate
        # and house districts
        clean_results[j]["senate_district"] = senate_district_last
        clean_results[j]["house_district"] = house_district_last
    else:
        # Strip out the columns after the presidential results,
        # since those are obvious, and remove empty cells
        elec_metadata = [strip_empty(row[2:]) for row in elec_metadata]

        senate_district = elec_metadata[1][0].strip()
        clean_results[j]["senate_district"] = senate_district
        senate_district_last = senate_district

        house_district = elec_metadata[1][1].strip()
        clean_results[j]["house_district"] = house_district
        house_district_last = house_district

    if only_pres:
        # Find first ("Candidate") and last ("Votes") columns for election results
        headers = actual_data[0]
        start_cols = [i for i, x in enumerate(headers) if "Candidate" in x]
        end_cols = [i for i, x in enumerate(headers) if "Votes" in x]

        # Extract column(s)
        pres_data = [col[:][start_cols[0]:end_cols[0]+1] for col in actual_data]

        # Remove header and empty cells
        pres_data = [strip_empty(row[:]) for row in pres_data[1:]]

        # Remove empty rows
        pres_data = [row[:] for row in strip_empty(pres_data)]

        # Separate candidate names and totals
        pres_cands = [(x[0], x[1]) for x in pres_data[0:-3]]

        # Save everything
        clean_results[j]["pres_cands_list"] = pres_cands
        clean_results[j]["pres_valid_votes"] = pres_data[-3][1]
        clean_results[j]["pres_invalid_votes"] = pres_data[-2][1]
        clean_results[j]["pres_total_votes"] = pres_data[-1][1]

        # Save previous senate and house candidate names
        # Set totals to 0, since there weren't any results...
        senate_cands = [(x[0], 0) for x in senate_cands_list_last]
        house_cands = [(x[0], 0) for x in house_cands_list_last]

        clean_results[j]["senate_cands_list"] = senate_cands
        clean_results[j]["house_cands_list"] = house_cands

        clean_results[j]["senate_valid_votes"] = 0
        clean_results[j]["senate_invalid_votes"] = 0
        clean_results[j]["senate_total_votes"] = 0

        clean_results[j]["house_valid_votes"] = 0
        clean_results[j]["house_invalid_votes"] = 0
        clean_results[j]["house_total_votes"] = 0
    else:
        # Find first ("Candidate") and last ("Votes") columns for election results
        headers = actual_data[0]
        start_cols = [i for i, x in enumerate(headers) if "Candidate" in x]
        end_cols = [i for i, x in enumerate(headers) if "Votes" in x]

        # Extract the columns between first and last indexes
        pres_data = [col[:][start_cols[0]:end_cols[0]+1] for col in actual_data]
        senate_data = [col[:][start_cols[1]:end_cols[1]+1] for col in actual_data]
        house_data = [col[:][start_cols[2]:end_cols[2]+1] for col in actual_data]

        # Strip empty cells and remove headers
        pres_data = [strip_empty(row[:]) for row in pres_data[1:]]
        senate_data = [strip_empty(row[:]) for row in senate_data[1:]]
        house_data = [strip_empty(row[:]) for row in house_data[1:]]

        # Remove empty rows
        pres_data = [row[:] for row in strip_empty(pres_data)]
        senate_data = [row[:] for row in strip_empty(senate_data)]
        house_data = [row[:] for row in strip_empty(house_data)]

        # Separate candidate names and totals
        # Get rid of all non-digits in presidential candidate results, since
        # some have senate candidate names in them too
        pres_cands = [(x[0], re.sub(r"\D+", "", x[1])) for x in pres_data[0:-3]]
        senate_cands = [(x[0], x[1]) for x in senate_data[0:-3]]
        house_cands = [(x[0], x[1]) for x in house_data[0:-3]]

        # Save candidate names
        clean_results[j]["pres_cands_list"] = pres_cands
        clean_results[j]["senate_cands_list"] = senate_cands
        clean_results[j]["house_cands_list"] = house_cands

        # Save lists to global vars
        senate_cands_list_last = senate_cands
        house_cands_list_last = house_cands

        # Get and save vote totals
        clean_results[j]["pres_valid_votes"] = pres_data[-3][1]
        clean_results[j]["pres_invalid_votes"] = pres_data[-2][1]
        clean_results[j]["pres_total_votes"] = pres_data[-1][1]

        clean_results[j]["senate_valid_votes"] = senate_data[-3][1]
        clean_results[j]["senate_invalid_votes"] = senate_data[-2][1]
        clean_results[j]["senate_total_votes"] = senate_data[-1][1]

        clean_results[j]["house_valid_votes"] = house_data[-3][1]
        clean_results[j]["house_invalid_votes"] = house_data[-2][1]
        clean_results[j]["house_total_votes"] = house_data[-1][1]


# Loop through all the raw precints, extract data, and save to clean_results
clean_results = defaultdict(dict)
for j, entry in raw_results.items():
    print(j, entry[0][0], entry[0][2])
    parse_precinct(raw_results[j], j)


# -----------------
# Convert to long
# -----------------
long_results = defaultdict(dict)
entry_num = -1

for key, value in clean_results.items():
    for pres_cand, votes in value["pres_cands_list"]:
        entry_num += 1
        # Save all fields
        long_results[entry_num] = {k: v for (k, v) in value.items()}

        # Expand candidate data
        long_results[entry_num]["candidate"] = re.sub("\\(.*\\)", "", pres_cand).strip()
        long_results[entry_num]["cand_party"] = re.search(r"\((.*)\)", pres_cand).group(1)
        long_results[entry_num]["cand_votes"] = votes
        long_results[entry_num]["cand_race"] = "Presidential"

    for senate_cand, votes in value["senate_cands_list"]:
        entry_num += 1
        # Save all fields
        long_results[entry_num] = {k: v for (k, v) in value.items()}

        # Expand candidate data
        long_results[entry_num]["candidate"] = re.sub("\\(.*\\)", "", senate_cand).strip()
        long_results[entry_num]["cand_party"] = re.search(r"\((.*)\)", senate_cand).group(1)
        long_results[entry_num]["cand_votes"] = votes
        long_results[entry_num]["cand_race"] = "Senate"

    for house_cand, votes in value["house_cands_list"]:
        entry_num += 1
        # Save all fields
        long_results[entry_num] = {k: v for (k, v) in value.items()}

        # Expand candidate data
        long_results[entry_num]["candidate"] = re.sub("\\(.*\\)", "", house_cand).strip()
        long_results[entry_num]["cand_party"] = re.search(r"\((.*)\)", house_cand).group(1)
        long_results[entry_num]["cand_votes"] = votes
        long_results[entry_num]["cand_race"] = "House"

# Get rid of list columns
for v in long_results.values():
    del v['pres_cands_list']
    del v['senate_cands_list']
    del v['house_cands_list']


# --------------
# Write to CSV
# --------------
colnames = ["election_county", "precinct", "polling_place", "address",
            "election_year", "election_round",
            "senate_district", "house_district",
            "pres_valid_votes", "pres_invalid_votes", "pres_total_votes",
            "senate_valid_votes", "senate_invalid_votes", "senate_total_votes",
            "house_valid_votes", "house_invalid_votes", "house_total_votes",
            "candidate", "cand_votes", "cand_party", "cand_race",
            "registered_voters"]

csv_out = open('{0}.csv'.format(election_county), 'w')
writer = csv.writer(csv_out)

for key, value in long_results.items():
    w = csv.DictWriter(csv_out, colnames)
    if key == 0:
        w.writeheader()
    w.writerow(value)
