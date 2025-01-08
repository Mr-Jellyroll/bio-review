import pandas as pd
import re
import os
import sys

# Configuration constants
OUTPUT_DIR = os.path.expanduser('~/Documents/GitHub/bio-review/processed_data')
RULES_DIR = 'rules'  # New constant for rules directory
RULES_FILE = os.path.join(RULES_DIR, 'USFS_MSUP_Class_2.csv')  # Updated path

def get_available_files():
    """Get list of CSV and XLSX files in current directory excluding rules file"""
    all_files = os.listdir('.')
    valid_files = [f for f in all_files
                  if (f.endswith('.csv') or f.endswith('.xlsx'))
                  and f != os.path.basename(RULES_FILE)]  # Updated to use basename
    return valid_files

def process_species_records(input_csv_path, rules_csv_path=RULES_FILE):
    """Process species records from input CSV using classification rules"""
    print(f"\nReading input file: {input_csv_path}")
    print(f"Reading rules file: {rules_csv_path}")
    
    # Verify rules directory exists
    if not os.path.exists(RULES_DIR):
        raise FileNotFoundError(f"Rules directory '{RULES_DIR}' not found. Please create it and place USFS_MSUP_Class_2.csv inside.")
    
    # Verify rules file exists
    if not os.path.exists(rules_csv_path):
        raise FileNotFoundError(f"Rules file '{rules_csv_path}' not found in the rules directory.")
    
    dtypes = {
        'Review Records': str,
        'Biological Resource Review (presence/absence, resource description if appropriate)': str,
        'Biological RPMs': str
    }
    
    global rules_df
    input_df = pd.read_csv(input_csv_path, dtype=dtypes)
    rules_df = pd.read_csv(rules_csv_path, dtype=str)

# Species configurations
EXCLUDED_SPECIES = [
    'special-status fish', 'ringtail', 'California red-legged frog',
    'Sierra Nevada red fox', 'Wolverine', 'Pallid bat', 'California condor',
    'Valley elderberry longhorn beetle', 'Special-status bumble bees'
]

SPECIES_NAME_MAPPINGS = {
    'American Marten': 'Sierra marten',
    'Martes americana': 'Martes caurina sierrae',
    'mountain yellow-legged frog': 'Sierra Nevada yellow-legged frog',
    'Sierra Nevada Yellow-Legged Frog': 'Sierra Nevada yellow-legged frog',
    'Short-Leaved Hulsea': 'short-leaved hulsea',
    "Bolander's Woodreed": "Bolander's woodreed",
    'Great Gray Owl': 'great gray owl',
    'California Spotted Owl - Sierra Nevada DPS': 'California spotted owl - Sierra Nevada DPS',
    'California Spotted Owl - Coastal-Southern California DPS': 'California spotted owl - Coastal-Southern California DPS'
}

TAXON_ORDER = {
    'Invasive Plants': 1,
    'Plants': 2,
    'Plant': 2,
    'Invertebrates': 3,
    'Fish': 4,
    'Amphibian': 5,
    'Reptiles': 6,
    'Bird': 7,
    '--': 7,
    'Mammal': 8
}

def get_available_files():
    """Get list of CSV and XLSX files in current directory excluding USFS_MSUP_Class_2.csv"""
    all_files = os.listdir('.')
    valid_files = [f for f in all_files
                  if (f.endswith('.csv') or f.endswith('.xlsx'))
                  and f != 'USFS_MSUP_Class_2.csv']
    return valid_files

def display_file_options(files):
    """Display numbered list of files"""
    print("\nAvailable files:")
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file}")
    print()

def get_user_selection(files):
    """Get user's file selection"""
    while True:
        try:
            selection = int(input("Enter the number of the file you want to process: "))
            if 1 <= selection <= len(files):
                return files[selection - 1]
            else:
                print(f"Please enter a number between 1 and {len(files)}")
        except ValueError:
            print("Please enter a valid number")

