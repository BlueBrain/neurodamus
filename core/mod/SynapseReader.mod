COMMENT
/**
 * @file syn2reader.mod
 * @brief A Reader for Synapse files, inc Nrn and SYN2
 * @author F. Pereira
 * @date 2018-06
 * @remark Copyright (C) 2018 EPFL - Blue Brain Project
 * All rights reserved. Do not distribute without further notice.
 */

// This file is a reminiscent of the Syntool reader mod which used to get synapses via
// synapsetool, which supported a number of formats, inc NRN, SYN2 and SONATA edges.
//
// This section is particularly useful to given insight on the Neurodamus internal
// synapse structure. Notice that we historically (from nrn) had 19 fields, out of which
// we stored 11, later bumped to 14.

// The NRN Synapse fields according to SYN2 transitional spec
// ---------------------------------------------------------------------
// | Synapse field name     [ND index] |  Gap-J fields name
// ---------------------------------------------------------------------
//   - connected_neurons_post          | connected_neurons_post (not loaded)
//   0 connected_neurons_pre      [0]  | connected_neurons_pre
//   1 delay                      [1]  | (N/A)
//   2 morpho_section_id_post     [2]  | morpho_section_id_post
//   3 morpho_segment_id_post     [3]  | morpho_section_id_post
//   4 morpho_offset_segment_post [4]  | morpho_section_id_post
//   5 morpho_section_id_pre           | morpho_section_id_pre (unused)
//   6 morpho_segment_id_pre           | morpho_section_id_pre (unused)
//   7 morpho_offset_segment_pre       | morpho_section_id_pre (unused)
//   8 conductance                [5]  | conductance (required)
//   9 u_syn                      [6]  | (N/A)
//  10 depression_time            [7]  | junction_id_pre
//  11 facilitation_time          [8]  | junction_id_post
//  12 decay_time                 [9]  | N/A
//  13 syn_type_id                [10] | N/A
//  14 morpho_type_id_pre              | N/A
//  15 morpho_branch_order_dend        | N/A
//  16 morpho_branch_order_axon        | N/A
//  17 n_rrp_vesicles (optional)  [11] | N/A
//  18 morpho_section_type_pos         | N/A
//  NA u_hill_coefficient         [12] | N/A
//  NA conductance_scale_factor   [13] | N/A


// The SYN2 v2 spec fields
// : This spec deprecates compat with NRN
// ---------------------------------------------------------------------
// | Synapse field name     [ND index] |  Gap-J fields name
// ---------------------------------------------------------------------
//  connected_neurons_post            | connected_neurons_post (not loaded)
//  connected_neurons_pre        [0]  | connected_neurons_pre
//  delay                        [1]  | (N/A)
//  morpho_section_id_post       [2]  | morpho_section_id_post
//  (N/A)                        [3]  | (N/A)
//  morpho_section_fraction_post [4]  | morpho_section_fraction_post
//  conductance                  [5]  | conductance (required)
//  u_syn                        [6]  | (N/A)
//  depression_time              [7]  | junction_id_pre
//  facilitation_time            [8]  | junction_id_post
//  decay_time                   [9]  | (N/A)
//  syn_type_id                  [10] | (N/A)
//  n_rrp_vesicles  (required)   [11] | (N/A)
//  u_hill_coefficient           [12] | (N/A)
//  conductance_scale_factor     [13] | (N/A)


// NEUROGLIAL Field Spec  (for reference only)
// -----------------------------------
// | Synapse field name     [ND index]
// -----------------------------------
//  source_node_id     [query field]
//  target_node_id               [0]  !! NOTE: target
//  synapse_id                   [1]
//  morpho_section_id_pre        [2]
//  morpho_segment_id_pre        [3]
//  morpho_offset_segment_pre    [4]

ENDCOMMENT
