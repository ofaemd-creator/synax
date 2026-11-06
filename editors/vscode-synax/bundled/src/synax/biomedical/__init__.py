"""
SYNAX Biomedical Signal Processing & Retrospective Evaluation Package (`synax.biomedical`)
==========================================================================================
Strictly non-clinical research toolkit (EU MDR 2017/745 & IEC 60601-2-4 research-only).
Provides bit-exact MIT/PhysioNet WFDB binary waveform & annotation readers, physiological
rhythm interval reconstruction, and SYNAX (.sx) neuro-symbolic feature extraction.
"""

from .wfdb_reader import (
    WFDBAnnotation,
    WFDBChannelSpec,
    WFDBHeader,
    WFDBRecord,
    RhythmSegment,
    extract_rhythm_segments,
    read_wfdb_annotations,
    read_wfdb_header,
    read_wfdb_record,
)
try:  # Feature engine requires the optional `numpy` extra (`pip install synax[fast]`)
    from .vf_features import (
        FEATURE_NAMES,
        RecordKernelTelemetry,
        SynaxBiomedicalPipeline,
        extract_window_features,
    )
except ImportError:  # pragma: no cover - WFDB reader stays usable without numpy
    FEATURE_NAMES = ()  # type: ignore[assignment]
    RecordKernelTelemetry = None  # type: ignore[assignment]
    SynaxBiomedicalPipeline = None  # type: ignore[assignment]
    extract_window_features = None  # type: ignore[assignment]

__all__ = [
    "WFDBAnnotation",
    "WFDBChannelSpec",
    "WFDBHeader",
    "WFDBRecord",
    "RhythmSegment",
    "extract_rhythm_segments",
    "read_wfdb_annotations",
    "read_wfdb_header",
    "read_wfdb_record",
    "FEATURE_NAMES",
    "RecordKernelTelemetry",
    "SynaxBiomedicalPipeline",
    "extract_window_features",
]
