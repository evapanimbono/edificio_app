from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pago
from notificaciones.models import Notificacion

print("✅ Las señales de Pagos se han cargado correctamente") # <--- Agrega esto

@receiver(post_save, sender=Pago)
def notificar_pago_validado(sender, instance, created, **kwargs):
# Verificamos que el pago esté validado
    if instance.estado_validacion == 'validado':
        from notificaciones.models import Notificacion
        
        try:
            # El receptor siempre será el usuario que registró el pago (el vecino)
            # No importa si pagó mensualidad o gasto extra.
            Notificacion.objects.create(
                receptor=instance.usuario,
                mensaje=f"¡Buenas noticias! Tu pago #{instance.id} por un monto de {instance.monto_total} USD ha sido validado correctamente.",
                tipo='sistema'
            )
        except Exception as e:
            # Lo logueamos pero no dejamos que rompa el proceso principal
            print(f"Error enviando notificación: {e}")

    elif instance.estado_validacion == 'rechazado':
        from notificaciones.models import Notificacion

        try:
            Notificacion.objects.create(
                receptor=instance.usuario,
                mensaje=f"Atención: Tu pago #{instance.id} ha sido rechazado. Motivo: {instance.observaciones}",
                tipo='sistema'
            )
        except Exception as e:
            # Lo logueamos pero no dejamos que rompa el proceso principal
            print(f"Error enviando notificación: {e}")