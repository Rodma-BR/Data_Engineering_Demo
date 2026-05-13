# Delete History

import argparse
import datetime as dt
from dateutil.relativedelta import relativedelta

parser = argparse.ArgumentParser(description='Parser test')
parser.add_argument("--uc_catalog", type = str, help = 'Choose UC Catalog to use', default = "Momentum")
parser.add_argument("--uc_schema", type = str, help = 'Choose UC Schema to use')
parser.add_argument("--uc_table", type = str, help = 'Choose UC Table to use')
parser.add_argument("--days", type = int, help = 'Delete all data until "n" days before today', default = 0)
parser.add_argument("--months", type = int, help = 'Delete all data until "n" months before today', default = 0)
parser.add_argument("--years", type = int, help = 'Delete all data until "n" years before today', default = 0)
args = parser.parse_args()

uc_catalog = args.uc_catalog.lower()
uc_schema = args.uc_schema.lower()
uc_table = args.uc_table.lower()
days = int(args.days)
months = int(args.months)
years = int(args.years)

uc_table_full = f"{uc_catalog}.{uc_schema}.{uc_table}"

print(uc_table_full)

if spark.catalog.tableExists(uc_table_full) == False:
    print("Table doesn't exists")

else:

    print(f"Delete until {days} days, {months} months and {years} years")

    if (days == 0) and (months == 0) and (years == 0):

        spark.sql(f"DELETE FROM {uc_table_full}")
        assert spark.table(uc_table_full).count() == 0
        print("Deleted All data")

    today = dt.datetime.now().date()
    last_date = today - relativedelta(days = days, months= months, years = years)
    last_date = last_date.strftime("%Y-%m-%d")
    print(last_date)

    before = spark.table(uc_table_full).count()

    spark.sql(f"""DELETE FROM {uc_table_full} WHERE Evaluated_Date <= '{last_date}'""")

    after =  spark.table(uc_table_full).count()

    print(f"{before} Records before operation, {after}  records after operation")