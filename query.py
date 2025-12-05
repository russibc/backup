#!/usr/bin/env python3
"""
TSV Query Tool - Execute SQL queries directly on TSV files

Usage:
    python query.py <tsv_file> '<sql_query>'

Examples:
    python query.py output.tsv 'SELECT * FROM data LIMIT 10'
    python query.py output.tsv 'SELECT Entry, Mass FROM data WHERE Mass > 50000'
    python query.py output.tsv 'SELECT COUNT(*) FROM data'
"""

import pandas as pd
import sqlite3
import sys
import os
import tempfile
from pathlib import Path
import argparse


class TSVQueryTool:
    def __init__(self, tsv_file, verbose=False):
        """
        Initialize the query tool

        Args:
            tsv_file: Path to the TSV file
            verbose: Print additional information
        """
        self.tsv_file = tsv_file
        self.verbose = verbose
        self.temp_db = None
        self.conn = None
        self.table_name = 'data'  # Default table name

    def sanitize_column_names(self, columns):
        """Sanitize column names for SQLite compatibility"""
        sanitized = {}
        for col in columns:
            # Replace problematic characters
            new_col = col.replace(' ', '_')
            new_col = new_col.replace('[', '_')
            new_col = new_col.replace(']', '_')
            new_col = new_col.replace('(', '_')
            new_col = new_col.replace(')', '_')
            new_col = new_col.replace('-', '_')
            new_col = new_col.replace('/', '_')
            new_col = new_col.replace('\\', '_')
            new_col = new_col.replace('.', '_')
            new_col = new_col.replace(',', '_')
            new_col = new_col.replace(';', '_')
            new_col = new_col.replace(':', '_')
            # Remove consecutive underscores
            while '__' in new_col:
                new_col = new_col.replace('__', '_')
            new_col = new_col.strip('_')

            # Ensure it doesn't start with a number
            if new_col and new_col[0].isdigit():
                new_col = 'col_' + new_col

            sanitized[col] = new_col

        return sanitized

    def load_tsv_to_db(self):
        """Load TSV file into a temporary SQLite database"""
        if self.verbose:
            print(f"Loading TSV file: {self.tsv_file}", file=sys.stderr)

        try:
            # Load TSV
            df = pd.read_csv(self.tsv_file, sep='\t', low_memory=False)

            if self.verbose:
                print(f"Loaded {len(df)} rows and {len(df.columns)} columns", file=sys.stderr)

            # Sanitize column names
            column_mapping = self.sanitize_column_names(df.columns)
            df_renamed = df.rename(columns=column_mapping)

            if self.verbose and any(orig != new for orig, new in column_mapping.items()):
                print("Column names sanitized:", file=sys.stderr)
                for orig, new in column_mapping.items():
                    if orig != new:
                        print(f"  '{orig}' -> '{new}'", file=sys.stderr)

            # Create temporary database
            self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            if self.verbose:
                print(f"Creating temporary database: {self.temp_db.name}", file=sys.stderr)

            # Connect and load data
            self.conn = sqlite3.connect(self.temp_db.name)
            df_renamed.to_sql(self.table_name, self.conn, if_exists='replace', index=False)

            if self.verbose:
                print(f"Data loaded into table '{self.table_name}'", file=sys.stderr)

            return True

        except Exception as e:
            print(f"Error loading TSV: {e}", file=sys.stderr)
            return False

    def execute_query(self, query):
        """
        Execute SQL query and return results

        Args:
            query: SQL query string

        Returns:
            pandas DataFrame with results
        """
        if self.conn is None:
            raise RuntimeError("Database not loaded. Call load_tsv_to_db() first.")

        try:
            if self.verbose:
                print(f"Executing query: {query}", file=sys.stderr)

            # Execute query
            result = pd.read_sql_query(query, self.conn)

            if self.verbose:
                print(f"Query returned {len(result)} rows", file=sys.stderr)

            return result

        except Exception as e:
            print(f"Error executing query: {e}", file=sys.stderr)
            return None

    def print_results(self, df, max_rows=None, max_width=None):
        """
        Print query results in a formatted table with borders

        Args:
            df: pandas DataFrame with results
            max_rows: Maximum number of rows to display
            max_width: Maximum width for output
        """
        if df is None or len(df) == 0:
            print("No results found.")
            return

        # Limit rows if specified
        display_df = df.head(max_rows) if max_rows else df

        # Calculate column widths
        col_widths = {}
        for col in display_df.columns:
            # Get max width between column name and values
            max_val_width = display_df[col].astype(str).str.len().max()
            col_widths[col] = max(len(str(col)), max_val_width, 3)  # minimum 3 chars

            # Limit width if max_width is specified
            if max_width:
                col_widths[col] = min(col_widths[col], max_width)

        # Build separator line
        separator = '+' + '+'.join(['-' * (w + 2) for w in col_widths.values()]) + '+'

        # Print top border
        print(separator)

        # Print header
        header_parts = []
        for col in display_df.columns:
            header_parts.append(f" {str(col):<{col_widths[col]}} ")
        print('|' + '|'.join(header_parts) + '|')

        # Print header separator
        print(separator)

        # Print rows
        for _, row in display_df.iterrows():
            row_parts = []
            for col in display_df.columns:
                value = str(row[col])
                # Truncate if too long
                if len(value) > col_widths[col]:
                    value = value[:col_widths[col] - 3] + '...'
                row_parts.append(f" {value:<{col_widths[col]}} ")
            print('|' + '|'.join(row_parts) + '|')

        # Print bottom border
        print(separator)

        # Print summary
        if max_rows and len(df) > max_rows:
            print(f"\nShowing {len(display_df)} of {len(df)} rows")
        else:
            print(f"\n{len(df)} row(s) returned")

        if self.verbose:
            print(f"Columns: {len(df.columns)}", file=sys.stderr)

    def cleanup(self):
        """Close connection and delete temporary database"""
        if self.conn:
            self.conn.close()

        if self.temp_db:
            try:
                os.unlink(self.temp_db.name)
                if self.verbose:
                    print(f"Temporary database deleted: {self.temp_db.name}", file=sys.stderr)
            except:
                pass

    def query(self, sql_query, max_rows=None, max_width=None):
        """
        Main method: load TSV, execute query, print results, cleanup

        Args:
            sql_query: SQL query to execute
            max_rows: Maximum number of rows to display
            max_width: Maximum width for output
        """
        try:
            # Load TSV into temporary database
            if not self.load_tsv_to_db():
                return False

            # Execute query
            result = self.execute_query(sql_query)

            # Print results
            if result is not None:
                self.print_results(result, max_rows, max_width)
                return True
            else:
                return False

        finally:
            # Always cleanup
            self.cleanup()


