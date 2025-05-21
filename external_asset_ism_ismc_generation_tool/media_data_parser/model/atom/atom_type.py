from enum import Enum


class AtomType(Enum):
    MOOV_ATOM_TYPE = 'moov'
    MOOF_ATOM_TYPE = 'moof'
    MFRA_ATOM_TYPE = 'mfra'
    MVEX_ATOM_TYPE = 'mvex'

    UNKNOWN = None

    @classmethod
    def _missing_(cls, value):
        return AtomType.UNKNOWN
