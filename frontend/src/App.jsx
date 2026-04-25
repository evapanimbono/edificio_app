import { useState, useEffect } from 'react'
import Login from './Login'
import Layout from './Layout'
import './App.css'

function App() {
  // 1. Aquí están todos tus useState
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'))
  const [edificios, setEdificios] = useState([])
  const [apartamentos, setApartamentos] = useState([])
  const [vistaActual, setVistaActual] = useState('edificios');
  const [aptoSeleccionado, setAptoSeleccionado] = useState(null);
  const [userRole, setUserRole] = useState(null); // Empezamos en null para saber que está cargando
  const [userData, setUserData] = useState(null); // Guardaremos el objeto completo del perfil

  // 2. Aquí están tus funciones como verDetalleApto...
  const verDetalleApto = (id) => {
    const token = localStorage.getItem('access_token');
    fetch(`http://localhost:8000/api/edificios/apartamentos/detalle/${id}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => {
      if (res.status === 401) { handleLogout(); throw new Error("Sesión expirada"); }
      return res.json();
    })
    .then(data => setAptoSeleccionado(data))
    .catch(err => console.error("Error fatal:", err));
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
  }

  // 3. Aquí están todos tus useEffect (el del perfil, edificios y apartamentos)
  useEffect(() => {
    if (isLoggedIn) {
      const token = localStorage.getItem('access_token');
      
      // Llamamos a tu URL de perfil propio
      fetch('http://localhost:8000/api/usuarios/perfil/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => {
        if (res.status === 401) throw new Error("Sesión expirada");
        return res.json();
      })
      .then(data => {
        setUserData(data);
        // Aquí mapeamos tu 'tipo_usuario' de Django al estado de React
        // Si eres superuser, puedes forzar 'admin' o usar el tipo que devuelve Django
        setUserRole(data.tipo_usuario); 
        console.log("Bienvenido:", data.username, "Rol:", data.tipo_usuario);
      })
      .catch(err => {
        console.error("Error identificando perfil:", err);
        handleLogout();
      });
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (isLoggedIn && userRole) { // Agregamos userRole aquí también
      const token = localStorage.getItem('access_token');
      fetch('http://localhost:8000/api/edificios/', { 
        headers: { 'Authorization': `Bearer ${token}` } 
      })
      .then(res => res.json())
      .then(data => setEdificios(data))
      .catch(err => console.error(err));
    }
  }, [isLoggedIn, userRole]);

  useEffect(() => {
    // Solo disparamos la petición si hay login Y ya sabemos el rol del usuario
    if (isLoggedIn && userRole) { 
      const token = localStorage.getItem('access_token');
      fetch('http://localhost:8000/api/edificios/apartamentos/', { 
        headers: { 'Authorization': `Bearer ${token}` } 
      })
      .then(res => res.json())
      .then(data => {
        console.log("Apartamentos cargados:", data);
        setApartamentos(data);
      })
      .catch(err => console.error(err));
    }
  }, [isLoggedIn, userRole]); // <-- IMPORTANTE: Agregamos userRole aquí

  // GUARDIA 1: ¿Está logueado?
  // Si no lo está, lo mandamos al Login y la ejecución se detiene aquí.
  if (!isLoggedIn) return <Login onLoginSuccess={() => setIsLoggedIn(true)} />

  // GUARDIA 2: ¿Ya sabemos quién es (su rol)?
  // Si está logueado pero la API aún no nos dice si es admin o arrendatario,
  // mostramos la carga y la ejecución se detiene aquí.
  if (userRole === null) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'sans-serif' }}>
        <p>Cargando tu perfil...</p>
      </div>
    );
  }

  // SI PASÓ LOS DOS GUARDIAS:
  // Ahora sí, mostramos la App completa.
  return (
    <Layout onLogout={handleLogout} setVistaActual={setVistaActual} vistaActual={vistaActual} userRole={userRole}>
      
      {/* --- INICIO LÓGICA POR ROL --- */}
      {userRole === 'arrendatario' ? (
        <>
          {/* VISTA INICIO / APARTAMENTOS (Para el arrendatario es su hogar) */}
          {vistaActual === 'apartamentos' && (
            <div style={welcomeCardStyle}>
              <h2>👋 ¡Hola, {userData?.nombre_completo || userData?.username}!</h2>
              <p>Aquí tienes la información de tu hogar:</p>
              
              {apartamentos.length > 0 ? (
                <div 
                  onClick={() => verDetalleApto(apartamentos[0].id)} 
                  style={{...cardStyle, borderLeft: '5px solid #3b82f6', cursor: 'pointer'}}
                >
                  <h3>Apto {apartamentos[0].numero_apartamento}</h3>
                  <p>{apartamentos[0].edificio_nombre}</p>
                </div>
              ) : (
                <p>No tienes un apartamento asignado todavía.</p>
              )}
            </div>
          )}

          {/* VISTA EDIFICIOS (Información del edificio donde vive) */}
          {vistaActual === 'edificios' && (
            <>
              <h3 style={{ marginBottom: '1.5rem', color: '#334155' }}>Mi Edificio</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {edificios.map(e => (
                  <div key={e.id} style={cardStyle}>
                    <div style={{ fontWeight: 'bold' }}>{e.nombre}</div>
                    <div style={{ color: '#64748b' }}>📍 {e.direccion}</div>
                    {/* Aquí el diseño será 100% idéntico al del Arrendador */}
                  </div>
                ))}
                {edificios.length === 0 && <p>No tienes un edificio asignado.</p>}
              </div>
            </>
          )}
        </>
      ) : (

        /* VISTA ADMIN/ARRENDADOR */
        <>
          {vistaActual === 'edificios' && (
            <>
              <h3 style={{ marginBottom: '1.5rem', color: '#334155' }}>Tus Edificios</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {edificios.map(e => (
                  <div key={e.id} style={cardStyle}>
                    <div style={{ fontWeight: 'bold' }}>{e.nombre}</div>
                    <div style={{ color: '#64748b' }}>📍 {e.direccion}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {vistaActual === 'apartamentos' && (
            <>
              <h3 style={{ marginBottom: '1.5rem', color: '#334155' }}>Lista de Apartamentos</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {apartamentos.map(a => {
                  let colores = a.estado === 'activo' ? { bg: '#dcfce7', text: '#166534' } : { bg: '#fee2e2', text: '#991b1b' };
                  return (
                    <div key={a.id} style={{ ...cardStyle, cursor: 'pointer' }} onClick={() => verDetalleApto(a.id)}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>Apto: {a.numero_apartamento}</div>
                          <div style={{ color: '#64748b', fontSize: '0.85rem' }}>{a.edificio_nombre} • Piso {a.piso}</div>
                        </div>
                        <span style={{ backgroundColor: colores.bg, color: colores.text, padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 'bold' }}>
                          {a.estado}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '15px', borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                        <span>🛏️ {a.habitaciones}</span> <span>🚿 {a.banos}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </>
      )}
      {/* --- FIN LÓGICA POR ROL --- */}

      {/* MODAL DE DETALLE (Para ambos roles) */}
      {aptoSeleccionado && (
        <div style={modalStyles.overlay}>
          <div style={modalStyles.content}>
                       
            <div style={{ borderBottom: '2px solid #f1f5f9', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, color: '#1e293b' }}>Apto {aptoSeleccionado.numero_apartamento}</h2>
              <span style={{ color: '#64748b', fontSize: '0.9rem' }}>{aptoSeleccionado.edificio_nombre}</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Piso</label>
                <div style={{ fontWeight: '500' }}>{aptoSeleccionado.piso || 'N/A'}</div>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Estado</label>
                <div style={{ fontWeight: '500' }}>{aptoSeleccionado.estado}</div>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Habitaciones</label>
                <div style={{ fontWeight: '500' }}>🛏️ {aptoSeleccionado.habitaciones}</div>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Baños</label>
                <div style={{ fontWeight: '500' }}>🚿 {aptoSeleccionado.banos}</div>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Descripción</label>
              <p style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', marginTop: '5px', fontSize: '0.9rem' }}>
                {aptoSeleccionado.descripcion || "Sin descripción registrada."}
              </p>
            </div>

            <div style={{ marginTop: '2rem', display: 'flex', gap: '10px' }}>
                <button 
                  style={btnAccionStyle} 
                  onClick={() => alert("Abriendo tu contrato... (Aquí conectaremos la API de contratos)")}
                >
                  {userRole === 'arrendatario' ? 'Ver mi contrato' : 'Ver contratos'}
                </button>
                
                <button 
                  onClick={() => setAptoSeleccionado(null)} 
                  style={{ ...btnAccionStyle, backgroundColor: '#f1f5f9', color: '#475569' }}
                >
                  Cerrar
                </button>
            </div>
          </div>
        </div>
      )}

    </Layout>
  )
}

// --- ESTILOS ---
const cardStyle = { backgroundColor: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0' };
const welcomeCardStyle = { backgroundColor: '#f8fafc', padding: '2rem', borderRadius: '16px', border: '1px solid #e2e8f0', maxWidth: '600px', margin: '0 auto' };
const btnAccionStyle = { marginTop: '1rem', width: '100%', padding: '10px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' };
const modalStyles = {
  overlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  content: { backgroundColor: 'white', padding: '2rem', borderRadius: '20px', width: '90%', maxWidth: '500px', position: 'relative' },
  closeBtn: { position: 'absolute', top: '15px', right: '15px', background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer' },
  btnPrimary: { marginTop: '20px', width: '100%', padding: '10px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }
};

export default App;