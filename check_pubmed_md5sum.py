#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import gzip
import glob
import subprocess

    
def check_md5sum_file(curr_folder):
    md5sum_text = ""
    all_files = [os.path.basename(x) for x in glob.glob(curr_folder + "original_PubMed/*.md5")]
    all_files.sort()
    for in_file in all_files:
        os.chdir(curr_folder + "original_PubMed/")
        a = subprocess.check_output(["md5sum", in_file])
        with open(curr_folder + "original_PubMed/" + "md5sum.txt", "wb") as f:
            f.write(a)
        b = subprocess.check_output(["md5sum", "-c", "md5sum.txt"])
        if "OK" not in b:
            print in_file, "downloaded gzip file: corrupted"
        else:
            print in_file, "downloaded gzip file: OK"


def argument_parser():
    parser = argparse.ArgumentParser(description="check if files are downloaded correctly & completely, if not it will print the file name that is broken")
    parser.add_argument("-c", "--curr_folder", type=str, help="current folder that contains both md5sum file and downloaded filex")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = argument_parser()
    check_md5sum_file(args.curr_folder)






