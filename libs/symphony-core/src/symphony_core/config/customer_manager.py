#!/usr/bin/env python3
"""
Customer Configuration Management System

Handles customer configuration storage, validation, and management for Symphony
autonomous enterprise deployments.
"""

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@dataclass
class CustomerProfile:
    """Customer profile information"""

    organization_name: str
    customer_id: str
    industry: str
    business_domain: str
    team_size: int
    implementation_timeline: str
    primary_contact: Dict[str, str]
    technical_contact: Dict[str, str]


@dataclass
class CustomerConfig:
    """Complete customer configuration"""

    schema_version: str
    customer_profile: CustomerProfile
    business_objectives: Dict[str, Any]
    technical_environment: Dict[str, Any]
    operational_constraints: Dict[str, Any]
    agent_configuration: Dict[str, Any]
    integrations: Dict[str, Any]
    monitoring: Dict[str, Any]
    security: Dict[str, Any]
    implementation: Dict[str, Any]
    maintenance: Dict[str, Any]
    metadata: Dict[str, Any]
    created_date: str
    created_by: str


class CustomerConfigManager:
    """Manages customer configurations for Symphony deployments"""

    def __init__(self, symphony_root: Optional[str] = None):
        self.symphony_root = Path(symphony_root or os.getcwd())
        self.organizations_dir = self.symphony_root / "organizations"
        self.customers_dir = self.organizations_dir / "customers"
        self.defaults_dir = self.organizations_dir / "defaults"
        self.schema_file = self.organizations_dir / "config-schema.yaml"

        # Encryption key for sensitive data
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)

        # Ensure directories exist
        self._ensure_directories()

        # Load schema and package configs
        self.schema = self._load_schema()
        self.packages = self._load_packages()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = self.symphony_root / ".symphony_key"

        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Restrict permissions
            return key

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.organizations_dir,
            self.customers_dir,
            self.customers_dir / "templates",
            self.defaults_dir,
            self.defaults_dir / "startup",
            self.defaults_dir / "smb",
            self.defaults_dir / "enterprise",
            self.defaults_dir / "global",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_schema(self) -> Dict[str, Any]:
        """Load configuration schema"""
        if self.schema_file.exists():
            with open(self.schema_file, "r") as f:
                return yaml.safe_load(f)
        return {}

    def _load_packages(self) -> Dict[str, Dict[str, Any]]:
        """Load package configurations"""
        packages = {}
        for package_type in ["startup", "smb", "enterprise", "global"]:
            package_file = self.defaults_dir / package_type / "package-config.yaml"
            if package_file.exists():
                with open(package_file, "r") as f:
                    packages[package_type] = yaml.safe_load(f)
        return packages

    def create_customer_directory(self, customer_id: str) -> Path:
        """Create directory structure for a new customer"""
        customer_dir = self.customers_dir / customer_id

        # Create customer directory structure
        directories = [
            customer_dir,
            customer_dir / "config",
            customer_dir / "deployment",
            customer_dir / "agents",
            customer_dir / "integrations",
            customer_dir / "monitoring",
            customer_dir / "state",
            customer_dir / "logs",
            customer_dir / "backups",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        return customer_dir

    def generate_customer_config(
        self,
        organization_name: str,
        customer_id: str,
        industry: str,
        package_type: str = "startup",
        **kwargs,
    ) -> CustomerConfig:
        """Generate a customer configuration from template and package defaults"""

        # Load package defaults
        if package_type not in self.packages:
            raise ValueError(f"Unknown package type: {package_type}")

        package_config = self.packages[package_type]

        # Create customer profile
        profile = CustomerProfile(
            organization_name=organization_name,
            customer_id=customer_id,
            industry=industry,
            business_domain=kwargs.get("business_domain", "general"),
            team_size=kwargs.get("team_size", 10),
            implementation_timeline=package_config["package_info"][
                "implementation_time"
            ],
            primary_contact=kwargs.get("primary_contact", {}),
            technical_contact=kwargs.get("technical_contact", {}),
        )

        # Create base configuration
        config = CustomerConfig(
            schema_version="2025.1",
            customer_profile=profile,
            business_objectives=package_config.get("default_configuration", {}).get(
                "business_objectives", {}
            ),
            technical_environment=package_config.get("default_configuration", {}).get(
                "technical_environment", {}
            ),
            operational_constraints=package_config.get("default_configuration", {}).get(
                "operational_constraints", {}
            ),
            agent_configuration={
                "selected_package": package_type,
                "agents": package_config.get("agents", {}),
                "performance_targets": package_config.get("default_configuration", {})
                .get("agent_configuration", {})
                .get("performance_targets", {}),
            },
            integrations={
                "linear": {"enabled": True},
                "github": {"enabled": True},
                "slack": {"enabled": False},
                "hubspot": {"enabled": False},
                "quickbooks": {"enabled": False},
            },
            monitoring=package_config.get("default_configuration", {}).get(
                "monitoring", {}
            ),
            security={
                "data_encryption": "standard",
                "access_controls": [],
                "audit_logging": True,
                "compliance_monitoring": True,
            },
            implementation=package_config.get("implementation", {}),
            maintenance=package_config.get("maintenance", {}),
            metadata={
                "version_history": [],
                "validation_status": "pending",
                "deployment_status": "not_deployed",
                "package_info": package_config["package_info"],
            },
            created_date=datetime.now(timezone.utc).isoformat(),
            created_by="symphony-cli",
        )

        return config

    def save_customer_config(self, customer_config: CustomerConfig) -> Path:
        """Save customer configuration to disk"""
        customer_id = customer_config.customer_profile.customer_id
        customer_dir = self.create_customer_directory(customer_id)
        config_file = customer_dir / "config" / "customer-config.yaml"

        # Convert to dictionary and encrypt sensitive fields
        config_dict = asdict(customer_config)
        config_dict = self._encrypt_sensitive_fields(config_dict)

        # Save configuration
        with open(config_file, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        # Save metadata
        metadata_file = customer_dir / "config" / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(
                {
                    "customer_id": customer_id,
                    "organization_name": customer_config.customer_profile.organization_name,
                    "industry": customer_config.customer_profile.industry,
                    "package_type": customer_config.agent_configuration[
                        "selected_package"
                    ],
                    "created_date": customer_config.created_date,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "config_hash": self._calculate_config_hash(config_dict),
                },
                f,
                indent=2,
            )

        logger.info(f"Customer configuration saved: {config_file}")
        return config_file

    def load_customer_config(self, customer_id: str) -> Optional[CustomerConfig]:
        """Load customer configuration from disk"""
        config_file = (
            self.customers_dir / customer_id / "config" / "customer-config.yaml"
        )

        if not config_file.exists():
            logger.warning(f"Customer config not found: {customer_id}")
            return None

        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)

        # Decrypt sensitive fields
        config_dict = self._decrypt_sensitive_fields(config_dict)

        # Convert to CustomerConfig object
        # Note: This is simplified - in production, you'd want proper deserialization
        return config_dict

    def list_customers(self) -> List[Dict[str, Any]]:
        """List all customers with their basic information"""
        customers = []

        for customer_dir in self.customers_dir.iterdir():
            if customer_dir.is_dir() and customer_dir.name != "templates":
                metadata_file = customer_dir / "config" / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    customers.append(metadata)

        return sorted(customers, key=lambda x: x.get("created_date", ""))

    def validate_customer_config(
        self, config: Union[CustomerConfig, Dict[str, Any]]
    ) -> List[str]:
        """Validate customer configuration against schema"""
        errors = []

        if isinstance(config, CustomerConfig):
            config_dict = asdict(config)
        else:
            config_dict = config

        # Basic validation - in production, use jsonschema or similar
        required_fields = [
            "customer_profile.organization_name",
            "customer_profile.customer_id",
            "customer_profile.industry",
            "agent_configuration.selected_package",
        ]

        for field_path in required_fields:
            if not self._get_nested_field(config_dict, field_path):
                errors.append(f"Required field missing: {field_path}")

        # Validate package type
        package_type = self._get_nested_field(
            config_dict, "agent_configuration.selected_package"
        )
        if package_type and package_type not in self.packages:
            errors.append(f"Invalid package type: {package_type}")

        return errors

    def update_customer_config(self, customer_id: str, updates: Dict[str, Any]) -> bool:
        """Update customer configuration with new values"""
        config_dict = self.load_customer_config(customer_id)
        if not config_dict:
            return False

        # Apply updates
        config_dict = self._deep_update(config_dict, updates)

        # Update metadata
        config_dict["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        config_dict["metadata"]["version_history"].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updates": updates,
                "updated_by": "symphony-cli",
            }
        )

        # Validate and save
        errors = self.validate_customer_config(config_dict)
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            return False

        # Save updated configuration
        customer_dir = self.customers_dir / customer_id
        config_file = customer_dir / "config" / "customer-config.yaml"

        with open(config_file, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        return True

    def get_customer_status(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive customer status information"""
        customer_dir = self.customers_dir / customer_id

        if not customer_dir.exists():
            return {"error": "Customer not found"}

        status = {
            "customer_id": customer_id,
            "config_exists": (
                customer_dir / "config" / "customer-config.yaml"
            ).exists(),
            "deployment_status": "unknown",
            "agent_status": {},
            "integration_status": {},
            "monitoring_status": {},
            "last_activity": None,
        }

        # Load metadata if exists
        metadata_file = customer_dir / "config" / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            status.update(metadata)

        # Check state files
        state_dir = customer_dir / "state"
        if state_dir.exists():
            for state_file in state_dir.glob("*.json"):
                with open(state_file, "r") as f:
                    state_data = json.load(f)
                status[state_file.stem] = state_data

        return status

    def _encrypt_sensitive_fields(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in configuration"""
        sensitive_paths = [
            "integrations.linear.api_token",
            "integrations.github.api_token",
            "integrations.slack.bot_token",
            "integrations.hubspot.api_key",
            "integrations.quickbooks.client_secret",
        ]

        result = config_dict.copy()

        for path in sensitive_paths:
            value = self._get_nested_field(result, path)
            if value and not value.startswith("encrypted:"):
                encrypted_value = self.cipher.encrypt(value.encode()).decode()
                self._set_nested_field(result, path, f"encrypted:{encrypted_value}")

        return result

    def _decrypt_sensitive_fields(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in configuration"""
        sensitive_paths = [
            "integrations.linear.api_token",
            "integrations.github.api_token",
            "integrations.slack.bot_token",
            "integrations.hubspot.api_key",
            "integrations.quickbooks.client_secret",
        ]

        result = config_dict.copy()

        for path in sensitive_paths:
            value = self._get_nested_field(result, path)
            if value and isinstance(value, str) and value.startswith("encrypted:"):
                try:
                    encrypted_data = value[10:]  # Remove 'encrypted:' prefix
                    decrypted_value = self.cipher.decrypt(
                        encrypted_data.encode()
                    ).decode()
                    self._set_nested_field(result, path, decrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt field {path}: {e}")

        return result

    def _get_nested_field(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested field value using dot notation"""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _set_nested_field(self, data: Dict[str, Any], path: str, value: Any):
        """Set nested field value using dot notation"""
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _deep_update(
        self, base: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep update dictionary with another dictionary"""
        result = base.copy()

        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value

        return result

    def _calculate_config_hash(self, config_dict: Dict[str, Any]) -> str:
        """Calculate hash of configuration for change tracking"""
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


# Utility functions for CLI integration
def get_customer_manager(symphony_root: Optional[str] = None) -> CustomerConfigManager:
    """Get configured customer manager instance"""
    return CustomerConfigManager(symphony_root)


def create_customer_from_template(
    organization_name: str,
    customer_id: str,
    industry: str,
    package_type: str = "startup",
    **kwargs,
) -> CustomerConfig:
    """Create customer configuration from template"""
    manager = get_customer_manager()
    return manager.generate_customer_config(
        organization_name, customer_id, industry, package_type, **kwargs
    )


def save_customer_configuration(config: CustomerConfig) -> Path:
    """Save customer configuration to disk"""
    manager = get_customer_manager()
    return manager.save_customer_config(config)
