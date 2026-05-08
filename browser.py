# browser.py
# Responsável por criar e destruir o navegador Chrome.
#
# ESTRATÉGIA PARA MANTER O CHROMEDRIVER SEMPRE COMPATÍVEL:
#
#   Plano A — Selenium Manager (embutido no Selenium 4.6+):
#     O próprio Selenium já inclui um gerenciador interno que detecta a versão
#     do Chrome instalada e baixa o chromedriver certo. Não precisa de nenhuma
#     dependência extra. Basta NÃO passar um Service com caminho fixo.
#
#   Plano B — webdriver-manager (fallback):
#     Se o Selenium Manager falhar por algum motivo (rede, proxy, permissão),
#     tentamos com o webdriver-manager como segunda opção.
#
# CAUSA DO ERRO WinError 193:
#   O webdriver-manager às vezes baixa um executável corrompido ou de
#   arquitetura errada e salva no cache. Na próxima execução ele reutiliza
#   o arquivo com defeito sem baixar novamente.
#   Solução: limpar o cache antes de tentar, e usar o Selenium Manager
#   como Plano A (que não tem esse problema de cache).

import os
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from logger import logger


def _limpar_cache_webdriver_manager() -> None:
    """
    Remove o cache local do webdriver-manager (~/.wdm).
    Chamado antes do Plano B para evitar reutilização de arquivo corrompido.
    """
    cache_dir = os.path.join(os.path.expanduser("~"), ".wdm")
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            logger.info("Cache do webdriver-manager limpo.")
        except Exception as e:
            logger.warning(f"Não foi possível limpar cache do wdm: {e}")


def _opcoes_chrome() -> webdriver.ChromeOptions:
    """Retorna as opções padrão do Chrome para a automação."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Suprime logs de debug do chromedriver no console
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return options


def criar_navegador(timeout_padrao: int = 25) -> tuple[webdriver.Chrome, WebDriverWait]:
    """
    Cria uma instância do Chrome com chromedriver gerenciado automaticamente.

    Tenta duas estratégias em ordem:
      1. Selenium Manager (embutido, sem dependências extras)
      2. webdriver-manager (com limpeza de cache antes de tentar)

    Parâmetros
    ----------
    timeout_padrao : int
        Tempo máximo (segundos) que o WebDriverWait vai aguardar elementos.

    Retorna
    -------
    driver : webdriver.Chrome
    wait   : WebDriverWait já configurado com o timeout padrão

    Levanta RuntimeError se nenhuma estratégia funcionar.
    """
    options = _opcoes_chrome()

    # ------------------------------------------------------------------
    # Plano A: Selenium Manager (sem caminho fixo = usa o gerenciador interno)
    # ------------------------------------------------------------------
    try:
        logger.info("Plano A: iniciando Chrome via Selenium Manager...")
        # Não passar Service() = Selenium 4.6+ usa o Selenium Manager embutido
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, timeout_padrao)
        logger.info("✅ Chrome iniciado com sucesso via Selenium Manager.")
        return driver, wait

    except Exception as e:
        logger.warning(f"Plano A falhou: {e}")

    # ------------------------------------------------------------------
    # Plano B: webdriver-manager com cache limpo
    # ------------------------------------------------------------------
    try:
        logger.info("Plano B: iniciando Chrome via webdriver-manager (limpando cache)...")
        _limpar_cache_webdriver_manager()

        # Import aqui para não quebrar se o pacote não estiver instalado
        from webdriver_manager.chrome import ChromeDriverManager

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, timeout_padrao)
        logger.info("✅ Chrome iniciado com sucesso via webdriver-manager.")
        return driver, wait

    except Exception as e:
        logger.error(f"Plano B também falhou: {e}")

    raise RuntimeError(
        "Não foi possível iniciar o Chrome por nenhuma estratégia.\n"
        "Verifique se o Google Chrome está instalado e tente novamente."
    )


def fechar_navegador(driver: webdriver.Chrome) -> None:
    """Encerra o navegador de forma segura."""
    try:
        driver.quit()
        logger.info("Navegador encerrado.")
    except Exception:
        pass  # Se já estiver fechado, ignora silenciosamente