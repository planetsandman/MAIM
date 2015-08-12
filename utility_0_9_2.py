# -*- coding: utf-8 -*-
#Steven Guinn
#08/05/2015
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146
#301 Braddock Rd    Frostburg MD 215325

#################################################### Imports ###############################################################
# This utility file must be within the same local scope of the main module
############################################################################################################################
import os
import sys
import osgeo.ogr as ogr
import osgeo.osr as osr
from osgeo import gdal
from osgeo import gdal_array
from osgeo.gdal_array import *
from osgeo.gdalconst import *
import numpy as np
import random
import math
import shutil
from copy import deepcopy
###################################################### Constants ###########################################################
CELLSIZE=1.0
DEFAULT_R=10.0
CHAR_LEN='4'
VARLIST=('maxelev','maxunit','maxcomplex','maxboundarycoefficient','minelev','minunit','mincomplex','minboundarycoefficient','fromcat','cat','changecat','accretioncat','min_boundary_set','max_boundary_set','abbreviation')
SHORT_VARLIST=('maxelev','minelev','fromcat','cat','changecat','min_boundary_set','max_boundary_set')
BOUNDARY_VARLIST=('maxelev','minelev')
SUFFIX_LIST=('Min','Max','Mean','1Q','2Q','3Q')
###################################################### Housekeeping Functions ##############################################
def cleanMakeDir(out_dir,mode=0777):
	if os.path.exists(out_dir):
		print "Output Directory exist!"
		removeall(out_dir)   #this erases the contents of the directory
		print "Cleaned Output Directory!"
	else:
		os.mkdir(out_dir)
		os.chmod(out_dir,mode)
		print "Created Output Directory!"
def rmgeneric(path, __func__):
    try:
        __func__(path)
        print 'Removed ', path
    except OSError, (errno, strerror):
        print "Error" % {'path' : path, 'error': strerror }           
def removeall(path):

    if not os.path.isdir(path):
        return
    
    files=os.listdir(path)

    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f=os.rmdir
            rmgeneric(fullpath, f)   
######################################################   I/O Functions        ##############################################
def validate_paramfile(infile,VERBOSE=False):				#check to see if the parameters are valid before running the model
	infile.seek(0)	#reset the file pointer to the start position
	linelist=infile.readlines()
	temp_list=list()					#strip out comments
	for item in linelist:				#strip out comments
		comment=item.strip().find('#')	#strip out comments
		if comment >= 0:				#strip out comments
			if comment == 0:			#strip out comments
				pass					#strip out comments
			else:						#strip out comments
				temp_list.append(item[:comment])###########
		else:							#strip out comments
			temp_list.append(item)		#strip out comments
	linelist=temp_list					#strip out comments
	pathlist=list()
	for line in linelist:
		if len(line.strip().split(',')) <=2:
			if line.strip().split(',')[1].count(os.sep) > 0:
				pathlist.append(line.strip().split(','))
			else:
				pass
		else:
			pass
	if VERBOSE:
		for path in pathlist:
			status=os.path.exists(path[1])
			if status:
				print path[0],'\t',path[1],'\t',status
			else:
				print path[1],'\t',status
				return status
		print os.linesep
	else:
		for path in pathlist:
			status=os.path.exists(path[1])
			if not status:
				return status
	return True
