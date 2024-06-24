import unittest
import contextlib
import json
import requests
import sys
import os
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from target_annotation import open_targets
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
        self.disease_id = "EFO_0001378"  # Multiple Myeloma
        self.ensemble_id = "ENSG00000149554"  # CHEK1

        self.bad_ensemble_id_numbers = "ENSG01234567910"  # check empty response

        self.bad_disease_id_numbers = "EFO_9999999"

        self.all_bad_disease_ids_tags = [
            "\n",
            "",
            self.disease_id + "\n",
            self.disease_id + "$#@",
            "#@$" + self.disease_id,
            "1234567",
            self.disease_id.replace("_", ""),
            self.disease_id.replace("_", "__"),
            self.disease_id + "_",
        ]  # check if disease id has a valid identifier

        self.all_bad_ens_ids = [
            self.ensemble_id.replace("ENS", ""),
            self.ensemble_id.replace("ENS", "ENS#"),
            "#@$" + self.ensemble_id,
            self.ensemble_id[:-1],
            self.ensemble_id + "0",
        ]  # check ensemble id has the correct ENS tag and number of digits

        self.all_valid_disease_ids = [
            "MONDO_0004992",  # All cancer
            "EFO_0001663",  # Prostate cancer
            "NCIT_C165465",  # Skin verrucous carcinoma
            "CVDO_0000092",  # Atrial fibrillation
        ]

        self.all_valid_ens_ids = [
            "ENSG00000119969",  # HELLS
            "ENSG00000089685",  # BIRC5
            "ENSG00000012048",  # BRCA1
            "ENSG00000171791",  # BCL2
        ]

        self.open_targets_bounds = (1, 100, 10000)
        self.open_targets_outside_bounds = (-1, 10001, 100000)

        test_data_dir = os.path.dirname(__file__) + "/test_data"

        target_annotation_file = "%s/%s_target_annotation.json" % (
            test_data_dir,
            self.ensemble_id,
        )
        self.target_annotation = open_json(target_annotation_file)

        assoc_targets_file = "%s/%s_associated_targets.json" % (
            test_data_dir,
            self.disease_id,
        )
        self.associated_targets = open_json(assoc_targets_file)

        self.datasource_ids = "europepmc"
        self.datasource_ids_list = ["europepmc"]

        target_evidence_file = "{0}/{1}_target_evidence_size_{2}.json"
        self.all_target_evidences = {
            size: open_json(
                target_evidence_file.format(test_data_dir, self.disease_id, size)
            )
            for size in range(1, 3)
        }

        self.good_response = GoodStatus()
        self.bad_response = BadStatus()

    def test_request_ot_target_annotation(self):
        """Test target_disease_evidences request from open targets"""

        for invalid_obj_type in [1, [], {}, None]:
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_target_annotation(invalid_obj_type)

        with self.assertRaises(exceptions.EmptyOpenTargetsResponse):
            open_targets.request_ot_target_annotation(self.bad_ensemble_id_numbers)

        for ens_id in self.all_bad_ens_ids:
            with self.assertRaises(exceptions.InvalidEnsembleId):
                open_targets.request_ot_target_annotation(ens_id)

        results = open_targets.request_ot_target_annotation(self.ensemble_id)
        self.assertIsInstance(results, dict)

    def test_request_ot_associated_targets(self):
        """Test associated_targets request from open targets"""

        for invalid_obj_type in [1, [], {}, None]:
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_associated_targets(invalid_obj_type)

        with self.assertRaises(exceptions.EmptyOpenTargetsResponse):
            open_targets.request_ot_associated_targets(self.bad_disease_id_numbers)

        for disease_id in self.all_bad_disease_ids_tags:
            with self.assertRaises(exceptions.InvalidDiseaseID):
                open_targets.request_ot_associated_targets(disease_id)

        results = open_targets.request_ot_associated_targets(self.disease_id)
        self.assertIsInstance(results, dict)

    def test_request_ot_target_disease_evidences(self):
        """Test target_disease_evidences request from open targets"""

        for invalid_obj_type in [1, [], {}, None]:
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_target_disease_evidences(
                    invalid_obj_type, self.ensemble_id, size=self.open_targets_bounds[0]
                )
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_target_disease_evidences(
                    self.disease_id, invalid_obj_type, size=self.open_targets_bounds[0]
                )

        for invalid_obj_type in [1, {}, None]:
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_target_disease_evidences(
                    self.disease_id,
                    self.ensemble_id,
                    datasource_ids=invalid_obj_type,
                    size=self.open_targets_bounds[0],
                )

        for invalid_obj_type in ["", [], {}, None]:
            with self.assertRaises(TypeCheckError):
                open_targets.request_ot_target_disease_evidences(
                    self.disease_id, self.ensemble_id, size=invalid_obj_type
                )

        for bound in self.open_targets_outside_bounds:
            with self.assertRaises(exceptions.InvalidQueryParameter):
                open_targets.request_ot_target_disease_evidences(
                    self.disease_id, self.ensemble_id, size=bound
                )

        with self.assertRaises(exceptions.EmptyOpenTargetsResponse):
            open_targets.request_ot_target_disease_evidences(
                self.bad_disease_id_numbers,
                self.ensemble_id,
            )
            open_targets.request_ot_target_disease_evidences(
                self.disease_id,
                self.bad_ensemble_id_numbers,
            )

        for disease_id in self.all_bad_disease_ids_tags:
            with self.assertRaises(exceptions.InvalidDiseaseID):
                open_targets.request_ot_target_disease_evidences(
                    disease_id, self.ensemble_id
                )

        for ens_id in self.all_bad_ens_ids:
            with self.assertRaises(exceptions.InvalidEnsembleId):
                open_targets.request_ot_target_disease_evidences(self.disease_id, ens_id)

        results = open_targets.request_ot_target_disease_evidences(
            self.disease_id,
            self.ensemble_id,
            datasource_ids=self.datasource_ids,
            size=self.open_targets_bounds[2],
        )
        self.assertIsInstance(results, dict)

    def test_request_open_targets(self):
        """Test generic request made to open targets"""
        with self.assertRaises(exceptions.InvalidStatusCode):
            with contextlib.redirect_stdout(None):
                open_targets.request_open_targets(
                    query="", variables={}, max_tries=1, seconds_to_wait=0.001
                )

        with self.assertRaises(TypeCheckError):
            with contextlib.redirect_stdout(None):
                open_targets.request_open_targets(query="", variables=[])
