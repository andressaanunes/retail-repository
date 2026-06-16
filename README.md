# ☕ Retail Insights

**Simulador de Expansão — Análise de Vazios Comerciais via IA Geográfica**

Aplicação interativa para análise estratégica de expansão de redes varejistas, combinando geolocalização, inteligência artificial (Gemini) e visualização em mapas interativos.

## Funcionalidades

- **Mapa interativo** com clustering de lojas e sugestões de expansão (Folium)
- **Simulador de cenários** com parâmetros: densidade populacional, renda, público-alvo e fluxo de pedestres
- **Análise estratégica via IA** (Google Gemini) com sugestões de localização e formato ideal de loja (drive-thru, flagship, quiosque ou core)
- **KPIs dinâmicos** por país, estado e cidade
- **Formulário de avaliação** com escala Likert integrado ao Supabase
- **Interface bilíngue** (Português/Inglês) com tema claro/escuro

## Tecnologias

| Tecnologia | Uso |
|---|---|
| [Streamlit](https://streamlit.io/) | Framework web |
| [Folium](https://python-visualization.github.io/folium/) | Mapas interativos |
| [Google Gemini](https://ai.google.dev/) | Análise estratégica de expansão |
| [Supabase](https://supabase.com/) | Banco de dados (lojas, imagens, respostas) |
| [Pandas](https://pandas.pydata.org/) | Manipulação de dados |

## Pré-requisitos

- Python 3.11+

## Instalação

```bash
pip install streamlit pandas folium streamlit-folium supabase google-generativeai requests
```

## Configuração

Crie um arquivo `.streamlit/secrets.toml` com as seguintes chaves:

```toml
SUPABASE_URL = "https://<seu-projeto>.supabase.co"
SUPABASE_KEY = "<sua-chave-anon>"
GEMINI_API_KEY = "<sua-chave-gemini>"
```

## Execução

```bash
streamlit run retail-expansion-ai.py
```

## Estrutura do CSV esperado

O arquivo de entrada deve conter as colunas (case-insensitive):

| Coluna | Descrição |
|---|---|
| `Latitude` | Latitude da loja |
| `Longitude` | Longitude da loja |
| `City` | Cidade |
| `Country` | País |
| `State/Province` | Estado ou província |

O carregamento segue a prioridade: **CSV enviado** > **Supabase** > **fallback local**.

## Licença

Este projeto é de uso acadêmico (TCC).
