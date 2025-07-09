🏢 App: Edificios
Esta app gestiona los edificios y apartamentos dentro del sistema de administración de propiedades. 
Incluye vistas para listar, crear, editar y ver detalles, con permisos diferenciados por tipo de usuario.

📁 Modelos principales
Edificio: contiene nombre, dirección, coordenadas, descripción y fechas.
Apartamento: relacionado a un edificio, con campos como número, piso, habitaciones, baños, estado, etc.

🔐 Permisos y Roles
Vista	                           Superuser	Arrendador	                      Arrendatario
Listar edificios	                   ✅	      ✅	                                🚫
Ver detalle de edificio	               ✅	      ✅	                                ✅
Crear / Editar / Eliminar edificio	   ✅	      🚫	                             🚫
Listar apartamentos	                   ✅	      ✅	                                🚫
Ver detalle de apartamento	           ✅	      ✅	                                ✅ (solo propios)
Crear / Editar apartamento	           ✅	      ✅ (solo en edificios asignados)	🚫

🔧 Vistas disponibles
🏢 Edificios
GET /api/edificios/: lista los edificios disponibles para el usuario autenticado.
GET /api/edificios/<id>/: detalle de un edificio específico.
POST /api/edificios/crear/: crea un edificio (solo superuser).
PATCH /api/edificios/editar/<id>/: actualiza un edificio (solo superuser).
DELETE /api/edificios/eliminar/<id>/: elimina un edificio si no tiene usuarios ni apartamentos asociados (solo superuser).

🏘️ Apartamentos
GET /api/edificios/apartamentos/: lista de apartamentos visibles según permisos.
GET /api/edificios/apartamentos/<id>/: detalle de un apartamento.
POST /api/edificios/apartamentos/crear/: crear un apartamento (superuser o arrendador con edificio asignado).
PATCH /api/edificios/apartamentos/editar/<id>/: editar apartamento (según permisos).

🔎 Filtros disponibles
🏢 Edificios (GET /api/edificios/)
Campo	         Tipo	Descripción
nombre	         Texto	Buscar por nombre (parcial)
created_at__gte	 Fecha	Fecha de creación desde
created_at__lte	 Fecha	Fecha de creación hasta

🏘️ Apartamentos (GET /api/edificios/apartamentos/)
Campo	            Tipo	Descripción
edificio	        Número	ID del edificio
edificio_nombr      Texto	Buscar por nombre del edificio
estado	            Texto	Estado del apartamento (disponible, ocupado, etc.)
habitaciones_min	Número	Mínimo de habitaciones
banos_min	        Número	Mínimo de baños
piso	            Número	Número exacto de piso
numero_apartamento	Texto	Buscar por número del apartamento (parcial)

🧠 Validaciones importantes
No se puede crear un apartamento duplicado (mismo número en un mismo edificio).
No se puede eliminar un edificio que tenga usuarios asignados o apartamentos existentes.
Solo se puede crear o editar apartamentos en edificios donde el arrendador esté asignado.