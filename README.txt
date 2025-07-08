Proyecto Edificio App

·Descripción
Edificio App es una plataforma web para la gestión integral de edificios residenciales, que facilita la administración de apartamentos, contratos de arrendamiento, pagos, 
gastos extra, usuarios y comunicaciones internas. Está diseñada para ser segura, escalable y modular, adaptándose a las necesidades de administradores, arrendadores y arrendatarios.

·Tecnologías usadas
Backend: Django 5.2, Django REST Framework
Base de datos: PostgreSQL
Autenticación: JWT / Token Authentication (ajustar según lo implementado)
Filtros: django-filter
Documentación API: drf-yasg (Swagger)
Tareas programadas: django-celery-beat (en desarrollo)
Frontend: (Por definir / separado)
Control de versiones: Git

·Estructura del proyecto
El proyecto está organizado en varias aplicaciones Django, cada una enfocada en un módulo funcional:
App	           Funcionalidad principal
======================================================================
usuarios	   |Gestión de usuarios, roles y permisos
pagos	       |Registro y validación de pagos y recibos
contratos	   |Administración de contratos y mensualidades
mensualidades  |(Integrado con contratos, mensualidades automáticas)
edificios	   |Gestión de edificios
apartamentos   |Gestión de apartamentos y su relación con contratos
gastos	       |Control de gastos extra asociados a apartamentos
tasas	       |Gestión de tasas y ajustes para cálculos financieros
log	           |Registro de logs y auditorías
notificaciones |Sistema de notificaciones y alertas (pendiente)
encuestas	   |Gestión de encuestas internas (pendiente)

·Estado general del desarrollo
Módulo	Vistas y Permisos	Serializers	Lógica Funcional	Logs	Filtros
============================================================================
usuarios	   ✅	           ✅	        ✅	         ✅	     ✅
pagos	       ✅	           ✅	        ✅	         ✅	     ✅
contratos	   ✅	           ✅	        ✅	         ✅	     ✅
mensualidades  ✅	           ✅	        ✅	         ✅	     🚧
edificios	   ✅	           ✅	        ✅	         ✅	     ✅
apartamentos   ✅	           ✅	        ✅	         ✅	     ✅
gastos	       ✅	           ✅	        ✅	         ✅	     ✅
tasas	       ⏳	           ✅	        ✅	         ✅	     🚧
log	           ✅	           ✅	        ✅	         ✅        —
notificaciones	💤 (pendiente)	 —	           —	          —         —
encuestas	    💤 (pendiente)	 —	           —	          —         —

·Instalación y puesta en marcha
1. Clonar el repositorio:
git clone https://tu-repositorio.git
cd edificio_app

2. Crear y activar entorno virtual:
python3 -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate     # Windows

3. Instalar dependencias:
pip install -r requirements.txt

4. Configurar base de datos en settings.py (PostgreSQL).

5. Aplicar migraciones:
python manage.py migrate

6. Crear superusuario (opcional):
python manage.py createsuperuser

7. Correr servidor de desarrollo:
python manage.py runserver

·Uso de la API
La documentación Swagger está disponible en /swagger/ (o ruta que definas).
Autenticación mediante token (ajustar según implementación).
Consultar permisos y roles para acceso a recursos.

·Cómo contribuir
Seguir las buenas prácticas de Django y REST Framework.
Agregar tests unitarios e integración para nuevas funcionalidades.
Documentar cambios en README y en el código.
Crear branches temáticos y hacer PRs para revisión.

·Documentación específica de módulos
Se recomienda crear carpetas o archivos docs/ por cada app para documentar:
Modelos y relaciones
Endpoints disponibles y ejemplos
Validaciones y permisos especiales
Flujo de trabajo interno
