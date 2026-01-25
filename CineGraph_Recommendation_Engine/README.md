# 🎬 CineGraph - Sistema de Recomendação Baseado em Grafos

> Descubra filmes através de conexões ocultas entre atores, diretores e temas, utilizando Teoria dos Grafos.

![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![React](https://img.shields.io/badge/React-Vite-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)

## 📖 Sobre o Projeto

O **CineGraph** é uma aplicação Full Stack que foge dos filtros tradicionais. Em vez de apenas filtrar por "Ação" ou "Comédia", ele constrói um **Grafo Não-Direcionado Ponderado** onde:
* **Nós (Nodes):** São Filmes, Atores, Diretores, Gêneros e Palavras-chave.
* **Arestas (Edges):** São as conexões entre eles (ex: Filme A *tem como diretor* Christopher Nolan).

O algoritmo calcula o **caminho** entre um filme e outro, somando pesos para determinar a relevância da recomendação.

---

## 🚀 Funcionalidades Principais

* **Algoritmo de Recomendação:** Lógica personalizada usando `NetworkX` para percorrer vizinhos de 1º e 2º grau.
* **ETL Otimizado (Multithread):** Pipeline de extração de dados da API do TMDB capaz de baixar e processar milhares de filmes simultaneamente usando `ThreadPoolExecutor` e controle de concorrência (`threading.Lock`).
* **Busca Inteligente:** Encontre o ID de qualquer filme pelo nome antes de pedir recomendações.
* **Interface Interativa:** Frontend em React (Vite) limpo e responsivo.

---

## 🛠️ Tecnologias Utilizadas

### Backend & Data
* **Python:** Linguagem principal.
* **FastAPI:** Framework para criação da API REST.
* **NetworkX:** Biblioteca para construção e manipulação do Grafo.
* **PostgreSQL:** Banco de dados relacional para persistência dos metadados.
* **Psycopg2:** Driver de conexão com o banco.

### Frontend
* **React.js:** Biblioteca de interface.
* **Vite:** Build tool rápida.
* **Axios:** Consumo de API.
* **CSS3:** Estilização responsiva.

---

## ⚙️ Como o Algoritmo Funciona

O sistema atribui "pesos" diferentes para cada tipo de conexão, priorizando a visão artística sobre categorias genéricas:

| Conexão (Aresta) | Peso | Justificativa |
| :--- | :---: | :--- |
| **Diretor** | `5.0` | O estilo de direção é o fator mais forte de similaridade. |
| **Ator/Atriz** | `3.0` | Elenco define muito o tom do filme. |
| **Keyword (Tema)** | `2.0` | Temas específicos (ex: "viagem no tempo") são bons conectores. |
| **Gênero** | `0.5` | Muito genérico, serve apenas como base fraca. |

---

## 📦 Instalação e Execução

### Pré-requisitos
* Python 3.8+
* Node.js e npm
* PostgreSQL instalado e rodando
* Chave de API do TMDB (The Movie Database)

### 1. Configuração do Backend

Clone o repositório e configure o ambiente:

```bash
# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale as dependências
pip install fastapi uvicorn requests psycopg2-binary networkx python-dotenv