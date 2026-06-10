# Estudo IA – Assistente Local de Estudos

Assistente de estudos 100% local e gratuito. Faça upload de PDFs e converse com a IA sobre o conteúdo usando RAG (Retrieval-Augmented Generation).

**Sem custo · Sem internet · Sem APIs externas**

## Como funciona

1. Você faz upload de um PDF
2. O sistema extrai o texto, divide em trechos e gera embeddings localmente
3. Quando você faz uma pergunta, o sistema encontra os trechos mais relevantes e envia ao modelo local (Ollama)
4. O modelo responde com base apenas no seu material

## Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd teste

# 2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale e inicie o Ollama (em outro terminal)
ollama serve

# 5. Baixe um modelo (escolha um)
ollama pull llama3.2        # recomendado — 2 GB, rápido
ollama pull llama3.2:1b     # mais leve — 1.3 GB
ollama pull mistral         # mais preciso — 4 GB
```

## Executando

```bash
uvicorn app:app --reload
```

Acesse: http://localhost:8000

## Uso

1. Na sidebar esquerda, clique em **Upload de PDF** (ou arraste um arquivo)
2. Aguarde o processamento (aparecerá na lista de documentos)
3. Digite sua pergunta no chat e pressione Enter
4. A IA responderá com base no conteúdo dos seus documentos

## Modelos recomendados

| Modelo | RAM | Velocidade | Qualidade |
|--------|-----|-----------|-----------|
| `llama3.2:1b` | ~1.5 GB | rápido | boa |
| `llama3.2` | ~2 GB | médio | ótima |
| `mistral` | ~4 GB | lento | excelente |
