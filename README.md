# Maré Boa

**Um agente cognitivo para decisão de surf no Rio de Janeiro**

Projeto da disciplina **Agentes Cognitivos com LangChain**
Instituto Infnet, Pós-graduação em IA e Machine Learning, Novembro de 2026

**Aluna:** Maria Glatthardt Grisolia · **Professor:** Gabriel Caldas

---

## O problema

Surfo há alguns meses e sou iniciante. A decisão de onde e quando surfar depende da interação entre direção do swell contra a orientação da praia, direção do vento, período da ondulação e o meu nível. Um site de previsão entrega os números; o raciocínio fica comigo.

Este agente faz o cruzamento: consulta a condição real de oito praias, cruza com as características de cada uma, filtra pelo meu nível e explica a recomendação. Diferente de um site, ele personaliza, decompõe pergunta composta e lembra do que eu disse antes.

## O que o agente faz

| Capacidade | Como |
|---|---|
| Condição real do mar | Open-Meteo Marine e Forecast, ao vivo, sem chave |
| Compara 8 praias e recomenda | Pontuação determinística cruzando swell, vento, tamanho e período com a orientação da praia |
| Serviços próximos | Text-to-query sobre banco com aluguel de prancha, escolas, comida, preços e acessos |
| Dimensiona prancha | Fórmula de volume e comprimento a partir de peso, altura, nível, idade e condicionamento |
| Explica conceitos | RAG sobre índice FAISS, com reescrita de consulta para o vocabulário dos documentos |
| Lembra entre conversas | Checkpointer para curto prazo, store para perfil e histórico de sessões |
| Verifica o que respondeu | Camada que compara a resposta contra a evidência das ferramentas |

## Estrutura

```
.
├── agente_surf.ipynb    notebook executado, 100 células, 5 fases
├── app.py               interface Streamlit
├── requirements.txt
└── README.md
```

O relatório técnico em PDF e o vídeo de demonstração são entregues no Moodle.

## Resultados

**Fase 1, a chain MVP:** 8 de 8 intenções classificadas corretamente, incluindo apelido coloquial e entidade embutida. O `batch` foi **10,6 vezes mais rápido** que a execução sequencial (1,00 s contra 10,58 s), que é o argumento concreto a favor da composição declarativa com LCEL.

**Fase 2, o agente:** roteamento mediu 1,5 s para dúvida conceitual contra 30,7 s para o agente completo, **20 vezes** de diferença. Encontrei duas inconsistências factuais reais, em que o agente recebeu dado correto e escreveu texto errado, o que motivou a camada de verificação da Fase 5.

**Fase 3, memória:** o agente guardou um fato dito de passagem sem que eu pedisse, recuperou em thread nova, e encadeou duas ferramentas num só turno. Recomendou a Barra em vez da Macumba mesmo depois de eu dizer que amei a Macumba, argumentando com os dados.

**Fase 4, RAG:** **4 de 6** perguntas em gíria de surfista recuperaram o documento errado. A reescrita de consulta melhorou o score médio em **43%** (1,354 para 0,773), mas não corrigiu tudo, e o caso remanescente falhou por viés nos meus próprios exemplos.

**Fase 5, avaliação:**

| Métrica | Resultado |
|---|---|
| Trajetória de ferramentas correta | 8/9 (89%) |
| Sem contradição factual | 6/9 (67%) |
| Logicamente coerentes | 7/9 (78%) |
| **Com ferramenta desnecessária** | **0/9 (0%)** |
| Tempo médio por caso | 37,1 s |

O verificador detectou as duas falhas reais da Fase 2 e aprovou o caso de controle.

**O achado mais importante:** num caso fora do escopo, o agente respondeu uma pergunta de conhecimento geral violando regra explícita do prompt, e **as duas métricas aprovaram**, porque nenhuma ferramenta foi chamada e não havia evidência para contradizer. Falta um terceiro eixo de aderência a política, e essa é a lição sobre a avaliação, não sobre o agente.

## Como executar

Desenvolvido e executado no **Google Colab** (CPU basta).

1. Abrir `agente_surf.ipynb` no Colab
2. Cadastrar nos Secrets (ícone de chave): `GROQ_API_KEY` e `LANGSMITH_API_KEY`, com acesso ao notebook ligado
3. Ambiente de execução, Executar tudo

As chaves são gratuitas: `console.groq.com` e `smith.langchain.com`, sem cartão de crédito.

### Sem credenciais

O notebook detecta a ausência de chave e ativa `MODO_DEMO` sozinho, com um modelo simulado sensível ao prompt, que devolve JSON quando o prompt pede JSON e texto quando pede texto. **Todas as células executam** e a estrutura do agente é idêntica, o que permite auditar o código sem nenhuma credencial.

### A interface

Subir o `app.py` pelo painel de arquivos do Colab e executar a última célula do notebook, que configura o Streamlit e abre pelo proxy nativo do Colab, sem necessidade de túnel externo.

Para rodar localmente: `pip install -r requirements.txt` e `streamlit run app.py`, com `GROQ_API_KEY` em `.streamlit/secrets.toml`.

## Nota sobre as versões

O projeto usa a **série 1.x do LangChain**, que é a das aulas. Nessa série, `initialize_agent`, `AgentExecutor` e o pacote `langchain.memory` foram removidos, e a criação de agentes foi consolidada em `create_agent`, com a memória gerenciada por checkpointers. A seção 2.5 do relatório documenta a correspondência entre cada construção clássica e o seu substituto.

O identificador do modelo **não é fixo no código**: o notebook consulta o endpoint de modelos do provedor e escolhe por ordem de preferência. O motivo é concreto, já que o `llama-3.3-70b-versatile` foi desativado pelo Groq em agosto de 2026 e um identificador fixo quebrou o projeto na primeira execução.

## Uso de ferramentas de IA

Conforme exigido no enunciado, registro que utilizei um assistente de IA como apoio na estruturação inicial do código, na revisão de texto e na verificação de cálculos. A escolha do domínio, a execução dos experimentos, as decisões de arquitetura, a identidade visual e as análises são de minha autoria. Todos os números citados vêm das execuções registradas no notebook.
