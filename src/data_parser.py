import os
import pandas as pd


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
                    "Total CRP - NUMBER OF CONTRACTS": "CRP-Contract",
                    "Total CRP - NUMBER OF FARMS": "CRP-Farm",
                    "Total CRP - ACRES": "CRP-Acre",
                    "Total CRP - ANNUAL RENTAL PAYMENTS ($1000)": "CRP-Rent-1K",
                    "Total CRP - ANNUAL RENTAL PAYMENTS ($/ACRE)": "CRP-Ren-Acre",
                    "Total General Sign-Up - NUMBER OF CONTRACTS": "Gen-Contract",
                    "Total General Sign-Up - NUMBER OF FARMS": "Gen-Farm",
                    "Total General Sign-Up - ACRES": "Gen-Acre",
                    "Total General Sign-Up - ANNUAL RENTAL PAYMENTS ($1000)": "Gen-Rent-1K",
                    "Total General Sign-Up - ANNUAL RENTAL PAYMENTS ($/ACRE)": "Gen-Rent-Acre",
                    "Total Continuous - NUMBER OF CONTRACTS": "Cont-Contract",
                    "Total Continuous - NUMBER OF FARMS": "Cont-Farm",
                    "Total Continuous - ACRES": "Cont-Acre",
                    "Total Continuous - ANNUAL RENTAL PAYMENTS ($1000)": "Cont-Rent-1K",
                    "Total Continuous - ANNUAL RENTAL PAYMENTS ($/ACRE)": "Cont-Rent-Acre",
                    "CREP Only - NUMBER OF CONTRACTS": "CREP-Contract",
                    "CREP Only - NUMBER OF FARMS": "CREP-Farm",
                    "CREP Only - ACRES": "CREP-Acre",
                    "CREP Only - ANNUAL RENTAL PAYMENTS ($1000)": "CREP-Rent-1K",
                    "CREP Only - ANNUAL RENTAL PAYMENTS ($/ACRE)": "CREP-Rent-Acre",
                    "Continuous Non-CREP - NUMBER OF CONTRACTS": "No-CREP-Contract",
                    "Continuous Non-CREP - NUMBER OF FARMS": "No-CREP-Farm",
                    "Continuous Non-CREP - ACRES": "No-CREP-Acre",
                    "Continuous Non-CREP - ANNUAL RENTAL PAYMENTS ($1000)": "No-CREP-Rent-1K",
                    "Continuous Non-CREP - ANNUAL RENTAL PAYMENTS ($/ACRE)": "No-CREP-Rent-Acre",
                    "Farmable Wetland - NUMBER OF CONTRACTS": "Wet-Contract",
                    "Farmable Wetland - NUMBER OF FARMS": "Wet-Farm",
                    "Farmable Wetland - ACRES": "Wet-Acre",
                    "Farmable Wetland - ANNUAL RENTAL PAYMENTS ($1000)": "Wet-Rent-1K",
                    "Farmable Wetland - ANNUAL RENTAL PAYMENTS ($/ACRE)": "Wet-Rent-Acre",
                    "Grassland - NUMBER OF CONTRACTS": "Grass-Contract",
                    "Grassland - NUMBER OF FARMS": "Grass-Farm",
                    "Grassland - ACRES": "Grass-Acre",
                    "Grassland - ANNUAL RENTAL PAYMENTS ($1000)": "Grass-Rent-1K",
                    "Grassland - ANNUAL RENTAL PAYMENTS ($/ACRE)": "Grass-Rent-Acre",
                    "Pay_year": "year",
                    "State": "state_name",
                    "payments": "amount",

                },
                "value_names_map": {
                    "CRP": "Conservation Reserve Program (CRP)",
                    "ACEP": "Agricultural Conservation Easement Program (ACEP)",
                    "RCPP": "Regional Conservation Partnership Program (RCPP)",
                    "EQIP": "Environmental Quality Incentives Program (EQIP)",
                    "CSP": "Conservation Stewardship Program (CSP)",
                    "Other 1 - planning": "Other planning",
                    "Other 2 - improvement": "Other improvement",
                    "Conservating planning assessment": "Conservation planning assessment",
                    "Resource-conserving crop rotatation": "Resource-conserving crop rotation",
                    "Land Management": "Land management",
                    "Forest Management": "Land management",
                    "Soil Remediation": "Soil remediation"
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
            pass

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
                             "Tree Assistance Program (TAP)"]:
            return "program"
        elif entity_name in ["Total Commodities Programs, Subtitle A", "Dairy Margin Coverage, Subtitle D",
                             "Supplemental Agricultural Disaster Assistance, Subtitle E"]:
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
            # # Import CRP CSV files and convert to existing format
            # crp_data = pd.read_csv(self.crp_csv_filepath)
            # # Rename column names to make it more uniform
            # crp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)
            #
            # # Add entity type to crp_data
            # crp_data = crp_data.assign(entity_type="program")
            #
            # # Add state code to crp_data using self.us_state_abbreviations
            # crp_data = crp_data.assign(state_code=crp_data["state_name"].map(
            #     {v: k for k, v in self.us_state_abbreviations.items()}))
            #
            # self.crp_data = crp_data
            #
            # # Import ACEP CSV files and convert to existing format
            # acep_data = pd.read_csv(self.acep_csv_filepath)
            # # Rename column names to make it more uniform
            # acep_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)
            #
            # # Add entity type to acep_data
            # acep_data = acep_data.assign(entity_type="program")
            #
            # # Add state code to acep_data using self.us_state_abbreviations
            # acep_data = acep_data.assign(state_code=acep_data["state_name"].map(
            #     {v: k for k, v in self.us_state_abbreviations.items()}))
            #
            # self.acep_data = acep_data
            #
            # # Import RCPP CSV files and convert to existing format
            # rcpp_data = pd.read_csv(self.rcpp_csv_filepath)
            # # Rename column names to make it more uniform
            # rcpp_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)
            #
            # # Add entity type to rcpp_data
            # rcpp_data = rcpp_data.assign(entity_type="program")
            #
            # # Add state code to rcpp_data using self.us_state_abbreviations
            # rcpp_data = rcpp_data.assign(state_code=rcpp_data["state_name"].map(
            #     {v: k for k, v in self.us_state_abbreviations.items()}))
            #
            # self.rcpp_data = rcpp_data

            # Import EQIP CSV files and convert to existing format
            eqip_data = pd.read_csv(self.eqip_csv_filepath)
            # Rename column names to make it more uniform
            eqip_data.rename(columns=self.metadata[self.title_name]["column_names_map"], inplace=True)

            # Replace value names
            eqip_data = eqip_data.replace(self.metadata[self.title_name]["value_names_map"])

            # Filter only relevant years data
            eqip_data = eqip_data[eqip_data["year"].between(self.start_year, self.end_year, inclusive="both")]

            # Add entity type to eqip
            eqip_data = eqip_data.assign(entity_type="program")

            # Add state code to eqip using self.us_state_abbreviations
            eqip_data = eqip_data.assign(state_code=eqip_data["state_name"].map(
                {v: k for k, v in self.us_state_abbreviations.items()}))

            self.eqip_data = eqip_data

            print("EQIP data")
            print(self.eqip_data)
