"""Utility functions for target-annotation package
"""
import requests
import requests_cache
import warnings
from typeguard import typechecked
from typing import Optional
from datetime import timedelta


@typechecked
def get_ensembl_from_uniprot(uniprot: str, timeout: Optional[float] = 5):
    session = requests_cache.CachedSession(
        "requests_cache",
        backend="sqlite",
        use_cache_dir=True,
        allowable_methods=("GET", "HEAD", "POST"),
        expire_after=timedelta(days=30),
    )
    try:
        req = session.get(
            "https://rest.uniprot.org/uniprotkb/" + uniprot + ".json", timeout=timeout
        ).json()
    except (requests.ReadTimeout, requests.ConnectTimeout):
        warnings.warn(f"{uniprot}: Request timed out", stacklevel=2)
        return None
    try:
        ens_id = [
            x
            for x in req["uniProtKBCrossReferences"]
            if (x["database"] == "OpenTargets") or (x["database"] == "HPA")
        ][0]["id"]
    except (KeyError, IndexError):
        warnings.warn(f"{uniprot}: No ensembl_id from OpenTargets or HPA", stacklevel=2)
        return None
    return ens_id
