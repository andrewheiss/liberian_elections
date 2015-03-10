#!/bin/bash
export RBENV_VERSION=jruby-1.7.19
for f in 2005/*.pdf; do
    # 2005 Presidential runoff
    tabula -p all -a 72.17142857142858,34.582142857142856,236.06071428571428,816.4392857142857 -o $f.csv $f
done
