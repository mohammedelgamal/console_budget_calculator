# Encrypted Console Budget Manager Documentation

## Overview

The **Encrypted Console Budget Manager** is a robust, command-line interface (CLI) application designed for secure personal financial management. It allows users to create multiple budgets, track expenses, and ensure that sensitive financial data is stored securely using industry-standard encryption.

By leveraging **AES-GCM (Advanced Encryption Standard in Galois/Counter Mode)**, the application ensures that even if the database file is compromised, the actual descriptions and amounts of budget items remain unreadable without the corresponding encryption key.

---

## Key Features

| Feature | Description |
| :--- | :--- |
| **Multi-Budget Support** | Create, rename, and manage multiple independent budget categories. |
| **Secure Storage** | All budget item descriptions and amounts are encrypted before being saved to the database. |
| **Full CRUD Operations** | Complete Create, Read, Update, and Delete functionality for both budgets and individual items. |
| **Persistent Database** | Uses SQLite for reliable, local data storage. |
| **Automated Key Management** | Automatically generates and manages a 256-bit AES key for encryption. |
| **Relational Integrity** | Implements foreign key constraints with cascading deletes to maintain data consistency. |

---

## Security Architecture

The application prioritizes data privacy through a multi-layered security approach:

### 1. Encryption Standard
The system uses **AES-GCM (256-bit)**, which provides both confidentiality and authenticity. Each encryption operation generates a unique 12-byte **nonce** (number used once), which is stored alongside the ciphertext to prevent replay attacks and ensure that identical inputs result in different ciphertexts.

### 2. Key Management
- **Key Generation**: On the first run, the application generates a cryptographically secure 256-bit key.
- **Storage**: The key is stored locally in a file named `budget_key.key`.
- **Warning**: The `budget_key.key` file is essential for accessing your data. If this file is lost, the encrypted data in the database cannot be recovered.

### 3. Data Handling
Only the sensitive fields (`description` and `amount`) are encrypted. Budget names and structural metadata remain unencrypted to allow for efficient database indexing and retrieval.

---

## Prerequisites and Installation

### Dependencies
The application requires Python 3.x and the `cryptography` library.

### Installation Steps

1.  **Install the required library**:
    ```bash
    pip install cryptography
    ```

2.  **Download the script using `wget`**:
    Use the following command to download the script.
    ```bash
    wget -O console_budget_calculator.py https://github.com/mohammedelgamal/console_budget_calculator
    ```

3.  **Run the application**:
    ```bash
    python console_budget_calculator.py
    ```

### Making the Script Directly Executable

To run the application simply by typing a short command like `budget` instead of `python console_budget_calculator.py`, you can use a wrapper script or add the script to your system's execution path.

#### Option A: Using a Wrapper Script (Recommended for Windows)

1.  **Rename the script** to a shorter name, e.g., `budget.py`.
2.  **Create a batch file** named `budget.bat` in the same directory with the following content:
    ```batch
    @echo off
    python "%~dp0budget.py" %*
    ```
3.  **Add the script's directory to your system's PATH environment variable.** This allows you to run `budget` from any command prompt or PowerShell window.

#### Option B: Using a Shell Alias or Symbolic Link (Recommended for Linux/macOS)

1.  **Rename the script** to a shorter, executable name, e.g., `budget`.
    ```bash
    mv console_budget_calculator.py budget
    ```
2.  **Make the script executable** and add the Python interpreter shebang line (if not already present):
    ```bash
    # Add this line to the very top of the 'budget' file: #!/usr/bin/env python3
    chmod +x budget
    ```
3.  **Move the script** to a directory included in your system's PATH (e.g., `/usr/local/bin`):
    ```bash
    sudo mv budget /usr/local/bin/
    ```
    You can now run the application from any terminal by simply typing `budget`.

---

## Usage Guide

### Main Menu
Upon launching, you are presented with three primary options:
1. **Create New Budget**: Initialize a new budget category with a unique name.
2. **Manage Existing Budgets**: Access the sub-menu to open, rename, or delete existing budgets.
3. **Exit**: Securely close the database connection and exit the program.

### Managing Budgets
In the budget management menu, you can use the following commands:
- `O <ID>`: **Open** a budget to view and manage its items.
- `R <ID>`: **Rename** an existing budget.
- `D <ID>`: **Delete** a budget and all its associated items.
- `B`: Go **Back** to the main menu.

### Managing Items within a Budget
Once a budget is opened, you can perform the following actions:
- `A`: **Add** a new item (Description and Amount).
- `E <ID>`: **Edit** an existing item's description or amount.
- `D <ID>`: **Delete** a specific item.
- `B`: Go **Back** to the budget list.

---

## Technical Implementation

### Class Structure

#### `CryptoManager`
Responsible for all cryptographic operations.
- `_load_or_generate_key()`: Handles the lifecycle of the encryption key.
- `encrypt(plaintext)`: Encodes text into an encrypted, base64-encoded string.
- `decrypt(token)`: Decodes and decrypts the encrypted string back to plaintext.

#### `BudgetDB`
Manages the SQLite database and executes SQL queries.
- `_create_tables()`: Initializes the `budgets` and `items` tables.
- `create_budget(name)` / `get_budgets()` / `update_budget_name()` / `delete_budget()`: Budget CRUD logic.
- `add_item()` / `get_items()` / `update_item()` / `delete_item()`: Item CRUD logic.

### Database Schema

The application uses two related tables:

**Table: `budgets`**
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `name` | TEXT | UNIQUE |

**Table: `items`**
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `budget_id` | INTEGER | FOREIGN KEY (budgets.id) ON DELETE CASCADE |
| `description` | TEXT | Encrypted String |
| `amount` | TEXT | Encrypted String |

---

## Important Considerations

> [!CAUTION]
> **Key Security**: Never share your `budget_key.key` file. Anyone with access to this file and your `secure_budgets.db` can read your financial data.
>
> **Data Recovery**: There is no "password reset" or recovery mechanism. If you delete the key file, your data is permanently locked.
>
> **Input Validation**: While the application handles basic errors, ensure that "Amount" inputs are numeric to avoid decryption display errors.
