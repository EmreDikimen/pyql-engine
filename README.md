# PyQL Engine

An in-memory database CLI that replaces complex SQL `WHERE` clauses with raw Python scripts. This tool allows developers to query and manipulate table data directly using familiar Python loops, conditions, and expressions.

## Features
- Interactive REPL with command history and tab-autocompletion.
- Standard database operations (Create, Insert, Print).
- **PYSELECT:** Evaluate dynamic Python conditions directly in your queries.
- **Run Python Scripts:** Execute raw Python scripts on your tables to perform complex logic (updates, deletes) without writing complicated SQL.
- File persistence (Save/Load tables).
- Safe execution environment that catches syntax errors and restricts unsupported keywords (e.g., `def`).

## Getting Started
Ensure you have Python 3 installed. Clone the repository and run the engine:

```bash
git clone [https://github.com/EmreDikimen/pyql-engine.git](https://github.com/EmreDikimen/pyql-engine.git)
cd pyql-engine
python3 -m pyql_engine.cli
