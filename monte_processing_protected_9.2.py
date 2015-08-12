# -*- coding: utf-8 -*-
#Steven Guinn
#8/08/2014
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146

#######################################################################################################################
import time
import gc
from utility_0_9_1 import *
stime = time.clock()
sim_path = sys.argv[1]
#########################################################  read in the sim file    ####################################
sf = open(sim_path,'r')
if validate_paramfile(sf):
	variable_dict,parameter_list,cat_list = read_paramfile(sf)
else:
	print "Invalid Parameter File"
	sys.exit()
out_dir=variable_dict['outputws']
results_dir=os.path.join(out_dir,'results')
map_dir=os.path.join(out_dir,'maps')
prefix = variable_dict['prefix']
prefix=prefix+'_protected'
result_path=os.path.join(results_dir,prefix+'_veg_summary_monte.csv')
############################################################### open datasets and convert to arrays ##################
veg_ds=gdal.Open(variable_dict['catagoryfile'])
elev_ds=gdal.Open(variable_dict['elevfile'])
veg_arr_base=gdal_array.DatasetReadAsArray(veg_ds)
elev_arr_base=gdal_array.DatasetReadAsArray(elev_ds)
blank_value_arr=(veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')*int(variable_dict['ignore_catagory'])	#remove this
################################################################# make mask ###########################################
MAX_ELEV=float(variable_dict['max_elev'])
elev_mask=(elev_arr_base >= MAX_ELEV).astype('b')
ignore_mask = (veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')
temp_mask = elev_mask+ignore_mask
mask = (temp_mask == 0).astype('b')
elev_mask = None
ignore_mask = None
temp_mask = None
dev_mask_base = np.array(mask)*0
#######################################################     header setup ##############################################
summary_list=list()
s='Year,Area,'
#######################################################   read in the protected file ##################################
pf = open(variable_dict['protectedfile'],'r')
lines=pf.readlines()
dev_list=list()
for line in lines:
	dev_list.append(line.strip().lower())
dev_dict=dict()
for dev in dev_list:
	try:
		cat_list.pop(cat_list.index(dev))
		_mask = (veg_arr_base == int(variable_dict[dev]['cat'])).astype('b')
		dev_dict[dev]=(_mask * mask).sum()
		s=s+variable_dict[dev]['abbreviation']+','
		dev_mask_base=_mask+dev_mask_base
	except ValueError:
		pass

dev_mask = (dev_mask_base == 0).astype('b')
temp_mask = None
########################################################  summary processing ############################################
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
		veg_arr=veg_arr*mask*dev_mask
		for sum in summary_list:
			cat_name=sum[0]
			cat_num=sum[1]
			veg_mask=veg_arr==cat_num
			summary_dict[cat_name].append(veg_mask.sum())
		veg_ds=None
		veg_arr=None
	area=str(mask.sum())
	s=rundate+','+area+','
	for dev in dev_list:
		try:
			s=s+str(dev_dict[dev])+','
		except KeyError:
			pass
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
dev_mask = (dev_mask_base != 0).astype('b')
undev_mask = (dev_mask_base == 0).astype('b')
veg_list=list()
dir_list=os.listdir(results_dir)
for map in dir_list:
	if os.path.splitext(map)[0][(os.path.splitext(map)[0].rfind('_')):]=='_veg':
		veg_list.append(os.path.join(results_dir,map))
veg_list.sort()
format = "GTiff"
driver = gdal.GetDriverByName(format)
#base_veg_path=veg_list.pop(0)
#out_path=os.path.join(results_dir,'protected_'+os.path.basename(base_veg_path))
#shutil.copy(base_veg_path,out_path)
base_veg_path=variable_dict['catagoryfile']
base_veg_ds=gdal.Open(base_veg_path)
base_veg_array=gdal_array.DatasetReadAsArray(base_veg_ds)
base_veg_ds=None
for veg in veg_list:
	out_path=os.path.join(results_dir,'protected_'+os.path.basename(veg))
	print out_path
	old_veg_ds=gdal.Open(veg)
	old_veg_array=gdal_array.DatasetReadAsArray(old_veg_ds)
	new_veg_array=(base_veg_array*dev_mask)+(old_veg_array*undev_mask)
	writeByteRaster(out_path,(new_veg_array),old_veg_ds)
if variable_dict['deletemaps'] == 'true': 
	cleanMakeDir(map_dir)
	os.rmdir(map_dir)
etime=time.clock()
print 'total processing time ',etime-stime, ' seconds'











