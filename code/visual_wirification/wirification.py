# -*- coding: utf-8 -*-
#Author: Chunyang Chen
#Goal: some scripts to do different things

import operator
import os
import shutil
import hashlib
import re
import numpy
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFile
from multiprocessing import Pool
#import xml2seq_verbose as xml2seq


def checkFileValidity(inputFile):
	'''
	Check the validity of the XML file and ignore it if possible
	Due to the unknown reasons, the content in some XML file is repetative or
	'''
	homeScreen_list = ["Make yourself at home", "You can put your favorite apps here.", "To see all your apps, touch the circle."]
	unlockHomeScreen_list = ["Camera", "[16,600][144,728]", "Phone", "[150,1114][225,1189]", "People", "[256,1114][331,1189]", "Messaging", "[468,1114][543,1189]", "Browser", "[574,1114][649,1189]"]
	with open(inputFile) as f:
		content = f.read()
		#it is the layout code for the whole window and no rotation
		if 'bounds="[0,0][800,1216]"' in content and '<hierarchy rotation="1">' not in content:
			if not all(keyword in content for keyword in homeScreen_list) and not all(keyword in content for keyword in unlockHomeScreen_list):
				#it should not be the homepage of the phone
				bounds_list = re.findall(r'bounds="(.+?)"', content)
				if len(bounds_list) < 2:
					return False
				return True

	return False
def compareHisto(first, sec):
	imA = Image.open(first)
	imB = Image.open(sec)

	# Normalise the scale of images
	if imA.size[0] > imB.size[0]:
		imA = imA.resize((imB.size[0], imA.size[1]))
	else:
		imB = imB.resize((imA.size[0], imB.size[1]))

	if imA.size[1] > imB.size[1]:
		imA = imA.resize((imA.size[0], imB.size[1]))
	else:
		imB = imB.resize((imB.size[0], imA.size[1]))

	hA = imA.histogram()
	hB = imB.histogram()
	sum_hA = 0.0
	sum_hB = 0.0
	diff = 0.0

	for i in range(len(hA)):
		#print(sum_hA)
		sum_hA += hA[i]
		sum_hB += hB[i]
		diff += abs(hA[i] - hB[i])

	return diff/(2*max(sum_hA, sum_hB))

def checkDuplicateFile(inputFile, hash_dict):
	with open(inputFile) as f:
		content = f.read()
		content = re.sub(r'(?!.*\/>).*', "", content)
		content = re.sub(r'\s', "", content)
		content = re.sub(r'content-desc=".*?"', "", content)  #remove the filled text
		content = re.sub(r'text=".*?"', "", content)  #remove the text
		content = re.sub(r'bounds=".*?"', "", content)
		content = re.sub(r'index=".*?"', "", content)
		content = re.sub(r'NAF=".*?"', "", content)
		content = re.sub(r'focused=".*?"', "", content)
		content = re.sub(r'checked=".*?"', "", content)
		content = re.sub(r'password=".*?"', "", content)
		content = re.sub(r'selected=".*?"', "", content)
        content = re.sub(r'enabled=".*?"', "", content)
        content = re.sub(r'checkable=".*?"', "", content)
        content = re.sub(r'focusable=".*?"', "", content)
        content = re.sub(r'scrollable=".*?"', "", content)
        content = re.sub(r'long-clickable=".*?"', "", content)
        fileHash = hashlib.sha224(content).hexdigest()       #get the hash digest of the file
        if fileHash not in hash_dict:
        	hash_dict[fileHash] = ""
        	return [True, hash_dict]
        else:
        	return [False, hash_dict]

def imageProcessing(img):
	"""
	preprocess the image using basic operations
	"""
	img = img.crop((0, 32, 799, 1214))     #remove the margins
	img = img.resize((256, 256), Image.ANTIALIAS)	  #resize the image for the model
	return img

