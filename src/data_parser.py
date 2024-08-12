import os
import pandas as pd
import json


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
                    "payments": "amount",
                    "category_name": "practice_category",
                    "StatutoryCategory": "practice_category",
                    "practice_code": "practice_code_processed",
                    "full_practice_code": "practice_code"
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
                    # "Existing Activity Payments": "Miscellaneous",
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
            pass
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
        if entity_name in ["Agriculture Risk Coverage County Option (ARC-CO)",
                           "Agriculture Risk Coverage Individual Coverage (ARC-IC)"]:
            return "sub_program"
        elif entity_name in ["Price Loss Coverage (PLC)",
                             "Emergency Assistance for Livestock, Honey Bees, and Farm-Raised Fish Program (ELAP)",
                             "Livestock Forage Program (LFP)", "Livestock Indemnity Payments (LIP)",
                             "Tree Assistance Program (TAP)", "Supplemental Nutrition Assistance Program (SNAP)"]:
            return "program"
        elif entity_name in ["Total Commodities Programs, Subtitle A", "Dairy Margin Coverage, Subtitle D",
                             "Supplemental Agricultural Disaster Assistance, Subtitle E",
                             "Environmental Quality Incentives Program (EQIP)",
                             "Conservation Stewardship Program (CSP)", ]:
            return "subtitle"
        else:
            return "unknown"

    def __convert_to_new_data_frame(self, data_frame, program_name, data_type=None):
        row_list = []
        for state_code in self.us_state_abbreviations:
            state_data = data_frame[
                data_frame["state_name"] == self.us_state_abbreviations[state_code]]
            for year in range(self.start_year, self.end_year + 1):
                row_dict = dict()
                if state_data['state_name'].size == 1:
                    row_dict["state_code"] = state_code
                    row_dict["year"] = year
                    row_dict["entity_name"] = program_name
                    row_dict["entity_type"] = self.__find_entity_type(program_name)

                    if data_type == "Base Acres":
                        row_dict["base_acres"] = state_data[str(year)].item()
                    elif data_type == "Payee Count":
                        row_dict["recipient_count"] = state_data[str(year)].item()
                    elif data_type == "Total Payment":
                        row_dict["amount"] = round(state_data[str(year)].item(), 2)

                    row_list.append(row_dict)
        output_data_frame = pd.DataFrame(data=row_list)
        return output_data_frame

    def format_data(self):

        if self.title_name == "Title 1: Commodities":
            # Import base acres CSV files and convert to existing format
            base_acres_data_arc_co = pd.read_csv(self.base_acres_csv_filepath_arc_co)
            # Rename column names to make it more uniform
            base_acres_data_arc_co.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            base_acres_data_plc = pd.read_csv(self.base_acres_csv_filepath_plc)
            # Rename column names to make it more uniform
            base_acres_data_plc.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            base_acres_data_arc_co_output = self.__convert_to_new_data_frame(base_acres_data_arc_co,
                                                                             "Agriculture Risk Coverage County Option (ARC-CO)",
                                                                             "Base Acres")
            base_acres_data_plc_output = self.__convert_to_new_data_frame(base_acres_data_plc,
                                                                          "Price Loss Coverage (PLC)",
                                                                          "Base Acres")
            self.base_acres_data = pd.concat([base_acres_data_arc_co_output, base_acres_data_plc_output],
                                             ignore_index=True)

            # Import farm payee count CSV files and convert to existing format
            farm_payee_count_data_arc_co = pd.read_csv(self.farm_payee_count_csv_filepath_arc_co)
            # Rename column names to make it more uniform
            farm_payee_count_data_arc_co.rename(columns=self.metadata[self.title_name]["column_names_map"],
                                                inplace=True)

            farm_payee_count_data_arc_ic = pd.read_csv(self.farm_payee_count_csv_filepath_arc_ic)
            # Rename column names to make it more uniform
            farm_payee_count_data_arc_ic.rename(columns=self.metadata[self.title_name]["column_names_map"],
                                                inplace=True)

            farm_payee_count_data_plc = pd.read_csv(self.farm_payee_count_csv_filepath_plc)
            # Rename column names to make it more uniform
            farm_payee_count_data_plc.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

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

            # Import total payment count CSV files and convert to existing format
            total_payment_data_arc_co = pd.read_csv(self.total_payment_csv_filepath_arc_co)
            # Rename column names to make it more uniform
            total_payment_data_arc_co.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            total_payment_data_arc_ic = pd.read_csv(self.total_payment_csv_filepath_arc_ic)
            # Rename column names to make it more uniform
            total_payment_data_arc_ic.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            total_payment_data_plc = pd.read_csv(self.total_payment_csv_filepath_plc)
            # Rename column names to make it more uniform
            total_payment_data_plc.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

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

            dmc_sada_data = pd.read_csv(self.dmc_sada_csv_filepath)
            # Rename column names to make it more uniform
            dmc_sada_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # some columns have empty values and this makes the rows type as object
            # this makes the process of SUM errors since those are object not number
            # so the columns should be numeric all the time
            # make sure every number columns be number
            dmc_sada_data[["amount",
                           "recipient_count"]] = \
                dmc_sada_data[["amount",
                               "recipient_count"]].apply(pd.to_numeric)

            # Filter Dairy data
            self.dmc_data = dmc_sada_data[dmc_sada_data["entity_name"] == "Dairy"]
            self.dmc_data = self.dmc_data.replace(self.metadata[self.title_name]["value_names_map"])
            self.dmc_data = self.dmc_data.assign(entity_type="subtitle")
            # Add state code to dmc_data using self.us_state_abbreviations
            self.dmc_data = self.dmc_data.assign(state_code=self.dmc_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            # Filter Non-Dairy data
            self.sada_data = dmc_sada_data[dmc_sada_data["entity_name"] != "Dairy"]
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

            # TODO: Add ACEP, RCPP, and CRP data processing and update self.program_data

            # Import CRP CSV files and convert to existing format
            crp_raw_data = pd.read_csv(self.crp_csv_filepath)

            # Remove leading and trailing whitespaces from column names
            crp_raw_data.columns = crp_raw_data.columns.str.strip()

            # Create new blank data frame
            crp_data = pd.DataFrame(
                columns=["year", "state_name", "amount", "recipient_count", "farm_count", "base_acres",
                         "practice_category"])

            # Iterate through each row in crp_raw_data
            for index, row in crp_raw_data.iterrows():
                # Extract year and state_name from row
                year = row["year"]
                state_name = row["state"]

                # Extract amount, recipient_count, farm_count, base_acres, and practice_category from row
                total_crp_amount = row["Total CRP - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_crp_recipient_count = row["Total CRP - NUMBER OF CONTRACTS"]
                total_crp_farm_count = row["Total CRP - NUMBER OF FARMS"]
                total_crp_base_acres = row["Total CRP - ACRES"]
                total_crp_practice_category = "Total CRP"

                # Extract total general sign-up data
                total_general_sign_up_amount = row["Total General Sign-Up - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_general_sign_up_recipient_count = row["Total General Sign-Up - NUMBER OF CONTRACTS"]
                total_general_sign_up_farm_count = row["Total General Sign-Up - NUMBER OF FARMS"]
                total_general_sign_up_base_acres = row["Total General Sign-Up - ACRES"]
                total_general_sign_up_practice_category = "Total General Sign-up"

                # Extract total continuous data
                total_continuous_amount = row["Total Continuous - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_continuous_recipient_count = row["Total Continuous - NUMBER OF CONTRACTS"]
                total_continuous_farm_count = row["Total Continuous - NUMBER OF FARMS"]
                total_continuous_base_acres = row["Total Continuous - ACRES"]
                total_continuous_practice_category = "Total Continuous Sign-up"

                # Extract CREP only data
                total_crep_only_amount = row["CREP Only - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_crep_only_recipient_count = row["CREP Only - NUMBER OF CONTRACTS"]
                total_crep_only_farm_count = row["CREP Only - NUMBER OF FARMS"]
                total_crep_only_base_acres = row["CREP Only - ACRES"]
                total_crep_only_practice_category = "CREP Only"

                # Extract continuous non-CREP data
                total_continuous_non_crep_amount = row["Continuous Non-CREP - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_continuous_non_crep_recipient_count = row["Continuous Non-CREP - NUMBER OF CONTRACTS"]
                total_continuous_non_crep_farm_count = row["Continuous Non-CREP - NUMBER OF FARMS"]
                total_continuous_non_crep_base_acres = row["Continuous Non-CREP - ACRES"]
                total_continuous_non_crep_practice_category = "Continuous Non-CREP"

                # Extract farmable wetland data
                total_farmable_wetland_amount = row["Farmable Wetland - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_farmable_wetland_recipient_count = row["Farmable Wetland - NUMBER OF CONTRACTS"]
                total_farmable_wetland_farm_count = row["Farmable Wetland - NUMBER OF FARMS"]
                total_farmable_wetland_base_acres = row["Farmable Wetland - ACRES"]
                total_farmable_wetland_practice_category = "Farmable Wetland"

                # Extract grassland data
                total_grassland_amount = row["Grassland - ANNUAL RENTAL PAYMENTS ($1000)"] * 1000
                total_grassland_recipient_count = row["Grassland - NUMBER OF CONTRACTS"]
                total_grassland_farm_count = row["Grassland - NUMBER OF FARMS"]
                total_grassland_base_acres = row["Grassland - ACRES"]
                total_grassland_practice_category = "Grassland"

                # data rows
                crp_data_rows = [{"year": year, "state_name": state_name, "amount": total_crp_amount,
                                  "recipient_count": total_crp_recipient_count,
                                  "farm_count": total_crp_farm_count, "base_acres": total_crp_base_acres,
                                  "practice_category": total_crp_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_general_sign_up_amount,
                                  "recipient_count": total_general_sign_up_recipient_count,
                                  "farm_count": total_general_sign_up_farm_count,
                                  "base_acres": total_general_sign_up_base_acres,
                                  "practice_category": total_general_sign_up_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_continuous_amount,
                                  "recipient_count": total_continuous_recipient_count,
                                  "farm_count": total_continuous_farm_count, "base_acres": total_continuous_base_acres,
                                  "practice_category": total_continuous_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_crep_only_amount,
                                  "recipient_count": total_crep_only_recipient_count,
                                  "farm_count": total_crep_only_farm_count, "base_acres": total_crep_only_base_acres,
                                  "practice_category": total_crep_only_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_continuous_non_crep_amount,
                                  "recipient_count": total_continuous_non_crep_recipient_count,
                                  "farm_count": total_continuous_non_crep_farm_count,
                                  "base_acres": total_continuous_non_crep_base_acres,
                                  "practice_category": total_continuous_non_crep_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_farmable_wetland_amount,
                                  "recipient_count": total_farmable_wetland_recipient_count,
                                  "farm_count": total_farmable_wetland_farm_count,
                                  "base_acres": total_farmable_wetland_base_acres,
                                  "practice_category": total_farmable_wetland_practice_category},
                                 {"year": year, "state_name": state_name, "amount": total_grassland_amount,
                                  "recipient_count": total_grassland_recipient_count,
                                  "farm_count": total_grassland_farm_count, "base_acres": total_grassland_base_acres,
                                  "practice_category": total_grassland_practice_category}]

                # Append extracted data to crp_data
                crp_data = crp_data.append(crp_data_rows,
                                           ignore_index=True)

            # Rename column names to make it more uniform
            # crp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # # Remove leading and trailing whitespaces from practice_code column
            # crp_data["practice_code"] = crp_data["practice_code"].str.strip()

            # Replace value names
            # crp_data["practice_category"] = crp_data["practice_category"].replace(
            #     self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            crp_data = crp_data[crp_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Exclude amount values that are NaN
            crp_data = crp_data[crp_data["amount"].notna()]

            # Change state name to title case
            crp_data["state_name"] = crp_data["state_name"].str.title()

            # Filter only states in self.us_state_abbreviations
            crp_data = crp_data[crp_data["state_name"].isin(self.us_state_abbreviations.values())]

            # Add entity type to crp
            crp_data = crp_data.assign(entity_type="program")

            # Add entity_name to crp
            crp_data = crp_data.assign(entity_name="Conservation Reserve Program (CRP)")

            # Add state code to crp using self.us_state_abbreviations
            crp_data = crp_data.assign(state_code=crp_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            self.crp_data = crp_data

            self.program_data = pd.concat([self.eqip_data, self.csp_data, self.crp_data], ignore_index=True)

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
