import ConfigParser
import MySQLdb
import MySQLdb.cursors
from unidecode import unidecode
from kyotocabinet import *
import sys
from pprint import pprint


Config = ConfigParser.ConfigParser()
Config.read("./moodle_filescan.conf")
  
    
moodle_db = MySQLdb.connect(	host=Config.get("MySQL", "host"), # your host, usually localhost
                     	user=Config.get("MySQL", "user"), # your username
                    	passwd=Config.get("MySQL", "passwd"), # your password
                      	db=Config.get("MySQL", "db"), # name of the data base
                      	cursorclass=MySQLdb.cursors.DictCursor)



# Find all the non-legacy PDF files 
cur = moodle_db.cursor() 
cur.execute("select mdl_files.filename, mdl_files.contenthash, mdl_context.instanceid, mdl_context.path from mdl_files, mdl_context where mdl_context.id = mdl_files.contextid and mdl_context.contextlevel = 70 and mdl_files.filesize <> 0 and mdl_files.mimetype = 'application/pdf' and contenthash='405ad25ed7684fa4648e6509464a4c4e3fe6abf2';")

for file_info in cur.fetchall():
#if True:
	#file_info =cur.fetchone()
	pprint(file_info)


	paths = file_info['path'].split("/")[1:]		# Drop first element (because of the initial slash in path)
	paths.reverse()
	path_string = []
	course_id = 0
	
	for p in paths:
		path_cur = moodle_db.cursor();
  		path_cur.execute("select instanceid, contextlevel from mdl_context where id=%s" % p)
  		path_info = path_cur.fetchone()
  		print path_info
  		
  		# Lookup folder or resource
  		if path_info['contextlevel'] ==70:
  			module_cur = moodle_db.cursor();
  			module_cur.execute("select module, instance, section from mdl_course_modules where id=%s" % path_info['instanceid'])
  			module_info = module_cur.fetchone()	
  			print module_info
  			
			# File or folder?
			if module_info['module'] == 34:			# 34 = folder
				folder_cur = moodle_db.cursor();
				folder_cur.execute("select mdl_folder.name from mdl_folder where id=%s", module_info['instance'])
				folder_info = folder_cur.fetchone()
				print folder_info
				path_string = "/%s/%s" % (folder_info['name'], file_info['filename'])
				
		
			elif module_info['module'] == 16:			# 16 = resource
				resource_cur = moodle_db.cursor();
				resource_cur.execute("select mdl_resource.name from mdl_resource where id=%s", module_info['instance'])
				resource_info = resource_cur.fetchone()
				print resource_info
				path_string = "/%s" % (resource_info['name'])

		elif path_info['contextlevel'] == 50:
			# course level
			course_id = path_info['instanceid']

	# Get more course information
	course_cur = moodle_db.cursor();
  	course_cur.execute("select mdl_course.fullname from mdl_course where id=%s;" , course_id)
	course_info = course_cur.fetchone()
	
	print "Course name: %s" % course_info['fullname']
	print "Course link: https://moodle.swarthmore.edu/course/view.php?id=%s" % course_id		
	print path_string
	print "\n\n\n\n\n"			
