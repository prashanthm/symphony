#!/usr/bin/env python3
"""
Symphony Authentication Commands

Interactive CLI commands for managing authentication credentials
for Symphony integrations with secure local storage.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Try to import the AuthenticationManager, provide stub if not available
try:
    from symphony_core.auth.auth_manager import AuthenticationManager
    AUTH_MANAGER_AVAILABLE = True
except ImportError:
    AUTH_MANAGER_AVAILABLE = False
    
    class AuthenticationManager:
        """Stub AuthenticationManager for testing"""
        def __init__(self):
            self.credentials = {}
            
        def store_credentials(self, service, credentials):
            self.credentials[service] = credentials
            return True
            
        def verify_credentials(self, service):
            return service in self.credentials
            
        def remove_credentials(self, service):
            if service in self.credentials:
                del self.credentials[service]
                return True
            return False
            
        def clear_all_credentials(self):
            services = list(self.credentials.keys())
            self.credentials.clear()
            return services
            
        def get_authentication_status(self):
            status = {}
            for service in ['linear', 'github', 'hubspot']:
                status[service] = {
                    'authenticated': service in self.credentials,
                    'token_type': 'API Token' if service in self.credentials else None,
                    'expires_at': None,
                    'last_verified': None
                }
            return status

console = Console()


@click.group()
def auth():
    """Authentication and credential management"""
    pass


@auth.command()
@click.option('--service', '-s', 
              type=click.Choice(['linear', 'github', 'hubspot']),
              required=True,
              help='Service to authenticate with')
@click.option('--token', '-t', help='Authentication token')
@click.option('--interactive', is_flag=True, help='Interactive token entry')
def login(service: str, token: str, interactive: bool):
    """Authenticate with external services"""
    try:
        auth_manager = AuthenticationManager()
        
        # Use correct capitalization for service names
        service_display = {
            'linear': 'Linear',
            'github': 'GitHub', 
            'hubspot': 'HubSpot'
        }.get(service, service.title())
        
        console.print(f"[purple]🔐 Authenticating with {service_display}[/purple]")
        
        # Get token
        if not token and not interactive:
            console.print("[yellow]Please provide a token using --token or use --interactive[/yellow]")
            return
            
        if interactive:
            if service == 'linear':
                token = Prompt.ask("Enter your Linear API token", password=True)
            elif service == 'github':
                token = Prompt.ask("Enter your GitHub personal access token", password=True)
            elif service == 'hubspot':
                token = Prompt.ask("Enter your HubSpot API key", password=True)
                
        if not token:
            console.print("[red]No token provided[/red]")
            return
            
        # Store credentials
        if service == 'hubspot':
            credentials = {'api_key': token}
        else:
            credentials = {'token': token}
            
        auth_manager.store_credentials(service, credentials)
        
        # Verify credentials
        if auth_manager.verify_credentials(service):
            console.print(f"[green]✅ Successfully authenticated with {service_display}[/green]")
        else:
            console.print(f"[red]❌ Failed to verify credentials for {service_display}[/red]")
            console.print(f"[yellow]The token may be invalid or the service may be unreachable[/yellow]")
            
    except Exception as e:
        service_display = {
            'linear': 'Linear',
            'github': 'GitHub',
            'hubspot': 'HubSpot'
        }.get(service, service.title())
        console.print(f"[red]❌ Error authenticating with {service_display}: {e}[/red]")


@auth.command()
@click.option('--service', '-s',
              type=click.Choice(['linear', 'github', 'hubspot']),
              help='Service to logout from')
@click.option('--all', is_flag=True, help='Logout from all services')
def logout(service: str, all: bool):
    """Remove stored authentication credentials"""
    try:
        auth_manager = AuthenticationManager()
        
        if all:
            console.print("[purple]🚪 Logging out of all services[/purple]")
            services = auth_manager.clear_all_credentials()
            if services:
                console.print(f"[green]✅ Successfully logged out of all services: {', '.join(services)}[/green]")
            else:
                console.print("[yellow]No services were authenticated[/yellow]")
        elif service:
            service_display = {
                'linear': 'Linear',
                'github': 'GitHub',
                'hubspot': 'HubSpot'
            }.get(service, service.title())
            console.print(f"[purple]🚪 Logging out of {service_display}[/purple]")
            if auth_manager.remove_credentials(service):
                console.print(f"[green]✅ Successfully logged out of {service_display}[/green]")
            else:
                console.print(f"[yellow]Not currently authenticated with {service_display}[/yellow]")
        else:
            console.print("[yellow]Please specify --service or --all[/yellow]")
            
    except Exception as e:
        if service:
            service_display = {
                'linear': 'Linear', 
                'github': 'GitHub',
                'hubspot': 'HubSpot'
            }.get(service, service.title())
            console.print(f"[red]❌ Error logging out of {service_display}: {e}[/red]")
        else:
            console.print(f"[red]❌ Error logging out of all services: {e}[/red]")


@auth.command()
def status():
    """Show authentication status for all services"""
    try:
        auth_manager = AuthenticationManager()
        
        console.print("[blue]🔐 Authentication Status[/blue]")
        
        status_table = Table(title="Service Authentication Status")
        status_table.add_column("Service", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Token Type", style="white")
        
        auth_status = auth_manager.get_authentication_status()
        
        for service, status_info in auth_status.items():
            status_icon = "✅ Authenticated" if status_info['authenticated'] else "❌ Not authenticated"
            token_type = status_info.get('token_type', 'None')
            
            service_display = {
                'linear': 'Linear',
                'github': 'GitHub', 
                'hubspot': 'HubSpot'
            }.get(service, service.title())
            
            status_table.add_row(
                service_display,
                status_icon,
                token_type
            )
            
        console.print(status_table)
        
    except Exception as e:
        console.print(f"[red]❌ Error checking authentication status: {e}[/red]")


if __name__ == "__main__":
    auth()