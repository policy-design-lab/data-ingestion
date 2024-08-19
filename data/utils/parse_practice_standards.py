import csv
import re
from copy import deepcopy

if __name__ == '__main__':
    csp_practice_standards = []
    eqip_practice_standards = []
    csp_practice_standards_with_code = []
    eqip_practice_standards_with_code = []
    csp_missing_practice_standards = []
    eqip_missing_practice_standards = []
    eqip_practice_standards_filtered = []
    csp_practice_standards_filtered = []
    merged_practice_standards_filtered = []
    nrcs_practice_standards = []
    nrcs_practice_standards_dict_list = []

    # Read and parse NRCS practice standards
    with open('../common/nrcs_practice_standards.txt', 'r') as f:
        lines = f.readlines()
        print(len(lines))
        for line in lines:
            parts = line.rsplit('(', maxsplit=2)
            practice_name = parts[0].strip()
            practice_unit = parts[1].split(')')[0].strip()
            practice_code = parts[2].split(')')[0].strip()
            nrcs_practice_standards.append((practice_code, practice_name, practice_unit))
            nrcs_practice_standards_dict_list.append(
                {"practice_code": practice_code, "practice_name": practice_name, "practice_unit": practice_unit,
                 "source": 'NRCS'})

    # Parse CSP practice standards
    with open('../common/csp_practice_standards_all.txt', 'r') as f:
        lines = f.readlines()
        print(len(lines))
        for line in lines:
            parts = line.rsplit('(', maxsplit=1)
            csp_practice_name = parts[0].strip()
            csp_practice_code = parts[1].split(')')[0].strip()
            csp_practice_standards.append((csp_practice_code, csp_practice_name))

    # Parse EQIP practice standards
    with open('../common/eqip_practice_standards_all.txt', 'r') as f:
        lines = f.readlines()
        print(len(lines))
        for line in lines:
            parts = line.rsplit('(', maxsplit=1)
            eqip_practice_name = parts[0].strip()
            eqip_practice_code = parts[1].split(')')[0].strip()
            eqip_practice_standards.append((eqip_practice_code, eqip_practice_name))

    # Check for match between CSP and NRCS practice standards
    for practice_code, practice_name in csp_practice_standards:

        if re.search(r'\d{3}', practice_code):
            csp_practice_code = re.search(r'\d{3}', practice_code).group()
        # Add other practice codes that does not contain three-digit codes.
        else:
            csp_practice_code = practice_code

        found_code = False
        for item in csp_practice_standards_filtered:
            if item['practice_code'] == csp_practice_code:
                found_code = True
                break
        if not found_code:
            csp_practice_standards_filtered.append(
                {"practice_code": csp_practice_code, "practice_name": practice_name})

        found = False
        for national_practice_code, national_practice_name, _ in nrcs_practice_standards:
            if practice_code.find(national_practice_code) != -1:
                print(f'Found {national_practice_code} in {practice_code}')
                csp_practice_standards_with_code.append((practice_code, practice_name, national_practice_code))
                found = True
                break
        if not found:
            csp_missing_practice_standards.append((practice_code, practice_name))
            print(f'Could not find {practice_code} in national practice standards')

    # Check for match between EQIP and NRCS practice standards
    for practice_code, practice_name in eqip_practice_standards:

        if re.search(r'\d{3}', practice_code):
            eqip_practice_code = re.search(r'\d{3}', practice_code).group()
        # Add other practice codes that does not contain three-digit codes.
        else:
            eqip_practice_code = practice_code

        found_code = False
        for item in eqip_practice_standards_filtered:
            if item['practice_code'] == eqip_practice_code:
                found_code = True
                break
        if not found_code:
            eqip_practice_standards_filtered.append(
                {"practice_code": eqip_practice_code, "practice_name": practice_name})

        found = False
        for national_practice_code, national_practice_name, _ in nrcs_practice_standards:
            if practice_code.find(national_practice_code) != -1:
                print(f'Found {national_practice_code} in {practice_code}')
                eqip_practice_standards_with_code.append((practice_code, practice_name, national_practice_code))
                found = True
                break
        if not found:
            eqip_missing_practice_standards.append((practice_code, practice_name))
            print(f'Could not find {practice_code} in national practice standards')

    # Merge eqip_practice_standards_filtered and csp_practice_standards_filtered while removing duplicates
    merged_practice_standards_filtered = deepcopy(eqip_practice_standards_filtered)
    for item in merged_practice_standards_filtered:
        item['source'] = 'EQIP'
    for item_csp in csp_practice_standards_filtered:
        found = False
        for item_eqip in eqip_practice_standards_filtered:
            if item_csp['practice_code'] == item_eqip['practice_code']:
                found = True
                break
        if not found:
            merged_practice_standards_filtered.append(
                {"practice_code": item_csp['practice_code'], "practice_name": item_csp['practice_name'],
                 "source": 'CSP'})

    for item_nrcs in nrcs_practice_standards_dict_list:
        found = False
        for item in merged_practice_standards_filtered:
            if item_nrcs['practice_code'] == item['practice_code']:
                found = True
                break
        if not found:
            merged_practice_standards_filtered.append(
                {"practice_code": item_nrcs['practice_code'], "practice_name": item_nrcs['practice_name'],
                 "source": 'NRCS'})

    # Add a few missing practice standards
    merged_practice_standards_filtered.append(
        {"practice_code": "OTP", "practice_name": "Other Payment", "source": "CSP"})
    merged_practice_standards_filtered.append(
        {"practice_code": "EUP", "practice_name": "Erroneous Underpayment", "source": "CSP"})
    merged_practice_standards_filtered.append(
        {"practice_code": "ERP", "practice_name": "Equitable Relief Payment", "source": "CSP"})

    nrcs_practice_standards.sort(key=lambda x: x[0])
    with open('../common/nrcs_practice_standards.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['practice_name', 'practice_unit', 'practice_code'])
        writer.writerows(nrcs_practice_standards)

    eqip_practice_standards.sort(key=lambda x: x[0])
    with open('../common/eqip_practice_standards.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['practice_code', 'practice_name'])
        writer.writerows(eqip_practice_standards)

    csp_practice_standards.sort(key=lambda x: x[0])
    with open('../common/csp_practice_standards.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['practice_code', 'practice_name'])
        writer.writerows(csp_practice_standards)

    # csp_missing_practice_standards.sort(key=lambda x: x[0])
    # with open('csp_missing_practice_standards.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['practice_code', 'practice_name'])
    #     writer.writerows(csp_missing_practice_standards)

    # csp_practice_standards_with_code.sort(key=lambda x: x[0])
    # with open('csp_practice_standards_with_matching_nrcs_code.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['practice_code', 'practice_name', 'national_practice_code'])
    #     writer.writerows(csp_practice_standards_with_code)

    # eqip_missing_practice_standards.sort(key=lambda x: x[0])
    # with open('eqip_missing_practice_standards.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['practice_code', 'practice_name'])
    #     writer.writerows(eqip_missing_practice_standards)

    # eqip_practice_standards_with_code.sort(key=lambda x: x[0])
    # with open('eqip_practice_standards_with_matching_nrcs_code.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['practice_code', 'practice_name', 'national_practice_code'])
    #     writer.writerows(eqip_practice_standards_with_code)
    #
    # csp_practice_standards_filtered.sort(key=lambda x: x['practice_code'])
    # with open('csp_practice_standards.csv', 'w') as f:
    #     writer = csv.DictWriter(f, fieldnames=['practice_code', 'practice_name'])
    #     writer.writeheader()
    #     writer.writerows(csp_practice_standards_filtered)
    #
    # eqip_practice_standards_filtered.sort(key=lambda x: x['practice_code'])
    # with open('eqip_practice_standards.csv', 'w') as f:
    #     writer = csv.DictWriter(f, fieldnames=['practice_code', 'practice_name'])
    #     writer.writeheader()
    #     writer.writerows(eqip_practice_standards_filtered)

    merged_practice_standards_filtered.sort(key=lambda x: x['practice_code'])
    with open('../common/merged_practice_standards.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['practice_code', 'practice_name', 'source'])
        writer.writeheader()
        writer.writerows(merged_practice_standards_filtered)
