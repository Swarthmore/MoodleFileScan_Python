######!/usr/local/bin/python3.3

#
#
# may need to run "unset LANG" before running
# https://github.com/Homebrew/homebrew-dupes/pull/21

import magic
import os
from os.path import join, getsize
import analyze_scans



f = open('moodle_files.txt', 'r')

for filename in f:
	filename = filename.rstrip()
	filetype = magic.from_file(filename).decode('ascii', 'ignore')
	if filetype.find("PDF") ==0:
		print("\nFound a PDF file ", filename)
		if analyze_scans.analyze_pdf_file_for_percent_black_magick(filename):
			print ("Check this file:", filename, "\n")
	else:
		#print "%s is not a PDF (%s)" % (filename, filetype)
		print('.'),