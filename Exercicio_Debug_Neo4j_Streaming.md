# Exercício — Diagnóstico e Correção de um Sistema sobre Neo4j

## Contexto

Vocês receberam o código de um sistema real: a API de catálogo da
**StreamFlix**, um serviço de streaming de filmes. O projeto foi deixado por
quem trabalhava nele antes, está incompleto e, no estado em que chegou até
vocês, **não funciona** — a API não consegue conversar com o banco, e o
próprio banco não está armazenando os dados da forma como um banco de grafos
deveria.

Isso é mais comum do que parece em desenvolvimento de software: entrar num
projeto que já existe, descobrir por que ele não funciona e corrigi-lo, sem
ninguém ao lado explicando o que foi feito. Esse é o exercício.

Vocês podem (e devem, se quiserem) usar IA para ajudar. Mas usar IA aqui não
é digitar "conserta esse código" e colar a resposta: a IA não sabe o que foi
ensinado nesta disciplina nem o padrão de modelagem de grafo que o professor
espera. Quem souber **o que perguntar**, **o que testar** e **o que
questionar** na resposta da IA termina com um sistema correto. Quem apenas
aceitar a primeira sugestão termina com um sistema que até roda, mas continua
sem seguir o padrão de grafo necessário — e isso custa mais pontos do que o
sistema simplesmente não funcionar (ver critérios de avaliação).

