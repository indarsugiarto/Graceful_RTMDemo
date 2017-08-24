#!/bin/bash

#Use this simple script to test the current PLL configuration
#It is from ~/Projects/SpiNN/general/miscTest/readPLL

ybug spin5 << EOF
app_load readPLL.apx . 3 16
sleep 2
app_stop 16
EOF

