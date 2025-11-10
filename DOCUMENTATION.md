# azptu - Azure PTU CLI - Documentação Completa

## Visão Geral

O **azptu** é uma ferramenta de linha de comando para gerenciar deployments de **Provisioned Throughput Units (PTU)** no Azure AI Foundry. Execute diretamente como `azptu <comando>` sem precisar do prefixo `python`.

### Funcionalidades Principais

- 🤖 **Gerenciamento de Projetos**: Listar e definir projetos AI Foundry como padrão
- 📊 **Deployments PTU**: Criar, atualizar, deletar e consultar deployments PTU
- ✅ **Validação Automática**: Validação de capacidades mínimas e incrementos por modelo
- 💾 **Estado Persistente**: Armazenamento de resource group e subscription para reutilização
- 🌍 **Múltiplos Tipos**: Suporte a Regional, Global e Data Zone deployments
- 🔧 **Azure SDK**: Implementação robusta usando Azure Python SDK
- 📋 **Configuração JSON**: Sistema centralizado de configuração
- 🚀 **Execução Direta**: Execute como `azptu` em vez de `python azptu.py`

## Arquivos do Sistema

### Arquivos Principais

1. **azptu.py** - Aplicação principal
2. **azptu.bat** - Script Windows (Batch) para execução direta
3. **azptu.ps1** - Script PowerShell para execução direta
4. **config_consolidated.json** - Configuração unificada
5. **setup.bat / setup.ps1** - Scripts de instalação automática

### Execução

- **Windows (Batch)**: `azptu <comando>` ou `.\azptu.bat <comando>`
- **PowerShell**: `.\azptu.ps1 <comando>`
- **Linux/Mac**: `./azptu.py <comando>` (após `chmod +x azptu.py`)
- **Fallback**: `python azptu.py <comando>` (qualquer sistema)

## Instalação

### Pré-requisitos

1. **Python 3.8+**
2. **Azure CLI** instalado e configurado
3. **Credenciais Azure** configuradas

### Instalação de Dependências

```bash
pip install -r requirements.txt
```

### Autenticação Azure

```bash
# Fazer login no Azure CLI
az login

# Verificar subscription ativa
az account show

# Trocar subscription se necessário
az account set --subscription "sua-subscription-id"
```

## Configuração

### Arquivo de Configuração (config_consolidated.json)

O sistema utiliza um arquivo JSON centralizado que contém:

- **ptu_requirements**: Requisitos mínimos e incrementos por modelo
- **ptu_models**: Lista de modelos disponíveis com versões
- **messages**: Mensagens localizadas (português)
- **deployment_types**: Configurações de tipos de deployment
- **settings**: Configurações gerais do sistema

### Estado Persistente

O CLI mantém estado persistente em `.cli_state` com:
- Resource Group padrão
- Subscription padrão
- Cache de projetos
- Expiração automática (5 minutos por padrão)

## Comandos Disponíveis

### Gerenciamento de Projetos

#### `list-projects`
Lista todos os projetos AI disponíveis na subscription.

```bash
python ai_foundry_ptu_cli_consolidated.py list-projects
```

**Saída:**
```
Projetos AI disponíveis:
----------------------------------------
 1. ✓ meu-ai-foundry
    Resource Group: rg-ai-foundry
    Location: eastus
    Kind: AIServices
    Endpoint: https://meu-ai-foundry.openai.azure.com/

 2. ✓ outro-projeto
    Resource Group: rg-projects
    Location: westeurope
    Kind: OpenAI

Projeto atual: (não definido)
```

#### `set-project <projeto>`
Define um projeto como padrão para os comandos.

```bash
python ai_foundry_ptu_cli_consolidated.py set-project meu-ai-foundry
```

### Estado Persistente

#### `set-resource-group <nome>`
Define resource group padrão para comandos PTU.

```bash
python ai_foundry_ptu_cli_consolidated.py set-resource-group rg-ai-foundry
```

