def format_ascii_table(table_name, table_data):
    if not table_data:
        return f"Error: Table '{table_name}' not found."
    
    columns = table_data["columns"]
    rows = table_data["rows"]
    
    if not columns:
        return f"Table '{table_name}' has no columns."

    # Calculate column widths
    col_widths = [len(col) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    # Create separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    # Build the table string
    output = [f"Table: {table_name}", separator]
    
    # Header
    header = "|" + "|".join(f" {columns[i]:<{col_widths[i]}} " for i in range(len(columns))) + "|"
    output.append(header)
    output.append(separator)
    
    # Rows
    if not rows:
        # Correctly calculate empty row space
        empty_space = sum(col_widths) + 2 * len(columns) + (len(columns) - 1)
        # However, it's simpler to just show it's empty
        output.append("| (empty) ".ljust(len(separator)-1) + "|")
        output.append(separator)
    else:
        for row in rows:
            row_str = "|" + "|".join(f" {str(row[i]):<{col_widths[i]}} " for i in range(len(row))) + "|"
            output.append(row_str)
        output.append(separator)
        
    return "\n".join(output)