def read_paramfile(infile,VERBOSE=False,SUMMARY=False):	
	infile.seek(0)						#reset the file pointer to the start position
	linelist=infile.readlines()
	temp_list=list()					#strip out comments
	for item in linelist:				#strip out comments
		comment=item.strip().find('#')	#strip out comments
		if comment >= 0:				#strip out comments
			if comment == 0:			#strip out comments
				pass					#strip out comments
			else:						#strip out comments
				temp_list.append(item[:comment])###########
		else:							#strip out comments
			temp_list.append(item)		#strip out comments
	linelist=temp_list					#linelist now only has uncommented lines
	parameter_list=list()
	cat_list=list()
	new_keys=list()
	master_dict={}
	for line in linelist:
		if len(line.strip().split(',')) <=2:		#check to see if the line is a model or vegetation class parameter
			var1=line.strip().split(',')[0].strip().lower()
			if os.path.isfile(line.strip().split(',')[1].strip()):
				val1=line.strip().split(',')[1].strip()
			else:
				val1=line.strip().split(',')[1].strip().lower()
			master_dict[var1]=val1
			parameter_list.append(var1)
		else:
			vname=line.strip().split(',')[0].strip().lower()
			var1=line.strip().split(',')[1].strip().lower()
			val1=line.strip().split(',')[2].strip().lower()
			if not master_dict.has_key(vname):
				master_dict[vname]=dict()
				master_dict[vname][var1]=val1
				cat_list.append(vname)
			else:
				master_dict[vname][var1]=val1
				master_dict[vname]['min_boundary_set']=False
				master_dict[vname]['max_boundary_set']=False
	if os.path.isfile(master_dict['boundary_name_file']):		#this lets us overload the function to only process a subset of the classes
		f=open(master_dict['boundary_name_file'],'r')
		new_cat_list=list()
		lines= f.readlines()
		f.close()
		badcat=0
		for line in lines:
			new_cat_list.append(line.strip().lower())
		for cat in new_cat_list:
			if cat_list.count(cat) != 1:
				badcat+=1
				print cat
			else:
				pass
		if badcat == 0:
			cat_list=new_cat_list
	if VERBOSE:
		if os.path.isfile(master_dict['boundary_name_file']):
			print "Using external Catagory File"
		all_list=parameter_list
		all_list.extend(cat_list)
		if not SUMMARY:
			for item in all_list:
				if type(master_dict[item]) is str:
					print item,master_dict[item]
				if type(master_dict[item]) is dict:
					print item
					print "\tUpward Terminal Catagory",isTerminal(master_dict[item],upward=True)		
					print "\tDownward Terminal Catagory",isTerminal(master_dict[item],upward=False)  
					for var in VARLIST:
						print '\t',var,':',master_dict[item][var]
				else:
					pass
		else:
			for item in all_list:
				if type(master_dict[item]) is str:
					print item,master_dict[item]
				if type(master_dict[item]) is dict:
					print item
					for var in SHORT_VARLIST:
						print '\t',var,':',master_dict[item][var]
	return master_dict,parameter_list,cat_list
def writeIntRaster(outpath,inArray,template_DS,INT16_NODATA=-9999,mode=0777):#writes a single band raster to the same extent and projection as the template DS
	image_driver=template_DS.GetDriver()
	image_out_DS=image_driver.Create(outpath,template_DS.RasterXSize,template_DS.RasterYSize,template_DS.RasterCount,GDT_Int16)
	projection=template_DS.GetProjectionRef()
	geotransform=template_DS.GetGeoTransform()
	image_out_DS.SetProjection(projection)
	image_out_DS.SetGeoTransform(geotransform)
	image_band_out=image_out_DS.GetRasterBand(1)
	image_band_out.SetNoDataValue(INT16_NODATA)
	image_band_out=gdal_array.BandWriteArray(image_band_out,inArray)
	os.chmod(outpath,mode)
	image_out_DS=None
def writeByteRaster(outpath,inArray,template_DS,Byte_NODATA=255,mode=0777):#writes a single band raster to the same extent and projection as the template DS	
	image_driver=template_DS.GetDriver()
	image_out_DS=image_driver.Create(outpath,template_DS.RasterXSize,template_DS.RasterYSize,template_DS.RasterCount,GDT_Byte)
	projection=template_DS.GetProjectionRef()
	geotransform=template_DS.GetGeoTransform()
	image_out_DS.SetProjection(projection)
	image_out_DS.SetGeoTransform(geotransform)
	image_band_out=image_out_DS.GetRasterBand(1)
	image_band_out.SetNoDataValue(Byte_NODATA)
	image_band_out=gdal_array.BandWriteArray(image_band_out,inArray)
	os.chmod(outpath,mode)
	image_out_DS=None
