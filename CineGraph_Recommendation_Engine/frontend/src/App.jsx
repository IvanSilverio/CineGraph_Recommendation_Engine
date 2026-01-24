import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  // Estados
  const [movieId, setMovieId] = useState('')
  const [searchQuery, setSearchQuery] = useState('') // Texto da busca por nome
  const [searchResults, setSearchResults] = useState([]) // Lista de filmes encontrados pelo nome
  
  const [recommendations, setRecommendations] = useState([]) // Resultado final (Recomendações)
  const [error, setError] = useState(null)

  // 1. Função para buscar o ID pelo Nome
  const handleSearchByName = async () => {
    if (!searchQuery) return
    try {
      // Chama a nova rota que criamos no Python
      const response = await axios.get(`http://127.0.0.1:8000/api/search?query=${searchQuery}`)
      setSearchResults(response.data.results)
      setError(null)
    } catch (err) {
      console.error(err)
      setError("Erro ao buscar filmes.")
    }
  }

  // 2. Função quando clica em um filme da lista
  const selectMovie = (id) => {
    setMovieId(id)       // Preenche o campo de ID automaticamente
    setSearchResults([]) // Limpa a lista de busca para não poluir
    setSearchQuery('')   // Limpa o texto da busca
  }

  // 3. Função de Recomendação
  const handleRecommend = async () => {
    setError(null)
    setRecommendations([])

    if (!movieId) return 

    try {
      console.info(`Buscando recomendações para ID: ${movieId}`)
      const response = await axios.get(`http://127.0.0.1:8000/api/recommend/${movieId}`)
      setRecommendations(response.data.results)
    } catch (err) {
      console.error(err)
      setError("Erro ao conectar com o servidor.")
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🎬 CineGraph</h1>
        <p>Encontre o ID pelo nome e descubra novas conexões.</p>
      </header>
      
      {/* Busca por nome */}
      <div className="search-section" style={{marginBottom: '40px', padding: '20px', border: '1px solid #333', borderRadius: '10px'}}>
        <h3>1º Passo: Não sabe o ID? Busque o filme:</h3>
        <div className="search-box">
          <input 
            type="text" 
            placeholder="Digite o nome (ex: Batman)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchByName()}
          />
          <button onClick={handleSearchByName} style={{backgroundColor: '#444'}}>
            🔍 Buscar
          </button>
        </div>

        {/* Lista de Filmes Encontrados */}
        {searchResults.length > 0 && (
          <div className="search-results-list" style={{display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center'}}>
            {searchResults.map((filme) => (
              <div 
                key={filme.id} 
                onClick={() => selectMovie(filme.id)}
                style={{
                  background: '#2a2a2a', 
                  padding: '10px', 
                  borderRadius: '5px', 
                  cursor: 'pointer',
                  border: '1px solid #555'
                }}
              >
                <strong>{filme.titulo}</strong> <br/>
                <small>ID: {filme.id} | Ano: {filme.ano}</small>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recomendação */}
      <div className="recommendation-section">
        <h3>2º Passo: Gerar Recomendações</h3>
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

      {error && <div className="error-msg">{error}</div>}

      {/* Grid de Resultados Finais */}
      <div className="results-grid">
        {recommendations.map((filme) => (
          <div key={filme.id} className="movie-card">
            <img src={filme.poster} alt={filme.titulo} className="poster"/>
            <div className="info">
              <h3>{filme.titulo}</h3>
              <p className="year">{filme.ano}</p>
              <div className="score-badge">Score: {filme.score_similaridade}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App