import numpy as np
import fast_functions as ff


def DSC_computation(label, pred):
    P = np.zeros(3, dtype=np.uint32)
    ff.DSC_computation(label, pred, P)
    return 2 * float(P[2]) / (P[0] + P[1]), P[2], P[1], P[0]


def post_processing(F, S, threshold, organ_ID):
    ff.post_processing(F, S, threshold, False)
    return F
