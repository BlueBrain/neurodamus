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

NEURON {
THREADSAFE
  ARTIFICIAL_CELL InhPoissonStim
  RANGE rmax
  RANGE duration
  POINTER uniform_rng, exp_rng, vecRate, vecTbins
  :THREADSAFE : only true if every instance has its own distinct Random
}
VERBATIM
extern int ifarg(int iarg);
extern double* vector_vec(void* vv);
extern void* vector_new1(int _i);
extern int vector_capacity(void* vv);
extern void* vector_arg(int iarg);
#if !defined(CORENEURON_BUILD)
double nrn_random_pick(void* r);
#endif
void* nrn_random_arg(int argpos);

// constant used to indicate an event triggered after a restore to restart the main event loop
const int POST_RESTORE_RESTART_FLAG = 99;

ENDVERBATIM


PARAMETER {
  interval_min = 1.0  : average spike interval of surrogate Poisson process
  duration	= 1e6 (ms) <0,1e9>   : duration of firing (msec)
}

VERBATIM
#include "nrnran123.h"
ENDVERBATIM

ASSIGNED {
   vecRate
   vecTbins
   index
   curRate
   start (ms)
   event (ms)
   uniform_rng
   exp_rng
   usingR123
   rmax

}

INITIAL {
   index = 0.

   : determine start of spiking.
   VERBATIM
   void *vvTbins = *((void**)(&_p_vecTbins));
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
   void *vvRate = *((void**)(&_p_vecRate));
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

: Supports multiple rng types: mcellran4, random123
: mcellran4:
: 1st arg: exp_rng
: 2nd arg: uniform_rng
: random123
: 3 exp seeds
: 3 uniform seeds
PROCEDURE setRNGs() {
VERBATIM
{
#if !NRNBBCORE
    usingR123 = 0;
    if( ifarg(1) && hoc_is_double_arg(1) ) {
        nrnran123_State** pv = (nrnran123_State**)(&_p_exp_rng);
        
        if (*pv) {
            nrnran123_deletestream(*pv);
            *pv = (nrnran123_State*)0;
        }
        *pv = nrnran123_newstream3((uint32_t)*getarg(1), (uint32_t)*getarg(2), (uint32_t)*getarg(3));
        
        pv = (nrnran123_State**)(&_p_uniform_rng);
        if (*pv) {
            nrnran123_deletestream(*pv);
            *pv = (nrnran123_State*)0;
        }
        *pv = nrnran123_newstream3((uint32_t)*getarg(4), (uint32_t)*getarg(5), (uint32_t)*getarg(6));

        usingR123 = 1;
    } else if( ifarg(1) ) {
        void** pv = (void**)(&_p_exp_rng);
        *pv = nrn_random_arg(1);

        pv = (void**)(&_p_uniform_rng);
        *pv = nrn_random_arg(2);
    } else {
        if( usingR123 ) {
            nrnran123_State** pv = (nrnran123_State**)(&_p_exp_rng);
            nrnran123_deletestream(*pv);
            pv = (nrnran123_State**)(&_p_uniform_rng);
            nrnran123_deletestream(*pv);
            _p_exp_rng = (nrnran123_State*)0;
            _p_uniform_rng = (nrnran123_State*)0;
        }
    }
#endif
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
            if( usingR123 ) {
		_lurand = nrnran123_dblpick((nrnran123_State*)_p_uniform_rng);
            } else {
#if !NRNBBCORE
		_lurand = nrn_random_pick(_p_uniform_rng);
#endif
            }
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
            if( usingR123 ) {
		_lerand = nrnran123_negexp((nrnran123_State*)_p_exp_rng);
            } else {
#if !NRNBBCORE
		_lerand = nrn_random_pick(_p_exp_rng);
#endif
            }
	}else{
  	  hoc_execerror("multithread random in NetStim"," only via hoc Random");
	}
ENDVERBATIM
}





PROCEDURE setTbins() {
VERBATIM

  void** vv;
  vv = (void**)(&_p_vecTbins);
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
  vv = (void**)(&_p_vecRate);
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
    vv = *((void**)(&_p_vecTbins));
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
        void *vvRate = *((void**)(&_p_vecRate));
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



COMMENT
/**
 * Upon a net_receive, we do up to two things.  The first is to determine the next time this artificial cell triggers
 * and sending a self event.  Second, we check to see if the synapse coupled to this artificial cell should be activated.
 * This second task is not done if we have just completed a state restore and only wish to restart the self event triggers.
 *
 * @param flag 0 for Typical activation, POST_RESTORE_RESTART_FLAG for only restarting the self event triggers 
 */
ENDCOMMENT
NET_RECEIVE (w) {
    : Note - if we have restored a sim from a saved state.  We need to restart the queue, but do not generate a spike now
    if ( flag == POST_RESTORE_RESTART_FLAG ) {
        net_send(event, 0)
    } else if (flag == 0 ) {
        update_time()
        generate_next_event()
        
        : stop even producing surrogate events if we are past duration
        if (t+event < start+duration) {
            net_send(event, 0)
        }
    
        : check if we trigger event on coupled synapse
VERBATIM
        double u = (double)urand(_threadargs_);
        //printf("InhPoisson: spike time at time %g urand=%g curRate=%g, rmax=%g, curRate/rmax=%g \n",t, u, curRate, rmax, curRate/rmax);
        if (u<curRate/rmax) {
ENDVERBATIM
            :printf("InhPoisson: spike time at time %g\n",t)
            net_event(t)
VERBATIM
        }
ENDVERBATIM
    }
}


COMMENT
/**
 * Supply the POST_RESTORE_RESTART_FLAG.  For example, so a hoc program can call a NetCon.event with the proper event value
 *
 * @return POST_RESTORE_RESTART_FLAG value for entities that wish to use its value 
 */
ENDCOMMENT
FUNCTION getPostRestoreFlag() {
VERBATIM
    return POST_RESTORE_RESTART_FLAG;
ENDVERBATIM
}


COMMENT
/**
 * After a resume, populate variable 'event' with the first event time that can be given to net_send such that the elapsed time is 
 * greater than the resume time.  Note that if an event was generated just before saving, but due for delivery afterwards (delay 0.1), 
 * then the hoc layer must deliver this event directly.
 *
 * @param delay (typically 0.1) #TODO: accept a parameter rather than using hard coded value below
 * @return Time of the next event.  If this is less than the current time (resume time), the hoc layer should deliver the event immediately
 */
ENDCOMMENT
FUNCTION resumeEvent() {
    LOCAL elapsed_time, delay
    : Since we want the minis to be consistent with the previous run, it should use t=0 as a starting point until it
    : reaches an elapsed_time >= resume_t.  Events generated right before the save time but scheduled for delivery afterwards
    : will already be restored to the NetCon by the bbsavestate routines
    
    elapsed_time = event : event has some value from the INITIAL block
    delay = 0.1

    while( elapsed_time < t ) {
        update_time()
        generate_next_event()
        elapsed_time = elapsed_time + event
    }
    resumeEvent = elapsed_time
    event = elapsed_time-t
}

