import os
import pandas as pd

def list_xlsx_files(directory):
    """
    List all .xlsx files in the specified directory.

    Args:
        directory (str): Path to the directory to search for .xlsx files.

    Returns:
        list: List of .xlsx file names.
    """
    return [f for f in os.listdir(directory) if f.endswith('.xlsx')]

def convert_xlsx_to_csv(input_file, output_file):
    """
    Convert an Excel (.xlsx) file to a CSV file.

    Args:
        input_file (str): Path to the input .xlsx file.
        output_file (str): Path to the output .csv file.
    """
    try:
        # Load the Excel file
        excel_data = pd.read_excel(input_file, engine='openpyxl')

        # Write to CSV while preserving row and column spacing
        excel_data.to_csv(output_file, index=False)
        print(f"File converted successfully: {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # List .xlsx files in the current directory
    current_directory = os.getcwd()
    xlsx_files = list_xlsx_files(current_directory)

    if not xlsx_files:
        print("No .xlsx files found in the current directory.")
    else:
        print("Available .xlsx files:")
        for idx, file in enumerate(xlsx_files, start=1):
            print(f"{idx}: {file}")

        # Prompt the user to select a file
        try:
            file_choice = int(input("Enter the number of the file to convert: ")) - 1
            if file_choice < 0 or file_choice >= len(xlsx_files):
                raise ValueError("Invalid choice.")

            input_file = xlsx_files[file_choice]
            output_file = os.path.splitext(input_file)[0] + ".csv"

            # Convert the selected file
            convert_xlsx_to_csv(input_file, output_file)

        except ValueError as ve:
            print(f"Error: {ve}")
