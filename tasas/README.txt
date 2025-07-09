📚 README - App TASAS
📝 Descripción
La app tasas gestiona las tasas de cambio diarias (USD a Bs) utilizadas para calcular el monto en Bs
de los pagos realizados en USD. Esto es fundamental para convertir y mostrar los valores correctamente según la fecha del pago.

🚀 Funcionalidades principales
🔹 Listar tasas diarias con filtros por rango de fechas.
🔹 Ver detalle de una tasa diaria específica.
🔹 Crear nuevas tasas diarias, con validaciones para evitar duplicados por fecha.
🔹 Editar y eliminar tasas diarias (en planificación para próximas iteraciones).

📋 Endpoints disponibles
Método	  URL	            Descripción	            Permisos
GET	      /	                Lista todas las tasas	Autenticado
GET	      /detalle/<id>/	Detalle de una tasa	    Autenticado
POST      /crear/       	Crear una nueva tasa	Autenticado (admin)

📦 Serializers
TasaDiaSerializer (listado)
TasaDiaDetalleSerializer (detalle)
CrearTasaDiaSerializer (creación con validación)

⚙️ Filtros
Filtro por fecha especifica o rango de fechas: fecha__gte y fecha__lte para consultas específicas.

🔐 Permisos
Solo usuarios autenticados pueden ver y crear tasas.
La creación esta restringida a superuser y arrendadores según política de la app.

📈 Flujo típico
Se crea o actualiza la tasa diaria.
Se usa la tasa para calcular montos en Bs en la app de pagos.
Los pagos registrados usan la tasa correcta según fecha.