
from dotenv import dotenv_values
from neo4j import GraphDatabase

config = dotenv_values(".env.teste")

uri = config["NEO4J_URI"]
usuario = config["NEO4J_USER"]
senha = config["NEO4J_PASSWORD"]
banco = config.get("NEO4J_DATABASE", "neo4j")

try:
    with GraphDatabase.driver(
        uri,
        auth=(usuario, senha)
    ) as driver:

        driver.verify_connectivity()

        with driver.session(database=banco) as session:
            resultado = session.run("""
                MATCH (n)
                RETURN count(n) AS total_nos
            """).single()

            print("Conexao estabelecida com sucesso!")
            print("Instancia:", uri)
            print("Total de nos:", resultado["total_nos"])

except Exception as erro:
    print("Falha na conexao:", type(erro).__name__)
    print(str(erro))
