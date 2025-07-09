📜 App Log
Esta app registra todas las acciones importantes realizadas por los usuarios dentro del sistema, como creaciones, 
actualizaciones, eliminaciones o validaciones. Ideal para auditoría, seguimiento y control de cambios.

🎯 Funcionalidades principales
📋 Listar logs de acciones, filtrados por tipo de usuario:
    👨‍💼 Arrendador: ve acciones realizadas por usuarios vinculados a los edificios que administra.
    🧑‍💼 Superusuario: ve todas las acciones del sistema.
🔍 Ver detalle de un log específico.
⚙️ Registrar logs automáticamente desde cualquier parte del sistema usando la función registrar_log.

🗂 Modelo principal
LogAccion
👤 usuario: usuario que realizó la acción (puede ser null para acciones automáticas).
📝 accion: nombre de la acción (crear, actualizar, eliminar, validar...).
📊 tabla_afectada: nombre de la tabla relacionada (ej. contratos, mensualidades...).
🆔 registro_id: ID del objeto afectado.
📅 fecha: fecha y hora en que ocurrió la acción.
🧾 descripcion: detalle libre sobre lo ocurrido.

🛂 Permisos y roles
Acción	                👨‍💼 Arrendador	                            🧑‍💼 Superusuario
Ver lista de logs	           ✅ Sí (solo usuarios relacionados)	        ✅ Sí
Ver detalle de un log	       ✅ Sí (solo usuarios relacionados)	        ✅ Sí

🧍‍♂️ Los arrendatarios no tienen acceso a esta app.

🔗 Endpoints disponibles (URLs)
Método	        URL	            Descripción	                        Permisos
GET	            /	            Listar logs de acciones	            Arrendador / Superusuario
GET	            /<pk>/	        Ver detalle de un log específico	Arrendador / Superusuario

🔍 Filtros disponibles
Puedes usar filtros para buscar logs por:
    👤 usuario: ID del usuario que hizo la acción.
    🗃️ tabla_afectada: nombre de la tabla (ej. contratos, mensualidades...).
    📝 accion: nombre de la acción (ej. creó, eliminó...).
    📅 fecha_desde, fecha_hasta: rango de fechas.
    🏢 edificio: logs asociados a usuarios que habitan o administran dicho edificio.
    🏠 apartamento: logs asociados a usuarios con contratos en ese apartamento.

⚙️ Registro automático de logs
Desde cualquier parte de tu código puedes registrar acciones llamando a:

registrar_log(
    usuario=usuario,
    accion="creó contrato",
    tabla="Contrato",
    registro_id=123,
    descripcion="Contrato creado para el apartamento 101"
)

usuario: puede ser None si es una acción automática.
tabla: debe ser el nombre de la tabla afectada.
registro_id: ID del objeto creado/actualizado.
descripcion: texto libre explicando el cambio.

✅ Se usa en tareas, vistas y serializers en toda la app.

🧠 Lógica interna destacada
Los arrendadores solo ven logs de los usuarios (arrendadores y arrendatarios) que pertenecen a edificios que administran o colaboran.
Los superusuarios pueden ver todos los registros sin restricción.
El filtrado por edificio y apartamento permite auditoría detallada.