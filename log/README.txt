# App Log

Esta app gestiona el registro de acciones importantes realizadas por los usuarios en la plataforma, como creación, actualización, validación, etc.

## Funcionalidades

- Registro automático de acciones relevantes en la base de datos.
- Filtrado avanzado de logs por usuario, tabla afectada, acción, rango de fechas, edificio y apartamento.
- Permisos para que solo superusuarios y arrendadores vinculados puedan ver logs relacionados a sus edificios.
- Vistas API para listar y obtener detalle de logs.
- Seguridad implementada con permisos personalizados y validaciones para restringir acceso.

## Modelos

- `LogAccion`: almacena información sobre el usuario que realizó la acción, la tabla afectada, tipo de acción, registro modificado, descripción y fecha.

## Vistas

- `ListaLogAccionesAPIView`: lista logs filtrables y seguros según permisos.
- `DetalleLogAccionAPIView`: detalle individual de un log.

## Filtros

- Filtros por usuario, tabla afectada, acción, rango de fecha, edificio y apartamento, basados en las relaciones de usuario y edificio/apartamento.

## Permisos

- Solo superusuarios y arrendadores autorizados pueden consultar logs.
- Arrendadores solo ven logs relacionados a los edificios y usuarios que administran.

## Uso

El acceso a las APIs requiere autenticación y permisos adecuados. Para filtrar, se usan query params compatibles con Django Filter.

---