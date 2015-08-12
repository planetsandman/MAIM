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
elev_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_elevation_input.xml"
veg_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_vegetation_input.xml"
site_template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_sites.xml"
place_name_path="D:\\data\\maim\\redeux\\metadata\\place_keywords.csv"
file_list=["input\\veg_cats.tif","input\\dem1m.tif","site_extent.shp"]
def listFiles(dir):
    rootdir = dir
    for root, subFolders, files in os.walk(rootdir):
        for file in files:
            yield os.path.join(root,file)
    return
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
###################### veg #################################
path=os.path.join(ws,file_list[0])
arcpy.MetadataImporter_conversion(veg_template_path,path)
try:
	tree = ET.parse(path+'.xml')
except IOError:
	print "File read error for ",path
root = tree.getroot()
set_place_kwords(root,SITE)
set_title(root,SITE,"Vegetation","Input","2008")
try:
	tree.write(path+'.xml')
except IOError:
	print "File write error for ",path
###################### elevation ############################
path=os.path.join(ws,file_list[1])
arcpy.MetadataImporter_conversion(elev_template_path,path)
try:
	tree = ET.parse(path+'.xml')
except IOError:
	print "File read error for ",path
root = tree.getroot()
set_place_kwords(root,SITE)
set_title(root,SITE,"Elevation 1m","Input","2008")
try:
	tree.write(path+'.xml')
except IOError:
	print "File write error for ",path
###################### site ##################################
path=os.path.join(ws,file_list[2])
arcpy.MetadataImporter_conversion(site_template_path,path)
try:
	tree = ET.parse(path+'.xml')
except IOError:
	print "File read error for ",path
root = tree.getroot()
set_place_kwords(root,SITE)
set_title(root,SITE,"Modeled","Region","2008")
try:
	tree.write(path+'.xml')
except IOError:
	print "File write error for ",path
###############################################    end    #############################################################
etime = time.clock()
print 'total processing time ',(etime-stime)/60.0, ' minutes'		