import os, re, magic, pyPdf
from os.path import join, getsize
import elementtree.ElementTree as ET

# From http://stackoverflow.com/questions/6026287/batch-ocr-program-for-pdfs

#path is the directory with the files, other 2 are the names of the files you will store your lists in

base_dir = '<BASE DIR>'
moodle_xml_file = ""

report_file  = open("PDF_OCR_report.txt", "w")
no_text_listing = []
text_listing = []
unknown_listing = []


# Get index XML  (if there is an XML file)
if moodle_xml_file:
	tree = ET.parse(moodle_xml_file)
	xml_root = tree.getroot()


for root, dirs, files in os.walk(base_dir):


	for name in files:	

		# Get the actual filename from the Moodle file.xml file
		actual_filename = name
		
		if moodle_xml_file:
			for file in xml_root.findall("./file"):
				if file.find("contenthash").text == name:
					actual_filename = file.find("filename").text
					break;
				
		filename =  join(root, name)
		filetype = magic.from_file(filename).decode('ascii', 'ignore')
		if filetype.find("PDF") ==0:
			print "Found PDF file: %s" % filename
			
			try:
			
				pdf = pyPdf.PdfFileReader(open(filename, 'rb'))
				if pdf.getIsEncrypted():
					pdf.decrypt('')
			
				has_text = False
				for i in range(0, pdf.getNumPages()):
					content = pdf.getPage(i).extractText()

					# this step checks to see if text is present
					# Look for a word with 2 or more characters
					# From http://stackoverflow.com/questions/6053064/python-pypdf-adobe-pdf-ocr-error-unsupported-filter-lzwdecode
					if re.findall(r'\w{2,}', content):
						has_text = True
						continue

				if has_text:
					text_listing.append(actual_filename)
				else:
					no_text_listing.append(actual_filename)

			except Exception,e: 
				print str(e)
				print "Problem reading %s" % filename
				unknown_listing.append(actual_filename + "\n")


		else: 
			print "Not a PDF file: %s" % filename


# Output results to a file
report_file.write("PDF's not containing text\n-------------------------------\n")
for f in no_text_listing:
	report_file.write(f + "\n")
	
report_file.write("\n\nPDFs containing text\n-------------------------------\n")
for f in text_listing:
	report_file.write(f + "\n")

report_file.write("\n\nNot able to determine\n-------------------------------\n")
for f in unknown_listing:
	report_file.write(f + "\n")

report_file.close()
