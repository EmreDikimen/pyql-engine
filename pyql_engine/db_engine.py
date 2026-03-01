import json
import os

class Database:
    def __init__(self):
        # tables: { table_name: { "columns": [col1, col2, ...], "rows": [[val1, val2, ...], ...] } }
        self.tables = {}

    def create_table(self, table_name, columns):
        if table_name in self.tables:
            return f"Error: Table '{table_name}' already exists."
        self.tables[table_name] = {"columns": columns, "rows": []}
        return f"Table '{table_name}' created."

    def insert_into(self, table_name, values):
        if table_name not in self.tables:
            return f"Error: Table '{table_name}' does not exist."

        expected_cols = len(self.tables[table_name]["columns"])
        if len(values) != expected_cols:
            return f"Error: Expected {expected_cols} values, got {len(values)}."

        self.tables[table_name]["rows"].append(values)
        return f"Inserted 1 row into '{table_name}'."

    def select_from(self, table_name, selected_cols):
        if table_name not in self.tables:
            return f"Error: Table '{table_name}' does not exist."

        table = self.tables[table_name]
        all_cols = table["columns"]

        if "*" in selected_cols:
            indices = list(range(len(all_cols)))
            final_cols = all_cols
        else:
            indices = []
            final_cols = []
            for col in selected_cols:
                if col in all_cols:
                    indices.append(all_cols.index(col))
                    final_cols.append(col)
                else:
                    return f"Error: Column '{col}' not found in table '{table_name}'."

        new_rows = []
        for row in table["rows"]:
            new_rows.append([row[i] for i in indices])

        return {"columns": final_cols, "rows": new_rows}

    def update_rows(self, table_name, assignments, where_clauses):
        if table_name not in self.tables:
            return f"Error: Table '{table_name}' does not exist."

        table = self.tables[table_name]
        columns = table["columns"]

        for col in assignments:
            if col not in columns:
                return f"Error: Column '{col}' not found in table '{table_name}'."

        for col, _ in where_clauses:
            if col not in columns:
                return f"Error: Column '{col}' not found in table '{table_name}'."

        updated = 0
        for row in table["rows"]:
            if self._row_matches_where(row, columns, where_clauses):
                for col, val in assignments.items():
                    row[columns.index(col)] = val
                updated += 1

        return f"Updated {updated} row(s) in '{table_name}'."

    def delete_rows(self, table_name, where_clauses):
        if table_name not in self.tables:
            return f"Error: Table '{table_name}' does not exist."

        table = self.tables[table_name]
        columns = table["columns"]

        for col, _ in where_clauses:
            if col not in columns:
                return f"Error: Column '{col}' not found in table '{table_name}'."

        original_count = len(table["rows"])
        table["rows"] = [row for row in table["rows"] if not self._row_matches_where(row, columns, where_clauses)]
        deleted = original_count - len(table["rows"])
        return f"Deleted {deleted} row(s) from '{table_name}'."

    def save_table(self, table_name):
        if table_name not in self.tables:
            return f"Error: Table '{table_name}' does not exist."

        filename = f"{table_name}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.tables[table_name], f)
            return f"Table '{table_name}' saved to {filename}."
        except Exception as e:
            return f"Error saving table: {e}"

    def load_table(self, table_name):
        filename = f"{table_name}.json"
        if not os.path.exists(filename):
            return f"Error: File {filename} not found."

        try:
            with open(filename, 'r') as f:
                self.tables[table_name] = json.load(f)
            return f"Table '{table_name}' loaded from {filename}."
        except Exception as e:
            return f"Error loading table: {e}"

    def load_table_if_exists(self, table_name):
        if table_name in self.tables:
            return None
        filename = f"{table_name}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    self.tables[table_name] = json.load(f)
                return None
            except Exception as e:
                return f"Error loading table: {e}"
        return f"Error: Table '{table_name}' not found in memory or {filename}."

    def _row_matches_where(self, row, columns, where_clauses):
        if not where_clauses:
            return True

        for col, expected in where_clauses:
            idx = columns.index(col)
            if str(row[idx]) != expected:
                return False
        return True

    def get_table(self, table_name):
        return self.tables.get(table_name)
