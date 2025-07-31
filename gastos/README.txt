📊 App Gastos
Esta app gestiona los Gastos Extra relacionados con apartamentos en edificios, con control de acceso según el tipo de usuario 
(superuser, arrendador, arrendatario), y acciones como crear, listar, actualizar, anular, eliminar y consultar detalles de gastos extra.

🗂️ Modelo principal
GastoExtra con campos relevantes:
apartamento 🏢: FK al apartamento asociado
descripcion 📝
monto_usd 💵
saldo_pendiente 💰
fecha_generacion 📅
fecha_vencimiento ⏰ (opcional)
estado (pendiente, pagado, atrasado) ⏳✔️❌
comentario_anulacion 📝❌
timestamps: created_at, updated_at

📄 Serializers
GastoExtraSerializer 🧾: para listar y mostrar detalles completos.
GastoExtraCreateSerializer ➕: para crear gastos extra con validaciones, incluyendo validación de apartamento por número y contrato activo.
GastoExtraUpdateSerializer ✏️: para actualizar descripción, monto y vencimiento con validaciones.
GastoExtraDetailSerializer 🔍: (similar a GastoExtraSerializer con validaciones adicionales).

🔍 Vistas disponibles
ListaGastosExtraAPIView (GET)
Todos los usuarios autenticados pueden listar.
Los arrendatarios ven solo gastos asociados a sus apartamentos con contratos activos.
Arrendadores y superusuarios ven gastos de apartamentos en edificios que administran.
Restricción: arrendatarios no pueden filtrar por apartamento ni fechas de generación.

CrearGastoExtraAPIView (POST)
Solo superuser y arrendadores pueden crear gastos.
Se registra acción en log.

DetalleGastoExtraAPIView (GET)
Permisos según tipo de usuario:
Arrendatarios sólo gastos asociados a sus contratos activos.
Arrendadores y superusuarios sólo gastos en edificios que administran.

ActualizarGastoExtraAPIView (PATCH/PUT)
Solo superuser y arrendadores.
No se puede actualizar un gasto con pagos validados o pendientes asociados.
Actualiza estado según fecha vencimiento.
Registra acción en log.

AnularGastoExtraAPIView (UPDATE)
Solo superuser y arrendadores.
No se puede anular gasto pagado ni con pagos validados o pendientes asociados.
Registra acción en log.

EliminarGastoExtraAPIView (DELETE)
Solo superuser y arrendadores.
No se puede eliminar gasto que no haya sido anulado antes.
Registra acción en log.

🔐 Permisos y validaciones
Arrendatarios: sólo consulta gastos de sus apartamentos, con restricciones de filtro.
Arrendadores: gestionan gastos en edificios asignados.
Validación para que monto sea mayor a cero.
Validación para apartamento válido con contrato activo al crear.

No se permite eliminar o modificar gastos que ya tienen pagos validados o pendientes asociados o estén pagados.

⚙️ Filtros disponibles (con django-filters)
Para todos los usuarios:
estado (pendiente, pagado, atrasado)
monto_usd_min y monto_usd_max (rango de monto)
fecha_vencimiento_desde y fecha_vencimiento_hasta (rango fechas vencimiento)

Solo para arrendadores y superusuarios:
apartamento (filtrar por apartamento ID)
fecha_generacion_desde y fecha_generacion_hasta (rango fechas de creación)

🔗 URLs principales
Método	            Ruta	               Descripción	                Permisos
GET	               /	                   Listar gastos extra	        Todos usuarios autenticados
POST	           /crear/	               Crear un gasto extra	        Superuser, Arrendador
GET	               /detalle/<int:pk>/	   Ver detalle de gasto extra	Según permisos
PATCH	           /editar/<int:pk>/	   Actualizar gasto extra	    Superuser, Arrendador
UPDATE	           /anular/<int:pk>/	   Anular gasto extra	        Superuser, Arrendador
DELETE	           /eliminar/<int:pk>/	   Eliminar gasto extra	        Superuser, Arrendador
