# -*- coding: utf-8 -*-
#Steven Guinn
#12/10/2014
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146
#301 Braddock Rd    Frostburg MD 215325


import arcpy,time
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
template_path = "D:\\data\\maim\\redeux\\metadata\\project_template_elevation.xml"
path = "D:\\data\\maim\\redeux\\metadata\\high_2010_elev.tif"
place_name_path="D:\\data\\maim\\redeux\\metadata\\place_keywords.csv"
SITE='gwmp_b'
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
	iterator = root.getiterator('placeKeys')
	for element in iterator:
		for item in place_keyword_dict[SITE]:
			new_sub_element = ET.SubElement(element,'keyword')
			new_sub_element.text=item
def set_title(xml_root,SITE,SLR,TYPE,YEAR):
	iterator = root.getiterator('resTitle')
	for element in iterator:
		element.text=SITE+" "+SLR+" "+TYPE+" "+YEAR
def set_temp_kwords(xml_root,YEAR):
	iterator = root.getiterator('tempKeys')
	for element in iterator:
		for sub_element in element.findall('keyword'):
			start_year=sub_element.text
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text=YEAR
	temp_range= start_year+" to "+YEAR
	iterator = root.getiterator('searchKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text=temp_range
def set_protected(xml_root):
	iterator = root.getiterator('searchKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Protected"
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Developed Land"
	iterator = root.getiterator('themeKeys')
	for element in iterator:
		new_sub_element = ET.SubElement(element,'keyword')
		new_sub_element.text="Protect Developed Land"
#######################################################################################################################
stime = time.clock()

place_keyword_dict=getKeywords(place_name_path)
arcpy.MetadataImporter_conversion(template_path,path)

tree = ET.parse(path+'.xml')
root = tree.getroot()
iterator = root.getiterator('placeKeys')
for element in iterator:
	for sub_element in element.findall('keyword'):
		print sub_element.tag,sub_element.text
set_place_kwords(root,SITE)								#set_plcae() function call
print"again"

iterator = root.getiterator('placeKeys')
for element in iterator:
	for sub_element in element.findall('keyword'):
		print sub_element.tag,sub_element.text

iterator = root.getiterator('resTitle')
for element in iterator:
	print element.tag,element.text

set_title(root,SITE,"High","1m Elevation","2010")		#set_title() function call
print"again"
iterator = root.getiterator('resTitle')
for element in iterator:
	print element.tag,element.text
set_temp_kwords(root,'2010')
set_protected(root)
tree.write(path+'.xml')
etime = time.clock()
print 'total processing time ',etime-stime, ' seconds'		