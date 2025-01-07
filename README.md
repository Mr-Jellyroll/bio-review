# Biological Review Processor

This tool automates the processing of biological species review records to generate standardized biological resource reviews and RPMs (Resource Protection Measures) based on predefined classification rules.

## Overview

The script processes species records from input CSV files and maps them to standardized review language and RPMs based on species type, location, and specific guidance rules. It maintains proper taxonomic ordering and handles various species-specific conditions.

## Prerequisites

- Python 3.x
- pandas library (`pip install pandas`)

## File Structure

Required files:

- species-mapper.py: Main processing script
- USFS_MSUP_Class_2.csv: Classification rules file containing review language and RPMs
- Input file (CSV or XLSX) containing the review records to process

### File Requirements

#### Input CSV (Test.csv):
File Requirements

Input File (CSV or XLSX):

Must contain a column named "Review Records" with species data in the format:
``CopySpecies Name - Location Information``

Example:
```CopyPacific fisher - Not within 650-ft of CBI reproductive```
```Yosemite Toad - SNF Occupied | USFWS Critical Habitat```
```California Spotted Owl - Sierra Nevada DPS - CASPO Warning Layer```

#### Rules CSV USFS_MSUP_Class_2.csv:
Must contain the following columns:
- Species
- Scientific Name
- Habitat
- USFS guidance
- Taxon
- Species Specific Guidance
- Review Language (1-4)
- RPM (1-4)

## Usage

Run the script from the command line:
```bash
python3 species-mapper.py
```

The script will:
1. Display a list of available CSV and XLSX files in the current directory
2. Prompt you to select a file to process
3. If an XLSX file is selected, automatically convert it to CSV
4. Process the records according to the rules in USFS_MSUP_Class_2.csv
5. Save the output in `/bio-review/processed_data/`

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
- "Kaiser Pass Access" → Review Language (4)
- "SNF Occupied Unknown" → Review Language (2)
- "SNF Occupied" → Review Language (1)

### Location Processing

The script handles various location indicators:

- Source combinations (USFS/CNDDB/SCE)
- Critical Habitat designation
- Outside of SNF Mapped Habitat
- Distance-based criteria (e.g., "Within 1-mi")

### Excluded Species

Certain species are excluded from processing, including:

- Special-status fish
- Ringtail
- California red-legged frog
- Sierra Nevada red fox
- Wolverine
- Pallid bat
- California condor
- Valley elderberry longhorn beetle
- Special-status bumble bees

## Output Format

### File Location
Processed files are saved in /bio-review/processed_data/ with "_processed" appended to the original filename.

The processed CSV will maintain all original columns and add/update:
1. Biological Resource Review: Standardized review language for each species, ordered by taxonomy
2. Biological RPMs: Combined RPMs with "General Measures and Standard OMP BMPs" always at the end

## Error Handling

The script will check for:
- File availability and access
- Required columns
- Directory permissions
- Data format integrity
- CSV/XLSX conversion

Error messages will indicate the specific issue and required fixes.

## Troubleshooting

Common issues:
1. No files found: Ensure CSV/XLSX files are in the current directory
2. Conversion errors: Check XLSX file format and permissions
3. Missing output: Verify write permissions for output directory
4. Empty results: Confirm input data follows expected format

## Notes

- Keep both the script and USFS_MSUP_Class_2.csv in the same directory as your input file
- Maintain the standard format in the Review Records column
- Do not modify the structure of USFS_MSUP_Class_2.csv
- The script automatically handles both CSV and XLSX input files