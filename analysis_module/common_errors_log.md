# Analysis Module - Common Errors Log

This document tracks common errors encountered in the analysis module and their solutions.

## Error 1: "No data available for the selected variables and time range"

### Symptoms
- User selects variables and chart type
- Clicks "Generate Chart"
- Gets message "No data available for the selected variables and time range"
- Happens even when data should be available

### Root Cause
**Composite metrics selected as X-axis variables cause SQL errors**

When users select composite metrics (like "Total Time", "Average Time", "Fail Rate") as X-axis variables, the code tries to use these as database column names in SQL queries. These don't exist as actual columns, causing the query to fail.

### Solution
Modified `get_aggregated_chart_data()` method in `data_manager.py`:

1. **Check if X variable is a real database column**: Only use actual database columns (`date_audited`, `week_id`, `project_name`, `locale`, `duration`, `time_limit`, `score`, `bonus_paid`) in SQL SELECT clause.

2. **Handle composite metrics as X variables**: When composite metric is selected as X variable, group by `date_audited` instead and calculate the composite value for display.

3. **Calculate X variable display values**: Added logic to compute actual X variable values when they're composite metrics.

### What to Look For
- Check if X variable is in the list of actual database columns
- Look for SQL errors in console output
- Verify that composite metrics are being calculated correctly, not used directly in SQL

### Code Location
- File: `analysis_module/data_manager.py`
- Method: `get_aggregated_chart_data()`
- Lines: ~134-150 (group_by_field logic)

---

## Error 2: Week Selection Not Working (RESOLVED)

### Symptoms
- Time range selection works fine for charts
- Week selection doesn't return any data for charts
- Numerical statistics work fine with week selection
- Debug output shows: "time data '20-05-2025' does not match format '%d/%m/%Y'"

### Root Cause
**Date format mismatch in week label parsing**

The code expected week labels to be in `dd/MM/yyyy` format (with slashes), but the actual database format was `dd-MM-yyyy` (with hyphens). This caused the date parsing to fail, resulting in no data being retrieved.

### Solution
Modified the date parsing logic in `get_chart_data()` method to handle multiple date formats:

```python
# Try multiple date formats - first try dd-MM-yyyy, then dd/MM/yyyy
date_formats = ['%d-%m-%Y', '%d/%m/%Y']
start_date = None
end_date = None

for fmt in date_formats:
    try:
        start_date = datetime.strptime(start_date_str, fmt).strftime('%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, fmt).strftime('%Y-%m-%d')
        break  # Success, exit the format loop
    except ValueError:
        continue  # Try next format
```

### What to Look For
- Check console output for date parsing errors
- Verify week_label format in the database
- Ensure date format patterns match actual data
- Look for "time data does not match format" errors

### Code Location
- File: `analysis_module/data_manager.py`
- Method: `get_chart_data()`
- Lines: ~62-75 (date parsing logic)

---

## Error 3: Database Connection Leaks

### Symptoms
- Application becomes slow over time
- Database locked errors
- Memory usage increases

### Root Cause
Database connections not being properly closed when exceptions occur.

### Solution
Added proper try-finally blocks to ensure connections are always closed:

```python
conn = None
try:
    conn = sqlite3.connect(DB_FILE)
    # ... database operations
except Exception as e:
    # ... error handling
finally:
    if conn:
        conn.close()
```

### What to Look For
- Missing `finally` blocks in database operations
- Connections being closed only in success paths
- Multiple connection objects without proper cleanup

### Code Location
- File: `analysis_module/data_manager.py`
- All methods that use `sqlite3.connect()`

---

## Debugging Tips

### Enable Debug Output
The analysis module includes debug print statements that can be enabled/disabled:

```python
# In get_chart_data() and get_aggregated_chart_data()
print(f"Debug: Query executed: {query}")
print(f"Debug: Parameters: {params}")
print(f"Debug: Raw data count: {len(raw_data)}")
```

### Common Debug Checks
1. **Verify variable names**: Ensure UI variable names match database column names
2. **Check data types**: Verify data conversion between UI and database
3. **Validate date formats**: Ensure date strings match expected formats
4. **Test SQL queries**: Run queries manually in database browser to verify syntax
5. **Check data existence**: Verify that data actually exists for the selected time range

### Database Schema Reference
Key tables and columns:
- `tasks`: duration, time_limit, score, project_name, locale, date_audited, bonus_paid, week_id
- `weeks`: id, week_label (format: "dd/MM/yyyy - dd/MM/yyyy")

---

## Future Improvements

1. **Better error handling**: Replace generic "no data" messages with specific error descriptions
2. **Input validation**: Validate variable selections before querying database
3. **Query optimization**: Cache frequently used queries
4. **Logging system**: Replace print statements with proper logging framework 