import { useState } from 'react'
import axios from 'axios'
import './App.css'

/**
 * Componente principal da aplicação CineGraph.
 * Gerencia o estado da busca, comunica-se com a API Backend e renderiza os resultados.
 */
function App() {
  // Gerenciamento de Estado (State Management)
  const [movieId, setMovieId] = useState('')      // Armazena o input do usuário
  const [results, setResults] = useState([])      // Armazena a lista de filmes retornada pela API
  const [error, setError] = useState(null)        // Gerencia mensagens de erro de requisição

  // Handlers & Lógica de Negócio

  /**
   * Dispara a requisição assíncrona para o backend.
   * Utiliza axios para buscar recomendações baseadas no ID do filme.
   */
  const handleSearch = async () => {
    // Reset de estados para nova busca
    setError(null)
    setResults([])

    // Validação básica de entrada
    if (!movieId) return 

    try {
      console.info(`Iniciando busca para o Movie ID: ${movieId}`)
      
      // Chamada à API (Endpoint de Recomendação)
      const response = await axios.get(`http://127.0.0.1:8000/api/recommend/${movieId}`)
      
      // Atualiza o estado com os dados recebidos (Payload)
      setResults(response.data.results)

    } catch (err) {
      console.error("Falha na requisição:", err)
      setError("Falha ao conectar com o servidor. Verifique se o Backend está ativo.")
    }
  }

  // Renderização (View) 
  return (
    <div className="container">
      <header>
        <h1>🎬 CineGraph</h1>
        <p>Recomendação via Grafos (Diretores, Atores & Keywords)</p>
      </header>
      
      {/* Input de Busca e Controle */}
      <div className="search-box">
        <input 
          type="number" 
          placeholder="Digite o ID (ex: 278)"
          value={movieId}
          onChange={(e) => setMovieId(e.target.value)} // Two-way data binding
        />
        <button onClick={handleSearch}>
          Recomendar
        </button>
      </div>

      {/* Renderização Condicional de Erro */}
      {error && <div className="error-msg">{error}</div>}

      {/* Grid de Resultados */}
      <div className="results-grid">
        {results.map((filme) => (
          <div key={filme.id} className="movie-card">
            
            <img 
              src={filme.poster} 
              alt={filme.titulo} 
              className="poster"
            />
            
            <div className="info">
              <h3>{filme.titulo}</h3>
              <p className="year">{filme.ano}</p>
              
              <div className="score-badge">
                Score: {filme.score_similaridade}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Estado Vazio (Empty State) */}
      {results.length === 0 && !error && (
        <p className="hint">Digite um ID para iniciar a análise de grafos.</p>
      )}
    </div>
  )
}

export default App