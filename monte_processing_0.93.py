# -*- coding: utf-8 -*-
#Steven Guinn
#8/04/2014
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146
#301 Braddock Rd    Frostburg MD 215325
################################## Info Header ########################################################################

#######################################################################################################################
import sys
import time
import gc
from utility_0_9_1 import *
stime = time.clock()
sim_path = sys.argv[1]
VEG_OUT = True
#########################################################  read in the sim file    ####################################
sf = open(sim_path,'r')
validate_paramfile(sf,True)
variable_dict,parameter_list,cat_list = read_paramfile(sf)
var_dict_bak=deepcopy(variable_dict)
################################################################ retrieve core parameters #############################
MAX_ELEV = float(variable_dict['max_elev'])
TimeStep = float(variable_dict['time_step'])
SiteHistSLR = float(variable_dict['sitehistslr'])
GlobalHistSLR = float(variable_dict['globalhistslr'])
SiteSubRate = SiteHistSLR-GlobalHistSLR
DEMYr = int(variable_dict['dem_date'])
GT = float(variable_dict['gtiderange'])
T0_mod = variable_dict['t0_mod']=='true'
slr_file = variable_dict['slr_sceneriofile']
prefix = variable_dict['prefix']
isMonte=variable_dict['montecarloprocessing']
monte_runs=int(variable_dict['monterunnumber'])
ELEV_out=variable_dict['elevationoutput']
HTU_out=variable_dict['htu_output']
####################################################### initial directory set up ######################################
out_dir=variable_dict['outputws']
map_dir=os.path.join(out_dir,'maps')
results_dir=os.path.join(out_dir,'results')
result_path=os.path.join(results_dir,prefix+'_veg_summary_monte.csv')
################################################################ open datasets and convert to arrays ##################
veg_ds=gdal.Open(variable_dict['catagoryfile'])
elev_ds=gdal.Open(variable_dict['elevfile'])
veg_arr_base=gdal_array.DatasetReadAsArray(veg_ds)
elev_arr_base=gdal_array.DatasetReadAsArray(elev_ds)
blank_value_arr=(veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')*int(variable_dict['ignore_catagory'])
################################################################ create intial mask ###################################
mask_arr=makeMask(elev_arr_base,veg_arr_base,variable_dict,cat_list,False)	
###########################################    Monte Processing     ###################################################
print "Monte Processing"
BINS=list()
for cat in cat_list:
	BINS.append(int(variable_dict[cat]['cat']))
BINS.append(24)
BINS.sort()
wd=map_dir														#change to the output dir of the current MAIM run #
os.chdir(wd)
dir_list=os.listdir(wd)
########################################## Set up the mask index ######################################################
ma_mask=np.ma.array(mask_arr)
index=ma_mask.nonzero()
index_list=list()
row_list=index[0]
col_list=index[1]
i=0
while i < len(row_list):		#reformat the index list into yx raster coords
	index_list.append((row_list[i],col_list[i]))
	i+=1
for item in dir_list:			#rundate loop
	print "processing ",item
	path=os.path.join(wd,item)
	vegmap_list=getFileList(path,TYPE='.tif',COUNT=3)
	elevmap_list=getFileList(path,TYPE='.tif',COUNT=2)
################################################  calculate the majority class  #######################################
	if VEG_OUT:
		veg_array_list=list()
		for gis in vegmap_list:
			veg_ds=gdal.Open(gis)
			veg_array_list.append(gdal_array.DatasetReadAsArray(veg_ds))
		veg_stack=np.dstack(veg_array_list)			
		out_veg = np.ones((veg_stack.shape[0],veg_stack.shape[1]))*int(variable_dict['ignore_catagory'])
		out_prob = np.zeros((veg_stack.shape[0],veg_stack.shape[1]))
		for loc in index_list:
			slc=veg_stack[loc[0],loc[1],:]
			h=np.histogram(slc,BINS)
			b=list()
			count=0
			while count < len(h[0]):
				b.append((h[0][count],h[1][count]))
				count +=1
			b.sort(reverse=True)
			out_prob[loc[0],loc[1]]=float(b[0][0])/float(len(slc))
			out_veg[loc[0],loc[1]]=b[0][1]				
		veg_path=os.path.join(results_dir,(prefix+'_'+item+'_veg.tif'))
		veg_prob_path=os.path.join(results_dir,(prefix+'_'+item+'_probability.tif'))
		writeByteRaster(veg_path,(out_veg),veg_ds)	
		writeFloatRaster(veg_prob_path,out_prob,veg_ds)
		out_veg=None
		out_prob=None
		veg_stack=None
		gc.collect()
	if (ELEV_out == 'true') or (HTU_out== 'true'):
		elev_array_list=list()
		for elevmap in elevmap_list:
			elevation_ds=gdal.Open(elevmap)
			elev_arr=gdal_array.DatasetReadAsArray(elevation_ds)
			elev_array_list.append(elev_arr)
		elev_stack=np.dstack(elev_array_list)
		out_elev = np.mean(elev_stack,axis=2)
		if ELEV_out == 'true':
			elev_path=os.path.join(results_dir,(prefix+'_'+item+'_elev.tif'))
			writeFloatRaster(elev_path,out_elev,elev_ds)
		if HTU_out == 'true':	################### Convert to HTU ################################################
			elev_path=os.path.join(results_dir,(prefix+'_'+item+'_HTU.tif'))
			writeFloatRaster(elev_path,convertToHTU(out_elev,GT),elev_ds)
	elevation_ds=None
	elev_stack=None
	out_elev=None
########################################################  summary processing ############################################
#######################################################     header setup ##############################################
if VEG_OUT:
	summary_list=list()
	s='Year,Area,'
	for cat in cat_list:
		summary_list.append((variable_dict[cat]['abbreviation'],int(variable_dict[cat]['cat'])))
		for suffix in SUFFIX_LIST:
			s=s+variable_dict[cat]['abbreviation']+suffix+','
	s=s[:-1]
	s=s+'\n'
	f=open(result_path,'w')
	f.write(s)
	dir_list=os.listdir(map_dir)
	dir_list.sort()
	for rundate in dir_list:			#rundate loop
		print rundate
		summary_dict=dict()
		for item in summary_list:
			summary_dict[item[0]]=list()
		path=os.path.join(map_dir,rundate)
		vegmap_list=getFileList(path,TYPE='.tif',COUNT=3)
		for vegmap in vegmap_list:
			veg_ds=gdal.Open(vegmap)
			veg_arr=gdal_array.DatasetReadAsArray(veg_ds)
			veg_arr=veg_arr*mask_arr
			for sum in summary_list:
				cat_name=sum[0]
				cat_num=sum[1]
				veg_mask=veg_arr==cat_num
				summary_dict[cat_name].append(veg_mask.sum())
			veg_ds=None
			veg_arr=None
		area=str(mask_arr.sum())
		s=rundate+','+area+','
		for cat in summary_list:
			summary_dict[cat[0]].sort()
			s=s+str(np.asarray(summary_dict[cat[0]]).min())+','
			s=s+str(np.asarray(summary_dict[cat[0]]).max())+','
			s=s+str(np.asarray(summary_dict[cat[0]]).mean())+','
			s=s+str(percentile(summary_dict[cat[0]],0.25))+','
			s=s+str(percentile(summary_dict[cat[0]],0.5))+','
			s=s+str(percentile(summary_dict[cat[0]],0.75))+','
		s=s[:-1]
		s=s+'\n'
		f.write(s)
	f.close()
etime = time.clock()
print 'total processing time ',etime-stime, ' seconds'
	

