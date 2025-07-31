📚 README - App TASAS

📝 Descripción
La app 'tasas' gestiona las tasas de cambio diarias (USD a Bs) utilizadas para calcular el monto en Bs
de los pagos realizados en USD. Estas tasas son fundamentales para convertir y mostrar los valores correctamente según la fecha efectiva del pago.

🚀 Funcionalidades principales
🔹 Listar tasas diarias con filtros por fecha específica o rango de fechas.
🔹 Ver el detalle de una tasa diaria específica.
🔹 Crear nuevas tasas diarias, con validaciones automáticas para evitar duplicados y garantizar consistencia.
🔹 Validación automática de que una sola tasa puede estar activa por día por arrendador.
🔹 Filtrado contextual según el usuario autenticado (solo puede ver o crear tasas propias).
🔹 Eliminación y anulación de tasas.

📋 Endpoints disponibles
Método    URL	                  Descripción	                          Permisos
GET       /                       Lista todas las tasas de tu cuenta     Arrendador o Superusuario
GET       /detalle/<id>/          Ver el detalle de una tasa             Arrendador o Superusuario
POST      /crear/                 Crear nueva tasa diaria                Arrendador o Superusuario
POST      /anular/<id>/           Crear nueva tasa diaria                Arrendador o Superusuario
POST      /eliminar/<id>/         Crear nueva tasa diaria                Arrendador o Superusuario
GET       /activa/                Crear nueva tasa diaria                Arrendador o Superusuario


📦 Serializers
🔸 `TasaDiaSerializer`: usado para el listado.
🔸 `TasaDiaDetalleSerializer`: usado para la vista de detalle.
🔸 `TasaDiaCrearSerializer`: incluye validaciones automáticas por fecha y usuario.

⚙️ Filtros disponibles
🔹 Por fecha exacta: `?fecha=YYYY-MM-DD`
🔹 Por rango de fechas: `?fecha__gte=YYYY-MM-DD&fecha__lte=YYYY-MM-DD`
🔹 Internamente, también se filtran por el usuario autenticado para evitar acceso a tasas ajenas.

🔐 Permisos y validaciones
🔸 Solo arrendadores activos o superusuarios pueden acceder a tasas.
🔸 Solo arrendadores activos o superusuarios pueden crear nuevas tasas.
🔸 La tasa debe estar activa y coincidir con la fecha de transferencia del pago (en pagos y recibos).
🔸 Se impide crear tasas duplicadas por fecha y usuario.

📈 Flujo funcional
1. El arrendador crea una tasa con fecha y valor exactos (1 por día).
2. La tasa activa siempre es la ultima ingresada (la fecha mas cercana a la actual)
3. Al ingresar una tasa esta queda como activa y la tasa activa anterior pasa a inactiva
4. Al anular una tasa activa la ultima tasa ingresada (la que tenga fecha mas cercana a la actual y no este anulada) pasa a activa
5. La app de pagos selecciona automáticamente la tasa activa correspondiente a la fecha de transferencia.
6. Se calcula el monto en Bs con base en esa tasa y se guarda en el registro del pago.
7. Si no hay tasa disponible para esa fecha, se muestra un error indicando que el arrendador debe registrar una.

🧪 Casos validados
✔ Intentos de duplicar tasas por fecha y usuario → rechazados.
✔ Creación de tasas sin valor o sin fecha → rechazadas.
✔ Búsqueda restringida a tasas del arrendador autenticado.
✔ Tasa aplicada siempre debe coincidir con la fecha de la transferencia.

📌 Notas
👉 Las tasas solo se crean manualmente por ahora, pero se puede automatizar mediante integración con APIs externas si se desea a futuro.
👉 La app está integrada completamente con el flujo de pagos y recibos de mensualidades y gastos extra.
