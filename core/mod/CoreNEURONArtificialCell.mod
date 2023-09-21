COMMENT
/**
 * @file CoreNEURONArtificialCell.mod
 * @brief Artificial cell that is used to create empty cells for ranks without cells
 */
ENDCOMMENT

NEURON {
    THREADSAFE
    ARTIFICIAL_CELL CoreNEURONArtificialCell
}

NET_RECEIVE (w) {
    : net_event is required for neuron code generation and hence false if block
    if (0) {
        net_event(t)
    }
}
