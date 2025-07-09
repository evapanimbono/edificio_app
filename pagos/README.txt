📚 README - App PAGOS
📝 Descripción
La app pagos gestiona todo el proceso de pagos de mensualidades y gastos extra por arrendatarios y arrendadores,
 desde el registro hasta la validación y consulta de recibos y pagos.

🚀 Funcionalidades principales
🔹 Registro de pagos por mensualidades y gastos extra, en efectivo, transferencia o mixto.
🔹 Validación de pagos por parte de arrendadores.
🔹 Gestión y visualización de recibos (pendientes, atrasados, pagados).
🔹 Generación manual o automática de recibos asociados a mensualidades y gastos extra.
🔹 Visualización detallada de pagos y recibos, con estados y montos en USD y Bs.
🔹 Permisos diferenciados para arrendatarios y arrendadores.

📋 Endpoints disponibles
Método	    URL	                        Descripción	                                                Permisos
GET	        /	                        Lista pagos (filtrable por usuario/estado)	                Arrendador, arrendatario
POST	    /registrar/	                Registrar nuevo pago	                                    Autenticado
POST	    /validar/<pago_id>/ 	    Validar o rechazar pago pendiente	                        Arrendador
GET	        /validados/historial/	    Historial de pagos validados	                            Autenticado
GET	        /detalle/<id>/	            Detalle de pago específico	                                Usuario propietario
POST	    /detalle-previo/	        Obtener detalle previo antes de registrar pago	            Autenticado
GET	        /recibos/	                Listado de recibos asociados (arrendador o arrendatario)	Autenticado
GET	        /recibos/seleccionables/	Listado de recibos pendientes o atrasados para pago	        Autenticado
GET	        /recibos/usuario/	        Recibos del usuario autenticado	                            Autenticado
POST	    /recibos/generar/	        Generar recibos manualmente (superusuario)	                Superusuario

📦 Serializers
PagoSerializer
PagoEfectivoSerializer 
PagoTransferenciaSerializer 
ItemPagoSerializer
BilleteSerializer
TransferenciaSerializer
PagoRegistroSerializer
DetallePagoSerializer

ReciboMensualidadSerializer
ReciboGastoExtraSerializer
ReciboSerializer
GenerarReciboSerializer

🔐 Permisos
Arrendatarios pueden ver y registrar pagos solo para sus recibos y contratos.
Arrendadores pueden validar pagos y ver recibos asociados a edificios que administran.
Superusuarios tienen acceso completo.

📈 Flujo típico
Arrendatario o arrendador consulta recibos pendientes o atrasados (vía RecibosSeleccionablesAPIView).
Solicitan detalle previo del pago a realizar (vía DetallePagoPrevioAPIView).
Registran pago con montos y tipo seleccionado (efectivo/transferencia/mixto).
Si lo registra arrendador, el pago queda validado automáticamente.
Si lo registra arrendatario, queda pendiente para validación por arrendador (ValidarPagoView).
Se actualizan estados de mensualidades, gastos y recibos según pago validado.

🔧 Próximos pasos
Implementar vista detalle de recibo.
Mejorar manejo de anulaciones y eliminaciones en mensualidades, gastos y pagos.
Añadir edición y eliminación de tasas con efectos en pagos asociados.