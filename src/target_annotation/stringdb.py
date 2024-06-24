import requests

import pandas as pd
import IPython
from IPython.display import Image
# from IPython.display import SVG, display
from IPython import get_ipython
import typeguard
from typing import Union
from .utils import retry, exceptions

VALID_STATUS_CODE = 200

string_api_url = "https://version-12-0.string-db.org/api"


@typeguard.typechecked
def get_interactions(
    gene: str,
    net_type: str = "physical",
    required_score: int = 400,
    limit: int = 10,
    **retry_kwargs,
) -> pd.DataFrame:
    """Returns top interactions for specific gene

    Args:
        gene (str): gene name, protein name, or stringdb id
        net_type (str, optional): "functional" or "physical". Defaults to "physical".
        required_score (int, optional): required score. Defaults to 400.
        limit (int, optional): number of nodes to add to network. Defaults to 5.

    Returns:
        pd.DataFrame: top interactions for gene.
        see https://string-db.org/help/api/#getting-all-the-string-interaction-partners-of-the-protein-set for more info.
    """

    method = "interaction_partners"
    output_format = "json"

    params = {
        "identifiers": gene,  # your protein list
        "species": 9606,  # species NCBI identifier
        "network_type": net_type,
        "limit": limit,
        "required_score": required_score,
        "caller_identity": "Aitia",
    }
    request_url = "/".join([string_api_url, output_format, method])

    @retry.Retryer(**retry_kwargs)
    def make_response():
        response = requests.post(request_url, data=params, timeout=None)
        if not _has_valid_status(response):
            raise exceptions.InvalidStatusCode(
                f"Bad status code with response result\n{response.json()}"
            )
        return response.json()

    return pd.DataFrame.from_dict(make_response())


@typeguard.typechecked
def get_network(
    genes: list,
    net_type: str = "physical",
    required_score: int = 400,
    limit: int = 10,
    **retry_kwargs,
) -> pd.DataFrame:
    """Returns top interactions for specific genes

    Args:
        genes (list): list of gene names, protein names, or stringdb ids
        net_type (str, optional): "functional" or "physical". Defaults to "physical".
        required_score (int, optional): required score. Defaults to 400.
        limit (int, optional): number of nodes to add to network. Defaults to 5.

    Returns:
        pd.Dataframe: top interactions for gene.
        see https://string-db.org/help/api/#getting-all-the-string-interaction-partners-of-the-protein-set for more info.
    """

    method = "network"
    output_format = "json"

    params = {
        "identifiers": "%0d".join(genes),  # your protein list
        "species": 9606,  # species NCBI identifier
        "network_type": net_type,
        "required_score": required_score,
        "add_nodes": limit,
        "caller_identity": "Aitia",
    }
    request_url = "/".join([string_api_url, output_format, method])

    @retry.Retryer(**retry_kwargs)
    def make_response():
        response = requests.post(request_url, data=params, timeout=None)
        if not _has_valid_status(response):
            raise exceptions.InvalidStatusCode(
                f"Bad status code with response result\n{response.json()}"
            )
        return response.json()

    return pd.DataFrame.from_dict(make_response())


@typeguard.typechecked
def get_network_plot(
    genes: Union[str, list],
    net_type: str = "physical",
    network_flavor: str = "evidence",
    required_score: int = 400,
    limit: int = 10,
    display_image: bool = True,
    **retry_kwargs,
) -> Union[IPython.core.display.Image, bytes]:
    """Returns top interactions for specific gene

    Args:
        genes (Union[str, list]): gene name, protein name, or stringdb id (or list)
        net_type (str, optional): "functional" or "physical". Defaults to "physical".
        network_flavor (str, optional): "evidence", "confidence", or "actions". Defaults to "evidence".
        required_score (int, optional): required score. Defaults to 400.
        limit (int, optional): number of nodes to add to network. Defaults to 5.


    Returns:
        bytes: svg image as bytes.
        see https://string-db.org/help/api/#getting-all-the-string-interaction-partners-of-the-protein-set for more info.
    """

    output_format = "highres_image"
    method = "network"

    if isinstance(genes, str):
        genes = [genes]

    params = {
        "identifiers": "%0d".join(genes),  # your protein list
        "species": 9606,  # species NCBI identifier
        "network_type": net_type,
        "network_flavor": network_flavor,
        "add_color_nodes": limit,
        "required_score": required_score,
        "caller_identity": "Aitia",
    }
    request_url = "/".join([string_api_url, output_format, method])

    @retry.Retryer(**retry_kwargs)
    def make_response():
        response = requests.post(request_url, data=params, timeout=None)
        if not _has_valid_status(response):
            raise exceptions.InvalidStatusCode(
                f"Bad status code with response result\n{response.content}"
            )
        return response.content

    if (get_ipython().__class__.__name__ == "ZMQInteractiveShell") and display_image:
        return Image(make_response())
    return make_response()


@typeguard.typechecked
def _has_valid_status(response: requests.models.Response) -> bool:
    return response.status_code == VALID_STATUS_CODE
