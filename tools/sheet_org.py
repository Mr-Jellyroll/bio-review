import pandas as pd

# Load the Excel file
file_path = '/Users/Shane/Documents/GitHub/bio-review/Biological-Review-Rubric-Template-Language.xlsx'
xls = pd.ExcelFile(file_path)

# Get and print sheet names
sheet_names = xls.sheet_names
print("Sheet Names:", sheet_names)

# Load the desired sheet
sheet_name = sheet_names[0]  # Replace with the actual sheet name you want
df = pd.read_excel(xls, sheet_name=sheet_name)

# Print column names
print("Column Names:", df.columns.tolist())

# Display the first few rows
print(df.head())