def convert_xlsx_to_csv(xlsx_file):
    """Convert XLSX file to CSV"""
    print(f"\nConverting {xlsx_file} to CSV...")
    
    # Read XLSX
    df = pd.read_excel(xlsx_file)
    
    # Create CSV filename
    csv_file = xlsx_file.rsplit('.', 1)[0] + '.csv'
    
    # Save as CSV
    df.to_csv(csv_file, index=False)
    print(f"Converted to {csv_file}")
    
    return csv_file

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            raise

def clean_species_name(name):
    """Clean up species name for matching"""
    if isinstance(name, str):
        return re.sub(r'\s+', ' ', name.strip().lower())
    return ''

def standardize_species_name(species_name):
    """Standardize species names according to SNF rules"""
    if not isinstance(species_name, str):
        return species_name
        
    # Check for woodpeckers first
    if 'woodpecker' in species_name.lower():
        return '00_Woodpeckers'
        
    # Check for direct mappings
    if species_name in SPECIES_NAME_MAPPINGS:
        return SPECIES_NAME_MAPPINGS[species_name]
        
    # Check for American Marten within 500 ft
    if 'American Marten' in species_name and re.search(r'within.*?500.*?ft', species_name.lower()):
        return species_name.replace('American Marten', 'Sierra marten')
        
    return species_name

def should_process_species(species_name):
    """Check if species should be processed based on exclusion list"""
    return not any(excluded in species_name.lower() for excluded in EXCLUDED_SPECIES)

def modify_source_text(review_lang, location_info):
    """Modify review language based on which sources are present"""
    if not review_lang:
        return review_lang

    sources = []
    if 'USFS' in location_info:
        sources.append('USFS')
    if 'CNDDB' in location_info:
        sources.append('CNDDB')
    if 'SCE' in location_info:
        sources.append('SCE')

    if not sources:
        return review_lang

    source_pattern = r'Within \d+(?:\.\d+)?-mi of (?:a |an )?((?:CNDDB|USFS|SCE)(?:/(?:CNDDB|USFS|SCE))*) occurrence record(?:s)?'
    match = re.search(source_pattern, review_lang)
    
    if match:
        sources.sort()
        source_text = '/'.join(sources)
        if len(sources) == 1:
            replacement = f'Within 1-mi of a {source_text} occurrence record'
        else:
            replacement = f'Within 1-mi of {source_text} occurrence records'
            
        review_lang = re.sub(source_pattern, replacement, review_lang)

    return review_lang

def modify_review_language_for_critical_habitat(review_lang, location_info):
    """Add critical habitat text to review language if needed"""
    if 'Critical Habitat' in location_info:
        if 'Critical Habitat' not in review_lang:
            # Match text with or without colon before (habitat suitable)
            match = re.search(r'\) - Within (.*?)(:|(?=\s*\(habitat suitable\)))', review_lang)
            if match:
                original_text = match.group(1)
                modified_text = f"{original_text} and USFWS Critical Habitat"
                if ':' in match.group(0):
                    review_lang = review_lang.replace(original_text + ":", modified_text + ":")
                else:
                    review_lang = review_lang.replace(original_text, modified_text)
    return review_lang

