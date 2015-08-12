# -*- coding: utf-8 -*-
#Steven Guinn
#8/04/2014
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146
#301 Braddock Rd    Frostburg MD 215325

import os
import sys
import time
import arcpy
stime = time.clock()
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
#######################################################################################################################
ws =sys.argv[1]
SITE=sys.argv[2]
elev_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_elevation.xml"
veg_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_vegetation.xml"
prob_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_probability.xml"
place_name_path="D:\\data\\maim\\redeux\\metadata\\place_keywords.csv"
def listFiles(dir):
    rootdir = dir
    for root, subFolders, files in os.walk(rootdir):
        for file in files:
            yield os.path.join(root,file)
    return
def veg_metadata(path,template,place_dict,SITE):
	bname = os.path.split(t)[1]
	words = bname.split('_')
	if words[0]=='protected':
		PROTECTED=True
		SLR=words[1]
		YEAR=words[2]
		TYPE="Protected Vegetation"
	else:
		PROTECTED=False
		SLR=words[0]
		YEAR=words[1]
		TYPE="Vegetation"
	arcpy.MetadataImporter_conversion(template,path)
	try:
		tree = ET.parse(path+'.xml')
	except IOError:
		print "File read error for ",path
		return -1
	root = tree.getroot()
	set_place_kwords(root,SITE)
	set_title(root,SITE,SLR,YEAR,TYPE)
	set_temp_kwords(root,YEAR)
	if PROTECTED:
		set_protected(root)
	try:
		tree.write(path+'.xml')
	except IOError:
		print "File write error for ",path
		return -1
	return 1
def elev_metadata(path,template,place_dict,SITE):
	bname = os.path.split(t)[1]
	words = bname.split('_')
	SLR=words[0]
	YEAR=words[1]
	TYPE="Elevation 1 meter"
	arcpy.MetadataImporter_conversion(template,path)
	try:
		tree = ET.parse(path+'.xml')
	except IOError:
		print "File read error for ",path
		return -1
	root = tree.getroot()
	set_place_kwords(root,SITE)
	set_title(root,SITE,SLR,YEAR,TYPE)
	set_temp_kwords(root,YEAR)
	try:
		tree.write(path+'.xml')
	except IOError:
		print "File write error for ",path
		return -1
	return 1
def probability_metadata(path,template,place_dict,SITE):
	bname = os.path.split(t)[1]
	words = bname.split('_')
	SLR=words[0]
	YEAR=words[1]
	TYPE="Monte Carlo Probability"
	arcpy.MetadataImporter_conversion(template,path)
	try:
		tree = ET.parse(path+'.xml')
	except IOError:
		print "File read error for ",path
		return -1
	root = tree.getroot()
	set_place_kwords(root,SITE)
	set_title(root,SITE,SLR,YEAR,TYPE)
	set_temp_kwords(root,YEAR)
	try:
		tree.write(path+'.xml')
	except IOError:
		print "File write error for ",path
		return -1
	return 1
def getKeywords(path):
	f=open(path,'r')
	linelist=f.readlines()
	keyword_dict=dict()
	for line in linelist:
		words=line.strip().split(',')
		key = words.pop(0).lower()
		keyword_dict[key]=words
	f.close()
	return keyword_dict
def set_place_kwords(xml_root,SITE):
	iterator = xml_root.getiterator('placeKeys')
	for element in iterator:
		for item in place_keyword_dict[SITE]:
			new_sub_element = ET.SubElement(element,'keyword')
			new_sub_element.text=item
def set_title(xml_root,SITE,SLR,YEAR,TYPE):
	iterator = xml_root.getiterator('resTitle')
	for element in iterator:
		element.text=SITE+" "+SLR+" "+YEAR+" "+TYPE
def set_temp_kwords(xml_root,YEAR):
	iterator = xml_root.getiterator('tempKeys')
	for element in iterator:
		for sub_element in element.findall('keyword'):
			start_year=sub_element.text
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text=YEAR
	temp_range= start_year+" to "+YEAR
	iterator = xml_root.getiterator('searchKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text=temp_range
def set_protected(xml_root):
	iterator = xml_root.getiterator('searchKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Protected"
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Developed Land"
	iterator = xml_root.getiterator('themeKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Protect Developed Land"
###############################################    Main   #############################################################
place_keyword_dict=getKeywords(place_name_path)
tree=listFiles(ws)
for t in tree:
	if os.path.splitext(t)[1]=='.tif':								#check to see if file is a .tif
		bname = os.path.split(t)[1]
		words = bname.split('_')
		if words[-1]=='veg.tif':									#test for a veg file name
			veg_metadata(t,veg_template_path,place_keyword_dict,SITE)
			print "processing ",bname
		if words[-1]=='elev.tif':									#test for a elevation file name
			elev_metadata(t,elev_template_path,place_keyword_dict,SITE)
			print "processing ",bname
		if words[-1]=='probability.tif':							#test for a probability file name
			probability_metadata(t,prob_template_path,place_keyword_dict,SITE)
			print "processing ",bname
etime = time.clock()
print 'total processing time ',(etime-stime)/60.0, ' minutes'		