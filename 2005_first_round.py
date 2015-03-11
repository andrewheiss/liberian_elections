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
election_type = "1st round"
election_round = 1
election_county = "Bong"


# -------------------------------
# Convert raw wide CSVs to long
# -------------------------------
# Load CSV file
f = open("2005/1st round/Raw CSVs/bomi_small.csv")
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

# print(raw_results)

clean_results = defaultdict(dict)

def parse_precinct(raw):
    # First two rows have polling place and turnout data
    prec_metadata = [raw[i] for i in range(0, 2)]
    elec_metadata = [raw[i] for i in range(2, 4)]
    actual_data = [raw[i] for i in range(4, len(raw))]

    clean_results[0]["precinct"] = prec_metadata[0][0].replace("Precinct: ", "")
    clean_results[0]["polling_place"] = prec_metadata[0][2].strip()
    clean_results[0]["address"] = prec_metadata[1][0]

    # Strip out the columns with polling place data and collapse columns by
    # removing empty cells
    # TODO: Get turnout demographics someday, but they're tricky to parse
    turnout = [filter(None, row[5:]) for row in prec_metadata]
    clean_results[0]["turnout"] = turnout[0][0].replace("Total: ", "").strip()

    # Strip out the columns after the presidential results,
    # since those are obvious, and remove empty cells
    elec_metadata = [filter(None, row[2:]) for row in elec_metadata]
    clean_results[0]["senate_election"] = elec_metadata[1][0].strip()
    clean_results[0]["house_election"] = elec_metadata[1][1].strip()

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

    # Separate candidate names and totals
    pres_cands = [(x[0], x[1]) for x in pres_data[0:-3]]
    senate_cands = [(x[0], x[1]) for x in senate_data[0:-3]]
    house_cands = [(x[0], x[1]) for x in house_data[0:-3]]

    # Save candidate names
    clean_results[0]["pres_cands_list"] = pres_cands
    clean_results[0]["senate_cands_list"] = senate_cands
    clean_results[0]["house_cands_list"] = house_cands

    # Get and save vote totals
    clean_results[0]["pres_valid_votes"] = pres_data[-3][1]
    clean_results[0]["pres_invalid_votes"] = pres_data[-2][1]
    clean_results[0]["pres_total_votes"] = pres_data[-1][1]

    clean_results[0]["senate_valid_votes"] = senate_data[-3][1]
    clean_results[0]["senate_invalid_votes"] = senate_data[-2][1]
    clean_results[0]["senate_total_votes"] = senate_data[-1][1]

    clean_results[0]["house_valid_votes"] = house_data[-3][1]
    clean_results[0]["house_invalid_votes"] = house_data[-2][1]
    clean_results[0]["house_total_votes"] = house_data[-1][1]


parse_precinct(raw_results[0])
print(clean_results)


sys.exit()


# Wide CSVs are in three horizontal chunks for each of the elections (presidential, senate, and house)
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
