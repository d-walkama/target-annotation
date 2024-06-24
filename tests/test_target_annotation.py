import unittest
import os
import sys
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from target_annotation import TargetAnnotation
from target_annotation.utils.exceptions import InvalidDiseaseID


class TestTargetAnnotation(unittest.TestCase):
    """Unit test class for sim cleanup"""

    def setUp(self):
        self.test_data_dir = os.path.dirname(__file__) + "/test_data"

        self.good_target = "ENSG00000001167"
        self.bad_target = "foo"
        self.bad_target_ensg = "ENSG00000000000"
        self.bad_target_type = 0

        self.good_disease_code = "MONDO_0004975"
        self.bad_disease_code = "foo"
        self.bad_disease_code_2 = "MONDO_0000000"

        self.good_results_path = self.test_data_dir

    def test_invalid_inputs(self):
        with self.assertRaises(TypeCheckError):
            _ = TargetAnnotation(
                targets=self.bad_target_type,
                disease_code=self.good_disease_code,
                results_path=self.good_results_path,
            )

    def test_invalid_targets(self):
        with self.assertRaises(ValueError):
            _ = TargetAnnotation(
                disease_code=self.good_disease_code,
                results_path=self.good_results_path,
                targets=self.bad_target,
            )

    def test_nomatch_ensg_code(self):
        pipe = TargetAnnotation(
            targets=self.bad_target_ensg,
            disease_code=self.good_disease_code,
            results_path=self.good_results_path,
        )
        pipe.run()

    def test_invalid_disease_code(self):
        with self.assertRaises(InvalidDiseaseID):
            pipe = TargetAnnotation(
                targets=self.good_target,
                disease_code=self.bad_disease_code,
                results_path=self.good_results_path,
            )
            pipe.run()

    def test_nomatch_disease_code(self):
        pipe = TargetAnnotation(
            targets=self.good_target,
            disease_code=self.bad_disease_code_2,
            results_path=self.good_results_path,
        )
        pipe.run()

    def test_class_type(self):
        pipe = TargetAnnotation(
            targets=self.good_target,
            disease_code=self.good_disease_code,
            results_path=self.good_results_path,
        )
        self.assertIsInstance(pipe, TargetAnnotation)

    def test_full_class(self):
        pipe = TargetAnnotation(
            targets=self.good_target,
            disease_code=self.good_disease_code,
            results_path=self.good_results_path,
        )
        res = pipe.run()

        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), 1)
        self.assertEqual(list(res.keys())[0], self.good_target)

    def test_export(self):
        pipe = TargetAnnotation(
            targets=self.good_target,
            disease_code=self.good_disease_code,
            results_path=self.good_results_path,
        )
        _ = pipe.run()
        pipe.export()

        self.assertTrue(
            os.path.exists(self.good_results_path + "/target_annotation.json")
        )

    def tearDown(self):
        if os.path.exists(self.good_results_path + "/target_annotation.json"):
            os.remove(self.good_results_path + "/target_annotation.json")
