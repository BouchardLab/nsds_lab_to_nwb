#!/bin/bash

SAVE_PATH="_test/"
BLOCK_NAME="RVG02_B09"
BLOCK_META="../tests/_data/RVG02/block_data.csv"

python generate_nwb.py  $SAVE_PATH $BLOCK_NAME $BLOCK_META
