COMMENT
/**
 * @file netstim_inhpoisson.mod
 * @brief 
 * @author ebmuller
 * @date 2011-03-16
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

: Inhibitory poisson generator by the thinning method.
: See:  
:   Muller, Buesing, Schemmel, Meier (2007). "Spike-Frequency Adapting
:   Neural Ensembles: Beyond Mean Adaptation and Renewal Theories",
:   Neural Computation 19:11, 2958-3010.
:   doi:10.1162/neco.2007.19.11.2958
:
: Based on vecstim.mod and netstim2.mod shipped with PyNN
: Author: Eilif Muller, 2011

VERBATIM
extern int ifarg(int iarg);
extern double* vector_vec(void* vv);
extern int vector_capacity(void* vv);
extern void* vector_arg(int iarg);
double nrn_random_pick(void* r);
void* nrn_random_arg(int argpos);
ENDVERBATIM

NEURON {
  ARTIFICIAL_CELL InhPoissonStim
  RANGE rmax
  RANGE duration
  POINTER uniform_rng, exp_rng 
  :THREADSAFE : only true if every instance has its own distinct Random
}

PARAMETER {
  interval_min = 1.0  : average spike interval of surrogate Poisson process
  duration	= 1e6 (ms) <0,1e9>   : duration of firing (msec)
}

ASSIGNED {
   vecRate
   vecTbins
   index
   curRate
   start (ms)
   event (ms)
   uniform_rng
   exp_rng
   rmax

}

INITIAL {
   index = 0.

   : determine start of spiking.
   VERBATIM
   void *vvTbins = *((void**)(&vecTbins));
   double* px;

   if (vvTbins && vector_capacity(vvTbins)>=1) {
     px = vector_vec(vvTbins);
     start = px[0];
     if (start < 0.0) start=0.0;
   }
   else start = 0.0;

   /* first event is at the start 
   TODO: This should draw from a more appropriate dist
   that has the surrogate process starting a t=-inf
   */
   event = start;

   /* set curRate */
   void *vvRate = *((void**)(&vecRate));
   px = vector_vec(vvRate);

   /* set rmax */
   rmax = 0.0;
   int i;
   for (i=0;i<vector_capacity(vvRate);i++) {
      if (px[i]>rmax) rmax = px[i];
   }

   if (vvRate && vector_capacity(vvRate)>0) {
     curRate = px[0];
   }
   else {
      curRate = 1.0;
      rmax = 1.0;
   }

   ENDVERBATIM

   update_time()
   erand() : for some reason, the first erand() call seems
           : to give implausibly large values, so we discard it
   generate_next_event()
   : stop even producing surrogate events if we are past duration
   if (t+event < start+duration) {
     net_send(event, 0)
   }

 
}

: This procedure queues the next surrogate event in the 
: poisson process (rate=ramx) to be thinned.
PROCEDURE generate_next_event() {

	event = 1000.0/rmax*erand()
	: but not earlier than 0
	if (event < 0) {
		event = 0
	}

}

: Not sure why this func is needed
PROCEDURE seed(x) {
	set_seed(x)
}

: 1st arg: exp_rng
: 2nd arg: uniform_rng
PROCEDURE setRNGs() {
VERBATIM
{
  /* Set exp_rng from first arg */
  void** pv = (void**)(&_p_exp_rng);
  if (ifarg(1)) {
    *pv = nrn_random_arg(1);
  }else{
    *pv = (void*)0;
  }

  /* Set uniform_rng from second arg */
  pv = (void**)(&_p_uniform_rng);
  if (ifarg(2)) {
    *pv = nrn_random_arg(2);
  }else{
    *pv = (void*)0;
  }

}
ENDVERBATIM
}


FUNCTION urand() {
VERBATIM
	if (_p_uniform_rng) {
		/*
		:Supports separate independent but reproducible streams for
		: each instance. However, the corresponding hoc Random
		: distribution MUST be set to Random.uniform(0,1)
		*/
		_lurand = nrn_random_pick(_p_uniform_rng);
	}else{
  	  hoc_execerror("multithread random in NetStim"," only via hoc Random");
	}
ENDVERBATIM
}

FUNCTION erand() {
VERBATIM
	if (_p_exp_rng) {
		/*
		:Supports separate independent but reproducible streams for
		: each instance. However, the corresponding hoc Random
		: distribution MUST be set to Random.negexp(1)
		*/
		_lerand = nrn_random_pick(_p_exp_rng);
	}else{
  	  hoc_execerror("multithread random in NetStim"," only via hoc Random");
	}
ENDVERBATIM
}





PROCEDURE setTbins() {
VERBATIM

  void** vv;
  vv = (void**)(&vecTbins);
  *vv = (void*)0;

  if (ifarg(1)) {
    *vv = vector_arg(1);

    /*int size = vector_capacity(*vv);
    int i;
    double* px = vector_vec(*vv);
    for (i=0;i<size;i++) {
      printf("%f ", px[i]);
    }*/
  }

ENDVERBATIM
}


PROCEDURE setRate() {
VERBATIM

  void** vv;
  vv = (void**)(&vecRate);
  *vv = (void*)0;

  if (ifarg(1)) {
    *vv = vector_arg(1);

    int size = vector_capacity(*vv);
    int i;
    double max=0.0;
    double* px = vector_vec(*vv);
    for (i=0;i<size;i++) {
    	if (px[i]>max) max = px[i];
    }
    rmax = max;

  }
ENDVERBATIM
}

PROCEDURE update_time() {
VERBATIM
  void* vv; int i, i_prev, size; double* px;
  i = (int)index;
  i_prev = i;

  if (i >= 0) { // are we disabled?
    vv = *((void**)(&vecTbins));
    if (vv) {
      size = vector_capacity(vv);
      px = vector_vec(vv);
      /* advance to current tbins without exceeding array bounds */
      while ((i+1 < size) && (t>=px[i+1])) {
	index += 1.;
	i += 1;
      }
      /* did the index change? */
      if (i!=i_prev) {
        /* advance curRate to next vecRate if possible */
        void *vvRate = *((void**)(&vecRate));
        if (vvRate && vector_capacity(vvRate)>i) {
          px = vector_vec(vvRate);
          curRate = px[i];
        }
        else curRate = 1.0;
      }

      /* have we hit last bin? ... disable time advancing leaving curRate as it is*/
      if (i==size)
        index = -1.;

    } else { /* no vecTbins, use some defaults */
      rmax = 1.0;
      curRate = 1.0;
      index = -1.; /* no vecTbins ... disable time advancing & Poisson unit rate. */
    }
  }

ENDVERBATIM
}

NET_RECEIVE (w) {
	if (flag == 0) { : external event

	  update_time()
	  generate_next_event()
          : stop even producing surrogate events if we are past duration
          if (t+event < start+duration) {
            net_send(event, 0)
          }

          : trigger event
VERBATIM	    
          double u = (double)urand();
	  /*printf("InhPoisson: spike time at time %g urand=%g curRate=%g, rmax=%g, curRate/rmax=%g \n",t, u, curRate, rmax, curRate/rmax);*/
	  if (u<curRate/rmax) {
ENDVERBATIM
	    :printf("InhPoisson: spike time at time %g\n",t)
            net_event(t)
VERBATIM	    
          }
ENDVERBATIM


	}	  
}