Importante: nem todo problema deste sistema aparece lendo o código ou pedindo
pra uma IA revisá-lo — alguns só aparecem **rodando o sistema com dados
reais** e comparando o resultado com o que era esperado (ver "Cenários que
precisam funcionar de verdade", abaixo). Uma IA que só leu o `app.py` e disse
"está tudo certo" não testou nada — quem entrega só isso como validação não
atende à Declaração de Uso de IA.

## Objetivos de aprendizagem

- Diagnosticar falhas de conexão e de execução entre uma API e um banco de
  dados — habilidade de depuração geral, não específica de Neo4j.
- Reconhecer, num banco de grafos já existente, se a modelagem (nós,
  relacionamentos, propriedades) reflete de fato as entidades e associações
  do domínio, ou se está apenas "disfarçada" de grafo.
- Corrigir a modelagem e as consultas Cypher para que passem a seguir os
  princípios de banco de dados de grafos trabalhados em aula.
- Usar IA de forma crítica: formular boas perguntas, validar as respostas
  contra o que foi efetivamente ensinado (e contra o que vocês já sabem de
  outras disciplinas de desenvolvimento de sistemas/back-end), e documentar
  esse processo de forma honesta.

## O que vocês recebem

Uma pasta de projeto (`app.py`, `seed_grafo.py`, `requirements.txt`,
`README.md`) com uma API em FastAPI sobre Neo4j. Ao tentar rodar, vocês vão
encontrar problemas em pelo menos dois níveis diferentes — e é esperado que
vocês mesmos descubram quais, exatamente:

1. **O sistema não funciona de ponta a ponta.** Alguma coisa impede a API de
   se conectar ao banco ou impede uma ou mais rotas de responder
   corretamente.
2. **O banco não segue o padrão de grafo necessário.** Mesmo depois de a
   conexão estar de pé, a forma como os dados estão guardados não corresponde
   a como um banco de grafos deveria representar este domínio — revisem os
   conceitos de modelagem e boas práticas vistos nas aulas de Neo4j
   (introdução, prática e migração) antes de decidir o que está errado e por
   quê.

Não vamos listar os problemas aqui. Encontrar e justificar cada um — com base
no que foi ensinado, não por tentativa e erro às cegas — é parte do que está
sendo avaliado.

## O domínio: catálogo da StreamFlix

A StreamFlix cataloga filmes. Cada filme tem um diretor, um ou mais atores no
elenco e pertence a um ou mais gêneros. Usuários cadastrados podem avaliar
filmes com uma nota — e um mesmo usuário avaliando o mesmo filme de novo deve
**atualizar** a nota dada, não criar uma segunda avaliação solta.

## Rotas obrigatórias (resumo)

| # | Rota | O que precisa fazer |
|---|---|---|
| 1 | `GET /filmes` | Lista os filmes do catálogo |
| 2 | `GET /filmes/{id}` | Detalhe de um filme, incluindo diretor, elenco e gênero(s) |
| 3 | `GET /filmes/busca` | Filtra filmes por algum critério (gênero, título, nota, ano — à escolha de vocês), sem abrir brecha de injeção na consulta |
| 4 | `POST /usuarios` | Cadastra um usuário |
| 5 | `POST /avaliacoes` | Usuário avalia um filme (reavaliar atualiza, não duplica) |
| 6 | `GET /relatorios/ranking` | Ranking de filmes por nota média das avaliações |

O código entregue já tem uma tentativa de cada uma dessas seis rotas — parte
delas pode estar certa, parte pode não estar. Testem rota por rota.

## Cenários que precisam funcionar de verdade

Além das seis rotas, pelo menos estes três comportamentos precisam ser
testados com requisições reais (não só "a rota existe e não dá erro"). Nenhum
dos três aparece como um erro óbvio só de olhar o código — só rodando:

1. **Reavaliar não duplica.** Façam `POST /avaliacoes` duas vezes para o
   mesmo usuário e o mesmo filme, com notas diferentes. No fim, deve existir
   **uma** avaliação daquele usuário para aquele filme, com a nota mais
   recente — não duas.
2. **Avaliar algo que não existe não pode "dar certo".** Façam
   `POST /avaliacoes` com um `filme_id` (ou `usuario_id`) que não existe no
   banco. A resposta precisa indicar erro (ex.: `404`) — se a API responder
   `201` como se tivesse funcionado, ela está aceitando uma avaliação "no
   vazio", sem checar se o que está sendo referenciado de fato existe.
3. **Buscar por um título com aspas simples não pode quebrar nem "escapar"
   da busca.** Testem `GET /filmes/busca` com um título contendo `'` (por
   exemplo, um valor como `Teste' OR '1'='1`). O resultado esperado é uma
   busca normal (sem resultado, ou resultado filtrado de verdade) — não um
   erro de sintaxe nem a lista completa de filmes vazando por engano.

Guardem a evidência (request + resposta) desses três testes junto com a
evidência das rotas — eles contam na nota de "funcionamento" e no
diagnóstico escrito.

## O que entregar

1. **Código corrigido** (API + script de carga do banco), com evidência de
   que cada rota da tabela acima funciona (print do Swagger, coleção de
   requisições, ou script de teste).
2. **Diagnóstico por escrito**, para cada problema que vocês corrigiram:
   - O que estava errado (sintoma + causa real, não só "dava erro").
   - Qual conceito de aula (ou de outra disciplina de desenvolvimento de
     sistemas) justifica a forma como vocês corrigiram.
3. **Declaração de Uso de IA** (obrigatória, mesmo que não tenham usado).
4. **Autoavaliação de Entendimento, Domínio e Tempo Gasto** (obrigatória).

### Declaração de Uso de IA

Podem usar IA (ChatGPT, Claude, Copilot, Gemini etc.) em qualquer parte.
Condição: declarar por escrito:

- Qual(is) ferramenta(s) de IA usou, **incluindo o modelo** (ex.: "Claude,
  modelo Sonnet 4.5"; "ChatGPT, GPT-5.1"), ou "nenhuma".
- Em quais partes a IA foi usada (ex.: diagnóstico da falha de conexão,
  correção da modelagem do grafo, reescrita de uma query específica).
- Quais métricas usou para validar o que a IA sugeriu, **antes de aceitar**.
  Pelo menos **uma métrica quantitativa** + **uma justificativa
  qualitativa**. Exemplos: corretude (testou e o retorno bateu com o
  esperado?), taxa de retrabalho (quantas correções precisou fazer até
  funcionar), completude (a IA cobriu os casos de erro?), coerência com o
  que foi ensinado em aula (a sugestão da IA usa o mesmo padrão de
  modelagem/consulta visto nas aulas de Neo4j, ou inventou outra coisa que
  "parece funcionar")?
- **Obrigatório:** descrevam pelo menos **um caso concreto** em que a
  primeira resposta da IA pareceu certa, mas se mostrou errada, incompleta ou
  insegura quando vocês de fato rodaram o sistema (ex.: um dos três cenários
  da seção "Cenários que precisam funcionar de verdade"). Digam o que a IA
  sugeriu, o que o teste real mostrou, e o que vocês mudaram por causa disso.
  Se a IA acertou tudo de primeira em todos os pontos, digam isso também —
  mas expliquem como verificaram cada um dos três cenários mesmo assim.

Declarações vagas, sem métrica ou sem o caso concreto acima, contam como não
cumprido.

### Autoavaliação de Entendimento, Domínio e Tempo Gasto

Para cada parte abaixo, dê uma nota de 1 a 5 (1 = "só copiei, não sei
explicar"; 5 = "domino e refaço sem apoio"), justifique em 1–2 frases, e
informe o **tempo aproximado** que levou:

| Parte | Nota (1–5) | Justificativa | Tempo aproximado |
|---|---|---|---|
| Diagnóstico da falha de conexão/execução | | | |
| Correção da modelagem do grafo | | | |
| Reescrita das consultas Cypher afetadas | | | |
| Uso crítico da IA (o que pediu, o que questionou) | | | |

Informem também o **tempo total aproximado** do exercício. Pode ser
verificado oralmente a critério do professor.

## Entrega

- Código completo (API + script de carga), em repositório ou `.zip`.
- Evidência de teste de cada rota e dos três cenários de borda.
- Diagnóstico por escrito.
- Declaração de Uso de IA.
- Autoavaliação.

Prazo: [preencher no AVA].

## Critérios de Avaliação (total 1,0 ponto)

| Critério | Pontos |
|---|---|
| Modelagem do grafo corrigida: estrutura final (nós, relacionamentos e propriedades) coerente com o domínio e com os princípios de banco de grafos trabalhados em aula | 0,40 |
| Conexão restabelecida e API respondendo corretamente nas seis rotas obrigatórias, incluindo os três cenários de borda | 0,20 |
| Diagnóstico por escrito, correto e justificado com conceitos (de aula ou de outras disciplinas) — não apenas "a IA corrigiu" | 0,10 |
| Declaração de Uso de IA, com ferramenta, modelo, métrica concreta e o caso de correção após teste real | 0,10 |
| Autoavaliação de entendimento/domínio e tempo gasto, coerente com o código entregue | 0,10 |
| Evidência de teste de cada rota e de cada cenário de borda | 0,10 |

Um sistema que **funciona mas mantém o banco fora do padrão de grafo
necessário** perde mais pontos do que um sistema **com o banco corrigido mas
alguma rota ainda com problema** — a modelagem correta do banco é o critério
de maior peso deste exercício.
