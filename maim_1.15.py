# -*- coding: utf-8 -*-
#Steven Guinn
#8/05/2015
#University of Maryland Center for Environmental Science
#Appalachian Laboratory            http://www.al.umces.edu/ 
#301 689 7146
#301 Braddock Rd    Frostburg MD 215325
################################## Info Header ########################################################################

#######################################################################################################################
import sys
import time
import gc
from utility_0_9_2 import *
stime = time.clock()
sim_path = sys.argv[1]
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
cleanMakeDir(out_dir)
map_dir=os.path.join(out_dir,'maps')
cleanMakeDir(map_dir)
results_dir=os.path.join(out_dir,'results')
cleanMakeDir(results_dir)
################################################################ Create SLR Scenerio parameter list and directories ###
slr_list,T0=createScenerioList(slr_file)
T0Yr=T0[0]
#GSL_Last=T0[1]
if T0[2] or T0[3]:
	T0_dir=os.path.join(map_dir,str(T0Yr))
	cleanMakeDir(T0_dir)
for slr in slr_list:
	if slr[2] or slr[3]:
		adir=os.path.join(map_dir,str(slr[0]))
		cleanMakeDir(adir)
################################################################ open datasets and convert to arrays ##################
veg_ds=gdal.Open(variable_dict['catagoryfile'])
elev_ds=gdal.Open(variable_dict['elevfile'])
veg_arr_base=gdal_array.DatasetReadAsArray(veg_ds)
elev_arr_base=gdal_array.DatasetReadAsArray(elev_ds)
blank_value_arr=(veg_arr_base == int(variable_dict['ignore_catagory'])).astype('b')*int(variable_dict['ignore_catagory'])
water_value_arr=(veg_arr_base == int(variable_dict['estuarine open water']['cat'])).astype('b')*int(variable_dict['estuarine open water']['cat'])
######################################################   Processing loop    ###########################################
if isMonte == 'true':	##############################   Monte Carlo Simulation Processing loop    ####################
################################################################# set up boundary logging for sensitivity analysis ####
	bname_dict={}
	for cat in cat_list:
		bname_dict[cat]=dict()
	for key in bname_dict.keys():
		for var in BOUNDARY_VARLIST:
			bname_dict[key][var]=list()
	run_num=0
	while run_num < monte_runs:
		GSL_Last=T0[1]
		print "Run Number: ",run_num
		variable_dict = setBoundaries(var_dict_bak,cat_list)	#change boundary values in the dictionary object ##
		logBoundary(bname_dict,cat_list,variable_dict)				#log the boundaries
		veg_arr = np.array(veg_arr_base)							#make a DEEP copy of the base veg array ###########
######################################################   T0 modification and summary   ################################
		if T0_mod:
