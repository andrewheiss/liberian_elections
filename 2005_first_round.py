#!/usr/bin/env python3
# --------------
# Load modules
# --------------
import csv
import re
from collections import defaultdict
import sys


# -----------------------
# Election file details
# -----------------------
election_year = 2005
election_round = 1
election_county = "GrandCapeMount"


# -------------------------------
# Convert raw wide CSVs to long
# -------------------------------
# Load CSV file
f = open("2005/1st round/Raw CSVs/GrandCapeMountByPollingPlace.csv")
csv_file = csv.reader(f)


# ------------------------
# Group rows by precinct
# ------------------------
# The raw CSVs consist of 30ish rows for each precinct (which correspond to one
# page in the PDF. This separates each precinct into a dictionary with each of
# the sub-rows saved as a list.
raw_results = defaultdict(list)
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
def parse_precinct(raw, j):
    clean_results[j]["election_year"] = election_year
    clean_results[j]["election_round"] = election_round
    clean_results[j]["election_county"] = election_county

    # First two rows have polling place and turnout data
    prec_metadata = [raw[i] for i in range(0, 2)]
    elec_metadata = [raw[i] for i in range(2, 4)]
    actual_data = [raw[i] for i in range(4, len(raw))]

    clean_results[j]["precinct"] = prec_metadata[0][0].replace("Precinct: ", "")
    clean_results[j]["polling_place"] = prec_metadata[0][2].strip()
    clean_results[j]["address"] = prec_metadata[1][0]

    # Strip out the columns with polling place data and collapse columns by
    # removing empty cells
    # TODO: Get turnout demographics someday, but they're tricky to parse
    turnout = [filter(None, row[5:]) for row in prec_metadata]
    clean_results[j]["registered_voters"] = turnout[0][0].replace("Total: ", "").strip()

    # Strip out the columns after the presidential results,
    # since those are obvious, and remove empty cells
    elec_metadata = [filter(None, row[2:]) for row in elec_metadata]
    clean_results[j]["senate_district"] = elec_metadata[1][0].strip()
    clean_results[j]["house_district"] = elec_metadata[1][1].strip()

    # Find first ("Candidate") and last ("Votes") columns for election results
    headers = actual_data[0]
    start_cols = [i for i, x in enumerate(headers) if "Candidate" in x]
    end_cols = [i for i, x in enumerate(headers) if "Votes" in x]

    # Extract the columns between first and last indexes
    pres_data = [col[:][start_cols[0]:end_cols[0]+1] for col in actual_data]
    senate_data = [col[:][start_cols[1]:end_cols[1]+1] for col in actual_data]
    house_data = [col[:][start_cols[2]:end_cols[2]+1] for col in actual_data]

    # Strip empty cells and remove headers
    pres_data = [filter(None, row[:]) for row in pres_data[1:]]
    senate_data = [filter(None, row[:]) for row in senate_data[1:]]
    house_data = [filter(None, row[:]) for row in house_data[1:]]

    # Remove empty rows
    pres_data = [row[:] for row in filter(None, pres_data)]
    senate_data = [row[:] for row in filter(None, senate_data)]
    house_data = [row[:] for row in filter(None, house_data)]

    # print(senate_data)

    # Separate candidate names and totals
    # print(pres_data[0:-3])
    pres_cands = [(x[0], x[1]) for x in pres_data[0:-3]]
    senate_cands = [(x[0], x[1]) for x in senate_data[0:-3]]
    house_cands = [(x[0], x[1]) for x in house_data[0:-3]]

    # Save candidate names
    clean_results[j]["pres_cands_list"] = pres_cands
    clean_results[j]["senate_cands_list"] = senate_cands
    clean_results[j]["house_cands_list"] = house_cands

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
