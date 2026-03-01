import sys
import re
import readline
import os
import ast
from pyql_engine.db_engine import Database
from pyql_engine.formatter import format_ascii_table

class PyQL_REPL:
    def __init__(self):
        self.db = Database()
        self.setup_readline()

    def setup_readline(self):
        # Enable history and arrow key support
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)

    def _get_table_name_completions(self, prefix):
        names = []
        if self.db.tables:
            names.extend(self.db.tables.keys())
        saved_tables = [f.replace(".json", "") for f in os.listdir(".") if f.endswith(".json")]
        names.extend(saved_tables)
        return [name for name in sorted(set(names)) if name.lower().startswith(prefix.lower())]

    def _get_filename_completions(self, prefix):
        # Suggest .json files in current directory for LOAD
        files = [f.replace(".json", "") for f in os.listdir(".") if f.endswith(".json")]
        return [f for f in files if f.lower().startswith(prefix.lower())]

    def _get_script_completions(self, prefix):
        files = [f for f in os.listdir(".") if f.endswith(".py")]
        return [f for f in files if f.lower().startswith(prefix.lower())]

    def completer(self, text, state):
        line_buffer = readline.get_line_buffer()
        begidx = readline.get_begidx()
        context = line_buffer[:begidx].lower()

        # Table name completions based on context
        if re.search(r"\binsert\s+into\s+$", context):
            matches = self._get_table_name_completions(text)
        elif re.search(r"\bfrom\s+$", context):
            matches = self._get_table_name_completions(text)
        elif re.search(r"\bprint\s+$", context):
            matches = self._get_table_name_completions(text)
        elif re.search(r"\bsave\s+$", context):
            matches = self._get_table_name_completions(text)
        elif re.search(r"\brun\s+script\s+\S+\s+$", context):
            matches = self._get_table_name_completions(text)
        elif re.search(r"\bload\s+$", context):
            matches = self._get_filename_completions(text)
        elif re.search(r"\brun\s+script\s+$", context):
            matches = self._get_script_completions(text)
        else:
            options = ["CREATE TABLE ", "INSERT INTO ", "SELECT ", "FROM ", "UPDATE ", "DELETE FROM ", "SAVE ", "LOAD ", "RUN SCRIPT ", "print ", "exit", "quit"]
            matches = [opt for opt in options if opt.lower().startswith(text.lower())]

        if state < len(matches):
            return matches[state]
        return None

    def _parse_where_clause(self, where_clause_str):
        if not where_clause_str:
            return []
        conditions = []
        for cond in where_clause_str.split("AND"):
            cond = cond.strip()
            if "=" in cond:
                col, val = cond.split("=", 1)
                conditions.append((col.strip(), val.strip().strip("'").strip('"')))
        return conditions

    def _validate_script(self, script_code):
        try:
            parsed = ast.parse(script_code)
        except SyntaxError as e:
            return f"Script syntax error at line {e.lineno}: {e.msg}"

        disallowed_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)
        for node in ast.walk(parsed):
            if isinstance(node, disallowed_nodes):
                return "Script contains unsupported statements (functions, classes, or imports)."
        return None

    def parse_and_execute(self, command):
        command = command.strip()
        if not command:
            return ""

        # RUN SCRIPT filename table_name
        run_match = re.match(r"RUN SCRIPT (\S+) (\w+)", command, re.IGNORECASE)
        if run_match:
            script_name = run_match.group(1)
            table_name = run_match.group(2)

            load_error = self.db.load_table_if_exists(table_name)
            if load_error:
                return load_error

            if not os.path.exists(script_name):
                return f"Error: Script file '{script_name}' not found."

            script_locals = {
                "db": self.db,
                "table": table_name,
                "print_table": lambda: format_ascii_table(table_name, self.db.get_table(table_name)),
            }

            try:
                with open(script_name, "r") as f:
                    script_code = f.read()

                validation_error = self._validate_script(script_code)
                if validation_error:
                    return validation_error

                exec(script_code, {}, script_locals)
                save_result = self.db.save_table(table_name)
                if save_result.startswith("Error"):
                    return save_result
                return f"Script '{script_name}' executed on table '{table_name}'. {save_result}"
            except Exception as e:
                return f"Error executing script: {e}"

        # SAVE table_name
        save_match = re.match(r"SAVE (\w+)", command, re.IGNORECASE)
        if save_match:
            return self.db.save_table(save_match.group(1))

        # LOAD table_name
        load_match = re.match(r"LOAD (\w+)", command, re.IGNORECASE)
        if load_match:
            return self.db.load_table(load_match.group(1))

        # SELECT col1, col2 FROM table_name [WHERE col=val AND ...]
        select_match = re.match(r"SELECT (.*) FROM (\w+)(?:\s+WHERE\s+(.+))?", command, re.IGNORECASE)
        if select_match:
            columns_str = select_match.group(1)
            table_name = select_match.group(2)
            where_clause = select_match.group(3)
            
            selected_cols = [c.strip() for c in columns_str.split(",")]
            result = self.db.select_from(table_name, selected_cols)
            
            if isinstance(result, str):
                return result

            if where_clause:
                where_conditions = self._parse_where_clause(where_clause)
                # Filter results in-place
                filtered_rows = []
                for row in result["rows"]:
                    if self.db._row_matches_where(row, result["columns"], where_conditions):
                        filtered_rows.append(row)
                result["rows"] = filtered_rows
            
            return format_ascii_table(f"SELECT result from {table_name}", result)

        # UPDATE table_name SET col1=val1, col2=val2 WHERE col=val
        update_match = re.match(r"UPDATE (\w+) SET (.+?)(?:\s+WHERE\s+(.+))?", command, re.IGNORECASE)
        if update_match:
            table_name = update_match.group(1)
            assignment_str = update_match.group(2)
            where_clause = update_match.group(3)

            assignments = {}
            for part in assignment_str.split(","):
                col, val = part.split("=", 1)
                assignments[col.strip()] = val.strip().strip("'").strip('"')

            where_conditions = self._parse_where_clause(where_clause)
            return self.db.update_rows(table_name, assignments, where_conditions)

        # DELETE FROM table_name WHERE col=val
        delete_match = re.match(r"DELETE FROM (\w+)(?:\s+WHERE\s+(.+))?", command, re.IGNORECASE)
        if delete_match:
            table_name = delete_match.group(1)
            where_clause = delete_match.group(2)
            where_conditions = self._parse_where_clause(where_clause)
            return self.db.delete_rows(table_name, where_conditions)

        # CREATE TABLE table_name (col1, col2, ...)
        create_match = re.match(r"CREATE TABLE (\w+) \((.*)\)", command, re.IGNORECASE)
        if create_match:
            table_name = create_match.group(1)
            columns = [c.strip() for c in create_match.group(2).split(",")]
            return self.db.create_table(table_name, columns)

        # INSERT INTO table_name VALUES (val1, val2, ...)
        insert_match = re.match(r"INSERT INTO (\w+) VALUES \((.*)\)", command, re.IGNORECASE)
        if insert_match:
            table_name = insert_match.group(1)
            values = [v.strip().strip("'").strip('"') for v in insert_match.group(2).split(",")]
            return self.db.insert_into(table_name, values)

        # print table_name
        print_match = re.match(r"print (\w+)", command, re.IGNORECASE)
        if print_match:
            table_name = print_match.group(1)
            table_data = self.db.get_table(table_name)
            if table_data:
                return format_ascii_table(table_name, table_data)
            return f"Error: Table '{table_name}' not found."

        if command.lower() in ["exit", "quit"]:
            print("Goodbye!")
            sys.exit(0)

        return f"Error: Unknown command '{command}'"

    def run(self):
        print("PyQL Engine Interactive REPL")
        print("Commands: CREATE TABLE, INSERT INTO, SELECT ... FROM ..., UPDATE, DELETE, SAVE, LOAD, RUN SCRIPT, print, exit")
        print("Support for arrow keys and TAB completion enabled.")
        while True:
            try:
                user_input = input("pyql> ")
                if user_input:
                    result = self.parse_and_execute(user_input)
                    if result:
                        print(result)
            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\nUse exit/quit to leave.")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    repl = PyQL_REPL()
    repl.run()
