import ConfigParser
import MySQLdb
import MySQLdb.cursors
from unidecode import unidecode
from kyotocabinet import *
import sys


Config = ConfigParser.ConfigParser()
Config.read("./moodle_filescan.conf")

file_db = DB()
# open the database
if not file_db.open("filestore.kch", DB.OWRITER | DB.OCREATE):
	print >>sys.stderr, "file database open error: " + str(file_db.error())
    
    
moodle_db = MySQLdb.connect(	host=Config.get("MySQL", "host"), # your host, usually localhost
                     	user=Config.get("MySQL", "user"), # your username
                    	passwd=Config.get("MySQL", "passwd"), # your password
                      	db=Config.get("MySQL", "db"), # name of the data base
                      	cursorclass=MySQLdb.cursors.DictCursor)

cur = moodle_db.cursor() 

# Find all the non-legacy PDF files 
cur.execute("select mdl_files.filename, mdl_files.contenthash from mdl_files, mdl_context where mdl_context.id = mdl_files.contextid and mdl_context.contextlevel = 70 and mdl_files.filesize <> 0 and mdl_files.mimetype = 'application/pdf';")

for row in cur.fetchall() :
	print row

	file_cur = moodle_db.cursor();
  	file_cur.execute("select mdl_course.fullname, mdl_course.id from mdl_course, mdl_course_modules, mdl_context, mdl_files where mdl_context.id = mdl_files.contextid and mdl_course_modules.id = mdl_context.instanceid and mdl_course.id = mdl_course_modules.course and mdl_context.contextlevel = 70 and mdl_files.contenthash = %s;", row['contenthash'])

	courses = []
	for c in file_cur.fetchall():
		courses.append({
		"fullname" : unidecode(c['fullname']), 
		"id" : c['id']
		})
		
	file_record = {
		'filename':unidecode(row['filename']),
		'checked':False, 
		'scan_status':None, 
		'ocr_status': None,
		'courses': courses
		}	
		
	if not file_db.set(row['contenthash'], file_record):
		print >>sys.stderr, "set error: " + str(file_db.error())  


# close the database
if not file_db.close():
	print >>sys.stderr, "close error: " + str(file_db.error())  	