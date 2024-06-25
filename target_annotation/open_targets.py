"""
Methods to look up Open Targets records. Options currently supported are:

1. Target annotation
2. Associated targets to disease
3. Disease - Target evidence
"""


import requests
import requests_cache
from .utils import retry, exceptions
import typing
import typeguard
import re
from datetime import timedelta


BASE_URL = "https://api.platform.opentargets.org/api/v4/graphql"

OPEN_TARGETS_SIZE_BOUNDS = (1, 10000)

VALID_STATUS_CODE = 200

VALID_DISEASE_ID_PATTERNS = r"[A-Za-z0-9_]"


TARGET_ANNOTATION = """
query target($ensemblId: String!){
    target(ensemblId: $ensemblId){
        id
        approvedSymbol
        biotype
        proteinIds{
            id
    	    source
        }
        geneOntology{
            aspect
            evidence
            geneProduct
            source
            term{
                id
                name
            }
        }
        targetClass{
            id
            label
            level
        }
        functionDescriptions
        tractability {
            modality
            label
            value
        }
        geneticConstraint {
            constraintType
            exp
            obs
            score
            oe
            oeLower
            oeUpper
        }
        pathways{
            pathway
            topLevelTerm
        }
        expressions{
            tissue{
                label
            }
            rna{
                value
            }
        }
        associatedDiseases{
            rows{
                score
                disease{
                    id
                    name
                }
            }
        }
        isEssential
        depMapEssentiality{
            tissueId
            tissueName
            screens{
                cellLineName
                depmapId
                diseaseCellLineId
                diseaseFromSource
                expression
                geneEffect
                mutation
            }
        }
        chemicalProbes{
            id
            drugId
        }
        knownDrugs{
			rows{
                prefName
                label
                drugType
                disease{
                    id
                    name
                }
            }
        }
        safetyLiabilities {
            event
            eventId
            biosamples {
                cellFormat
                cellLabel
                tissueLabel
                tissueId
            }
            effects {
                dosing
                direction
            }
            studies {
                name
                type
                description
            }
            datasource
            literature
        }
    }
}
"""

ASSOCIATED_TARGETS_QUERY = """
query associatedTargets($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets {
      count
      rows {
        target {
          id
          approvedSymbol
        }
        score
      }
    }
  }
}
"""


TARGET_DISEASE_EVIDENCE_QUERY = """
query targetDiseaseEvidence($efoId: String!, $ensemblIds: [String!]!,
                            $datasourceIds: [String!]!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    evidences(datasourceIds: $datasourceIds, ensemblIds:
              $ensemblIds, size: $size) {
      count
      rows {
        disease {
            id
            name
        }
        target {
            id
            approvedSymbol
        }
        urls{
          url
          niceName
        }
        diseaseFromSource
        literature
        publicationYear
        datasourceId
        datatypeId
        score
        resourceScore
        textMiningSentences{
            section
            text
        }
        significantDriverMethods
        cohortId
        cohortShortName
        cohortDescription
        mutatedSamples {
            functionalConsequence {
                id
                label
            }
            numberSamplesTested
                numberMutatedSamples
            }
      }
    }
  }
}
"""


