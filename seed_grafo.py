"""
Carga inicial do banco da StreamFlix (catalogo de filmes).
Script herdado de uma versao anterior do projeto, antes da virada para Neo4j.
Rodar uma vez para popular o banco antes de subir a API (app.py).
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("Credenciais do Neo4j não configuradas.")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

FILMES = [
    {
        "id": 1, "titulo": "Fronteira Vermelha", "ano": 2019, "duracao_min": 128,
        "sinopse": "Um piloto precisa atravessar o deserto antes que a tempestade chegue.",
        "genero": "Acao", "diretor_nome": "Marina Kessel",
        "atores": "Theo Vance, Lia Brandt, Marina Kessel",
    },
    {
        "id": 2, "titulo": "Silencio de Vidro", "ano": 2021, "duracao_min": 104,
        "sinopse": "Uma investigadora descobre que o crime comecou dentro da propria familia.",
        "genero": "Drama", "diretor_nome": "Caue Abrantes",
        "atores": "Lia Brandt, Rafael Nunes",
    },
    {
        "id": 3, "titulo": "Risos do Andar de Baixo", "ano": 2022, "duracao_min": 96,
        "sinopse": "Dois vizinhos competem para ver quem incomoda mais o predio.",
        "genero": "Comedia", "diretor_nome": "Marina Kessel",
        "atores": "Theo Vance, Rafael Nunes",
    },
    {
        "id": 4, "titulo": "Orbita Zero", "ano": 2023, "duracao_min": 141,
        "sinopse": "A tripulacao de uma estacao espacial perde contato com a Terra.",
        "genero": "Acao", "diretor_nome": "Caue Abrantes",
        "atores": "Lia Brandt, Theo Vance",
    },
]

USUARIOS = [
    {"id": 1, "nome": "Patricia Souza", "email": "patricia@streamflix.com", "criado_em": "2024-02-10"},
    {"id": 2, "nome": "Igor Matos", "email": "igor@streamflix.com", "criado_em": "2024-03-05"},
]

# avaliacoes guardadas junto do usuario que avaliou, do jeito que vieram
# do protótipo antigo em planilha
AVALIACOES_POR_USUARIO = {
    1: [
        {"filme_id": 1, "nota": 5, "data": "2024-04-01"},
        {"filme_id": 2, "nota": 3, "data": "2024-04-03"},
    ],
    2: [
        {"filme_id": 1, "nota": 4, "data": "2024-04-02"},
        {"filme_id": 4, "nota": 5, "data": "2024-05-10"},
    ],
}



def carregar_dados(tx):
    # 1. Criar ou atualizar filmes
    for filme in FILMES:
        tx.run("""
            MERGE (f:Filme {id: $id})
            SET f.titulo = $titulo,
                f.ano = $ano,
                f.duracao_min = $duracao_min,
                f.sinopse = $sinopse
        """, **filme).consume()

        # 2. Diretor como nó Pessoa
        tx.run("""
            MATCH (f:Filme {id: $filme_id})
            MERGE (p:Pessoa {nome: $nome})
            MERGE (f)-[:DIRIGIDO_POR]->(p)
        """, filme_id=filme["id"],
             nome=filme["diretor_nome"]).consume()

        # 3. Atores como nós Pessoa
        atores = [a.strip() for a in filme["atores"].split(",")]

        for ator in atores:
            tx.run("""
                MATCH (f:Filme {id: $filme_id})
                MERGE (p:Pessoa {nome: $nome})
                MERGE (p)-[:ATUOU_EM]->(f)
            """, filme_id=filme["id"],
                 nome=ator).consume()

        # 4. Gêneros como nós
        tx.run("""
            MATCH (f:Filme {id: $filme_id})
            MERGE (g:Genero {nome: $genero})
            MERGE (f)-[:PERTENCE_A]->(g)
        """, filme_id=filme["id"],
             genero=filme["genero"]).consume()

    # 5. Criar ou atualizar usuários
    for usuario in USUARIOS:
        tx.run("""
            MERGE (u:Usuario {id: $id})
            SET u.nome = $nome,
                u.email = $email,
                u.criado_em = $criado_em
        """, **usuario).consume()

    # 6. Criar avaliações como relacionamentos
    for usuario_id, avaliacoes in AVALIACOES_POR_USUARIO.items():
        for avaliacao in avaliacoes:
            tx.run("""
                MATCH (u:Usuario {id: $usuario_id})
                MATCH (f:Filme {id: $filme_id})
                MERGE (u)-[a:AVALIOU]->(f)
                ON CREATE SET
                    a.nota = $nota,
                    a.data = $data
            """,
                usuario_id=usuario_id,
                filme_id=avaliacao["filme_id"],
                nota=avaliacao["nota"],
                data=avaliacao["data"]
            ).consume()


def carregar():
    with driver.session(database="neo4j") as session:
        # Restrições para evitar nós duplicados
        restricoes = [
            "CREATE CONSTRAINT filme_id IF NOT EXISTS "
            "FOR (f:Filme) REQUIRE f.id IS UNIQUE",

            "CREATE CONSTRAINT usuario_id IF NOT EXISTS "
            "FOR (u:Usuario) REQUIRE u.id IS UNIQUE",

            "CREATE CONSTRAINT pessoa_nome IF NOT EXISTS "
            "FOR (p:Pessoa) REQUIRE p.nome IS UNIQUE",

            "CREATE CONSTRAINT genero_nome IF NOT EXISTS "
            "FOR (g:Genero) REQUIRE g.nome IS UNIQUE"
        ]

        for cypher in restricoes:
            session.run(cypher).consume()

        # Executa a carga em uma única transação
        session.execute_write(carregar_dados)

    print("Carga do grafo concluída com sucesso!")


if __name__ == "__main__":
    try:
        carregar()
    finally:
        driver.close()
