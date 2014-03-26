import wand.image
import PIL.Image, PIL.ImageStat, PIL.ImageDraw
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
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO



DEBUG_LEVEL = 2
ocr_temp_file_path = './tmp/ocr.txt'
image_temp_file_path = './tmp/tmp.jpg'

def analyze_pdf_file_for_percent_black(file_db, contenthash, file_info):

	file = os.path.join(moodle_file_dir, contenthash[0:2], contenthash[2:4],contenthash)
	
	threshold_filter = 150
	border_size = 0.15  # percentage of document on each side
	
	black_list = []
	max_black = 0
	max_black_page = 0	
	black_threshold = 10
	width = 0
	height = 0
	page_number = 1
	
	print "\n\n==============================\nRunning analyze_pdf_file_for_percent_black on %s" % file

	
	try:
		# Convert the PDF file into a sequence of images
		with wand.image.Image(filename=file) as img:
			img.save(filename=image_temp_file_path)

		# Get the list of files 
		image_listing = sorted(glob.glob('./tmp/*.jpg'))

		# Loop through all the images
		for image_file in image_listing:	
			im = PIL.Image.open(image_file)
			size = im.size
			
			if DEBUG_LEVEL >= 2:
				print "Image %s: Height: %d, Width %d" %(image_file, size[1], size[0])

			if DEBUG_LEVEL >= 3:
				print PIL.ImageStat.Stat(im).sum
				print im.histogram()
	
			# Convert to greyscale
			im = im.convert("L")	
			
			if DEBUG_LEVEL >= 2:
				im.save(image_file + "_grey.jpg", "JPEG")		# Greyscale image
	

			# Create a  mask in the center of the page
			mask_width = int(round((1.0-2*border_size)*size[0]))
			mask_height = int(round((1.0-2*border_size)*size[1]))
			if DEBUG_LEVEL >= 2:
				print "Mask width: %d, height: %d" % (mask_width, mask_height)
	
			mask = PIL.Image.new("L", (mask_width, mask_height),255)	# same size as image	


			# Put the mask on top of the image
			x_offset = int(round(border_size*size[0]))
			y_offset = int(round(border_size*size[1]))
			offset=(x_offset, y_offset)
			im.paste(mask,offset)

			# Convert masked image to black and white
			table = []
			for i in range(256):
				if i < threshold_filter:
					table.append(0) # black
				else:
					table.append(255) # white
			im = im.point(table) 

			if DEBUG_LEVEL >= 2:
				im.save(image_file + "_thresh.jpg", "JPEG")		# Black and white masked image (used for histogram)
	
			# Compare black to white and calculate percentage black
			hist = im.histogram()
			percent_black = 100*(float(hist[0])) / (hist[0] + hist[255])
		
			if DEBUG_LEVEL >= 1:
				print "Page %d: black percentage: %.1f" % (page_number, percent_black)		
		
			black_list.append(percent_black)
			max_black = max(percent_black, max_black)

			if percent_black == max_black:
				max_black_page = page_number
			
			page_number += 1


		print "Maximum black %.1f on page %d" % (max_black, max_black_page)

		if max_black < black_threshold:
			print ("No large areas of black detected")
		else:
			print ("Large areas of black detected")

		if DEBUG_LEVEL >= 2:
			for (i, item) in enumerate(black_list):
				if (item > black_threshold):
					print "Page %d is %.1f%% black"	% ( (i+1), item)
		
		# Save scan info to pickledb
		file_info['scan_status'] = {
			'black_list': black_list,
			'max_black': max_black,
			'max_black_page': max_black_page
		}

		if not file_db.set(contenthash, file_info):
			print >>sys.stderr, "set error: " + str(file_db.error()) 
		
		if DEBUG_LEVEL >= 1:
			print "Updated file database for %s" % contenthash
			pprint(file_info)
			
	except Exception,e:  
		print "Problem processing file.  Skipping %s\n%s" % (file, str(e))
		return 0
	


				
	return 1





