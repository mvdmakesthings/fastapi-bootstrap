"""
Secure credential handling for AWS and other services.
"""

import base64
import getpass
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import boto3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """Manager for secure credential storage and retrieval."""

    def __init__(self, config_dir: Optional[Path] = None, env_name: str = "dev"):
        """
        Initialize the credential manager.

        Args:
            config_dir: Directory to store encrypted credentials
            env_name: Environment name
        """
        self.config_dir = config_dir or Path.home() / ".fastapi-bootstrap"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.env_name = env_name
        self.creds_file = self.config_dir / f"{self.env_name}_credentials.enc"
        self.key_file = self.config_dir / ".key"

    def _get_encryption_key(self, password: Optional[str] = None) -> bytes:
        """
        Get or create encryption key.

        Args:
            password: Optional password for key derivation

        Returns:
            bytes: Encryption key
        """
        if self.key_file.exists():
            # Use existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Create new key with password
            if password is None:
                password = getpass.getpass(
                    "Enter a password to encrypt your credentials: "
                )

            # Generate a salt
            salt = os.urandom(16)

            # Derive a key from the password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Save salt and key
            with open(self.key_file, "wb") as f:
                f.write(key)

        return key

    def save_credentials(
        self, credentials: Dict[str, Any], password: Optional[str] = None
    ) -> bool:
        """
        Encrypt and save credentials.

        Args:
            credentials: Dictionary of credentials to save
            password: Optional password for encryption

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Get encryption key
            key = self._get_encryption_key(password)

            # Encrypt credentials
            f = Fernet(key)
            encrypted_data = f.encrypt(json.dumps(credentials).encode())

            # Save encrypted credentials
            with open(self.creds_file, "wb") as f:
                f.write(encrypted_data)

            # Set strict permissions
            os.chmod(self.creds_file, 0o600)

            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

    def load_credentials(
        self, password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt credentials.

        Args:
            password: Optional password for decryption

        Returns:
            Dict[str, Any]: Decrypted credentials or None if failed
        """
        if not self.creds_file.exists():
            return None

        try:
            # Get encryption key
            key = self._get_encryption_key(password)

            # Load and decrypt credentials
            with open(self.creds_file, "rb") as f:
                encrypted_data = f.read()

            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)

            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def store_aws_credentials(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_session_token: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        Store AWS credentials securely.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_session_token: Optional AWS session token
            password: Optional password for encryption

        Returns:
            bool: True if stored successfully, False otherwise
        """
        credentials = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }

        if aws_session_token:
            credentials["aws_session_token"] = aws_session_token

        return self.save_credentials(credentials, password)

    def get_aws_credentials(
        self, password: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Get AWS credentials.

        Args:
            password: Optional password for decryption

        Returns:
            Dict[str, str]: AWS credentials or None if failed
        """
        credentials = self.load_credentials(password)
        if credentials:
            aws_creds = {
                "aws_access_key_id": credentials.get("aws_access_key_id", ""),
                "aws_secret_access_key": credentials.get("aws_secret_access_key", ""),
            }

            if "aws_session_token" in credentials:
                aws_creds["aws_session_token"] = credentials["aws_session_token"]

            return aws_creds

        return None

    def store_database_credentials(
        self,
        username: str,
        password: str,
        host: str,
        port: int,
        database_name: str,
        encryption_password: Optional[str] = None,
    ) -> bool:
        """
        Store database credentials securely.

        Args:
            username: Database username
            password: Database password
            host: Database host
            port: Database port
            database_name: Database name
            encryption_password: Optional password for encryption

        Returns:
            bool: True if stored successfully, False otherwise
        """
        credentials = {
            "database": {
                "username": username,
                "password": password,
                "host": host,
                "port": port,
                "database_name": database_name,
            }
        }

        # Load existing credentials if any
        existing_creds = self.load_credentials(encryption_password)
        if existing_creds:
            existing_creds.update(credentials)
            return self.save_credentials(existing_creds, encryption_password)

        return self.save_credentials(credentials, encryption_password)

    def get_database_credentials(
        self, encryption_password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get database credentials.

        Args:
            encryption_password: Optional password for decryption

        Returns:
            Dict[str, Any]: Database credentials or None if failed
        """
        credentials = self.load_credentials(encryption_password)
        if credentials and "database" in credentials:
            return credentials["database"]

        return None

    def store_credentials_in_aws_secrets_manager(
        self, secret_name: str, session: Optional[boto3.Session] = None
    ) -> bool:
        """
        Store credentials in AWS Secrets Manager.

        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            session: Optional boto3 session

        Returns:
            bool: True if stored successfully, False otherwise
        """
        credentials = self.load_credentials()
        if not credentials:
            print("No credentials found to store in AWS Secrets Manager")
            return False

        if session is None:
            session = boto3.Session()

        client = session.client("secretsmanager")

        try:
            # Check if secret exists
            try:
                client.describe_secret(SecretId=secret_name)
                # Update existing secret
                client.update_secret(
                    SecretId=secret_name, SecretString=json.dumps(credentials)
                )
            except client.exceptions.ResourceNotFoundException:
                # Create new secret
                client.create_secret(
                    Name=secret_name, SecretString=json.dumps(credentials)
                )

            return True
        except Exception as e:
            print(f"Error storing credentials in AWS Secrets Manager: {e}")
            return False
