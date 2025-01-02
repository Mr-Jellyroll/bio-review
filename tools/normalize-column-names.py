import pandas as pd

# Load the data
sheet_a = pd.read_excel("/Users/Shane/Documents/GitHub/bio-review/Biological-Review-Rubric-Template-Language.xlsx", sheet_name="USFS MSUP (Class II)")  # Replace with your sheet name

# Normalize column names
sheet_a.columns = sheet_a.columns.str.strip().str.lower()

# Print normalized column names
print(sheet_a.columns)
