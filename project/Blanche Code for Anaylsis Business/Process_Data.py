import pandas as pd
import re

from openpyxl.styles.builtins import currency


class DataProcessor():
    def __init__(self):
        self.currency_rates = {
            '$': 83.5 ,  # USD to INR
            '€': 89.2 ,  # EUR to INR
            '£': 105.3 ,  # GBP to INR
            '₹': 1  # INR
        }

    def extract_year(sel, text):
        year_match = re.search(r'(?:19|20\d{2)', str(text))
        return int(year_match.group()) if year_match else None

    def _convert_to_inr(self,value):
        if pd.ins(value):
            return None

        match = re.search((r'([₹$€£])\s*(\d[\d,.]*)'), str(value))
        if match:
            currency = match.group(1)
            amount = float(match.group(2).replace(',',''))
            return amount * self.currency_rates[currency]

        try:
            return float(str(value).replace(',',''))
        except:
            return None


    def process(self, filepath):
        if filepath.endswitch('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath)


        df['Year'] = df['Year'].apply(self._extract_year)
        df['Total_INR'] = df['Total'].apply(self.convert_to_inr)

        df = df.dropna(subset=['Year', 'Total_INR','Service ID'])

        return df[['Year', 'Service ID', 'Category', 'Total_INR']]




