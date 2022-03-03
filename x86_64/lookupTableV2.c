/* Created by Language version: 7.7.0 */
/* NOT VECTORIZED */
#define NRN_VECTORIZED 0
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "scoplib_ansi.h"
#undef PI
#define nil 0
#include "md1redef.h"
#include "section.h"
#include "nrniv_mf.h"
#include "md2redef.h"
 
#if METHOD3
extern int _method3;
#endif

#if !NRNGPU
#undef exp
#define exp hoc_Exp
extern double hoc_Exp(double);
#endif
 
#define nrn_init _nrn_init__lookupTableV2
#define _nrn_initial _nrn_initial__lookupTableV2
#define nrn_cur _nrn_cur__lookupTableV2
#define _nrn_current _nrn_current__lookupTableV2
#define nrn_jacob _nrn_jacob__lookupTableV2
#define nrn_state _nrn_state__lookupTableV2
#define _net_receive _net_receive__lookupTableV2 
 
#define _threadargscomma_ /**/
#define _threadargsprotocomma_ /**/
#define _threadargs_ /**/
#define _threadargsproto_ /**/
 	/*SUPPRESS 761*/
	/*SUPPRESS 762*/
	/*SUPPRESS 763*/
	/*SUPPRESS 765*/
	 extern double *getarg();
 static double *_p; static Datum *_ppvar;
 
#define t nrn_threads->_t
#define dt nrn_threads->_dt
#define _nd_area  *_ppvar[0]._pval
#define ptr	*_ppvar[2]._pval
#define _p_ptr	_ppvar[2]._pval
 
#if MAC
#if !defined(v)
#define v _mlhv
#endif
#if !defined(h)
#define h _mlhh
#endif
#endif
 
#if defined(__cplusplus)
extern "C" {
#endif
 static int hoc_nrnpointerindex =  2;
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_getValueForSection();
 static double _hoc_getValueForGid();
 static double _hoc_vInfo();
 static int _mechtype;
extern void _nrn_cacheloop_reg(int, int);
extern void hoc_register_prop_size(int, int, int);
extern void hoc_register_limits(int, HocParmLimits*);
extern void hoc_register_units(int, HocParmUnits*);
extern void nrn_promote(Prop*, int, int);
extern Memb_func* memb_func;
 
#define NMODL_TEXT 1
#if NMODL_TEXT
static const char* nmodl_file_text;
static const char* nmodl_filename;
extern void hoc_reg_nmodl_text(int, const char*);
extern void hoc_reg_nmodl_filename(int, const char*);
#endif

 extern Prop* nrn_point_prop_;
 static int _pointtype;
 static void* _hoc_create_pnt(_ho) Object* _ho; { void* create_point_process();
 return create_point_process(_pointtype, _ho);
}
 static void _hoc_destroy_pnt();
 static double _hoc_loc_pnt(_vptr) void* _vptr; {double loc_point_process();
 return loc_point_process(_pointtype, _vptr);
}
 static double _hoc_has_loc(_vptr) void* _vptr; {double has_loc_point();
 return has_loc_point(_vptr);
}
 static double _hoc_get_loc_pnt(_vptr)void* _vptr; {
 double get_loc_point_process(); return (get_loc_point_process(_vptr));
}
 extern void _nrn_setdata_reg(int, void(*)(Prop*));
 static void _setdata(Prop* _prop) {
 _p = _prop->param; _ppvar = _prop->dparam;
 }
 static void _hoc_setdata(void* _vptr) { Prop* _prop;
 _prop = ((Point_process*)_vptr)->_prop;
   _setdata(_prop);
 }
 /* connect user functions to hoc names */
 static VoidFunc hoc_intfunc[] = {
 0,0
};
 static Member_func _member_func[] = {
 "loc", _hoc_loc_pnt,
 "has_loc", _hoc_has_loc,
 "get_loc", _hoc_get_loc_pnt,
 "getValueForSection", _hoc_getValueForSection,
 "getValueForGid", _hoc_getValueForGid,
 "vInfo", _hoc_vInfo,
 0, 0
};
#define getValueForSection getValueForSection_lookupTableV2
#define getValueForGid getValueForGid_lookupTableV2
#define vInfo vInfo_lookupTableV2
 extern double getValueForSection( );
 extern double getValueForGid( );
 extern double vInfo( );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 0,0
};
 static double v = 0;
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 0,0
};
 static DoubVec hoc_vdoub[] = {
 0,0,0
};
 static double _sav_indep;
 static void nrn_alloc(Prop*);
