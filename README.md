# azptu - Azure PTU CLI

![Azure AI Foundry](https://img.shields.io/badge/Azure-AI%20Foundry-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)
![GitHub](https://img.shields.io/badge/GitHub-pateixei%2Fazptu-black)

Uma ferramenta de linha de comando para gerenciar **Provisioned Throughput Units (PTU)** no Azure AI Foundry com validação automática, estado persistente implementada usando o Azure Python SDK.

Execute diretamente como: `azptu <comando> [opções]`

## ⚡ Quick Start

### 1. Instalação Rápida

**Opção A: Clone do GitHub (Recomendado)**
```bash
# Clone o repositório
git clone https://github.com/pateixei/azptu.git
cd azptu

# Instalar dependências
pip install -r requirements.txt

# Autenticar no Azure
az login
```

**Opção B: Download Manual**
```bash
# Baixe os arquivos do repositório e execute:
pip install -r requirements.txt
az login
```

### 2. Configuração Inicial

```bash
# Definir padrões (substitua pelos seus valores)
azptu set-resource-group "rg-ai-foundry"
azptu set-subscription "00000000-0000-0000-0000-000000000000"

# Verificar configuração
azptu show-config
```

### 3. Primeiro Deployment PTU

```bash
# Listar modelos disponíveis
azptu list-ptu-models

# Criar deployment regional GPT-4o
azptu create-ptu-deployment \
  --account-name "meu-ai-foundry" \
  --deployment-name "gpt4o-production" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --capacity 100 \
  --deployment-type regional
```

## 📁 Arquivos da Versão 

```
📦 azptu-cli/
├── 🐍 azptu.py                              # Aplicação principal (1800+ linhas)
├── 🚀 azptu.bat                             # Script Windows (Batch)
├── ⚡ azptu.ps1                             # Script PowerShell
├── ⚙️ config.json                          # Configuração unificada
├── 📋 requirements.txt                     # Dependências Python
├── 📖 DOCUMENTATION.md                     # Documentação completa
├── 📄 README.md                            # Este arquivo
└── 💾 .cli_state                           # Estado persistente (gerado automaticamente)
```

### Execução Direta

- **Windows (Batch)**: `azptu.bat <comando>` ou `.\azptu <comando>`
- **PowerShell**: `.\azptu.ps1 <comando>`
- **Linux/Mac**: `./azptu.py <comando>` (após `chmod +x azptu.py`)
- **Fallback**: `python azptu.py <comando>` (qualquer sistema)

## 🚀 Funcionalidades Principais

### ✅ Validação Automática PTU
- Capacidades mínimas por modelo
- Incrementos obrigatórios
- Suporte a Regional/Global/Data Zone

### 💾 Estado Persistente
- Resource Group e Subscription salvos
- Cache de projetos
- Expiração automática (5 minutos)

### 🔧 Azure Python SDK
- Implementação robusta e confiável
- Tratamento completo de erros
- Operações assíncronas suportadas

### 🌍 Múltiplos Tipos de Deployment
- **Regional**: Capacidade dedicada por região
- **Global**: Capacidade compartilhada globalmente  
- **Data Zone**: Isolamento de dados aprimorado

### 📊 Modelos Suportados
- **OpenAI**: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- **OpenAI Advanced**: o1-preview, o1-mini
- **DeepSeek**: R1, V3
- **Embeddings**: text-embedding-3-large/small, ada-002
- **Multimodal**: DALL-E 3, Whisper, TTS

## 📋 Comandos Disponíveis

### 🏗️ Gerenciamento de Projetos
```bash
list-projects          # Lista projetos AI disponíveis
set-project <nome>     # Define projeto padrão
```

### 🚀 Deployments PTU (Azure SDK)
```bash
create-ptu-deployment  # Criar novo deployment PTU
update-ptu-capacity    # Atualizar capacidade PTU
delete-ptu-deployment  # Deletar deployment PTU
get-ptu-info          # Informações do deployment
```

### 💾 Estado Persistente
```bash
set-resource-group <nome>    # Definir resource group padrão
set-subscription <id>        # Definir subscription padrão
show-config                  # Mostrar configuração atual
logoff                       # Limpar todo estado
```

### ℹ️ Informações
```bash
list-ptu-models       # Lista modelos com requisitos PTU
version              # Informações da versão
--help               # Ajuda completa
```

## 🔧 Exemplos de Uso

### Cenário: Deployment Completo

```bash
# 1. Configuração inicial
python azptu.py set-resource-group "rg-production"
python azptu.py set-subscription "sua-subscription-id"

# 2. Verificar modelos disponíveis  
python azptu.py list-ptu-models

# 3. Criar deployment regional GPT-4o (100 PTU)
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry-prod" \
  --deployment-name "gpt4o-api" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --capacity 100

# 4. Verificar deployment criado
python azptu.py get-ptu-info \
  --account-name "ai-foundry-prod" \
  --deployment-name "gpt4o-api"

# 5. Escalar para 200 PTU
python azptu.py update-ptu-capacity \
  --account-name "ai-foundry-prod" \
  --deployment-name "gpt4o-api" \
  --new-capacity 200
```

### Cenário: Múltiplos Deployments

```bash
# GPT-4o para produção (Regional)
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry" --deployment-name "gpt4o-prod" \
  --model-name "gpt-4o" --model-version "2024-08-06" --capacity 150

# GPT-4o Mini para desenvolvimento (Regional)  
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry" --deployment-name "gpt4o-mini-dev" \
  --model-name "gpt-4o-mini" --model-version "2024-07-18" --capacity 50

# DeepSeek R1 para pesquisa (Global)
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry" --deployment-name "deepseek-research" \
  --model-name "deepseek-r1" --model-version "2025-01-20" \
  --capacity 200 --deployment-type global
```

## 🎯 Validação PTU Automática

### Exemplos de Validação

#### ✅ Válidos
```bash
# GPT-4o Regional: 50 PTU mínimo, incremento 50
--model-name gpt-4o --capacity 100    # ✅ 50 + (1 × 50)
--model-name gpt-4o --capacity 200    # ✅ 50 + (3 × 50)

# GPT-4o Mini Regional: 25 PTU mínimo, incremento 25  
--model-name gpt-4o-mini --capacity 75   # ✅ 25 + (2 × 25)
```

#### ❌ Inválidos
```bash
# Capacidade insuficiente
--model-name gpt-4o --capacity 25
# Erro: Capacidade insuficiente para gpt-4o (Regional): mínimo 50, fornecido 25

# Incremento incorreto
--model-name gpt-4o --capacity 125  
# Erro: Capacidade 125 PTU inválida para gpt-4o (Regional). Use incrementos de 50

# Tipo não suportado
--model-name gpt-4 --deployment-type regional
# Erro: Modelo 'gpt-4' não suporta deployment Regional. Use Global ou Data Zone.
```

## ⚙️ Configuração Detalhada

### config_consolidated.json

```json
{
  "version": "1.0.0-consolidated",
  "ptu_requirements": {
    "gpt-4o": {
      "regional_min": 50, "regional_increment": 50,
      "global_min": 100, "global_increment": 100
    },
    "gpt-4o-mini": {
      "regional_min": 25, "regional_increment": 25,
      "global_min": 50, "global_increment": 50
    }
    // ... mais modelos
  },
  "ptu_models": {
    "models": [
      {
        "name": "gpt-4o",
        "description": "GPT-4 Omni - Modelo multimodal avançado",
        "versions": ["2024-08-06", "2024-11-20"],
        "supported_regions": ["US East", "US West", "Europe West"]
      }
      // ... mais modelos
    ]
  },
  "messages": {
    // Mensagens localizadas em português
  }
}
```

### Estado Persistente (.cli_state)

```json
{
  "timestamp": 1704671234.567,
  "state": {
    "resource_group": {
      "name": "rg-ai-foundry",
      "set_at": "2024-01-07T14:30:00"
    },
    "subscription": {
      "id": "fad729f9-287d-4b9d-baa0-ee7a900f3f93",
      "set_at": "2024-01-07T14:30:00"
    }
  }
}
```

## 🛠️ Tratamento de Erros

### Erros Comuns e Soluções

#### Autenticação
```bash
# Problema: Erro de autenticação
# Solução:
az login
az account set --subscription "sua-subscription-id"
```

#### Quota Insuficiente
```bash
# Problema: Quota insuficiente para PTU
# Soluções:
# 1. Reduzir capacidade
--capacity 50

# 2. Usar região diferente  
--deployment-type regional

# 3. Usar Global PTU
--deployment-type global
```

#### Validação PTU
```bash
# Problema: Capacidade inválida
# Solução: Verificar requisitos
python azptu.py list-ptu-models
```

## 📊 Monitoramento e Custos

### Verificação de Usage

```bash
# Informações detalhadas do deployment
python azptu.py get-ptu-info \
  --account-name "ai-foundry" \
  --deployment-name "gpt4o-prod"

# Output:
# Nome: gpt4o-prod
# Modelo: gpt-4o v2024-08-06
# Capacidade: 150 PTUs
# Estado: Succeeded
# SKU: ProvisionedManaged (Regional)
```

### Estimativa de Custos (USD/hora)

| Modelo | Regional PTU | Global PTU | Data Zone PTU |
|--------|--------------|-------------|---------------|
| GPT-4o | $0.50 | $0.65 | $0.70 |
| GPT-4o Mini | $0.20 | $0.25 | $0.28 |
| GPT-4 Turbo | $0.45 | $0.60 | $0.65 |

*Valores aproximados, consulte Azure Portal para preços atuais*

## 🔒 Segurança e Compliance

### Autenticação
- **DefaultAzureCredential**: Suporte a múltiplos métodos de auth
- **Service Principal**: Para ambientes automatizados
- **Managed Identity**: Para recursos Azure

### Data Zone PTU (Compliance)
```bash
# Para maior isolamento de dados
python azptu.py create-ptu-deployment \
  --deployment-type data-zone \
  --model-name "gpt-4o" \
  --capacity 100
```

### RBAC Mínimo Necessário
- `Cognitive Services Contributor` (Resource Group)
- `Reader` (Subscription - para listar recursos)

## 🚀 Performance e Otimização

### Recomendações por Cenário

#### Alta Latência Crítica
```bash
# Regional PTU na região mais próxima
--deployment-type regional
```

#### Uso Intermitente/Spiky
```bash
# Global PTU para flexibilidade
--deployment-type global  
```

#### Compliance/Regulamentações
```bash
# Data Zone PTU para isolamento
--deployment-type data-zone
```

#### Desenvolvimento/Teste
```bash
# Capacidade mínima para economizar
--model-name gpt-4o-mini --capacity 25
```

## 🔄 Workflows Avançados

### Script de Deployment Automatizado

```bash
#!/bin/bash
# deploy-ptu-environment.sh

# Produção
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry-prod" \
  --deployment-name "gpt4o-prod-v1" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --capacity 200 \
  --deployment-type regional

# Staging  
python azptu.py create-ptu-deployment \
  --account-name "ai-foundry-staging" \
  --deployment-name "gpt4o-staging-v1" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --capacity 100 \
  --deployment-type regional

echo "✅ Ambiente PTU implantado com sucesso!"
```

### Backup de Configuração

```bash
# Backup da configuração atual
python azptu.py show-config > config-backup.txt

# Backup de deployments (manual via Portal Azure ou az CLI)
az cognitiveservices account deployment list \
  --name "ai-foundry-prod" \
  --resource-group "rg-production" > deployments-backup.json
```

## 📚 Recursos Adicionais

### Documentação Microsoft
- [Azure AI Foundry](https://docs.microsoft.com/azure/ai-foundry)
- [Provisioned Throughput](https://docs.microsoft.com/azure/ai-foundry/concepts/provisioned-throughput)
- [Azure Python SDK](https://docs.microsoft.com/python/api/azure-mgmt-cognitiveservices)

### Ferramentas Relacionadas
- [Azure CLI](https://docs.microsoft.com/cli/azure/)
- [Azure Portal](https://portal.azure.com)
- [Azure Monitor](https://docs.microsoft.com/azure/azure-monitor/)

## 🆘 Suporte

### Issues Conhecidos
1. **Timeout em operações**: Aumentar timeout em environments lentos
2. **Cache stale**: Use `logoff` para limpar cache problemático
3. **Permissões**: Verificar RBAC no resource group

### Debug Mode
```python
# No início do arquivo .py, alterar:
logging.basicConfig(level=logging.DEBUG)

# Para logs detalhados de todas as operações
```

### Contatos
- **Azure Support**: Para questões de quota e billing
- **GitHub Issues**: Para bugs do CLI
- **Microsoft Learn**: Para documentação oficial

---

## 📄 Licença

Este projeto é fornecido como exemplo educacional. Consulte a documentação oficial da Microsoft para uso em produção.

**Versão**: 1.0.0 Consolidated  
**Última Atualização**: Janeiro 2025  
**Testado**: Azure Subscription real (fad729f9-287d-4b9d-baa0-ee7a900f3f93)  
**Status**: ✅ Production Ready com validação real