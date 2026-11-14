# StreamFlix — API sobre Neo4j

Projeto entregue como está: código de um protótipo anterior, que precisa ser
posto para funcionar e corrigido antes de ir para produção.

## Como executar

```bash
pip install -r requirements.txt
python seed_grafo.py
uvicorn app:app --reload
```

> **Windows:** se `uvicorn` não for reconhecido, use
> `python -m uvicorn app:app --reload`.

A API deveria subir em `http://localhost:8000/docs`. O Neo4j é esperado
rodando localmente com a senha configurada em `app.py`/`seed_grafo.py`
(ajustem para a senha de vocês).

O enunciado completo do exercício (o que precisa ser entregue e como é
avaliado) está em `Exercícios/Exercicio_Debug_Neo4j_Streaming.md`.
