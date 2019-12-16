#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import glob


def check_latest_date(in_folder):
    folder_dates = [x.split("/")[-2] for x in glob.glob(in_folder + "*/")]
    folder_dates.sort(reverse=True)
    print folder_dates[0] + "/"

    
def argument_parser():
    parser = argparse.ArgumentParser(description="check the path of the folder that is lastly updated, this will result in the lastly updated date")
    parser.add_argument("-i", "--in_folder", type=str, help="the base folder of the daily update")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = argument_parser()
    check_latest_date(args.in_folder)