#### `set-subscription <id>`
Define subscription padrão para comandos PTU.

```bash
python ai_foundry_ptu_cli_consolidated.py set-subscription fad729f9-287d-4b9d-baa0-ee7a900f3f93
```

#### `show-config`
Mostra configuração atual (resource group, subscription).

```bash
python ai_foundry_ptu_cli_consolidated.py show-config
```

**Saída:**
```
Estado Persistente Atual
--------------------------------------------------
Resource Group: rg-ai-foundry
Subscription: fad729f9-287d-4b9d-baa0-ee7a900f3f93
```

#### `logoff`
Limpa todo o estado persistente salvo.

```bash
python ai_foundry_ptu_cli_consolidated.py logoff
```

### Informações de Modelos

#### `list-ptu-models`
Lista modelos disponíveis para PTU com requisitos.

```bash
python ai_foundry_ptu_cli_consolidated.py list-ptu-models
```

**Saída:**
```
🤖 Modelos Disponíveis para PTU Deployment
============================================================

 1. gpt-4o
    Descrição: GPT-4 Omni - Modelo multimodal avançado
    Versões: 2024-08-06, 2024-11-20, 2024-05-13
    Requisitos PTU:
      Regional: 50 PTU min (incremento 50)
      Global: 100 PTU min (incremento 100)

 2. gpt-4o-mini
    Descrição: GPT-4 Omni Mini - Versão mais eficiente e rápida
    Versões: 2024-07-18, 2024-08-06
    Requisitos PTU:
      Regional: 25 PTU min (incremento 25)
      Global: 50 PTU min (incremento 50)

...

📊 Total: 14 modelos disponíveis
💡 Dica: Use 'create-ptu-deployment' para criar um deployment PTU
```

### Deployments PTU (Azure Python SDK)

#### `create-ptu-deployment`
Cria novo deployment PTU usando Azure Python SDK.

```bash
python ai_foundry_ptu_cli_consolidated.py create-ptu-deployment \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-production \
  --model-name gpt-4o \
  --model-version 2024-08-06 \
  --capacity 100 \
  --deployment-type regional
```

**Parâmetros:**
- `--subscription-id` (opcional se definido no estado)
- `--resource-group` (opcional se definido no estado)
- `--account-name` (obrigatório) - Nome do recurso Azure AI Services
- `--deployment-name` (obrigatório) - Nome do deployment
- `--model-name` (obrigatório) - Nome do modelo
- `--model-version` (obrigatório) - Versão do modelo
- `--capacity` (obrigatório) - Capacidade PTU
- `--deployment-type` (opcional) - Tipo: regional, global, data-zone

**Saída de Sucesso:**
```
Criando deployment PTU 'gpt4o-production'...
Resource Group: rg-ai-foundry
AI Services: meu-ai-foundry
Modelo: gpt-4o v2024-08-06
Capacidade: 100 PTUs
Tipo: regional

Criando deployment 'gpt4o-production' com 100 PTUs...
Deployment 'gpt4o-production' criado com sucesso!
  Modelo: gpt-4o v2024-08-06
  Capacidade: 100 PTUs
  Tipo: regional
  SKU: ProvisionedManaged
```

#### `update-ptu-capacity`
Atualiza capacidade PTU de um deployment existente.

```bash
python ai_foundry_ptu_cli_consolidated.py update-ptu-capacity \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-production \
  --new-capacity 200
```

**Saída:**
```
Atualizando capacidade do deployment 'gpt4o-production'...
Resource Group: rg-ai-foundry
AI Services: meu-ai-foundry
Nova capacidade: 200 PTUs

Obtendo informações do deployment 'gpt4o-production'...
Atualizando capacidade de 100 para 200 PTUs...
Capacidade do deployment 'gpt4o-production' atualizada com sucesso!
  Capacidade anterior: 100 PTUs
  Nova capacidade: 200 PTUs
  Modelo: gpt-4o v2024-08-06
```

#### `get-ptu-info`
Obtém informações detalhadas de um deployment.

