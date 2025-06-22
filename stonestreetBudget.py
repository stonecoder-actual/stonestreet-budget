import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

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
        category = str(row.get('Category', '')).lower()
        txn_type = str(row['type']).lower()

        # Custom logic for specific cases
        if description == '#name?' and category == 'rent':
            return 'Rent'
        elif category == 'personal care':
            return 'Planet Fitness'

        # Existing example logic for custom identifier - user can customize this
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

class DateFilterGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Select CSV File and Date")
        self.master.geometry("400x300")
        
        self.selected_month = None
        self.selected_year = None
        self.selected_file = None
        self.proceed = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title label
        title_label = ttk.Label(self.master, text="Select CSV File and Date Range", font=("Arial", 12))
        title_label.pack(pady=10)

        # File selection frame
        file_frame = ttk.Frame(self.master)
        file_frame.pack(pady=10)
        
        self.file_label = ttk.Label(file_frame, text="No file selected", width=40)
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Month selection
        month_frame = ttk.Frame(self.master)
        month_frame.pack(pady=5)
        
        ttk.Label(month_frame, text="Month:").pack(side=tk.LEFT, padx=5)
        self.month_var = tk.StringVar()
        month_combo = ttk.Combobox(month_frame, textvariable=self.month_var, state="readonly")
        month_combo['values'] = [
            "01 - January", "02 - February", "03 - March", "04 - April",
            "05 - May", "06 - June", "07 - July", "08 - August",
            "09 - September", "10 - October", "11 - November", "12 - December"
        ]
        month_combo.pack(side=tk.LEFT, padx=5)
        
        # Year selection
        year_frame = ttk.Frame(self.master)
        year_frame.pack(pady=5)
        
        ttk.Label(year_frame, text="Year:").pack(side=tk.LEFT, padx=5)
        self.year_var = tk.StringVar()
        year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, state="readonly")
        current_year = datetime.now().year
        year_combo['values'] = [str(year) for year in range(current_year - 5, current_year + 2)]
        year_combo.set(str(current_year))
        year_combo.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.master)
        button_frame.pack(pady=20)
        
        proceed_button = ttk.Button(button_frame, text="Proceed", command=self.on_proceed)
        proceed_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
    def on_proceed(self):
        if not self.selected_file:
            messagebox.showwarning("Warning", "Please select a CSV file first.")
            return
            
        if not self.month_var.get() or not self.year_var.get():
            messagebox.showwarning("Warning", "Please select both month and year.")
            return
            
        self.selected_month = self.month_var.get()[:2]  # Extract month number
        self.selected_year = self.year_var.get()
        self.proceed = True
        self.master.destroy()
        
    def on_cancel(self):
        self.proceed = False
        self.master.destroy()

    def browse_file(self):
        global csv_file
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file = filename
            csv_file = filename  # Update the global csv_file variable
            # Show only the filename, not the full path
            display_name = os.path.basename(filename)
            self.file_label.config(text=display_name)

