from django.apps import AppConfig


class PagosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pagos'

    def ready(self):
        # Este método se ejecuta cuando Django inicia.
        # Importamos las señales para que los decoradores @receiver se activen.
        import pagos.signals