#!/usr/bin/env python3
# --------------
# Load modules
# --------------
from bs4 import BeautifulSoup
from collections import defaultdict
from itertools import chain
from random import choice
from decimal import Decimal
from time import sleep
import re
import csv
import urllib.request
import logging


def clean_num(x):
    return(int(re.sub(r"\D+", "", x)))


def get_url(url):
    user_agents = [
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36',
      'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'
    ]

    agent = choice(user_agents)
    wait = choice(range(1, 3))

    response = urllib.request.Request(url, headers={'User-Agent': agent})
    handler = urllib.request.urlopen(response).read()

    sleep(wait)

    return(handler)


def parse_precinct(url, house_district, voters, place_name, turnout):
    global csv_started

    metadata = {}
    metadata['house_district'] = house_district
    metadata['county_voters'] = voters
    metadata['county_turnout'] = turnout
    metadata['address'] = place_name

    soup = BeautifulSoup(get_url(url))

    # The actual results are in a table with a PNG background
    results_section = soup.find('td', background='../images/main_back.png')

    # Some URLs don't work...
    if not results_section:
        logging.error("{0} doesn't exist!".format(url))
        return(False)

    # That table is actually 2 tables---the results are in the 2nd one
    results_section = results_section.findAll('table')[1]

    # And *that* table has 3 rows, but only the 2nd is important
    results_section = results_section.findAll('tr')[1]

    # The results are in 2 tables:
    # 1. Precinct information
    # 2. Results for elections

    results = results_section.findAll('table')

    # Deal with precinct table and save election metadata
    election_county_raw = results[0].select('h2')[0].contents[0]
    metadata['election_county'] = re.sub(r" County", "", election_county_raw)

    precinct_raw = results[0].select('h4')[0].contents[0]
    metadata['precinct'] = clean_num(precinct_raw)

    metadata['year'] = 2011

    # Deal with actual results
    actual_results = results[1].select('.res table')

    if len(actual_results) > 1:
        metadata['election_round'] = 1

        # Presidential data
        pres_data_raw = extract_data(actual_results[0])
        pres_data_long = convert_to_long(pres_data_raw, "Presidential", metadata)

        # Senate data
        senate_data_raw = extract_data(actual_results[1])
        senate_data_long = convert_to_long(senate_data_raw, "Senate", metadata)

        # House data
        house_data_raw = extract_data(actual_results[2])
        house_data_long = convert_to_long(house_data_raw, "House", metadata)

        # Combine the three into one big long dictionary
        final_results = defaultdict(dict)
        entry_num = -1

        for key, value in chain(pres_data_long.items(),
                senate_data_long.items(), house_data_long.items()):
            entry_num += 1
            final_results[entry_num] = value
    else:
        metadata['election_round'] = 2

        # Presidential data
        pres_data_raw = extract_data(actual_results[0])
        pres_data_long = convert_to_long(pres_data_raw, "Presidential", metadata)
        final_results = pres_data_long

    logging.info("Saved {0}, {1} (round {2}): {3}".format(metadata['election_county'],
                                                    metadata['address'],
                                                    metadata['election_round'],
                                                    url))

    fieldnames = ['election_county', 'precinct', 'polling_place', 'address',
                  'election_year', 'election_round', 'senate_district',
                  'house_district', 'valid_votes', 'invalid_votes',
                  'total_votes', 'candidate', 'cand_votes', 'cand_party',
                  'cand_race', 'county_voters', 'county_turnout']

    for key, value in final_results.items():
        w = csv.DictWriter(open('2011.csv', 'a'), fieldnames)
        if csv_started is False:
            w.writeheader()
            csv_started = True
        w.writerow(value)


