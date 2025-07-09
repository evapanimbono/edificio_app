# App Gastos

Esta app gestiona los gastos extra asociados a apartamentos dentro de edificios, junto con los recibos que se generan para cada gasto.

## Funcionalidades

- Crear, listar, editar y eliminar gastos extra.
- Generación automática de recibos relacionados a cada gasto extra.
- Control de estados de gastos y recibos: pendiente, pagado, atrasado, etc.
- Validación avanzada de campos y estados, incluyendo fechas y montos.
- Logs automáticos para registrar acciones sobre gastos.
- Permisos para que solo usuarios autorizados (arrendadores y superusuarios) puedan gestionar gastos y recibos.
- Filtros para buscar gastos por apartamento, monto, fechas, estado y más.

## Modelos principales

- `GastoExtra`: representa un gasto adicional asignado a un apartamento.

## Vistas API

- Listar gastos con filtros por apartamento, monto, fechas, estado, etc.
- Crear, editar y eliminar gastos extra (con permisos adecuados).
- Detalle individual de un gasto extra.

## Permisos

- Solo arrendadores vinculados a edificios y superusuarios pueden acceder y modificar gastos.
- Arrendatarios no tienen acceso para modificar gastos.

## Filtros disponibles

- Apartamento (solo para arrendadores y superusuarios).
- Monto en USD (para todos).
- Fecha de generación (arrendadores y superusuarios).
- Fecha de vencimiento (para todos).
- Estado del gasto (para todos).

## Uso

Todas las operaciones requieren autenticación. Los filtros se pasan vía query params compatibles con Django Filter.

---