def writeFloatRaster(outpath,inArray,template_DS,FLOAT_NODATA=-9999,mode=0777):#writes a single band raster to the same extent and projection as the template DS
	image_driver=template_DS.GetDriver()
	image_out_DS=image_driver.Create(outpath,template_DS.RasterXSize,template_DS.RasterYSize,template_DS.RasterCount,GDT_Float32)
	projection=template_DS.GetProjectionRef()
	geotransform=template_DS.GetGeoTransform()
	image_out_DS.SetProjection(projection)
	image_out_DS.SetGeoTransform(geotransform)
	image_band_out=image_out_DS.GetRasterBand(1)
	image_band_out.SetNoDataValue(FLOAT_NODATA)
	image_band_out=gdal_array.BandWriteArray(image_band_out,inArray)
	os.chmod(outpath,mode)
	image_out_DS=None
def createScenerioList(slr_file):		#takes the SLR scenerio file and returns a list of processing variables for each time step
	slr_f=open(slr_file,'r')
	slr_lines=slr_f.readlines()
	#slr_list=list()
	slr_list=list()
	#create the rundate/slr list in format of <year>,<slr>,<write Elev>,<write Vegetation> 
	for item in slr_lines:
		slr_list.append((int(item.rstrip().split(',')[0].strip()),float(item.rstrip().split(',')[1].strip()),item.rstrip().split(',')[2].strip().lower()=='true',item.rstrip().split(',')[3].strip().lower()=='true'))
	T0=slr_list.pop(0)
	return slr_list,T0
######################################################   Model Functions      ##############################################
def changeMatrix(from_array,to_array,OUTPUT_MAP=False):	#computes the change between to numpy integer arrays. Must be the same size. Can output map optionally
	if from_array.shape==to_array.shape:
		fchar_arr=from_array.astype('S'+CHAR_LEN)
		tchar_arr=to_array.astype('S'+CHAR_LEN)
		char_result=np.core.defchararray.add(fchar_arr,tchar_arr)
		return char_result.astype('i')
	else:
		return None
def decisionTree(vardict,cat_list,VERBOSE=False,T0=False,PROTECT=False): # the T0 option moves vegetation up, forceing the intial veg data to conform with the model assumptions
	veg_cats=list()
	catlist=deepcopy(cat_list)
	if T0:										#create the veg cat switch list /current cat/max_elev/to_catagory/units	
		if PROTECT:
			if os.path.isfile(vardict['protectedfile']):
				pf = open(vardict['protectedfile'],'r')
				lines=pf.readlines()
				dev_list=list()
				for line in lines:
					dev_list.append(line.strip().lower())
				for dev in dev_list:
					try:
						catlist.pop(catlist.index(dev))
					except ValueError:
						pass
			for cat in catlist:
				if isTerminal(vardict[cat]):		#check to see if the catagory is allowed to move "up"
					pass 
				if int(vardict[cat]['cat']) == 17:
					pass
				else:
					veg_cats.append([int(vardict[cat]['cat']),float(vardict[cat]['maxelev']),int(vardict[cat]['fromcat']),vardict[cat]['maxunit']])
		else:
			for cat in catlist:
				if isTerminal(vardict[cat]):		#check to see if the catagory is allowed to move "up"
					pass 
				if int(vardict[cat]['cat']) == 17:
					pass
				else:
					veg_cats.append([int(vardict[cat]['cat']),float(vardict[cat]['maxelev']),int(vardict[cat]['fromcat']),vardict[cat]['maxunit']])
	else:
		if PROTECT:
			if os.path.isfile(vardict['protectedfile']):
				pf = open(vardict['protectedfile'],'r')
				lines=pf.readlines()
				dev_list=list()
				for line in lines:
					dev_list.append(line.strip().lower())
				for dev in dev_list:
					try:
						catlist.pop(catlist.index(dev))
					except ValueError:
						pass	
			for cat in catlist:
				if isTerminal(vardict[cat],False):	#check to see if the catagory is allowed to move "down"
					pass
				else:
					veg_cats.append([int(vardict[cat]['cat']),float(vardict[cat]['minelev']),int(vardict[cat]['changecat']),vardict[cat]['minunit']])
		else:
			for cat in catlist:
				if isTerminal(vardict[cat],False):	#check to see if the catagory is allowed to move "down"
					pass
				else:
					veg_cats.append([int(vardict[cat]['cat']),float(vardict[cat]['minelev']),int(vardict[cat]['changecat']),vardict[cat]['minunit']])
	if VERBOSE:
		count=0
		if T0:
			print "\n****************** T0 Decision Tree ***************************\n"
			for cat in catlist:
				if isTerminal(vardict[cat]):
					pass
				else:
					print cat,T0_dtree[count]
					count += 1
		else:
			print "\n************************* Decision Tree **********************\n"
			for cat in catlist:
				if isTerminal(vardict[cat],False):
					pass
				else:
					print cat,dtree[count]
					count += 1
	return veg_cats								#returns a list of tuples
