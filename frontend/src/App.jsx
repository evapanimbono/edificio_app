import { useState } from 'react'
import './App.css'

function App() {
  const [mensaje, setMensaje] = useState("Cargando datos del backend...")

  return (
    <div className="App">
      <header>
        <h1>Gestión de Edificios</h1>
        <p>Panel de Control</p>
      </header>

      <main>
        <div className="card">
          <h2>Estado de la Conexión:</h2>
          <p>{mensaje}</p>
        </div>
      </main>
    </div>
  )
}

export default App