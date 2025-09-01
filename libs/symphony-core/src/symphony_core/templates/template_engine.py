"""
YAML Template Engine for Symphony Configuration System
Provides standardized document generation from YAML templates
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class TemplateValidationError:
    """Template validation error details"""
    field: str
    error_type: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class TemplateInfo:
    """Template metadata information"""
    name: str
    version: str
    description: str
    author: str
    category: str


class TemplateEngine:
    """
    YAML Template Engine for standardized document generation
    
    Features:
    - Load and parse YAML templates
    - Generate formatted documents from templates
    - Validate input parameters against template rules
    - Support default values and substitution
    - Extensible template format
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template engine
        
        Args:
            template_dir: Directory containing YAML templates
        """
        self.template_dir = template_dir or self._get_default_template_dir()
        self.loaded_templates: Dict[str, Dict[str, Any]] = {}
        self.template_cache: Dict[str, Any] = {}
    
    def _get_default_template_dir(self) -> str:
        """Get default template directory"""
        current_dir = Path(__file__).parent
        return str(current_dir)
    
    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load YAML template from file
        
        Args:
            template_name: Name of template (with or without .yaml extension)
            
        Returns:
            Parsed template dictionary
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            yaml.YAMLError: If template YAML is invalid
        """
        # Ensure .yaml extension
        if not template_name.endswith('.yaml'):
            template_name += '.yaml'
        
        # Check cache first
        if template_name in self.loaded_templates:
            return self.loaded_templates[template_name]
        
        # Load from file
        template_path = Path(self.template_dir) / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # Validate template structure
            self._validate_template_structure(template_data, template_name)
            
            # Cache the loaded template
            self.loaded_templates[template_name] = template_data
            
            return template_data
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in template {template_name}: {e}")
    
    def _validate_template_structure(self, template_data: Dict[str, Any], template_name: str):
        """Validate template has required structure"""
        required_sections = ['template_info', 'sections']
        
        for section in required_sections:
            if section not in template_data:
                raise ValueError(f"Template {template_name} missing required section: {section}")
        
        # Validate template_info
        template_info = template_data['template_info']
        required_info_fields = ['name', 'version', 'description', 'category']
        
        for field in required_info_fields:
            if field not in template_info:
                raise ValueError(f"Template {template_name} template_info missing field: {field}")
    
    def generate_document(self, 
                         template_name: str, 
                         parameters: Dict[str, Any], 
                         agent_name: str = "Symphony Agent") -> Dict[str, Any]:
        """
        Generate document from template with parameters
        
        Args:
            template_name: Name of template to use
            parameters: Parameters to substitute in template
            agent_name: Name of agent generating the document
            
        Returns:
            Generated document with metadata
        """
        # Load template
        template = self.load_template(template_name)
        
        # Merge parameters with defaults
        merged_params = self._merge_with_defaults(template, parameters)
        
        # Add system parameters
        system_params = {
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat(),
            'template_name': template_name,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        merged_params.update(system_params)
        
        # Validate parameters
        validation_errors = self._validate_parameters(template, merged_params)
        if validation_errors:
            return {
                'success': False,
                'errors': validation_errors,
                'template_name': template_name
            }
        
        # Generate sections
        generated_sections = {}
        sections = template['sections']
        
        for section_name, section_config in sections.items():
            section_format = section_config.get('format', '')
            
            try:
                generated_sections[section_name] = section_format.format(**merged_params)
            except KeyError as e:
                # Missing parameter for this section
                missing_param = str(e).strip("'")
                generated_sections[section_name] = f"[Missing parameter: {missing_param}]"
        
        # Generate full document
        full_document = self._combine_sections(generated_sections, template)
        
        return {
            'success': True,
            'document': full_document,
            'sections': generated_sections,
            'template_info': template['template_info'],
            'parameters_used': merged_params,
            'generated_at': system_params['timestamp']
        }
    
    def _merge_with_defaults(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user parameters with template defaults"""
        defaults = template.get('default_values', {})
        merged = defaults.copy()
        merged.update(parameters)
        return merged
    
    def _validate_parameters(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> List[TemplateValidationError]:
        """Validate parameters against template rules"""
        errors = []
        validation_rules = template.get('validation_rules', {})
        
        # Check required fields
        required_fields = validation_rules.get('required_fields', [])
        for field in required_fields:
            if field not in parameters or not parameters[field]:
                errors.append(TemplateValidationError(
                    field=field,
                    error_type='required',
                    message=f'Required field {field} is missing or empty'
                ))
        
        # Check minimum lengths
        min_lengths = validation_rules.get('min_length', {})
        for field, min_len in min_lengths.items():
            if field in parameters and len(str(parameters[field])) < min_len:
                errors.append(TemplateValidationError(
                    field=field,
                    error_type='min_length',
                    message=f'Field {field} must be at least {min_len} characters',
                    expected=str(min_len),
                    actual=str(len(str(parameters[field])))
                ))
        
        # Check format patterns
        format_checks = validation_rules.get('format_checks', [])
        for check in format_checks:
            field = check['field']
            pattern = check['pattern']
            
            if field in parameters:
                value = str(parameters[field])
                if not re.search(pattern, value):
                    errors.append(TemplateValidationError(
                        field=field,
                        error_type='format',
                        message=f'Field {field} does not match required format',
                        expected=pattern,
                        actual=value[:50] + '...' if len(value) > 50 else value
                    ))
        
        # Check enum values
        for rule_name, valid_values in validation_rules.items():
            if rule_name.endswith('_values') and isinstance(valid_values, list):
                field_name = rule_name.replace('_values', '')
                if field_name in parameters and parameters[field_name] not in valid_values:
                    errors.append(TemplateValidationError(
                        field=field_name,
                        error_type='enum',
                        message=f'Field {field_name} must be one of: {", ".join(valid_values)}',
                        expected=", ".join(valid_values),
                        actual=str(parameters[field_name])
                    ))
        
        return errors
    
    def _combine_sections(self, sections: Dict[str, str], template: Dict[str, Any]) -> str:
        """Combine generated sections into full document"""
        # Get section order from template (if specified)
        section_order = template.get('section_order', list(sections.keys()))
        
        # Combine sections in specified order
        document_parts = []
        for section_name in section_order:
            if section_name in sections:
                document_parts.append(sections[section_name])
        
        # Add any remaining sections not in the order
        for section_name, content in sections.items():
            if section_name not in section_order:
                document_parts.append(content)
        
        return '\n\n'.join(document_parts)
    
    def list_available_templates(self) -> List[TemplateInfo]:
        """List all available templates in the template directory"""
        templates = []
        template_dir = Path(self.template_dir)
        
        if not template_dir.exists():
            return templates
        
        for template_file in template_dir.glob('*.yaml'):
            try:
                template_data = self.load_template(template_file.stem)
                template_info = template_data['template_info']
                
                templates.append(TemplateInfo(
                    name=template_info['name'],
                    version=template_info['version'],
                    description=template_info['description'],
                    author=template_info['author'],
                    category=template_info['category']
                ))
            except Exception as e:
                # Skip invalid templates
                continue
        
        return templates
    
    def get_template_parameters(self, template_name: str) -> Dict[str, Any]:
        """Get parameter information for a template"""
        template = self.load_template(template_name)
        
        return {
            'template_info': template['template_info'],
            'default_values': template.get('default_values', {}),
            'validation_rules': template.get('validation_rules', {}),
            'required_fields': template.get('validation_rules', {}).get('required_fields', []),
            'sections': list(template['sections'].keys())
        }
    
    def validate_template_parameters(self, template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters without generating document"""
        template = self.load_template(template_name)
        merged_params = self._merge_with_defaults(template, parameters)
        
        validation_errors = self._validate_parameters(template, merged_params)
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors,
            'merged_parameters': merged_params,
            'template_info': template['template_info']
        }


# Utility functions
def create_template_engine(template_dir: Optional[str] = None) -> TemplateEngine:
    """Create a template engine instance"""
    return TemplateEngine(template_dir)


def generate_document_from_template(template_name: str, 
                                   parameters: Dict[str, Any],
                                   agent_name: str = "Symphony Agent",
                                   template_dir: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to generate document from template"""
    engine = TemplateEngine(template_dir)
    return engine.generate_document(template_name, parameters, agent_name)