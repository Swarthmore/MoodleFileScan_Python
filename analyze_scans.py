import wand.image
import PIL.Image, PIL.ImageStat, PIL.ImageDraw
import re
import io
import sys, getopt
import os, glob, shutil


DEBUG_LEVEL = 1


def analyze_pdf_file_for_percent_black_magick(file):
	
	threshold_filter = 150
	border_size = 0.15  # percentage of document on each side
	
	black_list = []
	max_black = 0
	max_black_page = 0	
	black_threshold = 10
	width = 0
	height = 0
	page_number = 1
	
	print "Running analyze_pdf_file_for_percent_black_magick on %s" % file

	
	try:
		# Convert the PDF file into a sequence of images
		with wand.image.Image(filename=file) as img:
			img.save(filename='./tmp/tmp.jpg')

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
				print "Page %d: black percentage: %.2f" % (page_number, percent_black)		
		
			black_list.append(percent_black)
			max_black = max(percent_black, max_black)

			if percent_black == max_black:
				max_black_page = page_number
			
			page_number += 1


		print "Maximum black %.2f on page %d" % (max_black, max_black_page)

		if max_black < black_threshold:
			print ("No large areas of black detected")
			return 0
		else:
			print ("Large areas of black detected")

		if DEBUG_LEVEL >= 2:
			for (i, item) in enumerate(black_list):
				if (item > black_threshold):
					print "Page %d is %.1f black"	% ( (i+1), item)
		
		
		
			
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

empty_tmp_folder()
analyze_pdf_file_for_percent_black_magick(inputfile)		
#empty_tmp_folder()		
		
		
version = '0.1'		