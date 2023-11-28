"""
Collection of modules for analyzing, annotating, and expanding upon results from REFS.
"""
from . import _version
# import json
# from packaging import version
# import os

__version__ = _version.get_versions()["version"]

from .target_annotation import TargetAnnotation
from .open_targets import (
    request_ot_target_annotation,
    request_ot_associated_targets,
    request_ot_target_disease_evidences,
    request_open_targets,
)
from .pharos import request_pharos_target_annotation
from .ontology_source import request_ebi_ontology_sources
from .extract_table import ExtractTable

# # check if there are newer versions
# if os.path.exists("/projects/Gemini/conda_channel/channeldata.json"):
#     with open(
#         "/projects/Gemini/conda_channel/channeldata.json", "r", encoding="UTF-8"
#     ) as file:
#         temp = json.load(file)
#         newest_version = temp["packages"]["analysis-functions"]["version"]

#     if version.parse(__version__) < version.parse(newest_version):
#         print(f"Newer version available: {newest_version}. Please update.")
