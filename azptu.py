#!/usr/bin/env python3
"""
azptu - Azure PTU CLI

Uma ferramenta de linha de comando para gerenciar deployments PTU no Azure AI Foundry.
Execute diretamente como: azptu <comando> [opções]

Funcionalidades:
- Gerenciamento de projetos AI Foundry
- Criação, atualização e remoção de deployments PTU
- Validação automática de capacidades PTU por modelo
- Estado persistente para resource group e subscription
- Suporte a todos os tipos de deployment (Regional, Global, Data Zone)
- Interface via Azure CLI e Azure Python SDK

Autor: AI Assistant
Versão: 0.9.0
Data: 2025-11-07
"""

import click
import sys
import json
import os
import requests
import time
import datetime
import subprocess
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Deployment, Sku, DeploymentModel, DeploymentProperties
import logging

# Configuração global
CONFIG = None

# ============================================================================
# CONFIGURAÇÃO E UTILITÁRIOS
# ============================================================================

def load_config():
    """Carrega configurações do arquivo config.json"""
    global CONFIG
    if CONFIG is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
        except FileNotFoundError:
            click.echo(f"[ERRO] Arquivo de configuração não encontrado: {config_path}", err=True)
            sys.exit(1)
        except json.JSONDecodeError as e:
            click.echo(f"[ERRO] Erro ao ler arquivo de configuração: {e}", err=True)
            sys.exit(1)
    return CONFIG

def get_message(category, key, **kwargs):
    """Obtém mensagem localizada do arquivo de configuração"""
    config = load_config()
    try:
        message = config['messages'][category][key]
        if isinstance(message, str) and kwargs:
            return message.format(**kwargs)
        return message
    except KeyError:
        return f"[MENSAGEM NÃO ENCONTRADA: {category}.{key}]"

def get_ptu_requirements():
    """Obtém configurações de requisitos PTU"""
    config = load_config()
    return config['ptu_requirements']

def get_ptu_models():
    """Obtém lista de modelos PTU"""
    config = load_config()
    return config['ptu_models']['models']

# Configurar logging
logging.basicConfig(level=logging.WARNING)

# ============================================================================
# GERENCIAMENTO DE ESTADO
# ============================================================================

