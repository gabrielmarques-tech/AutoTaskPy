# main.py
# Ponto de entrada da automação IXC → Radius Manager.
#
# Este script apenas ORQUESTRA o processo. Toda a lógica de negócio
# está encapsulada nos módulos:
#
#   browser.py          → criação do navegador (com chromedriver automático)
#   ixc.py              → todas as interações com o IXC Soft
#   radius.py           → todas as interações com o Radius Manager
#   selenium_helpers.py → utilitários genéricos de Selenium
#   logger.py           → log centralizado (arquivo + console)
#
# FLUXO GERAL:
#   1. Lê os clientes do clientes.txt
#   2. Abre o Chrome (chromedriver atualizado automaticamente)
#   3. Faz login no IXC (aguarda 2FA manual)
#   4. Abre segunda aba e faz login no Radius
#   5. Para cada cliente:
#      a. Pesquisa no IXC
#      b. Extrai o ID do serviço
#      c. Aplica a redução no Radius
#      d. Volta para a listagem do IXC
#   6. Fecha o navegador

import os
import traceback

from dotenv import load_dotenv

from logger import logger
from browser import criar_navegador, fechar_navegador
from ixc import IXCAutomacao
from radius import RadiusAutomacao
from selenium_helpers import fechar_modal_ixc

# ---------------------------------------------------------------------------
# Carrega variáveis de ambiente do .env
# ---------------------------------------------------------------------------
load_dotenv()

SITE_IXC     = os.getenv("SITE_IXC")
EMAIL_IXC    = os.getenv("EMAIL")
SENHA_IXC    = os.getenv("SENHA")
SITE_RADIUS  = os.getenv("SITE_R")
USUARIO_RADIUS = os.getenv("USUARIO_R")
SENHA_RADIUS = os.getenv("SENHA_R")

# ---------------------------------------------------------------------------
# Leitura da lista de clientes
# ---------------------------------------------------------------------------
base_dir    = os.path.dirname(os.path.abspath(__file__))
arquivo_clientes = os.path.join(base_dir, "clientes.txt")

with open(arquivo_clientes, "r", encoding="utf-8") as f:
    lista_clientes = [linha.strip() for linha in f if linha.strip()]

logger.info(f"{len(lista_clientes)} cliente(s) carregado(s) de '{arquivo_clientes}'.")

# ---------------------------------------------------------------------------
# Início da automação
# ---------------------------------------------------------------------------
driver, _ = criar_navegador(timeout_padrao=25)

try:
    # --- Instancia os módulos de automação ---
    ixc    = IXCAutomacao(driver, SITE_IXC, EMAIL_IXC, SENHA_IXC)
    radius = RadiusAutomacao(driver, SITE_RADIUS, USUARIO_RADIUS, SENHA_RADIUS)

    # --- Login no IXC (aguarda 2FA manual) ---
    ixc.login()

    # --- Navega para a listagem de clientes no IXC ---
    ixc.navegar_para_clientes()

    # --- Abre segunda aba e faz login no Radius ---
    driver.execute_script("window.open('');")
    guia_radius = driver.window_handles[1]
    guia_ixc    = driver.window_handles[0]

    driver.switch_to.window(guia_radius)
    radius.login()

    # Volta para a aba do IXC para começar o processamento
    driver.switch_to.window(guia_ixc)

    # -----------------------------------------------------------------------
    # Loop principal: processa cada cliente da lista
    # -----------------------------------------------------------------------
    for nome_cliente in lista_clientes:
        logger.info(f"{'='*60}")
        logger.info(f"Iniciando: {nome_cliente}")

        try:
            # Garante que estamos na tela de listagem (fecha modais, renavega se preciso)
            fechar_modal_ixc(driver)
            ixc.garantir_pagina_clientes()

            # Pesquisa o cliente
            ixc.pesquisar_cliente(nome_cliente)

            # Verifica se encontrou resultados na tabela
            if not ixc.obter_primeira_linha_tabela():
                logger.warning(f"Cliente '{nome_cliente}' não encontrado na tabela. Pulando.")
                continue

            # Abre o cadastro do cliente
            ixc.abrir_primeiro_cliente()

            # Abre a aba de serviços
            try:
                ixc.abrir_aba_servicos()
            except Exception:
                logger.error(f"Aba 'Serviços' não acessível para '{nome_cliente}'. Pulando.")
                ixc.voltar_para_lista()
                continue

            # Obtém o ID/valor do serviço
            try:
                valor_servico = ixc.obter_valor_servico()
            except Exception:
                logger.error(
                    f"Falha ao obter valor do serviço para '{nome_cliente}':\n"
                    f"{traceback.format_exc()}"
                )
                ixc.voltar_para_lista()
                continue

            # Aplica a redução no Radius
            driver.switch_to.window(guia_radius)
            try:
                radius.aplicar_reducao(valor_servico)
            except Exception:
                logger.error(
                    f"Erro ao aplicar redução no Radius para '{nome_cliente}':\n"
                    f"{traceback.format_exc()}"
                )
            finally:
                # Sempre volta para o IXC, mesmo que o Radius tenha falhado
                driver.switch_to.window(guia_ixc)

            logger.info(f"✅ Cliente '{nome_cliente}' processado com sucesso.")

        except Exception:
            logger.error(
                f"Erro inesperado no cliente '{nome_cliente}':\n"
                f"{traceback.format_exc()}"
            )
            # Garante que voltamos para a aba do IXC antes de tentar o próximo
            try:
                driver.switch_to.window(guia_ixc)
            except Exception:
                pass

        finally:
            # Volta para a listagem e limpa o campo — independente de sucesso ou falha
            ixc.voltar_para_lista()
            try:
                ixc.limpar_campo_pesquisa()
            except Exception:
                pass

    logger.info(f"{'='*60}")
    logger.info("Automação concluída. Todos os clientes foram processados.")

except Exception:
    logger.error(f"Erro geral na automação:\n{traceback.format_exc()}")

finally:
    fechar_navegador(driver)