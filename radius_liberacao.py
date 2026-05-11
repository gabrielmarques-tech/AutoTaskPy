# radius_liberacao.py
# Módulo com todas as interações do Radius Manager para o fluxo de LIBERAÇÃO.
#
# Herda de RadiusAutomacao (radius.py) reaproveitando:
#   - login()
#
# Adiciona métodos exclusivos da liberação:
#   - abrir_perfil_cliente()  → pesquisa pelo ID e abre o cadastro no Radius
#   - aplicar_plano()         → seleciona o Service plan correto e clica Update User
#
# LÓGICA DO MAPEAMENTO DE PLANOS:
#   O IXC retorna o plano como "150M / 50M" (após extração do regex em ixc_liberacao.py).
#   O Radius tem opções como "150M / 50M", "100M / 050M", etc.
#   A estratégia é:
#     1. Extrair os números do texto do IXC (download e upload)
#     2. Varrer todas as opções do dropdown do Radius
#     3. Selecionar a opção cujos números coincidam
#   Isso funciona para qualquer plano sem mapeamento manual.

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from radius import RadiusAutomacao
from selenium_helpers import safe_wait
from logger import logger


def _extrair_numeros_plano(texto: str) -> tuple[int, int]:
    """
    Extrai os valores numéricos de download e upload de um texto de plano.

    Exemplos:
      "150M / 50M"   → (150, 50)
      "1G / 200M"    → (1000, 200)   ← converte G para M multiplicando por 1000
      "100M / 050M"  → (100, 50)

    Retorna (0, 0) se não conseguir extrair.
    """
    # Busca padrões como "150M", "1G", "500M" etc.
    partes = re.findall(r'(\d+)\s*([MmGg])', texto)

    if len(partes) < 2:
        return (0, 0)

    def para_mega(valor: str, unidade: str) -> int:
        v = int(valor)
        return v * 1000 if unidade.upper() == 'G' else v

    download = para_mega(partes[0][0], partes[0][1])
    upload   = para_mega(partes[1][0], partes[1][1])
    return (download, upload)


class RadiusLiberacao(RadiusAutomacao):
    """Extensão do RadiusAutomacao com os métodos do fluxo de liberação."""

    # ------------------------------------------------------------------
    # Abertura do perfil
    # ------------------------------------------------------------------

    def abrir_perfil_cliente(self, id_cliente: str) -> None:
        """
        Pesquisa o cliente pelo ID no Radius e abre seu perfil.

        Reutiliza o mesmo fluxo de navegação da redução (menu → busca → resultado).
        Após abrir o perfil, o Radius mostra o cadastro completo do cliente
        incluindo o campo Service plan que será alterado em aplicar_plano().
        """
        logger.info(f"Abrindo perfil no Radius para ID: '{id_cliente}'")

        # Abre o menu de clientes
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/div/table/tbody/tr/td[2]/span[2]"),
            "clickable",
            timeout=10,
        ).click()
        time.sleep(0.6)

        # Seleciona busca por ID
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/div/div[2]/table/tbody/tr[2]/td[2]"),
            "clickable",
            timeout=10,
        ).click()
        time.sleep(0.6)

        # Preenche o ID e pesquisa
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

        # Abre o perfil do cliente encontrado
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[4]/tbody/tr[1]"
             "/td/table[2]/tbody/tr[2]/td[3]/font/a"),
            "clickable",
            timeout=10,
        ).click()

        logger.info("Perfil do cliente aberto no Radius.")

    # ------------------------------------------------------------------
    # Aplicação do plano
    # ------------------------------------------------------------------

    def aplicar_plano(self, plano_ixc: str) -> None:
        """
        Seleciona o Service plan correto no Radius com base no plano lido do IXC.

        Estratégia de matching:
          1. Extrai os números de download/upload do texto do IXC
             ex: "150M / 50M" → (150, 50)
          2. Varre todas as opções do dropdown do Radius
          3. Para cada opção, extrai seus números e compara
          4. Seleciona a opção cujos números coincidam
          5. Clica em Update User

        Essa abordagem funciona para qualquer plano sem mapeamento manual,
        mesmo que o formato do texto seja diferente entre IXC e Radius
        (ex: "050M" no Radius vs "50M" no IXC — os números são iguais).

        Levanta Exception se não encontrar nenhuma opção compatível.
        """
        logger.info(f"Buscando Service plan no Radius para: '{plano_ixc}'")

        # Rola a página para baixo para garantir que o select está visível
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)

        select_element = safe_wait(self.driver, (By.ID, "srvid"), "presence", timeout=10)
        select = Select(select_element)

        # Extrai os números do plano do IXC
        download_ixc, upload_ixc = _extrair_numeros_plano(plano_ixc)
        logger.info(f"Números extraídos do IXC → download: {download_ixc}M, upload: {upload_ixc}M")

        if download_ixc == 0:
            raise Exception(f"Não foi possível extrair números do plano '{plano_ixc}'.")

        # Varre as opções do dropdown procurando a que bate com o plano
        opcao_encontrada = None
        for opcao in select.options:
            texto_opcao = opcao.text.strip()

            # Pula a opção de redução (não deve ser selecionada na liberação)
            if "REDUÇÃO" in texto_opcao.upper() or "REDUCAO" in texto_opcao.upper():
                continue

            dl_radius, ul_radius = _extrair_numeros_plano(texto_opcao)

            if dl_radius == download_ixc and ul_radius == upload_ixc:
                opcao_encontrada = opcao
                logger.info(f"Service plan encontrado: '{texto_opcao}' (value={opcao.get_attribute('value')})")
                break

        if not opcao_encontrada:
            raise Exception(
                f"Nenhum Service plan compatível com '{plano_ixc}' "
                f"({download_ixc}M/{upload_ixc}M) encontrado no Radius."
            )

        # Salva o texto e value ANTES de selecionar para evitar StaleElementReferenceException
        # (após o Select mudar o valor, a referência ao elemento antigo fica inválida)
        valor_encontrado = opcao_encontrada.get_attribute("value")
        texto_encontrado = opcao_encontrada.text

        # Seleciona a opção pelo value
        Select(select_element).select_by_value(valor_encontrado)
        time.sleep(0.3)

        # Clica em Update User para salvar
        safe_wait(
            self.driver,
            (By.XPATH,
             "/html/body/table/tbody/tr[3]/td/table[1]/tbody/tr[1]/td/table[2]/tbody/tr"
             "/td/table/tbody/tr/td/form/p[3]/input"),
            "clickable",
            timeout=10,
        ).click()

        logger.info(f"Service plan '{texto_encontrado}' aplicado e Update User clicado.")