def filter_transactions_by_date(month, year):
    """
    Filter transactions in the selected CSV file to keep only those in the specified month and year.
    """
    try:
        if not os.path.exists(csv_file):
            messagebox.showerror("Error", "Please select a CSV file first.")
            return 0, 0
            
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Convert Transaction Date to datetime
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        
        # Filter by month and year
        filtered_df = df[
            (df['Transaction Date'].dt.month == int(month)) & 
            (df['Transaction Date'].dt.year == int(year))
        ]
        
        # Save filtered transactions back to CSV
        filtered_df.to_csv(csv_file, index=False)
        
        return len(filtered_df), len(df)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to filter transactions: {e}")
        return 0, 0

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
        # Remove rows with Description "#NAME?"
        removed_rows = self.transactions[self.transactions['Description'] == '#NAME?']
        self.transactions = self.transactions[self.transactions['Description'] != '#NAME?']
        # Save removed rows to processed_transactions.csv
        if not removed_rows.empty:
            try:
                import csv
                file_exists = os.path.exists("processed_transactions.csv")
                with open("processed_transactions.csv", mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['Transaction Date', 'Description', 'Amount'])
                    if not file_exists:
                        writer.writeheader()
                    for _, row in removed_rows.iterrows():
                        key = (
                            str(row.get('Transaction Date', '')).strip(),
                            str(row.get('Description', '')).strip(),
                            str(row.get('Amount', '')).strip()
                        )
                        # Avoid duplicates by checking if key already in processed_transactions
                        if key not in self.processed_transactions:
                            writer.writerow({
                                'Transaction Date': row.get('Transaction Date', ''),
                                'Description': row.get('Description', ''),
                                'Amount': row.get('Amount', '')
                            })
                            self.processed_transactions.add(key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save removed transactions to processed file: {e}")
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

        # Add all processed transactions (with Custom Identifier) to processed_transactions.csv
        try:
            import csv
            file_exists = os.path.exists("processed_transactions.csv")
            with open("processed_transactions.csv", mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Transaction Date', 'Description', 'Amount'])
                if not file_exists:
                    writer.writeheader()
                for _, row in self.transactions.iterrows():
                    txn_key = (
                        str(row.get('Transaction Date', '')).strip(),
                        str(row.get('Description', '')).strip(),
                        str(row.get('Amount', '')).strip()
                    )
                    if row.get('Custom Identifier', '') and txn_key not in self.processed_transactions:
                        writer.writerow({
                            'Transaction Date': row.get('Transaction Date', ''),
                            'Description': row.get('Description', ''),
                            'Amount': row.get('Amount', '')
                        })
                        self.processed_transactions.add(txn_key)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save processed transactions during initialization: {e}")

        self.current_index = 0
        self.hide_processed = tk.BooleanVar(value=False)
        self.filtered_transactions = self.transactions.copy()

        # Create UI elements
        self.create_widgets()
        self.update_transaction_counter()
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
                    print(f"Mapping applied: '{key}' -> '{val}' for description '{description}'")  # Debug log
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
        self.identifier_combo['values'] = sorted(['Ignore', 'Rent', 'Phone', 'Philo', 'Spotify', 'Peacock', 'Youtube', 'Canva', 'Microsoft Office', 'Xbox', 'Adobe', 'Fuel', 'Car wash', 'USAA', 'Groceries', 'Vitamins', 'Coffee', 'LMNT', 'Toothpaste', 'Amazon', 'Eating out', 'Other', 'Burn Bootcamp', 'Planet Fitness', 'National Academy', 'Income', 'Savings'])
        self.identifier_combo.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Transaction counter label
        self.transaction_counter_label = ttk.Label(self.master, text="")
        self.transaction_counter_label.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Hide processed transactions radio button
        self.hide_processed_radio = ttk.Checkbutton(self.master, text="Hide Processed Transactions", variable=self.hide_processed, command=self.toggle_hide_processed)
        self.hide_processed_radio.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Add mapping UI elements
        self.add_mapping_button = ttk.Button(self.master, text="Add Mapping", command=self.add_mapping)
        self.add_mapping_button.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Navigation buttons
        self.prev_button = ttk.Button(self.master, text="Previous", command=self.prev_transaction)
        self.prev_button.grid(row=row, column=0, padx=5, pady=10)

        self.next_button = ttk.Button(self.master, text="Next", command=self.next_transaction)
        self.next_button.grid(row=row, column=1, sticky='w', padx=5, pady=10)

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
            self.update_transaction_counter()
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

            # Enable editing controls
            self.identifier_combo.config(state='normal')
            self.add_mapping_button.config(state='normal')
        else:
            messagebox.showinfo("Info", "No more transactions.")

    def save_current_identifier(self):
        if 0 <= self.current_index < len(self.filtered_transactions):
            row = self.filtered_transactions.iloc[self.current_index]
            txn_key = (
                str(row.get('Transaction Date', '')).strip(),
                str(row.get('Description', '')).strip(),
                str(row.get('Amount', '')).strip()
            )
            # Always update the Custom Identifier
            # Need to update the original transactions DataFrame as well
            # Normalize description strings for matching and include Amount
            original_index = self.transactions.index[
                (self.transactions['Transaction Date'].astype(str).str.strip() == str(row['Transaction Date']).strip()) &
                (self.transactions['Description'].astype(str).str.strip().str.lower() == str(row['Description']).strip().lower()) &
                (self.transactions['Amount'].astype(str).str.strip() == str(row['Amount']).strip())
            ].tolist()
            if original_index:
                selected_identifier = self.identifier_var.get()
                print(f"Saving Custom Identifier '{selected_identifier}' for transaction with description '{row['Description']}' and amount '{row['Amount']}'")  # Debug log
                # If "Ignore" is selected, save empty string as Custom Identifier
                if selected_identifier == "Ignore":
                    self.transactions.at[original_index[0], 'Custom Identifier'] = ''
                else:
                    self.transactions.at[original_index[0], 'Custom Identifier'] = selected_identifier
            else:
                print(f"No matching transaction found for description '{row['Description']}' and amount '{row['Amount']}'")  # Debug log
            # Mark transaction as processed if not already
            if txn_key not in self.processed_transactions:
                self.save_processed_transaction(*txn_key)

    def next_transaction(self):
        self.save_current_identifier()
        if self.current_index < len(self.filtered_transactions) - 1:
            self.current_index += 1
            self.update_transaction_counter()
            self.display_transaction()
        else:
            messagebox.showinfo("Info", "This is the last transaction.")

    def prev_transaction(self):
        self.save_current_identifier()
        if self.current_index > 0:
            self.current_index -= 1
            self.update_transaction_counter()
            self.display_transaction()
        else:
            messagebox.showinfo("Info", "This is the first transaction.")

    def save_to_csv(self):
        self.save_current_identifier()
        try:
            # Save the updated transactions DataFrame back to the CSV file
            self.transactions.to_csv(csv_file, index=False)
            messagebox.showinfo("Success", f"Custom Identifiers saved to '{csv_file}'.")
            # Close the GUI window after saving
            self.master.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to CSV: {e}")

    def load_processed_transactions(self):
        self.processed_transactions = set()
        if os.path.exists("processed_transactions.csv"):
            try:
                df = pd.read_csv("processed_transactions.csv")
                for _, row in df.iterrows():
                    key = (
                        str(row.get('Transaction Date', '')),
                        str(row.get('Description', '')),
                        str(row.get('Amount', ''))
                    )
                    self.processed_transactions.add(key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load processed transactions: {e}")

    def save_processed_transaction(self, transaction_date, description, amount):
        try:
            # Append to processed_transactions.csv
            import csv
            file_exists = os.path.exists("processed_transactions.csv")
            with open("processed_transactions.csv", mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Transaction Date', 'Description', 'Amount'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    'Transaction Date': transaction_date,
                    'Description': description,
                    'Amount': amount
                })
            # Add to in-memory set with amount to uniquely identify the transaction
            self.processed_transactions.add((transaction_date, description, str(amount)))
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
        self.update_transaction_counter()
        self.display_transaction()

    def update_transaction_counter(self):
        total = len(self.transactions)
        remaining = len(self.transactions[self.transactions['Custom Identifier'].isnull() | (self.transactions['Custom Identifier'] == '')])
        self.transaction_counter_label.config(text=f"Total Transactions: {total} | Remaining without Custom Identifier: {remaining}")

def main():
    # First show the date filter GUI
    filter_root = tk.Tk()
    filter_app = DateFilterGUI(filter_root)
    filter_root.mainloop()
    
    # Check if user proceeded with file selection and date selection
    if not filter_app.proceed:
        print("Operation cancelled. Exiting.")
        return
        
    if not filter_app.selected_file:
        messagebox.showwarning("Warning", "Please select a CSV file first.")
        return
    
    # Filter transactions by selected month and year
    filtered_count, total_count = filter_transactions_by_date(filter_app.selected_month, filter_app.selected_year)
    
    if filtered_count == 0:
        messagebox.showinfo("Info", f"No transactions found for {filter_app.month_var.get()} {filter_app.selected_year}.")
        return
    
    messagebox.showinfo("Filtering Complete", 
                       f"Filtered transactions: {filtered_count} out of {total_count} total transactions kept for {filter_app.month_var.get()} {filter_app.selected_year}.")
    
    # Now show the main budget tracker GUI
    root = tk.Tk()
    app = BudgetTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
