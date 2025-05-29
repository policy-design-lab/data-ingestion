import os
import pandas as pd

pd.options.mode.copy_on_write = True

pd.options.mode.copy_on_write = True


class DataParser:
    def __init__(self, start_year, end_year, title_name, data_folder, program_csv_filename, subtitle_name="",
                 program_name="", **kwargs):
        self.start_year = start_year
        self.end_year = end_year
        self.title_name = title_name
        self.data_folder = data_folder
        self.program_csv_filepath = os.path.join(data_folder, program_csv_filename)
        self.program_data = None
        self.us_state_abbreviations = {
            'AL': 'Alabama',
            'AK': 'Alaska',
            'AZ': 'Arizona',
            'AR': 'Arkansas',
            'CA': 'California',
            'CO': 'Colorado',
            'CT': 'Connecticut',
            'DC': 'District of Columbia',
            'DE': 'Delaware',
            'FL': 'Florida',
            'GA': 'Georgia',
            'HI': 'Hawaii',
            'ID': 'Idaho',
            'IL': 'Illinois',
            'IN': 'Indiana',
            'IA': 'Iowa',
            'KS': 'Kansas',
            'KY': 'Kentucky',
            'LA': 'Louisiana',
            'ME': 'Maine',
            'MD': 'Maryland',
            'MA': 'Massachusetts',
            'MI': 'Michigan',
            'MN': 'Minnesota',
            'MS': 'Mississippi',
            'MO': 'Missouri',
            'MT': 'Montana',
            'NE': 'Nebraska',
            'NV': 'Nevada',
            'NH': 'New Hampshire',
            'NJ': 'New Jersey',
            'NM': 'New Mexico',
            'NY': 'New York',
            'NC': 'North Carolina',
            'ND': 'North Dakota',
            'OH': 'Ohio',
            'OK': 'Oklahoma',
            'OR': 'Oregon',
            'PA': 'Pennsylvania',
            'RI': 'Rhode Island',
            'SC': 'South Carolina',
            'SD': 'South Dakota',
            'TN': 'Tennessee',
            'TX': 'Texas',
            'UT': 'Utah',
            'VT': 'Vermont',
            'VA': 'Virginia',
            'WA': 'Washington',
            'WV': 'West Virginia',
            'WI': 'Wisconsin',
            'WY': 'Wyoming'
        }
        self.metadata = {
            "Title 1: Commodities": {
                "column_names_map": {
                    "payments": "amount",
                    "count": "recipient_count",
                    "state": "state_name",
                    "State Name": "state_name",
                    "program": "entity_name"
                },
                "value_names_map": {
                    "Dairy": "Dairy Margin Coverage, Subtitle D",
                    "DMC": "Dairy Margin Coverage, Subtitle D",
                    "TAP": "Tree Assistance Program (TAP)",
                    "NAP": "Noninsured Crop Disaster Assistance Program (NAP)",
                    "LFP": "Livestock Forage Program (LFP)",
                    "LIP": "Livestock Indemnity Payments (LIP)",
                    "ELAP": "Emergency Assistance for Livestock, Honey Bees, and Farm-Raised Fish Program (ELAP)"
                }
            },
            "Title 2: Conservation": {
                "column_names_map": {
                    "Pay_year": "year",
                    "State": "state_name",
                    "state": "state_name",
                    "payments": "amount",
                    "category_name": "practice_category",
                    "StatutoryCategory": "practice_category",
                    "practice_code": "practice_code_processed",
                    "full_practice_code": "practice_code",
                    "Number of Contracts": "contract_count",
                    "Number of Acres": "base_acres",
                    "Total Financial Assistance Payments ($1000)": "amount",

                },
                "value_names_map": {
                    "CRP": "Conservation Reserve Program (CRP)",
                    "ACEP": "Agricultural Conservation Easement Program (ACEP)",
                    "RCPP": "Regional Conservation Partnership Program (RCPP)",
                    "EQIP": "Environmental Quality Incentives Program (EQIP)",
                    "CSP": "Conservation Stewardship Program (CSP)",
                    "Land management": "Land Management",
                    "Forest management": "Land Management",
                    "Soil remediation": "Soil Remediation",
                    "Other 2 - improvement": "Other Improvement",
                    "Other 1 - planning": "Other Planning",
                    "Conservating planning assessment": "Conservation Planning Assessment",
                    "Resource-conserving crop rotatation": "Resource-conserving Crop Rotation",
                    "Comprehensive Nutrient Mgt.": "Comprehensive Nutrient Management",
                    "Comprehensive Nutrient Mgt. (6(B)(i))": "Comprehensive Nutrient Management",
                    "Soil testing": "Soil Testing",
                    "Soil remediation (6(A)(vi)": "Soil Remediation",
                    "other (6(B)(vi))": "Other Planning",
                    "conservating planning assessment (6(B)Iiv))": "Conservation Planning Assessment",
                    "Resource-conserving crop rotatation (6(B)(ii)": "Resource-conserving Crop Rotation",
                    "Soil health (6(B)(iii))": "Soil Health",
                    "Soil testing (6(A)(v))": "Soil Testing",
                    "Vegetative (6(A)(iii)": "Vegetative",
                    "Structural (6(A)(i))": "Structural",
                    "Land Management (6(A)(ii))": "Land Management",
                    "Forest management (6(A)(iv))": "Forest Management",
                    "Vegetative (6(A)(iii))": "Vegetative",
                    "Soil remediation (6(A)(vi))": "Soil Remediation",
                    "Other (6(A)(vii))": "Other Improvements",
                    "NIPF": "Non-Industrial Private Forestland",
                    "Pastured Cropland": "Grassland",
                    "2014 Other Practices": "Miscellaneous",
                    "Hawaii/Pacific ": "Hawaii"  # Check with the team if this mapping is okay, else remove
                }
            },
            "Supplemental Nutrition Assistance Program (SNAP)": {
                "column_names_map": {
                    "payments": "amount",
                    "count": "recipient_count",
                    "state": "state_name",
                    "State": "state_name",
                    "program": "entity_name"
                }
            },
            "Crop Insurance": {
                "column_names_map": {
                    "state": "state_code",
                    "policies_prem": "premium_policy_count",
                    "acres_insured": "base_acres",
                    "liabilities": "liability_amount",
                    "premium": "premium_amount",
                    "subsidy": "premium_subsidy_amount",
                    "indemnity": "indemnity_amount",
                    "farmer_premium": "farmer_premium_amount",
                    "loss_ratio": "loss_ratio",
                    "net_benefit": "net_farmer_benefit_amount"
                }
            }
        }

        # Main program category specific file paths
        if self.title_name == "Title 1: Commodities":
            self.base_acres_data = None
            self.farm_payee_count_data = None
            self.dmc_data = None
            self.sada_data = None

            self.base_acres_csv_filepath_arc_co = str(
                os.path.join(data_folder, kwargs["base_acres_csv_filename_arc_co"]))
            self.base_acres_csv_filepath_plc = str(os.path.join(data_folder, kwargs["base_acres_csv_filename_plc"]))

            self.farm_payee_count_csv_filepath_arc_co = str(os.path.join(data_folder,
                                                                         kwargs[
                                                                             "farm_payee_count_csv_filename_arc_co"]))
            self.farm_payee_count_csv_filepath_arc_ic = str(os.path.join(data_folder,
                                                                         kwargs[
                                                                             "farm_payee_count_csv_filename_arc_ic"]))
            self.farm_payee_count_csv_filepath_plc = str(os.path.join(data_folder,
                                                                      kwargs["farm_payee_count_csv_filename_plc"]))
            self.total_payment_csv_filepath_arc_co = str(os.path.join(data_folder,
                                                                      kwargs["total_payment_csv_filename_arc_co"]))
            self.total_payment_csv_filepath_arc_ic = str(os.path.join(data_folder,
                                                                      kwargs["total_payment_csv_filename_arc_ic"]))
            self.total_payment_csv_filepath_plc = str(os.path.join(data_folder,
                                                                   kwargs["total_payment_csv_filename_plc"]))
            self.dmc_sada_csv_filepath = str(
                os.path.join(data_folder, kwargs["dmc_sada_csv_filename"]))
        elif self.title_name == "Title 2: Conservation":
            self.acep_data = None
            self.crp_data = None
            self.eqip_data = None
            self.rcpp_data = None
            self.csp_data = None

            self.crp_csv_filepath = str(os.path.join(data_folder, kwargs["crp_csv_filename"]))
            self.acep_csv_filepath = str(os.path.join(data_folder, kwargs["acep_csv_filename"]))
            self.rcpp_csv_filepath = str(os.path.join(data_folder, kwargs["rcpp_csv_filename"]))
            self.eqip_csv_filepath = str(os.path.join(data_folder, kwargs["eqip_csv_filename"]))
            self.csp_csv_filepath = str(os.path.join(data_folder, kwargs["csp_csv_filename"]))
            pass
        elif self.title_name == "Crop Insurance":
            self.ci_data = None
            self.ci_benefit_csv_filepath = str(os.path.join(data_folder, kwargs["ci_state_year_benefit_filename"]))
        elif self.title_name == "Supplemental Nutrition Assistance Program (SNAP)":
            self.snap_data = None
            self.snap_mon_part_filepath = str(os.path.join(data_folder, kwargs["snap_monthly_participation_filename"]))
            self.snap_cost_filepath = str(os.path.join(data_folder, kwargs["snap_cost_filename"]))

    @staticmethod
    def __find_entity_type(entity_name):
        """
        This function is used to find the entity type (program, sub_program, subtitle, etc.) given the entity name
        :param entity_name:
        :return: entity type
        """

        if entity_name in ["Total Commodities Programs, Subtitle A", "Dairy Margin Coverage, Subtitle D",
                           "Supplemental Agricultural Disaster Assistance, Subtitle E"]:
            return "subtitle"
        elif entity_name in ["Price Loss Coverage (PLC)",
                             "Emergency Assistance for Livestock, Honey Bees, and Farm-Raised Fish Program (ELAP)",
                             "Livestock Forage Program (LFP)", "Livestock Indemnity Payments (LIP)",
                             "Tree Assistance Program (TAP)", "Environmental Quality Incentives Program (EQIP)",
                             "Conservation Stewardship Program (CSP)",
                             "Supplemental Nutrition Assistance Program (SNAP)"]:
            return "program"
        elif entity_name in ["Agriculture Risk Coverage County Option (ARC-CO)",
                             "Agriculture Risk Coverage Individual Coverage (ARC-IC)",
                             "General Sign-up", "Continuous Sign-up", "Grassland"]:
            return "sub_program"
        elif entity_name in ["CREP Only", "Continuous Non-CREP", "Farmable Wetland"]:
            return "sub_sub_program"
        else:
            return "unknown"

    def __convert_to_new_data_frame(self, data_frame, entity_name, data_type=None):
        row_list = []
        for state_code in self.us_state_abbreviations:
            state_data = data_frame[
                data_frame["state_name"] == self.us_state_abbreviations[state_code]]
            for year in range(self.start_year, self.end_year + 1):
                row_dict = dict()
                if state_data['state_name'].size == 1:
                    row_dict["state_code"] = state_code
                    row_dict["year"] = year
                    row_dict["entity_name"] = entity_name
                    row_dict["entity_type"] = self.__find_entity_type(entity_name)

                    if data_type == "Base Acres":
                        row_dict["base_acres"] = state_data[str(year)].item()
                    elif data_type == "Payee Count":
                        row_dict["recipient_count"] = state_data[str(year)].item()
                    elif data_type == "Total Payment":
                        row_dict["amount"] = round(state_data[str(year)].item(), 2)

                    row_list.append(row_dict)
        output_data_frame = pd.DataFrame(data=row_list)
        return output_data_frame

    def __read_and_clean_data(self, filepath):
        """
        Reads a CSV file and cleans the data.
        :param filepath: Path to the CSV file.
        :return: Cleaned DataFrame.
        """
        # Read the CSV file
        data = pd.read_csv(filepath)

        # Remove leading and trailing whitespaces from column names
        data.columns = data.columns.str.strip()

        # Rename columns to make them more uniform
        data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

        # Remove trailing whitespaces from specific columns if they exist
        if "practice_code" in data.columns:
            data["practice_code"] = data["practice_code"].str.strip()
        if "state_name" in data.columns:
            data["state_name"] = data["state_name"].str.strip()

        return data

    def format_data(self):

        if self.title_name == "Title 1: Commodities":

            # Read and clean the base acres CSV files for ARC-CO and PLC
            base_acres_data_arc_co = self.__read_and_clean_data(self.base_acres_csv_filepath_arc_co)
            base_acres_data_plc = self.__read_and_clean_data(self.base_acres_csv_filepath_plc)

            # Convert the base acres data to the new format
            base_acres_data_arc_co_output = self.__convert_to_new_data_frame(base_acres_data_arc_co,
                                                                             "Agriculture Risk Coverage County Option (ARC-CO)",
                                                                             "Base Acres")
            base_acres_data_plc_output = self.__convert_to_new_data_frame(base_acres_data_plc,
                                                                          "Price Loss Coverage (PLC)",
                                                                          "Base Acres")
            self.base_acres_data = pd.concat([base_acres_data_arc_co_output, base_acres_data_plc_output],
                                             ignore_index=True)

            # Read and clean the farm payee count CSV files for ARC-CO, ARC-IC, and PLC
            farm_payee_count_data_arc_co = self.__read_and_clean_data(self.farm_payee_count_csv_filepath_arc_co)
            farm_payee_count_data_arc_ic = self.__read_and_clean_data(self.farm_payee_count_csv_filepath_arc_ic)
            farm_payee_count_data_plc = self.__read_and_clean_data(self.farm_payee_count_csv_filepath_plc)

            # Convert the farm payee count data to the new format
            farm_payee_count_data_arc_co_output = self.__convert_to_new_data_frame(farm_payee_count_data_arc_co,
                                                                                   "Agriculture Risk Coverage County Option (ARC-CO)",
                                                                                   "Payee Count")
            farm_payee_count_data_arc_ic_output = self.__convert_to_new_data_frame(farm_payee_count_data_arc_ic,
                                                                                   "Agriculture Risk Coverage Individual Coverage (ARC-IC)",
                                                                                   "Payee Count")
            farm_payee_count_data_plc_output = self.__convert_to_new_data_frame(farm_payee_count_data_plc,
                                                                                "Price Loss Coverage (PLC)",
                                                                                "Payee Count")
            self.farm_payee_count_data = pd.concat(
                [farm_payee_count_data_arc_co_output, farm_payee_count_data_arc_ic_output,
                 farm_payee_count_data_plc_output], ignore_index=True)

            # Read and clean the total payment CSV files for ARC-CO, ARC-IC, and PLC
            total_payment_data_arc_co = self.__read_and_clean_data(self.total_payment_csv_filepath_arc_co)
            total_payment_data_arc_ic = self.__read_and_clean_data(self.total_payment_csv_filepath_arc_ic)
            total_payment_data_plc = self.__read_and_clean_data(self.total_payment_csv_filepath_plc)

            # Convert the total payment data to the new format
            total_payment_data_arc_co_output = self.__convert_to_new_data_frame(total_payment_data_arc_co,
                                                                                "Agriculture Risk Coverage County Option (ARC-CO)",
                                                                                "Total Payment")
            total_payment_data_arc_ic_output = self.__convert_to_new_data_frame(total_payment_data_arc_ic,
                                                                                "Agriculture Risk Coverage Individual Coverage (ARC-IC)",
                                                                                "Total Payment")
            total_payment_data_plc_output = self.__convert_to_new_data_frame(total_payment_data_plc,
                                                                             "Price Loss Coverage (PLC)",
                                                                             "Total Payment")
            self.program_data = pd.concat([total_payment_data_arc_co_output, total_payment_data_arc_ic_output,
                                           total_payment_data_plc_output], ignore_index=True)

            # Read and clean the DMC and SADA CSV files
            dmc_sada_data = self.__read_and_clean_data(self.dmc_sada_csv_filepath)

            # some columns have empty values and this makes the rows type as object
            # this makes the process of SUM errors since those are object not number
            # so the columns should be numeric all the time
            # make sure every number columns be number
            dmc_sada_data[["amount",
                           "recipient_count"]] = \
                dmc_sada_data[["amount",
                               "recipient_count"]].apply(pd.to_numeric)

            # Filter Dairy data
            self.dmc_data = dmc_sada_data[dmc_sada_data["entity_name"].isin(["Dairy", "DMC"])]
            self.dmc_data = self.dmc_data.replace(self.metadata[self.title_name]["value_names_map"])
            self.dmc_data = self.dmc_data.assign(entity_type="subtitle")
            # Add state code to dmc_data using self.us_state_abbreviations
            self.dmc_data = self.dmc_data.assign(state_code=self.dmc_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            # Filter Non-Dairy data
            self.sada_data = dmc_sada_data[~dmc_sada_data["entity_name"].isin(["Dairy", "DMC"])]
            self.sada_data = self.sada_data.replace(self.metadata[self.title_name]["value_names_map"])
            self.sada_data = self.sada_data.assign(entity_type="program")
            # Add state code to sada_data using self.us_state_abbreviations
            self.sada_data = self.sada_data.assign(state_code=self.sada_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            # perform left join on the base acres and farm payee count data
            self.program_data = pd.merge(self.program_data, self.base_acres_data,
                                         on=["state_code", "year", "entity_name",
                                             "entity_type"], how="left")
            self.program_data = pd.merge(self.program_data, self.farm_payee_count_data,
                                         on=["state_code", "year", "entity_name", "entity_type"], how="left")
        elif self.title_name == "Title 2: Conservation":

            # Import EQIP CSV files and convert to existing format
            eqip_data = pd.read_csv(self.eqip_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            eqip_data.columns = eqip_data.columns.str.strip()

            # Rename column names to make it more uniform
            eqip_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Remove leading and trailing whitespaces from practice_code column
            eqip_data["practice_code"] = eqip_data["practice_code"].str.strip()

            # Replace value names
            eqip_data["practice_category"] = eqip_data["practice_category"].replace(
                self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            eqip_data = eqip_data[eqip_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            eqip_data = eqip_data[eqip_data["amount"].notna()]

            # Filter only states in self.us_state_abbreviations
            eqip_data = eqip_data[eqip_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add entity type to eqip
            eqip_data = eqip_data.assign(entity_type="program")

            # Add entity_name to eqip
            eqip_data = eqip_data.assign(entity_name="Environmental Quality Incentives Program (EQIP)")

            # Add state code to eqip using self.us_state_abbreviations
            eqip_data = eqip_data.assign(state_code=eqip_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            self.eqip_data = eqip_data

            # Import CSP CSV files and convert to existing format
            csp_data = pd.read_csv(self.csp_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            csp_data.columns = csp_data.columns.str.strip()

            # Rename column names to make it more uniform
            csp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Remove leading and trailing whitespaces from practice_code column
            csp_data["practice_code"] = csp_data["practice_code"].str.strip()

            # Replace value names
            csp_data["practice_category"] = csp_data["practice_category"].replace(
                self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            csp_data = csp_data[csp_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            csp_data = csp_data[csp_data["amount"].notna()]

            # Filter only states in self.us_state_abbreviations
            csp_data = csp_data[csp_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add entity type to csp
            csp_data = csp_data.assign(entity_type="program")

            # Add entity_name to csp
            csp_data = csp_data.assign(entity_name="Conservation Stewardship Program (CSP)")

            # Add state code to csp using self.us_state_abbreviations
            csp_data = csp_data.assign(state_code=csp_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            self.csp_data = csp_data

            # Import CRP CSV files and convert to existing format
            crp_raw_data = pd.read_csv(self.crp_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            crp_raw_data.columns = crp_raw_data.columns.str.strip()

            total_crp_data = crp_raw_data[
                ["year", "state", "Total CRP - ANNUAL RENTAL PAYMENTS ($1000)", "Total CRP - NUMBER OF CONTRACTS",
                 "Total CRP - NUMBER OF FARMS", "Total CRP - ACRES"]]
            total_crp_data.rename(columns={"Total CRP - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                                           "Total CRP - NUMBER OF CONTRACTS": "contract_count",
                                           "Total CRP - NUMBER OF FARMS": "farm_count",
                                           "Total CRP - ACRES": "base_acres"}, inplace=True)
            total_crp_data["amount"] = total_crp_data["amount"] * 1000
            total_crp_data["entity_name"] = "Total CRP"
            total_crp_data["entity_type"] = "sub_program"

            general_sign_up_data = crp_raw_data[[
                "year", "state", "Total General Sign-Up - ANNUAL RENTAL PAYMENTS ($1000)",
                "Total General Sign-Up - NUMBER OF CONTRACTS",
                "Total General Sign-Up - NUMBER OF FARMS", "Total General Sign-Up - ACRES"]]
            general_sign_up_data.rename(
                columns={"Total General Sign-Up - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                         "Total General Sign-Up - NUMBER OF CONTRACTS": "contract_count",
                         "Total General Sign-Up - NUMBER OF FARMS": "farm_count",
                         "Total General Sign-Up - ACRES": "base_acres"}, inplace=True)
            general_sign_up_data["amount"] = general_sign_up_data["amount"] * 1000
            general_sign_up_data["entity_name"] = "General Sign-up"
            general_sign_up_data["entity_type"] = "sub_program"

            continuous_sign_up_data = crp_raw_data[[
                "year", "state", "Total Continuous - ANNUAL RENTAL PAYMENTS ($1000)",
                "Total Continuous - NUMBER OF CONTRACTS",
                "Total Continuous - NUMBER OF FARMS", "Total Continuous - ACRES"]]
            continuous_sign_up_data.rename(columns={"Total Continuous - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                                                    "Total Continuous - NUMBER OF CONTRACTS": "contract_count",
                                                    "Total Continuous - NUMBER OF FARMS": "farm_count",
                                                    "Total Continuous - ACRES": "base_acres"}, inplace=True)
            continuous_sign_up_data["amount"] = continuous_sign_up_data["amount"] * 1000
            continuous_sign_up_data["entity_name"] = "Continuous Sign-up"
            continuous_sign_up_data["entity_type"] = "sub_program"

            crep_only_data = crp_raw_data[["year", "state", "CREP Only - ANNUAL RENTAL PAYMENTS ($1000)",
                                           "CREP Only - NUMBER OF CONTRACTS", "CREP Only - NUMBER OF FARMS",
                                           "CREP Only - ACRES"]]
            crep_only_data.rename(columns={"CREP Only - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                                           "CREP Only - NUMBER OF CONTRACTS": "contract_count",
                                           "CREP Only - NUMBER OF FARMS": "farm_count",
                                           "CREP Only - ACRES": "base_acres"}, inplace=True)
            crep_only_data["amount"] = crep_only_data["amount"] * 1000
            crep_only_data["entity_name"] = "CREP Only"
            crep_only_data["entity_type"] = "sub_sub_program"

            continuous_non_crep_data = crp_raw_data[
                ["year", "state", "Continuous Non-CREP - ANNUAL RENTAL PAYMENTS ($1000)",
                 "Continuous Non-CREP - NUMBER OF CONTRACTS", "Continuous Non-CREP - NUMBER OF FARMS",
                 "Continuous Non-CREP - ACRES"]]
            continuous_non_crep_data.rename(
                columns={"Continuous Non-CREP - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                         "Continuous Non-CREP - NUMBER OF CONTRACTS": "contract_count",
                         "Continuous Non-CREP - NUMBER OF FARMS": "farm_count",
                         "Continuous Non-CREP - ACRES": "base_acres"}, inplace=True)
            continuous_non_crep_data["amount"] = continuous_non_crep_data["amount"] * 1000
            continuous_non_crep_data["entity_name"] = "Continuous Non-CREP"
            continuous_non_crep_data["entity_type"] = "sub_sub_program"

            farmable_wetland_data = crp_raw_data[["year", "state", "Farmable Wetland - ANNUAL RENTAL PAYMENTS ($1000)",
                                                  "Farmable Wetland - NUMBER OF CONTRACTS",
                                                  "Farmable Wetland - NUMBER OF FARMS", "Farmable Wetland - ACRES"]]
            farmable_wetland_data.rename(columns={"Farmable Wetland - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                                                  "Farmable Wetland - NUMBER OF CONTRACTS": "contract_count",
                                                  "Farmable Wetland - NUMBER OF FARMS": "farm_count",
                                                  "Farmable Wetland - ACRES": "base_acres"}, inplace=True)
            farmable_wetland_data["amount"] = farmable_wetland_data["amount"] * 1000
            farmable_wetland_data["entity_name"] = "Farmable Wetland"
            farmable_wetland_data["entity_type"] = "sub_sub_program"

            grassland_data = crp_raw_data[
                ["year", "state", "Grassland - ANNUAL RENTAL PAYMENTS ($1000)", "Grassland - NUMBER OF CONTRACTS",
                 "Grassland - NUMBER OF FARMS", "Grassland - ACRES"]]

            grassland_data.rename(columns={"Grassland - ANNUAL RENTAL PAYMENTS ($1000)": "amount",
                                           "Grassland - NUMBER OF CONTRACTS": "contract_count",
                                           "Grassland - NUMBER OF FARMS": "farm_count",
                                           "Grassland - ACRES": "base_acres"}, inplace=True)

            grassland_data["amount"] = grassland_data["amount"] * 1000
            grassland_data["entity_name"] = "Grassland"
            grassland_data["entity_type"] = "sub_program"

            crp_data = pd.concat([total_crp_data, general_sign_up_data, continuous_sign_up_data, crep_only_data,
                                  continuous_non_crep_data, farmable_wetland_data, grassland_data], ignore_index=True)

            # Rename column names to make it more uniform
            crp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Filter only relevant years data
            crp_data = crp_data[crp_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            crp_data = crp_data[crp_data["amount"].notna()]

            # Change state name to title case
            crp_data["state_name"] = crp_data["state_name"].str.title()

            # Filter only states in self.us_state_abbreviations
            crp_data = crp_data[crp_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add state code to crp using self.us_state_abbreviations
            crp_data = crp_data.assign(state_code=crp_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            self.crp_data = crp_data

            # Import ACEP CSV file and convert to pandas dataframe
            acep_data = pd.read_csv(self.acep_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            acep_data.columns = acep_data.columns.str.strip()

            # Rename column names to make it more uniform
            acep_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Remove leading and trailing whitespaces from state_name column
            acep_data["state_name"] = acep_data["state_name"].str.strip()

            # Replace value names
            acep_data["state_name"] = acep_data["state_name"].replace(self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            acep_data = acep_data[acep_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            acep_data = acep_data[acep_data["amount"].notna()]

            # Filter only states in self.us_state_abbreviations
            acep_data = acep_data[acep_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add entity type to acep
            acep_data = acep_data.assign(entity_type="program")

            # Add entity_name to acep
            acep_data = acep_data.assign(entity_name="Agricultural Conservation Easement Program (ACEP)")

            # Add state code to acep using self.us_state_abbreviations
            acep_data = acep_data.assign(state_code=acep_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            # Multiply amount by 1000
            acep_data["amount"] = acep_data["amount"] * 1000

            self.acep_data = acep_data

            # Import RCPP CSV file and convert to pandas dataframe
            rcpp_data = pd.read_csv(self.rcpp_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            rcpp_data.columns = rcpp_data.columns.str.strip()

            # Rename column names to make it more uniform
            rcpp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Remove leading and trailing whitespaces from state_name column
            rcpp_data["state_name"] = rcpp_data["state_name"].str.strip()

            # Replace value names
            rcpp_data["state_name"] = rcpp_data["state_name"].replace(self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            rcpp_data = rcpp_data[rcpp_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            rcpp_data = rcpp_data[rcpp_data["amount"].notna()]

            # Filter only states in self.us_state_abbreviations
            rcpp_data = rcpp_data[rcpp_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add entity type to rcpp
            rcpp_data = rcpp_data.assign(entity_type="program")

            # Add entity_name to rcpp
            rcpp_data = rcpp_data.assign(entity_name="Regional Conservation Partnership Program (RCPP)")

            # Add state code to rcpp using self.us_state_abbreviations
            rcpp_data = rcpp_data.assign(state_code=rcpp_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            # Multiply amount by 1000
            rcpp_data["amount"] = rcpp_data["amount"] * 1000

            self.rcpp_data = rcpp_data

            self.program_data = pd.concat(
                [self.eqip_data, self.csp_data, self.crp_data, self.acep_data, self.rcpp_data],
                ignore_index=True)

        elif self.title_name == "Supplemental Nutrition Assistance Program (SNAP)":
            # Import SNAP Cost CSV file
            snap_cost_data = pd.read_csv(self.snap_cost_filepath)

            snap_mon_part_data = pd.read_csv(self.snap_mon_part_filepath)

            # Filter columns from start year to end year along with the 'state' column
            snap_cost_data = snap_cost_data[['State'] + [col for col in snap_cost_data.columns if
                                                         col != 'State' and col != 'Total' and self.start_year <= int(
                                                             col) <= self.end_year]]

            snap_mon_part_data = snap_mon_part_data[['State'] + [col for col in snap_mon_part_data.columns if
                                                                 col != 'State' and col != 'Avg.' and self.start_year <= int(
                                                                     col) <= self.end_year]]

            # Rename column names to make it more uniform
            snap_cost_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            snap_mon_part_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # change state name to full name
            snap_cost_data["state_name"] = snap_cost_data["state_name"].map(self.us_state_abbreviations)
            snap_mon_part_data["state_name"] = snap_mon_part_data["state_name"].map(self.us_state_abbreviations)

            # restructure the data frame
            snap_cost_data_output = \
                self.__convert_to_new_data_frame(
                    snap_cost_data, "Supplemental Nutrition Assistance Program (SNAP)", "Total Payment")

            snap_mon_part_data_output = \
                self.__convert_to_new_data_frame(
                    snap_mon_part_data, "Supplemental Nutrition Assistance Program (SNAP)", "Payee Count")

            # perform left join on the base acres and farm payee count data
            self.snap_data = pd.merge(snap_cost_data_output, snap_mon_part_data_output,
                                      on=["state_code", "year", "entity_name", "entity_type"], how="left")

        elif self.title_name == "Crop Insurance":
            # Import Crop Insurance Benefit CSV file
            ci_data = pd.read_csv(self.ci_benefit_csv_filepath)

            # Filter rows where the 'year' column values are between self.start_year and self.end_year
            ci_data = ci_data[(ci_data['year'] >= self.start_year) & (ci_data['year'] <= self.end_year)]

            # Rename column names to make it more uniform
            ci_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Add entity type to ci_data
            ci_data = ci_data.assign(entity_type="program")

            # Add entity_name to ci_data
            ci_data = ci_data.assign(entity_name="Crop Insurance")

            self.ci_data = ci_data
