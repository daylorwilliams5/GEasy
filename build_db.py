
import duckdb, os
DB_PATH = os.environ.get("GEASY_DB_PATH", "geasy.duckdb")
DATA_DIR = os.environ.get("GEASY_DATA_DIR", "data")
con = duckdb.connect(DB_PATH)
con.execute(open("schema.sql","r", encoding="utf-8").read())
for name in ["courses","professors","sections","reviews"]:
    con.execute(f"CREATE OR REPLACE TEMP VIEW src AS SELECT * FROM read_csv_auto('{DATA_DIR}/{name}.csv', header=True)")
    con.execute(f"INSERT OR REPLACE INTO {name} SELECT * FROM src")
print(f"Built DuckDB at {DB_PATH}")
