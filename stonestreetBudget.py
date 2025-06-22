import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

csv_file = "phatstacks.csv"
mapping_file = "description_identifier_mapping.json"

def read_transactions(csv_path):
    """
    Reads the bank transactions from the CSV file.
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(csv_path)
    return df

def add_custom_identifier(transactions_df):
    """
    Adds a 'Custom Identifier' column to the DataFrame based on
    the 'Description' and 'type' columns.
    """
    def identifier(row):
        description = str(row['Description']).lower()
        txn_type = str(row['type']).lower()

        # Example logic for custom identifier - user can customize this
        if 'grocery' in description:
            return 'GROCERY'
        elif 'rent' in description:
            return 'RENT'
        elif txn_type == 'credit':
            return 'CREDIT'
        elif txn_type == 'debit':
            return 'DEBIT'
        else:
            return 'OTHER'

    transactions_df['Custom Identifier'] = transactions_df.apply(identifier, axis=1)
    return transactions_df

class BudgetTrackerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Personal Budget Tracker")

        # Load description to identifier mappings
        self.load_mappings()

        # Load processed transactions
        self.load_processed_transactions()

        # Load transactions
        self.transactions = pd.read_csv(csv_file)
        # Keep only relevant columns
        relevant_columns = ['Transaction Date', 'Amount', 'Credit Debit Indicator', 'type', 'Description', 'Category']
        # Add 'Custom Identifier' if present or create empty
        if 'Custom Identifier' in self.transactions.columns:
            relevant_columns.append('Custom Identifier')
        self.transactions = self.transactions[relevant_columns]

        # Add Custom Identifier column if not present
        if 'Custom Identifier' not in self.transactions.columns:
            self.transactions['Custom Identifier'] = ''
        
        # Replace NaN or 'nan' strings with empty string in Custom Identifier column
        self.transactions['Custom Identifier'] = self.transactions['Custom Identifier'].replace('nan', '').fillna('').astype(str)

        # Apply mappings to assign identifiers automatically
        self.apply_mappings()
        # Save updated transactions with assigned identifiers to CSV on first load
        self.transactions.to_csv(csv_file, index=False)
        # Remove filtering to keep all rows including those with Custom Identifiers
        # self.transactions = self.transactions[self.transactions['Custom Identifier'].isnull() | (self.transactions['Custom Identifier'] == '')].reset_index(drop=True)

        self.current_index = 0
        self.hide_processed = tk.BooleanVar(value=False)
        self.filtered_transactions = self.transactions.copy()

        # Create UI elements
        self.create_widgets()
        self.display_transaction()

    def load_mappings(self):
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    self.mappings = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load mappings: {e}")
                self.mappings = {}
        else:
            self.mappings = {}

    def save_mappings(self):
        try:
            with open(mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mappings: {e}")

    def add_mapping(self):
        # Use the current transaction's Description field as the key
        if 0 <= self.current_index < len(self.filtered_transactions):
            desc = str(self.filtered_transactions.iloc[self.current_index].get('Description', '')).strip().lower()
            identifier = self.identifier_var.get().strip()
            if not desc or not identifier:
                messagebox.showwarning("Warning", "Current transaction description or identifier is empty.")
                return
            self.mappings[desc] = identifier
            self.save_mappings()
            messagebox.showinfo("Info", f"Mapping added: '{desc}' -> '{identifier}'")
            # Re-apply mappings to transactions
            self.apply_mappings()
            # Update filtered transactions after applying mappings
            self.toggle_hide_processed()
            self.display_transaction()

    def apply_mappings(self):
        for idx, row in self.transactions.iterrows():
            description = str(row.get('Description', '')).lower()
            for key, val in self.mappings.items():
                if key in description:
                    self.transactions.at[idx, 'Custom Identifier'] = val
                    break

    def create_widgets(self):
        # Labels for transaction fields
        self.labels = {}
        fields = ['Transaction Date', 'Amount', 'Credit Debit Indicator', 'type', 'Description', 'Category']
        row = 0
        for field in fields:
            lbl = ttk.Label(self.master, text=field + ":")
            lbl.grid(row=row, column=0, sticky='e', padx=5, pady=2)
            val = ttk.Label(self.master, text="", width=50, anchor='w', relief='sunken')
            val.grid(row=row, column=1, sticky='w', padx=5, pady=2)
            self.labels[field] = val
            row += 1

        # Custom Identifier label and combobox
        ttk.Label(self.master, text="Custom Identifier:").grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.identifier_var = tk.StringVar()
        self.identifier_combo = ttk.Combobox(self.master, textvariable=self.identifier_var)
        self.identifier_combo['values'] = sorted(['Rent', 'Phone', 'Philo', 'Spotify', 'Peacock', 'Youtube', 'Canva', 'Microsoft Office', 'Xbox', 'Adobe', 'Fuel', 'Car wash', 'USAA', 'Groceries', 'Vitamins', 'Coffee', 'LMNT', 'Toothpaste', 'Amazon', 'Eating out', 'Other', 'Burn Bootcamp', 'Planet Fitness', 'National Academy', 'Income', 'Savings'])
        self.identifier_combo.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Hide processed transactions radio button
        self.hide_processed_radio = ttk.Checkbutton(self.master, text="Hide Processed Transactions", variable=self.hide_processed, command=self.toggle_hide_processed)
        self.hide_processed_radio.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Add mapping UI elements
        # Removed the description input and extra identifier combobox as per user request

        self.add_mapping_button = ttk.Button(self.master, text="Add Mapping", command=self.add_mapping)
        self.add_mapping_button.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Navigation buttons
        self.prev_button = ttk.Button(self.master, text="Previous", command=self.prev_transaction)
        self.prev_button.grid(row=row, column=0, padx=5, pady=10)

        self.next_button = ttk.Button(self.master, text="Next", command=self.next_transaction)
        self.next_button.grid(row=row, column=1, sticky='w', padx=5, pady=10)

        # Remove Save to CSV button as per user request
        # self.save_button = ttk.Button(self.master, text="Save to CSV", command=self.save_to_csv)
        # self.save_button.grid(row=row+1, column=0, columnspan=2, pady=10)

        # Clear processed transactions button
        self.clear_processed_button = ttk.Button(self.master, text="Clear Processed Transactions", command=self.clear_processed_transactions)
        self.clear_processed_button.grid(row=row+2, column=0, columnspan=2, pady=5)

        # Backup processed transactions button
        self.backup_processed_button = ttk.Button(self.master, text="Backup Processed Transactions", command=self.backup_processed_transactions)
        self.backup_processed_button.grid(row=row+3, column=0, columnspan=2, pady=5)

        # Clear all custom identifiers button
        self.clear_custom_ids_button = ttk.Button(self.master, text="Clear All Custom Identifiers", command=self.clear_all_custom_identifiers)
        self.clear_custom_ids_button.grid(row=row+4, column=0, columnspan=2, pady=5)

        # Finished button to save CSV
        self.finished_button = ttk.Button(self.master, text="Finished", command=self.save_to_csv)
        self.finished_button.grid(row=row+5, column=0, columnspan=2, pady=10)

    def clear_processed_transactions(self):
        try:
            if os.path.exists("processed_transactions.csv"):
                os.remove("processed_transactions.csv")
            self.processed_transactions.clear()
            messagebox.showinfo("Success", "Processed transactions cleared.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear processed transactions: {e}")

    def clear_all_custom_identifiers(self):
        try:
            # Clear all custom identifiers in the transactions DataFrame
            self.transactions['Custom Identifier'] = ''
            # Save the updated DataFrame back to CSV
            self.transactions.to_csv(csv_file, index=False)
            # Refresh the filtered transactions to only those without custom identifiers
            self.transactions = self.transactions[self.transactions['Custom Identifier'].isnull() | (self.transactions['Custom Identifier'] == '')].reset_index(drop=True)
            self.current_index = 0
            self.display_transaction()
            messagebox.showinfo("Success", "All custom identifiers cleared.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear custom identifiers: {e}")

    def backup_processed_transactions(self):
        import shutil
        import datetime
        try:
            if os.path.exists("processed_transactions.csv"):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"processed_transactions_backup_{timestamp}.csv"
                shutil.copy("processed_transactions.csv", backup_filename)
                messagebox.showinfo("Success", f"Backup created: {backup_filename}")
            else:
                messagebox.showwarning("Warning", "No processed transactions file to backup.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup processed transactions: {e}")

    def display_transaction(self):
        if 0 <= self.current_index < len(self.filtered_transactions):
            row = self.filtered_transactions.iloc[self.current_index]
            for field, label in self.labels.items():
                label.config(text=str(row.get(field, '')))
            # Set combobox to current custom identifier or empty
            current_id = row.get('Custom Identifier', '')
            self.identifier_var.set(current_id)

            # Disable editing if transaction already processed
            txn_key = (str(row.get('Transaction Date', '')), str(row.get('Description', '')))
            # Remove disabling of editing controls to always allow editing
            # if txn_key in self.processed_transactions:
            #     self.identifier_combo.config(state='disabled')
            #     self.add_mapping_button.config(state='disabled')
            #     self.save_button.config(state='disabled')
            # else:
            self.identifier_combo.config(state='normal')
            self.add_mapping_button.config(state='normal')
            # Removed reference to save_button as it no longer exists
            # self.save_button.config(state='normal')
        else:
            messagebox.showinfo("Info", "No more transactions.")

    def save_current_identifier(self):
        if 0 <= self.current_index < len(self.filtered_transactions):
            row = self.filtered_transactions.iloc[self.current_index]
            txn_key = (str(row.get('Transaction Date', '')), str(row.get('Description', '')))
            # Always update the Custom Identifier
            # Need to update the original transactions DataFrame as well
            original_index = self.transactions.index[self.transactions['Transaction Date'] == row['Transaction Date']]
            original_index = original_index[self.transactions.loc[original_index, 'Description'] == row['Description']].tolist()
            if original_index:
                self.transactions.at[original_index[0], 'Custom Identifier'] = self.identifier_var.get()
            # Mark transaction as processed if not already
            if txn_key not in self.processed_transactions:
                self.save_processed_transaction(*txn_key)

    def next_transaction(self):
        # Removed auto save on next
        self.save_current_identifier()
        if self.current_index < len(self.filtered_transactions) - 1:
            self.current_index += 1
            self.display_transaction()
        else:
            messagebox.showinfo("Info", "This is the last transaction.")

    def prev_transaction(self):
        # Removed auto save on prev
        self.save_current_identifier()
        if self.current_index > 0:
            self.current_index -= 1
            self.display_transaction()
        else:
            messagebox.showinfo("Info", "This is the first transaction.")

    def save_to_csv(self):
        self.save_current_identifier()
        try:
            # Save the updated transactions DataFrame back to the CSV file
            self.transactions.to_csv(csv_file, index=False)
            messagebox.showinfo("Success", f"Custom Identifiers saved to '{csv_file}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to CSV: {e}")

    def load_processed_transactions(self):
        self.processed_transactions = set()
        if os.path.exists("processed_transactions.csv"):
            try:
                df = pd.read_csv("processed_transactions.csv")
                for _, row in df.iterrows():
                    key = (str(row.get('Transaction Date', '')), str(row.get('Description', '')))
                    self.processed_transactions.add(key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load processed transactions: {e}")

    def save_processed_transaction(self, transaction_date, description):
        try:
            # Append to processed_transactions.csv
            import csv
            file_exists = os.path.exists("processed_transactions.csv")
            with open("processed_transactions.csv", mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Transaction Date', 'Description'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({'Transaction Date': transaction_date, 'Description': description})
            # Add to in-memory set
            self.processed_transactions.add((transaction_date, description))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save processed transaction: {e}")

    def toggle_hide_processed(self):
        # Update the transactions DataFrame based on the hide_processed flag
        if self.hide_processed.get():
            # Filter to only transactions without Custom Identifier
            self.filtered_transactions = self.transactions[self.transactions['Custom Identifier'].isnull() | (self.transactions['Custom Identifier'] == '')].reset_index(drop=True)
        else:
            # Show all transactions
            self.filtered_transactions = self.transactions.reset_index(drop=True)
        self.current_index = 0
        self.display_transaction()

def main():
    root = tk.Tk()
    app = BudgetTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
