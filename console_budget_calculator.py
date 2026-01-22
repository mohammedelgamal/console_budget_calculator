import sqlite3
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Configuration ---
DB_NAME = "secure_budgets.db"
KEY_FILE = "budget_key.key"

class CryptoManager:
    """Handles AES-GCM encryption and decryption."""
    def __init__(self):
        self.key = self._load_or_generate_key()
        self.aesgcm = AESGCM(self.key)

    def _load_or_generate_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()
        else:
            key = AESGCM.generate_key(bit_length=256)
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            print(f"[!] New encryption key generated and saved to '{KEY_FILE}'.")
            return key

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        data = plaintext.encode('utf-8')
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt(self, token: str) -> str:
        try:
            encrypted_blob = base64.b64decode(token)
            nonce = encrypted_blob[:12]
            ciphertext = encrypted_blob[12:]
            return self.aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
        except Exception:
            return "[Decryption Error]"

class BudgetDB:
    """Manages SQLite connection and full CRUD operations."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.execute("PRAGMA foreign_keys = 1") # Enable foreign key support
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        # Added ON DELETE CASCADE to automatically remove items when a budget is deleted
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER,
                description TEXT,
                amount TEXT,
                FOREIGN KEY(budget_id) REFERENCES budgets(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    # --- Budget CRUD ---
    def create_budget(self, name):
        try:
            self.cursor.execute("INSERT INTO budgets (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_budgets(self):
        self.cursor.execute("SELECT id, name FROM budgets")
        return self.cursor.fetchall()

    def update_budget_name(self, budget_id, new_name):
        try:
            self.cursor.execute("UPDATE budgets SET name = ? WHERE id = ?", (new_name, budget_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_budget(self, budget_id):
        # Items are deleted automatically due to ON DELETE CASCADE
        self.cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        self.conn.commit()

    # --- Item CRUD ---
    def add_item(self, budget_id, desc_enc, amt_enc):
        self.cursor.execute(
            "INSERT INTO items (budget_id, description, amount) VALUES (?, ?, ?)",
            (budget_id, desc_enc, amt_enc)
        )
        self.conn.commit()

    def get_items(self, budget_id):
        self.cursor.execute(
            "SELECT id, description, amount FROM items WHERE budget_id = ?", 
            (budget_id,)
        )
        return self.cursor.fetchall()

    def update_item(self, item_id, desc_enc, amt_enc):
        self.cursor.execute(
            "UPDATE items SET description = ?, amount = ? WHERE id = ?",
            (desc_enc, amt_enc, item_id)
        )
        self.conn.commit()

    def delete_item(self, item_id):
        self.cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

# --- User Interface ---

def main():
    crypto = CryptoManager()
    db = BudgetDB()

    while True:
        print("\n=== Encrypted Budget Manager ===")
        print("1. Create New Budget")
        print("2. Manage Existing Budgets (Open/Rename/Delete)")
        print("3. Exit")
        
        choice = input("Select option: ")

        if choice == '1':
            name = input("Enter unique budget name: ")
            if db.create_budget(name):
                print(f"Budget '{name}' created.")
            else:
                print("Error: Budget name already exists.")

        elif choice == '2':
            manage_budgets_menu(db, crypto)

        elif choice == '3':
            db.close()
            print("Goodbye.")
            break

def manage_budgets_menu(db, crypto):
    while True:
        budgets = db.get_budgets()
        if not budgets:
            print("\nNo budgets found.")
            return

        print("\n--- Available Budgets ---")
        for b in budgets:
            print(f"ID: {b[0]} | Name: {b[1]}")
        print("-------------------------")
        print("Actions: [O]pen ID, [R]ename ID, [D]elete ID, [B]ack")
        
        # Example Input: "O 1" to Open ID 1
        cmd = input("Command (e.g., 'O 1'): ").split()
        if not cmd: continue
        
        action = cmd[0].upper()
        
        if action == 'B':
            break

        if len(cmd) < 2:
            print("Please provide an ID (e.g., 'O 5').")
            continue

        try:
            b_id = int(cmd[1])
            selected_budget = next((b for b in budgets if b[0] == b_id), None)
            
            if not selected_budget:
                print("Invalid Budget ID.")
                continue

            if action == 'O':
                manage_single_budget(db, crypto, b_id, selected_budget[1])
            elif action == 'R':
                new_name = input(f"Rename '{selected_budget[1]}' to: ")
                if db.update_budget_name(b_id, new_name):
                    print("Budget renamed.")
                else:
                    print("Name already exists.")
            elif action == 'D':
                confirm = input(f"Are you sure you want to DELETE '{selected_budget[1]}' and ALL its encrypted items? (y/n): ")
                if confirm.lower() == 'y':
                    db.delete_budget(b_id)
                    print("Budget deleted.")
        except ValueError:
            print("Invalid input.")

def manage_single_budget(db, crypto, budget_id, budget_name):
    while True:
        print(f"\n>>> Managing: {budget_name} <<<")
        
        # Display current state immediately
        items = db.get_items(budget_id)
        total = 0.0
        
        print(f"{'ID':<4} | {'Description':<30} | {'Amount':>10}")
        print("-" * 50)
        
        for item in items:
            item_id, desc_enc, amt_enc = item
            dec_desc = crypto.decrypt(desc_enc)
            dec_amt_str = crypto.decrypt(amt_enc)
            
            try:
                dec_amt = float(dec_amt_str)
                total += dec_amt
                print(f"{item_id:<4} | {dec_desc:<30} | {dec_amt:>10.2f}")
            except ValueError:
                print(f"{item_id:<4} | {dec_desc:<30} | {'Error':>10}")

        print("-" * 50)
        print(f"{'':<4} | {'TOTAL':<30} | {total:>10.2f}")
        
        print("\nActions: [A]dd Item, [E]dit Item ID, [D]elete Item ID, [B]ack")
        cmd = input("Command: ").split()
        
        if not cmd: continue
        action = cmd[0].upper()

        if action == 'B':
            break
        
        elif action == 'A':
            desc = input("Description: ")
            amt = input("Amount: ")
            db.add_item(budget_id, crypto.encrypt(desc), crypto.encrypt(amt))
            
        elif action in ['E', 'D']:
            if len(cmd) < 2:
                print("Please provide an Item ID.")
                continue
            
            try:
                item_id = int(cmd[1])
                # Validate that the item belongs to the current budget
                if not any(i[0] == item_id for i in items):
                    print("Item ID not found in this budget.")
                    continue

                if action == 'E':
                    new_desc = input("New Description: ")
                    new_amt = input("New Amount: ")
                    db.update_item(item_id, crypto.encrypt(new_desc), crypto.encrypt(new_amt))
                    print("Item updated.")
                
                elif action == 'D':
                    db.delete_item(item_id)
                    print("Item deleted.")
                    
            except ValueError:
                print("Invalid ID format.")

if __name__ == "__main__":
    main()