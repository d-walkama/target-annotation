"""Methods to look up ontology source ID prefixes"""


import requests
import typeguard
from typing import Union
from .utils import exceptions, retry

EBI_ONTOLOGY_URL = "https://www.ebi.ac.uk/ols4/api/ontologies?size=1000"

VALID_STATUS_CODE = 200

MAX_TRIES = 3

SECONDS_TO_WAIT = 10


@retry.Retryer(max_tries=MAX_TRIES, seconds_to_wait=SECONDS_TO_WAIT)
def request_ebi_ontology_sources(timeout: Union[float, None] = None) -> list:
    """Look up all EBI ontology IDs

    Args:
        timeout (Union[float, None], optional): timeout for request.
            Default to None.
        
    Returns:
        list: Ontology codes from EBI such as EFO, MONDO, NCIT etc.
    """
    response = requests.get(EBI_ONTOLOGY_URL, timeout=timeout)
    found_ontology_sources = _find_all_ontology_sources_in_response(response)

    return found_ontology_sources


@typeguard.typechecked
def _find_all_ontology_sources_in_response(response: requests.models.Response) -> list:
    if not _has_valid_status(response):
        raise exceptions.InvalidStatusCode(
            "EBI returned an invalid status code while looking up ontology ids"
        )

    response_list = response.json()["_embedded"]["ontologies"]

    ontologies = [x["ontologyId"] for x in response_list]
    return ontologies


@typeguard.typechecked
def _has_valid_status(response: requests.models.Response) -> bool:
    return response.status_code == VALID_STATUS_CODE