static void  nrn_init(_NrnThread*, _Memb_list*, int);
static void nrn_state(_NrnThread*, _Memb_list*, int);
 static void _hoc_destroy_pnt(_vptr) void* _vptr; {
   destroy_point_process(_vptr);
}
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"lookupTableV2",
 0,
 0,
 0,
 "ptr",
 0};
 
extern Prop* need_memb(Symbol*);

static void nrn_alloc(Prop* _prop) {
	Prop *prop_ion;
	double *_p; Datum *_ppvar;
  if (nrn_point_prop_) {
	_prop->_alloc_seq = nrn_point_prop_->_alloc_seq;
	_p = nrn_point_prop_->param;
	_ppvar = nrn_point_prop_->dparam;
 }else{
 	_p = nrn_prop_data_alloc(_mechtype, 0, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 0;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _lookupTableV2_reg() {
	int _vectorized = 0;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 0,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 0, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "pointer");
 add_nrn_artcell(_mechtype, 0);
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 lookupTableV2 /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/lookupTableV2.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
 
/*VERBATIM*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

typedef struct{
	float **axon;
	float **apicals;
	float **basals;
	int *axonsSz;
	int *apicalsSz;
	int *basalsSz;
	float soma;
	unsigned int axonSz;
	unsigned int apicalSz;
	unsigned int basalSz;
} sectionEntry;

typedef struct{
	int **gids;
	sectionEntry **secData;
	float **factors;
	int numToRead;
	int *tableSizes;
	char vInfo;
	float *xPos;
	float *yPos;
	float *zPos;
}tableStruct;

float swapForFloat(int iAmAFloat){
	float factor;
	unsigned char *inPoint = (unsigned char *) &iAmAFloat;
	unsigned char *outPoint = (unsigned char *) &factor;
	iAmAFloat = (int)htonl(iAmAFloat);
	int k;
	for(k = 0; k < 4; ++k)
		outPoint[k]=inPoint[k];
	return factor;
};

void readAndSwapInt(int *readInto, int number, FILE *file){
	int i = 0;
	fread(readInto,sizeof(int),number,file);
	for(i = 0; i < number; ++i){
		readInto[i] = (int)htonl(readInto[i]);
	}        	
};
void readAndSwapFloat(float *readInto, int number, FILE *file){
	int i = 0;
	int tempReadArray[number];
	fread(&tempReadArray,sizeof(int),number,file);
	for(i = 0; i < number; ++i){
		readInto[i] = swapForFloat(tempReadArray[i]);
	}        	
};

 
double vInfo (  ) {
   double _lvInfo;
 
/*VERBATIM*/
	tableStruct **tempData = (tableStruct**)(&_p_ptr);
	tableStruct *tbl = (tableStruct*) *tempData;
	return tbl->vInfo;
 
return _lvInfo;
 }
 
static double _hoc_vInfo(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  vInfo (  );
 return(_r);
}
 
double getValueForGid (  ) {
   double _lgetValueForGid;
 
/*VERBATIM*/
	tableStruct **tempData = (tableStruct**)(&_p_ptr);
	tableStruct *tbl = (tableStruct*) *tempData;
	if((tbl->numToRead)==0)
		return 1;
	float retVal = 0;
	int i,j;
	if(ifarg(1)){
		int targetGid = (int) *getarg(1);
		for(i = 0; i < (tbl->numToRead); ++i){
			for (j = 0; j < (tbl->tableSizes)[i]; ++j){
				if((tbl->gids)[i][j]==targetGid){
					retVal+=(tbl->factors)[i][j];
					break; //Break inner loop. (In the latest specification a gid can only be mentioned once per table.)
				}
			}
		}
	}
	return retVal;   
 
return _lgetValueForGid;
 }
 
static double _hoc_getValueForGid(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getValueForGid (  );
 return(_r);
}
 
double getValueForSection (  ) {
   double _lgetValueForSection;
 
/*VERBATIM*/
	tableStruct **tempData = (tableStruct**)(&_p_ptr);
	tableStruct *tbl = (tableStruct*) *tempData;
	if((tbl->numToRead)==0)
		return 1;
	float retVal = 0;
	int i,j;
	if(ifarg(4)){
		int targetGid = (int) *getarg(1);
		int targetType = (int) *getarg(2);
		int targetSec = (int) *getarg(3);
		int usedCompIndex;
		float compDist = (float) *getarg(4);
		for(i = 0; i < (tbl->numToRead); ++i){	//TODO: Argh, use a map or something!
			for (j = 0; j < (tbl->tableSizes)[i]; ++j){
				if((tbl->gids)[i][j]==targetGid){ //or directly sort it by gid
					sectionEntry tEntry = (tbl->secData)[i][j];
					if(targetType == 3)		
						if(targetSec<tEntry.basalSz){
							usedCompIndex = (int)(tEntry.basalsSz[targetSec]*compDist);
							retVal+=tEntry.basals[targetSec][usedCompIndex];	
						} else
							printf("Target Section out of bounds: %i, %i, %i",targetGid,targetType,targetSec);
					else if(targetType == 4)
						if(targetSec<tEntry.apicalSz){
							usedCompIndex = (int)(tEntry.apicalsSz[targetSec]*compDist);
							retVal+=tEntry.apicals[targetSec][usedCompIndex];
						} else
							printf("Target Section out of bounds!");
					else if(targetType == 2)
						if(targetSec<tEntry.axonSz){
							usedCompIndex = (int)(tEntry.axonsSz[targetSec]*compDist);
							retVal+=tEntry.axon[targetSec][usedCompIndex];
						} else
							printf("Target Section out of bounds!");
					else if(targetType == 1)
						retVal+=tEntry.soma;
					break; //Break inner loop. (In the latest specification a gid can only be mentioned once per table.)
				}
			}
		}
	}
	return retVal;
 
return _lgetValueForSection;
 }
 
static double _hoc_getValueForSection(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getValueForSection (  );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
	//printf("Building lookup table...\n");
	if(sizeof(float)!=4 || sizeof(int)!=4){
		printf("sizeof does not match. Need to specify data type sizes more explicitly\n");
		return;
	}
	tableStruct** tempTable = (tableStruct**)(&(_p_ptr));
	tableStruct* tbl = 0;
	tbl = (tableStruct*)hoc_Emalloc(sizeof(tableStruct));
	tbl->numToRead = 0;
	if(ifarg(1)&&hoc_is_str_arg(1)){
		char tableName[128];
		sprintf(tableName,"%s",gargstr(1));
		FILE *file;
		//printf("Opening file: %s\n",tableName);
		if((file = fopen(tableName, "r"))==NULL) {
			//printf("FAILURE!\n");
			//tbl->numToRead=0;
			*tempTable = tbl;   			 
			return;
		}
		float retVal = 0;
		//int numToRead;
		int i,j,k;
		int gidNum;
		char header[128] = {0x0};
		char readChar = 0x1;
		i=0;
		int iAmAFloat;
		while(readChar!=0xA){
			fread(&readChar,1,1,file);
			header[i++]=readChar;
		}
		if(strncmp(header,"ExtracellularElectrodeLookupTable",33)!=0){
			*tempTable = tbl;
			printf("Header does not match: \n");
			printf("%s", header);
			return;
		}
		fread(&(tbl->vInfo),sizeof(char),1,file);		
		char circuitPath[512];
		readChar = 0x1;
		i=0;		
		while(readChar!=0xA){
			fread(&readChar,1,1,file);
			circuitPath[i++]=readChar;
		}
		//printf(circuitPath);
		fread(&(tbl->numToRead),sizeof(int),1,file);        
		tbl->numToRead = (int)htonl(tbl->numToRead);
		//printf("number: %d\n",tbl->numToRead);
		tbl->gids = (int**)hoc_Emalloc((tbl->numToRead)*sizeof(int *));
		tbl->factors = (float**)hoc_Emalloc((tbl->numToRead)*sizeof(float *));
		tbl->secData = (sectionEntry**)hoc_Emalloc((tbl->numToRead)*sizeof(sectionEntry *));
		tbl->tableSizes = (int*)hoc_Emalloc((tbl->numToRead)*sizeof(int));
		tbl->xPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));
		tbl->yPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));
		tbl->zPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));
		//printf("gids: %d; factors: %d; tableSizes: %d\n",tbl->gids,tbl->factors,tbl->tableSizes);   
		for(i = 0; i < tbl->numToRead; ++i){				
			fread((&iAmAFloat),sizeof(float),1,file);
			tbl->xPos[i] = swapForFloat(iAmAFloat);
			fread((&iAmAFloat),sizeof(float),1,file);
			tbl->yPos[i] = swapForFloat(iAmAFloat);
			fread((&iAmAFloat),sizeof(float),1,file);								
			tbl->zPos[i] = swapForFloat(iAmAFloat);				
			int tableSize;
			fread((&tableSize),sizeof(int),1,file);
			tableSize = (int)htonl(tableSize);
			//printf("tableSize: %d",tableSize);
			(tbl->tableSizes)[i]=tableSize;
			(tbl->gids)[i] = (int*)hoc_Emalloc(tableSize*sizeof(int));
			(tbl->factors)[i] = (float*)hoc_Emalloc(tableSize*sizeof(float));
			(tbl->secData)[i] = (sectionEntry*)hoc_Emalloc(tableSize*sizeof(sectionEntry));
			if((tbl->gids)[i]==0 || (tbl->factors)[i]==0 || (tbl->secData)[i]==0){
				printf("Problem allocating memory for factor tables\n");
				return;
			}						
			int index;				
			float factor;
			//unsigned char *inPoint = (unsigned char *) &iAmAFloat;
			//unsigned char *outPoint = (unsigned char *) &factor;
			unsigned int somaSize, axonSize, dendriteSize, apicalSize;
			for (j = 0; j < tableSize; ++j){
				fread(&index,4,1,file);
				(tbl->gids)[i][j]=(int)htonl(index);
				//TODO: byte swapping only needed on little endian systems. 
				fread((&iAmAFloat),sizeof(iAmAFloat),1,file);	//Need to read the float as an int before byte swapping, otherwise the float register might try to "repair" it...					
				//iAmAFloat = (int)htonl(iAmAFloat);
				//for(k = 0; k < 4; ++k)
				//	outPoint[k]=inPoint[k];															
				(tbl->factors)[i][j]=swapForFloat(iAmAFloat);
				fread(&somaSize,4,1,file);
				somaSize = (unsigned int)htonl(somaSize);
				fread(&axonSize,4,1,file);
				axonSize = (unsigned int)htonl(axonSize);
				(tbl->secData)[i][j].axonSz = axonSize;
				fread(&dendriteSize,4,1,file);
				dendriteSize = (unsigned int)htonl(dendriteSize);
				(tbl->secData)[i][j].basalSz = dendriteSize;
				fread(&apicalSize,4,1,file);
				apicalSize = (unsigned int)htonl(apicalSize);
				(tbl->secData)[i][j].apicalSz = apicalSize;
				if(somaSize!=1){
					printf("Need exactly one value for the soma. Got %d",somaSize);
					return;
				}
				
				(tbl->secData)[i][j].axonsSz = (int*)hoc_Emalloc(axonSize*sizeof(int));
				(tbl->secData)[i][j].axon = (float**)hoc_Emalloc(axonSize*sizeof(float*));				
				(tbl->secData)[i][j].basalsSz = (int*)hoc_Emalloc(dendriteSize*sizeof(int));
				(tbl->secData)[i][j].basals = (float**)hoc_Emalloc(dendriteSize*sizeof(float*));
				(tbl->secData)[i][j].apicalsSz = (int*)hoc_Emalloc(apicalSize*sizeof(int));
				(tbl->secData)[i][j].apicals = (float**)hoc_Emalloc(apicalSize*sizeof(float*));
				
				fread(&somaSize,4,1,file);
				somaSize = (unsigned int)htonl(somaSize);
				if(somaSize!=1){
					printf("Need exactly one value for the soma. Got %d",somaSize);
					return;
				}				
				readAndSwapInt((tbl->secData)[i][j].axonsSz,axonSize,file);
				readAndSwapInt((tbl->secData)[i][j].basalsSz,dendriteSize,file);
				readAndSwapInt((tbl->secData)[i][j].apicalsSz,apicalSize,file);
				
				fread((&iAmAFloat),sizeof(iAmAFloat),1,file);
				(tbl->secData)[i][j].soma = swapForFloat(iAmAFloat);		
				for(k = 0; k < axonSize; ++k){
					(tbl->secData)[i][j].axon[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].axonsSz[k]*sizeof(float));
					readAndSwapFloat((tbl->secData)[i][j].axon[k],(tbl->secData)[i][j].axonsSz[k],file);					
				}
				for(k = 0; k < dendriteSize; ++k){
					(tbl->secData)[i][j].basals[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].basalsSz[k]*sizeof(float));
					readAndSwapFloat((tbl->secData)[i][j].basals[k],(tbl->secData)[i][j].basalsSz[k],file);					
				}
				for(k = 0; k < apicalSize; ++k){
					(tbl->secData)[i][j].apicals[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].apicalsSz[k]*sizeof(float));
					readAndSwapFloat((tbl->secData)[i][j].apicals[k],(tbl->secData)[i][j].apicalsSz[k],file);					
				}								
			}
		}   		
	}
	*tempTable = tbl;
 }
 
}
}

