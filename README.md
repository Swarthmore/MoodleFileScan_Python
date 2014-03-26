MoodleFileScan
==============

Scan Moodle filesystem looking for non-OCR'd PDFs and badly scanned documents

1) Set up config file with your information.  Rename to "moodle_filescan.conf"

2) Run generate_file_listing.py to find all of PDF's in Moodle and save references in a Kyoto Cabinet database

3) Run analyze_scans.py to find PDF's with lots of dark colors around the edges.  Will also determine if PDF's are OCR'd or not.  All information is saved to the local Kyoto Cabinet database.

4) Run build_scan_report.py to generate a CSV file with a listing of scans with lots of dark colors around the edge.
