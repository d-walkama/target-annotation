import unittest
import json
import requests
import sys
import os
import pandas as pd
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis_functions import stringdb


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


class TestStringDB(unittest.TestCase):
    """Unit test class for open targets"""

    def setUp(self):
        self.gene = "TP53"
        self.gene_list = ["TP53", "CHEK1"]

        self.good_response = GoodStatus()
        self.bad_response = BadStatus()

    def test_get_interactions(self):
        """Test target_disease_evidences request from open targets"""

        for invalid_obj_type in [1, [], {}, None]:
            with self.assertRaises(TypeCheckError):
                stringdb.get_interactions(invalid_obj_type)

        results = stringdb.get_interactions(self.gene)
        self.assertIsInstance(results, pd.DataFrame)

    def test_get_network(self):
        """Test associated_targets request from open targets"""

        for invalid_obj_type in [1, "test", {}, None]:
            with self.assertRaises(TypeCheckError):
                stringdb.get_network(invalid_obj_type)

        results = stringdb.get_network(self.gene_list)
        self.assertIsInstance(results, pd.DataFrame)

    def test_get_network_plot(self):
        """Test target_disease_evidences request from open targets"""

        for invalid_obj_type in [1, {}, None]:
            with self.assertRaises(TypeCheckError):
                stringdb.get_network_plot(invalid_obj_type)

        results = stringdb.get_network_plot(self.gene)
        self.assertIsInstance(results, bytes)
