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
import math
import numpy as np

ImageFile.LOAD_TRUNCATED_IMAGES = True
#import xml2seq_verbose as xml2seq

# data = pd.read_csv('PlayStore_Full_2016_01_NoDescription_CSV.csv', error_bad_lines = False, sep = ';')
# dataDict = {}
# dataDictRe = {}
# for index, row in data.iterrows():
#     dataDict[row["Url"].replace("https://play.google.com/store/apps/details?id=",'')] = row["Category"]
#     if dataDictRe.has_key(row["Category"]) == False:
#         dataDictRe[row["Category"]] = [row["Url"].replace("https://play.google.com/store/apps/details?id=",'')]
#     else:
#         dataDictRe[row["Category"]].append(row["Url"].replace("https://play.google.com/store/apps/details?id=",''))
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
				#if float(len(bounds_list)) / len(set(bounds_list)) < 1.2:   #so far, we do not check this option
					#print len(text_list), len(set(text_list)), inputFile.split("\\")[-1]
				return True

	return False
def compareHisto(first, sec):
	try:
		imA = Image.open(open(first,'rb'))
	except IOError:
		print "First FIle: %s is wrong" % first
		return 'error1'
	try:
		imB = Image.open(open(sec,'rb'))
	except IOError:
		print "Second FIle: %s is wrong" % sec
		return 'error2'
	# Normalise the scale of images
	if imA.size[0] > imB.size[0]:
		imA = imA.resize((imB.size[0], imA.size[1]))
	else:
		imB = imB.resize((imA.size[0], imB.size[1]))

	if imA.size[1] > imB.size[1]:
		imA = imA.resize((imA.size[0], imB.size[1]))
	else:
		imB = imB.resize((imB.size[0], imA.size[1]))
	#print(len(np.array(imA).shape))	

	#print('imB.shape',np.array(imB).shape)
	hA = imA.histogram()
	hB = imB.histogram()
	if len(hA) != len(hB):
		A,B,C,D = imA.split()
		imA = Image.merge('RGB',(A,B,C))
		print('shape',np.array(imA).shape)
	sum_hA = 0.0
	sum_hB = 0.0
	diff = 0.0
	#print('aMAX,MIN:',imA.getextrema())
	#print('aM',len(imA.getextrema()))
	#print('bMAX,MIN:',imB.getextrema())

	for i in range(len(hA)):
		#print(sum_hA)
		sum_hA += hA[i]
		#try:
		sum_hB += hB[i]
		#except IndexError:
		#	print('len(hA):', len(hA), imA.size[0], imA.size[1])
		#	print('len(hB):', len(hB), imB.size[0], imB.size[1])
		#	A,B,C,D = imA.split()
		#	print('A-4:::'D)
		#	print('A-4',np.array(imA).shape,'\n',np.array(imA)[0][0])
		#	print('aMAX,MIN:',imA.getextrema())
		#	print('bMAX,MIN:',imB.getextrema())
			#imshow()
			
		#	print('First:',first)
		#	print('Second:',sec)
			
		diff += abs(hA[i] - hB[i])

	return diff/(2*max(sum_hA, sum_hB))

def checkDuplicateFile(inputFile, hash_dict):
	with open(inputFile) as f:
		content = f.read()
		content = re.sub(r'(?!.*\/>).*', "", content)
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

