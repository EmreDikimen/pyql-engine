# Example script to run against a table using RUN SCRIPT
# Available variables:
#   db: Database instance
#   table: table name
#   print_table(): returns ASCII table string

# Insert a new row
existing = db.get_table(table)
if existing:
    columns = existing["columns"]
    if len(columns) >= 4:
        db.insert_into(table, ["101", "NewUser", "active", "99"])

# Update rows where status is inactive
rows = db.get_table(table)["rows"]
for row in rows:
    if row[2] == "inactive":
        row[2] = "active"

# Delete rows with score below 50
rows_to_keep = []
for row in db.get_table(table)["rows"]:
    if int(row[3]) >= 50:
        rows_to_keep.append(row)

# Overwrite rows directly
db.tables[table]["rows"] = rows_to_keep
