
import sqlite3
import datetime
import csv
import os

# --- Configuration ---
DATABASE_NAME = "banking_data.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpass" 
CSV_EXPORT_FILENAME = r"c:\Users\hp\Desktop\project.py\system_transactions.csv"



# Path to external CSV for initial user accounts
# Make sure your file exists at this path
INITIAL_ACCOUNTS_FILE = r"c:\Users\hp\Desktop\project.py\system_transactions.csv"


class DatabaseManager:
    """
    Manages all persistent data operations for the banking application using SQLite.
    This class is unaware of the GUI elements (Tkinter).
    """
    def __init__(self):
        """Initializes the database connection and creates necessary tables."""
        self.db_conn = self._connect_db()
        self._load_initial_data() # Load sample accounts if tables are new

    def _connect_db(self):
        """Internal method to establish connection and ensure tables exist."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # 1. Accounts Table: Stores user credentials and current balance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0.00
                )
            """)
            
            # 2. Transactions Table: Stores transaction history for statements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    type TEXT NOT NULL, 
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY(account_id) REFERENCES accounts(id)
                )
            """)
            
            # 3. Admins Table: Stores admin credentials (simple for this example)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            
            # Initialize default admin account if it doesn't exist
            cursor.execute("SELECT id FROM admins WHERE username=?", (ADMIN_USERNAME,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                               (ADMIN_USERNAME, ADMIN_PASSWORD))
            
            conn.commit()
            return conn
        except sqlite3.Error as e:
            raise ConnectionError(f"Database initialization failed: {e}")

    def _load_initial_data(self):
    #"""Imports transaction data from system_transactions.csv."""
        cursor = self.db_conn.cursor()

        # Skip loading if data already exists
        cursor.execute("SELECT COUNT(*) FROM transactions")
        if cursor.fetchone()[0] > 0:
            print("✅ Transactions already exist in DB — skipping CSV load.")
            return

        print("Loading data from system_transactions.csv...")

        import csv, os
        if not os.path.exists(INITIAL_ACCOUNTS_FILE):
            print(f"⚠ CSV file not found: {INITIAL_ACCOUNTS_FILE}")
            return

        with open(INITIAL_ACCOUNTS_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if not {"Username", "Type", "Amount"}.issubset(reader.fieldnames):
                print("⚠ CSV file format not supported. Expected headers: Username, Type, Amount, Description, Timestamp")
                return

            for row in reader:
                username = row.get("Username", "").strip()
                tx_type = row.get("Type", "").strip().capitalize()
                amount_str = row.get("Amount", "0").strip()
                desc = row.get("Description", "").strip()
                timestamp = row.get("Timestamp", "").strip()

                try:
                    amount = float(amount_str)
                except ValueError:
                    print(f"Skipping invalid amount for {username}: {amount_str}")
                    continue

                if not username or not tx_type:
                    continue

                # Ensure account exists
                account_id = self.get_account_id_by_username(username)
                if not account_id:
                    self.create_account(username, "default123", 0, is_initial_load=True)
                    account_id = self.get_account_id_by_username(username)

                # Insert transaction
                cursor.execute("""
                    INSERT INTO transactions (account_id, type, amount, timestamp, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (account_id, tx_type, amount, timestamp, desc))

                # Update account balance
                if tx_type.lower() == "deposit":
                    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (amount, account_id))
                elif tx_type.lower() == "withdraw":
                    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id=?", (amount, account_id))

        self.db_conn.commit()
        print("✅ Transaction CSV import complete.")

    # --- Core Account Management Methods (Modified create_account) ---
    
    def check_admin_credentials(self, username, password):
        """Checks if the username and password are valid admin credentials, returning True if so."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE username=? AND password=?", (username, password))
        return cursor.fetchone() is not None

    def check_credentials(self, username, password):
        """Checks if the username and password are valid, returning ID and username."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, username FROM accounts WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()

    def create_account(self, username, password, initial_deposit, is_initial_load=False):
        """
        Creates a new user account and records the initial deposit.
        is_initial_load flag is used to skip input validation for built-in data.
        """
        if not is_initial_load:
            try:
                initial_deposit = float(initial_deposit)
                if initial_deposit < 0:
                     return "Initial deposit cannot be negative."
            except ValueError:
                return "Initial deposit must be a valid number."
        
        cursor = self.db_conn.cursor()
        
        try:
            # 1. Create the account
            cursor.execute("INSERT INTO accounts (username, password, balance) VALUES (?, ?, ?)", 
                           (username, password, initial_deposit))
            self.db_conn.commit()
            
            # 2. Record the initial deposit transaction
            new_account_id = cursor.lastrowid
            self.record_transaction(new_account_id, 'Deposit', initial_deposit, "Initial deposit on account creation")
            return True
        except sqlite3.IntegrityError:
            return "Username already exists."
        except sqlite3.Error as e:
            return f"Database error: {e}"

    def get_balance(self, user_id):
        """Retrieves the current balance for the given user ID."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE id=?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0.00

    def get_account_id_by_username(self, username):
        """Retrieves the account ID for a given username."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None

    # --- Admin Methods ---
    
    def get_all_accounts_summary(self):
        """Retrieves a summary of all user accounts for the admin dashboard."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, username, balance FROM accounts ORDER BY id ASC")
        return cursor.fetchall()
        
    def get_all_transactions(self):
        """Retrieves all transaction records."""
        cursor = self.db_conn.cursor()
        # Join accounts to show username
        cursor.execute("""
            SELECT 
                t.timestamp, 
                a.username, 
                t.type, 
                t.amount, 
                t.description 
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            ORDER BY t.timestamp DESC
        """)
        return cursor.fetchall()
        
    def export_all_transactions_to_csv(self):
        """
        Retrieves all transaction data and writes it to a CSV file.
        Returns the filename on success.
        """
        # Fetch the data using the same query as get_all_transactions
        data = self.get_all_transactions()
        
        if not data:
            return None # No data to export
            
        header = ["Timestamp", "Username", "Type", "Amount", "Description"]
        filename = CSV_EXPORT_FILENAME

        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                writer.writerows(data)
            return filename
        except IOError as e:
            raise IOError(f"Failed to write CSV file {filename}: {e}")

    # --- Transaction Methods ---

    def update_balance(self, user_id, amount):
        """Updates the balance of a user."""
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (amount, user_id))
        self.db_conn.commit()

    def record_transaction(self, account_id, type, amount, description=""):
        """Records a transaction in the history table."""
        cursor = self.db_conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO transactions (account_id, type, amount, timestamp, description) 
            VALUES (?, ?, ?, ?, ?)
        """, (account_id, type, amount, timestamp, description))
        self.db_conn.commit()

    def get_transaction_history(self, user_id):
        """Retrieves all transactions for a specific user ID."""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT timestamp, type, amount, description FROM transactions 
            WHERE account_id=? ORDER BY timestamp DESC
        """, (user_id,))
        return cursor.fetchall()
