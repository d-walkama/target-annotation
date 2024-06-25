"""
Module containing a target annotation and simulation cleanup pipeline.

Creates annotations from OpenTarget and Pharos for a list of targets.
"""
import json
import os
from typing import Union, List
from typeguard import typechecked, TypeCheckError
from tqdm import tqdm
import re

from . import open_targets as ot
from . import pharos
from .utils.exceptions import EmptyOpenTargetsResponse, EmptyPharosResponse


@typechecked
class TargetAnnotation:
    """Class for conducting target annotation"""

    def __init__(
        self,
        targets: Union[List[str], str],
        disease_code: str,
        results_path: str,
    ):
        """Initialize Class

        Args:
            targets (Union[List[str], str, None]): which targets to consider.
            disease_code (str): A disease code such as "EFO_0001378".
                https://www.ebi.ac.uk/ols/ontologie/efo.
            results_path (str): path for where results JSON should be saved.

        """

        self.targets = [targets] if isinstance(targets, str) else targets
        self.disease_code = disease_code
        self.results_path = os.path.expanduser(results_path)

        if not all(re.match("ENSG[0-9]{11}$", x) for x in self.targets):
            raise ValueError("targets must be a list of valid ensembl ids")

        if not os.path.isdir(self.results_path):
            os.makedirs(self.results_path)

    def __get_target_open_targets(self):
        if not hasattr(self, "ot_target_results"):
            ot_target_results = {}
            for ensg in tqdm(self.targets, "OT: target annotation..."):
                try:
                    ot_target_results[ensg] = ot.request_ot_target_annotation(ensg)
                except (EmptyOpenTargetsResponse, TypeCheckError):
                    ot_target_results[ensg] = {}
            self.ot_target_results = ot_target_results
        return self.ot_target_results

    def __get_target_pharos(self):
        if not hasattr(self, "pharos_target_results"):
            pharos_target_results = {}
            for ensg in tqdm(self.targets, "Pharos: target annotation..."):
                try:
                    pharos_target_results[
                        ensg
                    ] = pharos.request_pharos_target_annotation(ensg)
                except (EmptyPharosResponse, TypeCheckError):
                    pharos_target_results[ensg] = {}
            self.pharos_target_results = pharos_target_results
        return self.pharos_target_results

    def __get_disease_open_targets(self):
        if not hasattr(self, "ot_disease_results"):
            ot_disease_results = {}
            for ensg in tqdm(self.targets, "OT: disease annotation..."):
                try:
                    ot_disease_results[ensg] = ot.request_ot_target_disease_evidences(
                        self.disease_code, ensg
                    )
                except (EmptyOpenTargetsResponse, TypeCheckError):
                    ot_disease_results[ensg] = {}
            self.ot_disease_results = ot_disease_results
        return self.ot_disease_results

    def __add_target_labels(self):
        self.__get_target_open_targets()
        self.__get_disease_open_targets()
        self.__get_target_pharos()

        if not hasattr(self, "res_by_driver"):
            self.res_by_driver = {u: {} for u in self.targets}

        for key, value in self.res_by_driver.items():
            if key in self.ot_target_results:
                value["OpenTargets"] = self.ot_target_results[key]
            if key in self.ot_disease_results:
                value["OpenTargets_disease_evidence"] = self.ot_disease_results[key]
            if key in self.pharos_target_results:
                value["Pharos"] = self.pharos_target_results[key]

        return self.res_by_driver

    def run(self) -> dict:
        """Run the pipeline

        Returns:
            dict: annotations by driver.
        """
        _ = self.__add_target_labels()

        return self.res_by_driver

    def export(self):
        """Export results to file target_annotation.json"""
        res = self.run()
        with open(
            self.results_path + "/target_annotation.json",
            "w",
            encoding="UTF-8",
        ) as file:
            json.dump(res, file)
