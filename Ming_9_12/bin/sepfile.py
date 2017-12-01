#!/usr/bin/python
import sys
import os
import argparse
import pandas as pd
import math
import subprocess
def main():

	#parse in all the parameters
    parser = argparse.ArgumentParser(description='Running sepfile wrapper')
    parser.add_argument('mgf', help='mgf')
    parser.add_argument('mgfo', help='mgfo')
    args = parser.parse_args()
	
    #define the paths
    p_mgf = args.mgf
    p_mgfo = args.mgfo

        
    # set the step to be 15 each
    step = 15
    lists = []
    ionlist =[] 
    feature_count = 0
    with open(p_mgf,'r') as inmgf:
        content = inmgf.readlines()
        list1 = []
        counter = 0
        for line in content:    
            if counter == step:
                lists.append(list1)
                list1 = []
                counter = 0
            if len(line.split('BEGIN IONS')) !=1:
                if len(ionlist) !=0:
                    list1.append(ionlist)
                    ionlist =[]                   
            if len(line.split('FEATURE_ID=')) !=1:
                old_count = feature_count
                feature_count= int(line.split('FEATURE_ID=')[-1])
                if old_count != feature_count:
                    counter = counter+1
            ionlist.append(line)
    lists.append(list1);
    inmgf.close()

    #write the file
    counter2 = 0;
    for files in lists:
        filename = "/mgf%s.mgf" %(counter2)
        with open(p_mgfo+filename,'w') as mgfo:
            for ions in files: 
                for lines in ions: 
                    mgfo.write(lines)
        mgfo.close()
        counter2 = counter2+1


if __name__ == "__main__":
	main()
	
