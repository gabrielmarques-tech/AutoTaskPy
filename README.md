# 🤖 AutoTaskPy

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.18-43B02A?logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Ativo-success)

Automação web para gerenciamento de clientes entre o sistema ERP **IXC Soft** e o **Radius Manager**, utilizando Python e Selenium.

Possui dois fluxos independentes:
- **Redução** — reduz o serviço de clientes inadimplentes
- **Liberação** — libera a conexão de clientes após pagamento

## 💼 Contexto e impacto

Desenvolvido para uso real em um provedor de internet (ISP), este projeto
automatiza uma rotina operacional crítica que antes era feita manualmente.

| | Antes | Depois |
|---|---|---|
| Tempo por execução | 2–3 horas (manual) | ~30 minutos |
| Risco de erro humano | Alto | Eliminado |
| Clientes por lote | 40–50 | 40–50 |
| Intervenção necessária | Total | Mínima (só 2FA inicial) |

Desenvolvido de forma independente em ~3 meses, sem orientação externa.
---

## 📋 O que faz

### Redução de clientes
- Lê a lista de `clientes.txt`
- Pesquisa cada cliente no IXC Soft
- Extrai o ID do serviço
- Aplica a redução de serviço no Radius Manager

### Liberação de clientes
- Lê a lista de `clientes_liberacao.txt`
- Pesquisa cada cliente no IXC Soft
- Obtém o ID e lê o plano contratado (ex: 150M / 50M)
- Libera o contrato via Status Acesso → Liberar manualmente
- Localiza o cliente no Radius e aplica o Service plan correto
- Clica em Update User para confirmar

---

## 🗂️ Estrutura do projeto

```
AutoTaskPy/
│
├── main.py                  # Executa a REDUÇÃO de clientes
├── main_liberacao.py        # Executa a LIBERAÇÃO de clientes
│
├── ixc.py                   # Interações base com o IXC Soft
├── ixc_liberacao.py         # Métodos extras do IXC para liberação
│
├── radius.py                # Interações base com o Radius Manager
├── radius_liberacao.py      # Métodos extras do Radius para liberação
│
├── browser.py               # Criação do Chrome (chromedriver automático)
├── selenium_helpers.py      # Utilitários genéricos de Selenium
├── logger.py                # Log centralizado (arquivo + console)
│
├── clientes_ex.txt          # Modelo: nomes para reduzir
├── clientes_liberacao_ex.txt # Modelo: nomes para liberar
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

Para reduzir — crie `clientes.txt` com um nome por linha:
```
João da Silva
Maria Oliveira
Empresa XYZ
```

Para liberar — crie `clientes_liberacao.txt` com um nome por linha:
```
João da Silva
Maria Oliveira
Empresa XYZ
```

> Veja os arquivos `clientes_ex.txt` e `clientes_liberacao_ex.txt` como modelo.

**5. Execute**

Para reduzir clientes:
```bash
python main.py
```

Para liberar clientes:
```bash
python main_liberacao.py
```

> ⚠️ O login do IXC utiliza **2FA manual**. Após rodar o script, complete a autenticação no navegador — a automação continua sozinha depois.

---

## 📁 Arquivos não versionados

Por segurança, os seguintes arquivos **não são enviados ao GitHub**:

| Arquivo | Motivo |
|---|---|
| `.env` | Contém senhas e credenciais |
| `clientes.txt` | Dados sensíveis de clientes |
| `clientes_liberacao.txt` | Dados sensíveis de clientes |
| `automacao.log` | Log gerado localmente |
| `__pycache__/` | Cache do Python |

---

## 🖼️ Screenshots

<img width="1356" height="724" alt="WhatsApp Image 2026-05-19 at 00 12 06" src="https://github.com/user-attachments/assets/1fbb2aab-c797-4710-8b3e-355176d4e472" />
<img width="1233" height="657" alt="WhatsApp Image 2026-05-18 at 21 47 18" src="https://github.com/user-attachments/assets/85fb4319-8f23-4984-ba6f-c62c55dc2a95" />



---

## 🛠️ Tecnologias

- [Python](https://www.python.org/)
- [Selenium](https://www.selenium.dev/)
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
