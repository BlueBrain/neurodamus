COMMENT
If the local variable step method is used then the only variables that should
be added are variables of the cell in which this ALU has been instantiated.
ENDCOMMENT

NEURON {
	POINT_PROCESS ALU
	POINTER ptr
	RANGE Dt
	RANGE output
}

PARAMETER {
	Dt = .1 (ms)
	output = 0
}

ASSIGNED {
	ptr
}

INITIAL {
	net_send(0, 1)
}


NET_RECEIVE(w) {
	process()
	net_send(Dt, 1)
}

VERBATIM

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern int ifarg(int iarg);

typedef struct {
	double** ptrs_; /* list of pointers to hoc variables */
	int np_;
	int psize_;
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

ENDVERBATIM

CONSTRUCTOR {
VERBATIM {
	INFOCAST;
	Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
	info->psize_ = 10;
	info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();
	info->np_ = 0;
	*ip = info;
	
        if (ifarg(2)) {
             Dt = *getarg(2);
        }
}
ENDVERBATIM
}

DESTRUCTOR {
VERBATIM {
	INFOCAST; Info* info = *ip;
	free(info->ptrs_);
	free(info);
}
ENDVERBATIM
}


PROCEDURE addvar() { : double* pd
VERBATIM { INFOCAST; Info* info = *ip;
	if (info->np_ >= info->psize_) {
		info->psize_ += 10;
		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();
	}
	info->ptrs_[info->np_] = hoc_pgetarg(1);
	++info->np_;
    //printf("I have %d values..\n", info->np_);
}
ENDVERBATIM
}

PROCEDURE process() {
VERBATIM { INFOCAST; Info* info = *ip;
	int i;
	double n = 0;
	for (i=0; i < info->np_; ++i) {
      //  printf("%f", *info->ptrs_[i]);
		n += *info->ptrs_[i];
	}
    //printf("\n");
//	output = n/info->np_;
	if (info->np_ > 0) 
	  output = n/info->np_;
	else output = 0;
}
ENDVERBATIM
}
