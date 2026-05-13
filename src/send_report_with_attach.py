import pyspark.sql.functions as F
import pyspark.sql.types as T
#from pyspark.sql.window import Window
import sys
#import importlib
import json
from email.message import EmailMessage
import smtplib
import pickle
import os

# Append the directory to sys.path
# sys.path.append("../utils")
# import qa_bimbo.general_functions as gf

import argparse
parser = argparse.ArgumentParser(description='Parser test')
parser.add_argument("--job_run_id", type = str, help = 'Job run id')
parser.add_argument("--task_run_id", type = str, help = 'Task run id')
parser.add_argument("--emails", type = str, help = 'List of emails separated by semicolon')
parser.add_argument("--subject", type = str, help = 'Email subject')
parser.add_argument("--message", type = str, help = 'Email message')
parser.add_argument("--evaluated_date", type = str, help = 'Date to evaluate')
parser.add_argument("--workspace_id", type = int, help = 'Databricks workspace id')
args = parser.parse_args()

# Get task arguments
job_run_id = args.job_run_id
task_run_id = args.task_run_id
emails = args.emails
subject = args.subject
message = args.message
arg_status = args.argentina_status
evaluated_date = args.evaluated_date
workspace_id = args.workspace_id
layer = "Curated"

workspace_name = {: "Dev", : "Prod"}
print("Databricks workspace", workspace_id)


if (evaluated_date == '') or (evaluated_date == None):
    evaluated_date = F.current_date()

# Global parameters
start_time = spark.range(1).select(F.current_timestamp()).collect()[0][0]
today = spark.range(1).select(F.current_date()).collect()[0][0]

temporal_files = {"bugs_info_report" : {"temporal_file_path" : "../temporal/curated/temporal_processes_report.csv", "temporal_file_name" : f"Bugs_Info_{today}.csv"}
                  }

#print(arg_status)

#################
# Files to attach
#################

# Count By Date
# Read count by day table and generate attachment file
df_count_tables = spark.table("")\
    .filter((F.col("Evaluated_Date") == evaluated_date) & (F.col("Sql_Source") == "Sql_Server"))
df_count_tables.toPandas().to_csv(temporal_files["count_tables"]["temporal_file_path"], index=False)

###############
# Create report
###############

# Read bugs info table and generate HTML to send in email body
bugs_info = spark.table("").filter( (F.col("Evaluated_Date") == evaluated_date) & (F.col("Layer") == layer)).orderBy("Process_Name", "Country", "Table_Name")
bugs_info.toPandas().to_csv(temporal_files["bugs_info_report"]["temporal_file_path"], index=False)

summary_report = bugs_info.groupBy("Country", "Layer", "Process_Name").agg(F.sum("Is_Ok").alias("Total_Tables_Ok"),
                                                          F.sum("Has_Warnings").alias("Total_Tables_Warned"),
                                                          F.sum("Has_Bugs").alias("Total_Tables_Bugged"),
                                                          F.max("Evaluated_Date").alias("Evaluated_Date")
                                                          ).withColumn("Process_Order", F.col("Process_Name"))
                                                        
body_table = gf.df_to_html(summary_report)

#ext.logic_app_email_sender(send_to_ = [emails], subject_ = subject, message_ = f"{country} | " + message , body_table_ = body_table , run_id_ = task_run_id)
with open('./pss.pkl', 'rb') as file:
    p = pickle.load(file)

remitente = ""
destinatario = emails.split(";")
#print(emails, destinatario)
mensaje = f"""<html> 
    <head> 
    <style> #Data_Table {{ font-family: Arial, Helvetica, sans-serif; border-collapse: collapse; width: 100%; }} #Data_Table td, #Data_Table th {{   border: 1px solid #ddd;   padding: 8px; }} #Data_Table tr:nth-child(even) {{background-color: #f2f2f2;}} #Data_Table tr:hover {{background-color: #ddd;}} #Data_Table th {{   padding-top: 12px;   padding-bottom: 12px;   text-align: left;   background-color: #e3e320;   color: white; }} #Mensaje {{ background: # 064; color: #FFFFFF; }} 
    </style> 
    </head>
    <body>
    <table id='Data_Table'>
    {body_table}
    </table> 
    <div id='Mensaje'> <br>
    {message}
    <br>
    </div> 
    </body> 
    </html>"""
email = EmailMessage()
email["From"] = remitente
email["To"] = destinatario
email["Subject"] = subject.replace("@ambiente", workspace_name.get(workspace_id))
email.set_content(mensaje, subtype="html")
for process in temporal_files.keys():
    with open(temporal_files[process]["temporal_file_path"], "rb") as f:
        email.add_attachment(
            f.read(),
            filename=temporal_files[process]["temporal_file_name"],
            maintype="application",
            subtype="csv"
        )
        
smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
smtp.starttls()
smtp.login(remitente, "password")
smtp.sendmail(remitente, destinatario, email.as_string())
smtp.quit()

for process in temporal_files.keys():
    try:   
        os.remove(temporal_files[process]["temporal_file_path"])
    except OSError as error:
        print(error)
        print(f"File {temporal_files[process]["temporal_file_path"]} path can not be removed")

print("Succeded!")




