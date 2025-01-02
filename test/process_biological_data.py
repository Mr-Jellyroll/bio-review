import pandas as pd

# Read the Excel sheets
template_df = pd.read_excel('SheetA.xlsx')  # Template language sheet
data_df = pd.read_excel('SheetC.xlsx')      # Data sheet

def process_review_records(review_records, template_df):
    # Split the review records by newline to get individual species
    species_list = [s.strip().split('-')[0].strip() for s in review_records.split('\n')]
    
    # Initialize output strings
    review_output = "POTENTIAL TO OCCUR:\n"
    rpm_output = ""
    
    # Process each species
    for species in species_list:
        # Find matching template row (case-insensitive)
        template_match = template_df[template_df['species'].str.lower() == species.lower()]
        
        if not template_match.empty:
            # Add review language
            review_language = template_match.iloc[0]['review language']
            review_output += f"{review_language}\n\n"
            
            # Add RPMs
            rpm = template_match.iloc[0]['rpm']
            if rpm_output:
                rpm_output += f"; {rpm}"
            else:
                rpm_output += rpm
    
    return review_output.strip(), rpm_output

# Process each row in data_df
results = []
for index, row in data_df.iterrows():
    review_text, rpm_text = process_review_records(row['Review Records'], template_df)
    results.append({
        'Biological Resource Review': review_text,
        'Biological RPMs': rpm_text
    })

# Create output dataframe
output_df = pd.DataFrame(results)

# Save to new Excel file or update existing file
output_df.to_excel('output.xlsx', index=False)