def create_boundaries(variable_dict,cat_list, VERBOSE=False):
	boundary_list=list()
	for cat in cat_list:
		if isTerminal(variable_dict[cat]):
			bound=(float(variable_dict[cat]['minelev']),float(variable_dict[cat]['minboundarycoefficient']))
			if boundary_list.count(bound)==0:
				boundary_list.append(bound)
		if isTerminal(variable_dict[cat],False):
			bound=(float(variable_dict[cat]['maxelev']),float(variable_dict[cat]['maxboundarycoefficient']))
			if boundary_list.count(bound)==0:
				boundary_list.append(bound)
		if (not isTerminal(variable_dict[cat],False)) and (not isTerminal(variable_dict[cat])):
			bound=(float(variable_dict[cat]['maxelev']),float(variable_dict[cat]['maxboundarycoefficient']))
			if boundary_list.count(bound)==0:
				boundary_list.append(bound)
			bound=(float(variable_dict[cat]['minelev']),float(variable_dict[cat]['minboundarycoefficient']))
			if boundary_list.count(bound)==0:
				boundary_list.append(bound)
	boundary_values=dict()
	for boundary in boundary_list:
		new_value=random.choice(np.random.normal(boundary[0],boundary[1],(1000,)))
		key=str(boundary[0])+'&&'+str(boundary[1])
		boundary_values[key]=new_value
	if VERBOSE:
		for key in boundary_values.keys():
			print key,boundary_values[key]
	return boundary_values
