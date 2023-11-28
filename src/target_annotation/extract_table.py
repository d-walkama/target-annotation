"""ExtractTables module
"""
import json
import os
import pandas as pd
from typeguard import typechecked
import copy
import warnings
from collections import Counter

@typechecked
class ExtractTable:
    """Generate target summary table from sim results and target annotations"""

    def __init__(
        self,
        annotate_db: str,
        output_path: str,
        top_expression_count: int = 3,
    ) -> None:
        """
        Args:
            annotate_db (str): json database from TargetAnnotation workflow
            output_path (str): where to save summary table
            top_expression_count (int, optional): number of top cell lines to keep
                expression data from. Defaults to 3.

        Raises:
            ValueError: "'annotate_db' must be a json file"
        """
        self.annotate_db = os.path.expanduser(annotate_db)
        self.output_path = os.path.expanduser(output_path)

        self.top_expression_count = top_expression_count

        if not self.annotate_db.split(".")[-1] == "json":
            raise ValueError("'annotate_db' must be a json file")
        with open(self.annotate_db, "r", encoding="UTF-8") as file:
            self.annotate_db = json.load(file)

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def __create_ref_df(self):
        temp = pd.DataFrame.from_dict(self.annotate_db, orient="index")
        self.annotate_ref_df = pd.DataFrame(index=temp.index)
        self.annotate_ref_df = self.annotate_ref_df.join(
            pd.json_normalize(temp["OpenTargets"])
            .set_index(temp.index)
            .add_prefix("OT_")
        )
        self.annotate_ref_df = self.annotate_ref_df.join(
            pd.json_normalize(temp["OpenTargets_disease_evidence"])
            .set_index(temp.index)
            .add_prefix("OT_disease_"),
        )
        self.annotate_ref_df = self.annotate_ref_df.join(
            pd.json_normalize(temp["Pharos"])
            .set_index(temp.index)
            .add_prefix("Pharos_")
        )

    def __get_basic_df(self):
        basic_cols = [
            "OT_approvedSymbol",
            "Pharos_sym",
            "Pharos_name",
            "Pharos_description",
            "OT_functionDescriptions",
            "OT_biotype",
        ]
        self.basic_df = copy.deepcopy(self.annotate_ref_df[basic_cols])
        self.basic_df.rename(
            columns={
                "OT_approvedSymbol": "ot_symbol",
                "Pharos_sym": "pharos_symbol",
                "Pharos_name": "name",
                "Pharos_description": "pharos_description",
                "OT_functionDescriptions": "ot_description",
                "OT_biotype": "biotype",
            },
            inplace=True,
        )
        self.basic_df["symbol"] = self.basic_df["ot_symbol"].combine_first(
            self.basic_df["pharos_symbol"]
        )
        self.basic_df["description"] = self.basic_df[
            "pharos_description"
        ].combine_first(
            self.basic_df["ot_description"].apply(
                lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
            )
        )
        self.basic_df.drop(
            columns=[
                "pharos_symbol",
                "ot_symbol",
                "pharos_description",
                "ot_description",
            ],
            inplace=True,
        )
        temp = self.basic_df.pop("symbol")
        self.basic_df.insert(1, "symbol", temp)
        temp = self.basic_df.pop("description")
        self.basic_df.insert(3, "description", temp)

        self.basic_df_key = pd.DataFrame(
            {
                "column": [
                    "symbol",
                    "name",
                    "description",
                    "biotype",
                ],
                "key": [
                    "preferred symbol",
                    "name (Pharos)",
                    "description (Pharos first, OT if no Pharos)",
                    "biotype (OT)",
                ],
            }
        )

    def __get_pathways(self):
        self.path_df = (
            self.annotate_ref_df["Pharos_pathways"]
            .dropna()
            .apply(lambda x: {xx["type"]: xx["name"] for xx in x})
        ).rename("pathways")
        self.path_df_key = pd.DataFrame(
            {"column": "pathways", "key": "Pathways from Pharos."},
            index=[0],
        )

    def __get_classes(self):
        self.class_df = self.annotate_ref_df["Pharos_dto"].dropna().apply(
            lambda x: ["DTO: " + xx["name"] for xx in x]
        ) + self.annotate_ref_df["Pharos_pantherClasses"].dropna().apply(
            lambda x: ["Panther: " + xx["name"] for xx in x]
        )
        self.class_df = self.class_df.rename("classes")
        self.class_df_key = pd.DataFrame(
            {"column": "classes", "key": "Panther and DTO classes from Pharos."},
            index=[0],
        )

    def __get_go_terms(self):
        self.go_df = (
            self.annotate_ref_df["OT_geneOntology"]
            .dropna()
            .apply(lambda x: {xx["term"]["id"]: xx["term"]["name"] for xx in x})
        ).rename("GO terms")
        self.go_df_key = pd.DataFrame(
            {"column": "GO terms", "key": "GO terms collected from OT."},
            index=[0],
        )

    def __get_tract_df(self):
        self.tract_df = (
            self.annotate_ref_df["OT_tractability"]
            .dropna()
            .apply(
                lambda lam: [
                    x["modality"] + ": " + x["label"]
                    for x in [x for x in lam if x["value"]]
                ]
            )
        ).rename("tractability")
        self.tract_df_key = pd.DataFrame(
            {"column": "tractability", "key": "tractability from OT."}, index=[0]
        )

    def __get_tdl(self):
        self.tdl_df = copy.deepcopy(self.annotate_ref_df["Pharos_tdl"]).rename(
            "IDG Development Level"
        )
        self.tdl_df_key = pd.DataFrame(
            {
                "column": "IDG Development Level",
                "key": (
                    "Descriptions of the IDG illumination levels,"
                    " highlighting the milestones attained in research"
                    " for this target. From Pharos."
                ),
            },
            index=[0],
        )

    def __get_dep_map_essentiality(self):
        self.essential_df = copy.deepcopy(
            self.annotate_ref_df["OT_isEssential"]
        ).rename("is_essential")
        self.essential_df_key = pd.DataFrame(
            {"column": "is_essential", "key": "is essential from DepMap"}, index=[0]
        )

    def __get_tissue_specificity(self):
        self.tissue_spec_df = (
            self.annotate_ref_df["Pharos_tissueSpecificity"]
            .dropna()
            .apply(lambda x: {xx["name"]: xx["value"] for xx in x})
            .rename("tissue specificity")
        )
        self.tissue_spec_df_key = pd.DataFrame(
            {
                "column": "tissue specificity",
                "key": "tissue specificity from Pharos.",
            },
            index=[0],
        )

    def __get_expression(self):
        self.top_expression_df = (
            self.annotate_ref_df["OT_expressions"]
            .dropna()
            .apply(lambda x: {i["tissue"]["label"]: i["rna"]["value"] for i in x})
            .apply(Counter)
            .apply(lambda x: x.most_common()[: self.top_expression_count])
            .rename("top_rna_expression")
        )
        self.top_expression_df_key = pd.DataFrame(
            {
                "column": "top_rna_expression",
                "key": "top expression from Expression Atlas in OT.",
            },
            index=[0],
        )

    def __get_chem_probes(self):
        self.chem_probes_df = (
            self.annotate_ref_df["OT_chemicalProbes"]
            .dropna()
            .apply(lambda x: len(x) > 0)
        ).rename("has_chem_probe")
        self.chem_probes_df_key = pd.DataFrame(
            {
                "column": "has_chem_probe",
                "key": "whether chemical probe exists in ChEMBL.",
            },
            index=[0],
        )

    def __get_known_drugs(self):
        self.known_drugs_df = (
            self.annotate_ref_df["OT_knownDrugs.rows"]
            .dropna()
            .apply(lambda x: len(x) > 0)
        ).rename("has_known_drug")
        self.known_drugs_df_key = pd.DataFrame(
            {
                "column": "has_known_drug",
                "key": "whether known drug exists for target.",
            },
            index=[0],
        )

    def __get_gwas(self):
        self.gwas_df = (
            self.annotate_ref_df["Pharos_gwas"]
            .dropna()
            .apply(lambda x: {xx["snps"][0]["value"]: xx["trait"] for xx in x})
        ).rename("gwas")
        self.gwas_df_key = pd.DataFrame(
            {
                "column": "gwas",
                "key": "GWAS catalog results: www.ebi.ac.uk/gwas",
            },
            index=[0],
        )

    def __get_gwas_analytics(self):
        self.gwas_analytics_df = (
            self.annotate_ref_df["Pharos_gwasAnalytics.associations"]
            .dropna()
            .apply(lambda x: {xx["trait"]: xx["meanRankScore"] for xx in x})
        ).rename("gwas_analytics")
        self.gwas_analytics_df_key = pd.DataFrame(
            {
                "column": "gwas_analytics",
                "key": (
                    "GWAS trait and meanRankScore."
                    " Target Illumination GWAS Analytics (TIGA) scores and ranks"
                    " those traits according to a subset of study parameters."
                    " https://unmtid-shinyapps.net/shiny/tiga/"
                ),
            },
            index=[0],
        )

    def __get_genetic_constraint(self):
        self.gen_constraint_df = (
            self.annotate_ref_df["OT_geneticConstraint"]
            .dropna()
            .apply(
                lambda x: [xx["oeUpper"] for xx in x if xx["constraintType"] == "lof"]
            )
            .apply(lambda x: x[0] if len(x) == 1 else x)
        ).rename("gnomAD_LOEUF")
        self.gen_constraint_df_key = pd.DataFrame(
            {
                "column": "gnomAD_LOEUF",
                "key": (
                    "LOEUF genetic constraint:"
                    " https://gnomad.broadinstitute.org/help/constraint"
                ),
            },
            index=[0],
        )

    def __get_associated_diseases_pharos(self):
        self.associated_diseases_pharos_df = (
            self.annotate_ref_df["Pharos_diseases"]
            .dropna()
            .apply(lambda x: {xx["name"]: xx["associationCount"] for xx in x})
        ).rename("Pharos associated diseases")
        self.associated_diseases_pharos_df_key = pd.DataFrame(
            {
                "column": "Pharos associated diseases",
                "key": "associated disease and their association count from Pharos",
            },
            index=[0],
        )

    def __get_associated_diseases_ot(self):
        self.associated_diseases_ot_df = (
            self.annotate_ref_df["OT_associatedDiseases.rows"]
            .dropna()
            .apply(lambda x: {xx["disease"]["name"]: xx["score"] for xx in x})
        ).rename("OT associated diseases")
        self.associated_diseases_ot_df_key = pd.DataFrame(
            {
                "column": "OT associated diseases",
                "key": "associated disease and their score from OT",
            },
            index=[0],
        )

    def __get_disease_association(self):
        disease_id = None
        count = 0
        while not isinstance(disease_id, str):
            if count == len(self.annotate_ref_df["OT_disease_id"]):
                self.disease_association_df = None
                self.disease_association_df_key = None
                warnings.warn(
                    "no disease code from annotation db:"
                    + " OpenTargets_disease_evidence->id",
                    stacklevel=2,
                )
                return
            disease_id = self.annotate_ref_df["OT_disease_id"].iloc[count]
            count += 1
        self.disease_association_df = (
            self.annotate_ref_df["OT_associatedDiseases.rows"]
            .dropna()
            .apply(
                lambda x: [xx["score"] for xx in x if xx["disease"]["id"] == disease_id]
            )
            .apply(lambda x: x[0] if len(x) > 0 else None)
        ).rename("disease_association_score")
        self.disease_association_df_key = pd.DataFrame(
            {
                "column": "disease_association_score",
                "key": (
                    "score of association between disease of interest"
                    " and target from OT."
                ),
            },
            index=[0],
        )

    def __get_safety_liabilities(self):
        self.safety_liabilities_df = (
            self.annotate_ref_df["OT_safetyLiabilities"]
            .dropna()
            .apply(lambda x: [xx["event"] for xx in x])
        ).rename("safety_liabilities")
        self.safety_liabilities_df_key = pd.DataFrame(
            {
                "column": "safety_liabilities",
                "key": ("safety liabilities from OT."),
            },
            index=[0],
        )

    def __get_pharos_link(self):
        self.pharos_link_df = (
            self.annotate_ref_df.index.to_series()
            .dropna()
            .apply(lambda x: "https://pharos.nih.gov/targets/" + x)
            .rename("pharos_link")
        )
        self.pharos_link_df_key = pd.DataFrame(
            {"column": "pharos_link", "key": "link to Pharos Facets for target."},
            index=[0],
        )

    def __get_lit_urls(self):
        pmid = (
            self.annotate_ref_df["OT_disease_evidences.rows"]
            .dropna()
            .apply(lambda x: [xx["literature"][0] for xx in x])
        )

        self.pmid_df = pmid.apply(
            lambda x: ["https://pubmed.ncbi.nlm.nih.gov/" + xx for xx in x]
        ).rename("related_publications")
        self.pmid_df_key = pd.DataFrame(
            {
                "column": "related_publications",
                "key": "PubMed links for publications relating target to disease",
            },
            index=[0],
        )

    def get_expression_table(self):
        """get gene expression table

        Returns:
            pd.DataFrame: expression table
        """
        if not hasattr(self, "annotate_ref_df"):
            self.__create_ref_df()
        temp = (
            self.annotate_ref_df["OT_expressions"]
            .dropna()
            .apply(lambda xx: {x["tissue"]["label"]: x["rna"]["value"] for x in xx})
        )
        self.expression_table = pd.json_normalize(temp).set_index(temp.index)
        return self.expression_table

    def get_table(self):
        """Get final targets table

        Returns:
            pd.DataFrame: final targets table
        """
        self.__create_ref_df()
        self.__get_basic_df()
        self.__get_pathways()
        self.__get_classes()
        self.__get_go_terms()
        self.__get_tract_df()
        self.__get_tdl()
        self.__get_dep_map_essentiality()
        self.__get_tissue_specificity()
        self.__get_expression()
        self.__get_chem_probes()
        self.__get_known_drugs()
        self.__get_gwas()
        self.__get_gwas_analytics()
        self.__get_genetic_constraint()
        self.__get_associated_diseases_pharos()
        self.__get_associated_diseases_ot()
        self.__get_disease_association()
        self.__get_safety_liabilities()
        self.__get_pharos_link()
        self.__get_lit_urls()

        self.final_table = pd.concat(
            [
                self.basic_df,
                self.pharos_link_df,
                self.path_df,
                self.class_df,
                self.go_df,
                self.tract_df,
                self.tdl_df,
                self.essential_df,
                self.pmid_df,
                self.tissue_spec_df,
                self.top_expression_df,
                self.chem_probes_df,
                self.known_drugs_df,
                self.gwas_df,
                self.gwas_analytics_df,
                self.gen_constraint_df,
                self.associated_diseases_pharos_df,
                self.associated_diseases_ot_df,
                self.disease_association_df,
                self.safety_liabilities_df,
            ],
            axis=1,
        )

        self.final_table_key = pd.concat(
            [
                self.basic_df_key,
                self.pharos_link_df_key,
                self.path_df_key,
                self.class_df_key,
                self.go_df_key,
                self.tract_df_key,
                self.tdl_df_key,
                self.essential_df_key,
                self.pmid_df_key,
                self.tissue_spec_df_key,
                self.top_expression_df_key,
                self.chem_probes_df_key,
                self.known_drugs_df_key,
                self.gwas_df_key,
                self.gwas_analytics_df_key,
                self.gen_constraint_df_key,
                self.associated_diseases_pharos_df_key,
                self.associated_diseases_ot_df_key,
                self.disease_association_df_key,
                self.safety_liabilities_df_key,
            ]
        )

        return self.final_table, self.final_table_key

    def export_excel(self):
        """Export excel sheet"""
        expression_table = self.get_expression_table()
        final_table, final_table_key = self.get_table()

        with pd.ExcelWriter(  # pylint: disable=abstract-class-instantiated
            self.output_path + "/target_table.xlsx"
        ) as writer:
            final_table.to_excel(writer, sheet_name="summary_table")
            final_table_key.to_excel(
                writer, sheet_name="summary_table_key", index=False
            )
            expression_table.to_excel(writer, sheet_name="expression_table")