### eg. file: si/com.jaemin.kbible_36-output/stoat_fsm_output/ui/S_1.xml					
###     directory: sicom_jaemin_kbible_36-output_stoat_fsm_output_ui_S_1
###     specificOutputDir: "android_functionality_wirify6"
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
	h = 0
	def calcArea(dimensions):
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		return w * h

	def getCoordinates(line):
		#coordinates = re.findall(r"(?<=\[).*?(?=\])", node.attrib["bounds"])
		coordinates = re.findall(r"(?<=\[).*?(?=\])", re.findall(r'bounds="(.+?)"', line)[0])
		dim = {}
		area = 800*1280*0.1*0.1
		a,b = list(map(int, coordinates[0].split(",")))
		c,d = list(map(int, coordinates[1].split(",")))
		if a < 0 or b < 0 or c < 0 or d < 0 or a > 800 or c > 800 or b > 1280 or d > 1280:
			return None
		w = c-a
		l = d-b
		if w*l <= area:
			dim['from'] = tuple([a,b])
			dim['to'] = tuple([c,d])
		else:
			### Scale
			w_scale = int(w*0.05) #int(w*0.1)
			l_scale = int(l*0.05) #int(l*0.1)
			if (l-2*l_scale)*(w-2*w_scale) < area:
				w_scale = 0 #int(w*0.05)
				l_scale = 0 #int(l*0.05)
			dim['from'] = tuple([a+w_scale,b+l_scale])
			dim['to'] = tuple([c-w_scale,d-l_scale])

		return dim

	def imageWF(draw, dimensions, base):
		### #ffffff white, #ff0000 red
		draw.rectangle((dimensions['from'], dimensions['to']), outline="#ffffff", fill="#ff0000")
		### draw diagonal lines
		draw.line((dimensions['from'], dimensions['to']), fill="#ffffff", width=2)
		draw.line((dimensions['from'][0], dimensions['to'][1], dimensions['to'][0], dimensions['from'][1]), fill="#ffffff", width=2)

	def editTextWF(draw, dimensions, base):
		fntsize = 1
		### "#0000ff":Blue
		draw.rectangle((dimensions['from'], dimensions['to']), outline="black", fill="#0000ff")

		'''
		fnt = ImageFont.truetype("arial.ttf", fntsize)
		while fnt.getsize('I')[1] < dimensions['to'][1] - dimensions['from'][1]:
			fntsize += 1
			fnt = ImageFont.truetype("arial.ttf", fntsize)

		draw.text((dimensions['from'][0]+3, dimensions['from'][1]), 'I', font=fnt, fill="black")
		'''

	def buttonWF(draw, dimensions, base):
		### "#ffff00":yellow
		draw.rectangle((dimensions['from'], dimensions['to']), outline="#323232", fill="#ffff00")

	def textViewWF(draw, dimensions, base):
		'''
		if "title" in node.attrib["resource-id"]:
			draw.rectangle((dimensions['from'], dimensions['to']), fill="#343434")
		else:
			draw.rectangle((tuple(numpy.add(dimensions['from'],(10, 10))), tuple(numpy.subtract(dimensions['to'],(10, 10)))), fill="#cccccc")
		'''
		#draw.rectangle((dimensions['from'], dimensions['to']), fill="#343434")
		### "#00ff00":Green
		draw.rectangle((tuple(numpy.add(dimensions['from'],(10, 10))), tuple(numpy.subtract(dimensions['to'],(10, 10)))), fill="#00ff00")

	def toggleButtonWF(draw, dimensions, base):
		### dark blue
		draw.rectangle((dimensions['from'], dimensions['to']), outline="#486996", fill="#8eb3ee")

	def checkedTextViewWF(draw, dimensions, base):
		### blue green mix
		draw.rectangle((dimensions['from'], dimensions['to']), outline="#343434", fill="#4fccc6")

	def viewWF(draw, dimensions, base):
		'''
		if node.attrib["text"] != "" and node.attrib["content-desc"] != "":
			if node.attrib["focusable"] == "false":
				textViewWF(node, draw, dimensions)
			else:
				buttonWF(node, draw, dimensions)
		'''
		### dark grey
		draw.rectangle((dimensions['from'], dimensions['to']), fill="#bbbbbb")

	def checkBoxWF(draw, dimensions, base):
		# dark yellow
		draw.rectangle((dimensions['from'], dimensions['to']), fill="#f1c40f")

	def progressBarWF(draw, dimensions, base):
		#draw.rectangle((dimensions['from'], dimensions['to']), fill="#636363")
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]

		if w > h and w > 2 * h:
			im = Image.open('UIelement/progressbar_horizontal.png').convert('RGBA').resize((w, h))
		elif h > w and h > 2 * w:
			im = Image.open('UIelement/progressbar_vertical.png').convert('RGBA').resize((w, h))
		else:
			im = Image.open('UIelement/progressbar_circular.png').convert('RGBA').resize((w, h))

		base.paste(im, (dimensions['from']))

	def radioButtonWF(draw, dimensions, base):
		### yellow 
		### ellipse
		##### orange
		draw.rectangle((dimensions['from'], dimensions['to']), fill="#FFA500")
		# draw.ellipse((dimensions['from'][0], dimensions['from'][1], dimensions['to'][0], dimensions['to'][1]), fill="#ffff00")

	def switchWF(draw, dimensions, base):
		draw.rectangle((dimensions['from'], dimensions['to']), fill="#607d8b")
		switch = {}
		switch["from"] = tuple((dimensions["from"][0] + ((dimensions["to"][0] - dimensions["from"][0])/2), dimensions["from"][1]))
		switch["to"] = dimensions["to"]
		draw.rectangle((switch["from"], switch["to"]), fill="#fbea38")

	def seekBarWF(draw, dimensions, base):
		#draw.rectangle((dimensions['from'], dimensions['to']), fill="#000000")
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		if w < h:
			im = Image.open('UIelement/seekbar_vertical.png').convert('RGBA').resize((w, h))
		else:
			im = Image.open('UIelement/seekbar_horizontal.png').convert('RGBA').resize((w, h))
		base.paste(im, (dimensions['from']))

	def webViewWF(draw, dimensions, base):
		draw.rectangle((dimensions['from'], dimensions['to']), fill="#535353")

	def videoViewWF(draw, dimensions, base):
		im = Image.open('UIelement/videoview.png').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))

	def spinnerWF(draw, dimensions, base):
		im = Image.open('UIelement/spinner.png').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))

	def ratingBarWF(draw, dimensions, base):
		w = dimensions['to'][0] - dimensions['from'][0]
		h = dimensions['to'][1] - dimensions['from'][1]
		if w < h:
			im = Image.open('UIelement/ratingbar_vertical.png').convert('RGBA').resize((w, h))
		else:
			im = Image.open('UIelement/ratingbar_horizontal.png').convert('RGBA').resize((w, h))
		base.paste(im, (dimensions['from']))

	def chronometerWF(draw, dimensions, base):
		im = Image.open('UIelement/chronometer.png').convert('RGBA').resize((dimensions['to'][0] - dimensions['from'][0], dimensions['to'][1] - dimensions['from'][1]))
		base.paste(im, (dimensions['from']))

	#print inputFile_xml
	combine_img = Image.new('RGB', (512,256))
	source_img = Image.open(open(inputFile_xml.replace(".xml", ".png"),'rb')).convert("RGBA")

	#create a totally white image
	target_img = Image.new('RGB', (800,1280), (255, 255, 255))

	fnt = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 17)


	#setup mapping for wireframe tool
	widgets_set = set(['ImageView', 'ImageButton', 'EditText', 'Button', 'TextView', 'ToggleButton', 'CheckedTextView', 'View', 'CheckBox', 'RadioButton', 'ProgressBar','Switch', 'SeekBar', 'WebView', 'CompoundButton', 'MultiAutoCompleteTextView', 'VideoView', 'Spinner', 'RatingBar', 'Chronometer'])
	exclusive_set = set(['ScrollView', "HorizontalScrollView", "RecyclerView", "TableRow", "ViewPager"])
	wireframe = {}


	wireframe = dict.fromkeys(['ImageView', 'Image'], imageWF)
	wireframe.update(dict.fromkeys(['EditText', 'MultiAutoCompleteTextView'], editTextWF))
	wireframe.update(dict.fromkeys(['Button', 'ImageButton','CompoundButton'], buttonWF));
	wireframe.update(dict.fromkeys(['TextView'], textViewWF));
	wireframe.update(dict.fromkeys(['ToggleButton'], toggleButtonWF));
	wireframe.update(dict.fromkeys(['CheckedTextView'], checkedTextViewWF));
	wireframe.update(dict.fromkeys(['View'], viewWF));
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
					if coordinates == None:
						continue
					area = calcArea(coordinates)
					widgetInfo_list.append((widgetName, coordinates, area))
	if len(widgetInfo_list) > 2:
		widgetInfoSorted_list = sorted(widgetInfo_list, key=operator.itemgetter(2), reverse = True)  #sort the widgets by the area in descent
		for (widgetName, coordinates, area) in widgetInfoSorted_list:
			if widgetName in widgets_set:
				if widgetName == "ImageView" or widgetName == "Image":
					a += 1
				elif widgetName == "EditText" or widgetName == "MultiAutoCompleteTextView":
					b += 1
				elif widgetName == "Button" or widgetName == "ImageButton" or widgetName == "CompoundButton":
					c += 1
				elif widgetName == "TextView":
					d += 1
				elif widgetName == "CheckedTextView":
					e += 1
				elif widgetName == "View":
					f += 1
				elif widgetName == "CheckBox":
					g += 1
				elif widgetName == "ProgressBar":
					h += 1
				wireframe[widgetName](draw, coordinates, target_img)
			else:
				draw.rectangle((coordinates["from"], coordinates["to"]), fill="#dddddd") #draw other infrequent widgets
		if a+b+c+d+e+f+g+h >76 or a+b+c+d+e+f+g+h < 4:
			return None
		if not os.path.exists(os.path.join(specificOutputDir, directory)):
			os.makedirs(os.path.join(specificOutputDir, directory))
			os.makedirs(os.path.join(os.path.join(specificOutputDir, directory), "source"))
			os.makedirs(os.path.join(os.path.join(specificOutputDir, directory), "target"))
			fileHash = str(a) + str("!") + str(b) + str("!") + str(c) + str("!") + str(d) + str("!") + str(e) + str("!") + str(f) + str("!") + str(g) + str("!") + str(h) + str("!") + fileHash
			source_img.save(os.path.join(os.path.join(os.path.join(specificOutputDir, directory), "source"), fileHash+".png"), "PNG")
			target_img.save(os.path.join(os.path.join(os.path.join(specificOutputDir, directory), "target"), fileHash+".png"), "PNG")
			source_img = imageProcessing(source_img)
			target_img = imageProcessing(target_img)
			combine_img.paste(source_img, (0,0))
			combine_img.paste(target_img, (256,0))
			combine_img.save(os.path.join(os.path.join(specificOutputDir, directory), fileHash+".png"), "PNG")
			#print('source:',inputFile_xml)
			#print('des:',os.path.join(specificOutputDir, directory))

			#os.system('cp "%s" "%s"' %(inputFile_xml,os.path.join(specificOutputDir, directory)))

			return(len(widgetInfo_list))
	

