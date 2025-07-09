# App Edificios

Esta app maneja la administración y gestión de edificios dentro del sistema.

## Funcionalidades principales

- Gestión de edificios (crear, editar, listar y eliminar).
- Gestión de apartamentos (crear, editar y listar).
- Relación con apartamentos, usuarios (arrendadores, colaboradores, arrendatarios) y otros módulos.
- Control de permisos para que solo usuarios autorizados puedan realizar acciones específicas.
- Logs para registrar acciones importantes realizadas sobre los edificios y/o apartamentos.
- Filtros para buscar edificios y/o apartamentos por diferentes criterios.

## Modelos principales

- `Edificio`: representa un edificio en la aplicación.
- `Apartamento`: relacionado a un edificio, representa una unidad dentro del mismo.

## Vistas API

- Listar edificios con filtros por nombre, ubicación, o usuario asociado.
- Crear, editar y eliminar edificios (sólo para usuarios con permisos adecuados).
- Detalle individual del edificio.

- Listar apartamentos con filtros por edificio, estado, numero de habitaciones o baños, piso y numero de apartamento
- Crear, editar apartamentos (solo para usuarios con permisos asociados).
- Detalle individual del apartamento.

## Permisos

- Sólo superusuarios y arrendadores vinculados pueden gestionar edificios y/o apartamentos.
- Los arrendatarios tienen acceso limitado o sólo lectura, según configuración.

## Filtros disponibles

- Nombre del edificio.
- Ubicación o ciudad.
- Usuario asignado (arrendador o colaborador).

## Uso

Requiere autenticación. Los filtros pueden pasarse por query params compatibles con Django Filter.

---