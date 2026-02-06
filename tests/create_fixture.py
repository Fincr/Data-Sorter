"""Helper script to create the sample_input.xlsx fixture."""

import pandas as pd
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_input.xlsx"


def create_sample_input():
    data = [
        # Dublin districts — LETTERSHOP
        {"First Name": "Alice", "Last Name": "Murphy", "Address Line 1": "123 O'Connell St", "Address Line 2": "", "City": "Dublin 1", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Bob", "Last Name": "Kelly", "Address Line 1": "45 Grafton St", "Address Line 2": "", "City": "Dublin 2", "County": "Dublin", "Postcode": "D02 YX88", "Country": "Ireland"},
        {"First Name": "Claire", "Last Name": "Walsh", "Address Line 1": "Apt 3, Block B", "Address Line 2": "Ballymun", "City": "Dublin 10", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        {"First Name": "David", "Last Name": "Ryan", "Address Line 1": "7 Rathgar Road", "Address Line 2": "", "City": "Dublin 6W", "County": "Dublin", "Postcode": "D6W AB12", "Country": "Ireland"},
        {"First Name": "Emma", "Last Name": "O'Brien", "Address Line 1": "22 Phibsborough Rd", "Address Line 2": "", "City": "Dublin 7", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Fiona", "Last Name": "Byrne", "Address Line 1": "15 Talbot St", "Address Line 2": "", "City": "Dublin 1", "County": "Dublin", "Postcode": "D01 XY34", "Country": "Ireland"},
        # Compact format — no space
        {"First Name": "Gary", "Last Name": "Doyle", "Address Line 1": "Unit 8", "Address Line 2": "Dublin15", "City": "", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        # Lettershop named areas
        {"First Name": "Helen", "Last Name": "Nolan", "Address Line 1": "10 Main St", "Address Line 2": "Blackrock", "City": "", "County": "Dublin", "Postcode": "A94 XY12", "Country": "Ireland"},
        {"First Name": "Ian", "Last Name": "Casey", "Address Line 1": "5 Castle Ave", "Address Line 2": "Swords", "City": "", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Jane", "Last Name": "Brennan", "Address Line 1": "3 Marine Rd", "Address Line 2": "Dún Laoghaire", "City": "", "County": "Dublin", "Postcode": "", "Country": "Ireland"},
        # National areas
        {"First Name": "Kevin", "Last Name": "Lynch", "Address Line 1": "78 Patrick St", "Address Line 2": "", "City": "Cork", "County": "Co. Cork", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Laura", "Last Name": "Gallagher", "Address Line 1": "12 Shop Street", "Address Line 2": "", "City": "Galway", "County": "Co. Galway", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Mike", "Last Name": "Daly", "Address Line 1": "56 Tralee Rd", "Address Line 2": "", "City": "", "County": "Co. Kerry", "Postcode": "", "Country": "Ireland"},
        {"First Name": "Niamh", "Last Name": "Healy", "Address Line 1": "9 Main St", "Address Line 2": "Killarney", "City": "", "County": "Co. Kerry", "Postcode": "", "Country": "Ireland"},
        # Exception — empty address
        {"First Name": "Oscar", "Last Name": "Flynn", "Address Line 1": "", "Address Line 2": "", "City": "", "County": "", "Postcode": "", "Country": "Ireland"},
        # Exception — no country, no recognizable area
        {"First Name": "Pat", "Last Name": "Quinn", "Address Line 1": "12345 Unknown Place", "Address Line 2": "", "City": "", "County": "", "Postcode": "", "Country": ""},
        # Ireland Other fallback — Ireland country but vague address
        {"First Name": "Rachel", "Last Name": "Smith", "Address Line 1": "Rural Townland", "Address Line 2": "", "City": "", "County": "", "Postcode": "", "Country": "Ireland"},
    ]

    df = pd.DataFrame(data)
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(FIXTURE_PATH, index=False, engine="openpyxl")
    print(f"Created: {FIXTURE_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    create_sample_input()