class StateManager:
    """Gerenciador de estado da CLI com expiração automática."""
    
    def __init__(self, state_file=".cli_state", expiration_minutes=5):
        self.state_file = state_file
        self.expiration_seconds = expiration_minutes * 60
        self.state = {}
        self._load_state()
    
    def _load_state(self):
        """Carrega o estado do arquivo, verificando expiração."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verificar se o estado expirou
                if 'timestamp' in data:
                    timestamp = data['timestamp']
                    current_time = time.time()
                    
                    if current_time - timestamp < self.expiration_seconds:
                        self.state = data.get('state', {})
                        # Atualizar timestamp de acesso
                        self._save_state()
                    else:
                        # Estado expirado, limpar arquivo
                        self._clear_state()
                else:
                    # Arquivo sem timestamp, considerar inválido
                    self._clear_state()
            else:
                self.state = {}
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            self.state = {}
    
    def _save_state(self):
        """Salva o estado atual no arquivo."""
        try:
            data = {
                'timestamp': time.time(),
                'state': self.state
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            click.echo(f"Aviso: Não foi possível salvar estado: {e}", err=True)
    
    def _clear_state(self):
        """Limpa o estado e remove o arquivo."""
        self.state = {}
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        except Exception:
            pass
    
    def get(self, key, default=None):
        """Obtém um valor do estado."""
        return self.state.get(key, default)
    
    def set(self, key, value):
        """Define um valor no estado."""
        self.state[key] = value
        self._save_state()
    
    def remove(self, key):
        """Remove uma chave do estado."""
        if key in self.state:
            del self.state[key]
            self._save_state()
    
    def clear(self):
        """Limpa todo o estado."""
        self._clear_state()
    
    def get_current_project(self):
        """Obtém o projeto atual."""
        return self.get('current_project')
    
    def set_current_project(self, project_name, project_endpoint=None):
        """Define o projeto atual."""
        project_info = {
            'name': project_name,
            'endpoint': project_endpoint,
            'set_at': datetime.datetime.now().isoformat()
        }
        self.set('current_project', project_info)
    
    def get_projects_cache(self):
        """Obtém a cache de projetos."""
        return self.get('projects_cache', [])
    
    def set_projects_cache(self, projects):
        """Define a cache de projetos."""
        self.set('projects_cache', projects)
    
    def get_resource_group(self):
        """Obtém o resource group atual."""
        rg_data = self.get('resource_group')
        return rg_data.get('name') if rg_data else None
    
    def set_resource_group(self, resource_group):
        """Define o resource group atual."""
        rg_info = {
            'name': resource_group,
            'set_at': datetime.datetime.now().isoformat()
        }
        self.set('resource_group', rg_info)
    
    def get_subscription(self):
        """Obtém a subscription atual."""
        sub_data = self.get('subscription')
        return sub_data.get('id') if sub_data else None
    
    def set_subscription(self, subscription):
        """Define a subscription atual."""
        sub_info = {
            'id': subscription,
            'set_at': datetime.datetime.now().isoformat()
        }
        self.set('subscription', sub_info)

# ============================================================================
# VALIDAÇÃO PTU
# ============================================================================

def validate_ptu_capacity(model_name: str, capacity: int, deployment_type: str = "regional") -> tuple[bool, str]:
    """
    Valida se a capacidade de PTU atende aos requisitos mínimos e incrementos para o modelo especificado.
    
    Args:
        model_name: Nome do modelo (ex: gpt-4o, gpt-4o-mini)
        capacity: Capacidade de PTU solicitada
        deployment_type: Tipo de deployment ('regional', 'global' ou 'data-zone')
    
    Returns:
        tuple: (is_valid, error_message)
    """
    ptu_requirements = get_ptu_requirements()
    
    # Normalizar o nome do modelo - manter exato primeiro, depois variações
    model_key = model_name
    
    # Verificar se o modelo está na nossa base de dados
    if model_key not in ptu_requirements:
        # Tentar algumas variações comuns
        alt_keys = [
            model_name.lower(),
            model_name.replace('_', '-'),
            model_name.replace('-', '_'),
            model_name.lower().replace('_', '-'),
            model_name.lower().replace('-', '_')
        ]
        
        found_key = None
        for alt_key in alt_keys:
            if alt_key in ptu_requirements:
                found_key = alt_key
                break
        
        if not found_key:
            return True, ""  # Se não conhecemos o modelo, não validamos
        
        model_key = found_key
    
    requirements = ptu_requirements[model_key]
    
    # Determinar qual tipo usar (default: regional)
    if deployment_type.lower() in ['global', 'data-zone', 'datazone']:
        min_capacity = requirements['global_min']
        increment = requirements['global_increment']
        type_name = "Global/Data Zone"
    else:
        min_capacity = requirements['regional_min']
        increment = requirements['regional_increment']
        type_name = "Regional"
    
    # Verificar se o deployment regional está disponível para este modelo
    if min_capacity is None:
        if deployment_type.lower() not in ['global', 'data-zone', 'datazone']:
            return False, get_message('errors', 'model_not_support_regional', model_name=model_name)
    
    # Validar capacidade mínima
    if capacity < min_capacity:
        return False, get_message('errors', 'min_capacity_error', 
                                model_name=model_name, type_name=type_name, 
                                min_capacity=min_capacity, capacity=capacity)
    
    # Validar incremento correto
    if (capacity - min_capacity) % increment != 0:
        return False, get_message('errors', 'increment_error',
                                model_name=model_name, type_name=type_name,
                                increment=increment, capacity=capacity)
    
    return True, ""

# ============================================================================
# GERENCIAMENTO DE DEPLOYMENTS PTU (Azure SDK)
# ============================================================================

class DeploymentManager:
    """Gerenciador de deployments PTU usando Azure Python SDK."""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.credential = None
        self.client = None
    
    def get_credential(self):
        """Obter credenciais do Azure."""
        if not self.credential:
            try:
                self.credential = DefaultAzureCredential()
                # Testar as credenciais
                token = self.credential.get_token("https://management.azure.com/.default")
                return self.credential
            except ClientAuthenticationError as e:
                click.echo(f"Erro de autenticação: {e}", err=True)
                click.echo("Certifique-se de estar autenticado no Azure CLI: az login", err=True)
                raise
        return self.credential
    
    def get_management_client(self, subscription_id):
        """Criar cliente do Azure Cognitive Services Management."""
        if not self.client:
            credential = self.get_credential()
            self.client = CognitiveServicesManagementClient(
                credential=credential,
                subscription_id=subscription_id
            )
        return self.client
    
    def create_ptu_deployment(self, subscription_id, resource_group, account_name, 
                            deployment_name, model_name, model_version, 
                            capacity, deployment_type="regional"):
        """
        Criar um novo deployment PTU.
        
        Args:
            subscription_id: ID da subscription Azure
            resource_group: Nome do resource group
            account_name: Nome do recurso AI Services
            deployment_name: Nome do deployment
            model_name: Nome do modelo
            model_version: Versão do modelo
            capacity: Capacidade PTU
            deployment_type: Tipo do deployment (regional, global, data-zone)
        """
        try:
            # Validar capacidade PTU
            is_valid, error_message = validate_ptu_capacity(model_name, capacity, deployment_type)
            if not is_valid:
                raise ValueError(error_message)
            
            # Mapear tipo de deployment para sku-name
            sku_name_map = {
                'regional': 'ProvisionedManaged',
                'global': 'GlobalProvisionedManaged', 
                'data-zone': 'DataZoneProvisionedManaged'
            }
            sku_name = sku_name_map.get(deployment_type.lower(), 'ProvisionedManaged')
            
            # Criar cliente
            client = self.get_management_client(subscription_id)
            
            # Configurar deployment
            deployment_config = Deployment(
                sku=Sku(
                    name=sku_name,
                    capacity=capacity
                ),
                properties=DeploymentProperties(
                    model=DeploymentModel(
                        format="OpenAI",
                        name=model_name,
                        version=model_version
                    )
                )
            )
            
            click.echo(f"Criando deployment '{deployment_name}' com {capacity} PTUs...")
            
            # Criar deployment (operação assíncrona)
            operation = client.deployments.begin_create_or_update(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=deployment_name,
                deployment=deployment_config
            )
            
            # Aguardar conclusão
            result = operation.result()
            
            click.echo(f"Deployment '{deployment_name}' criado com sucesso!")
            click.echo(f"  Modelo: {model_name} v{model_version}")
            click.echo(f"  Capacidade: {capacity} PTUs")
            click.echo(f"  Tipo: {deployment_type}")
            click.echo(f"  SKU: {sku_name}")
            
            return result
            
        except ValueError as e:
            click.echo(f"Erro de validação: {e}", err=True)
            raise
        except HttpResponseError as e:
            if e.status_code == 429:
                click.echo("Erro: Capacidade PTU não disponível na região. Tente uma região diferente ou capacidade menor.", err=True)
            elif e.status_code == 403:
                click.echo("Erro: Quota insuficiente para esta capacidade PTU.", err=True)
            else:
                click.echo(f"Erro HTTP {e.status_code}: {e.message}", err=True)
            raise
        except Exception as e:
            click.echo(f"Erro ao criar deployment: {e}", err=True)
            raise
    
    def update_ptu_capacity(self, subscription_id, resource_group, account_name, 
                          deployment_name, new_capacity, deployment_type="regional"):
        """
        Atualizar a capacidade PTU de um deployment existente.
        
        Args:
            subscription_id: ID da subscription Azure
            resource_group: Nome do resource group
            account_name: Nome do recurso AI Services
            deployment_name: Nome do deployment
            new_capacity: Nova capacidade PTU
            deployment_type: Tipo do deployment
        """
        try:
            # Obter deployment atual
            client = self.get_management_client(subscription_id)
            
            click.echo(f"Obtendo informações do deployment '{deployment_name}'...")
            current_deployment = client.deployments.get(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=deployment_name
            )
            
            # Extrair informações do modelo
            model_name = current_deployment.properties.model.name if current_deployment.properties and current_deployment.properties.model else None
            model_version = current_deployment.properties.model.version if current_deployment.properties and current_deployment.properties.model else None
            
            if not model_name or not model_version:
                raise ValueError("Não foi possível obter informações do modelo do deployment atual")
            
            # Validar nova capacidade
            is_valid, error_message = validate_ptu_capacity(model_name, new_capacity, deployment_type)
            if not is_valid:
                raise ValueError(error_message)
            
            # Mapear tipo de deployment para sku-name
            sku_name_map = {
                'regional': 'ProvisionedManaged',
                'global': 'GlobalProvisionedManaged', 
                'data-zone': 'DataZoneProvisionedManaged'
            }
            sku_name = sku_name_map.get(deployment_type.lower(), 'ProvisionedManaged')
            
            # Configurar novo deployment com capacidade atualizada
            updated_deployment = Deployment(
                sku=Sku(
                    name=sku_name,
                    capacity=new_capacity
                ),
                properties=DeploymentProperties(
                    model=DeploymentModel(
                        format=current_deployment.properties.model.format if current_deployment.properties and current_deployment.properties.model else "OpenAI",
                        name=model_name,
                        version=model_version
                    )
                )
            )
            
            old_capacity = current_deployment.sku.capacity if current_deployment.sku else 0
            click.echo(f"Atualizando capacidade de {old_capacity} para {new_capacity} PTUs...")
            
            # Atualizar deployment
            operation = client.deployments.begin_create_or_update(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=deployment_name,
                deployment=updated_deployment
            )
            
            # Aguardar conclusão
            result = operation.result()
            
            click.echo(f"Capacidade do deployment '{deployment_name}' atualizada com sucesso!")
            click.echo(f"  Capacidade anterior: {old_capacity} PTUs")
            click.echo(f"  Nova capacidade: {new_capacity} PTUs")
            click.echo(f"  Modelo: {model_name} v{model_version}")
            
            return result
            
        except ValueError as e:
            click.echo(f"Erro de validação: {e}", err=True)
            raise
        except HttpResponseError as e:
            if e.status_code == 404:
                click.echo(f"Erro: Deployment '{deployment_name}' não encontrado.", err=True)
            elif e.status_code == 429:
                click.echo("Erro: Nova capacidade PTU não disponível na região.", err=True)
            elif e.status_code == 403:
                click.echo("Erro: Quota insuficiente para a nova capacidade PTU.", err=True)
            else:
                click.echo(f"Erro HTTP {e.status_code}: {e.message}", err=True)
            raise
        except Exception as e:
            click.echo(f"Erro ao atualizar deployment: {e}", err=True)
            raise
    
    def delete_ptu_deployment(self, subscription_id, resource_group, account_name, deployment_name):
        """
        Deletar um deployment PTU.
        
        Args:
            subscription_id: ID da subscription Azure
            resource_group: Nome do resource group
            account_name: Nome do recurso AI Services
            deployment_name: Nome do deployment
        """
        try:
            client = self.get_management_client(subscription_id)
            
            # Confirmar antes de deletar
            if not click.confirm(f"Tem certeza que deseja deletar o deployment '{deployment_name}'?"):
                click.echo("Operação cancelada.")
                return
            
            click.echo(f"Deletando deployment '{deployment_name}'...")
            
            # Deletar deployment
            operation = client.deployments.begin_delete(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=deployment_name
            )
            
            # Aguardar conclusão
            operation.result()
            
            click.echo(f"Deployment '{deployment_name}' deletado com sucesso!")
            click.echo("A capacidade PTU foi liberada de volta para a região.")
            
        except HttpResponseError as e:
            if e.status_code == 404:
                click.echo(f"Erro: Deployment '{deployment_name}' não encontrado.", err=True)
            else:
                click.echo(f"Erro HTTP {e.status_code}: {e.message}", err=True)
            raise
        except Exception as e:
            click.echo(f"Erro ao deletar deployment: {e}", err=True)
            raise
    
    def get_deployment_info(self, subscription_id, resource_group, account_name, deployment_name):
        """
        Obter informações detalhadas de um deployment.
        """
        try:
            client = self.get_management_client(subscription_id)
            
            deployment = client.deployments.get(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=deployment_name
            )
            
            return {
                'name': deployment.name,
                'model_name': deployment.properties.model.name if deployment.properties and deployment.properties.model else 'Unknown',
                'model_version': deployment.properties.model.version if deployment.properties and deployment.properties.model else 'Unknown',
                'model_format': deployment.properties.model.format if deployment.properties and deployment.properties.model else 'Unknown',
                'sku_name': deployment.sku.name if deployment.sku else 'Unknown',
                'capacity': deployment.sku.capacity if deployment.sku else 0,
                'provisioning_state': getattr(deployment.properties, 'provisioning_state', 'Unknown') if deployment.properties else 'Unknown'
            }
            
        except HttpResponseError as e:
            if e.status_code == 404:
                click.echo(f"Deployment '{deployment_name}' não encontrado.", err=True)
                return None
            else:
                raise
        except Exception as e:
            click.echo(f"Erro ao obter informações do deployment: {e}", err=True)
            raise

# ============================================================================
# CLASSE PRINCIPAL CLI
# ============================================================================

class AIFoundryCLI:
    """Classe principal para a aplicação CLI do AI Foundry SDK."""
    
    def __init__(self):
        self.credential = None
        self.client = None
        self.state_manager = StateManager()
    
    def get_credential(self):
        """Obter credenciais do Azure usando DefaultAzureCredential."""
        if not self.credential:
            try:
                self.credential = DefaultAzureCredential()
                # Testar as credenciais
                token = self.credential.get_token("https://management.azure.com/.default")
                return self.credential
            except ClientAuthenticationError as e:
                click.echo(f"Erro de autenticação: {e}", err=True)
                click.echo("Certifique-se de estar autenticado no Azure CLI: az login", err=True)
                sys.exit(1)
        return self.credential
    
    def get_project_client(self, project_endpoint):
        """Criar cliente do projeto AI Foundry."""
        try:
            credential = self.get_credential()
            # Para esta implementação, vamos usar diretamente a API REST
            # O SDK pode ser usado em versões futuras quando estiver mais maduro
            return credential
        except Exception as e:
            click.echo(f"Erro ao criar cliente do projeto: {e}", err=True)
            sys.exit(1)
    
    def list_available_projects(self):
        """Lista projetos disponíveis no Azure."""
        try:
            # Usar Azure CLI para listar recursos AI Services
            result = subprocess.run([
                'az', 'cognitiveservices', 'account', 'list',
                '--query', '[].{name:name,resourceGroup:resourceGroup,location:location,endpoint:properties.endpoint,kind:kind}',
                '--output', 'json'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                resources = json.loads(result.stdout)
                
                # Filtrar apenas recursos AI Services e OpenAI
                ai_resources = [r for r in resources if r['kind'] in ['AIServices', 'OpenAI', 'CognitiveServices']]
                
                # Cache dos projetos
                self.state_manager.set_projects_cache(ai_resources)
                
                return ai_resources
            else:
                click.echo("Erro ao listar recursos do Azure", err=True)
                return []
                
        except Exception as e:
            click.echo(f"Erro ao listar projetos: {e}", err=True)
            return []

# ============================================================================
# COMANDOS CLI
# ============================================================================

@click.group()
def cli():
    """azptu - Azure PTU CLI
    
    Ferramenta de linha de comando para gerenciar deployments PTU no Azure AI Foundry.
    
    Execute 'azptu --help' para ver todos os comandos disponíveis.
    """
    pass

@cli.command('list-projects')
def list_projects():
    """Lista todos os projetos AI disponíveis na subscription atual."""
    try:
        ai_cli = AIFoundryCLI()
        
        # Usar cache se disponível e recente
        cached_projects = ai_cli.state_manager.get_projects_cache()
        
        if cached_projects:
            click.echo("Projetos AI disponíveis (cache):")
            click.echo("-" * 40)
            for i, project in enumerate(cached_projects, 1):
                status = "✓" if project['kind'] in ['AIServices', 'OpenAI'] else "?"
                click.echo(f"{i:2}. {status} {project['name']}")
                click.echo(f"    Resource Group: {project['resourceGroup']}")
                click.echo(f"    Location: {project['location']}")
                click.echo(f"    Kind: {project['kind']}")
                if project.get('endpoint'):
                    click.echo(f"    Endpoint: {project['endpoint']}")
                click.echo()
        else:
            click.echo("Buscando projetos AI disponíveis...")
            projects = ai_cli.list_available_projects()
            
            if projects:
                click.echo(f"Encontrados {len(projects)} projetos AI:")
                click.echo("-" * 40)
                for i, project in enumerate(projects, 1):
                    status = "✓" if project['kind'] in ['AIServices', 'OpenAI'] else "?"
                    click.echo(f"{i:2}. {status} {project['name']}")
                    click.echo(f"    Resource Group: {project['resourceGroup']}")
                    click.echo(f"    Location: {project['location']}")
                    click.echo(f"    Kind: {project['kind']}")
                    if project.get('endpoint'):
                        click.echo(f"    Endpoint: {project['endpoint']}")
                    click.echo()
            else:
                click.echo("Nenhum projeto AI encontrado na subscription.")
        
        current_project = ai_cli.state_manager.get_current_project()
        if current_project:
            click.echo(f"Projeto atual: {current_project['name']}")
        else:
            click.echo("Nenhum projeto definido como padrão.")
            click.echo("Use 'set-project <nome>' para definir um projeto padrão.")
        
    except Exception as e:
        click.echo(f"Erro ao listar projetos: {e}", err=True)
        sys.exit(1)

@cli.command('set-project')
@click.argument('project_name')
@click.option('--endpoint', help='Endpoint do projeto (opcional)')
def set_project(project_name, endpoint):
    """Define o projeto padrão para usar nos comandos."""
    try:
        ai_cli = AIFoundryCLI()
        
        # Verificar se o projeto existe na lista de projetos conhecidos
        projects = ai_cli.state_manager.get_projects_cache()
        
        project_found = False
        if projects:
            for project in projects:
                if project['name'] == project_name:
                    project_found = True
                    endpoint = endpoint or project.get('endpoint')
                    break
        
        if not project_found:
            click.echo(f"Aviso: Projeto '{project_name}' não encontrado na cache.")
            click.echo("Execute 'list-projects' primeiro ou verifique o nome.")
        
        # Definir projeto atual
        ai_cli.state_manager.set_current_project(project_name, endpoint)
        
        click.echo(f"Projeto definido como: {project_name}")
        if endpoint:
            click.echo(f"Endpoint: {endpoint}")
        
    except Exception as e:
        click.echo(f"Erro ao definir projeto: {e}", err=True)
        sys.exit(1)

@cli.command('set-resource-group')
@click.argument('resource_group')
def set_resource_group(resource_group):
    """Define o Resource Group padrão para comandos PTU."""
    try:
        ai_cli = AIFoundryCLI()
        ai_cli.state_manager.set_resource_group(resource_group)
        
        click.echo(f"Resource Group definido como: {resource_group}")
        click.echo("Agora você pode usar comandos PTU sem especificar --resource-group")
        
    except Exception as e:
        click.echo(f"Erro ao definir resource group: {e}", err=True)
        sys.exit(1)

@cli.command('set-subscription')
@click.argument('subscription')
def set_subscription(subscription):
    """Define a Subscription padrão para comandos PTU."""
    try:
        ai_cli = AIFoundryCLI()
        ai_cli.state_manager.set_subscription(subscription)
        
        click.echo(f"Subscription definido como: {subscription}")
        click.echo("Agora você pode usar comandos PTU sem especificar --subscription")
        
    except Exception as e:
        click.echo(f"Erro ao definir subscription: {e}", err=True)
        sys.exit(1)

@cli.command('list-deployments')
@click.option('--project', help='Nome do projeto (usa padrão se não especificado)')
def list_deployments(project):
    """Lista todos os deployments no projeto AI Foundry atual."""
    try:
        ai_cli = AIFoundryCLI()
        
        # Usar projeto especificado ou padrão
        if not project:
            current_project = ai_cli.state_manager.get_current_project()
            if current_project:
                project = current_project['name']
            else:
                click.echo("Nenhum projeto especificado e nenhum projeto padrão definido.", err=True)
                click.echo("Use: list-deployments --project <nome> ou set-project <nome>", err=True)
                sys.exit(1)
        
        click.echo(f"Listando deployments do projeto: {project}")
        click.echo("=" * 50)
        
        # Implementar listagem de deployments usando Azure CLI
        result = subprocess.run([
            'az', 'cognitiveservices', 'account', 'deployment', 'list',
            '--name', project,
            '--resource-group', ai_cli.state_manager.get_resource_group() or 'default',
            '--output', 'json'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            deployments = json.loads(result.stdout)
            
            if deployments:
                for i, deployment in enumerate(deployments, 1):
                    click.echo(f"{i}. {deployment.get('name', 'Unknown')}")
                    # Adicionar mais detalhes conforme disponível na resposta
            else:
                click.echo("Nenhum deployment encontrado.")
        else:
            click.echo("Erro ao listar deployments. Verifique se o projeto existe e você tem permissões.", err=True)
        
    except Exception as e:
        click.echo(f"Erro ao listar deployments: {e}", err=True)
        sys.exit(1)

@cli.command('list-ptu-models')
def list_ptu_models():
    """Lista os modelos OpenAI e DeepSeek disponíveis para PTU deployment com informações de capacidade."""
    try:
        config = load_config()
        ptu_models = get_ptu_models()
        ptu_requirements = get_ptu_requirements()
        
        click.echo("Modelos Disponíveis para PTU Deployment")
        click.echo("=" * 60)
        
        for i, model in enumerate(ptu_models, 1):
            model_name = model['name']
            click.echo(f"\n{i:2}. {model_name}")
            click.echo(f"    Descricao: {model['description']}")
            click.echo(f"    Versoes: {', '.join(model['versions'])}")
            
            # Mostrar requisitos PTU se disponíveis
            if model_name in ptu_requirements:
                req = ptu_requirements[model_name]
                click.echo("    Requisitos PTU:")
                
                if req['regional_min']:
                    click.echo(f"      Regional: {req['regional_min']} PTU min (incremento {req['regional_increment']})")
                else:
                    click.echo("      Regional: Nao disponivel")
                
                click.echo(f"      Global: {req['global_min']} PTU min (incremento {req['global_increment']})")
            else:
                click.echo("    Requisitos PTU: Nao definidos")
        
        click.echo(f"\n{len(ptu_models)} modelos disponíveis")
        click.echo("\nDica: Use 'create-ptu-deployment' para criar um deployment PTU")
        
    except Exception as e:
        click.echo(f"Erro ao listar modelos PTU: {e}", err=True)
        sys.exit(1)

@cli.command('logoff')
def logoff():
    """Faz logoff limpando todo o estado salvo (projeto atual, cache, etc.)."""
    try:
        ai_cli = AIFoundryCLI()
        ai_cli.state_manager.clear()
        
        click.echo("Estado limpo com sucesso!")
        click.echo("- Projeto atual removido")
        click.echo("- Cache de projetos limpo")
        click.echo("- Resource Group removido")
        click.echo("- Subscription removida")
        click.echo("- Arquivo de estado removido")
        
    except Exception as e:
        click.echo(f"Erro ao limpar estado: {e}", err=True)
        sys.exit(1)

@cli.command('show-config')
def show_config():
    """Mostra a configuração persistente atual (resource group, subscription, projeto)."""
    try:
        ai_cli = AIFoundryCLI()
        
        click.echo(f"\n{get_message('info', 'state_info')}")
        click.echo("-" * 50)
        
        resource_group = ai_cli.state_manager.get_resource_group()
        subscription = ai_cli.state_manager.get_subscription()
        
        if resource_group:
            click.echo(get_message('info', 'stored_resource_group', resource_group=resource_group))
        else:
            click.echo("Resource Group: (não definido)")
        
        if subscription:
            click.echo(get_message('info', 'stored_subscription', subscription=subscription))
        else:
            click.echo("Subscription: (não definido)")
        
        if not resource_group and not subscription:
            click.echo(f"\n{get_message('info', 'no_stored_values')}")
            click.echo("Use 'set-resource-group' e 'set-subscription' para definir valores padrão")
        
    except Exception as e:
        click.echo(f"[ERRO] Erro ao verificar estado: {e}", err=True)
        sys.exit(1)

# ============================================================================
# COMANDOS PTU (Azure Python SDK)
# ============================================================================

@cli.command('create-ptu-deployment')
@click.option('--subscription-id', help='ID da subscription Azure')
@click.option('--resource-group', help='Nome do resource group')
@click.option('--account-name', required=True, help='Nome do recurso Azure AI Services')
@click.option('--deployment-name', required=True, help='Nome do deployment')
@click.option('--model-name', required=True, help='Nome do modelo (ex: gpt-4o, gpt-4o-mini)')
@click.option('--model-version', required=True, help='Versão do modelo (ex: 2024-08-06)')
@click.option('--capacity', required=True, type=int, help='Capacidade PTU (respeitando mínimos do modelo)')
@click.option('--deployment-type', default='regional', 
              type=click.Choice(['regional', 'global', 'data-zone'], case_sensitive=False),
              help='Tipo de deployment PTU (padrão: regional)')
def create_ptu_deployment(subscription_id, resource_group, account_name, deployment_name, 
                         model_name, model_version, capacity, deployment_type):
    """Criar novo deployment PTU usando Azure Python SDK."""
    try:
        ai_cli = AIFoundryCLI()
        deployment_manager = DeploymentManager(ai_cli.state_manager)
        
        # Usar valores do estado se não fornecidos
        if not resource_group:
            resource_group = ai_cli.state_manager.get_resource_group()
            if not resource_group:
                click.echo("Resource group é obrigatório. Use --resource-group ou set-resource-group", err=True)
                sys.exit(1)
        
        if not subscription_id:
            subscription_id = ai_cli.state_manager.get_subscription()
            if not subscription_id:
                click.echo("Subscription ID é obrigatório. Use --subscription-id ou set-subscription", err=True)
                sys.exit(1)
        
        click.echo(f"Criando deployment PTU '{deployment_name}'...")
        click.echo(f"Resource Group: {resource_group}")
        click.echo(f"AI Services: {account_name}")
        click.echo(f"Modelo: {model_name} v{model_version}")
        click.echo(f"Capacidade: {capacity} PTUs")
        click.echo(f"Tipo: {deployment_type}")
        
        deployment_manager.create_ptu_deployment(
            subscription_id=subscription_id,
            resource_group=resource_group,
            account_name=account_name,
            deployment_name=deployment_name,
            model_name=model_name,
            model_version=model_version,
            capacity=capacity,
            deployment_type=deployment_type
        )
        
    except Exception as e:
        click.echo(f"Erro ao criar deployment: {e}", err=True)
        sys.exit(1)

@cli.command('update-ptu-capacity')
@click.option('--subscription-id', help='ID da subscription Azure')
@click.option('--resource-group', help='Nome do resource group')
@click.option('--account-name', required=True, help='Nome do recurso Azure AI Services')
@click.option('--deployment-name', required=True, help='Nome do deployment')
@click.option('--new-capacity', required=True, type=int, help='Nova capacidade PTU')
@click.option('--deployment-type', default='regional', 
              type=click.Choice(['regional', 'global', 'data-zone'], case_sensitive=False),
              help='Tipo de deployment PTU (padrão: regional)')
def update_ptu_capacity(subscription_id, resource_group, account_name, deployment_name, 
                       new_capacity, deployment_type):
    """Atualizar capacidade PTU de deployment existente."""
    try:
        ai_cli = AIFoundryCLI()
        deployment_manager = DeploymentManager(ai_cli.state_manager)
        
        # Usar valores do estado se não fornecidos
        if not resource_group:
            resource_group = ai_cli.state_manager.get_resource_group()
            if not resource_group:
                click.echo("Resource group é obrigatório. Use --resource-group ou set-resource-group", err=True)
                sys.exit(1)
        
        if not subscription_id:
            subscription_id = ai_cli.state_manager.get_subscription()
            if not subscription_id:
                click.echo("Subscription ID é obrigatório. Use --subscription-id ou set-subscription", err=True)
                sys.exit(1)
        
        click.echo(f"Atualizando capacidade do deployment '{deployment_name}'...")
        click.echo(f"Resource Group: {resource_group}")
        click.echo(f"AI Services: {account_name}")
        click.echo(f"Nova capacidade: {new_capacity} PTUs")
        
        deployment_manager.update_ptu_capacity(
            subscription_id=subscription_id,
            resource_group=resource_group,
            account_name=account_name,
            deployment_name=deployment_name,
            new_capacity=new_capacity,
            deployment_type=deployment_type
        )
        
    except Exception as e:
        click.echo(f"Erro ao atualizar deployment: {e}", err=True)
        sys.exit(1)

@cli.command('delete-ptu-deployment')
@click.option('--subscription-id', help='ID da subscription Azure')
@click.option('--resource-group', help='Nome do resource group')
@click.option('--account-name', required=True, help='Nome do recurso Azure AI Services')
@click.option('--deployment-name', required=True, help='Nome do deployment')
@click.option('--force', is_flag=True, help='Pular confirmações (use com cuidado)')
def delete_ptu_deployment(subscription_id, resource_group, account_name, deployment_name, force):
    """Deletar deployment PTU usando Azure Python SDK."""
    try:
        ai_cli = AIFoundryCLI()
        deployment_manager = DeploymentManager(ai_cli.state_manager)
        
        # Usar valores do estado se não fornecidos
        if not resource_group:
            resource_group = ai_cli.state_manager.get_resource_group()
            if not resource_group:
                click.echo("Resource group é obrigatório. Use --resource-group ou set-resource-group", err=True)
                sys.exit(1)
        
        if not subscription_id:
            subscription_id = ai_cli.state_manager.get_subscription()
            if not subscription_id:
                click.echo("Subscription ID é obrigatório. Use --subscription-id ou set-subscription", err=True)
                sys.exit(1)
        
        click.echo(f"Preparando para deletar deployment '{deployment_name}'...")
        click.echo(f"Resource Group: {resource_group}")
        click.echo(f"AI Services: {account_name}")
        
        # Obter informações do deployment antes de deletar
        try:
            deployment_info = deployment_manager.get_deployment_info(
                subscription_id=subscription_id,
                resource_group=resource_group,
                account_name=account_name,
                deployment_name=deployment_name
            )
            
            if deployment_info:
                click.echo(f"\nInformações do deployment:")
                click.echo(f"- Modelo: {deployment_info['model_name']} v{deployment_info['model_version']}")
                click.echo(f"- Capacidade: {deployment_info['capacity']} PTUs")
                click.echo(f"- SKU: {deployment_info['sku_name']}")
                click.echo(f"- Estado: {deployment_info['provisioning_state']}")
            
        except Exception:
            pass  # Se não conseguir obter info, continua com a deleção
        
        if not force:
            if not click.confirm(f"\nDeseja realmente deletar o deployment '{deployment_name}'?"):
                click.echo("Operação cancelada.")
                return
        
        deployment_manager.delete_ptu_deployment(
            subscription_id=subscription_id,
            resource_group=resource_group,
            account_name=account_name,
            deployment_name=deployment_name
        )
        
    except Exception as e:
        click.echo(f"Erro ao deletar deployment: {e}", err=True)
        sys.exit(1)

@cli.command('get-ptu-info')
@click.option('--subscription-id', help='ID da subscription Azure')
@click.option('--resource-group', help='Nome do resource group')
@click.option('--account-name', required=True, help='Nome do recurso Azure AI Services')
@click.option('--deployment-name', required=True, help='Nome do deployment')
def get_ptu_info(subscription_id, resource_group, account_name, deployment_name):
    """Obter informações detalhadas de um deployment PTU."""
    try:
        ai_cli = AIFoundryCLI()
        deployment_manager = DeploymentManager(ai_cli.state_manager)
        
        # Usar valores do estado se não fornecidos
        if not resource_group:
            resource_group = ai_cli.state_manager.get_resource_group()
            if not resource_group:
                click.echo("Resource group é obrigatório. Use --resource-group ou set-resource-group", err=True)
                sys.exit(1)
        
        if not subscription_id:
            subscription_id = ai_cli.state_manager.get_subscription()
            if not subscription_id:
                click.echo("Subscription ID é obrigatório. Use --subscription-id ou set-subscription", err=True)
                sys.exit(1)
        
        click.echo(f"Obtendo informações do deployment '{deployment_name}'...")
        
        deployment_info = deployment_manager.get_deployment_info(
            subscription_id=subscription_id,
            resource_group=resource_group,
            account_name=account_name,
            deployment_name=deployment_name
        )
        
        if deployment_info:
            click.echo(f"\n=== Informações do Deployment PTU ===")
            click.echo(f"Nome: {deployment_info['name']}")
            click.echo(f"Modelo: {deployment_info['model_name']}")
            click.echo(f"Versão: {deployment_info['model_version']}")
            click.echo(f"Formato: {deployment_info['model_format']}")
            click.echo(f"SKU: {deployment_info['sku_name']}")
            click.echo(f"Capacidade: {deployment_info['capacity']} PTUs")
            click.echo(f"Estado: {deployment_info['provisioning_state']}")
            click.echo(f"Resource Group: {resource_group}")
            click.echo(f"AI Services: {account_name}")
        else:
            click.echo(f"Deployment '{deployment_name}' não encontrado.")
        
    except Exception as e:
        click.echo(f"Erro ao obter informações do deployment: {e}", err=True)
        sys.exit(1)

@cli.command()
def version():
    """Mostra a versão da aplicação."""
    config = load_config()
    click.echo(f"azptu - Azure PTU CLI v{config['version']}")
    click.echo("Ferramenta de linha de comando para gerenciar deployments PTU no Azure AI Foundry")
    click.echo()
    click.echo("Funcionalidades:")
    click.echo("  • Gerenciamento: list-projects, set-project, list-deployments, list-ptu-models")
    click.echo("  • PTU (Python SDK): create-ptu-deployment, update-ptu-capacity, delete-ptu-deployment, get-ptu-info")
    click.echo("  • Estado: set-resource-group, set-subscription, show-config, logoff")
    click.echo()
    click.echo("Configuração: Centralizada em JSON, mensagens localizáveis, validação PTU")
    click.echo("Estado: Resource Group e Subscription podem ser armazenados para uso futuro")
    click.echo("Implementação: Azure Python SDK para máxima compatibilidade e confiabilidade")
    click.echo()
    click.echo("Use: azptu --help para lista completa de comandos")

if __name__ == '__main__':
    cli()