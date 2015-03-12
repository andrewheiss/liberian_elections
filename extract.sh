#!/bin/bash
# https://github.com/tabulapdf/tabula-extractor/wiki/Using-the-command-line-tabula-extractor-tool
export RBENV_VERSION=jruby-1.7.19
for f in PDFs/*.pdf; do
    # echo $f
    # 2005 1st round
    # tabula -p all -a 70.66785714285714,39.09285714285714,562.3357142857143,811.9285714285714 -o $f.csv $f

    # 2005 Presidential runoff
    # tabula -p all -a 72.17142857142858,34.582142857142856,236.06071428571428,816.4392857142857 -o $f.csv $f

    # 2005 precinct lists
    # tabula -p all -a 87.125,43.5625,786.25,555.6875 -o $f.csv $f

    # 2011 precinct lists
    # tabula -p all -a 73.3125,13.8125,805.375,584.375 -o $f.csv $f

    # 2014 precinct lists
    tabula -p all -a 110.4375,41.5625,820.5625,609.1875 -o $f.csv $f
done
