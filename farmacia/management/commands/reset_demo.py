"""
python manage.py reset_demo

Elimina TODOS los datos demo y los vuelve a crear desde cero.
Útil para reiniciar la demo antes de una presentación.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import transaction
from farmacia.models import (
    Venta, Boleta, Pago, CarritoVenta, CarritoItem,
    HistorialStock, LoteMedicamento, Medicamento,
    Cliente, Proveedor, RolPermiso, NotaCredito,
)


class Command(BaseCommand):
    help = "Reinicia la demo: elimina datos y vuelve a sembrarlos"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n⚠  REINICIANDO DEMO — esto eliminará datos demo...\n"))

        with transaction.atomic():
            # Eliminar en orden por dependencias
            NotaCredito.objects.all().delete()
            Pago.objects.all().delete()
            Boleta.objects.all().delete()
            CarritoItem.objects.all().delete()
            CarritoVenta.objects.all().delete()
            Venta.objects.all().delete()
            HistorialStock.objects.all().delete()
            LoteMedicamento.objects.all().delete()
            Medicamento.objects.all().delete()
            Cliente.objects.all().delete()
            Proveedor.objects.all().delete()
            User.objects.filter(username__endswith="_demo").delete()

        self.stdout.write(self.style.SUCCESS("  ✓ Datos eliminados\n"))
        call_command("seed_demo")
