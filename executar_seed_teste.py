
import os
from dotenv import dotenv_values

config = dotenv_values(".env.teste")

# Configurar a instância de teste antes
# de importar o script de carga
os.environ["NEO4J_URI"] = config["NEO4J_URI"]
os.environ["NEO4J_USER"] = config["NEO4J_USER"]
os.environ["NEO4J_PASSWORD"] = config["NEO4J_PASSWORD"]
os.environ["NEO4J_DATABASE"] = config.get(
    "NEO4J_DATABASE", "neo4j"
)

from seed_grafo import carregar, driver

try:
    driver.verify_connectivity()

    print("Instância de teste:", config["NEO4J_URI"])
    print("Iniciando carga...")

    carregar()

    print("Teste de carga finalizado.")

finally:
    driver.close()