############################################ Preprocess the elevation data to match MTL dataum and T0 time step #######
			elev_arr=(elev_arr_base-float(variable_dict['navd88mtl_correction']))-((T0Yr-DEMYr)*SiteHistSLR)
			htu_arr=convertToHTU(elev_arr,GT)
			T0_dtree=decisionTree(variable_dict,cat_list,False,True,True)	#upper boundary ###################################
			next_veg=np.array(veg_arr)								#make a DEEP copy of the input veg
			for cat in T0_dtree:
				if cat[3] =='meters':		#check if the units are meters
					condlist=[veg_arr==cat[0]]
					choicelist=[elev_arr > cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #############
				else:						#else must be halftide
					condlist=[veg_arr==cat[0]]
					choicelist=[htu_arr > cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #############
			d_tree=decisionTree(variable_dict,cat_list,False,False,True)				#lower boundary #######################
			for cat in d_tree:
				if cat[3] =='meters':											#check if the units are meters
					condlist=[veg_arr==cat[0]]
					choicelist=[elev_arr < cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #############
				else:											#else must be halftide
					condlist=[veg_arr==cat[0]]
					choicelist=[htu_arr < cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #############
				veg_arr=np.array(next_veg)										#this is the T0 veg array
				if T0[3]:
					veg_cat_out_path=os.path.join(os.path.join(map_dir,str(T0Yr)),(str(T0Yr)+'_'+str(run_num)+'_VEG_CAT.tif'))
					writeByteRaster(veg_cat_out_path,(veg_arr),veg_ds)
				if T0[2]:
					elev_out_path=os.path.join(os.path.join(map_dir,str(T0Yr)),(str(T0Yr)+'_'+str(run_num)+'_ELEV.tif'))
					writeFloatRaster(elev_out_path,(elev_arr+float(variable_dict['navd88mtl_correction'])),elev_ds)
################################################################ No T0 ###################################
		else:
			elev_arr=(elev_arr_base-float(variable_dict['navd88mtl_correction']))
			d_tree=decisionTree(variable_dict,cat_list,False,False,True)
################################################################ create intial mask ###################################
		mask_arr=makeMask(elev_arr_base,veg_arr,variable_dict,cat_list,False)	
############################################################   Processing loop    #####################################
		d_tree=decisionTree(variable_dict,cat_list,False,False,False)
		for slr in slr_list:
			GSL_Cur=slr[1]
			rundate=slr[0]
			RunDate=str(rundate)
			print RunDate
			#calculate SLR for this time step
			elev_arr=elev_arr-((GSL_Cur-GSL_Last)+(SiteSubRate*TimeStep))
			#convert dem meters to HTU
			htu_arr=convertToHTU(elev_arr,GT)
			#calculate accreation for marshlands and swamps
			elev_arr=elev_arr+(marsh_acc(htu_arr,veg_arr)*TimeStep)+(swamp_acc(veg_arr)*TimeStep)
			#recalculate HTU
			htu_arr=convertToHTU(elev_arr,GT)
			#switch veg_cats
			next_veg=np.array(veg_arr)		# create the temp veg array to be:make a DEEP copy
			for cat in d_tree:
				if cat[3] =='meters':			#check if the units are meters
					condlist=[veg_arr==cat[0]]
					choicelist=[elev_arr < cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])
				if cat[3]=='halftide':			#else must be halftide
					condlist=[veg_arr==cat[0]]
					choicelist=[htu_arr < cat[1]]
					np.putmask(next_veg,np.select(condlist,choicelist),cat[2])
			veg_arr=np.array(next_veg)			#this is the T<time step> veg array:make a DEEP copy
			if slr[3]:
					veg_cat_out_path=os.path.join(os.path.join(map_dir,RunDate),(RunDate+'_'+str(run_num)+'_VEG_CAT.tif'))	#write out the T<time step> veg array
					writeByteRaster(veg_cat_out_path,(veg_arr),veg_ds)
			if slr[2]:
				elev_out_path=os.path.join(os.path.join(map_dir,RunDate),(RunDate+'_'+str(run_num)+'_ELEV.tif'))
				writeFloatRaster(elev_out_path,(elev_arr+float(variable_dict['navd88mtl_correction'])),elev_ds)
			GSL_Last=GSL_Cur
		elev_arr=None
		veg_arr=None
		htu_arr=None
		gc.collect()
		run_num += 1

#######################################################################################################################
##########################################  No Monte Simulation!  #####################################################
#######################################################################################################################
		
else:
	GSL_Last=T0[1]
	veg_arr = np.array(veg_arr_base)								#make a DEEP copy of the base veg array ###########
######################################################   T0 modification and summary   ################################
	if T0_mod:
############################################ Preprocess the elevation data to match MTL dataum and T0 time step #######
		elev_arr=(elev_arr_base-float(variable_dict['navd88mtl_correction']))-((T0Yr-DEMYr)*SiteHistSLR)
		htu_arr=convertToHTU(elev_arr,GT)
		T0_dtree=decisionTree(variable_dict,cat_list,T0=True)	#upper boundary #######################################
		next_veg=np.array(veg_arr)								#make a DEEP copy of the input veg
		for cat in T0_dtree:
			if cat[3] =='meters':		#check if the units are meters
				condlist=[veg_arr==cat[0]]
				choicelist=[elev_arr > cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #################
			else:						#else must be halftide
				condlist=[veg_arr==cat[0]]
				choicelist=[htu_arr > cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #################
		d_tree=decisionTree(variable_dict,cat_list,T0=False)					#lower boundary ###########################
		for cat in d_tree:
			if cat[3] =='meters':											#check if the units are meters
				condlist=[veg_arr==cat[0]]
				choicelist=[elev_arr < cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #################
			else:
				cat[3]=='halftide'											#else must be halftide
				condlist=[veg_arr==cat[0]]
				choicelist=[htu_arr < cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])	#adjust the new veg array #################
			veg_arr=np.array(next_veg)										#this is the T0 veg array			
			if T0[3]:
				veg_cat_out_path=os.path.join(os.path.join(map_dir,str(T0Yr)),(str(T0Yr)+'_VEG_CAT.tif'))
				writeByteRaster(veg_cat_out_path,(veg_arr),veg_ds)
			if T0[2]:
				elev_out_path=os.path.join(os.path.join(map_dir,str(T0Yr)),(str(T0Yr)+'_ELEV.tif'))
				writeFloatRaster(elev_out_path,elev_arr,elev_ds)
################################################################ No T0 ###################################
	else:
		elev_arr=(elev_arr_base-float(variable_dict['navd88mtl_correction']))
		d_tree=decisionTree(variable_dict,cat_list,T0=False)
################################################################ create intial mask ###################################
	mask_arr=makeMask(elev_arr_base,veg_arr,variable_dict,cat_list)		
############################################################   Processing loop    #####################################
	for slr in slr_list:
		GSL_Cur=slr[1]
		rundate=slr[0]
		RunDate=str(rundate)
		print RunDate
		#calculate SLR for this time step
		elev_arr=elev_arr-((GSL_Cur-GSL_Last)+(SiteSubRate*TimeStep))
		#convert dem meters to HTU
		htu_arr=convertToHTU(elev_arr,GT)
		#calculate accreation for marshlands and swamps
		elev_arr=elev_arr+(marsh_acc(htu_arr,veg_arr)*TimeStep)+(swamp_acc(veg_arr)*TimeStep)
		#recalculate HTU
		htu_arr=convertToHTU(elev_arr,GT)
		#switch veg_cats
		next_veg=np.array(veg_arr)		# create the temp veg array to be:make a DEEP copy
		for cat in d_tree:
			if cat[3] =='meters':			#check if the units are meters
				condlist=[veg_arr==cat[0]]
				choicelist=[elev_arr < cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])
			if cat[3]=='halftide':			#else must be halftide
				condlist=[veg_arr==cat[0]]
				choicelist=[htu_arr < cat[1]]
				np.putmask(next_veg,np.select(condlist,choicelist),cat[2])
		veg_arr=np.array(next_veg)			#this is the T<time step> veg array:make a DEEP copy
		if slr[3]:
				veg_cat_out_path=os.path.join(os.path.join(map_dir,RunDate),(RunDate+'_VEG_CAT.tif'))	#write out the T<time step> veg array
				writeByteRaster(veg_cat_out_path,(veg_arr),veg_ds)
		if slr[2]:
			if ELEV_out == 'true':
				elev_out_path=os.path.join(os.path.join(map_dir,RunDate),(RunDate+'_ELEV.tif'))
				writeFloatRaster(elev_out_path,elev_arr,elev_ds)
			if HTU_out == 'true':	################### Convert to HTU ####################################################
				HTU_elev_path=os.path.join(os.path.join(map_dir,RunDate),(RunDate+'_HTU.tif'))
				writeFloatRaster(HTU_elev_path,convertToHTU(elev_arr,GT),elev_ds)
		GSL_Last=GSL_Cur
	elev_arr=None
	veg_arr=None
	htu_arr=None
	gc.collect()
etime = time.clock()
print 'total processing time ',etime-stime, ' seconds'
	

