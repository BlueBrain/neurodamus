#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;

extern void _ALU_reg(void);
extern void _ASCIIrecord_reg(void);
extern void _BinReportHelper_reg(void);
extern void _BinReports_reg(void);
extern void _CoreConfig_reg(void);
extern void _DetAMPANMDA_reg(void);
extern void _DetGABAAB_reg(void);
extern void _gap_reg(void);
extern void _GluSynapse_reg(void);
extern void _GluSynapse_TM_reg(void);
extern void _HDF5reader_reg(void);
extern void _HDF5record_reg(void);
extern void _lookupTableV2_reg(void);
extern void _memoryaccess_reg(void);
extern void _MemUsage_reg(void);
extern void _netstim_inhpoisson_reg(void);
extern void _ProbAMPANMDA_EMS_reg(void);
extern void _ProbGABAAB_EMS_reg(void);
extern void _ProfileHelper_reg(void);
extern void _SonataReportHelper_reg(void);
extern void _SonataReports_reg(void);
extern void _SpikeWriter_reg(void);
extern void _SynapseReader_reg(void);
extern void _TTXDynamicsSwitch_reg(void);
extern void _utility_reg(void);
extern void _VecStim_reg(void);

void modl_reg(){
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");

    fprintf(stderr," \"mods.tmp/ALU.mod\"");
    fprintf(stderr," \"mods.tmp/ASCIIrecord.mod\"");
    fprintf(stderr," \"mods.tmp/BinReportHelper.mod\"");
    fprintf(stderr," \"mods.tmp/BinReports.mod\"");
    fprintf(stderr," \"mods.tmp/CoreConfig.mod\"");
    fprintf(stderr," \"mods.tmp/DetAMPANMDA.mod\"");
    fprintf(stderr," \"mods.tmp/DetGABAAB.mod\"");
    fprintf(stderr," \"mods.tmp/gap.mod\"");
    fprintf(stderr," \"mods.tmp/GluSynapse.mod\"");
    fprintf(stderr," \"mods.tmp/GluSynapse_TM.mod\"");
    fprintf(stderr," \"mods.tmp/HDF5reader.mod\"");
    fprintf(stderr," \"mods.tmp/HDF5record.mod\"");
    fprintf(stderr," \"mods.tmp/lookupTableV2.mod\"");
    fprintf(stderr," \"mods.tmp/memoryaccess.mod\"");
    fprintf(stderr," \"mods.tmp/MemUsage.mod\"");
    fprintf(stderr," \"mods.tmp/netstim_inhpoisson.mod\"");
    fprintf(stderr," \"mods.tmp/ProbAMPANMDA_EMS.mod\"");
    fprintf(stderr," \"mods.tmp/ProbGABAAB_EMS.mod\"");
    fprintf(stderr," \"mods.tmp/ProfileHelper.mod\"");
    fprintf(stderr," \"mods.tmp/SonataReportHelper.mod\"");
    fprintf(stderr," \"mods.tmp/SonataReports.mod\"");
    fprintf(stderr," \"mods.tmp/SpikeWriter.mod\"");
    fprintf(stderr," \"mods.tmp/SynapseReader.mod\"");
    fprintf(stderr," \"mods.tmp/TTXDynamicsSwitch.mod\"");
    fprintf(stderr," \"mods.tmp/utility.mod\"");
    fprintf(stderr," \"mods.tmp/VecStim.mod\"");
    fprintf(stderr, "\n");
  }
  _ALU_reg();
  _ASCIIrecord_reg();
  _BinReportHelper_reg();
  _BinReports_reg();
  _CoreConfig_reg();
  _DetAMPANMDA_reg();
  _DetGABAAB_reg();
  _gap_reg();
  _GluSynapse_reg();
  _GluSynapse_TM_reg();
  _HDF5reader_reg();
  _HDF5record_reg();
  _lookupTableV2_reg();
  _memoryaccess_reg();
  _MemUsage_reg();
  _netstim_inhpoisson_reg();
  _ProbAMPANMDA_EMS_reg();
  _ProbGABAAB_EMS_reg();
  _ProfileHelper_reg();
  _SonataReportHelper_reg();
  _SonataReports_reg();
  _SpikeWriter_reg();
  _SynapseReader_reg();
  _TTXDynamicsSwitch_reg();
  _utility_reg();
  _VecStim_reg();
}
