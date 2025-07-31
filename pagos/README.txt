📚 README - App PAGOS
📝 Descripción
La app pagos gestiona todo el proceso de pagos de mensualidades y gastos extra por arrendatarios y arrendadores,
desde el registro hasta la validación y consulta de recibos y pagos.

🚀 Funcionalidades principales
🔹 Registro de pagos por mensualidades y gastos extra, en efectivo, transferencia o mixto.
🔹 Validación de pagos por parte de arrendadores.
🔹 Gestión y visualización de recibos (pagados, anulados).
🔹 Generación automática de recibos asociados a mensualidades y gastos extra pagados.
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
POST	    /anular/<pago_id>/	        Anular pago que ya haya sido validado       	            Arrendador
POST	    /eliminar/<pago_id>/	    Anular pago que ya haya sido validado       	            Arrendador

GET	        /recibos/	                Listado de recibos asociados (arrendador o arrendatario)	Autenticado
GET	        /recibos/<id>/	            Detalle de recibo específico                    	        Autenticado

📦 Serializers
PagoSerializer
PagoEfectivoSerializer 
PagoTransferenciaSerializer 
ItemPagoSerializer
BilleteSerializer
TransferenciaSerializer
PagoRegistroSerializer
DetallePagoSerializer
AnularPagoSerializer
AccionValidarPagoSerializer

ReciboMensualidadSerializer
ReciboGastoExtraSerializer
ReciboSerializer

🔐 Permisos
Arrendatarios pueden ver y registrar pagos y recibos solo para sus mensualidades y gastos extras asociados.
Arrendadores pueden registrar, validar pagos y ver recibos y pagos asociados a apartamentos de edificios que administran.
Superusuarios tienen acceso completo.

📈 Flujo típico
Arrendatario o arrendador consulta mensualidades y/o gastos extras pendientes o atrasados.
Solicitan detalle previo del pago a realizar (vía DetallePagoPrevioAPIView).
Registran pago con montos y tipo seleccionado (efectivo/transferencia/mixto).
Si lo registra arrendador, el pago queda validado automáticamente.
Si lo registra arrendatario, queda pendiente para validación por arrendador (ValidarPagoView).
Se genera automáticamente un recibo asociado al pago y a la mensualidad y/o gasto extra.
Se actualizan estados de mensualidades y gastos según pago validado.