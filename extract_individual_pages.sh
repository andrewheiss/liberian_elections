#!/usr/bin/env sh
export RBENV_VERSION=jruby-1.7.19

PDF_FILE="list_2014.pdf"

NUM_PAGES=$(/usr/local/bin/mutool info -m $PDF_FILE | grep Pages | awk '{print $2}')

for i in $(seq 1 $NUM_PAGES); do 
    echo "Extracting page ${i}"
    # 2005
    # tabula -p $i -a 83.62162162162161,34.306306306306304,107.2072072072072,564.9819819819819 -o output/${i}_info.csv $PDF_FILE 2> /dev/null
    # tabula -p $i -a 156.5225225225225,34.306306306306304,783.6846846846846,564.9819819819819 -o output/${i}_data.csv $PDF_FILE 2> /dev/null

    # 2011
    # tabula -p $i -a 71.82882882882882,18.225225225225223,94.34234234234233,581.063063063063 -o output/${i}_info.csv $PDF_FILE 2> /dev/null
    # tabula -p $i -a 138.2972972972973,17.153153153153152,802.9819819819819,579.990990990991 -o output/${i}_data.csv $PDF_FILE 2> /dev/null

    # 2014
    # Tabula struggles with the general information for 2014, so this grabs too
    # much data on purpose, which (unfortunately) means more post-extraction
    # cleaning. ¯\_(ツ)_/¯
    tabula -p $i -a 109.03603603603604,40.73873873873874,164.15315315315314,612.2792792792793 -o output/${i}_info.csv $PDF_FILE 2> /dev/null
    tabula -p $i -a 154.56756756756755,44.333333333333336,817.1711711711712,605.09009009009 -o output/${i}_data.csv $PDF_FILE 2> /dev/null
done

echo "All done!"
