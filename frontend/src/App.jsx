import { useState, useEffect } from 'react'
import Login from './Login'
import Layout from './Layout'
import './App.css'

function App() {
  // 1. Aquí están todos tus useState
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'))

  const [userRole, setUserRole] = useState(null); // Empezamos en null para saber que está cargando
  const [userData, setUserData] = useState(null); // Guardaremos el objeto completo del perfil
  
  const [edificios, setEdificios] = useState([])
  const [vistaActual, setVistaActual] = useState('edificios');

  const [apartamentos, setApartamentos] = useState([])  
  const [aptoSeleccionado, setAptoSeleccionado] = useState(null);
  
  const [datosContrato, setDatosContrato] = useState(null);
  const [cargandoContrato, setCargandoContrato] = useState(false);
  const [contratosApto, setContratosApto] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [contratoSeleccionado, setContratoSeleccionado] = useState(null);
  const [aptoIdParaContrato, setAptoIdParaContrato] = useState(null);

  const [arrendatarios, setArrendatarios] = useState([])  

  // 2. Aquí están tus funciones como verDetalleApto...  
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
  }

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

  const obtenerInfoContrato = async () => {
    setCargandoContrato(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/contratos/mi-contrato/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDatosContrato(data);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setCargandoContrato(false);
    }
  };

  const verDetalleContrato = () => {
    // 1. Pedir los datos a la API (Llamamos a la función anterior)
    obtenerInfoContrato(); 
    
    // 2. Cerrar el modal para que no estorbe
    setAptoSeleccionado(null); 
    
    // 3. Cambiar la vista de la app a la nueva pantalla
    setVistaActual('mi-contrato'); 
  };

  const verHistorialContratosApto = async (idManual = null) => {
    // 1. BLINDAJE: Si idManual es un evento de React (tiene la propiedad target), lo ignoramos
    const idReal = (idManual && idManual.target) ? null : idManual;

    // 2. Determinamos el ID final
    let idFinal = null;
    if (idReal) {
      idFinal = idReal;
    } else if (aptoSeleccionado) {
      idFinal = aptoSeleccionado.id;
    } else {
      idFinal = aptoIdParaContrato;
    }

    // Si sigue siendo un objeto o nulo, no podemos continuar
    if (!idFinal || typeof idFinal === 'object') {
      console.error("ID no válido detectado:", idFinal);
      return;
    }

    // 3. Guardar info para el Header
    if (aptoSeleccionado) {
      window.aptoSeleccionadoLocal = {
        numero_apartamento: aptoSeleccionado.numero_apartamento,
        edificio_nombre: aptoSeleccionado.edificio_nombre
      };
      setAptoIdParaContrato(idFinal);
    }

    setCargandoHistorial(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/contratos/?apartamento=${idFinal}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setContratosApto(data); 
        setAptoSeleccionado(null); 
        setVistaActual('historial-contratos');
      }
    } catch (error) {
      console.error("Error de red:", error);
    } finally {
      setCargandoHistorial(false);
    }
  };

  const verDetalleEspecificoContrato = async (id) => {
    try {
      const token = localStorage.getItem('access_token');
      // Llamamos a tu vista de detalle de Django
      const response = await fetch(`http://localhost:8000/api/contratos/${id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setContratoSeleccionado(data); // Guardamos el contrato completo
        setVistaActual('detalle-contrato-arrendador'); // Cambiamos a la nueva pantalla
      }
    } catch (error) {
      console.error("Error al cargar el detalle del contrato:", error);
    }
  };

  const prepararNuevoContrato = async (idApartamento) => {
    const token = localStorage.getItem('access_token');
    
    // Guardamos el ID del apartamento para usarlo luego en el POST
    setAptoIdParaContrato(idApartamento);

    try {
      const response = await fetch('http://localhost:8000/api/usuarios/arrendador/arrendatarios/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setArrendatarios(data);
        setVistaActual('crear-contrato');
      }
    } catch (error) {
      console.error("Error al cargar arrendatarios:", error);
    }
  };

  const fechaHoy = new Date().toISOString().split('T')[0];

  const formatearFechaEsp = (fechaStr) => {
    if (!fechaStr || fechaStr === 'Presente') return fechaStr;
    // Dividimos la cadena "2026-04-29" por los guiones
    const [año, mes, dia] = fechaStr.split('-');
    // Devolvemos el formato que queremos
    return `${dia}/${mes}/${año}`;
  };

  const manejarGuardarContrato = async (formData) => {
    const token = localStorage.getItem('access_token');
    
    // Nos aseguramos de que esto sea un ID (número) y no el objeto completo
    const idLimpio = typeof aptoIdParaContrato === 'object' ? aptoIdParaContrato.id : aptoIdParaContrato;

    try {
      const response = await fetch('http://localhost:8000/api/contratos/crear/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData 
      });

      if (response.ok) {
        // Pasamos el ID limpio para refrescar
        await verHistorialContratosApto(idLimpio);
      } else {
        const errorData = await response.json();
        alert("Error: " + JSON.stringify(errorData));
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const manejarCerrarModal = () => {
    setAptoSeleccionado(null); // Cierra el modal
    setDatosContrato(null);    // Limpia la info del contrato para que no aparezca abierta la próxima vez
  };

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
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>Apto: {a.numero_apartamento}</div>
                          <div style={{ color: '#64748b', fontSize: '0.85rem' }}>{a.edificio_nombre} • Piso {a.piso}</div>
                        </div>
                        <span style={{ backgroundColor: colores.bg, color: colores.text, padding: '4px 10px',marginTop: '4px', borderRadius: '8px', fontSize: '0.75rem', fontWeight: 'bold' , display: 'inline-block', width: 'fit-content', textAlign: 'center' }}>
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

        {/* --- PANTALLA DE DETALLE DEL CONTRATO --- */}
        {vistaActual === 'mi-contrato' && (
          <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <header style={{ marginBottom: '2rem' }}>
              <h2 style={{ color: '#1e293b', fontSize: '1.8rem' }}>Mi Contrato de Arrendamiento</h2>
              <p style={{ color: '#64748b' }}>Consulta tus condiciones, montos y fechas de pago.</p>
            </header>

            {!datosContrato ? (
              <div style={{ textAlign: 'center', padding: '3rem', backgroundColor: '#f8fafc', borderRadius: '12px' }}>
                <p style={{ color: '#94a3b8' }}>Cargando información del contrato...</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '1.5rem' }}>
                {/* Tarjeta de Resumen Financiero */}
                <div style={{ backgroundColor: '#ffffff', padding: '2rem', borderRadius: '12px', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
                    <div>
                      <label style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Monto Mensual</label>
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#0f172a', marginTop: '5px' }}>
                        ${datosContrato.monto_usd_mensual} USD
                      </div>
                    </div>
                    <div>
                      <label style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Día de Pago</label>
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#0f172a', marginTop: '5px' }}>
                        Día {datosContrato.fecha_pago_mensual}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detalles de Vigencia */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div style={{ backgroundColor: '#f8fafc', padding: '1.5rem', borderRadius: '12px' }}>
                    <label style={{ color: '#64748b', fontSize: '0.85rem' }}>Fecha de Inicio</label>
                    <div style={{ fontWeight: '600', marginTop: '5px' }}>{formatearFechaEsp(datosContrato.fecha_inicio)}</div>
                  </div>
                  <div style={{ backgroundColor: '#f8fafc', padding: '1.5rem', borderRadius: '12px' }}>
                    <label style={{ color: '#64748b', fontSize: '0.85rem' }}>Vencimiento</label>
                    <div style={{ fontWeight: '600', marginTop: '5px' }}>{formatearFechaEsp(datosContrato.fecha_fin) || 'Indefinido'}</div>
                  </div>
                </div>

                {/* Botón de Descarga si existe PDF */}
                {datosContrato.archivo_contrato_pdf && (
                  <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                    <a 
                      href={datosContrato.archivo_contrato_pdf} 
                      target="_blank" 
                      rel="noreferrer"
                      style={{
                        display: 'inline-block',
                        padding: '12px 24px',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        fontWeight: '600',
                        transition: 'background-color 0.2s'
                      }}
                    >
                      📥 Descargar Contrato en PDF
                    </a>
                  </div>
                )}

                <button 
                  onClick={() => setVistaActual('apartamentos')}
                  style={{
                    marginTop: '1rem',
                    background: 'none',
                    border: 'none',
                    color: '#64748b',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    textDecoration: 'underline'
                  }}
                >
                  Volver a mis apartamentos
                </button>
              </div>
            )}
          </div>
        )}

        {/* --- PANTALLA DE HISTORIAL DE CONTRATOS (Para el Arrendador) --- */}
        {vistaActual === 'historial-contratos' && (() => {
          // 1. Buscamos si hay algún contrato activo para bloquear/desbloquear el botón de "Nuevo"
          const tieneContratoActivo = contratosApto.some(c => c.activo === true);

          // 2. Prioridad de datos para el Header
          const aptoData = contratosApto.length > 0 ? contratosApto[0] : null;
          
          const numeroMostrado = aptoData 
            ? aptoData.apartamento_numero 
            : (window.aptoSeleccionadoLocal?.numero_apartamento || "");

          const edificioMostrado = aptoData 
            ? aptoData.edificio_nombre 
            : (window.aptoSeleccionadoLocal?.edificio_nombre || "Edificio");

          return (
            <div style={{ padding: '20px', maxWidth: '1100px', margin: '0 auto' }}>
              
              {/* HEADER */}
              <header style={{ 
                marginBottom: '2.5rem', 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                backgroundColor: 'white', 
                padding: '1.5rem', 
                borderRadius: '12px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)' 
              }}>
                <div>
                  <h2 style={{ color: '#1e293b', fontSize: '1.8rem', margin: '0 0 5px 0' }}>
                    Historial: Apto {numeroMostrado}
                  </h2>
                  <span style={{ color: '#475569', fontSize: '1.1rem', fontWeight: '500', display: 'block', marginBottom: '5px' }}>
                    {edificioMostrado}
                  </span>
                  <p style={{ color: '#64748b', margin: 0, fontSize: '0.95rem' }}>Registro histórico de arrendamientos.</p>
                </div>

                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                  <button 
                    disabled={tieneContratoActivo}
                    onClick={() => {
                      const idApto = aptoData ? aptoData.apartamento : aptoIdParaContrato;
                      prepararNuevoContrato(idApto);
                    }}
                    style={{ 
                      padding: '10px 20px', 
                      backgroundColor: tieneContratoActivo ? '#f1f5f9' : '#16a34a', 
                      color: tieneContratoActivo ? '#94a3b8' : 'white', 
                      border: tieneContratoActivo ? '1px solid #e2e8f0' : 'none', 
                      borderRadius: '8px', 
                      cursor: tieneContratoActivo ? 'not-allowed' : 'pointer', 
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span>+</span> Nuevo Contrato
                  </button>

                  <button 
                    onClick={() => setVistaActual('apartamentos')}
                    style={{ 
                      padding: '10px 20px', 
                      backgroundColor: '#f8fafc', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px', 
                      cursor: 'pointer', 
                      color: '#475569', 
                      fontWeight: 'bold' 
                    }}
                  >
                    ← Volver
                  </button>
                </div>
              </header>

              {/* CONTENIDO: Tabla o Mensaje de "Sin Contratos" */}
              {contratosApto.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '4rem 2rem', 
                  backgroundColor: 'white', 
                  borderRadius: '12px', 
                  border: '1px solid #e2e8f0',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>📄</div>
                  <h3 style={{ color: '#1e293b', marginBottom: '0.5rem', fontSize: '1.4rem' }}>No hay contratos registrados</h3>
                  <p style={{ color: '#64748b', margin: 0, fontSize: '1rem' }}>
                    Este apartamento aún no tiene historial. Usa el botón <strong>"+ Nuevo Contrato"</strong> para empezar.
                  </p>
                </div>
              ) : (
                <div style={{ backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                      <tr>
                        <th style={{ padding: '15px', color: '#64748b', fontSize: '0.85rem' }}>Inquilino</th>
                        <th style={{ padding: '15px', color: '#64748b', fontSize: '0.85rem' }}>Inicio / Fin</th>
                        <th style={{ padding: '15px', color: '#64748b', fontSize: '0.85rem' }}>Monto</th>
                        <th style={{ padding: '15px', color: '#64748b', fontSize: '0.85rem' }}>Estado</th>
                        <th style={{ padding: '15px', color: '#64748b', fontSize: '0.85rem' }}>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contratosApto.map((contrato) => (
                        <tr key={contrato.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '15px', fontWeight: '500' }}>{contrato.arrendatario_nombre}</td>
                          
                          <td style={{ padding: '15px', color: '#475569', fontSize: '0.9rem' }}>
                            {formatearFechaEsp(contrato.fecha_inicio)} a {contrato.fecha_fin ? formatearFechaEsp(contrato.fecha_fin) : 'Presente'}
                          </td>

                          <td style={{ padding: '15px', fontWeight: 'bold', color: '#1e293b' }}>
                            ${contrato.monto_usd_mensual}
                          </td>

                          <td style={{ padding: '15px' }}>
                            <span style={{ 
                              padding: '4px 12px', 
                              borderRadius: '20px', 
                              fontSize: '0.75rem',
                              backgroundColor: contrato.activo ? '#dcfce7' : '#f1f5f9',
                              color: contrato.activo ? '#166534' : '#64748b',
                              fontWeight: 'bold',
                              textTransform: 'uppercase'
                            }}>
                              {contrato.activo ? 'ACTIVO' : 'FINALIZADO'}
                            </span>
                          </td>

                          <td style={{ padding: '15px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                              {/* Botón de Ver PDF mejorado */}
                              {contrato.archivo_contrato_pdf ? (
                                <button 
                                  onClick={() => {
                                    const servidor = "http://localhost:8000";
                                    let rutaArchivo = contrato.archivo_contrato_pdf;

                                    // Si la ruta no empieza con http ni con /, le agregamos la base de media
                                    let urlFinal;
                                    if (rutaArchivo.startsWith('http')) {
                                      urlFinal = rutaArchivo;
                                    } else {
                                      // Nos aseguramos de que empiece con / y contenga /media/
                                      const prefijo = rutaArchivo.startsWith('/') ? "" : "/";
                                      const contieneMedia = rutaArchivo.includes('/media/');
                                      
                                      urlFinal = contieneMedia 
                                        ? `${servidor}${prefijo}${rutaArchivo}`
                                        : `${servidor}/media/${prefijo}${rutaArchivo}`;
                                    }

                                    console.log("Intentando abrir:", urlFinal); // Para que verifiques en consola
                                    
                                    const nuevaVentana = window.open(urlFinal, '_blank', 'noopener,noreferrer');
                                  }}
                                  style={{ 
                                    color: '#16a34a', 
                                    border: 'none', 
                                    background: 'none', 
                                    padding: 0, 
                                    textAlign: 'left', 
                                    cursor: 'pointer', 
                                    fontSize: '0.85rem', 
                                    fontWeight: '600',
                                    textDecoration: 'underline' 
                                  }}
                                >
                                  📄 Ver PDF
                                </button>
                              ) : (
                                <span style={{ color: '#94a3b8', fontSize: '0.8rem', fontStyle: 'italic' }}>
                                  Sin archivo
                                </span>
                              )}

                              {/* Botón Ver Detalle (se mantiene igual) */}
                              <button 
                                onClick={() => verDetalleEspecificoContrato(contrato.id)}
                                style={{ color: '#3b82f6', border: 'none', background: 'none', padding: 0, textAlign: 'left', cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '5px' }}
                              >
                                <span>👁️</span> Ver detalle
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })()}

        {/* --- PANTALLA DE DETALLE ESPECÍFICO (Arrendador) --- */}
        {vistaActual === 'detalle-contrato-arrendador' && contratoSeleccionado && (
          <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <header style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '15px' }}>
              <button 
                onClick={() => setVistaActual('historial-contratos')}
                style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ←
              </button>
              <h2 style={{ margin: 0, color: '#1e293b' }}>Ficha del Contrato #{contratoSeleccionado.id}</h2>
            </header>

            <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0' }}>
              
              {/* SECCIÓN 1: DATOS DEL INQUILINO (Lo nuevo) */}
              <div style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#f8fafc', borderRadius: '10px', borderLeft: '4px solid #3b82f6' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#1e293b', fontSize: '1.1rem' }}>👤 Datos del Inquilino</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Nombre Completo</label>
                    <span style={{ fontWeight: '600' }}>{contratoSeleccionado.arrendatario_nombre}</span>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Correo Electrónico</label>
                    <span style={{ fontWeight: '600' }}>{contratoSeleccionado.arrendatario_email}</span>
                  </div>
                  {/* Si agregaste teléfono en el serializer, muéstralo aquí */}
                  {contratoSeleccionado.arrendatario_telefono && (
                    <div style={{ gridColumn: '1 / -1', marginTop: '5px' }}>
                      <label style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>Teléfono</label>
                      <span style={{ fontWeight: '600' }}>{contratoSeleccionado.arrendatario_telefono}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* SECCIÓN 2: INFORMACIÓN DEL INMUEBLE Y CONTRATO */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <div>
                  <h4 style={{ color: '#64748b', borderBottom: '1px solid #f1f5f9', paddingBottom: '5px', fontSize: '0.9rem' }}>Ubicación</h4>
                  <p><strong>Edificio:</strong> {contratoSeleccionado.edificio_nombre}</p>
                  <p><strong>Apartamento:</strong> {contratoSeleccionado.apartamento_numero}</p>
                </div>

                <div>
                  <h4 style={{ color: '#64748b', borderBottom: '1px solid #f1f5f9', paddingBottom: '5px', fontSize: '0.9rem' }}>Condiciones</h4>
                  <p><strong>Monto:</strong> <span style={{ color: '#16a34a', fontWeight: 'bold' }}>${contratoSeleccionado.monto_usd_mensual} USD</span></p>
                  <p><strong>Día de Pago:</strong> Día {contratoSeleccionado.fecha_pago_mensual}</p>
                </div>
              </div>

              {/* FOOTER: VIGENCIA Y PDF */}
              <div style={{ marginTop: '2rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
                <p style={{ textAlign: 'center', color: '#64748b', fontSize: '0.9rem' }}>
                  Contrato vigente desde el <strong>{formatearFechaEsp(contratoSeleccionado.fecha_inicio)}</strong> hasta <strong>{formatearFechaEsp(contratoSeleccionado.fecha_fin) || 'Vigente'}</strong>.
                </p>
                {contratoSeleccionado.archivo_contrato_pdf && (
                    <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                      <a 
                        href={contratoSeleccionado.archivo_contrato_pdf} 
                        target="_blank" 
                        rel="noreferrer"
                        style={{ display: 'inline-block', padding: '10px 20px', backgroundColor: '#0f172a', color: 'white', borderRadius: '6px', textDecoration: 'none' }}
                      >
                        📥 Descargar Contrato PDF
                      </a>
                    </div>
                )}
              </div>

            </div>
          </div>
        )}

        {vistaActual === 'crear-contrato' && (
          <div style={{ padding: '20px', maxWidth: '700px', margin: '0 auto' }}>
            <header style={{ marginBottom: '2rem' }}>
              <h2 style={{ color: '#1e293b' }}>📝 Crear Nuevo Contrato</h2>
              <p style={{ color: '#64748b' }}>Registra un nuevo contrato para el apartamento seleccionado.</p>
            </header>

            <form 
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                
                // Añadimos datos que no están en los inputs manualmente
                formData.append('apartamento', aptoIdParaContrato);
                formData.append('activo', true);

                // Llamamos a la función de guardado
                manejarGuardarContrato(formData); 
              }}
              style={{ 
                backgroundColor: 'white', 
                padding: '2rem', 
                borderRadius: '12px', 
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                display: 'grid',
                gap: '2rem'
              }}
            >
              {/* Selección de Inquilino */}
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#475569' }}>Inquilino</label>
                <select 
                  name="arrendatario" 
                  required 
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0', backgroundColor: '#fff' }}
                >
                  <option value="">Selecciona un arrendatario...</option>
                  {arrendatarios.map(user => (
                    <option key={user.id} value={user.id}>{user.nombre_completo} ({user.correo})</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '25px' }}>
                {/* Monto Mensual */}
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#475569' }}>Monto Mensual (USD)</label>
                  <input 
                    name="monto_usd_mensual" 
                    type="number" 
                    placeholder="Ej: 500" 
                    required 
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  />
                </div>

                {/* Día de Pago */}
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#475569' }}>Día de cobro (1-31)</label>
                  <input 
                    name="fecha_pago_mensual" 
                    type="number" 
                    min="1" 
                    max="31" 
                    placeholder="Ej: 5" 
                    required 
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '25px' }}>
                {/* Fecha Inicio */}
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#475569' }}>Fecha de Inicio</label>
                  <input 
                    name="fecha_inicio" 
                    type="date" 
                    defaultValue={fechaHoy}
                    required 
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  />
                </div>

                {/* Fecha Fin */}
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#475569' }}>Fecha de Vencimiento</label>
                  <input 
                    name="fecha_fin" 
                    type="date" 
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  />
                </div>
              </div>

              {/* Campo PDF */}
              <div style={{ marginTop: '10px' }}>
                <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', color: '#475569' }}>
                  Documento del Contrato (PDF)
                </label>
                <input 
                  type="file" 
                  accept=".pdf" 
                  name="archivo_contrato_pdf"
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    borderRadius: '8px', 
                    border: '1px dashed #cbd5e1',
                    backgroundColor: '#f8fafc',
                    cursor: 'pointer'
                  }} 
                />
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '5px' }}>
                  Formatos permitidos: Solo PDF. Máximo 5MB.
                </p>
              </div>

              {/* Botones de Acción */}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button 
                  type="submit" 
                  style={{ 
                    flex: 2, 
                    padding: '12px', 
                    backgroundColor: '#16a34a', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    fontWeight: 'bold', 
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#15803d'}
                  onMouseOut={(e) => e.target.style.backgroundColor = '#16a34a'}
                >
                  Guardar Contrato
                </button>
                <button 
                  type="button" 
                  onClick={() => setVistaActual('historial-contratos')}
                  style={{ 
                    flex: 1, 
                    padding: '12px', 
                    backgroundColor: '#f1f5f9', 
                    color: '#475569', 
                    border: 'none', 
                    borderRadius: '8px', 
                    fontWeight: 'bold', 
                    cursor: 'pointer' 
                  }}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}
      
      {/* --- FIN LÓGICA POR ROL --- */}

      {/* MODAL DE DETALLE (Para ambos roles) */}
      {aptoSeleccionado && (
        <div style={modalStyles.overlay}>
          <div style={modalStyles.content}>
            
            {/* CABECERA */}
            <div style={{ borderBottom: '2px solid #f1f5f9', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, color: '#1e293b' }}>Apto {aptoSeleccionado.numero_apartamento}</h2>
              <span style={{ color: '#64748b', fontSize: '0.9rem' }}>{aptoSeleccionado.edificio_nombre}</span>
            </div>

            {/* INFORMACIÓN BÁSICA */}
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

            {/* DESCRIPCIÓN */}
            <div style={{ marginTop: '1.5rem' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8' }}>Descripción</label>
              <p style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', marginTop: '5px', fontSize: '0.9rem' }}>
                {aptoSeleccionado.descripcion || "Sin descripción registrada."}
              </p>
            </div>

            {/* BOTONES DE ACCIÓN */}
            <div style={{ marginTop: '2rem', display: 'flex', gap: '10px' }}>
              
              {/* BOTÓN DINÁMICO: Cambia según el rol */}
              <button 
                style={{ ...btnAccionStyle, backgroundColor: '#3b82f6', color: 'white' }} 
                onClick={userRole === 'arrendatario' 
                  ? () => verDetalleContrato() 
                  : () => verHistorialContratosApto() 
                }
              >
                {userRole === 'arrendatario' ? 'Ver Detalles' : 'Ver Historial de Contratos'}
              </button>
              
              {/* BOTÓN CERRAR: Limpia el apartamento seleccionado */}
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