import unittest
import contextlib
import json
import requests
import sys
import os
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from target_annotation import pharos
from target_annotation.utils import exceptions


class GoodStatus(requests.models.Response):
    """Mock requests reponse type with a status code fixed to 200"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = 200


class BadStatus(requests.models.Response):
    """Mock requests reponse type with a status code fixed to 400"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = 400


def open_json(file_path):
    with open(file_path, "r", encoding="UTF-8") as file:
        contents = json.load(file)
    return contents


class TestOpenTargets(unittest.TestCase):
    """Unit test class for open targets"""

    def setUp(self):
        self.ensemble_id = "ENSG00000149554"  # CHEK1

        self.bad_ensemble_id_numbers = "ENSG01234567910"  # check empty response

        self.all_bad_ens_ids = [
            self.ensemble_id.replace("ENS", ""),
            self.ensemble_id.replace("ENS", "ENS#"),
            "#@$" + self.ensemble_id,
            self.ensemble_id[:-1],
            self.ensemble_id + "0",
        ]  # check ensemble id has the correct ENS tag and number of digits

        self.all_valid_ens_ids = [
            "ENSG00000119969",  # HELLS
            "ENSG00000089685",  # BIRC5
            "ENSG00000012048",  # BRCA1
            "ENSG00000171791",  # BCL2
        ]

        self.good_response = GoodStatus()
        self.bad_response = BadStatus()

    def test_request_pharos_target_annotation(self):
        """Test target_disease_evidences request from open targets"""

        for invalid_obj_type in [1, [], {}, None]:
            with self.assertRaises(TypeCheckError):
                pharos.request_pharos_target_annotation(invalid_obj_type)

        with self.assertRaises(exceptions.EmptyPharosResponse):
            pharos.request_pharos_target_annotation(self.bad_ensemble_id_numbers)

        for ens_id in self.all_bad_ens_ids:
            with self.assertRaises(exceptions.InvalidEnsembleId):
                pharos.request_pharos_target_annotation(ens_id)

        results = pharos.request_pharos_target_annotation(self.ensemble_id)
        self.assertIsInstance(results, dict)

    def test_request_pharos(self):
        """Test generic request made to open targets"""
        with self.assertRaises(exceptions.InvalidStatusCode):
            with contextlib.redirect_stdout(None):
                pharos.request_pharos(
                    query="", variables={}, max_tries=1, seconds_to_wait=0.001
                )

        with self.assertRaises(TypeCheckError):
            with contextlib.redirect_stdout(None):
                pharos.request_pharos(query="", variables=[])