@typeguard.typechecked
def request_ot_target_annotation(ensembl_id: str, **kwargs) -> dict:
    """Find target annotations
    Query constructed from
    https://api.platform.opentargets.org/api/v4/graphql/browser

    Args:
        ensemble_id (str): ensemble ID such as ENSG00000149554
        **kwargs: extra parameters passed to analysis_functions.retry.Retryer

    Returns:
        dict: dictionary of target data from open targets
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
    results = request_open_targets(TARGET_ANNOTATION, variables, **kwargs)
    results = results.get("target", {})

    if results is None:
        raise exceptions.EmptyOpenTargetsResponse(
            f"""
            Returned empty response with {ensembl_id}. Possible reason is an invalid
            ensemble ID. Please specify an ID with an appropriate ENSG prefix followed
            by 11 digits Please see https://www.genecards.org to look up your ensemble
            ID.
            """
        )
    return results


@typeguard.typechecked
def request_ot_associated_targets(efo_id: str, **kwargs) -> dict:
    """Find targets associated with a disease
    Query constructed from
    https://api.platform.opentargets.org/api/v4/graphql/browser

    Args:
        efo_id (str): disease ID such as EFO_0001378
        **kwargs: extra parameters passed to analysis_functions.retry.Retryer

    Returns:
        dict: dictionary of disease data from open targets.
    """
    if not _has_valid_disease_id(efo_id):
        raise exceptions.InvalidDiseaseID(
            f"""
            {efo_id} is an invalid disease ID. Please specify an ID with an appropriate
            ontology prefix such as EFO, MONDO, etc. followed by _#######. Please see
            https://www.ebi.ac.uk/efo/ to look up your disease identifier.
            """
        )

    variables = {"efoId": efo_id}
    results = request_open_targets(ASSOCIATED_TARGETS_QUERY, variables, **kwargs)
    results = results.get("disease", {})

    if results is None:
        raise exceptions.EmptyOpenTargetsResponse(
            f"""
            Returned empty response with {efo_id}. Possible reason is an invalid disease
            ID. Please specify an ID with an appropriate ontology prefix such as EFO,
            MONDO, etc. followed by _#######. Please see https://www.ebi.ac.uk/efo/ to
            look up your disease identifier.
            """
        )
    return results


@typeguard.typechecked
def request_ot_target_disease_evidences(
    efo_id: str,
    ensembl_id: str,
    datasource_ids: typing.Union[list, str] = "europepmc",
    size: int = 10000,
    **kwargs,
) -> dict:
    """Find Target-Disease Evidences from Open Targets
    Query constructed from
    https://api.platform.opentargets.org/api/v4/graphql/browser


    Args:
        efo_id (str): disease ID such as EFO_0001378
        ensemble_id (str): ensemble ID such as ENSG00000149554
        datasource_ids (list, str): let open targets know what datasource to use.
            Defaults to "europepmc".
        size (int): number of evidences returned from open targets.
            Must be between 1 and 10000. Defaults to 10000
        **kwargs: extra parameters passed to analysis_functions.retry.Retryer

    Returns:
        dict: dictionary of disease data and target evidences from open targets.
    """
    if not _has_valid_disease_id(efo_id):
        raise exceptions.InvalidDiseaseID(
            f"""
            {efo_id} is an invalid disease ID. Please specify an ID with an appropriate
            ontology prefix such as EFO, MONDO, etc. followed by _#######. Please see
            https://www.ebi.ac.uk/efo/ to look up your disease identifier.
            """
        )
    if not _has_valid_ensemble_id(ensembl_id):
        raise exceptions.InvalidEnsembleId(
            f"""
            {ensembl_id} is an invalid ensemble ID. Please specify an ID with an
            appropriate ENSG prefix followed by 11 digits. Please see
            https://www.genecards.org to look up your ensemble ID.
            """
        )
    if not _has_valid_size_param(size):
        raise exceptions.InvalidQueryParameter(
            f"size parameter must be within {OPEN_TARGETS_SIZE_BOUNDS}"
        )

    variables = {
        "efoId": efo_id,
        "ensemblIds": [ensembl_id],
        "datasourceIds": (
            datasource_ids if isinstance(datasource_ids, list) else [datasource_ids]
        ),
        "size": size,
    }
    results = request_open_targets(TARGET_DISEASE_EVIDENCE_QUERY, variables, **kwargs)
    results = results.get("disease", {})

    if results is None:
        raise exceptions.EmptyOpenTargetsResponse(
            f"""
            Returned empty response with {(efo_id, ensembl_id)}. Possible reason is an
            invalid ensemble ID or disease ID. Please specify an ID with an appropriate
            ENSG prefix followed by 11 digits Please see https://www.genecards.org to
            look up your ensemble ID. Please specify an ID with an appropriate ontology
            prefix such as EFO, MONDO, etc. followed by _#######. Please see
            https://www.ebi.ac.uk/efo/ to look up your disease identifier.
            """
        )
    return results


@typeguard.typechecked
def request_open_targets(query: str, variables: dict, **retry_kwargs) -> dict:
    """Generic functions for submitting queries to OpenTargets
    https://api.platform.opentargets.org/api/v4/graphql/browser

    Args:
        query (str): OpenTarget query
        variables (dict): variables to substitute into query

    Returns:
        dict: response from OpenTargets API
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
def _has_valid_disease_id(disease_id: str) -> bool:
    matched_patterns = re.findall(VALID_DISEASE_ID_PATTERNS, disease_id)
    contains_one_underscore = re.findall("_", disease_id)
    return (
        not disease_id.isdigit()
        and disease_id != ""
        and matched_patterns == list(disease_id)
        and len(contains_one_underscore) == 1
    )


@typeguard.typechecked
def _has_valid_ensemble_id(ensemble_id: str) -> bool:
    ensemble_digits = _extract_digits_from_string(ensemble_id)
    is_ensemble_prefix = re.match("^ENSG", ensemble_id)
    return is_ensemble_prefix is not None and len(ensemble_digits) == 11


@typeguard.typechecked
def _extract_digits_from_string(string: str) -> str:
    return re.sub("[^0-9]", "", string)


@typeguard.typechecked
def _has_valid_size_param(size: int) -> bool:
    min_size, max_size = OPEN_TARGETS_SIZE_BOUNDS
    return min_size <= size <= max_size


@typeguard.typechecked
def _has_valid_status(response: requests.models.Response) -> bool:
    return response.status_code == VALID_STATUS_CODE
