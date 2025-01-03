import pandas as pd
import re
import os

# Configuration constants
OUTPUT_DIR = os.path.expanduser('~/Documents/GitHub/bio-review/processed_data')
RULES_FILE = 'USFS_MSUP_Class_2.csv'

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
    'Great Gray Owl': 'great gray owl'
}

TAXON_ORDER = {
    'Invasive Plants': 1,
    'Plants': 2,
    'Plant': 2,  # Add this since some use 'Plant' instead of 'Plants'
    'Invertebrates': 3,
    'Fish': 4,
    'Amphibian': 5,
    'Reptiles': 6,
    'Bird': 7,
    '--': 7,  # Add this for woodpeckers
    'Mammal': 8
}

def ensure_output_directory():
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            raise

def clean_species_name(name):
    if isinstance(name, str):
        return re.sub(r'\s+', ' ', name.strip().lower())
    return ''

def standardize_species_name(species_name):
    if not isinstance(species_name, str):
        return species_name
        
    # Check for woodpeckers first (including Acorn Woodpecker)
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
    return not any(excluded in species_name.lower() for excluded in EXCLUDED_SPECIES)

def modify_source_text(review_lang, location_info):
    if not review_lang:
        return review_lang

    # Identify present sources
    sources = []
    if 'USFS' in location_info:
        sources.append('USFS')
    if 'CNDDB' in location_info:
        sources.append('CNDDB')
    if 'SCE' in location_info:
        sources.append('SCE')

    if not sources:
        return review_lang

    # Create pattern to match any combination of the sources
    source_pattern = r'Within \d+(?:\.\d+)?-mi of (?:a |an )?((?:CNDDB|USFS|SCE)(?:/(?:CNDDB|USFS|SCE))*) occurrence record(?:s)?'
    match = re.search(source_pattern, review_lang)
    
    if match:
        # Sort sources to ensure consistent ordering
        sources.sort()  # This will put CNDDB before USFS alphabetically
        
        # Build the replacement text
        source_text = '/'.join(sources)
        if len(sources) == 1:
            replacement = f'Within 1-mi of a {source_text} occurrence record'
        else:
            replacement = f'Within 1-mi of {source_text} occurrence records'
            
        # Replace the old source text with the new one
        review_lang = re.sub(source_pattern, replacement, review_lang)

    return review_lang

def modify_review_language_for_critical_habitat(review_lang, location_info):
    if 'Critical Habitat' in location_info:
        if 'Critical Habitat' not in review_lang:
            match = re.search(r'\) - Within ([^:]+):', review_lang)
            if match:
                original_text = match.group(1)
                modified_text = f"{original_text} and USFWS Critical Habitat"
                review_lang = review_lang.replace(original_text + ":", modified_text + ":")
    return review_lang

def get_review_number(species_name, location_info, rule):
    species_name = clean_species_name(species_name)
    
    # If Species Specific Guidance is empty/blank, use Review Language (1)
    if pd.isna(rule['Species Specific Guidance']) or rule['Species Specific Guidance'] in ['--', '', ' ']:
        return 1
    
    # Handle Sierra Nevada Yellow-Legged Frog with SNF Unknown occupied
    if 'sierra nevada yellow-legged frog' in species_name and 'SNF Unknown occupied' in location_info:
        return 2
        
    # Handle Woodpecker cases - both inside and outside polygon
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
            
    elif 'yosemite toad' in species_name:
        if 'SNF Occupied' in location_info:
            return 1
            
    elif 'USFS' in location_info and re.search(r'\d+\.\d+-mi', location_info):
        return 1
        
    return 1  # Default to Review Language (1)

def get_review_language(species, location_info, rule):
    if rule is None:
        return None, None
        
    review_num = get_review_number(species, location_info, rule)
    if review_num:
        review_col = f'Review Language ({review_num})'
        rpm_col = f'RPM ({review_num})'
        
        review = rule[review_col] if pd.notna(rule[review_col]) else None
        rpm = rule[rpm_col] if pd.notna(rule[rpm_col]) else None
        
        # Apply both modifications if review exists
        if review:
            # First modify based on sources present
            review = modify_source_text(review, location_info)
            # Then add critical habitat if needed
            review = modify_review_language_for_critical_habitat(review, location_info)
        
        return review, rpm
        
    return None, None

