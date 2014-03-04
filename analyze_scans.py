#from wand.image import Image, Color
#import wand.display
import subprocess
import re
import io

DEBUG_LEVEL = 1
#black_color = Color('black')
#white_color = Color('white')


def analyze_pdf_file_for_percent_black_magick(file):
	
	
	threshold_filter = "20%"
	black_list = []
	max_black = 0
	max_black_page = 0	
	black_threshold = 10

	# Split results into one per page based on lines starting with the filename (discard warnings, etc)
	page_regex = "^%s.*" % re.escape(file)
	
	# Find out the size of the page (assume it is always the same as a first estimate)
	try:
		identify_output = subprocess.check_output(["identify", file], stderr=subprocess.STDOUT, timeout=60).decode('ascii', "ignore")
		image_size = re.search("PDF (\d*)x(\d*)", identify_output)
		
	except subprocess.CalledProcessError:
		print ("Can't run identify on file -- skipping ", file)
		return 0
		
	except subprocess.SubprocessError:
		print("Subprocess error -- skipping file ", file)
		return 0				
	
	if DEBUG_LEVEL >= 2:
		print(identify_output)	

	# Calculate mask size
	width = float(image_size.group(1))
	height = float(image_size.group(2))	
	
	if DEBUG_LEVEL >= 2:
		print ("Width ", width, " height ", height)
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


		
version = '0.1'		