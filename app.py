"""
API da StreamFlix sobre Neo4j.
Projeto herdado do estagiario anterior, que saiu da empresa antes de terminar.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


app = FastAPI(title="StreamFlix - API sobre Neo4j")


class UsuarioIn(BaseModel):
    nome: str
    email: str
    criado_em: str  # "AAAA-MM-DD"


class AvaliacaoIn(BaseModel):
    usuario_id: int
    filme_id: int
    nota: int
    data: str  # "AAAA-MM-DD"


# ───────────────────────── Rota 1: GET /filmes ─────────────────────────

@app.get("/filmes")
def listar_filmes():
    cypher = """
    MATCH (f:Filme)
    RETURN f
    """

    with driver.session() as session:
        resultado = session.run(cypher)

        filmes = []

        for registro in resultado:
            filme = dict(registro["f"])
            filmes.append(filme)

        return filmes


# ───────────────────────── Rota 2: GET /filmes/busca (filtro) ─────────────────────────


@app.get("/filmes/busca")
def buscar_filmes(
    titulo: Optional[str] = None,
    genero: Optional[str] = None,
    ano: Optional[int] = None
):
    cypher = """
    MATCH (f:Filme)

    WHERE
        ($titulo IS NULL OR
         toLower(f.titulo) CONTAINS toLower($titulo))

    AND ($ano IS NULL OR f.ano = $ano)

    AND (
        $genero IS NULL OR
        EXISTS {
            MATCH (f)-[:PERTENCE_A]->(g:Genero)
            WHERE toLower(g.nome) = toLower($genero)
        }
    )

    RETURN f {
        .id,
        .titulo,
        .ano,
        .duracao_min,
        .sinopse
    } AS filme

    ORDER BY filme.titulo
    """

    with driver.session(database="neo4j") as session:
        resultado = session.run(
            cypher,
            titulo=titulo,
            genero=genero,
            ano=ano
        )

        return [dict(registro["filme"]) for registro in resultado]


# ───────────────────────── Rota 3: GET /filmes/{id} ─────────────────────────


@app.get("/filmes/{filme_id}")
def detalhe_filme(filme_id: int):
    cypher = """
    MATCH (f:Filme {id: $filme_id})

    OPTIONAL MATCH (f)-[:DIRIGIDO_POR]->(d:Pessoa)
    WITH f, collect(DISTINCT d.nome) AS diretores

    OPTIONAL MATCH (a:Pessoa)-[:ATUOU_EM]->(f)
    WITH f, diretores, collect(DISTINCT a.nome) AS atores

    OPTIONAL MATCH (f)-[:PERTENCE_A]->(g:Genero)

    RETURN
        f {
            .id,
            .titulo,
            .ano,
            .duracao_min,
            .sinopse
        } AS filme,
        diretores,
        atores,
        collect(DISTINCT g.nome) AS generos
    """

    with driver.session(database="neo4j") as session:
        resultado = session.run(cypher, filme_id=filme_id)
        registro = resultado.single()

        if registro is None:
            raise HTTPException(
                status_code=404,
                detail="Filme não encontrado"
            )

        filme = dict(registro["filme"])
        filme["diretores"] = registro["diretores"]
        filme["atores"] = registro["atores"]
        filme["generos"] = registro["generos"]

        return filme




# ───────────────────────── Rota 4: POST /usuarios ─────────────────────────



@app.post("/usuarios", status_code=201)
def criar_usuario(usuario: UsuarioIn):

    def cadastrar(tx):
        existente = tx.run("""
            MATCH (u:Usuario {email: $email})
            RETURN u.id AS id
        """, email=usuario.email).single()

        if existente:
            return None

        registro = tx.run("""
            MATCH (u:Usuario)
            WITH coalesce(max(u.id), 0) + 1 AS novo_id

            CREATE (novo:Usuario {
                id: novo_id,
                nome: $nome,
                email: $email,
                criado_em: $criado_em
            })

            RETURN
                novo.id AS id,
                novo.nome AS nome,
                novo.email AS email,
                novo.criado_em AS criado_em
        """,
            nome=usuario.nome,
            email=usuario.email,
            criado_em=usuario.criado_em
        ).single()

        return dict(registro)

    with driver.session(database="neo4j") as session:
        resultado = session.execute_write(cadastrar)

    if resultado is None:
        raise HTTPException(
            status_code=409,
            detail="Usuário com este e-mail já cadastrado"
        )

    return resultado




# ───────────────────────── Rota 5: POST /avaliacoes ─────────────────────────


@app.post("/avaliacoes")
def avaliar_filme(avaliacao: AvaliacaoIn):

    if not 1 <= avaliacao.nota <= 5:
        raise HTTPException(
            status_code=422,
            detail="A nota deve estar entre 1 e 5"
        )

    def registrar_avaliacao(tx):

        # Verificar se o usuário existe
        usuario = tx.run("""
            MATCH (u:Usuario {id: $usuario_id})
            RETURN u.id AS id
        """, usuario_id=avaliacao.usuario_id).single()

        if usuario is None:
            return {"erro": "usuario_nao_encontrado"}

        # Verificar se o filme existe
        filme = tx.run("""
            MATCH (f:Filme {id: $filme_id})
            RETURN f.id AS id
        """, filme_id=avaliacao.filme_id).single()

        if filme is None:
            return {"erro": "filme_nao_encontrado"}

        # Criar ou atualizar a avaliação
        registro = tx.run("""
            MATCH (u:Usuario {id: $usuario_id})
            MATCH (f:Filme {id: $filme_id})

            MERGE (u)-[a:AVALIOU]->(f)

            SET a.nota = $nota,
                a.data = $data

            RETURN
                u.id AS usuario_id,
                f.id AS filme_id,
                a.nota AS nota,
                a.data AS data
        """,
            usuario_id=avaliacao.usuario_id,
            filme_id=avaliacao.filme_id,
            nota=avaliacao.nota,
            data=avaliacao.data
        ).single()

        return dict(registro)

    with driver.session(database="neo4j") as session:
        resultado = session.execute_write(registrar_avaliacao)

    if resultado.get("erro") == "usuario_nao_encontrado":
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )

    if resultado.get("erro") == "filme_nao_encontrado":
        raise HTTPException(
            status_code=404,
            detail="Filme não encontrado"
        )

    return resultado



# ───────────────────────── Rota 6: GET /relatorios/ranking ─────────────────────────


@app.get("/relatorios/ranking")
def ranking_filmes():
    cypher = """
    MATCH (f:Filme)

    OPTIONAL MATCH (u:Usuario)-[a:AVALIOU]->(f)

    WITH
        f,
        count(a) AS total_avaliacoes,
        avg(a.nota) AS media

    RETURN
        f.id AS filme_id,
        f.titulo AS titulo,
        total_avaliacoes,
        media AS media_avaliacoes

    ORDER BY
        media_avaliacoes IS NULL ASC,
        media_avaliacoes DESC,
        total_avaliacoes DESC,
        titulo ASC
    """

    with driver.session(database="neo4j") as session:
        resultado = session.run(cypher)

        ranking = []

        for registro in resultado:
            ranking.append({
                "filme_id": registro["filme_id"],
                "titulo": registro["titulo"],
                "total_avaliacoes": registro["total_avaliacoes"],
                "media_avaliacoes": (
                    round(registro["media_avaliacoes"], 2)
                    if registro["media_avaliacoes"] is not None
                    else None
                )
            })

        return ranking
