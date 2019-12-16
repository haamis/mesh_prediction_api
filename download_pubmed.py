#!/usr/bin/env python
# -*- coding: utf-8 -*-

# previous step : check_previous_folder.py

# next step: xml2txt

import glob
import ftplib
import re
import os
import sys
import subprocess
import argparse
import gzip


def connect():
    """
    TODO: should provide this information as configuration file 
    """
    ftp=ftplib.FTP("ftp.ncbi.nlm.nih.gov","anonymous","ginter@cs.utu.fi")
    return ftp


def check_date(file_name):
    try:
        print file_name.split("medline")[1].split("n")[0]
        return file_name.split("medline")[1].split("n")[0]
    except:
        print file_name.split("pubmed")[1].split("n")[0]
        return file_name.split("pubmed")[1].split("n")[0]


def fetch(curr_folder, prev_folder):
    """
    provide the option of either "batch download" or "daily update"
    """
    with gzip.open(prev_folder + 'downloaded_files.txt.gz', 'rb') as f:        
        dlList = [line.strip('\n') for line in f]
    prev_batch = check_date(dlList[-1])
    ftp=connect()
    ftp.cwd("/pubmed/baseline")
    fileList=ftp.nlst()
    curr_batch = fileList[0].split("pubmed")[1].split("n")[0] 
    print 'current_batch', curr_batch
    print 'prev_batch', prev_batch
    if int(prev_batch) != int(curr_batch):
        print "batch download: download the whole set"
        ftp.cwd("/pubmed/baseline")
    else:
        print "daily update: download what is not downloaded yet"
        ftp.cwd("/pubmed/updatefiles")
        fileList=ftp.nlst()
    for fName in fileList:
        if '_' in fName:
            xml_name = fName.split('_')[0] + '.xml.gz'
        else:
            xml_name = fName.split('.')[0] + '.xml.gz'
        if xml_name not in dlList:
            print "downloading...", fName
            outFile = open(curr_folder + "original_PubMed/" + fName, "wb")
            ftp.retrbinary("RETR "+ fName, outFile.write)
            outFile.close()
    ftp.quit()
        

def argument_parser():
    parser = argparse.ArgumentParser(description="download the PubMed from ftp")
    parser.add_argument("-c", "--curr_folder", type=str, help="output folder where the downloaded files go")
    parser.add_argument("-p", "--prev_folder", type=str, help="previously updated folder")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = argument_parser()
    fetch(args.curr_folder, args.prev_folder)
    with gzip.open(args.prev_folder + 'downloaded_files.txt.gz', 'rb') as f:        
        prev_list = f.read()
    curr_files = [os.path.basename(x) for x in glob.glob(args.curr_folder + 'original_PubMed/*.xml.gz')]
    curr_files.sort()
    curr_list = '\n'.join(curr_files)
    with gzip.open(args.curr_folder + 'downloaded_files.txt.gz', 'wb') as f:
        f.write(''.join(prev_list + '\n' + curr_list))
