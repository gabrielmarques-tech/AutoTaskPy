# logger.py
# Módulo de log centralizado.
# Escreve no console E em arquivo automacao.log (mesmo diretório do script).

import logging
import os

def configurar_logger() -> logging.Logger:
    """
    Cria e retorna um logger configurado com saída em arquivo e console.
    Chamado uma única vez no início da aplicação.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "automacao.log")

    logger = logging.getLogger("automacao")
    logger.setLevel(logging.DEBUG)

    # Evita adicionar handlers duplicados se o módulo for reimportado
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Handler de arquivo
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Handler de console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# Instância global usada pelos outros módulos:  from logger import logger
logger = configurar_logger()