def get_review_number(species_name, location_info, rule):
    """Determine which review language number to use"""
    species_name = clean_species_name(species_name)

    # If location_info is None, empty string, or only whitespace, return 1
    if not location_info or not location_info.strip():
        return 1

    if pd.isna(rule['Species Specific Guidance']) or rule['Species Specific Guidance'] in ['--', '', ' ']:
        return 1

    # Yosemite Toad special cases
    if 'yosemite toad' in species_name.lower():
        if 'Kaiser Pass Access' in location_info:
            return 4
        if 'SNF Occupied Unknown' in location_info:  # Check for unknown status first
            return 2
        if 'SNF Occupied' in location_info:
            return 1

    # Add California Spotted Owl handling
    if 'california spotted owl' in species_name and 'CASPO Warning Layer' in location_info:
        return 1  # Use Review Language (1) for CASPO Warning Layer

    if 'sierra nevada yellow-legged frog' in species_name and 'SNF Unknown occupied' in location_info:
        return 2

    if species_name == '00_woodpeckers':
        return 1

    if 'pacific fisher' in species_name:
        if 'Not within' in location_info and 'CBI' in location_info:
            return 4
        elif 'Within 650-ft' in location_info and 'Critical Habitat' in location_info:
            return 1
        elif 'Within CBI' in location_info and 'reproductive' in location_info.lower():
            return 2
        elif 'Within 650-ft' in location_info and 'CBI' in location_info:
            return 3

    elif 'USFS' in location_info and re.search(r'\d+\.\d+-mi', location_info):
        return 1

    return 1

def get_review_language(species, location_info, rule, original_species=None):
    """Get appropriate review language and RPM based on guidance"""
    if rule is None:
        return None, None

    review_num = get_review_number(species, location_info, rule)
    if review_num:
        review_col = f'Review Language ({review_num})'
        rpm_col = f'RPM ({review_num})'

        review = rule[review_col] if pd.notna(rule[review_col]) else None
        rpm = rule[rpm_col] if pd.notna(rule[rpm_col]) else None

        if review:
            # For woodpeckers, prepend the original species name
            if species == '00_Woodpeckers' and original_species:
                review = f"{original_species} - {review}"
            
            review = modify_source_text(review, location_info)
            review = modify_review_language_for_critical_habitat(review, location_info)
            review = modify_outside_habitat_text(review, location_info)
        
        return review, rpm
        
    return None, None

def modify_outside_habitat_text(review_lang, location_info):
    """Modify review language to handle 'Outside of' cases"""
    if 'Outside of SNF Mapped Habitat' in location_info:
        # The exact text to find and replace
        find_text = " - Within USFS Mapped Suitable Habitat and access"
        replace_text = " - Outside of USFS Mapped Habitat - Access"
        
        if find_text in review_lang:
            review_lang = review_lang.replace(find_text, replace_text)

        
        if find_text in review_lang:
            review_lang = review_lang.replace(find_text, replace_text)
    
    return review_lang

def process_single_record(review_records):
    """Process a single review records entry"""
    if pd.isna(review_records) or not review_records:
        return None, None

    # Use dictionaries to group both reviews and RPMs by taxon
    taxon_groups = {taxon: [] for taxon in TAXON_ORDER.keys()}
    taxon_rpms = {taxon: set() for taxon in TAXON_ORDER.keys()}  # New dictionary for RPMs by taxon

    for line in review_records.split('\n'):
        if not line.strip():
            continue
            
        # Clean up line by removing "Done - " or "DONE - " prefixes
        line = re.sub(r'^(?:Done|DONE)\s*-\s*', '', line.strip())

        # Handle California Spotted Owl special case first
        if 'California Spotted Owl' in line and ' - ' in line:
            parts = line.split(' - ')
            original_species = (parts[0] + ' - ' + parts[1]).strip()
            location = ' - '.join(parts[2:]) if len(parts) > 2 else ''
        else:
            # Handle all other cases
            parts = line.split(' - ', 1)
            if len(parts) == 1:
                original_species = parts[0].strip()
                location = ''
            else:
                original_species = parts[0].strip()
                location = parts[1].strip()

        standardized_species = standardize_species_name(original_species)
        
        if not should_process_species(standardized_species):
            continue
            
        matching_rules = rules_df[rules_df['Species'].apply(lambda x:
            clean_species_name(x) == clean_species_name(standardized_species))]
            
        if not matching_rules.empty:
            rule = matching_rules.iloc[0]
            review_lang, rpm = get_review_language(standardized_species, location, rule, original_species=original_species)
            taxon = rule['Taxon']
                
            if review_lang and pd.notna(review_lang):
                if taxon in taxon_groups:
                    taxon_groups[taxon].append(review_lang)
                    
            if rpm and pd.notna(rpm):
                rpms = [r.strip() for r in rpm.split(';') if r.strip()]
                if taxon in taxon_rpms:
                    taxon_rpms[taxon].update(rpms)

    # Combine reviews in taxonomic order
    reviews = []
    rpms_ordered = []  # New list for ordered RPMs
    
    for taxon in sorted(taxon_groups.keys(), key=lambda x: TAXON_ORDER[x]):
        if taxon_groups[taxon]:
            reviews.extend(taxon_groups[taxon])
        # Add RPMs from this taxon
        if taxon_rpms[taxon]:
            rpms_ordered.extend(sorted(taxon_rpms[taxon]))  # Sort RPMs within each taxon
    
    final_review = None
    if reviews:
        final_review = 'POTENTIAL TO OCCUR:\n' + '\n\n'.join(reviews)
    
    final_rpms = None
    if rpms_ordered:  # Using the ordered RPMs list
        # Remove any General Measures that might be in the middle
        rpms_ordered = [rpm for rpm in rpms_ordered if 'General Measures and Standard OMP BMPs' not in rpm]
        # Add General Measures at the end
        rpms_ordered.append('General Measures and Standard OMP BMPs.')
        final_rpms = ';\n'.join(rpms_ordered)
    
    return final_review, final_rpms

