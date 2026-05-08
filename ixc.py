# ixc.py
# Módulo responsável por TODAS as interações com o sistema IXC Soft.
#
# Encapsula em métodos de uma classe o que antes estava espalhado no script
# principal. Cada método tem uma responsabilidade única e clara.
#
# Classe: IXCAutomacao
#   - login()                         → faz o login e aguarda 2FA manual
#   - navegar_para_clientes()         → abre o menu Cadastros → Cliente
#   - garantir_pagina_clientes()      → garante que estamos na listagem (com retry)
#   - limpar_campo_pesquisa()         → limpa o campo de busca de forma robusta
#   - pesquisar_cliente()             → digita e submete a pesquisa
#   - abrir_primeiro_cliente()        → duplo clique na primeira linha da tabela
#   - abrir_aba_servicos()            → clica na aba "Serviços" do cliente
#   - obter_valor_servico()           → navega dentro do serviço e extrai o valor
#   - voltar_para_lista()             → retorna para a listagem de clientes

import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from logger import logger
from selenium_helpers import safe_wait, click_js, remover_overlay, fechar_modal_ixc


class IXCAutomacao:
    """Automação do sistema IXC Soft via Selenium."""

    def __init__(self, driver: webdriver.Chrome, site: str, email: str, senha: str):
        self.driver = driver
        self.site   = site
        self.email  = email
        self.senha  = senha

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self) -> None:
        """
        Realiza login no IXC e aguarda o 2FA ser completado manualmente.
        A automação só continua quando o menu 'Cadastros' aparecer na tela.
        """
        logger.info("Acessando IXC...")
        self.driver.get(self.site)

        safe_wait(self.driver, (By.ID, "email"), "presence").send_keys(self.email)
        safe_wait(self.driver, (By.ID, "btn-next-login"), "clickable").click()
        safe_wait(self.driver, (By.ID, "password"), "presence").send_keys(self.senha)
        safe_wait(self.driver, (By.ID, "btn-enter-login"), "clickable").click()

        time.sleep(1)

        # Segunda tentativa de clique no login (o IXC às vezes ignora o primeiro)
        try:
            safe_wait(self.driver, (By.ID, "btn-enter-login"), "clickable", timeout=5).click()
        except Exception:
            pass

        logger.info("⏳ Aguarde: complete o 2FA manualmente. Esperando o menu 'Cadastros' aparecer...")

        # Espera generosa para o 2FA manual (120 segundos)
        safe_wait(self.driver, (By.XPATH, "//a[text()='Cadastros']"), "presence", timeout=120)
        logger.info("Login no IXC concluído.")

        # Fecha o modal "Lembrar" que aparece logo após o login
        fechar_modal_ixc(self.driver)

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def navegar_para_clientes(self) -> None:
        """Clica em Cadastros → Cliente para abrir a listagem."""
        remover_overlay(self.driver)
        safe_wait(self.driver, (By.XPATH, "//a[text()='Cadastros']"), "clickable").click()
        remover_overlay(self.driver)
        safe_wait(self.driver, (By.XPATH, "//a[contains(@rel,'cliente')]"), "clickable").click()
        remover_overlay(self.driver)

    def garantir_pagina_clientes(self) -> None:
        """
        Verifica se o campo de pesquisa de clientes está visível.
        Se não estiver, navega novamente para a listagem (até 3 tentativas).

        Levanta TimeoutException se não conseguir em nenhuma tentativa.
        """
        seletor_campo = (By.CSS_SELECTOR, "input.gridActionsSearchInput[placeholder='Consultar por Razão social']")

        for tentativa in range(1, 4):
            try:
                # Campo já visível? Ótimo, estamos na página certa.
                campo = self.driver.find_element(*seletor_campo)
                if campo.is_displayed():
                    return
            except NoSuchElementException:
                pass

            # Não está — navega de volta
            logger.info(f"Tentativa {tentativa}/3: navegando para a listagem de clientes...")
            try:
                self.navegar_para_clientes()
                safe_wait(self.driver, seletor_campo, "presence", timeout=10)
                return
            except Exception:
                time.sleep(1)

        raise TimeoutException("Não foi possível garantir a página de clientes após 3 tentativas.")

    # ------------------------------------------------------------------
    # Campo de pesquisa
    # ------------------------------------------------------------------

    def limpar_campo_pesquisa(self) -> None:
        """
        Limpa o campo de pesquisa de forma exaustiva.

        O IXC mantém o valor anterior no campo após voltar à listagem.
        Se não limparmos completamente, a próxima pesquisa concatena o nome
        anterior com o novo e o cliente não é encontrado.

        Métodos usados em sequência:
          1. Ctrl+A + Backspace  (simula o usuário limpando)
          2. JS value = ''       (força via JavaScript caso o evento não dispare)
          3. Verificação final   (se ainda tiver valor, repete)
        """
        seletor = (By.CSS_SELECTOR, "input.gridActionsSearchInput[placeholder='Consultar por Razão social']")

        try:
            campo = safe_wait(self.driver, seletor, "visible", timeout=10)

            # Garante foco no campo
            try:
                campo.click()
            except Exception:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", campo)

            # Método 1: Ctrl+A + Backspace
            campo.send_keys(Keys.CONTROL, "a")
            time.sleep(0.1)
            campo.send_keys(Keys.BACKSPACE)
            time.sleep(0.1)

            # Método 2: JS clear
            self.driver.execute_script("arguments[0].value = '';", campo)

            # Verificação final: se ainda tiver conteúdo, repete
            valor = campo.get_attribute("value") or ""
            if valor.strip():
                campo.send_keys(Keys.CONTROL, "a")
                time.sleep(0.05)
                campo.send_keys(Keys.BACKSPACE)
                self.driver.execute_script("arguments[0].value = '';", campo)
                time.sleep(0.05)

        except Exception as e:
            logger.error(f"Falha ao limpar campo de pesquisa: {e}")
            raise

    def pesquisar_cliente(self, nome: str) -> None:
        """
        Digita o nome do cliente no campo de pesquisa e pressiona Enter.
        Sempre chama limpar_campo_pesquisa() antes de digitar.
        """
        self.limpar_campo_pesquisa()

        seletor = (By.CSS_SELECTOR, "input.gridActionsSearchInput[placeholder='Consultar por Razão social']")
        campo = safe_wait(self.driver, seletor, "visible", timeout=10)
        campo.send_keys(nome)
        campo.send_keys(Keys.ENTER)
        time.sleep(1)  # Aguarda a tabela atualizar com os resultados

    # ------------------------------------------------------------------
    # Tabela de resultados
    # ------------------------------------------------------------------

    def obter_primeira_linha_tabela(self, retries: int = 6, espera: float = 1.0):
        """
        Tenta localizar a primeira linha da tabela de resultados.

        Parâmetros
        ----------
        retries : número de tentativas
        espera  : segundos entre cada tentativa

        Retorna o WebElement ou None se não encontrar.
        """
        xpath_linha = "/html/body/div[2]/div/div[7]/table/tbody/tr[1]/td[1]/div"

        for _ in range(retries):
            try:
                remover_overlay(self.driver)
                elemento = self.driver.find_element(By.XPATH, xpath_linha)
                if elemento.is_displayed():
                    return elemento
            except Exception:
                pass
            time.sleep(espera)

        return None

    # ------------------------------------------------------------------
    # Abertura do cliente
    # ------------------------------------------------------------------

    def abrir_primeiro_cliente(self) -> None:
        """
        Abre o cadastro do primeiro cliente da tabela via duplo clique.
        Se o duplo clique falhar, tenta dois cliques simples via JS.
        """
        elemento = self.obter_primeira_linha_tabela()
        if not elemento:
            raise Exception("Nenhum cliente encontrado na tabela.")

        try:
            ActionChains(self.driver).double_click(elemento).perform()
        except Exception:
            # Fallback: dois cliques via JavaScript
            click_js(self.driver, elemento)
            time.sleep(0.3)
            click_js(self.driver, elemento)

        time.sleep(2)  # Aguarda o formulário do cliente carregar

    # ------------------------------------------------------------------
    # Aba Serviços
    # ------------------------------------------------------------------

    def abrir_aba_servicos(self) -> None:
        """
        Clica na aba 'Serviços' dentro do cadastro do cliente (7ª aba).
        Levanta exceção se não conseguir clicar.
        """
        xpath_aba = "/html/body/form[2]/div[3]/ul/li[7]/a"
        safe_wait(self.driver, (By.XPATH, xpath_aba), "clickable", timeout=10).click()

    # ------------------------------------------------------------------
    # Obtenção do valor do serviço
    # ------------------------------------------------------------------

    def obter_valor_servico(self) -> str:
        """
        Acessa o primeiro serviço do cliente, navega até o campo de valor
        e retorna o valor encontrado como string.

        Fluxo interno:
          1. Duplo clique na célula do serviço para abrir o formulário
          2. Abre o menu de opções (nav[3])
          3. Seleciona a 3ª opção do menu
          4. Lê o valor do campo input da dl[3]

        Levanta exceção se qualquer passo falhar.
        """
        # Duplo clique na célula do serviço (4ª coluna, 1ª linha)
        xpath_celula = (
            "/html/body/form[2]/div[3]/div[7]/dl/div/div/div[6]"
            "/table/tbody/tr[1]/td[4]/div/div"
        )
        celula = safe_wait(self.driver, (By.XPATH, xpath_celula), "clickable", timeout=10)
        ActionChains(self.driver).double_click(celula).perform()
        time.sleep(0.8)

        # Abre o dropdown de ações do serviço
        safe_wait(self.driver, (By.XPATH, "/html/body/form[3]/div[2]/nav[3]/div/span"), "clickable").click()

        # Seleciona a opção de redução/suspensão (3ª opção)
        safe_wait(self.driver, (By.XPATH, "/html/body/form[3]/div[2]/nav[3]/ul/li[3]"), "clickable").click()

        # Lê o valor do campo
        campo_input = safe_wait(
            self.driver,
            (By.XPATH, "/html/body/form[3]/div[3]/div[1]/dl[3]/dd/div/input"),
            "presence",
            timeout=10,
        )
        valor = campo_input.get_attribute("value")
        logger.info(f"Valor extraído do serviço: '{valor}'")
        return valor

    # ------------------------------------------------------------------
    # Retorno à listagem
    # ------------------------------------------------------------------

    def voltar_para_lista(self) -> None:
        """
        Tenta retornar à listagem de clientes usando os botões de navegação.

        Plano A: Botão de voltar do form[3] e depois do form[2]
        Plano B: Re-navegar pelo menu Cadastros → Cliente
        """
        try:
            # Plano A: botões de voltar nativos do IXC
            safe_wait(
                self.driver,
                (By.XPATH, "/html/body/form[3]/div[1]/div[3]/a[4]"),
                "clickable",
                timeout=8,
            ).click()
            safe_wait(
                self.driver,
                (By.XPATH, "/html/body/form[2]/div[1]/div[3]/a[5]"),
                "clickable",
                timeout=8,
            ).click()
        except Exception:
            # Plano B: navega pelo menu
            logger.info("Botões de voltar falharam. Renavegando via menu.")
            try:
                self.navegar_para_clientes()
            except Exception:
                logger.error("Não foi possível retornar à listagem de clientes.")