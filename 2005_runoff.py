#!/usr/bin/env python3
# --------------
# Load modules
# --------------
import csv
import re
from collections import defaultdict


# -----------------------
# Election file details
# -----------------------
election_year = 2005
election_type = "Presidential"
election_round = 2
election_county = "Bong"


# -------------------------------
# Convert raw wide CSVs to long
# -------------------------------
# Load CSV file
f = open("2005/RunoffBongByPollingPlace.csv")
csv_file = csv.reader(f)

# Wide CSVs are in three horizontal chunks with 5 columns each. Separate them
# into individual columns and concatenate into one long list of 5 columns.
col1 = []
col2 = []
col3 = []

for row in csv_file:
    col1.append(row[0:5])
    col2.append(row[5:10])
    col3.append(row[10:15])

csv_long = col1 + col2 + col3

# Get rid of blank rows
csv_long = [row for row in csv_long if row != ['', '', '', '', '']]


# ------------------------
# Group rows by precinct
# ------------------------
# The raw CSVs consist of 10ish rows for each precinct. This separates each
# precinct into a dictionary with each of the sub-rows saved as a list.
raw_results = defaultdict(list)
entry_num = -1

for row in csv_long:
    if "Precinct:" in row[0]:
        entry_num += 1

    raw_results[entry_num].append(row)


# ---------------------------------
# Extract data from each precinct
# ---------------------------------
# Go through each saved precinct/polling place and extract relevant data
clean_results = defaultdict(dict)

for i, entry in raw_results.items():
    candidates = []
    clean_results[i]["election_year"] = election_year
    clean_results[i]["election_type"] = election_type
    clean_results[i]["election_round"] = election_round
    clean_results[i]["election_county"] = election_county
    clean_results[i]["precinct"] = entry[0][0].replace("Precinct: ", "")
    clean_results[i]["polling_place"] = entry[0][2]
    clean_results[i]["address"] = entry[1][0]
    clean_results[i]["registered_voters"] = entry[2][1]
    clean_results[i]["election"] = entry[3][0]

    for cand_row in entry[5:-3]:
        candidates.append((cand_row[0].strip(), cand_row[4]))

    clean_results[i]["candidate_list"] = candidates

    clean_results[i]["valid_votes"] = entry[-3][4]
    clean_results[i]["invalid_votes"] = entry[-2][4]
    clean_results[i]["total_votes"] = entry[-1][4]


# -----------------
# Convert to long
# -----------------
# Expand the dictionary so that there's a row for each candidate in each
# precinct/polling place.
long_results = defaultdict(dict)
entry_num = -1

for key, value in clean_results.items():
    # print(key, value)
    for cand, votes in value["candidate_list"]:
        entry_num += 1
        long_results[entry_num] = {k: v for (k, v) in value.items() if k != "candidate_list"}
        long_results[entry_num]["candidate"] = re.sub("\\(.*\\)", "", cand).strip()
        long_results[entry_num]["cand_party"] = re.search(r"\((.*)\)", cand).group(1)
        long_results[entry_num]["cand_votes"] = votes


# --------------
# Write to CSV
# --------------
# Get the right column order
colnames = ["election_county", "precinct", "polling_place", "address",
            "election", "election_year", "election_type", "election_round",
            "valid_votes", "invalid_votes", "total_votes", "candidate",
            "cand_party", "cand_votes", "registered_voters"]

# Save everything
csv_out = open('{0}.csv'.format(election_county), 'w')
writer = csv.writer(csv_out)

for key, value in long_results.items():
    w = csv.DictWriter(csv_out, fieldnames=colnames)
    if key == 0:
        w.writeheader()
    w.writerow(value)
