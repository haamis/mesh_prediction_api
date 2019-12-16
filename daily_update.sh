#!/bin/bash

curr_wrk_dir=$(pwd)
base_folder=/change/me
prev_folder=$base_folder$(python check_previous_folder.py -i $base_folder)
echo $prev_folder

date_text=$(date +'%Y_%m_%d/')
curr_folder=$base_folder$date_text
mkdir $curr_folder
echo $curr_folder

orig_ext=original_PubMed/
orig_folder=$curr_folder$orig_ext
mkdir $orig_folder

python download_pubmed.py -c $curr_folder -p $prev_folder
python check_pubmed_md5sum.py -c $curr_folder

