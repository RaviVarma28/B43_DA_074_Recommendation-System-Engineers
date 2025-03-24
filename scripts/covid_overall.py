import pandas as pd
from httpx import get
import numpy as np

def get_stats_covid():
    
    resp = get("https://covid-19.dataflowkit.com/v1")

    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())

        num_cols = ['Active Cases_text', 'New Cases_text', 'New Deaths_text', 'Total Cases_text', 'Total Deaths_text', 'Total Recovered_text']

        for col in num_cols:
            df[col]=pd.to_numeric(df[col].map(lambda x: x.strip().replace(",","") if isinstance(x, str) else x), errors='coerce')

        df.loc[0, 'Active Cases_text'] = df['Active Cases_text'].sum()
        df['Last Update'] = pd.to_datetime(df['Last Update'], errors='coerce')
        df.columns = ["_".join(i.split()) for i in df.columns.str.replace("_text","")]

        print("Extraction Complete!")
        return df
    else:
        raise Exception(f"Something went wrong! Status code: {resp.status_code}")

if __name__ == '__main__':
    df = get_stats_covid()

    df.to_csv("data/covid_sum.csv", index=False)