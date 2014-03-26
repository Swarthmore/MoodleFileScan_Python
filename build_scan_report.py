import re
import io
import sys, getopt
import os, glob, shutil
import ConfigParser
import json
from pprint import pprint
import math
import ast
from kyotocabinet import *
import csv
from cStringIO import StringIO
import MySQLdb
import MySQLdb.cursors

def get_fileinfo(contenthash):

	Config = ConfigParser.ConfigParser()
	Config.read("./moodle_filescan.conf")

	moodle_db = MySQLdb.connect(	
					host=Config.get("MySQL", "host"), # your host, usually localhost
					user=Config.get("MySQL", "user"), # your username
					passwd=Config.get("MySQL", "passwd"), # your password
					db=Config.get("MySQL", "db"), # name of the data base
					cursorclass=MySQLdb.cursors.DictCursor)

	# Find all the non-legacy PDF files 
	cur = moodle_db.cursor() 
	cur.execute("select mdl_files.filename, mdl_files.contenthash, mdl_context.instanceid, mdl_context.path from mdl_files, mdl_context where mdl_context.id = mdl_files.contextid and mdl_context.contextlevel = 70 and mdl_files.filesize <> 0 and mdl_files.mimetype = 'application/pdf' and mdl_files.contenthash=%s;", contenthash)

	for file_info in cur.fetchall():

		#pprint(file_info)

		paths = file_info['path'].split("/")[1:]		# Drop first element (because of the initial slash in path)
		paths.reverse()
		path_string = []
		course_id = 0
	
		for p in paths:

			path_cur = moodle_db.cursor();
			path_cur.execute("select instanceid, contextlevel from mdl_context where id=%s" % p)
			path_info = path_cur.fetchone()
			path_cur.close()
			#print path_info
		
			# Lookup folder or resource
			if path_info['contextlevel'] ==70:
				module_cur = moodle_db.cursor();
				module_cur.execute("select module, instance, section from mdl_course_modules where id=%s" % path_info['instanceid'])
				module_info = module_cur.fetchone()	
				module_cur.close()
				#print module_info
			
				# File or folder?
				if module_info['module'] == 34:			# 34 = folder
					folder_cur = moodle_db.cursor();
					folder_cur.execute("select mdl_folder.name from mdl_folder where id=%s", module_info['instance'])
					folder_info = folder_cur.fetchone()
					folder_cur.close()
					#print folder_info
					path_string = "/%s/%s" % (folder_info['name'], file_info['filename'])
				
		
				elif module_info['module'] == 16:			# 16 = resource
					resource_cur = moodle_db.cursor();
					resource_cur.execute("select mdl_resource.name from mdl_resource where id=%s", module_info['instance'])
					resource_info = resource_cur.fetchone()
					resource_cur.close()
					#print resource_info
					try:
						path_string = "/%s" % (resource_info['name'])
					except TypeError:
						print "** Cannot retrieve information for this file **"
						path_string = "?"

			elif path_info['contextlevel'] == 50:
				# course level
				course_id = path_info['instanceid']

		# Get more course information
		course_cur = moodle_db.cursor();
		course_cur.execute("select mdl_course.fullname from mdl_course where id=%s;" , course_id)
		course_info = course_cur.fetchone()
		course_link = "=HYPERLINK(\"%s/course/view.php?id=%s\", \"%s\")" % ( Config.get("Moodle", "moodle_url"), course_id, course_info['fullname'])
		
		# Close cursors
		cur.close()
		

	return {'course_fullname': course_info['fullname'], 'course_link':course_link, 'path_to_file':path_string}






################## MAIN PROGRAM #####################
		
# Load config file		
Config = ConfigParser.ConfigParser()
Config.read("./moodle_filescan.conf")	
			

# open the program database
file_db = DB()
if not file_db.open(Config.get("Local_DB", "filepath"), DB.OWRITER | DB.OCREATE | DB.OREADER):
	print >>sys.stderr, "file database open error: " + str(file_db.error())
	
	
# traverse records
cur = file_db.cursor()
cur.jump()


# Set up statistics counters
total_files = 0
scan_check_completed = 0
exceeded_black_threshold = 0
ocr_check_completed = 0
non_ocr_files = 0


# Open CSV file and traverse database records
with open(Config.get("Reporting", "report_filename"), 'wb') as f:
	writer = csv.writer(f)
	
	# Write out header
	writer.writerow(["Contenthash", "Filename", "Course", "Path to file", "Max % Black", "Max % black page", "OCR Status"])
	
	while True:
		rec = cur.get(True)
		if not rec: break

		# Get information for this record
		contenthash = rec[0]
		file_info = ast.literal_eval(rec[1])


		# Update stats
		total_files += 1
		if file_info['scan_status']:
			scan_check_completed += 1
			if file_info['scan_status']['max_black'] >= float(Config.get("Scan", "black_threshold")):
				exceeded_black_threshold += 1
		if file_info['ocr_status'] is not None:
			ocr_check_completed += 1 
			if not file_info['ocr_status']:
				non_ocr_files += 1

		# only save files that have completed the process
		if file_info['scan_status'] and file_info['scan_status']['max_black'] >= float(Config.get("Scan", "black_threshold")):
			
			if file_info['ocr_status'] is None:
				file_info['ocr_status'] = "Not checked"
				
			formatted_black_percentage = "%0.1f" % file_info['scan_status']['max_black']
			
			course_info = get_fileinfo(contenthash)			
			writer.writerow([contenthash, file_info['filename'], course_info['course_link'], course_info['path_to_file'], formatted_black_percentage, file_info['scan_status']['max_black_page'],file_info['ocr_status']])
			print "Saved info for %s" % file_info['filename']

		else:
			if file_info['scan_status'] is None or file_info['scan_status']['max_black'] is None:
				file_info['scan_status'] = {'max_black':"?"}
			print "Skipping \"%s\" because it has not been checked or does not meet black threshold (%s)" % (file_info['filename'], str(file_info['scan_status']['max_black']))



# Finish up and close the database
cur.disable()
if not file_db.close():
	print >>sys.stderr, "close error: " + str(file_db.error())  
		
# Generate stats at end
print "\n\n\n=============================================================="
print "Total files found: %d" % total_files
print "Files checked for scan quality: %d" %  scan_check_completed
print "Files flagged for scanning review: %d" % exceeded_black_threshold
print "Files checked for OCR status: %d" % ocr_check_completed
print "Files confirmed to not have OCR: %d" % non_ocr_files
				