def process_species_records(input_csv_path, rules_csv_path=RULES_FILE):
    """Process species records from input CSV using classification rules"""
    print(f"\nReading input file: {input_csv_path}")
    print(f"Reading rules file: {rules_csv_path}")
    
    dtypes = {
        'Review Records': str,
        'Biological Resource Review (presence/absence, resource description if appropriate)': str,
        'Biological RPMs': str
    }
    
    global rules_df
    input_df = pd.read_csv(input_csv_path, dtype=dtypes)
    rules_df = pd.read_csv(rules_csv_path, dtype=str)
    
    results = []
    for idx, row in input_df.iterrows():
        print(f"Processing record {idx + 1}...")
        review, rpms = process_single_record(row['Review Records'])
        results.append({
            'Biological Resource Review (presence/absence, resource description if appropriate)': review if review else '',
            'Biological RPMs': rpms if rpms else ''
        })
    
    results_df = pd.DataFrame(results)
    output_df = input_df.copy()
    output_df['Biological Resource Review (presence/absence, resource description if appropriate)'] = results_df['Biological Resource Review (presence/absence, resource description if appropriate)']
    output_df['Biological RPMs'] = results_df['Biological RPMs']
    
    return output_df

if __name__ == '__main__':
    print(f"\nStarting species record processing...")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        # Get and display available files
        available_files = get_available_files()
        
        if not available_files:
            print("No CSV or XLSX files found in the current directory")
            sys.exit(1)
            
        display_file_options(available_files)
        selected_file = get_user_selection(available_files)
        
        # Handle file based on type
        input_file = selected_file
        if selected_file.endswith('.xlsx'):
            input_file = convert_xlsx_to_csv(selected_file)
        
        # Create output filename
        output_filename = os.path.basename(input_file).rsplit('.', 1)[0] + '_processed.csv'
        output_file = os.path.join(OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        ensure_output_directory()
        
        # Process the data
        result_df = process_species_records(input_file)
        
        # Save results
        print(f"Saving results to: {os.path.abspath(output_file)}")
        result_df.to_csv(output_file, index=False)
        print("Processing completed successfully!")
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        print("\nPlease ensure:")
        print(f"1. The 'rules' directory exists in the current working directory")
        print(f"2. The USFS_MSUP_Class_2.csv file is inside the 'rules' directory")
        print(f"3. Your input file exists and is readable")
        print(f"4. You have write permissions for the output directory")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("Please check that:")
        print(f"1. Your input file has a 'Review Records' column")
        print(f"2. The input file format is correct")
        print(f"3. You have sufficient permissions for all operations")