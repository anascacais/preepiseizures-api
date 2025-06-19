from enum import Enum

class ModalityEnum(str, Enum):
    hospital_eeg = "hospital_eeg"
    wearable = "wearable"
    hospital_video = "hospital_video"
    report = "report"


class SeizureClassEnum(str, Enum):
    seizure = "seizure"
    non_seizure = "non-seizure"
    subclinical = "subclinical"
    electrographic = "electrographic"
    non_electrographic = "non-electrographic"
    aware = "aware"
    impaired_awareness = "impaired awareness"
    unknown_awareness = "unknown awareness"
    focal = "focal"
    generalized = "generalized"
    to_bilateral_tonic_clonic = "to bilateral tonic-clonic"
    tonic_clonic = "tonic-clonic"
    tonic = "tonic"
    absence = "absence"
    motor = "motor"
    non_motor = "non-motor"
    automatisms = "automatisms"
    behavior_arrest = "behavior arrest"
