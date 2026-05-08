# radius.py
# Módulo responsável por TODAS as interações com o Radius Manager.
#
# Classe: RadiusAutomacao
#   - login()                → faz o login no Radius
#   - aplicar_reducao()      → busca o cliente pelo ID e aplica a redução de serviço

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from logger import logger
from selenium_helpers import safe_wait


class RadiusAutomacao:
    """Automação do Radius Manager via Selenium."""

    # ID do serviço de redução configurado no Radius Manager.
    # Se mudar no futuro, altere apenas aqui.
    ID_SERVICO_REDUCAO = "45"

    def __init__(self, driver: webdriver.Chrome, site: str, usuario: str, senha: str):
        self.driver  = driver
        self.site    = site
        self.usuario = usuario
        self.senha   = senha

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self) -> None:
        """
        Faz login no Radius Manager.

        Os XPaths das linhas do formulário de login estão fixos
        pois o Radius Manager raramente muda sua estrutura.
        """
        logger.info("Acessando Radius Manager...")
        self.driver.get(self.site)

        safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form/table/tbody/tr[3]/td[2]/input"),
            "presence",
        ).send_keys(self.usuario)

        safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form/table/tbody/tr[4]/td[2]/input"),
            "presence",
        ).send_keys(self.senha)

        safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form/table/tbody/tr[6]/td/div/input[1]"),
            "clickable",
        ).click()

        logger.info("Login no Radius Manager concluído.")

    # ------------------------------------------------------------------
    # Aplicação da redução
    # ------------------------------------------------------------------

    def aplicar_reducao(self, id_cliente: str) -> None:
        """
        Busca o cliente pelo ID no Radius e aplica a redução de serviço.

        Parâmetros
        ----------
        id_cliente : str
            Valor copiado do campo de serviço no IXC (identificador do cliente no Radius).

        Fluxo:
          1. Abre o menu de clientes no Radius
          2. Preenche o campo de busca com o ID
          3. Clica em pesquisar
          4. Abre o resultado encontrado
          5. Seleciona o serviço de redução (ID_SERVICO_REDUCAO)
          6. Confirma a alteração
        """
        logger.info(f"Aplicando redução no Radius para ID: '{id_cliente}'")

        # Passo 1: Clica no menu de clientes (ícone/link de clientes na barra lateral)
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/div/table/tbody/tr/td[2]/span[2]"),
            "clickable",
            timeout=10,
        ).click()
        time.sleep(0.6)

        # Passo 2: Seleciona a opção de busca por ID dentro do submenu
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/div/div[2]/table/tbody/tr[2]/td[2]"),
            "clickable",
            timeout=10,
        ).click()
        time.sleep(0.6)

        # Passo 3: Preenche o campo de ID do cliente e pesquisa
        campo_id = safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[2]/tbody/tr/td[1]"
             "/table/tbody/tr/td/table/tbody/tr/td/form/table/tbody/tr[1]/td[2]/input"),
            "presence",
            timeout=10,
        )
        campo_id.clear()
        campo_id.send_keys(id_cliente)

        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[2]/tbody/tr/td[1]"
             "/table/tbody/tr/td/table/tbody/tr/td/form/p[2]/input"),
            "clickable",
            timeout=10,
        ).click()

        # Passo 4: Abre o cadastro do cliente encontrado
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[4]/tbody/tr[1]"
             "/td/table[2]/tbody/tr[2]/td[3]/font/a"),
            "clickable",
            timeout=10,
        ).click()

        # Passo 5: Seleciona o serviço de redução no dropdown
        select_element = safe_wait(self.driver, (By.ID, "srvid"), "presence", timeout=10)
        Select(select_element).select_by_value(self.ID_SERVICO_REDUCAO)

        # Passo 6: Confirma a alteração
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[2]/tbody/tr"
             "/td/table/tbody/tr/td/form/p[3]/input"),
            "clickable",
            timeout=10,
        ).click()

        logger.info(f"Redução aplicada com sucesso no Radius para ID: '{id_cliente}'")