def drawImageLabel(inputFile_xml, fileHash, directory, specificOutputDir):
	'''
	draw rectangle of the image and corresponding label
	'''
	a = 0
	b = 0
	c = 0
	d = 0
	e = 0
	f = 0
	g = 0

	def imageWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/ImageView.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		if wid==0 or hei== 0:
			return
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))
		
	def editTextWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/EditView.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def buttonWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/Button.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def textViewWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/TextView.bmp','rb')).convert('RGBA')
		x1,y1 = dimensions['from']
		x2,y2 = dimensions['to']
		wid = x2 - x1
		hei = y2 - y1
		
		if wid > 0 and hei > 0:
			im = im.resize((wid,hei),Image.ANTIALIAS)
			base.paste(im, (tuple(numpy.add(dimensions['from'],(10, 10)))))

	def toggleButtonWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/ToggleButton.png','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def checkedTextViewWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/CheckedTextView.png','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def checkBoxWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/CheckBox.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def progressBarWF(draw, dimensions, base):
		#draw.rectangle((dimensions['from'], dimensions['to']), fill="#636363")
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		im = Image.open('UIelement3/ProgressBar.bmp').convert('RGBA').resize((w, h))

		base.paste(im, (dimensions['from']))

	def radioButtonWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/RadioButton.png','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def switchWF(draw, dimensions, base):
		im = Image.open(open('UIelement3/Switch.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def seekBarWF(draw, dimensions, base):
		#draw.rectangle((dimensions['from'], dimensions['to']), fill="#000000")
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		if w < h:
			im = Image.open('UIelement3/seekbar_vertical.png').convert('RGBA').resize((w, h))
		else:
			im = Image.open('UIelement3/seekbar_horizontal.png').convert('RGBA').resize((w, h))
		base.paste(im, (dimensions['from']))

	def webViewWF(draw, dimensions, base):
		return
		im = Image.open(open('UIelement3/WebView.bmp','rb')).convert('RGBA')
		wid = dimensions['to'][0] - dimensions['from'][0]
		hei = dimensions['to'][1] - dimensions['from'][1]
		im = im.resize((wid,hei),Image.ANTIALIAS)
		base.paste(im, (dimensions['from']))

	def videoViewWF(draw, dimensions, base):
		im = Image.open('UIelement3/VideoView.bmp').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))

	def spinnerWF(draw, dimensions, base):
		im = Image.open('UIelement3/spinner.png').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))

	def ratingBarWF(draw, dimensions, base):
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		if w < h:
			im = Image.open('UIelement3/ratingbar_vertical.png').convert('RGBA').resize((w, h))
		else:
			im = Image.open('UIelement3/ratingbar_horizontal.png').convert('RGBA').resize((w, h))
		base.paste(im, (dimensions['from']))

	def chronometerWF(draw, dimensions, base):
		im = Image.open('UIelement3/chronometer.png').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))


	#print inputFile_xml
	combine_img = Image.new('RGB', (512,256))
	source_img = Image.open(inputFile_xml.replace(".xml", ".png")).convert("RGBA")

	#create a totally white image
	target_img = Image.new('RGB', (800,1280), (255, 255, 255))

	fnt = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 17)


	#setup mapping for wireframe tool
	widgets_set = set(['ImageView', 'ImageButton', 'EditText', 'Button', 'TextView', 'ToggleButton', 'CheckedTextView', 'CheckBox', 'RadioButton', 'ProgressBar','Switch', 'SeekBar', 'WebView', 'MultiAutoCompleteTextView', 'VideoView', 'Spinner', 'RatingBar', 'Chronometer'])
	exclusive_set = set([ "DatePicker", 'CalendarView', 'TimePicker'])
	wireframe = {}


	wireframe = dict.fromkeys(['ImageView'], imageWF)
	wireframe.update(dict.fromkeys(['EditText', 'MultiAutoCompleteTextView'], editTextWF))
	wireframe.update(dict.fromkeys(['Button', 'ImageButton'], buttonWF));
	wireframe.update(dict.fromkeys(['TextView'], textViewWF));
	wireframe.update(dict.fromkeys(['ToggleButton'], toggleButtonWF));
	wireframe.update(dict.fromkeys(['CheckedTextView'], checkedTextViewWF));
	wireframe.update(dict.fromkeys(['CheckBox'], checkBoxWF));
	wireframe.update(dict.fromkeys(['RadioButton'], radioButtonWF));
	wireframe.update(dict.fromkeys(['ProgressBar'], progressBarWF));
	wireframe.update(dict.fromkeys(['Switch'], switchWF));
	wireframe.update(dict.fromkeys(['SeekBar'], seekBarWF));
	wireframe.update(dict.fromkeys(['WebView'], webViewWF));
	wireframe.update(dict.fromkeys(['VideoView'], videoViewWF));
	wireframe.update(dict.fromkeys(['Spinner'], spinnerWF));
	wireframe.update(dict.fromkeys(['RatingBar'], ratingBarWF));
	wireframe.update(dict.fromkeys(['Chronometer'], chronometerWF));


	draw = ImageDraw.Draw(target_img)
	widgetInfo_list = []
	with open(inputFile_xml) as f1:
		for line in f1:
			line = line.strip()
			if line.startswith("<node") and line.endswith("/>"): #it is a leaf node
				widgetName = re.findall(r'class="(.+?)"', line)[0].split(".")[-1]
				if "Layout" not in widgetName and widgetName not in exclusive_set:  #the leaf is not the layout
					coordinates = getCoordinates(line)
					area = calcArea(coordinates)
					widgetInfo_list.append((widgetName, coordinates, area))

	if len(widgetInfo_list) > 2:
		widgetInfoSorted_list = sorted(widgetInfo_list, key=operator.itemgetter(2), reverse = True)  #sort the widgets by the area in descent
		for (widgetName, coordinates, area) in widgetInfoSorted_list:
			if widgetName in widgets_set:
				if widgetName == "ImageView":
					a += 1
				elif widgetName == "EditText" or widgetName == "MultiAutoCompleteTextView":
					b += 1
				elif widgetName == "Button" or widgetName == "ImageButton":
					c += 1
				elif widgetName == "TextView":
					d += 1
				elif widgetName == "CheckedTextView":
					e += 1
				elif widgetName == "CheckBox":
					f += 1
				elif widgetName == "ProgressBar":
					g += 1
				wireframe[widgetName](draw, coordinates, target_img)

		if not os.path.exists(os.path.join(specificOutputDir, directory)):
			os.makedirs(os.path.join(specificOutputDir, directory))
			os.makedirs(os.path.join(os.path.join(specificOutputDir, directory), "source"))
			os.makedirs(os.path.join(os.path.join(specificOutputDir, directory), "target"))
		fileHash = str(a) + str("!") + str(b) + str("!") + str(c) + str("!") + str(d) + str("!") + str(e) + str("!") + str(f) + str("!") + str(g) + str("!") + fileHash
        	source_img.save(os.path.join(os.path.join(os.path.join(specificOutputDir, directory), "source"), fileHash+".png"), "PNG")
        	target_img.save(os.path.join(os.path.join(os.path.join(specificOutputDir, directory), "target"), fileHash+".png"), "PNG")
        	source_img = imageProcessing(source_img)
        	target_img = imageProcessing(target_img)
        	combine_img.paste(source_img, (0,0))
        	combine_img.paste(target_img, (256,0))
        	combine_img.save(os.path.join(os.path.join(specificOutputDir, directory), fileHash+".png"), "PNG")
        	return(len(widgetInfo_list))

