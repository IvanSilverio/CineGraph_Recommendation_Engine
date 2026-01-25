import { useState } from 'react'
import axios from 'axios'
import './App.css'

/**
 * Componente Principal da Aplicação CineGraph.
 * Responsável por gerenciar a interação do usuário e conectar com o Backend Python.
 */
function App() {
  // 1. GERENCIAMENTO DE ESTADO (State Management)
  
  // Controle do ID do filme (usado para gerar recomendações)
  const [movieId, setMovieId] = useState('')
  
  // Controle da Busca Textual (Passo 1)
  const [searchQuery, setSearchQuery] = useState('')       // O que o usuário digita
  const [searchResults, setSearchResults] = useState([])   // Resultados da API de busca
  
  // Controle dos Resultados de Recomendação (Passo 2)
  const [recommendations, setRecommendations] = useState([]) // Lista final de filmes recomendados
  
  // Controle de Feedback Visual
  const [error, setError] = useState(null) // Mensagens de erro para o usuário

  // 2. LÓGICA DE NEGÓCIO (API Calls & Handlers)

  /**
   * Busca filmes pelo nome no banco de dados.
   * Conecta com o endpoint: GET /api/search
   */
  const handleSearchByName = async () => {
    // Evita requisições vazias desnecessárias
    if (!searchQuery) return

    try {
      // Faz a requisição assíncrona ao servidor Python (FastAPI)
      const response = await axios.get(`http://127.0.0.1:8000/api/search?query=${searchQuery}`)
      
      // Atualiza a lista de sugestões com os dados vindos do banco
      setSearchResults(response.data.results)
      setError(null) // Limpa erros antigos se der certo
    } catch (err) {
      console.error("Erro na busca:", err)
      setError("Erro ao buscar filmes. Verifique se o servidor está rodando.")
    }
  }

  /**
   * UX (User Experience): Ação ao clicar em um filme da lista de busca.
   * Preenche o campo de ID automaticamente e limpa a interface de busca.
   * @param {number} id - O ID do filme selecionado
   */
  const selectMovie = (id) => {
    setMovieId(id)       // Transfere o ID para o estado principal
    setSearchResults([]) // Esconde a lista de resultados (limpeza visual)
    setSearchQuery('')   // Limpa o campo de texto
  }

  /**
   * Core Feature: Solicita recomendações baseadas no Grafo.
   * Conecta com o endpoint: GET /api/recommend/{id}
   */
  const handleRecommend = async () => {
    // Reseta estados anteriores para dar feedback de "novo carregamento"
    setError(null)
    setRecommendations([])

    if (!movieId) return 

    try {
      console.info(`Iniciando algoritmo para o ID: ${movieId}`)
      
      // Chama o algoritmo de grafos no Python
      const response = await axios.get(`http://127.0.0.1:8000/api/recommend/${movieId}`)
      
      // O Python já devolve os dados enriquecidos (Título, Poster, Score)
      setRecommendations(response.data.results)
    } catch (err) {
      console.error("Erro na recomendação:", err)
      setError("Erro ao conectar com o servidor. O grafo foi carregado?")
    }
  }

  // 3. INTERFACE DO USUÁRIO (JSX / Render)
  return (
    <div className="container">
      {/* Cabeçalho */}
      <header>
        <h1>🎬 CineGraph</h1>
        <p>Encontre o ID pelo nome e descubra novas conexões via Teoria dos Grafos.</p>
      </header>
      
      {/* --- SEÇÃO 1: BUSCA POR NOME --- */}
      <div className="search-section" style={{marginBottom: '40px', padding: '20px', border: '1px solid #333', borderRadius: '10px'}}>
        <h3>Não sabe o ID? Busque o filme:</h3>
        
        <div className="search-box">
          <input 
            type="text" 
            placeholder="Digite o nome (ex: Batman)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            // Permite buscar apertando "Enter"
            onKeyDown={(e) => e.key === 'Enter' && handleSearchByName()}
          />
          <button onClick={handleSearchByName} style={{backgroundColor: '#444'}}>
            🔍 Buscar
          </button>
        </div>

        {/* Renderização Condicional: Só mostra a lista se houver resultados */}
        {searchResults.length > 0 && (
          <div className="search-results-list" style={{display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center', marginTop: '10px'}}>
            {searchResults.map((filme) => (
              <div 
                key={filme.id} 
                onClick={() => selectMovie(filme.id)}
                // Estilos inline para prototipagem rápida (Card clicável)
                style={{
                  background: '#2a2a2a', 
                  padding: '10px', 
                  borderRadius: '5px', 
                  cursor: 'pointer',
                  border: '1px solid #555',
                  minWidth: '150px'
                }}
              >
                <strong>{filme.titulo}</strong> <br/>
                <small>ID: {filme.id} | Ano: {filme.ano}</small>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SEÇÃO 2: RECOMENDAÇÃO */}
      <div className="recommendation-section">
        <h3>Gerar Recomendações</h3>
        <div className="search-box">
          <input 
            type="number" 
            placeholder="ID do Filme"
            value={movieId}
            onChange={(e) => setMovieId(e.target.value)}
          />
          <button onClick={handleRecommend}>
            ✨ Recomendar
          </button>
        </div>
      </div>

      {/* Exibição de Erros (se houver) */}
      {error && <div className="error-msg">{error}</div>}

      {/* --- SEÇÃO 3: GRID DE RESULTADOS (Cards) --- */}
      <div className="results-grid">
        {recommendations.map((filme) => (
          <div key={filme.id} className="movie-card">
            {/* O backend envia a URL completa da imagem ou um placeholder */}
            <img src={filme.poster} alt={filme.titulo} className="poster"/>
            
            <div className="info">
              <h3>{filme.titulo}</h3>
              <p className="year">{filme.ano}</p>
              
              {/* Exibe o peso da conexão calculado pelo Grafo */}
              <div className="score-badge">Score: {filme.score_similaridade}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App