def print_table_info(tsv_file):
    """Print information about the TSV file structure"""
    try:
        df = pd.read_csv(tsv_file, sep='\t', nrows=0, low_memory=False)

        tool = TSVQueryTool(tsv_file)
        column_mapping = tool.sanitize_column_names(df.columns)

        print("Table: data")
        print("\nColumns:")
        for i, (orig, new) in enumerate(column_mapping.items(), 1):
            if orig != new:
                print(f"  {i}. {new} (originally: {orig})")
            else:
                print(f"  {i}. {new}")

        print(f"\nTotal columns: {len(df.columns)}")
        print("\nExample queries:")
        print(f"  SELECT * FROM data LIMIT 10")
        print(f"  SELECT COUNT(*) FROM data")
        if len(df.columns) > 0:
            first_col = list(column_mapping.values())[0]
            print(f"  SELECT {first_col} FROM data")

    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Execute SQL queries on TSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s output.tsv 'SELECT * FROM data LIMIT 10'
  %(prog)s output.tsv 'SELECT Entry, Mass FROM data WHERE Mass > 50000'
  %(prog)s output.tsv 'SELECT COUNT(*) FROM data'
  %(prog)s output.tsv --info  # Show table structure
        '''
    )

    parser.add_argument('tsv_file', help='Path to TSV file')
    parser.add_argument('query', nargs='?', help='SQL query to execute')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose output')
    parser.add_argument('--info', action='store_true',
                        help='Show table structure and exit')
    parser.add_argument('--max-rows', type=int, default=None,
                        help='Maximum number of rows to display')
    parser.add_argument('--max-width', type=int, default=None,
                        help='Maximum width for output')

    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.tsv_file):
        print(f"Error: File '{args.tsv_file}' not found", file=sys.stderr)
        sys.exit(1)

    # Show info mode
    if args.info:
        print_table_info(args.tsv_file)
        sys.exit(0)

    # Query mode
    if not args.query:
        print("Error: Query is required (or use --info to show table structure)",
              file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Execute query
    tool = TSVQueryTool(args.tsv_file, verbose=args.verbose)
    success = tool.query(args.query, max_rows=args.max_rows, max_width=args.max_width)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()