import unittest
import requests
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from target_annotation import ontology_source
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


class TestOntologySource(unittest.TestCase):
    """Unit test class for ontology source module"""

    def setUp(self):
        self.ontology_source_min_count = 10

        self.example_ontology_ids = ["efo", "mondo", "ncit"]

        self.good_response = GoodStatus()
        self.bad_response = BadStatus()

    def test_request_ebi_ontology_source(self):
        """Test request for ebi ontoloy sources"""
        ontology_sources = ontology_source.request_ebi_ontology_sources()

        self.assertTrue(len(ontology_sources) > self.ontology_source_min_count)

        self.assertTrue(
            set(ontology_sources).issuperset(set(self.example_ontology_ids))
        )

        with self.assertRaises(exceptions.InvalidStatusCode):
            ontology_source._find_all_ontology_sources_in_response(  # pylint: disable=W0212
                self.bad_response
            )
