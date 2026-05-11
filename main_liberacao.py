# main_liberacao.py
# Ponto de entrada da automação de LIBERAÇÃO de clientes.
#
# FLUXO CORRETO POR CLIENTE:
#   1. IXC  → pesquisa cliente, abre cadastro
#   2. IXC  → obtém ID do cliente
#   3. IXC  → abre aba Contratos, abre contrato, lê o plano
#   4. IXC  → libera o contrato (Status Acesso → Liberar)
#   5. IXC  → volta para a listagem
#   6. Radius → abre perfil pelo ID, seleciona Service plan, clica Update User
#
# IMPORTANTE: O Radius só é acessado DEPOIS de tudo feito no IXC.
# Ir ao Radius antes de liberar fazia o formulário do contrato fechar
# ao voltar para o IXC, impedindo o clique em Status Acesso.

import os
import traceback

from dotenv import load_dotenv

from logger import logger
from browser import criar_navegador, fechar_navegador
from ixc_liberacao import IXCLiberacao
from radius_liberacao import RadiusLiberacao
from selenium_helpers import fechar_modal_ixc

# ---------------------------------------------------------------------------
# Carrega variáveis de ambiente
# ---------------------------------------------------------------------------
load_dotenv()

SITE_IXC       = os.getenv("SITE_IXC")
EMAIL_IXC      = os.getenv("EMAIL")
SENHA_IXC      = os.getenv("SENHA")
SITE_RADIUS    = os.getenv("SITE_R")
USUARIO_RADIUS = os.getenv("USUARIO_R")
SENHA_RADIUS   = os.getenv("SENHA_R")

# ---------------------------------------------------------------------------
# Leitura da lista de clientes
# ---------------------------------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
arquivo_clientes = os.path.join(base_dir, "clientes_liberacao.txt")

with open(arquivo_clientes, "r", encoding="utf-8") as f:
    lista_clientes = [linha.strip() for linha in f if linha.strip()]

logger.info(f"{len(lista_clientes)} cliente(s) carregado(s) para liberação.")

# ---------------------------------------------------------------------------
# Início da automação
# ---------------------------------------------------------------------------
driver, _ = criar_navegador(timeout_padrao=25)

try:
    ixc    = IXCLiberacao(driver, SITE_IXC, EMAIL_IXC, SENHA_IXC)
    radius = RadiusLiberacao(driver, SITE_RADIUS, USUARIO_RADIUS, SENHA_RADIUS)

    # Login no IXC (aguarda 2FA manual)
    ixc.login()
    ixc.navegar_para_clientes()

    # Abre segunda aba para o Radius e faz login
    driver.execute_script("window.open('');")
    guia_radius = driver.window_handles[1]
    guia_ixc    = driver.window_handles[0]

    driver.switch_to.window(guia_radius)
    radius.login()
    driver.switch_to.window(guia_ixc)

    # -----------------------------------------------------------------------
    # Loop principal
    # -----------------------------------------------------------------------
    for nome_cliente in lista_clientes:
        logger.info(f"{'='*60}")
        logger.info(f"Iniciando liberação: {nome_cliente}")

        id_cliente  = None
        plano_texto = None

        try:
            fechar_modal_ixc(driver)
            ixc.garantir_pagina_clientes()
            ixc.pesquisar_cliente(nome_cliente)

            if not ixc.obter_primeira_linha_tabela():
                logger.warning(f"Cliente '{nome_cliente}' não encontrado. Pulando.")
                continue

            # Abre o cadastro do cliente
            ixc.abrir_primeiro_cliente()

            # --- PASSO 1: obtém o ID ---
            try:
                id_cliente = ixc.obter_id_cliente()
            except Exception:
                logger.error(f"Falha ao obter ID de '{nome_cliente}':\n{traceback.format_exc()}")
                ixc.voltar_para_lista()
                continue

            # --- PASSO 2: abre contrato e lê o plano ---
            try:
                ixc.abrir_aba_contrato()
                ixc.abrir_primeiro_contrato()
                plano_texto = ixc.obter_plano_contrato()
                logger.info(f"Plano lido: '{plano_texto}'")
            except Exception:
                logger.error(f"Falha ao ler plano de '{nome_cliente}':\n{traceback.format_exc()}")
                ixc.voltar_para_lista()
                continue

            # --- PASSO 3: libera o contrato no IXC ---
            try:
                ixc.liberar_contrato()
                logger.info(f"Contrato de '{nome_cliente}' liberado no IXC.")
            except Exception:
                logger.error(f"Falha ao liberar contrato de '{nome_cliente}':\n{traceback.format_exc()}")
                ixc.voltar_para_lista()
                continue

            # --- PASSO 4: aplica o plano no Radius ---
            # Só vai ao Radius depois que tudo no IXC foi concluído
            driver.switch_to.window(guia_radius)
            try:
                radius.abrir_perfil_cliente(id_cliente)
                radius.aplicar_plano(plano_texto)
                logger.info(f"✅ Cliente '{nome_cliente}' liberado com sucesso.")
            except Exception:
                logger.error(f"Falha no Radius para '{nome_cliente}':\n{traceback.format_exc()}")
            finally:
                driver.switch_to.window(guia_ixc)

        except Exception:
            logger.error(f"Erro inesperado em '{nome_cliente}':\n{traceback.format_exc()}")
            try:
                driver.switch_to.window(guia_ixc)
            except Exception:
                pass

        finally:
            # Garante retorno à listagem e limpeza do campo para o próximo cliente
            try:
                ixc.voltar_para_lista()
            except Exception:
                pass
            try:
                ixc.limpar_campo_pesquisa()
            except Exception:
                pass

    logger.info("="*60)
    logger.info("Liberação concluída. Todos os clientes foram processados.")

except Exception:
    logger.error(f"Erro geral:\n{traceback.format_exc()}")

finally:
    fechar_navegador(driver)