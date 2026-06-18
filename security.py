import sqlite3
import os
import json
import base64
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from cryptography.fernet import Fernet

def get_db_connection(db_path: str = "profiles.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = "profiles.db") -> None:
    """Initialize the SQLite database with required tables."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Metadata table (for password verification salt & hash)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Saved profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            search_mode TEXT NOT NULL,
            search_query_encrypted TEXT NOT NULL,
            results_encrypted TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet key from a password and salt using PBKDF2."""
    kdf = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=100000,
        dklen=32
    )
    return base64.urlsafe_b64encode(kdf)

def is_master_password_set(db_path: str = "profiles.db") -> bool:
    """Check if the master password has been configured."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM db_metadata WHERE key = 'password_hash'")
    row = cursor.fetchone()
    conn.close()
    return row is not None

def set_master_password(password: str, db_path: str = "profiles.db") -> bytes:
    """Hash and store a new master password, and return the derived encryption key."""
    init_db(db_path)
    salt = os.urandom(16)
    
    # Hash password using PBKDF2
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=100000,
        dklen=32
    )
    
    salt_hex = salt.hex()
    hash_hex = password_hash.hex()
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('password_salt', ?)", (salt_hex,))
    cursor.execute("INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('password_hash', ?)", (hash_hex,))
    conn.commit()
    conn.close()
    
    # Return the derived encryption key for immediate login session
    return derive_key(password, salt)

def verify_password(password: str, db_path: str = "profiles.db") -> Optional[bytes]:
    """Verify password against stored hash and return derived key if valid, else None."""
    if not is_master_password_set(db_path):
        return None
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM db_metadata WHERE key = 'password_salt'")
    salt_row = cursor.fetchone()
    cursor.execute("SELECT value FROM db_metadata WHERE key = 'password_hash'")
    hash_row = cursor.fetchone()
    
    conn.close()
    
    if not salt_row or not hash_row:
        return None
        
    salt = bytes.fromhex(salt_row["value"])
    stored_hash = bytes.fromhex(hash_row["value"])
    
    # Re-compute hash
    computed_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=100000,
        dklen=32
    )
    
    # Secure comparison to prevent timing attacks
    if hmac_compare_digest(computed_hash, stored_hash):
        return derive_key(password, salt)
    
    return None

import hmac

def hmac_compare_digest(a: bytes, b: bytes) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(a, b)

def encrypt_data(data: str, key: bytes) -> str:
    """Encrypt a plaintext string using Fernet and return base64-encoded ciphertext."""
    f = Fernet(key)
    encrypted_bytes = f.encrypt(data.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_data(ciphertext: str, key: bytes) -> str:
    """Decrypt a base64-encoded ciphertext string using Fernet and return plaintext."""
    f = Fernet(key)
    decrypted_bytes = f.decrypt(ciphertext.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")

def save_profile(search_mode: str, search_query: str, results: List[Dict], key: bytes, db_path: str = "profiles.db") -> None:
    """Encrypt and store a search profile."""
    # Ensure database tables exist
    init_db(db_path)
    
    # Encrypt search query and results list
    encrypted_query = encrypt_data(search_query, key)
    encrypted_results = encrypt_data(json.dumps(results), key)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO saved_profiles (created_at, search_mode, search_query_encrypted, results_encrypted)
        VALUES (?, ?, ?, ?)
        """,
        (current_time, search_mode, encrypted_query, encrypted_results)
    )
    conn.commit()
    conn.close()

def get_saved_profiles(key: bytes, db_path: str = "profiles.db") -> List[Dict]:
    """Retrieve and decrypt all saved profiles."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, search_mode, search_query_encrypted, results_encrypted FROM saved_profiles ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    decrypted_profiles = []
    for row in rows:
        try:
            decrypted_query = decrypt_data(row["search_query_encrypted"], key)
            decrypted_results = json.loads(decrypt_data(row["results_encrypted"], key))
            decrypted_profiles.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "search_mode": row["search_mode"],
                "search_query": decrypted_query,
                "results": decrypted_results
            })
        except Exception as e:
            # Skip profile if decryption fails (e.g. key changed or bad data)
            continue
            
    return decrypted_profiles

def delete_saved_profile(profile_id: int, db_path: str = "profiles.db") -> None:
    """Delete a saved profile by its database ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
