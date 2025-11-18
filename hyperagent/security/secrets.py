"""Secrets management utilities"""
import os
from typing import Optional
from cryptography.fernet import Fernet
import base64
import hashlib


class SecretsManager:
    """
    Secrets Manager
    
    Concept: Secure storage and retrieval of sensitive data
    Logic: Encrypt secrets at rest, decrypt on demand
    Production: Use AWS Secrets Manager, HashiCorp Vault, etc.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize secrets manager
        
        Logic:
        1. Use provided key or generate from environment
        2. Create Fernet cipher for encryption
        """
        if encryption_key:
            key = self._derive_key(encryption_key)
        else:
            key = os.getenv("SECRETS_ENCRYPTION_KEY")
            if not key:
                # Fallback: generate from app secret (not recommended for production)
                key = self._derive_key(os.getenv("APP_SECRET", "default-secret"))
        
        self.cipher = Fernet(key)
    
    def _derive_key(self, secret: str) -> bytes:
        """Derive 32-byte key from secret string"""
        # Use SHA256 to derive consistent key
        key = hashlib.sha256(secret.encode()).digest()
        # Encode to base64 for Fernet
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def get_secret(secret_name: str, default: Optional[str] = None) -> str:
        """
        Get secret from environment or secrets manager
        
        Logic:
        1. Check environment variables first
        2. Check AWS Secrets Manager (if configured)
        3. Check HashiCorp Vault (if configured)
        4. Return default or raise error
        
        Production: Use cloud secrets manager
        Development: Use environment variables
        """
        # Try environment variable first
        value = os.getenv(secret_name)
        if value:
            return value
        
        # TODO: Integrate with AWS Secrets Manager
        # if os.getenv("AWS_REGION"):
        #     return get_aws_secret(secret_name)
        
        # TODO: Integrate with HashiCorp Vault
        # if os.getenv("VAULT_ADDR"):
        #     return get_vault_secret(secret_name)
        
        if default is not None:
            return default
        
        raise ValueError(f"Secret '{secret_name}' not found and no default provided")
    
    @staticmethod
    def validate_secrets(required_secrets: list) -> dict:
        """
        Validate all required secrets are present
        
        Returns:
            dict with secret_name -> bool (present/absent)
        """
        results = {}
        for secret_name in required_secrets:
            try:
                SecretsManager.get_secret(secret_name)
                results[secret_name] = True
            except ValueError:
                results[secret_name] = False
        
        return results