```bash
python ai_foundry_ptu_cli_consolidated.py get-ptu-info \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-production
```

**Saída:**
```
Obtendo informações do deployment 'gpt4o-production'...

=== Informações do Deployment PTU ===
Nome: gpt4o-production
Modelo: gpt-4o
Versão: 2024-08-06
Formato: OpenAI
SKU: ProvisionedManaged
Capacidade: 200 PTUs
Estado: Succeeded
Resource Group: rg-ai-foundry
AI Services: meu-ai-foundry
```

#### `delete-ptu-deployment`
Deleta um deployment PTU com confirmação.

```bash
python ai_foundry_ptu_cli_consolidated.py delete-ptu-deployment \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-production
```

**Com confirmação:**
```
Preparando para deletar deployment 'gpt4o-production'...
Resource Group: rg-ai-foundry
AI Services: meu-ai-foundry

Informações do deployment:
- Modelo: gpt-4o v2024-08-06
- Capacidade: 200 PTUs
- SKU: ProvisionedManaged
- Estado: Succeeded

Deseja realmente deletar o deployment 'gpt4o-production'? [y/N]: y
Deletando deployment 'gpt4o-production'...
Deployment 'gpt4o-production' deletado com sucesso!
A capacidade PTU foi liberada de volta para a região.
```

**Força (sem confirmação):**
```bash
python ai_foundry_ptu_cli_consolidated.py delete-ptu-deployment \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-production \
  --force
```

### Informações do Sistema

#### `version`
Mostra informações da versão e funcionalidades.

```bash
python ai_foundry_ptu_cli_consolidated.py version
```

**Saída:**
```
AI Foundry PTU CLI Consolidated v1.0.0-consolidated
Azure AI Projects SDK - Versão Consolidada
Funcionalidades:
  • Gerenciamento: list-projects, set-project, list-deployments, list-ptu-models
  • PTU (Python SDK): create-ptu-deployment, update-ptu-capacity, delete-ptu-deployment, get-ptu-info
  • Estado: set-resource-group, set-subscription, show-config, logoff
Configuração: Centralizada em JSON, mensagens localizáveis, validação PTU
Estado: Resource Group e Subscription podem ser armazenados para uso futuro
Implementação: Azure Python SDK para máxima compatibilidade e confiabilidade
```

## Validação PTU

### Sistema de Validação

O CLI inclui validação automática de capacidades PTU baseada em:

1. **Capacidade Mínima**: Cada modelo tem uma capacidade mínima específica
2. **Incrementos**: Capacidades devem seguir incrementos específicos
3. **Tipo de Deployment**: Regional vs Global vs Data Zone têm regras diferentes

### Exemplos de Validação

#### Validação Bem-sucedida
```bash
# GPT-4o regional: mínimo 50, incremento 50
python ai_foundry_ptu_cli_consolidated.py create-ptu-deployment \
  --model-name gpt-4o --capacity 100  # ✅ Válido (50 + 50)
```

#### Erros de Validação

**Capacidade abaixo do mínimo:**
```
Erro de validação: Capacidade insuficiente para gpt-4o (Regional): mínimo 50, fornecido 25
```

**Incremento incorreto:**
```
Erro de validação: Capacidade 75 PTU inválida para gpt-4o (Regional). Use incrementos de 50
```

**Modelo sem suporte regional:**
```
Erro de validação: Modelo 'gpt-4' não suporta deployment Regional. Use Global ou Data Zone.
```

### Requisitos por Modelo

| Modelo | Regional Min | Regional Inc | Global Min | Global Inc |
|--------|--------------|--------------|------------|------------|
| gpt-4o | 50 | 50 | 100 | 100 |
| gpt-4o-mini | 25 | 25 | 50 | 50 |
| gpt-4-turbo | 50 | 50 | 100 | 100 |
| gpt-4 | N/A | N/A | 300 | 50 |
| gpt-35-turbo | 25 | 25 | 100 | 100 |
| text-embedding-3-large | 100 | 100 | 150 | 50 |
| dall-e-3 | 10 | 10 | 25 | 5 |
| deepseek-r1 | 100 | 100 | 200 | 100 |
| o1-preview | N/A | N/A | 1000 | 100 |