# def compareHisto(first, sec):
# 	imA = Image.open(first)
# 	imB = Image.open(sec)
#
# 	# Normalise the scale of images
# 	if imA.size[0] > imB.size[0]:
# 		imA = imA.resize((imB.size[0], imA.size[1]))
# 	else:
# 		imB = imB.resize((imA.size[0], imB.size[1]))
#
# 	if imA.size[1] > imB.size[1]:
# 		imA = imA.resize((imA.size[0], imB.size[1]))
# 	else:
# 		imB = imB.resize((imB.size[0], imA.size[1]))
#
# 	hA = imA.histogram()
# 	hB = imB.histogram()
# 	sum_hA = 0.0
# 	sum_hB = 0.0
# 	diff = 0.0
#
# 	for i in range(len(hA)):
# 		#print(sum_hA)
# 		sum_hA += hA[i]
# 		sum_hB += hB[i]
# 		diff += abs(hA[i] - hB[i])
#
# 	return diff/(2*max(sum_hA, sum_hB))

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
	outputDir = "android_functionality_wirify_fix2"
	#keywords_dic = {"login":["login", "signin"], "setting":["setting"], "search":["search"]}
	#intialize the output directory
	if not os.path.exists(outputDir):
		print 'path_Not_Exist'
		os.makedirs(outputDir)
		# for keyActivity in keywords_dic: #initialize the specific directories
		# 	os.makedirs(os.path.join(outputDir, keyActivity))
	hash_dict = {}
	totalString = ""
	countValid = 0

	packageName = "_".join(os.path.basename(os.path.normpath(inputDir)).split("_")[:-1])
	# print(inputDir)
	# print("packagename")
	# print(packageName)
	# print packageName
	
	## eg. parenDir: si/com.jaemin.kbible_36-output/stoat_fsm_output
	parentDir = os.path.join(inputDir, "stoat_fsm_output")
	## eg. f_file: si/com.jaemin.kbible_36-output/stoat_fsm_output/explored_activity_list.txt
	f_file = os.path.join(parentDir, "explored_activity_list.txt")
	validFile_list = []  #store all valid file path

	#finished_app = str(os.listdir(outputDir))
	#if parentDir.split('/')[-2].replace('.','_').replace('/','_') in finished_app:
	#	#print('Finished:',parentDir.split('/')[-2].replace('.','_').replace('/','_'))
	#	return '\n'

	if os.path.isfile(f_file):
		#print('Current processing:' ,parentDir.split('/')[-2])


		f = open(f_file)
		line_list = f.readlines()
		# print(type(line_list))
		# print(line_list)
		f.close()
		
		if len(line_list) > 0:
			signalLaterAPP = False
			# reduce near duplicate ui images
			if ":" in line_list[0]:  #these apps are later tested which has the activity ID
				signalLaterAPP = True  #the signal that denotes that the app is later marked
				for line in line_list:
					#### !!!!!
					tmp = line.strip().split(":")
					if len(tmp) > 2:
						signalLaterAPP = False
						break
					[id, activityName] = tmp[0], tmp[1]
					####################
					if packageName in activityName:  #it belongs to this app, not the home screen of the phone
						activityName = activityName.lower()
						## eg. f_xmlFile: si/com.jaemin.kbible_36-output/stoat_fsm_output/ui/S_1.xml
						f_xmlFile = os.path.join(os.path.join(os.path.join(parentDir, "ui"), "S_" + str(id)+".xml"))
						if os.path.isfile(f_xmlFile):
							[boolvalue, hash_dict] = checkDuplicateFile(f_xmlFile, hash_dict)
							if boolvalue and checkFileValidity(f_xmlFile):
								flag = 0
								if len(validFile_list) == 0:
									try:
										aa = Image.open(open(f_xmlFile.replace("xml", "png"),'rb'))
									except IOError:
										flag = 1
								for xml in validFile_list:
									img1 = xml.replace("xml", "png")
									img2 = f_xmlFile.replace("xml", "png")
									
									compare_result = compareHisto(img1, img2)
									if compare_result == 'error1':
										validFile_list.remove(xml)
										continue
									if compare_result == 'error2' or compare_result < 0.07:
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
										if len(validFile_list) == 0:
											try:
												aa = Image.open(open(f_xmlFile.replace("xml", "png"),'rb'))
											except IOError:
												flag = 1
										for xml in validFile_list:
											img1 = xml.replace("xml", "png")
											img2 = f_xmlFile.replace("xml", "png")
											compare_result = compareHisto(img1, img2)
											if compare_result == 'error1':
												validFile_list.remove(xml)
												continue
											if compare_result == 'error2' or compare_result < 0.07:
												flag = 1
												break
										if flag == 0:
											validFile_list.append(f_xmlFile)
								else:
									line_list = [False]
									break
					# else:
					# 	print(count)
					# 	break   #jump out of the loop

			hash_dic = {}  #the key is the hash value
			# seperate ui images, one image one dir
			if (len(line_list) == 0 or line_list[0] != False) or signalLaterAPP:
				if len(validFile_list) > 0:
					specificOutputDir = outputDir
					count = 0
					for file in validFile_list:
						### eg. imageDir: si/com.jaemin.kbible_36-output/stoat_fsm_output/ui/S_1.png
						imageDir = file.replace(".xml", ".png")
						### eg. directory: si/com.jaemin.kbible_36-output/stoat_fsm_output/ui/S_1
						directory = file.replace(".xml", "")
						### eg. classname: com.jaemin.kbible_36-output
						classname = directory.split("/")[1]
						### eg. classname: com.jaemin.kbible
						classname = classname.split("_")[0]
						# category = "NULL"
						# if classname in dataDict.keys():
						# 	category = dataDict[classname]
						### eg. directory: sicom_jaemin_kbible_36-output/stoat_fsm_output/ui/S_1
						directory = directory.replace(".", "_")				
						### eg. directory: sicom_jaemin_kbible_36-output_stoat_fsm_output_ui_S_1
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
								except Exception, e:
									print e
								try:
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
	'''
	desk = ['verbo2','verbo2-2']
	skip = set()
	for dirs in desk:
		for existdir in os.listdir(dirs):
			if os.path.isdir(dirs + '/' +	existdir):
				name = existdir.split('_')
				start_index = name.index('verbo2') +1
				end_index = name.index('stoat') -1
				sname = ''
				for i in range(start_index,end_index):
					sname = sname + name[i] + '.'
				sname = sname[:-1]+'_'+name[end_index]
				#print(sname)
				skip.add(sname)
	print('skip',len(skip),' directory')
	#print(skip)
	'''
	for inputDir in inputDir_list:
		for dir in os.listdir(inputDir):
			currentDir = os.path.join(inputDir, dir)
			if os.path.isdir(currentDir) and currentDir.endswith("-output"):
				#if dir not in skip:
					#print(dir)
				dir_list.append(currentDir)

	print "totally %s directory" % len(dir_list)
	pool = Pool(8)
	results = pool.map(collectFuntionalityWirify, dir_list)
	pool.close()
	pool.join()
	print "There are %s apps" % (len(results))
	with open(outputFile, "w") as fw:
		fw.write("".join(results))


'''''
Line 388: OutputDir
InputDir
Outputfile
'''
if __name__ == '__main__':
	'''''
	f_imageLabel = "android_label/image_label.txt"
	f_appDescription = "description.txt"
	f_imageDir = "android_label/"
	f_appCategory = "appCategory/"
	f_activityName = "activityName.txt"
	'''
	#multiThreadImageCollection(["si"], "android_functionality_wirify5/android_functionality.txt")

	log_path = "android_functionality_wirify_fix2/android_functionality.txt"
	if os.path.exists(log_path):
		os.remove(log_path)
	try:
		#collectFuntionalityImage(r"E:\PhD\myPaper\sketch2UI\experiment\data", "functionality")
		#multiThreadImageCollection([r"E:\PhD\myPaper\sketch2UI\experiment\data\test"], "android_functionality/android_functionality.txt")
		#multiThreadImageCollection(["/home/ccy/gui_learning/top_10000_google_play_20170510_cleaned"], "android_functionality_wirify/android_functionality.txt")
		multiThreadImageCollection(["/media/cheer/New Volume/5K_data/verbo1","/media/cheer/New Volume/5K_data/verbo2","/media/cheer/New Volume/5K_data/verbo3"], log_path)

	except Exception, e:
		print e
		raise
