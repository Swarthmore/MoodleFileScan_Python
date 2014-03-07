import wand.image
import PIL.Image, PIL.ImageStat, PIL.ImageDraw
import re
import io
import sys, getopt
import os, glob, shutil


DEBUG_LEVEL = 2


def analyze_pdf_file_for_percent_black_magick(file):
	
	threshold_filter = 150
	border_size = 0.15  # percentage of document on each side
	
	black_list = []
	max_black = 0
	max_black_page = 0	
	black_threshold = 10
	width = 0
	height = 0
	
	
	print "Running analyze_pdf_file_for_percent_black_magick on %s" % file

	

	# Convert the PDF file into a sequence of images
	with wand.image.Image(filename=file) as img:
		img.save(filename='./tmp/tmp.jpg')
	
	
	# Get the list of files 
	image_listing = sorted(glob.glob('./tmp/*.jpg'))
	
	# Loop through all the images
	for image_file in image_listing:	
		im = PIL.Image.open(image_file)
		size = im.size
		print "Height: %d, Width %d" %(size[1], size[0])
	
		#print PIL.ImageStat.Stat(im).sum
		#print im.histogram()
		
		# Convert to greyscale
		im = im.convert("L")	
		#im.save(image_file + "_grey.jpg", "JPEG")	
		

		# Create a  mask in the center of the page
		mask_width = round((1.0-2*border_size)*size[0])
		mask_height = round((1.0-2*border_size)*size[1])
		print "Mask width: %d, height: %d" % (mask_width, mask_height)
		
		mask = PIL.Image.new("L", (mask_width, mask_height),255)	# same size as image		
		mask.save(image_file + "_mask.jpg", "JPEG")

		offset=(round(border_size*size[0]), round(border_size*size[1]))
		im.paste(mask,offset)
	
	
	
		# Convert to black and white
		table = []
		for i in range(256):
			if i < threshold_filter:
				table.append(0) # black
			else:
				table.append(255) # white
		
		im = im.point(table) 
	
	
		#im.save(image_file + "_thresh.jpg", "JPEG")
		
		# Compare black to white
		hist = im.histogram()
		percent_black = (float(hist[0])) / (hist[0] + hist[255])
		
		print "Percent black:  %f" % (percent_black*100)
	
	"""
	# Find out the size of the page (assume it is always the same as a first estimate)
	#try:
	with Image(filename=file) as img:
		# Calculate image size
		width = img.width
		height = img.height	

		if DEBUG_LEVEL >= 2:
			print "File width: %d, height %d" % (width, height)
		
		#palette = img.histogram.keys()
		#print palette	
	
		img.type = 'grayscale'
		img.alpha_channel = False
		palette = img.histogram.keys()
		#print palette				

		# create a new image of the same size, but with white all around
		with Image(width=img.width, height=img.height) as mask_image:
			mask_image.format = 'png'
		
			with Color('white') as fg:
				with Image(width=int(img.width*0.6), height=int(img.height*0.6), background=fg) as inner_mask_image:
				
					mask_image.composite_channel(
						channel='all_channels',
						image=inner_mask_image,
						operator='over',
						left=int(mask_image.width*0.2),
						top=int(mask_image.height*0.2)
					)	

					mask_image.composite_channel(
						channel='all_channels',
						image=img.sequence[0],
						operator='over',
						left=0,
						top=0
					)				

					mask_image.save(filename='/Users/aruether/Desktop/test.png')
					display(mask_image)
	
	
	#except Exception as e:
	#	print "Can't get size of file \"%s\"-- skipping " % file
	#	return 0			

	


	x0 = int(width*0.2)
	y0 = int(height*0.2)
	x1 = int(width*0.8)
	y1 = int(height*0.8)
	mask = "rectangle %d, %d, %d, %d" % (x0, y0, x1, y1)

	if DEBUG_LEVEL >= 2:
		print(mask)

	try:
		histogram = subprocess.check_output(["convert", file, "-depth", "8", "-colorspace", "Gray", "-alpha", "off", "-black-threshold", threshold_filter, "-fill", "white", "-draw", mask, "-type", "bilevel", "-define", "histogram:unique-colors=true", "-verbose", "-format", "%c", "histogram:info:-"], stderr=subprocess.STDOUT, timeout=60)
		
		# Convert to string
		histogram = histogram.decode('ascii', 'ignore')
		
	except subprocess.TimeoutExpired:
		print("Histogram timeout -- skipping file ", file)
		return 0	
	
	except subprocess.SubprocessError:
		print("Subprocess error -- skipping file ", file)
		return 0		
	
	
	if DEBUG_LEVEL >= 2:
		print(histogram)
	

	pages = re.split(page_regex, str(histogram), flags=re.MULTILINE)
	if DEBUG_LEVEL >= 1:
		print("Number of pages: ", len(pages))
	
	# Loop through each page looking for colors by iterating over each line
	for page_number in range(1,len(pages)):
		s = io.StringIO(pages[page_number-1])
		black = 0
		white = 0
		for line in s:
			if "(  0,  0,  0)" in line:
				black = float(re.search("^\s*(\d*):", line).group(1))
			if "(255,255,255)" in line:
				white = float(re.search("^\s*(\d*):", line).group(1))
		#print "Black %f   White %f" % (black, white)
		# if can't figure out percentage
		if black > 0:
			black_percentage = 100.0 * black / (white + black)
		else:
			black_percentage = 0

		if DEBUG_LEVEL >= 1:
			print ("Page ", page_number, "  black percentage: ", '{:.2f}'.format(black_percentage))		
			
		black_list.append(black_percentage)
		max_black = max(black_percentage, max_black)

		if black_percentage == max_black:
			max_black_page = page_number


	print ("Maximum black ", '{:.2f}'.format(max_black), " on page ", max_black_page)

	if max_black < black_threshold:
		print ("No large areas of black detected")
		return 0
	else:
		print ("Large areas of black detected")

		if DEBUG_LEVEL >= 2:
			for (i, item) in enumerate(black_list):
				if (item > black_threshold):
					print ("Page ", (i+1), " is ", '{:.2f}'.format(item),  "% black")
				
		return 1

"""
		



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