def process_single_record(review_records):
    """Process a single review records entry with debug output"""
    if pd.isna(review_records) or not review_records:
        return None, None
        
    print("\nDEBUG: Processing Review Records:")
    print(review_records)
        
    # Initialize taxonomic grouping with all possible taxa
    taxon_groups = {taxon: [] for taxon in TAXON_ORDER.keys()}
    rpms_set = set()
    
    # Process each species record
    for line in review_records.split('\n'):
        if not line.strip():
            continue
            
        if ' - ' in line:
            species, location = line.split(' - ', 1)
            original_species = species.strip()
            standardized_species = standardize_species_name(original_species)
            location = location.strip()
            
            print(f"\nDEBUG: Processing species:")
            print(f"Original: {original_species}")
            print(f"Standardized: {standardized_species}")
            
            # Skip excluded species
            if not should_process_species(standardized_species):
                print(f"DEBUG: Skipping excluded species: {standardized_species}")
                continue
                
            # Find matching rule
            print("DEBUG: Looking for matching rule...")
            matching_rules = rules_df[rules_df['Species'].apply(lambda x: 
                clean_species_name(x) == clean_species_name(standardized_species))]
            
            if not matching_rules.empty:
                rule = matching_rules.iloc[0]
                print(f"DEBUG: Found matching rule with species: {rule['Species']}")
                print(f"DEBUG: Species Specific Guidance: {rule['Species Specific Guidance']}")
                
                review_lang, rpm = get_review_language(standardized_species, location, rule)
                print(f"DEBUG: Got review language: {review_lang}")
                
                taxon = rule['Taxon']
                print(f"DEBUG: Taxon: {taxon}")
                
                if review_lang and pd.notna(review_lang):
                    if taxon not in taxon_groups:
                        print(f"DEBUG: Warning: Unknown taxon {taxon}")
                        continue
                    taxon_groups[taxon].append(review_lang)
                    print(f"DEBUG: Added review language to taxon group {taxon}")
                    
                if rpm and pd.notna(rpm):
                    rpms = [r.strip() for r in rpm.split(';') if r.strip()]
                    rpms_set.update(rpms)
                    print(f"DEBUG: Added RPMs: {rpms}")
            else:
                print(f"DEBUG: No matching rule found for species: {standardized_species}")
    
    print("\nDEBUG: Final taxon groups:")
    for taxon, reviews in taxon_groups.items():
        print(f"{taxon}: {len(reviews)} reviews")
    
    # Combine reviews in taxonomic order
    reviews = []
    for taxon in sorted(taxon_groups.keys(), key=lambda x: TAXON_ORDER[x]):
        if taxon_groups[taxon]:
            reviews.extend(taxon_groups[taxon])
    
    # Format final review and RPMs
    final_review = None
    if reviews:
        final_review = 'POTENTIAL TO OCCUR:\n' + '\n\n'.join(reviews)
    
    final_rpms = None
    if rpms_set:
        rpms_list = sorted(list(rpms_set))
        rpms_list = [rpm for rpm in rpms_list if 'General Measures and Standard OMP BMPs' not in rpm]
        rpms_list.append('General Measures and Standard OMP BMPs.')
        final_rpms = ';\n'.join(rpms_list)
    
    print("\nDEBUG: Final outputs:")
    print(f"Has review: {bool(final_review)}")
    print(f"Has RPMs: {bool(final_rpms)}")
    
    return final_review, final_rpms

def process_species_records(input_csv_path, rules_csv_path=RULES_FILE):
    print(f"\nReading input file: {input_csv_path}")
    print(f"Reading rules file: {rules_csv_path}")
    
    # Read CSVs with explicit string types for key columns
    dtypes = {
        'Review Records': str,
        'Biological Resource Review (presence/absence, resource description if appropriate)': str,
        'Biological RPMs': str
    }
    
    global rules_df
    input_df = pd.read_csv(input_csv_path, dtype=dtypes)
    rules_df = pd.read_csv(rules_csv_path, dtype=str)
    
    # Process all records
    results = []
    for idx, row in input_df.iterrows():
        print(f"\nProcessing record {idx + 1}...")
        review, rpms = process_single_record(row['Review Records'])
        results.append({
            'Biological Resource Review (presence/absence, resource description if appropriate)': review if review else '',
            'Biological RPMs': rpms if rpms else ''
        })
        print(f"Generated review: {bool(review)}")
        print(f"Generated RPMs: {bool(rpms)}")
    
    # Create output DataFrame
    results_df = pd.DataFrame(results)
    output_df = input_df.copy()
    
    # Update columns
    output_df['Biological Resource Review (presence/absence, resource description if appropriate)'] = results_df['Biological Resource Review (presence/absence, resource description if appropriate)']
    output_df['Biological RPMs'] = results_df['Biological RPMs']
    
    return output_df

if __name__ == '__main__':
    import sys
    
    # Get input file from command line argument or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'Test.csv'
    
    # Create output filename in the specified directory
    output_filename = os.path.basename(input_file).rsplit('.', 1)[0] + '_processed.csv'
    output_file = os.path.join(OUTPUT_DIR, output_filename)
    
    print(f"\nStarting species record processing...")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        # Ensure output directory exists
        ensure_output_directory()
        
        # Process the data
        result_df = process_species_records(input_file)
        
        # Save results
        print(f"\nSaving results to: {os.path.abspath(output_file)}")
        result_df.to_csv(output_file, index=False)
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nPlease check that:")
        print(f"1. Your input CSV file exists and is readable")
        print(f"2. The '{RULES_FILE}' file is in the same directory")
        print(f"3. The input CSV has a 'Review Records' column")
        print(f"4. You have write permissions for the output directory")