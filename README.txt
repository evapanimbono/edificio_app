🏢 Edificio App
📝 Descripción
Edificio App es una plataforma web para la gestión integral de edificios residenciales, que facilita la administración de apartamentos, contratos de arrendamiento, mensualidades, pagos, gastos extra, usuarios y comunicaciones internas.
Está diseñada para ser modular, segura y escalable, adaptándose a las necesidades de superusuarios, arrendadores y arrendatarios.

🛠️ Tecnologías usadas
Componente	            Tecnología
Backend	                Django 5.2 + Django REST Framework
Base de datos	        PostgreSQL
Autenticación	        JWT (con SimpleJWT)
Filtros	                django-filter
Documentación API	    drf-yasg (Swagger)
Tareas programadas	    Celery + django-celery-beat ✅
Control de versiones	Git
Frontend	            (Por definir / separado)

🗂 Estructura del proyecto
El sistema está dividido en varias apps Django, cada una con una funcionalidad específica:
App	           Funcionalidad principal
usuarios	   Gestión de usuarios, roles y permisos
pagos	       Registro y validación de pagos y recibos
contratos	   Administración de contratos y mensualidades
edificios	   Gestión de edificios y apartamentos
gastos	       Control de gastos extra asociados a apartamentos
tasas	       Gestión de tasas y ajustes para cálculos financieros
log	           Registro de logs y auditorías
notificaciones Sistema de notificaciones y alertas (pendiente)
encuestas	   Gestión de encuestas internas (pendiente)

Estado general del desarrollo
Módulo          Vistas y Permisos   Serializers   Lógica Funcional      Logs   Filtros
======================================================================================
usuarios              ✅                 ✅               ✅            ✅       ✅
pagos                 ✅                 ✅               ✅            ✅       ✅
contratos             ✅                 ✅               ✅            ✅       ✅
mensualidades         ✅                 ✅               ✅            ✅       ✅
edificios             ✅                 ✅               ✅            ✅       ✅
apartamentos          ✅                 ✅               ✅            ✅       ✅
gastos                ✅                 ✅               ✅            ✅       ✅
tasas                 ✅                 ✅               ✅            ✅       ✅
log                   ✅                 ✅               ✅            ✅       ✅
notificaciones        💤 (pendiente)      —                —              —        —
encuestas             💤 (pendiente)      —                —              —        —

⚙️ Instalación y puesta en marcha
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

📡 Uso de la API
La documentación Swagger está disponible en: /swagger/
La autenticación se realiza mediante JWT tokens.
Los permisos dependen del tipo de usuario:
    🧑‍💼 Superusuario: acceso total
    👨‍💼 Arrendador: acceso a los edificios que administra
    🧍 Arrendatario: acceso limitado a su propio contenido

🤝 Cómo contribuir
💡 Sigue las buenas prácticas de Django y DRF.
🧪 Agrega tests unitarios y de integración.
🧾 Documenta los cambios relevantes en este README y el código.
🌱 Usa ramas temáticas y realiza Pull Requests para revisión.

📚 Documentación específica por módulo
Cada app incluye su propio archivo README.md con:
🧩 Descripción funcional
👥 Roles y permisos disponibles
🔗 Endpoints disponibles
🧪 Filtros y validaciones
📦 Modelos y relaciones
⚙️ Lógica interna destacada
