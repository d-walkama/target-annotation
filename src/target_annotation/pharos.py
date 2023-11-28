import requests
import requests_cache

from .utils import retry, exceptions

import typeguard
import re
from datetime import timedelta

BASE_URL = "https://pharos-api.ncats.io/graphql"

VALID_STATUS_CODE = 200

TARGET_ANNOTATION = """
query targetDetails($ensemblId: String!){
  target(q:{stringid: $ensemblId}) {
    name
    preferredSymbol
    tdl
    fam
    sym
    description
    novelty
    pantherClasses {
      name
      pcid
    }
    dto {
      name
      dtoid
    }
    gwas {
      gwasid
      pvalue
      snps {
        name
        value
      }
      trait
    }
    gwasAnalytics {
      associations {
        meanRankScore
        diseaseName
        trait
        efoID
      }
    }
    pathways {
      name
      pwid
      targetCounts {
        name
        value
      }
      type
    }
    diseaseCounts {
      name
      value
    }
    diseases {
      name
      associationCount
      directAssociationCount
      mondoID
      datasource_count
      associations {
        disassid
        type
        name
        did
        evidence
        score
        source
      }
    }
    tissueSpecificity {
      name
      value
    }
    gtex {
      log2foldchange
      tissue
      tpm
    }
    ppis {
      nid
      props {
        name
        value
      }
      type
      target {
        preferredSymbol
      }
    }
    tinx{
      novelty
      score
      disease {
        name
        doid
      }
    }
  }
}
"""


@typeguard.typechecked
def request_pharos_target_annotation(ensembl_id: str, **kwargs) -> dict:
    """Find target annotations
    Query constructed from
    https://pharos.nih.gov/api

    Args:
        ensemble_id (str): ensemble ID such as ENSG00000149554
        **kwargs: extra parameters passed to analysis_functions.retry.Retryer

    Returns:
        dict: dictionary of target data from Pharos
    """
    if not _has_valid_ensemble_id(ensembl_id):
        raise exceptions.InvalidEnsembleId(
            f"""
            {ensembl_id} is an invalid ensemble ID. Please specify an ID with an
            appropriate ENSG prefix followed by 11 digits. Please see
            https://www.genecards.org to look up your ensemble ID.
            """
        )

    variables = {"ensemblId": ensembl_id}
    results = request_pharos(TARGET_ANNOTATION, variables, **kwargs)
    results = results.get("target", {})

    if results is None:
        raise exceptions.EmptyPharosResponse(
            f"""
            Returned empty response with {ensembl_id}. Possible reason is an invalid
            ensemble ID. Please specify an ID with an appropriate ENSG prefix followed
            by 11 digits Please see https://www.genecards.org to look up your ensemble
            ID.
            """
        )
    return results


@typeguard.typechecked
def request_pharos(query: str, variables: dict, **retry_kwargs) -> dict:
    """Generic functions for submitting queries to Pharos
    https://pharos.nih.gov/api

    Args:
        query (str): Pharos query
        variables (dict): variables to substitute into query

    Returns:
        dict: response from Pharos API
    """
    session = requests_cache.CachedSession(
        "requests_cache",
        backend="sqlite",
        use_cache_dir=True,
        allowable_methods=("GET", "HEAD", "POST"),
        expire_after=timedelta(days=30),
    )

    @retry.Retryer(**retry_kwargs)
    def make_response():
        response = session.post(
            BASE_URL, json={"query": query, "variables": variables}, timeout=None
        )
        if not _has_valid_status(response):
            raise exceptions.InvalidStatusCode(
                f"Bad status code with response result\n{response.json()}"
            )
        return response.json().get("data", {})

    return make_response()


@typeguard.typechecked
def _has_valid_ensemble_id(ensemble_id: str) -> bool:
    ensemble_digits = _extract_digits_from_string(ensemble_id)
    is_ensemble_prefix = re.match("^ENSG", ensemble_id)
    return is_ensemble_prefix is not None and len(ensemble_digits) == 11


@typeguard.typechecked
def _extract_digits_from_string(string: str) -> str:
    return re.sub("[^0-9]", "", string)


@typeguard.typechecked
def _has_valid_status(response: requests.models.Response) -> bool:
    return response.status_code == VALID_STATUS_CODE
