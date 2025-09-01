#!/usr/bin/env python3
"""
Authentication Manager

Manages authentication tokens and credentials for Symphony integrations
with secure local storage.
"""

import json
import logging
import os
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """Authentication token with metadata"""
    service: str
    token_type: str  # 'oauth', 'api_token', 'personal_access_token'
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    scopes: List[str] = None
    user_info: Dict[str, Any] = None
    created_at: str = None
    last_validated: Optional[str] = None
    is_valid: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.scopes is None:
            self.scopes = []
        if self.user_info is None:
            self.user_info = {}

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        
        expiry = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) >= expiry

    def expires_soon(self, minutes: int = 5) -> bool:
        """Check if token expires within specified minutes"""
        if not self.expires_at:
            return False
        
        expiry = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        warning_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        return warning_time >= expiry


class AuthenticationManager:
    """Manages authentication for Symphony integrations"""
    
    def __init__(self, symphony_root: Optional[str] = None):
        self.symphony_root = Path(symphony_root or Path.cwd())
        self.auth_dir = self.symphony_root / ".symphony" / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        
        # Encryption setup
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Supported services
        self.supported_services = {
            'linear': {
                'name': 'Linear',
                'token_type': 'personal_access_token',
                'scopes': ['read', 'write'],
                'validation_endpoint': 'https://api.linear.app/graphql',
                'docs_url': 'https://developers.linear.app/docs/graphql/working-with-the-graphql-api'
            },
            'github': {
                'name': 'GitHub',
                'token_type': 'personal_access_token',
                'scopes': ['repo', 'workflow', 'read:org'],
                'validation_endpoint': 'https://api.github.com/user',
                'docs_url': 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token'
            },
            'slack': {
                'name': 'Slack',
                'token_type': 'oauth',
                'scopes': ['channels:read', 'chat:write', 'commands'],
                'validation_endpoint': 'https://slack.com/api/auth.test',
                'docs_url': 'https://api.slack.com/authentication/token-types'
            },
            'hubspot': {
                'name': 'HubSpot',
                'token_type': 'oauth',
                'scopes': ['contacts', 'content'],
                'validation_endpoint': 'https://api.hubapi.com/oauth/v1/access-tokens/',
                'docs_url': 'https://developers.hubspot.com/docs/api/working-with-oauth'
            }
        }
        
        logger.info("Authentication Manager initialized")
    
    def store_token(
        self, 
        service: str, 
        access_token: str,
        token_type: str = None,
        refresh_token: str = None,
        expires_in: int = None,
        scopes: List[str] = None,
        user_info: Dict[str, Any] = None
    ) -> bool:
        """Store authentication token securely"""
        
        if service not in self.supported_services:
            raise ValueError(f"Unsupported service: {service}")
        
        # Calculate expiration time
        expires_at = None
        if expires_in:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
        
        # Use default token type if not specified
        if not token_type:
            token_type = self.supported_services[service]['token_type']
        
        # Use default scopes if not specified
        if not scopes:
            scopes = self.supported_services[service]['scopes']
        
        auth_token = AuthToken(
            service=service,
            token_type=token_type,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=scopes,
            user_info=user_info or {}
        )
        
        try:
            # Encrypt and save token
            self._save_encrypted_token(auth_token)
            logger.info(f"Stored authentication token for {service}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store token for {service}: {e}")
            return False
    
    def get_token(self, service: str) -> Optional[AuthToken]:
        """Retrieve authentication token"""
        
        if service not in self.supported_services:
            return None
        
        try:
            return self._load_encrypted_token(service)
        except Exception as e:
            logger.error(f"Failed to load token for {service}: {e}")
            return None
    
    def is_authenticated(self, service: str) -> bool:
        """Check if user is authenticated for a service"""
        
        token = self.get_token(service)
        if not token:
            return False
        
        # Check if token is expired
        if token.is_expired():
            logger.info(f"Token for {service} has expired")
            return False
        
        return token.is_valid
    
    async def validate_token(self, service: str) -> Dict[str, Any]:
        """Validate token by making API call"""
        
        token = self.get_token(service)
        if not token:
            return {
                'valid': False,
                'error': f'No token found for {service}'
            }
        
        # Check expiration first
        if token.is_expired():
            return {
                'valid': False,
                'error': f'Token for {service} has expired'
            }
        
        try:
            # Service-specific validation
            validation_result = await self._validate_service_token(service, token)
            
            # Update token status
            token.last_validated = datetime.now(timezone.utc).isoformat()
            token.is_valid = validation_result['valid']
            
            # Save updated token
            if validation_result['valid']:
                self._save_encrypted_token(token)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Token validation failed for {service}: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def revoke_token(self, service: str) -> bool:
        """Revoke/delete authentication token"""
        
        token_file = self.auth_dir / f"{service}_token.enc"
        
        try:
            if token_file.exists():
                token_file.unlink()
                logger.info(f"Revoked token for {service}")
                return True
            else:
                logger.warning(f"No token found for {service}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke token for {service}: {e}")
            return False
    
    def list_authenticated_services(self) -> List[Dict[str, Any]]:
        """List all authenticated services with status"""
        
        services = []
        
        for service_id, service_info in self.supported_services.items():
            token = self.get_token(service_id)
            
            service_status = {
                'service': service_id,
                'name': service_info['name'],
                'authenticated': False,
                'token_type': service_info['token_type'],
                'expires_at': None,
                'expires_soon': False,
                'last_validated': None,
                'scopes': [],
                'user_info': {}
            }
            
            if token:
                service_status.update({
                    'authenticated': not token.is_expired() and token.is_valid,
                    'expires_at': token.expires_at,
                    'expires_soon': token.expires_soon(),
                    'last_validated': token.last_validated,
                    'scopes': token.scopes,
                    'user_info': token.user_info
                })
            
            services.append(service_status)
        
        return services
    
    def get_service_info(self, service: str) -> Optional[Dict[str, Any]]:
        """Get information about a supported service"""
        
        if service not in self.supported_services:
            return None
        
        info = self.supported_services[service].copy()
        
        # Add authentication status
        token = self.get_token(service)
        info['authenticated'] = bool(token and not token.is_expired() and token.is_valid)
        
        if token:
            info['token_info'] = {
                'created_at': token.created_at,
                'expires_at': token.expires_at,
                'last_validated': token.last_validated,
                'scopes': token.scopes
            }
        
        return info
    
    def export_config_template(self) -> Dict[str, Any]:
        """Export configuration template for environment setup"""
        
        template = {
            'environment_variables': {},
            'authentication_guide': {},
            'services': {}
        }
        
        for service_id, service_info in self.supported_services.items():
            env_var = f"{service_id.upper()}_TOKEN"
            
            template['environment_variables'][env_var] = f"your_{service_id}_token_here"
            
            template['authentication_guide'][service_id] = {
                'name': service_info['name'],
                'token_type': service_info['token_type'],
                'required_scopes': service_info['scopes'],
                'documentation': service_info['docs_url'],
                'environment_variable': env_var
            }
            
            template['services'][service_id] = {
                'enabled': False,
                'token_source': 'environment',  # or 'interactive', 'file'
                'validation_enabled': True
            }
        
        return template
    
    # Internal methods
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure token storage"""
        
        key_file = self.symphony_root / ".symphony_auth_key"
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Secure file permissions
            key_file.chmod(0o600)
            logger.info("Generated new encryption key for authentication")
            
        except Exception as e:
            logger.error(f"Could not save encryption key: {e}")
        
        return key
    
    def _save_encrypted_token(self, auth_token: AuthToken):
        """Save encrypted authentication token"""
        
        token_file = self.auth_dir / f"{auth_token.service}_token.enc"
        
        # Convert to dict and encrypt
        token_dict = asdict(auth_token)
        token_json = json.dumps(token_dict)
        encrypted_data = self.cipher.encrypt(token_json.encode())
        
        with open(token_file, 'wb') as f:
            f.write(encrypted_data)
        
        # Secure file permissions
        token_file.chmod(0o600)
    
    def _load_encrypted_token(self, service: str) -> Optional[AuthToken]:
        """Load encrypted authentication token"""
        
        token_file = self.auth_dir / f"{service}_token.enc"
        
        if not token_file.exists():
            return None
        
        with open(token_file, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt and reconstruct
        decrypted_data = self.cipher.decrypt(encrypted_data)
        token_dict = json.loads(decrypted_data.decode())
        
        return AuthToken(**token_dict)
    
    async def _validate_service_token(self, service: str, token: AuthToken) -> Dict[str, Any]:
        """Validate token against service API"""
        
        # This is a simplified validation - in practice, you'd make actual API calls
        # For now, return based on token structure and expiration
        
        if service == 'linear':
            return await self._validate_linear_token(token)
        elif service == 'github':
            return await self._validate_github_token(token)
        elif service == 'slack':
            return await self._validate_slack_token(token)
        elif service == 'hubspot':
            return await self._validate_hubspot_token(token)
        else:
            return {
                'valid': False,
                'error': f'Validation not implemented for {service}'
            }
    
    async def _validate_linear_token(self, token: AuthToken) -> Dict[str, Any]:
        """Validate Linear API token"""
        
        # Basic validation - check token format
        if not token.access_token or len(token.access_token) < 20:
            return {
                'valid': False,
                'error': 'Invalid Linear token format'
            }
        
        # In a real implementation, you'd make a GraphQL query to Linear API
        return {
            'valid': True,
            'service': 'linear',
            'user_info': token.user_info,
            'scopes': token.scopes
        }
    
    async def _validate_github_token(self, token: AuthToken) -> Dict[str, Any]:
        """Validate GitHub API token"""
        
        # Basic validation - check token format
        if not token.access_token or not token.access_token.startswith(('ghp_', 'gho_', 'ghu_')):
            return {
                'valid': False,
                'error': 'Invalid GitHub token format'
            }
        
        # In a real implementation, you'd make a request to GitHub API
        return {
            'valid': True,
            'service': 'github',
            'user_info': token.user_info,
            'scopes': token.scopes
        }
    
    async def _validate_slack_token(self, token: AuthToken) -> Dict[str, Any]:
        """Validate Slack API token"""
        
        # Basic validation - check token format
        if not token.access_token or not token.access_token.startswith('xoxb-'):
            return {
                'valid': False,
                'error': 'Invalid Slack token format'
            }
        
        return {
            'valid': True,
            'service': 'slack',
            'user_info': token.user_info,
            'scopes': token.scopes
        }
    
    async def _validate_hubspot_token(self, token: AuthToken) -> Dict[str, Any]:
        """Validate HubSpot API token"""
        
        # Basic validation - check token format
        if not token.access_token or len(token.access_token) < 30:
            return {
                'valid': False,
                'error': 'Invalid HubSpot token format'
            }
        
        return {
            'valid': True,
            'service': 'hubspot',
            'user_info': token.user_info,
            'scopes': token.scopes
        }


# Factory function
def create_auth_manager(symphony_root: Optional[str] = None) -> AuthenticationManager:
    """Create and return an authentication manager instance"""
    return AuthenticationManager(symphony_root)