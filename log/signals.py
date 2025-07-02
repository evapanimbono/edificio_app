from .models import LogAccion

def registrar_log(usuario=None, accion="", tabla="", registro_id=None, descripcion=""):
    """
    Registra una acción en el log.

    Args:
        usuario (Usuario): Usuario que ejecuta la acción (puede ser None para acciones automáticas).
        accion (str): Acción realizada (ej: 'creación', 'actualización', 'validación').
        tabla (str): Nombre de la tabla afectada (ej: 'mensualidades', 'pagos', etc).
        registro_id (int): ID del registro afectado.
        descripcion (str): Detalles adicionales (opcional).
    """
    LogAccion.objects.create(
        usuario=usuario,
        accion=accion,
        tabla_afectada=tabla,
        registro_id=registro_id,
        descripcion=descripcion
    )