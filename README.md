# Biological Review Processor

This tool automates the processing of biological species review records to generate standardized biological resource reviews and RPMs (Resource Protection Measures) based on predefined classification rules.

## Overview

The script processes species records from input CSV files and maps them to standardized review language and RPMs based on species type, location, and specific guidance rules. It maintains proper taxonomic ordering and handles various species-specific conditions.

## Prerequisites

- Python 3.x
- pandas library (`pip install pandas`)

## File Structure

Required files:
- `species-mapper.py`: Main processing script
- `USFS_MSUP_Class_2.csv`: Classification rules file containing review language and RPMs
- Input CSV file (e.g., `Test.csv`) containing the review records to process

### CSV File Requirements

#### Input CSV (Test.csv):
Must contain a column named "Review Records" with species data in the format:
```
Species Name - Location Information
```
Example:
```
Pacific fisher - Not within 650-ft of CBI reproductive
Yosemite Toad - SNF Occupied | USFWS Critical Habitat
```

#### Rules CSV USFS_MSUP_Class_2.csv:
Must contain the following columns:
- Species
- Taxon
- Species Specific Guidance
- Review Language (1-4)
- RPM (1-4)

## Usage

Run the script from the command line:
```bash
python3 species-mapper.py your_input_file.csv
```

The script will:
1. Read the input CSV file
2. Process each record according to the rules in USFS_MSUP_Class_2.csv
3. Generate output with new/updated columns:
   - "Biological Resource Review (presence/absence, resource description if appropriate)"
   - "Biological RPMs"

Output will be saved as `your_input_file_processed.csv`

## Processing Logic

The script handles:
- Taxonomic ordering (Amphibian → Bird → Mammal)
- Species-specific conditions (e.g., Pacific Fisher location patterns)
- Standardized review language selection
- RPM compilation and formatting

### Special Cases

Pacific Fisher handling:
- "Not within" → Review Language (4)
- "Within 650-ft" + "Critical Habitat" → Review Language (1)
- "Within CBI" + "reproductive" → Review Language (2)
- "Within 650-ft" + "CBI" → Review Language (3)

Yosemite Toad handling:
- "SNF Occupied" + "Critical Habitat" → Review Language (1)

## Output Format

The processed CSV will maintain all original columns and add/update:
1. Biological Resource Review: Standardized review language for each species, ordered by taxonomy
2. Biological RPMs: Combined RPMs with "General Measures and Standard OMP BMPs" always at the end

## Error Handling

The script will check for:
- Missing input files
- Required columns
- File permissions
- Data format issues

Error messages will indicate the specific issue and required fixes.

## Troubleshooting

Common issues:
1. File not found: Ensure both input CSV and USFS_MSUP_Class_2.csv are in the same directory
2. Column errors: Verify "Review Records" column exists in input CSV
3. Empty output: Check input data format matches expected patterns

## Notes

- Keep both the script and USFS_MSUP_Class_2.csv in the same directory as your input file
- Maintain the standard format in the Review Records column
- Do not modify the structure of USFS_MSUP_Class_2.csv