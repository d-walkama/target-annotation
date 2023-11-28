import unittest
import sys
import os
import pandas as pd
import shutil
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from target_annotation import ExtractTable

class TestExtractTable(unittest.TestCase):
    def setUp(self) -> None:
        test_data_dir = os.path.dirname(__file__) + "/test_data/test_target_annotation"

        self.bad_annotate_db_type = 0

        self.bad_annotate_db_1 = test_data_dir + "/no_json/foo.txt"
        self.good_annotate_db = test_data_dir + "/target_annotation.json"
        self.annotate_db_no_disease = (
            test_data_dir + "/target_annotation_no_disease.json"
        )

        self.good_output_path = test_data_dir + "/table_result"

        return super().setUp()

    def test_invalid_type(self):
        with self.assertRaises(TypeCheckError):
            _ = ExtractTable(
                annotate_db=self.bad_annotate_db_type, output_path=self.good_output_path
            )

    def test_invalid_annotate_db(self):
        with self.assertRaises(ValueError):
            _ = ExtractTable(
                annotate_db=self.bad_annotate_db_1, output_path=self.good_output_path
            )

    def test_good_run(self):
        pipe = ExtractTable(
            annotate_db=self.good_annotate_db, output_path=self.good_output_path
        )

        res, _ = pipe.get_table()
        self.assertIsInstance(res, pd.DataFrame)

        pipe.export_excel()

    def test_expression_table(self):
        pipe = ExtractTable(
            annotate_db=self.good_annotate_db, output_path=self.good_output_path
        )
        res = pipe.get_expression_table()
        self.assertIsInstance(res, pd.DataFrame)

    def tearDown(self) -> None:
        if os.path.exists(self.good_output_path):
            shutil.rmtree(self.good_output_path)

        return super().tearDown()