def setBoundaries(variable_dict,cat_list,VERBOSE=False):
	new_vardict=deepcopy(variable_dict)		#create the new dictionary object to stor the new boundary values
	boundary_values=create_boundaries(variable_dict,cat_list)
	#boundary_values=create_boundaries(variable_dict,cat_list,True)
	for cat in cat_list:
		#print cat
		min_key=str(float(variable_dict[cat]['minelev']))+'&&'+str(float(variable_dict[cat]['minboundarycoefficient']))
		max_key=str(float(variable_dict[cat]['maxelev']))+'&&'+str(float(variable_dict[cat]['maxboundarycoefficient']))
		if isTerminal(variable_dict[cat],False):	#check to see if is downward terminal category
			#print cat
			new_vardict[cat]['min_boundary_set']=True
			if variable_dict[cat]['maxcomplex']=='true': 	#check to see if it a complex max boundary
				new_value=random.choice(np.random.normal(float(variable_dict[cat]['maxelev']),float(variable_dict[cat]['maxboundarycoefficient']),(1000,)))	#calculate the complex boundary value individually
				new_vardict[cat]['maxelev']=str(new_value)
				new_vardict[cat]['max_boundary_set']=True
			else:
				new_vardict[cat]['maxelev']=str(boundary_values[max_key])
				new_vardict[cat]['max_boundary_set']=True
		if isTerminal(variable_dict[cat]):			#check to see if is upward terminal category
			#print cat
			new_vardict[cat]['max_boundary_set']=True
			if variable_dict[cat]['mincomplex']=='true': 	#check to see if it a complex min boundary
				new_value=random.choice(np.random.normal(float(variable_dict[cat]['minelev']),float(variable_dict[cat]['minboundarycoefficient']),(1000,)))	#calculate the complex boundary value individually
				new_vardict[cat]['minelev']=str(new_value)
				new_vardict[cat]['min_boundary_set']=True
			else:
				new_vardict[cat]['minelev']=str(boundary_values[min_key])
				new_vardict[cat]['min_boundary_set']=True
		if (not isTerminal(variable_dict[cat])) and (not isTerminal(variable_dict[cat],False)):											#Must be a intermediat boundary class
			#print cat
			if variable_dict[cat]['maxcomplex']=='true': 	#check to see if it a complex max boundary
				new_value=random.choice(np.random.normal(float(variable_dict[cat]['maxelev']),float(variable_dict[cat]['maxboundarycoefficient']),(1000,)))	#calculate the complex boundary value individually
				new_vardict[cat]['maxelev']=str(new_value)
				new_vardict[cat]['max_boundary_set']=True
			else:
				new_vardict[cat]['maxelev']=str(boundary_values[max_key])
				new_vardict[cat]['max_boundary_set']=True
			if variable_dict[cat]['mincomplex']=='true': 	#check to see if it a complex min boundary
				new_value=random.choice(np.random.normal(float(variable_dict[cat]['minelev']),float(variable_dict[cat]['minboundarycoefficient']),(1000,)))	#calculate the complex boundary value individually
				new_vardict[cat]['minelev']=str(new_value)
				new_vardict[cat]['min_boundary_set']=True
			else:
				new_vardict[cat]['minelev']=str(boundary_values[min_key])
				new_vardict[cat]['min_boundary_set']=True	
	if VERBOSE:
		for cat in cat_list:
			print cat
			print '\t','min',str(float(variable_dict[cat]['minelev'])),'\t','min',str(float(new_vardict[cat]['minelev']))
			print '\t','max',str(float(variable_dict[cat]['maxelev'])),'\t','max',str(float(new_vardict[cat]['maxelev']))
	return new_vardict
