import os
import sqlite3
# Lazy import for pandas - deferred until first use
from core.optimization.lazy_imports import get_lazy_manager
from datetime import datetime
import sys
import re # For parsing CSV filename

# Database file name
DB_FILE = "tasks.db"

class ImportManager:
    """Import manager with lazy-loaded pandas for better startup performance"""
    
    def __init__(self):
        self._lazy_manager = get_lazy_manager()
        self._setup_lazy_imports()
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for heavy scientific libraries"""
        # Register pandas for lazy loading
        self._lazy_manager.register_module('pandas', 'pandas')
    
    @property
    def pd(self):
        """Lazy-loaded pandas module"""
        return self._lazy_manager.get_module('pandas')

# Global instance for easy access
_import_manager = ImportManager()

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_week_id_by_label(conn, week_label):
    """
    Gets the ID for a given week label.
    Returns the ID or None if not found.
    Requires an active database connection.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM weeks WHERE week_label=?", (week_label,))
        result = cursor.fetchone()
        if result:
            return result['id']
        return None
    except sqlite3.Error as e:
        print(f"Error retrieving week ID for label '{week_label}': {e}")
        return None

def create_week(conn, week_label):
    """
    Creates a new week entry in the database.
    Returns the new week's ID or None on failure.
    Requires an active database connection within a transaction.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO weeks (week_label) VALUES (?)", (week_label,))
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Warning: Week label '{week_label}' already exists or conflicted. Attempting to retrieve ID.")
        return get_week_id_by_label(conn, week_label)
    except sqlite3.Error as e:
        print(f"Error creating week '{week_label}': {e}")
        return None

def process_dataframe_for_insertion(df, week_id, week_label_for_reporting):
    """
    Validates rows in a DataFrame and prepares them for insertion.
    Returns (list_of_valid_rows, list_of_invalid_row_info, rows_in_df)
    """
    valid_rows_for_db = []
    invalid_rows_info = []
    rows_in_df = len(df)

    # --- Data Validation ---
    expected_columns = {
        "Attempt ID": str,
        "Duration": str,  # Changed from (int, float) to str for HH:MM:SS format
        "Project ID": str,
        "Project Name": str,
        "Operation ID": str,
        "Time Limit": str,  # Changed from (int, float) to str for HH:MM:SS format
        "Date Audited": str,
        "Score": (int, float),
        "Feedback": str,
        "Locale": str
    }

    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        error_message = f"Data source '{week_label_for_reporting}' missing required columns: {', '.join(missing_cols)}. Skipping this source."
        invalid_rows_info.append({'source': week_label_for_reporting, 'row_index': 'N/A', 'errors': [error_message], 'data_sample': 'N/A - Missing columns'})
        return [], invalid_rows_info, rows_in_df # Return early if fundamental columns are missing

    # Coerce types and prepare for validation
    for col, dtypes in expected_columns.items():
        if col in df.columns:
            try:
                if col == "Score":
                    df[col] = df[col].apply(lambda x: _import_manager.pd.to_numeric(x, errors='coerce'))
                if col in ["Duration", "Time Limit"]:
                    # Ensure time fields are strings and validate their format
                    df[col] = df[col].astype(str)
                if col == "Date Audited":
                    df[col] = df[col].apply(lambda x: str(x).strip() if _import_manager.pd.notna(x) and str(x).strip() else None)
            except Exception as e:
                print(f"Warning: Error coercing column '{col}' in '{week_label_for_reporting}': {e}")

    # Helper function to validate time format
    def is_valid_time_format(time_str):
        if not isinstance(time_str, str) or not time_str.strip():
            return False
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                return False
            hours, minutes, seconds = map(int, parts)
            return 0 <= hours < 100 and 0 <= minutes < 60 and 0 <= seconds < 60
        except (ValueError, AttributeError, TypeError):
            return False

    for index, row in df.iterrows():
        is_valid = True
        validation_errors_for_row = []

        for col_name in ["Attempt ID", "Duration", "Project ID", "Project Name",
                         "Operation ID", "Time Limit", "Date Audited", "Score", "Locale"]:
            if _import_manager.pd.isna(row[col_name]) or (isinstance(row[col_name], str) and not row[col_name].strip()):
                validation_errors_for_row.append(f"Missing or empty mandatory field: '{col_name}'")
                is_valid = False

        if is_valid: # Continue with type and value checks only if mandatory fields are present
            # Validate Duration format
            if not is_valid_time_format(row["Duration"]):
                validation_errors_for_row.append(f"Invalid time format for 'Duration': {row['Duration']}")
                is_valid = False
                
            # Validate Time Limit format
            if not is_valid_time_format(row["Time Limit"]):
                validation_errors_for_row.append(f"Invalid time format for 'Time Limit': {row['Time Limit']}")
                is_valid = False
                
            if not isinstance(row["Score"], expected_columns["Score"]):
                validation_errors_for_row.append(f"Invalid type for 'Score': {type(row['Score']).__name__}")
                is_valid = False
                
            if not row["Date Audited"] or not isinstance(row["Date Audited"], str): # Checked for non-empty string
                 validation_errors_for_row.append(f"Invalid or empty 'Date Audited'")
                 is_valid = False

            if isinstance(row["Score"], (int, float)) and row["Score"] < 0:
                validation_errors_for_row.append("Negative value for 'Score'")
                is_valid = False
        
        if is_valid:
            try:
                date_audited_iso = str(_import_manager.pd.to_datetime(row['Date Audited']).date())
            except Exception:
                validation_errors_for_row.append(f"Could not parse 'Date Audited': {row['Date Audited']}")
                is_valid = False

        if is_valid:
            valid_rows_for_db.append((
                str(row['Attempt ID']), # Ensure Attempt ID is string
                row['Duration'],  # Keep as string in HH:MM:SS format
                str(row['Project ID']),
                str(row['Project Name']),
                str(row['Operation ID']),
                row['Time Limit'],  # Keep as string in HH:MM:SS format
                date_audited_iso,
                row['Score'],
                str(row.get('Feedback', '')), # Handle potentially missing Feedback column gracefully
                str(row['Locale']),
                week_id
            ))
        else:
            invalid_rows_info.append({
                'source': week_label_for_reporting,
                'row_index': index + 2, # +2 for 0-index and header row
                'errors': validation_errors_for_row,
                'data_sample': {k: str(v)[:50] for k, v in row.to_dict().items()} # Truncate long values
            })
    return valid_rows_for_db, invalid_rows_info, rows_in_df

def import_tasks_from_excel(filename, conn):
    """
    Imports task data from a multi-sheet Excel file.
    Each sheet name is treated as a week label.
    """
    print(f"Attempting to import data from Excel file: '{filename}'...")
    total_rows_read_file = 0
    total_rows_inserted_file = 0
    all_invalid_rows_info_file = []
    file_level_errors = []

    try:
        excel_file = _import_manager.pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names

        existing_weeks_df = _import_manager.pd.read_sql_query("SELECT id, week_label FROM weeks", conn)
        existing_weeks = dict(zip(existing_weeks_df['week_label'], existing_weeks_df['id']))

        for sheet_name in sheet_names:
            week_label = sheet_name.strip()
            if not week_label:
                file_level_errors.append(f"Skipping empty sheet name.")
                continue
            
            print(f"Processing sheet: '{week_label}'...")

            week_id = existing_weeks.get(week_label)
            if week_id is None:
                week_id = create_week(conn, week_label)
                if week_id:
                    existing_weeks[week_label] = week_id
                    print(f"Created new week '{week_label}' with ID {week_id}")
                else:
                    file_level_errors.append(f"Failed to get or create week for label '{week_label}'. Skipping sheet.")
                    continue

            try:
                df = excel_file.parse(sheet_name)
            except Exception as e:
                file_level_errors.append(f"Error reading sheet '{week_label}': {e}")
                continue
            
            valid_rows_for_db, invalid_rows_info_sheet, rows_in_sheet = process_dataframe_for_insertion(df, week_id, sheet_name)
            total_rows_read_file += rows_in_sheet
            all_invalid_rows_info_file.extend(invalid_rows_info_sheet)

            if valid_rows_for_db:
                cursor = conn.cursor()
                insert_sql = """
                INSERT OR REPLACE INTO tasks (
                    attempt_id, duration, project_id, project_name, 
                    operation_id, time_limit, date_audited, score, 
                    feedback, locale, week_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                try:
                    cursor.executemany(insert_sql, valid_rows_for_db)
                    # rowcount for executemany is not always reliable for actual inserted/replaced
                    # We count based on valid_rows_for_db prepared for insertion.
                    total_rows_inserted_file += len(valid_rows_for_db)
                    print(f"Attempted to insert/replace {len(valid_rows_for_db)} valid rows from sheet '{week_label}'.")
                except sqlite3.Error as e:
                    file_level_errors.append(f"Database error during insertion for sheet '{week_label}': {e}.")
            else:
                print(f"No valid rows to insert from sheet '{week_label}'.")
        
    except Exception as e:
        file_level_errors.append(f"An unexpected error occurred while processing Excel file: {e}")

    return total_rows_read_file, total_rows_inserted_file, all_invalid_rows_info_file, file_level_errors


def import_tasks_from_csv(filename, conn):
    """
    Imports task data from a single CSV file.
    Attempts to derive week label from the filename.
    """
    print(f"Attempting to import data from CSV file: '{filename}'...")
    total_rows_read_file = 0
    total_rows_inserted_file = 0
    all_invalid_rows_info_file = []
    file_level_errors = []

    # Try to extract week_label from filename (e.g., auditor_tasks_MY-WEEK-LABEL.csv)
    week_label = None
    match = re.search(r"auditor_tasks_([^\.]+)\.csv", os.path.basename(filename), re.IGNORECASE)
    if match:
        week_label = match.group(1).replace("-", " ").replace("_", " ") # Basic cleanup
    else:
        # Fallback if pattern doesn't match - could prompt or use a default
        week_label = f"CSV Import - {os.path.basename(filename)}" 
        print(f"Warning: Could not parse week label from CSV filename. Using default: '{week_label}'")


    print(f"Processing CSV with derived week label: '{week_label}'...")
    
    existing_weeks_df = _import_manager.pd.read_sql_query("SELECT id, week_label FROM weeks", conn)
    existing_weeks = dict(zip(existing_weeks_df['week_label'], existing_weeks_df['id']))

    week_id = existing_weeks.get(week_label)
    if week_id is None:
        week_id = create_week(conn, week_label)
        if week_id:
            existing_weeks[week_label] = week_id # Add to our current session's lookup
            print(f"Created new week '{week_label}' with ID {week_id}")
        else:
            file_level_errors.append(f"Failed to get or create week for label '{week_label}' from CSV. Skipping file.")
            return total_rows_read_file, total_rows_inserted_file, all_invalid_rows_info_file, file_level_errors

    try:
        df = _import_manager.pd.read_csv(filename)
    except Exception as e:
        file_level_errors.append(f"Error reading CSV file '{filename}': {e}")
        return total_rows_read_file, total_rows_inserted_file, all_invalid_rows_info_file, file_level_errors

    valid_rows_for_db, invalid_rows_info_csv, rows_in_csv = process_dataframe_for_insertion(df, week_id, f"CSV: {os.path.basename(filename)} (Week: {week_label})")
    total_rows_read_file += rows_in_csv
    all_invalid_rows_info_file.extend(invalid_rows_info_csv)

    if valid_rows_for_db:
        cursor = conn.cursor()
        insert_sql = """
        INSERT OR REPLACE INTO tasks (
            attempt_id, duration, project_id, project_name, 
            operation_id, time_limit, date_audited, score, 
            feedback, locale, week_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor.executemany(insert_sql, valid_rows_for_db)
            total_rows_inserted_file += len(valid_rows_for_db)
            print(f"Attempted to insert/replace {len(valid_rows_for_db)} valid rows from CSV '{filename}'.")
        except sqlite3.Error as e:
            file_level_errors.append(f"Database error during insertion for CSV '{filename}': {e}.")
    else:
        print(f"No valid rows to insert from CSV '{filename}'.")

    return total_rows_read_file, total_rows_inserted_file, all_invalid_rows_info_file, file_level_errors


def main_import(filename):
    """Main import orchestration."""
    if not os.path.exists(filename):
        print(f"Error: File not found at '{filename}'")
        return

    conn = get_db_connection()
    if not conn:
        return

    total_rows_read = 0
    total_rows_inserted = 0
    all_invalid_rows_info = []
    all_file_level_errors = []

    try:
        conn.execute("BEGIN;") # Start a database transaction

        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension == '.xlsx':
            read, inserted, invalid_info, errors = import_tasks_from_excel(filename, conn)
            total_rows_read += read
            total_rows_inserted += inserted
            all_invalid_rows_info.extend(invalid_info)
            all_file_level_errors.extend(errors)
        elif file_extension == '.csv':
            read, inserted, invalid_info, errors = import_tasks_from_csv(filename, conn)
            total_rows_read += read
            total_rows_inserted += inserted
            all_invalid_rows_info.extend(invalid_info)
            all_file_level_errors.extend(errors)
        else:
            all_file_level_errors.append(f"Unsupported file type: '{file_extension}'. Please use .xlsx or .csv files.")

        if not all_file_level_errors and not any(item['errors'] for item in all_invalid_rows_info if 'errors' in item): # Check for critical errors
            conn.commit()
            print("\nDatabase transaction committed.")
        else:
            conn.rollback()
            print("\nDatabase transaction rolled back due to errors during processing.")
            # If only some sheets/rows had validation errors but no DB/file errors, we might still commit
            # The current logic rolls back if ANY error (file level or severe validation that stops processing) occurs.
            # More nuanced commit/rollback could be added based on severity.
            # For now, if all_file_level_errors is not empty, or critical validation errors that prevent processing, we rollback.
            # The "any(item['errors']..." is a simple check for any validation issue, which might be too strict for rollback.
            # Let's refine: rollback if all_file_level_errors OR if total_rows_inserted == 0 AND total_rows_read > 0 due to validation issues.
            # Simpler: rollback if all_file_level_errors exist. Validation errors for rows are reported but don't stop commit for other valid data.
            # Revisiting: if there are file_level_errors OR if (total_rows_inserted == 0 and total_rows_read > 0 and not all_file_level_errors)
            # The `process_dataframe_for_insertion` already skips entire sheets/CSVs if columns are missing.
            # So, if `all_file_level_errors` is populated, that's a clear rollback.
            # If it's empty, but `all_invalid_rows_info` has entries, those are row-level issues.
            # The previous logic was: if no file_level_errors and no validation_errors, then commit.
            # This means if there are *any* validation errors, it rolls back. This might be too strict.
            # Let's change to: commit if no all_file_level_errors, otherwise rollback. Validation errors are reported.
            if not all_file_level_errors and total_rows_inserted > 0: # If we inserted something and no file errors
                conn.commit()
                print("\nDatabase transaction committed (some rows may have been skipped due to validation).")
            elif not all_file_level_errors and total_rows_inserted == 0 and total_rows_read > 0:
                 conn.rollback() # No file errors, but nothing inserted - likely all rows failed validation
                 print("\nDatabase transaction rolled back: No valid data found to insert.")
            elif all_file_level_errors:
                 conn.rollback() # File errors occurred
                 print("\nDatabase transaction rolled back due to file processing or database errors.")
            else: # No errors, nothing read or inserted (e.g. empty file)
                 conn.commit() # Safe to commit, nothing changed
                 print("\nDatabase transaction committed (no data processed or no errors).")


    except Exception as e:
        if conn:
            conn.rollback()
        all_file_level_errors.append(f"A critical unexpected error occurred: {e}. Database transaction rolled back.")
        print("\nDatabase transaction rolled back due to a critical error.")
    finally:
        if conn:
            conn.close()

    # --- Final Report ---
    print("\n--- Import Summary ---")
    print(f"File: '{filename}'")
    print(f"Total rows read from file: {total_rows_read}")
    print(f"Total rows prepared and valid for database: {sum(1 for r in all_invalid_rows_info if not r.get('errors')) + total_rows_inserted}") # This calc needs review, better: total_rows_read - len(all_invalid_rows_info) if error means skipped
    print(f"Total rows attempted for database insert/replace: {total_rows_inserted}")
    
    total_rows_skipped_validation = len([info for info in all_invalid_rows_info if info.get('errors')])
    print(f"Total rows skipped due to validation errors: {total_rows_skipped_validation}")

    if all_invalid_rows_info:
        print("\n--- Validation Issues (Row-Level) ---")
        for info in all_invalid_rows_info:
            if info.get('errors'): # Only print if there were actual errors for this entry
                print(f"  Source: {info['source']}, Row Index (approx): {info['row_index']}, Errors: {', '.join(info['errors'])}")
                # print(f"    Data Sample: {info['data_sample']}") # Uncomment for more detail

    if all_file_level_errors:
        print("\n--- File Processing or Database Errors ---")
        for error in all_file_level_errors:
            print(f"- {error}")
    
    if not all_file_level_errors and total_rows_skipped_validation == 0 and total_rows_read > 0:
        print("\nImport completed successfully with all rows processed.")
    elif not all_file_level_errors and total_rows_inserted > 0 :
        print("\nImport completed. Some rows may have been skipped due to validation issues (see details above).")
    elif not all_file_level_errors and total_rows_read == 0:
        print("\nImport completed. No data found in the file to process.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_data.py <excel_or_csv_filename>")
    else:
        input_filename = sys.argv[1]
        main_import(input_filename)

