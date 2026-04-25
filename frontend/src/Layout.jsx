import React from 'react';
import { 
  Building2, 
  Home, 
  LayoutDashboard, 
  Wallet, 
  Bell, 
  LogOut,
  ClipboardList
} from 'lucide-react';

const Layout = ({ children, onLogout, setVistaActual, vistaActual, userRole }) => {
  
  // Definimos qué opciones existen
  const allMenuItems = [
    { icon: <Home size={20} />, label: 'Inicio', id: 'inicio', roles: ['admin', 'arrendador', 'arrendatario'] },
    
    { 
      icon: <Building2 size={20} />, 
      // Si es arrendatario, habilitamos 'edificios' pero con nombre singular
      label: userRole === 'arrendatario' ? 'Mi Edificio' : 'Edificios', 
      id: 'edificios', 
      roles: ['admin', 'arrendador', 'arrendatario'] // <-- Agregué 'arrendatario' aquí para que pueda verlo
    },
    
    { 
      icon: <LayoutDashboard size={20} />, 
      label: userRole === 'arrendatario' ? 'Mi Apartamento' : 'Apartamentos', 
      id: 'apartamentos', 
      roles: ['admin', 'arrendador', 'arrendatario'] 
    },
    
    { icon: <Wallet size={20} />, label: 'Mis Cuentas', id: 'cuentas', roles: ['admin', 'arrendador', 'arrendatario'] },
    { icon: <ClipboardList size={20} />, label: 'Encuestas', id: 'encuestas', roles: ['admin', 'arrendador', 'arrendatario'] },
    { icon: <Bell size={20} />, label: 'Notificaciones', id: 'notificaciones', roles: ['admin', 'arrendador', 'arrendatario'] },
  ];

  // Filtramos el menú: Solo mostramos lo que el rol del usuario permite
  const filteredMenu = allMenuItems.filter(item => item.roles.includes(userRole));

  return (
    <div style={styles.container}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <Building2 color="#3b82f6" size={32} />
          <span style={styles.logoText}>EdificioApp</span>
        </div>
        
        <nav style={styles.nav}>
          {filteredMenu.map((item) => {
            // Verificamos si este botón es el que está seleccionado actualmente
            const esActivo = vistaActual === item.id;

            return (
                <div 
                    key={item.id} 
                    // Combinamos el estilo base con el estilo de "activo"
                    style={{
                    ...styles.navItem,
                    backgroundColor: esActivo ? '#334155' : 'transparent',
                    color: esActivo ? '#ffffff' : '#94a3b8',
                    }} 
                    // Al hacer clic, ejecutamos la función que recibimos de App.jsx
                    onClick={() => setVistaActual(item.id)}
                >
                    {/* Aquí react decide qué icono poner (el de la casita, el edificio, etc) */}
                    <span style={{ color: esActivo ? '#3b82f6' : 'inherit' }}>
                    {item.icon}
                    </span>
                    <span style={styles.navLabel}>{item.label}</span>
                </div>
            );
          })}
        </nav>

        <div style={styles.footer}>
          <button onClick={onLogout} style={styles.logoutBtn}>
            <LogOut size={20} />
            <span style={styles.navLabel}>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      <main style={styles.main}>
        <header style={styles.topbar}>
          <h2 style={styles.pageTitle}>Sistema de Gestión</h2>
          <div style={styles.userBadge}>Sesión Activa</div>
        </header>
        
        <div style={styles.content}>
          {children}
        </div>
      </main>
    </div>
  );
};

const styles = {
  container: { display: 'flex', height: '100vh', backgroundColor: '#f8fafc', fontFamily: 'system-ui, sans-serif' },
  sidebar: { width: '260px', backgroundColor: '#1e293b', color: 'white', display: 'flex', flexDirection: 'column', padding: '1.5rem' },
  logo: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2.5rem', padding: '0 0.5rem' },
  logoText: { fontSize: '1.25rem', fontWeight: 'bold', letterSpacing: '-0.5px' },
  nav: { flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' },
  navItem: { display: 'flex', alignItems: 'center', gap: '12px', padding: '0.75rem 1rem', borderRadius: '8px', cursor: 'pointer', color: '#94a3b8', transition: 'all 0.2s' },
  navLabel: { fontSize: '0.95rem', fontWeight: '500' },
  footer: { borderTop: '1px solid #334155', paddingTop: '1.5rem' },
  logoutBtn: { display: 'flex', alignItems: 'center', gap: '12px', width: '100%', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', padding: '0.75rem 1rem' },
  main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  topbar: { height: '64px', backgroundColor: 'white', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2rem' },
  pageTitle: { fontSize: '1.1rem', fontWeight: '600', color: '#1e293b' },
  userBadge: { backgroundColor: '#e2e8f0', padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.85rem', fontWeight: '500', color: '#475569' },
  content: { flex: 1, padding: '2rem', overflowY: 'auto' }
};

export default Layout;