def empty_tmp_folder():

	# Thanks to http://stackoverflow.com/a/6615332
	folder_path = './tmp'
	for file_object in os.listdir(folder_path):
		file_object_path = os.path.join(folder_path, file_object)
		if os.path.isfile(file_object_path):
			os.unlink(file_object_path)
		else:
			shutil.rmtree(file_object_path)
			
	
	
	
	
	
	
# See if a PDF file contains text and record the results in the database	
def check_pdf_for_ocr(file_db, contenthash, file_info):

	if DEBUG_LEVEL >= 1:
		print "Now checking file %s for OCR status" % file_info['filename']

	try:

		filepath = os.path.join(moodle_file_dir, contenthash[0:2], contenthash[2:4],contenthash)

		
		text = convert_pdf_to_txt(filepath)

		if DEBUG_LEVEL >= 2:	
			print "Finished extracting the text"	
		
		if re.search("\S", text,re.MULTILINE):
			file_info['ocr_status'] = True
		else:
			file_info['ocr_status'] = False

		# Save updated info to db
		if not file_db.set(contenthash, file_info):
			print >>sys.stderr, "set error: " + str(file_db.error()) 
	
		if DEBUG_LEVEL >= 1:
			print "OCR status: %r" % file_info['ocr_status']
			
	except Exception,e:  
		print "Problem processing ocr for file.  Skipping %s\n%s" % (file, str(e))
		return 0	
	
	except SystemExit, se:
		print "Caught System Exit for file %s.  Skipping. %d" % (file, se.message)
		return 0



def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = Config.get("OCR", "max_pages_to_check")
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    str = retstr.getvalue()
    retstr.close()
    return str


	

		

################## MAIN PROGRAM #####################
		
		
Config = ConfigParser.ConfigParser()
Config.read("./moodle_filescan.conf")	
			
"""
inputfile = ''
outputfile = ''

try:
	opts, args = getopt.getopt(sys.argv[1:],"i:o:",["ifile=","ofile="])
except getopt.GetoptError:
	print 'Usage: -i <inputfile> -o <outputfile>'
	sys.exit(2)
for opt, arg in opts:
	if opt in ("-i", "--ifile"):
         inputfile = arg
	elif opt in ("-o", "--ofile"):
		outputfile = arg
"""

moodle_file_dir = Config.get("Moodle", "filedir")

file_db = DB()
# open the database
if not file_db.open("filestore.kch", DB.OWRITER | DB.OCREATE | DB.OREADER):
	print >>sys.stderr, "file database open error: " + str(file_db.error())
	
# traverse records
cur = file_db.cursor()
cur.jump()
while True:
	rec = cur.get(True)
	if not rec: break

	contenthash = rec[0]
	file_info = ast.literal_eval(rec[1])

	print contenthash
	print file_info

	empty_tmp_folder()
	
	#try: 
	
	# only process unchecked files
	if not file_info['checked']:
   
		if file_info['scan_status'] is None:
			analyze_pdf_file_for_percent_black(file_db, contenthash, file_info)
   
		if file_info['ocr_status'] is None:
			check_pdf_for_ocr(file_db, contenthash, file_info)
   
		# Mark as checked if OCR and Scan are done
		if (file_info['ocr_status'] is not None) and (file_info['scan_status'] is not None):
			file_info['checked'] = True	
		   
			if not file_db.set(contenthash, file_info):
				print >>sys.stderr, "set error: " + str(file_db.error()) 		
							
	#except Exception,e:  
	#	print "Problem processing file.  Skipping %s (%s)" % (contenthash, file_info['filename'])
	#	continue
		
		# Clean up
		empty_tmp_folder()	
		
	else:
		print "\n\nSkipping: Already checked %s (%s)" % (contenthash, file_info['filename'])

cur.disable()
# close the database
if not file_db.close():
	print >>sys.stderr, "close error: " + str(file_db.error())  
		
		
version = '0.1'		