def convert_to_long(raw_data, cand_race, metadata):
    long_results = defaultdict(dict)
    entry_num = -1

    # Loop through each candidate and expand their results per polling place
    for x in raw_data['cand_dict']:
        for i in range(0, len(raw_data['polling_places'])):
            entry_num += 1

            # Save general information
            house_district = "{0}, Electoral District {1}".format(
                metadata['election_county'], metadata['house_district'])

            long_results[entry_num]['cand_race'] = cand_race
            long_results[entry_num]['election_round'] = metadata['election_round']
            long_results[entry_num]['election_county'] = metadata['election_county']
            long_results[entry_num]['senate_district'] = metadata['election_county']
            long_results[entry_num]['address'] = metadata['address']
            long_results[entry_num]['county_voters'] = metadata['county_voters']
            long_results[entry_num]['county_turnout'] = metadata['county_turnout']
            long_results[entry_num]['house_district'] = house_district
            long_results[entry_num]['precinct'] = metadata['precinct']
            long_results[entry_num]['election_year'] = metadata['year']
            long_results[entry_num]['polling_place'] = raw_data['polling_places'][i]

            # Expand candidate information
            long_results[entry_num]['candidate'] = x['cand_name']
            long_results[entry_num]['cand_party'] = x['cand_party']
            long_results[entry_num]['cand_votes'] = x['cand_votes'][i]

            # Expand vote information
            long_results[entry_num]['valid_votes'] = raw_data['valid'][i]
            long_results[entry_num]['invalid_votes'] = raw_data['invalid'][i]
            long_results[entry_num]['total_votes'] = raw_data['total'][i]

    return(long_results)


def extract_data(table):
    clean_results = {}
    cand_list = []

    # Parse polling place information
    polling_places = table.findAll('th')
    polling_places = [clean_num(place.contents[0]) for place in polling_places[1:]]
    clean_results['polling_places'] = polling_places

    # Loop through each row in the table and save relevant data
    for row in table.findAll('tr'):
        results = row.findAll('td')
        cand_dict = {}

        # The first column has data like: Candidate name (Party)
        cand_name_party = results[0].contents[0]

        # If the row is not for a candidate, it has total vote information
        # Save vote information to clean_results dict
        if re.search("valid|total", cand_name_party, re.I | re.M):
            if cand_name_party == "Total Valid":
                valid = [votes.contents[0].strip() for votes in results[1:]]
                clean_results['valid'] = valid

            if cand_name_party == "Invalid":
                invalid = [votes.contents[0].strip() for votes in results[1:]]
                clean_results['invalid'] = invalid

            if cand_name_party == "Total":
                total = [votes.contents[0].strip() for votes in results[1:]]
                clean_results['total'] = total
        # Save candidate information as dict to cand_list
        else:
            cand_name = re.sub(r"\(.*\)", "", cand_name_party).strip()
            cand_party = re.search(r"\((.*)\)", cand_name_party).group(1)
            cand_votes = [votes.contents[0].strip() for votes in results[1:]]

            cand_dict['cand_name'] = cand_name
            cand_dict['cand_party'] = cand_party
            cand_dict['cand_votes'] = cand_votes

            cand_list.append(cand_dict)

    # Include final cand_list in cand_dict
    clean_results['cand_dict'] = cand_list

    # All done
    return(clean_results)


# Returns a list of tuples: [(County name, full URL), (..., ...)]
def get_county_list():
    # Yeah, yeah, yeah. I know.
    global base_url

    # Parse HTML
    full_url = base_url + "results.html"
    soup = BeautifulSoup(get_url(full_url))
    logging.info("Getting the list of all the "
                 "counties from {0}".format(full_url))

    # All the counties are <h2>s wrapped in <a>s
    county_tags = soup.findAll('h2')
    counties = [(tag.contents[0], base_url + tag.parent['href']) for tag in county_tags]
    return(counties)


