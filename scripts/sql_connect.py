from sqlalchemy import create_engine, text
import pandas as pd
import mysql.connector
from sqlalchemy.types import BIGINT, VARCHAR, DATETIME


username = "root"
passwd = "password"
db_name = "healthcare"

conn = mysql.connector.connect(
   host="localhost",
   user=username,
   password="password"
   )

cursor = conn.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")

cursor.close()
conn.close()

db_url = f"mysql+pymysql://{username}:{passwd}@localhost/{db_name}"

engine = create_engine(db_url)

tables = ['pubmed.csv', 'medical_news.csv']

for table in tables:

   df = pd.read_csv(f"data/{table}")

   table_name = table.split(".")[0]

   if table_name == "covid_sum":
      with engine.connect() as conn:
         conn.execute(text("DROP TABLE covid_sum"))
         conn.commit()
      
      df['Last_Update'] = pd.to_datetime(df['Last_Update'])

   dtype_mapping = {
      "int64": "INT",
      "float64": "FLOAT",
      "object": "VARCHAR(100)",
      "datetime64[ns]": "DATE"
      }

   column_definitions = ", ".join([f"`{col}` {dtype_mapping.get(str(df[col].dtype), 'TEXT')}" for col in df.columns]) 
   create_table_sql = f"""
   CREATE TABLE IF NOT EXISTS {table_name} (
      {column_definitions}
   )
   """
   with engine.connect() as conn:
      conn.execute(text(create_table_sql))
      conn.commit()

   columns = ", ".join([f"`{col}`" for col in df.columns])
   placeholders = ", ".join([f":{col}" for col in df.columns])

   sql = text(f"""
      INSERT IGNORE INTO {table_name} ({columns})
      VALUES ({placeholders})
   """)


   # with engine.connect() as conn:
      # for _, row in df.iterrows():
      #    conn.execute(sql, {col: row[col] for col in df.columns})
      # conn.commit()

   with engine.connect() as conn:
    for _, row in df.iterrows():
        row_dict = {col: (row[col] if row[col] is not None else "") for col in df.columns}
        conn.execute(sql, row_dict)
    conn.commit()

   print(f"{table_name} is successfully inserted into MySQL without duplicates!")

df = pd.read_csv("data/covid_sum.csv")

df['Last_Update']=pd.to_datetime(df['Last_Update'], errors='coerce')

df.to_sql('covid_sum', con=engine, index=False, if_exists='replace',
         dtype={
            'Active_Cases':BIGINT(),
            'Country':VARCHAR(100),
            'Last_Updated':DATETIME(),
            'New_Cases':BIGINT(),
            'New_Deaths':BIGINT(),
            'Total_Cases':BIGINT(),
            'Total_Deaths':BIGINT(),
            'Total_Recovered':BIGINT()
         }
         )
print("Covid_Sum Updated!")