# selenium_helpers.py
# Funções utilitárias de Selenium reutilizáveis em qualquer módulo.
#
# Centraliza aqui:
#   - safe_wait      → espera segura por elementos com tratamento de exceção
#   - click_js       → clique via JavaScript (evita falhas de "element not interactable")
#   - remover_overlay → remove o div que o IXC joga na frente da tela em alguns momentos
#   - fechar_modal_ixc → fecha qualquer modal/pop-up aberto no IXC
#
# Por que isso é importante?
# O IXC abre overlays e modais em momentos imprevisíveis. Sem tratamento
# centralizado, cada trecho de código precisaria repetir a mesma lógica
# de "fechar modal se existir". Com essas funções aqui, basta chamá-las.

import time
from typing import Literal

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.remote.webelement import WebElement

from logger import logger

# Tipo auxiliar para o parâmetro `condition` do safe_wait
TipoCondicao = Literal["presence", "visible", "clickable"]


# ---------------------------------------------------------------------------
# Espera segura
# ---------------------------------------------------------------------------

def safe_wait(
    driver: webdriver.Chrome,
    locator: tuple,
    condition: TipoCondicao = "presence",
    timeout: int = 25,
) -> WebElement:
    """
    Aguarda um elemento aparecer/estar visível/clicável.

    Parâmetros
    ----------
    driver    : instância do Chrome
    locator   : tupla (By.X, "seletor")
    condition : 'presence' | 'visible' | 'clickable'
    timeout   : segundos máximos de espera

    Levanta TimeoutException se o elemento não aparecer a tempo.
    """
    condicoes = {
        "presence": EC.presence_of_element_located,
        "visible":  EC.visibility_of_element_located,
        "clickable": EC.element_to_be_clickable,
    }

    if condition not in condicoes:
        raise ValueError(f"Condição inválida: '{condition}'. Use: {list(condicoes.keys())}")

    try:
        return WebDriverWait(driver, timeout).until(condicoes[condition](locator))
    except (TimeoutException, StaleElementReferenceException, NoSuchElementException):
        raise  # re-levanta para o chamador decidir o que fazer


# ---------------------------------------------------------------------------
# Clique via JavaScript
# ---------------------------------------------------------------------------

def click_js(driver: webdriver.Chrome, element: WebElement) -> None:
    """
    Clica em um elemento via JavaScript.

    Usado quando o Selenium recusa o clique normal por:
    - Elemento coberto por overlay
    - Elemento fora da área visível
    - Animações ainda em andamento
    """
    driver.execute_script("arguments[0].click();", element)


# ---------------------------------------------------------------------------
# Remoção de overlay do IXC
# ---------------------------------------------------------------------------

def remover_overlay(driver: webdriver.Chrome) -> None:
    """
    Remove o div de overlay que o IXC exibe enquanto carrega conteúdo.

    O elemento #backgroundContent "tampa" a tela e bloqueia todos os cliques.
    Removê-lo via JS é mais confiável do que esperar ele sumir sozinho.
    """
    try:
        driver.execute_script("""
            var overlay = document.getElementById('backgroundContent');
            if (overlay) { overlay.style.display = 'none'; }
        """)
        time.sleep(0.3)
    except WebDriverException:
        pass  # Se o JS falhar (ex: página ainda carregando), ignora


# ---------------------------------------------------------------------------
# Fechamento de modais/pop-ups do IXC
# ---------------------------------------------------------------------------

def fechar_modal_ixc(driver: webdriver.Chrome) -> None:
    """
    Verifica se há algum modal aberto no IXC e tenta fechá-lo.

    O IXC tem o hábito de abrir modais de aviso, confirmação e lembretes
    em momentos aleatórios. Esta função é chamada preventivamente antes
    de cada interação crítica para garantir que não haja nada bloqueando.

    Tentativas (em ordem):
      1. Botão com texto "Lembrar" (modal de 2FA/sessão)
      2. Botão genérico #closeButton
      3. Qualquer botão "Fechar" visível dentro de .ixc-modal
    """
    # Tentativa 1: modal de "Lembrar" que aparece após login
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Lembrar')]"))
        )
        click_js(driver, btn)
        logger.info("Modal 'Lembrar' fechado.")
        time.sleep(0.5)
        return
    except (TimeoutException, NoSuchElementException):
        pass

    # Tentativa 2: botão padrão #closeButton de modais do IXC
    try:
        btn = driver.find_element(By.ID, "closeButton")
        if btn.is_displayed():
            btn.click()
            logger.info("Modal fechado via #closeButton.")
            time.sleep(0.5)
            return
    except NoSuchElementException:
        pass

    # Tentativa 3: qualquer botão "Fechar" dentro de .ixc-modal
    try:
        modal = driver.find_element(By.CLASS_NAME, "ixc-modal")
        if modal.is_displayed():
            btn_fechar = modal.find_element(By.XPATH, ".//button[contains(text(),'Fechar')]")
            click_js(driver, btn_fechar)
            logger.info("Modal '.ixc-modal' fechado via botão interno.")
            time.sleep(0.5)
    except (NoSuchElementException, StaleElementReferenceException):
        pass  # Nenhum modal aberto — tudo certo