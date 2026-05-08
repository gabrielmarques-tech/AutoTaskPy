# 🤖 AutoTaskPy

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.18-43B02A?logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Ativo-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

Automação web para redução de serviços de clientes entre o sistema ERP **IXC Soft** e o **Radius Manager**, utilizando Python e Selenium.

---

## 📋 O que faz

- Lê uma lista de clientes do arquivo `clientes.txt`
- Pesquisa cada cliente no **IXC Soft**
- Extrai o ID do serviço do cliente
- Aplica a redução de serviço no **Radius Manager**
- Registra todo o processo em log (`automacao.log`)

---

## 🗂️ Estrutura do projeto

```
AutoTaskPy/
│
├── main.py                  # Orquestrador principal do fluxo
├── ixc.py                   # Todas as interações com o IXC Soft
├── radius.py                # Todas as interações com o Radius Manager
├── browser.py               # Criação do navegador Chrome (chromedriver automático)
├── selenium_helpers.py      # Utilitários genéricos de Selenium
├── logger.py                # Log centralizado (arquivo + console)
│
├── clientes.txt             # Lista de clientes a processar (não versionado)
├── .env                     # Credenciais (não versionado)
├── .env.example             # Modelo de variáveis de ambiente
├── requirements.txt         # Dependências do projeto
└── .gitignore
```

---

## ⚙️ Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [Google Chrome](https://www.google.com/chrome/) instalado
- Acesso ao IXC Soft e ao Radius Manager

> O **chromedriver é gerenciado automaticamente** pelo Selenium Manager — não é necessário baixar ou atualizar manualmente.

---

## 🚀 Como usar

**1. Clone o repositório**
```bash
git clone https://github.com/gabrielmarques-tech/AutoTaskPy.git
cd AutoTaskPy
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure as credenciais**

Copie o arquivo de exemplo e preencha com seus dados:
```bash
cp .env.example .env
```

Edite o `.env`:
```
SITE_IXC=https://seu-ixc.com.br
EMAIL=seu@email.com
SENHA=suasenha

SITE_R=http://seu-radius.com.br
USUARIO_R=usuario
SENHA_R=senharadius
```

**4. Adicione os clientes**

Crie o arquivo `clientes.txt` com um nome por linha:
```
João da Silva
Maria Oliveira
Empresa XYZ
```

**5. Execute**
```bash
python main.py
```

> ⚠️ O login do IXC utiliza **2FA manual**. Após rodar o script, complete a autenticação no navegador — a automação continua sozinha depois.

---

## 📁 Arquivos não versionados

Por segurança, os seguintes arquivos **não são enviados ao GitHub**:

| Arquivo | Motivo |
|---|---|
| `.env` | Contém senhas e credenciais |
| `clientes.txt` | Dados sensíveis de clientes |
| `automacao.log` | Log gerado localmente |
| `__pycache__/` | Cache do Python |

---

## 🖼️ Screenshots

> *Em breve*

---

## 🛠️ Tecnologias

- [Python](https://www.python.org/)
- [Selenium](https://www.selenium.dev/)
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
