import pandas as pd
import re
import os

# Configuration constants
OUTPUT_DIR = os.path.expanduser('~/Documents/GitHub/bio-review/processed_data')
RULES_FILE = 'USFS_MSUP_Class_2.csv'  # Updated rules file name

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            raise

def process_species_records(input_csv_path, rules_csv_path=RULES_FILE):
    """Process species records"""
    print(f"\nReading input file: {input_csv_path}")
    print(f"Reading rules file: {rules_csv_path}")
    
    input_df = pd.read_csv(input_csv_path, dtype=str)
    rules_df = pd.read_csv(rules_csv_path, dtype=str)
    
    def clean_species_name(name):
        if isinstance(name, str):
            return re.sub(r'\s+', ' ', name.strip().lower())
        return ''

    def find_matching_species(species_name):
        species_name = clean_species_name(species_name)
        matching_rules = rules_df[rules_df['Species'].apply(clean_species_name) == species_name]
        return matching_rules.iloc[0] if not matching_rules.empty else None

    def get_review_number(species_name, location_info, rule):
        """Determine which review language number to use based on location and guidance"""
        species_name = clean_species_name(species_name)
        
        # Pacific Fisher specific logic
        if species_name == 'pacific fisher':
            if 'Not within' in location_info and 'CBI' in location_info:
                return 4
            elif 'Within 650-ft' in location_info and 'Critical Habitat' in location_info:
                return 1
            elif 'Within CBI' in location_info and 'reproductive' in location_info.lower():
                return 2
            elif 'Within 650-ft' in location_info and 'CBI' in location_info:
                return 3
                
        # Yosemite Toad specific logic
        if species_name == 'yosemite toad':
            if 'SNF Occupied' in location_info and 'Critical Habitat' in location_info:
                return 1
                
        # Default USFS occurrence logic
        if 'USFS' in location_info and re.search(r'\d+\.\d+-mi', location_info):
            return 1
            
        return None

    def match_review_language(species_name, location_info, rule):
        """Get appropriate review language and RPM based on guidance"""
        if rule is None:
            return None, None
            
        review_num = get_review_number(species_name, location_info, rule)
        if review_num:
            review_col = f'Review Language ({review_num})'
            rpm_col = f'RPM ({review_num})'
            
            review = rule[review_col] if pd.notna(rule[review_col]) else None
            rpm = rule[rpm_col] if pd.notna(rule[rpm_col]) else None
            
            return review, rpm
            
        return None, None

    def process_single_record(review_records):
        """Process a single review records entry"""
        if pd.isna(review_records) or not review_records:
            return None, None
            
        taxon_groups = {
            'Amphibian': [],
            'Bird': [],
            'Mammal': []
        }
        
        rpms_set = set()
        
        for line in review_records.split('\n'):
            if not line.strip():
                continue
                
            if ' - ' in line:
                species, location = line.split(' - ', 1)
                species = species.strip()
                location = location.strip()
                
                rule = find_matching_species(species)
                if rule is not None:
                    review_lang, rpm = match_review_language(species, location, rule)
                    taxon = rule['Taxon']
                    
                    if review_lang and pd.notna(review_lang):
                        if taxon not in taxon_groups:
                            taxon_groups[taxon] = []
                        taxon_groups[taxon].append(review_lang)
                        
                    if rpm and pd.notna(rpm):
                        rpms = [r.strip() for r in rpm.split(';') if r.strip()]
                        rpms_set.update(rpms)
        
        # Combine reviews in taxonomic order
        reviews = []
        for taxon in ['Amphibian', 'Bird', 'Mammal']:
            if taxon_groups.get(taxon):
                reviews.extend(taxon_groups[taxon])
        
        # Format final review
        final_review = None
        if reviews:
            final_review = 'POTENTIAL TO OCCUR:\n' + '\n\n'.join(reviews)
        
        # Format final RPMs
        final_rpms = None
        if rpms_set:
            rpms_list = sorted(list(rpms_set))
            rpms_list = [rpm for rpm in rpms_list if 'General Measures and Standard OMP BMPs' not in rpm]
            rpms_list.append('General Measures and Standard OMP BMPs.')
            final_rpms = ';\n'.join(rpms_list)
        
        return final_review, final_rpms
    
    # Process each row
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