# Accepts a (County name, URL) tuple
# Returns a dictionary with:
#   * county: County name
#   * first_round: Tuple of (votes, turnout)
#   * runoff: Tuple of (votes, turnout)
#   * first_round_link: URL to results by polling place
#   * runoff_link: URL to results by polling place
def parse_county(county_url):
    # Global again. ¯\_(ツ)_/¯
    global base_url

    logging.info("Parsing information for {0} "
                 "county from {1}".format(county_url[0], county_url[1]))

    soup = BeautifulSoup(get_url(county_url[1]))

    # There are 3 <h2>s on the page: the county name and turnout numbers for
    # both rounds of the election. We just need the last two.
    turnout_raw = [x.contents[0] for x in soup.findAll('h2')[1:]]

    # Extract turnout data from headers
    # All follow this pattern: "Turnout: 22,428 (47.1%)"
    # So use regex to get the two numbers as groups
    pattern = re.compile(r"Turnout: ([\d,]+) \(([\d\.]+)%\)")
    turnout_numbers = [re.search(pattern, x).groups() for x in turnout_raw]

    # float(Decimal(x)) to make Python treat the decimal number right
    turnout_clean = [(int(x[0].replace(',', '')), float(Decimal(x[1])/100))
                     for x in turnout_numbers]

    # Get "Results by Polling Place" links
    polling_places_raw = soup(text="Results by Polling Place")
    polling_places = [base_url + x.parent.parent['href'] for x in polling_places_raw]

    # Nimba has a bug and only shows the first round on the main results page
    # The hardcoded results come from the interactive map on the home page:
    # http://www.necliberia.org/results2011/

    # The link for the by-polling-place results works, it's just not on the
    # county page, so it has to be prepended to the list of polling place URLs.
    if len(turnout_clean) == 1:
        runoff = (120683, 0.524)
        polling_places.insert(0, 'http://www.necliberia.org/results2011/county_33_vpr.html')
    else:
        runoff = turnout_clean[1]

    # Save to dictionary
    turnout = {}
    turnout['county'] = county_url[0]
    turnout['first_round'] = turnout_clean[0]
    turnout['runoff'] = runoff
    turnout['first_round_link'] = polling_places[1]
    turnout['runoff_link'] = polling_places[0]

    return(turnout)


# Accepts turnout dictionary from parse_county()
# Returns nothing, since it calls parse_precinct(), which writes to CSV
def parse_county_precincts(county):
    # Boo globals.
    global base_url

    loop = [(county['first_round'], county['first_round_link']),
            (county['runoff'], county['runoff_link'])]

    for x in loop:
        precincts = []

        soup = BeautifulSoup(get_url(x[1]))

        # The actual content is in a table with a PNG background
        precinct_list = soup.find('td', background='images/main_back.png')

        # That table is actually 2 tables---we care about the 2nd one
        precinct_list = precinct_list.findAll('table')[1]

        # And *that* table has 3 rows, but only the 2nd is important
        precinct_list = precinct_list.findAll('tr')[1]

        # Finally, the table is in a div with class="res"
        precinct_list = precinct_list.select('.res table')

        for row in precinct_list[0].findAll('tr'):
            cells = row.findAll('td')

            if cells is not None:
                precinct_name = cells[1].contents[0]
                precinct_url = base_url + cells[0].select('a')[0]['href']
                precincts.append((precinct_name, precinct_url))

        for precinct in precincts:
            parse_precinct(precinct[1],  # url
                           "?",  # house_district
                           county['first_round'][0],  # voters
                           precinct[0],  # place_name
                           county['first_round'][1])  # turnout


# --------------
# Actual logic
# --------------
# Set up log
logging.basicConfig(filename='2011.log', filemode='w', level=logging.DEBUG,
                    format='%(levelname)s %(asctime)s: %(message)s')
logging.captureWarnings(True)

# GLobal variables
base_url = "http://www.necliberia.org/results2011/"
csv_started = False

# Parse each county for total voters and turnout
county_details = [parse_county(county) for county in get_county_list()]

# Go through each county and save precinct-level vote information to CSV
for county in county_details:
    parse_county_precincts(county)

logging.info("All done!")
