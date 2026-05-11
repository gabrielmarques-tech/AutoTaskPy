# ixc_liberacao.py
# Módulo com todas as interações do IXC Soft para o fluxo de LIBERAÇÃO.
#
# Herda de IXCAutomacao (ixc.py) reaproveitando:
#   - login(), navegar_para_clientes(), garantir_pagina_clientes()
#   - pesquisar_cliente(), limpar_campo_pesquisa()
#   - obter_primeira_linha_tabela(), abrir_primeiro_cliente()
#   - voltar_para_lista()
#
# Adiciona métodos exclusivos da liberação:
#   - obter_id_cliente()        → lê o ID do cliente na tela principal
#   - abrir_aba_contrato()      → clica na aba Contrato (li[7])
#   - abrir_primeiro_contrato() → duplo clique na primeira linha da tabela
#   - obter_plano_contrato()    → lê a descrição do plano ex: "Plano Residencial 150M / 50M"
#   - liberar_contrato()        → abre Status Acesso → clica Liberar → volta à listagem

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from ixc import IXCAutomacao
from selenium_helpers import safe_wait, remover_overlay
from logger import logger


class IXCLiberacao(IXCAutomacao):
    """Extensão do IXCAutomacao com os métodos do fluxo de liberação."""

    # ------------------------------------------------------------------
    # ID do cliente
    # ------------------------------------------------------------------

    def obter_id_cliente(self) -> str:
        """
        Lê o ID do cliente na tela principal do cadastro.
        XPath: /html/body/form[2]/div[3]/div[1]/dl[1]/dd/input
        Esse ID será usado para pesquisar o cliente no Radius.
        """
        campo = safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form[2]/div[3]/div[1]/dl[1]/dd/input"),
            "presence",
            timeout=10,
        )
        id_cliente = campo.get_attribute("value").strip()
        logger.info(f"ID do cliente obtido: '{id_cliente}'")
        return id_cliente

    # ------------------------------------------------------------------
    # Aba Contrato
    # ------------------------------------------------------------------

    def abrir_aba_contrato(self) -> None:
        """
        Clica na aba 'Contratos' no menu do cadastro do cliente.
        XPath: /html/body/form/div[3]/ul/li[7]/a
        """
        remover_overlay(self.driver)
        safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form/div[3]/ul/li[7]/a"),
            "clickable",
            timeout=10,
        ).click()
        time.sleep(1)
        logger.info("Aba Contratos aberta.")

    def abrir_primeiro_contrato(self) -> None:
        """
        Dá duplo clique na primeira linha da tabela de contratos.
        XPath: /html/body/form/div[3]/div[7]/dl/div/div/div[6]/table/tbody/tr/td[3]/div
        """
        remover_overlay(self.driver)
        celula = safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form/div[3]/div[7]/dl/div/div/div[6]/table/tbody/tr/td[3]/div"),
            "clickable",
            timeout=10,
        )
        ActionChains(self.driver).double_click(celula).perform()
        time.sleep(1)
        logger.info("Contrato aberto.")

    # ------------------------------------------------------------------
    # Leitura do plano
    # ------------------------------------------------------------------

    def obter_plano_contrato(self) -> str:
        """
        Lê o campo Descricao do contrato e extrai apenas a velocidade.

        Texto completo ex: "Plano Residencial 150M / 50M"
        Retorna apenas:    "150M / 50M"

        XPath: /html/body/form[3]/div[3]/div[1]/dl[6]/dd/input
        """
        campo = safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form[3]/div[3]/div[1]/dl[6]/dd/input"),
            "presence",
            timeout=10,
        )
        texto_completo = campo.get_attribute("value").strip()
        logger.info(f"Descricao completa do contrato: '{texto_completo}'")

        match = re.search(r'(\d+\s*[MmGg]\s*/\s*\d+\s*[MmGg])', texto_completo)
        if match:
            plano = match.group(1).strip().upper()
            logger.info(f"Plano extraido: '{plano}'")
            return plano

        logger.warning(f"Padrao de velocidade nao encontrado em '{texto_completo}'. Usando texto completo.")
        return texto_completo

    # ------------------------------------------------------------------
    # Liberacao do contrato
    # ------------------------------------------------------------------

    def liberar_contrato(self) -> None:
        """
        Libera o contrato do cliente no IXC via Status Acesso.

        Fluxo:
          1. Clica em nav[6] — botão Status Acesso que abre o dropdown
          2. Clica em nav[6]/ul/li[2] — opção Liberar Manualmente
          3. Volta para a listagem de clientes (botao voltar ou menu)

        Usa click_js como fallback caso overlay bloqueie o clique normal.
        """
        remover_overlay(self.driver)

        # Passo 1: abre o dropdown "Status acesso"
        # Busca pelo texto da span dentro do nav — mais estável que posição numérica,
        # pois o número de navs na página varia dinamicamente por cliente.
        btn_status = safe_wait(
            self.driver,
            (By.XPATH, "//nav[.//span[contains(text(),'Status acesso')]]"),
            "presence",
            timeout=10,
        )
        try:
            btn_status.click()
        except Exception:
            click_js(self.driver, btn_status)
        time.sleep(0.8)

        # Passo 2: clica em "Liberar manualmente"
        # Usa o id="libera_internet" — fixo no HTML, não depende de posição
        btn_liberar = safe_wait(
            self.driver,
            (By.ID, "libera_internet"),
            "presence",
            timeout=10,
        )
        try:
            btn_liberar.click()
        except Exception:
            click_js(self.driver, btn_liberar)
        time.sleep(1)

        logger.info("Contrato liberado no IXC.")

        # Passo 3: volta para a listagem de clientes
        # Plano A: botao voltar nativo do cadastro
        # Plano B: renavega pelo menu se o botao falhar
        try:
            safe_wait(
                self.driver,
                (By.XPATH, "/html/body/form[2]/div[1]/div[3]/a[5]"),
                "clickable",
                timeout=8,
            ).click()
            time.sleep(0.5)
        except Exception:
            logger.info("Botao voltar nao encontrado, renavegando via menu.")
            try:
                self.navegar_para_clientes()
            except Exception:
                pass