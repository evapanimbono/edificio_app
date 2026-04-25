import { useState } from 'react'

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
        // Guardamos el token en el almacenamiento del navegador
        localStorage.setItem('access_token', data.access)
        localStorage.setItem('refresh_token', data.refresh)
        onLoginSuccess() // Avisamos a App.jsx que entramos
      } else {
        setError('Usuario o contraseña incorrectos')
      }
    } catch (err) {
      setError('Error de conexión con el servidor')
    }
  }

  return (
    <div style={styles.container}>
      <form onSubmit={handleSubmit} style={styles.card}>
        <h2 style={styles.title}>Edificio App</h2>
        <p style={styles.subtitle}>Ingresa tus credenciales</p>
        
        {error && <div style={styles.error}>{error}</div>}

        <input
          type="text"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={styles.input}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
          required
        />
        <button type="submit" style={styles.button}>Entrar</button>
      </form>
    </div>
  )
}

// Estilos básicos y modernos
const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#f0f2f5' },
  card: { padding: '2.5rem', backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)', width: '100%', maxWidth: '400px', textAlign: 'center' },
  title: { margin: '0 0 0.5rem', color: '#1a1a1a', fontSize: '1.8rem' },
  subtitle: { color: '#666', marginBottom: '2rem' },
  input: { width: '100%', padding: '0.8rem', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #ddd', boxSizing: 'border-box' },
  button: { width: '100%', padding: '0.8rem', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  error: { color: '#dc3545', backgroundColor: '#f8d7da', padding: '0.5rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.9rem' }
}

export default Login