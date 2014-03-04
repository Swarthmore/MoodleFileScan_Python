import re, os, MySQLdb, ConfigParser


# Load config 
Config = ConfigParser.ConfigParser()
Config.read("moodle_scans.conf")

# Open file as file object and read to string
ifile = open(Config.get('Files', "moodle_scan_file"),'r')

# Read file object to string
text = ifile.read()

# Close file object
ifile.close()

# Connect to the database and create a cursor
db = MySQLdb.connect(host=Config.get('Moodle', 'db_host'), user=Config.get('Moodle', 'db_user'), passwd=Config.get('Moodle', 'db_pass'), db=Config.get('Moodle', 'db_name'))
cur = db.cursor() 


expr = re.compile("Maximum black  (\d+[\.]?\d*)  on page  (\d*)\n.*\nCheck this file: (\S*)", re.M)
for el in expr.findall(text):
	#print os.path.basename(el) 
	print ",".join(el)
	

	# Use all the SQL you like
	cur.execute("select mdl_course.fullname, mdl_course.id, mdl_files. filename, mdl_context.contextlevel from mdl_course, mdl_course_modules, mdl_context, mdl_files where mdl_context.id = mdl_files.contextid and mdl_course_modules.id = mdl_context.instanceid and mdl_course.id = mdl_course_modules.course and mdl_context.contextlevel = 70 and mdl_files.contenthash = %s", el[2])

	# print all the first cell of all the rows
	for row in cur.fetchall() :
		print row
		
	print "--------------------------"