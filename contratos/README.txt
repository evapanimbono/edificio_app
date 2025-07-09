📄 App Contratos
Esta app gestiona los contratos de arrendamiento y las mensualidades relacionadas, controlando accesos según el tipo de usuario.

🎯 Funcionalidades principales
📋 Listar contratos y mensualidades filtrados según tipo de usuario:
    🧍‍♂️ Arrendatario: ve solo sus contratos y mensualidades.
    👨‍💼 Arrendador: ve contratos y mensualidades de apartamentos que administra.
    🧑‍💼 Superusuario: ve todo sin restricciones.
✍️ Crear, actualizar y eliminar contratos (solo arrendador o superusuario).
📆 Gestionar mensualidades:
    Crear mensualidades (solo superusuario).
    Modificar solo la fecha de vencimiento (arrendador o superusuario).
    Eliminar mensualidades sin pagos asociados.
    Anular mensualidades con pagos asociados.
⚙️ Generación automática de mensualidades para contratos activos en la fecha de pago mensual.
🧾 Registro de logs para todas las acciones importantes (crear, editar, eliminar, anular).

🗂 Modelos principales
Contrato
🔹 arrendatario: usuario arrendatario.
🔹 apartamento: apartamento arrendado.
🔹 fecha_inicio, fecha_fin: duración del contrato.
🔹 fecha_pago_mensual: día del mes para el pago.
🔹 monto_usd_mensual: monto mensual en USD.
🔹 archivo_contrato_pdf: contenido o ruta del contrato en PDF.
🔹 activo: indica si el contrato está vigente.
🔹 Fechas de auditoría: created_at, updated_at.

Mensualidad
🔸 contrato: contrato asociado.
🔸 fecha_generacion y fecha_vencimiento.
🔸 monto_usd y saldo_pendiente.
🔸 estado: pendiente, pagado, atrasado o anulado.
🔸 comentario_anulacion: opcional para justificar anulaciones.
🔸 Fechas de auditoría: created_at, updated_at.

🛂 Permisos y roles
Acción	                  🧍‍♂️ Arrendatario	         👨‍💼 Arrendador	                             🧑‍💼 Superusuario
Ver contratos propios	        ✅ Sí	                   ✅ Sí (apartamentos administrados)	        ✅ Sí
Crear contrato	                ❌ No	                   ✅ Sí	                                        ✅ Sí
Editar / eliminar contrato	    ❌ No	                   ✅ Sí	                                        ✅ Sí
Ver mensualidades	            ✅ Sí (propias)	           ✅ Sí (apartamentos administrados)	        ✅ Sí
Crear mensualidad	            ❌ No	                   ❌ No	                                        ✅ Sí
Editar mensualidad	            ❌ No	                   ✅ Sí (solo fecha de vencimiento)	            ✅ Sí
Eliminar mensualidad	        ❌ No	                   ✅ Sí (sin pagos asociados)	                ✅ Sí
Anular mensualidad	            ❌ No	                   ✅ Sí (con pagos asociados)	                ✅ Sí

🔗 Endpoints principales (URLs)
Contratos
Método	             URL	        Descripción	                            Permisos
GET	                /	            Listar contratos según usuario	        Autenticado
POST	            /crear/	        Crear contrato	                        Arrendador / Superusuario
GET	                /detalle/<pk>/	Ver detalle contrato (arrendatario)	    Arrendatario
GET/PUT/DELETE	    /<pk>/	        Detalle, actualizar o eliminar contrato	Arrendador / Superusuario

Mensualidades
Método	       URL	                            Descripción	                         Permisos
GET	           /mensualidades/	                Listar mensualidades según usuario	 Autenticado
GET	           /mensualidades/detalle/<pk>/	    Ver detalle mensualidad	             Arrendatario / Arrendador / Superusuario
POST	       /mensualidades/crear/	        Crear mensualidad	                 Superusuario
PUT/PATCH	   /mensualidades/actualizar/<pk>/	Editar mensualidad (fecha venc.)	 Arrendador / Superusuario
DELETE	       /mensualidades/eliminar/<pk>/	Eliminar mensualidad (sin pagos)	 Arrendador / Superusuario
POST	       /mensualidades/anular/<pk>/	    Anular mensualidad (con pagos)	     Arrendador / Superusuario

🔍 Filtros disponibles
Para contratos
🏢 Apartamento
👤 Usuario (arrendatario)
🏙️ Edificio
✅ Estado activo
📅 Rango fechas inicio y fin

Para mensualidades
📌 Estado (pendiente, pagado, atrasado, anulado)
📅 Rango fechas de generación y vencimiento
📄 Contrato, apartamento, usuario, edificio

⚙️ Tareas automáticas
generar_mensualidades_automaticas: crea mensualidades automáticamente para contratos activos en la fecha de pago mensual.

Registra logs y genera recibos relacionados.

🧾 Registro de acciones (logs)
Cada acción importante (crear, actualizar, eliminar, anular) queda registrada en LogAccion con:
👤 Usuario que realizó la acción.
✍️ Acción realizada.
📋 Tabla afectada.
🆔 ID del registro.
📝 Descripción detallada.

📝 Notas técnicas
Validaciones en serializers para evitar solapamiento de contratos y asegurar apartamento activo.
Validaciones para impedir modificación de mensualidades pagadas.
Estados claros para mensualidades: pendiente, pagado, atrasado, anulado.
Permisos personalizados para controlar acceso según rol y vínculo con edificios y contratos.

