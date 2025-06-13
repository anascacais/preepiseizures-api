from enum import Enum

class ModalityEnum(str, Enum):
    hospital_eeg = "hospital_eeg"
    wearable = "wearable"
    hospital_video = "hospital_video"
    report = "report"


class SeizureTypeEnum(str, Enum):
    focal = "focal"
    aware = "aware"
    motor = "motor"
    automatisms = "automatisms"
    impaired_awareness = "impaired awareness"
    tonic = "tonic"
    to_bilateral_tonic_clonic = "to bilateral tonic-clonic"
    generalized = "generalized"
    absence = "absence"
    tonic_clonic = "tonic-clonic"
    non_motor = "non-motor"
    behavior_arrest = "behavior arrest"