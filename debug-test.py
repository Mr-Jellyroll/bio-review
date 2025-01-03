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
    'Plant': 2,
    'Invertebrates': 3,
    'Fish': 4,
    'Amphibian': 5,
    'Reptiles': 6,
    'Bird': 7,
    '--': 7,
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
    return not any(excluded in species_name.lower() for excluded in EXCLUDED_SPECIES)

def modify_source_text(review_lang, location_info):
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
    
    if pd.isna(rule['Species Specific Guidance']) or rule['Species Specific Guidance'] in ['--', '', ' ']:
        return 1
    
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
            
    elif 'yosemite toad' in species_name:
        if 'SNF Occupied' in location_info:
            return 1
            
    elif 'USFS' in location_info and re.search(r'\d+\.\d+-mi', location_info):
        return 1
        
    return 1

def get_review_language(species, location_info, rule, original_species=None):
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
        
        return review, rpm
        
    return None, None

def process_single_record(review_records):
    if pd.isna(review_records) or not review_records:
        return None, None
        
    taxon_groups = {taxon: [] for taxon in TAXON_ORDER.keys()}
    rpms_set = set()
    
    for line in review_records.split('\n'):
        if not line.strip():
            continue
            
        if ' - ' in line:
            species, location = line.split(' - ', 1)
            original_species = species.strip()
            standardized_species = standardize_species_name(original_species)
            location = location.strip()
            
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
                    rpms_set.update(rpms)
    
    reviews = []
    for taxon in sorted(taxon_groups.keys(), key=lambda x: TAXON_ORDER[x]):
        if taxon_groups[taxon]:
            reviews.extend(taxon_groups[taxon])
    
    final_review = None
    if reviews:
        final_review = 'POTENTIAL TO OCCUR:\n' + '\n\n'.join(reviews)
    
    final_rpms = None
    if rpms_set:
        rpms_list = sorted(list(rpms_set))
        rpms_list = [rpm for rpm in rpms_list if 'General Measures and Standard OMP BMPs' not in rpm]
        rpms_list.append('General Measures and Standard OMP BMPs.')
        final_rpms = ';\n'.join(rpms_list)
    
    return final_review, final_rpms

def process_species_records(input_csv_path, rules_csv_path=RULES_FILE):
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
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'Test.csv'
    output_filename = os.path.basename(input_file).rsplit('.', 1)[0] + '_processed.csv'
    output_file = os.path.join(OUTPUT_DIR, output_filename)
    
    print(f"\nStarting species record processing...")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        ensure_output_directory()
        result_df = process_species_records(input_file)
        print(f"Saving results to: {os.path.abspath(output_file)}")
        result_df.to_csv(output_file, index=False)
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("Please check that:")
        print(f"1. Your input CSV file exists and is readable")
        print(f"2. The '{RULES_FILE}' file is in the same directory")
        print(f"3. The input CSV has a 'Review Records' column")
        print(f"4. You have write permissions for the output directory")