static void initmodel() {
  int _i; double _save;_ninits++;
{

}
}

static void nrn_init(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 initmodel();
}}

static double _nrn_current(double _v){double _current=0.;v=_v;{
} return _current;
}

static void nrn_state(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v = 0.0; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 _nd = _ml->_nodelist[_iml];
 v=_v;
{
}}

}

static void terminal(){}

static void _initlists() {
 int _i; static int _first = 1;
  if (!_first) return;
_first = 0;
}

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/lookupTableV2.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file lookupTableV2.mod\n"
  " * @brief \n"
  " * @author reimann\n"
  " * @date 2010-12-30\n"
  " * @remark Copyright \n"
  "\n"
  " BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "VERBATIM\n"
  "#include <stdio.h>\n"
  "#include <stdlib.h>\n"
  "#include <string.h>\n"
  "#include <netinet/in.h>\n"
  "\n"
  "typedef struct{\n"
  "	float **axon;\n"
  "	float **apicals;\n"
  "	float **basals;\n"
  "	int *axonsSz;\n"
  "	int *apicalsSz;\n"
  "	int *basalsSz;\n"
  "	float soma;\n"
  "	unsigned int axonSz;\n"
  "	unsigned int apicalSz;\n"
  "	unsigned int basalSz;\n"
  "} sectionEntry;\n"
  "\n"
  "typedef struct{\n"
  "	int **gids;\n"
  "	sectionEntry **secData;\n"
  "	float **factors;\n"
  "	int numToRead;\n"
  "	int *tableSizes;\n"
  "	char vInfo;\n"
  "	float *xPos;\n"
  "	float *yPos;\n"
  "	float *zPos;\n"
  "}tableStruct;\n"
  "\n"
  "float swapForFloat(int iAmAFloat){\n"
  "	float factor;\n"
  "	unsigned char *inPoint = (unsigned char *) &iAmAFloat;\n"
  "	unsigned char *outPoint = (unsigned char *) &factor;\n"
  "	iAmAFloat = (int)htonl(iAmAFloat);\n"
  "	int k;\n"
  "	for(k = 0; k < 4; ++k)\n"
  "		outPoint[k]=inPoint[k];\n"
  "	return factor;\n"
  "};\n"
  "\n"
  "void readAndSwapInt(int *readInto, int number, FILE *file){\n"
  "	int i = 0;\n"
  "	fread(readInto,sizeof(int),number,file);\n"
  "	for(i = 0; i < number; ++i){\n"
  "		readInto[i] = (int)htonl(readInto[i]);\n"
  "	}        	\n"
  "};\n"
  "void readAndSwapFloat(float *readInto, int number, FILE *file){\n"
  "	int i = 0;\n"
  "	int tempReadArray[number];\n"
  "	fread(&tempReadArray,sizeof(int),number,file);\n"
  "	for(i = 0; i < number; ++i){\n"
  "		readInto[i] = swapForFloat(tempReadArray[i]);\n"
  "	}        	\n"
  "};\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "NEURON {\n"
  "	ARTIFICIAL_CELL lookupTableV2\n"
  "	POINTER ptr\n"
  "}\n"
  "ASSIGNED{\n"
  "	ptr\n"
  "}\n"
  "\n"
  "CONSTRUCTOR{\n"
  "	VERBATIM\n"
  "	//printf(\"Building lookup table...\\n\");\n"
  "	if(sizeof(float)!=4 || sizeof(int)!=4){\n"
  "		printf(\"sizeof does not match. Need to specify data type sizes more explicitly\\n\");\n"
  "		return;\n"
  "	}\n"
  "	tableStruct** tempTable = (tableStruct**)(&(_p_ptr));\n"
  "	tableStruct* tbl = 0;\n"
  "	tbl = (tableStruct*)hoc_Emalloc(sizeof(tableStruct));\n"
  "	tbl->numToRead = 0;\n"
  "	if(ifarg(1)&&hoc_is_str_arg(1)){\n"
  "		char tableName[128];\n"
  "		sprintf(tableName,\"%s\",gargstr(1));\n"
  "		FILE *file;\n"
  "		//printf(\"Opening file: %s\\n\",tableName);\n"
  "		if((file = fopen(tableName, \"r\"))==NULL) {\n"
  "			//printf(\"FAILURE!\\n\");\n"
  "			//tbl->numToRead=0;\n"
  "			*tempTable = tbl;   			 \n"
  "			return;\n"
  "		}\n"
  "		float retVal = 0;\n"
  "		//int numToRead;\n"
  "		int i,j,k;\n"
  "		int gidNum;\n"
  "		char header[128] = {0x0};\n"
  "		char readChar = 0x1;\n"
  "		i=0;\n"
  "		int iAmAFloat;\n"
  "		while(readChar!=0xA){\n"
  "			fread(&readChar,1,1,file);\n"
  "			header[i++]=readChar;\n"
  "		}\n"
  "		if(strncmp(header,\"ExtracellularElectrodeLookupTable\",33)!=0){\n"
  "			*tempTable = tbl;\n"
  "			printf(\"Header does not match: \\n\");\n"
  "			printf(\"%s\", header);\n"
  "			return;\n"
  "		}\n"
  "		fread(&(tbl->vInfo),sizeof(char),1,file);		\n"
  "		char circuitPath[512];\n"
  "		readChar = 0x1;\n"
  "		i=0;		\n"
  "		while(readChar!=0xA){\n"
  "			fread(&readChar,1,1,file);\n"
  "			circuitPath[i++]=readChar;\n"
  "		}\n"
  "		//printf(circuitPath);\n"
  "		fread(&(tbl->numToRead),sizeof(int),1,file);        \n"
  "		tbl->numToRead = (int)htonl(tbl->numToRead);\n"
  "		//printf(\"number: %d\\n\",tbl->numToRead);\n"
  "		tbl->gids = (int**)hoc_Emalloc((tbl->numToRead)*sizeof(int *));\n"
  "		tbl->factors = (float**)hoc_Emalloc((tbl->numToRead)*sizeof(float *));\n"
  "		tbl->secData = (sectionEntry**)hoc_Emalloc((tbl->numToRead)*sizeof(sectionEntry *));\n"
  "		tbl->tableSizes = (int*)hoc_Emalloc((tbl->numToRead)*sizeof(int));\n"
  "		tbl->xPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));\n"
  "		tbl->yPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));\n"
  "		tbl->zPos = (float*)hoc_Emalloc((tbl->numToRead)*sizeof(float));\n"
  "		//printf(\"gids: %d; factors: %d; tableSizes: %d\\n\",tbl->gids,tbl->factors,tbl->tableSizes);   \n"
  "		for(i = 0; i < tbl->numToRead; ++i){				\n"
  "			fread((&iAmAFloat),sizeof(float),1,file);\n"
  "			tbl->xPos[i] = swapForFloat(iAmAFloat);\n"
  "			fread((&iAmAFloat),sizeof(float),1,file);\n"
  "			tbl->yPos[i] = swapForFloat(iAmAFloat);\n"
  "			fread((&iAmAFloat),sizeof(float),1,file);								\n"
  "			tbl->zPos[i] = swapForFloat(iAmAFloat);				\n"
  "			int tableSize;\n"
  "			fread((&tableSize),sizeof(int),1,file);\n"
  "			tableSize = (int)htonl(tableSize);\n"
  "			//printf(\"tableSize: %d\",tableSize);\n"
  "			(tbl->tableSizes)[i]=tableSize;\n"
  "			(tbl->gids)[i] = (int*)hoc_Emalloc(tableSize*sizeof(int));\n"
  "			(tbl->factors)[i] = (float*)hoc_Emalloc(tableSize*sizeof(float));\n"
  "			(tbl->secData)[i] = (sectionEntry*)hoc_Emalloc(tableSize*sizeof(sectionEntry));\n"
  "			if((tbl->gids)[i]==0 || (tbl->factors)[i]==0 || (tbl->secData)[i]==0){\n"
  "				printf(\"Problem allocating memory for factor tables\\n\");\n"
  "				return;\n"
  "			}						\n"
  "			int index;				\n"
  "			float factor;\n"
  "			//unsigned char *inPoint = (unsigned char *) &iAmAFloat;\n"
  "			//unsigned char *outPoint = (unsigned char *) &factor;\n"
  "			unsigned int somaSize, axonSize, dendriteSize, apicalSize;\n"
  "			for (j = 0; j < tableSize; ++j){\n"
  "				fread(&index,4,1,file);\n"
  "				(tbl->gids)[i][j]=(int)htonl(index);\n"
  "				//TODO: byte swapping only needed on little endian systems. \n"
  "				fread((&iAmAFloat),sizeof(iAmAFloat),1,file);	//Need to read the float as an int before byte swapping, otherwise the float register might try to \"repair\" it...					\n"
  "				//iAmAFloat = (int)htonl(iAmAFloat);\n"
  "				//for(k = 0; k < 4; ++k)\n"
  "				//	outPoint[k]=inPoint[k];															\n"
  "				(tbl->factors)[i][j]=swapForFloat(iAmAFloat);\n"
  "				fread(&somaSize,4,1,file);\n"
  "				somaSize = (unsigned int)htonl(somaSize);\n"
  "				fread(&axonSize,4,1,file);\n"
  "				axonSize = (unsigned int)htonl(axonSize);\n"
  "				(tbl->secData)[i][j].axonSz = axonSize;\n"
  "				fread(&dendriteSize,4,1,file);\n"
  "				dendriteSize = (unsigned int)htonl(dendriteSize);\n"
  "				(tbl->secData)[i][j].basalSz = dendriteSize;\n"
  "				fread(&apicalSize,4,1,file);\n"
  "				apicalSize = (unsigned int)htonl(apicalSize);\n"
  "				(tbl->secData)[i][j].apicalSz = apicalSize;\n"
  "				if(somaSize!=1){\n"
  "					printf(\"Need exactly one value for the soma. Got %d\",somaSize);\n"
  "					return;\n"
  "				}\n"
  "				\n"
  "				(tbl->secData)[i][j].axonsSz = (int*)hoc_Emalloc(axonSize*sizeof(int));\n"
  "				(tbl->secData)[i][j].axon = (float**)hoc_Emalloc(axonSize*sizeof(float*));				\n"
  "				(tbl->secData)[i][j].basalsSz = (int*)hoc_Emalloc(dendriteSize*sizeof(int));\n"
  "				(tbl->secData)[i][j].basals = (float**)hoc_Emalloc(dendriteSize*sizeof(float*));\n"
  "				(tbl->secData)[i][j].apicalsSz = (int*)hoc_Emalloc(apicalSize*sizeof(int));\n"
  "				(tbl->secData)[i][j].apicals = (float**)hoc_Emalloc(apicalSize*sizeof(float*));\n"
  "				\n"
  "				fread(&somaSize,4,1,file);\n"
  "				somaSize = (unsigned int)htonl(somaSize);\n"
  "				if(somaSize!=1){\n"
  "					printf(\"Need exactly one value for the soma. Got %d\",somaSize);\n"
  "					return;\n"
  "				}				\n"
  "				readAndSwapInt((tbl->secData)[i][j].axonsSz,axonSize,file);\n"
  "				readAndSwapInt((tbl->secData)[i][j].basalsSz,dendriteSize,file);\n"
  "				readAndSwapInt((tbl->secData)[i][j].apicalsSz,apicalSize,file);\n"
  "				\n"
  "				fread((&iAmAFloat),sizeof(iAmAFloat),1,file);\n"
  "				(tbl->secData)[i][j].soma = swapForFloat(iAmAFloat);		\n"
  "				for(k = 0; k < axonSize; ++k){\n"
  "					(tbl->secData)[i][j].axon[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].axonsSz[k]*sizeof(float));\n"
  "					readAndSwapFloat((tbl->secData)[i][j].axon[k],(tbl->secData)[i][j].axonsSz[k],file);					\n"
  "				}\n"
  "				for(k = 0; k < dendriteSize; ++k){\n"
  "					(tbl->secData)[i][j].basals[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].basalsSz[k]*sizeof(float));\n"
  "					readAndSwapFloat((tbl->secData)[i][j].basals[k],(tbl->secData)[i][j].basalsSz[k],file);					\n"
  "				}\n"
  "				for(k = 0; k < apicalSize; ++k){\n"
  "					(tbl->secData)[i][j].apicals[k] = (float*)hoc_Emalloc((tbl->secData)[i][j].apicalsSz[k]*sizeof(float));\n"
  "					readAndSwapFloat((tbl->secData)[i][j].apicals[k],(tbl->secData)[i][j].apicalsSz[k],file);					\n"
  "				}								\n"
  "			}\n"
  "		}   		\n"
  "	}\n"
  "	*tempTable = tbl;\n"
  "	ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION vInfo(){\n"
  "	VERBATIM\n"
  "	tableStruct **tempData = (tableStruct**)(&_p_ptr);\n"
  "	tableStruct *tbl = (tableStruct*) *tempData;\n"
  "	return tbl->vInfo;\n"
  "	ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION getValueForGid(){	\n"
  "	VERBATIM\n"
  "	tableStruct **tempData = (tableStruct**)(&_p_ptr);\n"
  "	tableStruct *tbl = (tableStruct*) *tempData;\n"
  "	if((tbl->numToRead)==0)\n"
  "		return 1;\n"
  "	float retVal = 0;\n"
  "	int i,j;\n"
  "	if(ifarg(1)){\n"
  "		int targetGid = (int) *getarg(1);\n"
  "		for(i = 0; i < (tbl->numToRead); ++i){\n"
  "			for (j = 0; j < (tbl->tableSizes)[i]; ++j){\n"
  "				if((tbl->gids)[i][j]==targetGid){\n"
  "					retVal+=(tbl->factors)[i][j];\n"
  "					break; //Break inner loop. (In the latest specification a gid can only be mentioned once per table.)\n"
  "				}\n"
  "			}\n"
  "		}\n"
  "	}\n"
  "	return retVal;   \n"
  "	ENDVERBATIM        \n"
  "}\n"
  "\n"
  "FUNCTION getValueForSection(){\n"
  "	VERBATIM\n"
  "	tableStruct **tempData = (tableStruct**)(&_p_ptr);\n"
  "	tableStruct *tbl = (tableStruct*) *tempData;\n"
  "	if((tbl->numToRead)==0)\n"
  "		return 1;\n"
  "	float retVal = 0;\n"
  "	int i,j;\n"
  "	if(ifarg(4)){\n"
  "		int targetGid = (int) *getarg(1);\n"
  "		int targetType = (int) *getarg(2);\n"
  "		int targetSec = (int) *getarg(3);\n"
  "		int usedCompIndex;\n"
  "		float compDist = (float) *getarg(4);\n"
  "		for(i = 0; i < (tbl->numToRead); ++i){	//TODO: Argh, use a map or something!\n"
  "			for (j = 0; j < (tbl->tableSizes)[i]; ++j){\n"
  "				if((tbl->gids)[i][j]==targetGid){ //or directly sort it by gid\n"
  "					sectionEntry tEntry = (tbl->secData)[i][j];\n"
  "					if(targetType == 3)		\n"
  "						if(targetSec<tEntry.basalSz){\n"
  "							usedCompIndex = (int)(tEntry.basalsSz[targetSec]*compDist);\n"
  "							retVal+=tEntry.basals[targetSec][usedCompIndex];	\n"
  "						} else\n"
  "							printf(\"Target Section out of bounds: %i, %i, %i\",targetGid,targetType,targetSec);\n"
  "					else if(targetType == 4)\n"
  "						if(targetSec<tEntry.apicalSz){\n"
  "							usedCompIndex = (int)(tEntry.apicalsSz[targetSec]*compDist);\n"
  "							retVal+=tEntry.apicals[targetSec][usedCompIndex];\n"
  "						} else\n"
  "							printf(\"Target Section out of bounds!\");\n"
  "					else if(targetType == 2)\n"
  "						if(targetSec<tEntry.axonSz){\n"
  "							usedCompIndex = (int)(tEntry.axonsSz[targetSec]*compDist);\n"
  "							retVal+=tEntry.axon[targetSec][usedCompIndex];\n"
  "						} else\n"
  "							printf(\"Target Section out of bounds!\");\n"
  "					else if(targetType == 1)\n"
  "						retVal+=tEntry.soma;\n"
  "					break; //Break inner loop. (In the latest specification a gid can only be mentioned once per table.)\n"
  "				}\n"
  "			}\n"
  "		}\n"
  "	}\n"
  "	return retVal;\n"
  "	ENDVERBATIM\n"
  "}\n"
  ;
#endif
