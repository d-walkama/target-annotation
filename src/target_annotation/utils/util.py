"""Utility functions for analysis-functions package
"""
import requests
import requests_cache
import warnings
import pandas as pd
from typeguard import typechecked
from typing import Union, Optional, List
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


@typechecked
def check_var_in_data(data_path: str, var_name: Union[str, List[str]]):
    data_subset = pd.read_csv(data_path, nrows=1)

    if isinstance(var_name, list):
        res = [x in data_subset.columns for x in var_name]
        return all(res)
    else:
        res = var_name in data_subset.columns
        return res


@typechecked
def get_columns_from_regex_list(df: pd.DataFrame, regex_list=Union[str, List[str]]):
    if isinstance(regex_list, str):
        regex_list = [regex_list]
    temp = [df.columns.str.contains(x) for x in regex_list]
    cols_to_keep = [any(column) for column in zip(*temp)]
    res = df.columns[cols_to_keep]
    return res
