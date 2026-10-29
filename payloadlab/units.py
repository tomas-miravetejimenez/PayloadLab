"""Small, explicit unit conversions used throughout PayloadLab."""

G0 = 9.80665
MM_TO_M = 1e-3
N_TO_KN = 1e-3
NM_TO_NMM = 1e3


def mm_to_m(value):
    return value * MM_TO_M


def m_to_mm(value):
    return value / MM_TO_M
