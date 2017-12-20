#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
# search and delete empty files
 
import os
 
str_directory = "Logs"

# get list of all files in the directory and remove possible hidden files
list_files = [x for x in os.listdir(str_directory) if x[0]!='.']
 
# now loop through the files and remove empty ones
for each_file in list_files:
    file_path = '%s/%s' % (str_directory, each_file)
 
    # check size and delete if 0
    if os.path.getsize(file_path)==0:
    	try:
        	os.remove(file_path)
    	except Exception as e:
        	print(e)
    else:
        pass