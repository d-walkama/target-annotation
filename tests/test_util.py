import unittest
import os
import sys
import numpy as np
import pandas as pd
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from target_annotation.utils import util


class TestUtil(unittest.TestCase):
    """Unit test class for util submodule"""

    def setUp(self):
        self.test_data_dir = os.path.dirname(__file__) + "/test_data"

        self.good_uniprot = "P78508"
        self.bad_uniprot_1 = 0
        self.bad_uniprot_2 = "Q9BYB0"
        self.bad_uniprot_3 = str(np.random.randint(0, 2**63))

        self.good_features_1 = "test_feature_1"
        self.good_features_2 = ["test_feature_1", "test_feature_2"]
        self.bad_feature = "test_feature_0"

        self.good_df = pd.DataFrame({"col1": ["foo", "bar"], "col2": ["faz", "baz"]})
        self.good_regex1 = "col1"
        self.good_regex2 = ["col1", "col2"]

    def test_get_ensembl_from_uniprot(self):
        with self.assertRaises(TypeCheckError):
            util.get_ensembl_from_uniprot(self.bad_uniprot_1)

        with self.assertWarns(Warning):
            util.get_ensembl_from_uniprot(self.bad_uniprot_2)

        res = util.get_ensembl_from_uniprot(self.good_uniprot)
        self.assertEqual(res, "ENSG00000177807")

        with self.assertWarns(Warning):
            res = util.get_ensembl_from_uniprot(self.bad_uniprot_3, timeout=10**-10)