## Tipos de Deployment

### Regional
- **SKU**: ProvisionedManaged
- **Descrição**: Capacidade dedicada em uma região específica
- **Location**: Obrigatório (eastus, westus2, etc.)
- **Latência**: Mais baixa para usuários na região
- **Custo**: Menor que Global/Data Zone

### Global
- **SKU**: GlobalProvisionedManaged
- **Descrição**: Capacidade compartilhada globalmente
- **Location**: Não aplicável
- **Latência**: Variável, roteamento automático
- **Custo**: Maior que Regional

### Data Zone
- **SKU**: DataZoneProvisionedManaged
- **Descrição**: Capacidade dedicada com isolamento de dados
- **Location**: Limitado (eastus, westus2, westeurope, etc.)
- **Compliance**: Maior isolamento de dados
- **Custo**: Maior que Regional

## Fluxos de Trabalho Comuns

### 1. Configuração Inicial

```bash
# 1. Autenticar no Azure
az login

# 2. Configurar defaults
python ai_foundry_ptu_cli_consolidated.py set-resource-group rg-ai-foundry
python ai_foundry_ptu_cli_consolidated.py set-subscription fad729f9-287d-4b9d-baa0-ee7a900f3f93

# 3. Verificar configuração
python ai_foundry_ptu_cli_consolidated.py show-config

# 4. Listar projetos disponíveis
python ai_foundry_ptu_cli_consolidated.py list-projects
```

### 2. Criação de Deployment PTU

```bash
# 1. Ver modelos disponíveis
python ai_foundry_ptu_cli_consolidated.py list-ptu-models

# 2. Criar deployment regional GPT-4o
python ai_foundry_ptu_cli_consolidated.py create-ptu-deployment \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod \
  --model-name gpt-4o \
  --model-version 2024-08-06 \
  --capacity 100 \
  --deployment-type regional

# 3. Verificar deployment criado
python ai_foundry_ptu_cli_consolidated.py get-ptu-info \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod
```

### 3. Escalonamento de Capacidade

```bash
# 1. Verificar capacidade atual
python ai_foundry_ptu_cli_consolidated.py get-ptu-info \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod

# 2. Aumentar capacidade
python ai_foundry_ptu_cli_consolidated.py update-ptu-capacity \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod \
  --new-capacity 200

# 3. Confirmar atualização
python ai_foundry_ptu_cli_consolidated.py get-ptu-info \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod
```

### 4. Limpeza de Recursos

```bash
# 1. Deletar deployment
python ai_foundry_ptu_cli_consolidated.py delete-ptu-deployment \
  --account-name meu-ai-foundry \
  --deployment-name gpt4o-prod

# 2. Limpar estado (opcional)
python ai_foundry_ptu_cli_consolidated.py logoff
```

## Tratamento de Erros

### Erros de Autenticação

**Problema**: `Erro de autenticação: DefaultAzureCredential failed to retrieve a token`

**Solução**:
```bash
az login
az account set --subscription "sua-subscription-id"
```

### Erros de Quota

**Problema**: `Erro: Quota insuficiente para esta capacidade PTU`

**Solução**:
1. Reduzir capacidade solicitada
2. Solicitar aumento de quota no Azure Portal
3. Usar região diferente

**Problema**: `Erro: Capacidade PTU não disponível na região`

**Solução**:
1. Tentar região diferente
2. Reduzir capacidade
3. Usar deployment Global em vez de Regional

### Erros de Validação

**Problema**: Capacidade inválida para modelo

**Solução**:
```bash
# Verificar requisitos do modelo
python ai_foundry_ptu_cli_consolidated.py list-ptu-models

# Ajustar capacidade conforme requisitos
python ai_foundry_ptu_cli_consolidated.py create-ptu-deployment \
  --model-name gpt-4o \
  --capacity 100  # Múltiplo de 50 para Regional
```

