COMMENT
/**
 * @file lookupTableV2.mod
 * @brief 
 * @author reimann
 * @date 2010-12-30
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

VERBATIM
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

ENDVERBATIM

NEURON {
	ARTIFICIAL_CELL lookupTableV2
	POINTER ptr
}
ASSIGNED{
	ptr
}

CONSTRUCTOR{
	VERBATIM
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
	ENDVERBATIM
}

FUNCTION vInfo(){
	VERBATIM
	tableStruct **tempData = (tableStruct**)(&_p_ptr);
	tableStruct *tbl = (tableStruct*) *tempData;
	return tbl->vInfo;
	ENDVERBATIM
}

FUNCTION getValueForGid(){	
	VERBATIM
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
	ENDVERBATIM        
}

FUNCTION getValueForSection(){
	VERBATIM
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
	ENDVERBATIM
}