def makeMask(elev_arr_base,veg_arr_base,variable_dict,cat_list,MASK_TERMINAL=True):
	MAX_ELEV=float(variable_dict['max_elev'])
	elev_mask=(elev_arr_base >= MAX_ELEV).astype('b')
	if MASK_TERMINAL:
		terminal_cat_mask=list()
		for cat in cat_list:
			if isTerminal(variable_dict[cat],False):
				terminal_cat_mask.append((veg_arr_base==int(variable_dict[cat]['cat'])).astype('b'))
		ignore_mask = (veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')
		temp_mask = elev_mask+ignore_mask
		for mask in terminal_cat_mask:
			temp_mask = temp_mask + mask
		return (temp_mask == 0).astype('b')
	else:
		ignore_mask = (veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')
		temp_mask = elev_mask+ignore_mask
		return (temp_mask == 0).astype('b')
def convertToHTU(arr,GT):
	htu_dem=arr/(GT/2.0)
	return htu_dem
def accreation(x):
	#####Log-Normal curve#####
	LogNorm_sigma = 0.55
	LogNorm_mu = 0.0
	LogNorm_shift = -1.2
	LogNorm_scale = 0.008
	#####Sigmoid 1 (lower)#####
	SigLo_scale = 0.0045
	SigLo_spread = 6.5
	SigLo_midpt = -0.5
	#####Sigmoid 2 (higher)#####
	SigHi_scale = -0.0035
	SigHi_spread = 20
	SigHi_midpt = 0.53
	LogNorm=np.exp(-0.5*np.power(((np.log(x-LogNorm_shift)-LogNorm_mu)/LogNorm_sigma),2))*LogNorm_scale
	SigLo=SigLo_scale*(1/(1+np.exp(SigLo_spread*(x-SigLo_midpt)))-1)
	SigHi=SigHi_scale*(1/(1+np.exp(SigHi_spread*(x-SigHi_midpt)))-1)
	return (LogNorm+SigLo+SigHi+0.001)
def marsh_acc(htu,veg):		#return values in meters for marsh cells only
	condlist=[veg==6,veg==8,veg==11,veg==20]
	choicelist=[veg*0+1,veg*0+1,veg*0+1,veg*0+1]
	veg_mask=np.select(condlist, choicelist)
	LogNorm_shift = -1.2
	acc=np.piecewise(htu,[htu <= LogNorm_shift, htu>LogNorm_shift],[0.001,accreation])
	return veg_mask*acc
def swamp_acc(veg):		#return values in meters for marsh cells only
	swamp_arr=np.zeros(veg.shape)
	condlist=[veg==3,veg==23]
	choicelist=[swamp_arr+.003,swamp_arr+.0011]
	swamp_elev=np.select(condlist, choicelist)
	return swamp_elev
def isTerminal(adict,upward=True):	#given a veg cat dictionary object determines if the cat is a terminal catagory in either direction
	if upward:
		if adict['cat'] == adict['fromcat']:
			return True
		else:
			return False
	else:
		if adict['cat'] == adict['changecat']:
			return True
		else:
			return False
def percentile(N, percent, key=lambda x:x):
    # Find the percentile of a list of values.
    # @parameter N - is a list of values. Note N MUST BE already sorted.
    # @parameter percent - a float value from 0.0 to 1.0.
    # @parameter key - optional key function to compute value from each element of N.
    # @return - the percentile of the values
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1
def GetRasterCoord(xy_tuple,in_raster_ds):		#returns in xy format, WILL NOT return a xy index that is out of bounds, rather truncates the raster location to the existing bounds
	gt=in_raster_ds.GetGeoTransform()
	xpix=int(round((xy_tuple[0]-gt[0])/abs(gt[1])))
	ypix=int(round((gt[3]-xy_tuple[1])/abs(gt[5])))
	#lets do the back check
	xpix-=1
	ypix-=1
	X=gt[0]+(xpix*gt[1])
	x_range=(X,X+gt[1])
	while not ((xy_tuple[0] >= x_range[0])&(xy_tuple[0] < x_range[1])):
		xpix +=1
		X=gt[0]+(xpix*gt[1])
		x_range=(X,X+gt[1])
		
	Y=gt[3]+(ypix*gt[5])
	y_range=(Y,Y+gt[5])
	while not ((xy_tuple[1] <= y_range[0])&(xy_tuple[1] > y_range[1])):
		ypix+=1
		Y=gt[3]+(ypix*gt[5])
		y_range=(Y,Y+gt[5])
	if xpix <= 0:
			xpix = 0
	if ypix <= 0:
			ypix = 0
	if xpix >= in_raster_ds.RasterXSize:
			xpix = in_raster_ds.RasterXSize-1
	if ypix >= in_raster_ds.RasterYSize:
			ypix = in_raster_ds.RasterYSize	-1
	return (xpix,ypix)
def GetProjCoord(xy_tuple,in_raster_ds):	#returns in xy format
	gt=in_raster_ds.GetGeoTransform()
	x=(xy_tuple[0]*gt[1])+gt[0]+(gt[1]/2)
	y=(gt[3]+(xy_tuple[1]*gt[5]))-(gt[1]/2)
	return (x,y)
def logBoundary(adict,catlist,var_dict):
	for cat in catlist:
		for var in BOUNDARY_VARLIST:
			adict[cat][var].append(var_dict[cat][var])
def getFileList(dirpath,TYPE=None,COUNT=None,SEP='_'):
	if TYPE==None:
		TYPE='.tif'
	if COUNT==None:
		COUNT=0
	outmap_list=list()
	map_list=os.listdir(dirpath)
	for map in map_list:
		if map.count(SEP) == COUNT:
			if (os.path.splitext(map)[1]==TYPE):
				outmap_list.append(os.path.join(dirpath,map))
	return outmap_list