def full_traceback(func):
    import traceback, functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = "{}\n\nOriginal {}".format(e, traceback.format_exc())
            raise type(e)(msg)
    return wrapper

@full_traceback
def collectFuntionalityWirify(inputDir):
	'''
	collect images whose activities about specific functionalities
	'''
	outputDir = "android_functionality_wirify1"
	#keywords_dic = {"login":["login", "signin"], "setting":["setting"], "search":["search"]}
	#intialize the output directory
	if not os.path.exists(outputDir):
		os.makedirs(outputDir)
		# for keyActivity in keywords_dic: #initialize the specific directories
		# 	os.makedirs(os.path.join(outputDir, keyActivity))
	hash_dict = {}
	totalString = ""
	countValid = 0

	packageName = "_".join(os.path.basename(os.path.normpath(inputDir)).split("_")[:-1])
	parentDir = os.path.join(inputDir, "stoat_fsm_output")
	f_file = os.path.join(parentDir, "explored_activity_list.txt")
	validFile_list = []  #store all valid file path

	if os.path.isfile(f_file):
		f = open(f_file)
		line_list = f.readlines()
		# print(type(line_list))
		# print(line_list)
		f.close()
		if len(line_list) > 0:
			signalLaterAPP = False
			if ":" in line_list[0]:  #these apps are later tested which has the activity ID
				signalLaterAPP = True  #the signal that denotes that the app is later marked
				for line in line_list:
					[id, activityName] = line.strip().split(":")
					if packageName in activityName:  #it belongs to this app, not the home screen of the phone
						activityName = activityName.lower()
						f_xmlFile = os.path.join(os.path.join(os.path.join(parentDir, "ui"), "S_" + str(id)+".xml"))
						if os.path.isfile(f_xmlFile):
							[boolvalue, hash_dict] = checkDuplicateFile(f_xmlFile, hash_dict)
							if boolvalue and checkFileValidity(f_xmlFile):
								flag = 0
								for xml in validFile_list:
									img1 = xml.replace("xml", "png")
									img2 = f_xmlFile.replace("xml", "png")
									if compareHisto(img1, img2) < 0.07:
										flag = 1
										break
								if flag == 0:
									validFile_list.append(f_xmlFile)


			else:  #for some apps, we donot record any ID, so we need to verify that all images are matched
				count = 0
				length = len(line_list)
				while count < length:
					count += 1
					f_xmlFile = os.path.join(os.path.join(os.path.join(parentDir, "ui"), "S_" + str(count)+".xml"))
					if os.path.isfile(f_xmlFile):
						with open(f_xmlFile) as f:
							if packageName in f.read():
								if len(line_list) > 0:
									activityName = line_list.pop(0).lower()   #pop up the first element
									[boolvalue, hash_dict] = checkDuplicateFile(f_xmlFile, hash_dict)
									if os.path.isfile(f_xmlFile) and boolvalue and checkFileValidity(f_xmlFile):
										flag = 0
										for xml in validFile_list:
											img1 = xml.replace("xml", "png")
											img2 = f_xmlFile.replace("xml", "png")
											try:
												if compareHisto(img1, img2) < 0.07:
													flag = 1
													break
											except Exception, e:
												print e
										if flag == 0:
											validFile_list.append(f_xmlFile)
								else:
									line_list = [False]
									break
					# else:
					# 	print(count)
					# 	break   #jump out of the loop

			hash_dic = {}  #the key is the hash value
			if (len(line_list) == 0 or line_list[0] != False) or signalLaterAPP:
				if len(validFile_list) > 0:
					specificOutputDir = outputDir
					count = 0
					for file in validFile_list:
						imageDir = file.replace(".xml", ".png")
						directory = file.replace(".xml", "")
						classname = directory.split("/")[1]
						classname = classname.split("_")[0]
						# category = "NULL"
						# if classname in dataDict.keys():
						# 	category = dataDict[classname]
						directory = directory.replace(".", "_")
						directory = directory.replace("/", "_")
						if os.path.isfile(imageDir):
							#content = xml2seq.xml2seq(file)   #only preserve the hierarchy structure
							#fileHash = hashlib.sha224(content).hexdigest()       #get the hash digest of the file
							fileHash = hashlib.sha224(file).hexdigest()
							#fileHash = category + str("!") + fileHash
							if fileHash not in hash_dic:
								#shutil.copy2(imageDir, specificOutputDir)
								
								try:
									len1 = drawImageLabel(file, fileHash, directory, specificOutputDir)
									if len1 != None:
										count += 1
										countValid += 1
										hash_dic[fileHash] = ""  #update the hash dictionary
										totalString += ("%s\t%s\n" % (fileHash, imageDir))

								except Exception, e:
									print e
				print "For %s, %s are valid " % (packageName, countValid)
			else:
				print "Something wrong with %s" % (packageName), len(line_list)


	return totalString

def multiThreadImageCollection(inputDir_list, outputFile):
	"""
	Due to the I/O speed limit and CPU computation, we decide to carry out the task in multi-thread
	"""
	dir_list = []  #get all subdirectories in the current directory
	for inputDir in inputDir_list:
		for dir in os.listdir(inputDir):
			currentDir = os.path.join(inputDir, dir)
			if os.path.isdir(currentDir) and currentDir.endswith("-output"):
				dir_list.append(currentDir)
	print "totally %s directory" % len(dir_list)
	pool = Pool(12)
	results = pool.map(collectFuntionalityWirify, dir_list)
	pool.close()
	pool.join()
	print "There are %s apps" % (len(results))
	with open(outputFile, "w") as fw:
		fw.write("".join(results))

if __name__ == '__main__':

	f_imageLabel = "android_label/image_label.txt"
	f_appDescription = "description.txt"
	f_imageDir = "android_label/"
	f_appCategory = "appCategory/"
	f_activityName = "activityName.txt"

	try:
		multiThreadImageCollection(["/home/cheer/disk1/ui"], "android_functionality_wirify1/android_functionality.txt")

	except Exception, e:
		print e
		raise