### Erros de Resource Group/Subscription

**Problema**: `Resource group não especificado`

**Solução**:
```bash
# Definir defaults
python ai_foundry_ptu_cli_consolidated.py set-resource-group rg-ai-foundry
python ai_foundry_ptu_cli_consolidated.py set-subscription fad729f9-287d-4b9d-baa0-ee7a900f3f93

# Ou especificar nos comandos
python ai_foundry_ptu_cli_consolidated.py create-ptu-deployment \
  --subscription-id fad729f9-287d-4b9d-baa0-ee7a900f3f93 \
  --resource-group rg-ai-foundry \
  ...
```

## Boas Práticas

### 1. Gerenciamento de Estado

- **Sempre configure defaults**: Use `set-resource-group` e `set-subscription`
- **Verifique configuração**: Use `show-config` regularmente
- **Limpe quando necessário**: Use `logoff` para limpar estado

### 2. Planejamento de Capacidade

- **Comece pequeno**: Inicie com capacidade mínima e escale conforme necessário
- **Monitor usage**: Observe utilização antes de escalar
- **Considere custos**: Global PTU é mais caro que Regional

### 3. Nomenclatura

- **Deployments**: Use nomes descritivos (ex: `gpt4o-prod`, `gpt4mini-dev`)
- **Consistência**: Mantenha padrão de nomenclatura na organização
- **Ambiente**: Inclua ambiente no nome quando aplicável

### 4. Segurança

- **Credenciais**: Use DefaultAzureCredential (nunca hardcode)
- **RBAC**: Configure permissões mínimas necessárias
- **Logs**: Monitor ações através dos logs Azure

### 5. Monitoramento

- **Capacity utilization**: Monitore uso de PTU
- **Performance**: Monitore latência e throughput
- **Costs**: Acompanhe custos no Azure Portal

## Estrutura de Custos

### Regional PTU
- Custo por PTU-hora mais baixo
- Ideal para uso consistente em região específica
- Latência otimizada para região

### Global PTU
- Custo por PTU-hora mais alto (~20-30% premium)
- Ideal para uso global ou spiky
- Roteamento automático para melhor disponibilidade

### Data Zone PTU
- Custo premium para isolamento de dados
- Compliance com regulamentações específicas
- Disponível apenas em regiões selecionadas

## Limitações Conhecidas

1. **Deployment Regional**: Alguns modelos (gpt-4, o1-*) não suportam Regional
2. **Data Zone**: Limitado a regiões específicas
3. **Quota**: Sujeito a quotas Azure por região/subscription
4. **Versões de Modelo**: Nem todas as versões estão disponíveis em todas as regiões

## Roadmap Futuro

- **Monitoramento**: Integração com Azure Monitor
- **Auto-scaling**: Ajuste automático de capacidade
- **Cost optimization**: Recomendações de otimização de custos
- **Multi-region**: Gerenciamento de deployments multi-região
- **Templates**: Templates pré-configurados para cenários comuns

## Suporte e Troubleshooting

### Logs e Debug

Para debug detalhado, modifique o logging no arquivo Python:

```python
# No início do arquivo
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verificação de Sistema

```bash
# Verificar Azure CLI
az --version
az account show

# Verificar Python e dependências
python --version
pip list | grep azure

# Verificar conectividade
az cognitiveservices account list --resource-group rg-ai-foundry
```

### Contatos

- **Azure Support**: Portal Azure para questões de quota/billing
- **GitHub Issues**: Para bugs do CLI
- **Documentação**: Microsoft Learn para Azure AI Foundry

---

**Versão**: 1.0.0 Consolidated  
**Última Atualização**: Janeiro 2025  
**Compatibilidade**: Azure AI Foundry, Azure OpenAI Service  
**Autor**: AI Assistant com validação em ambiente real Azure