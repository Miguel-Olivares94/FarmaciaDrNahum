"""
python manage.py seed_demo

Crea datos ficticios realistas para la demo del sistema.
Incluye: usuarios, roles, proveedores, medicamentos, clientes,
lotes, historial de stock y ventas de los últimos 90 días.
"""

import random
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from farmacia.models import (
    AuditoriaLog, Boleta, CarritoItem, CarritoVenta, Cliente,
    HistorialStock, LoteMedicamento, Medicamento, NotaCredito,
    Pago, Proveedor, RolPermiso, Venta,
)


PASS_DEMO = "Demo2026!"

PROVEEDORES = [
    {"nombre": "Laboratorio Chile S.A.", "razon_social": "Lab Chile S.A.", "rut": "76.123.456-7",
     "email": "ventas@labchile.cl", "fono": "+56223456789", "direccion": "Av. Providencia 1234, Santiago"},
    {"nombre": "Recalcine Laboratorios", "razon_social": "Recalcine S.A.", "rut": "91.234.567-8",
     "email": "contacto@recalcine.cl", "fono": "+56222345678", "direccion": "Los Leones 456, Santiago"},
    {"nombre": "Mintlab S.A.", "razon_social": "Mintlab S.A.", "rut": "76.345.678-9",
     "email": "info@mintlab.cl", "fono": "+56221234567", "direccion": "Av. Las Condes 789, Santiago"},
    {"nombre": "Andromaco S.A.", "razon_social": "Andromaco S.A.", "rut": "76.456.789-0",
     "email": "pedidos@andromaco.cl", "fono": "+56229876543", "direccion": "Vitacura 234, Santiago"},
    {"nombre": "Abbott Laboratories Chile", "razon_social": "Abbott Chile Ltda.", "rut": "96.567.890-1",
     "email": "abbott@abbott.cl", "fono": "+56228765432", "direccion": "Isidora Goyenechea 3000, Santiago"},
]

MEDICAMENTOS = [
    # (nombre, lab, principio, presentacion, dosis, tipo_venta, precio, stock, sku)
    ("Paracetamol 500mg",   "Lab Chile", "Paracetamol",           "Comprimidos", "500mg",   "libre",          890,  350, "DM-001"),
    ("Ibuprofeno 400mg",    "Recalcine", "Ibuprofeno",            "Comprimidos", "400mg",   "libre",          1200, 280, "DM-002"),
    ("Amoxicilina 500mg",   "Mintlab",   "Amoxicilina",           "Cápsulas",    "500mg",   "receta_simple",  3500, 120, "DM-003"),
    ("Loratadina 10mg",     "Andromaco", "Loratadina",            "Comprimidos", "10mg",    "libre",           650, 200, "DM-004"),
    ("Omeprazol 20mg",      "Abbott",    "Omeprazol",             "Cápsulas",    "20mg",    "receta_simple",  2800,  95, "DM-005"),
    ("Metformina 850mg",    "Lab Chile", "Metformina",            "Comprimidos", "850mg",   "receta_simple",  1800,  80, "DM-006"),
    ("Enalapril 10mg",      "Recalcine", "Enalapril",             "Comprimidos", "10mg",    "receta_simple",  1500,  60, "DM-007"),
    ("Atorvastatina 20mg",  "Mintlab",   "Atorvastatina",         "Comprimidos", "20mg",    "receta_simple",  4200,  45, "DM-008"),
    ("Alprazolam 0.5mg",    "Andromaco", "Alprazolam",            "Comprimidos", "0.5mg",   "controlada",     2200,  30, "DM-009"),
    ("Clonazepam 0.5mg",    "Abbott",    "Clonazepam",            "Comprimidos", "0.5mg",   "controlada",     1900,  25, "DM-010"),
    ("Salbutamol Spray",    "Lab Chile", "Salbutamol",            "Aerosol",     "100mcg",  "receta_simple",  5800,  55, "DM-011"),
    ("Cetirizina 10mg",     "Recalcine", "Cetirizina",            "Comprimidos", "10mg",    "libre",           720, 180, "DM-012"),
    ("Diclofenaco 50mg",    "Mintlab",   "Diclofenaco",           "Comprimidos", "50mg",    "receta_simple",  1600, 140, "DM-013"),
    ("Ranitidina 150mg",    "Andromaco", "Ranitidina",            "Comprimidos", "150mg",   "libre",           980,  90, "DM-014"),
    ("Aspirina 100mg",      "Abbott",    "Ácido Acetilsalicílico","Comprimidos", "100mg",   "libre",          1100, 320, "DM-015"),
    ("Vitamina C 1000mg",   "Lab Chile", "Ácido Ascórbico",       "Efervescentes","1000mg", "libre",          2300, 250, "DM-016"),
    ("Zinc 50mg",           "Recalcine", "Zinc",                  "Comprimidos", "50mg",    "libre",          1800, 160, "DM-017"),
    ("Losartán 50mg",       "Mintlab",   "Losartán",              "Comprimidos", "50mg",    "receta_simple",  2100,  70, "DM-018"),
    ("Metronidazol 500mg",  "Andromaco", "Metronidazol",          "Comprimidos", "500mg",   "receta_simple",  2400,  85, "DM-019"),
    ("Fluoxetina 20mg",     "Abbott",    "Fluoxetina",            "Cápsulas",    "20mg",    "receta_retenida",3800,  40, "DM-020"),
    ("Tramadol 50mg",       "Lab Chile", "Tramadol",              "Cápsulas",    "50mg",    "controlada",     3200,  20, "DM-021"),
    ("Ibuprofeno 600mg",    "Recalcine", "Ibuprofeno",            "Comprimidos", "600mg",   "receta_simple",  1900, 110, "DM-022"),
    ("Clorfenamina 4mg",    "Mintlab",   "Clorfenamina",          "Comprimidos", "4mg",     "libre",           450, 300, "DM-023"),
    ("Dexametasona 4mg",    "Andromaco", "Dexametasona",          "Comprimidos", "4mg",     "receta_simple",  2600,  35, "DM-024"),
    ("Vitamina D3 1000UI",  "Abbott",    "Colecalciferol",        "Cápsulas",    "1000UI",  "libre",          3100, 190, "DM-025"),
]

CLIENTES = [
    ("12345678-9", "Juan", "Pérez González", "juan.perez@gmail.com", "+56912345678"),
    ("13456789-0", "María", "López Silva", "maria.lopez@outlook.com", "+56923456789"),
    ("14567890-1", "Carlos", "Martínez Rojas", "cmartinez@gmail.com", "+56934567890"),
    ("15678901-2", "Ana", "Soto Fuentes", "ana.soto@hotmail.com", "+56945678901"),
    ("16789012-3", "Pedro", "Díaz Morales", "pedro.diaz@gmail.com", "+56956789012"),
    ("17890123-4", "Claudia", "Fernández Castro", "claudia.f@gmail.com", "+56967890123"),
    ("18901234-5", "Roberto", "Herrera Vega", "roberto.h@outlook.com", "+56978901234"),
    ("19012345-6", "Valentina", "Torres Campos", "valen.torres@gmail.com", "+56989012345"),
    ("10123456-7", "Diego", "Vargas Pinto", "dvargas@gmail.com", "+56990123456"),
    ("11234567-8", "Sofía", "Ramos Jiménez", "sofia.ramos@gmail.com", "+56901234567"),
    ("12234567-9", "Andrés", "Muñoz Sepúlveda", "andres.munoz@gmail.com", "+56911234567"),
    ("13345678-0", "Fernanda", "Gutiérrez Araya", "fer.gutierrez@hotmail.com", "+56922345678"),
    ("14456789-1", "Matías", "Contreras Leal", "matias.c@gmail.com", "+56933456789"),
    ("15567890-2", "Carolina", "Romero Navarro", "carolina.r@outlook.com", "+56944567890"),
    ("16678901-3", "Felipe", "Aguilera Reyes", "felipe.a@gmail.com", "+56955678901"),
    ("17789012-4", "Daniela", "Cabrera Molina", "dani.cabrera@gmail.com", "+56966789012"),
    ("18890123-5", "Sebastián", "Fuentes Espinoza", "seba.f@gmail.com", "+56977890123"),
    ("19901234-6", "Camila", "Pizarro Cortés", "camila.p@hotmail.com", "+56988901234"),
    ("11012345-7", "Tomás", "Salinas Miranda", "tomas.salinas@gmail.com", "+56999012345"),
    ("12112345-8", "Isadora", "Bravo Cisternas", "isa.bravo@gmail.com", "+56910123456"),
]

METODOS_PAGO = ["EFECTIVO", "EFECTIVO", "EFECTIVO", "DEBITO", "DEBITO", "CREDITO", "TRANSFERENCIA"]


class Command(BaseCommand):
    help = "Crea datos de demostración profesionales para el sistema"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Elimina datos demo antes de crear nuevos")

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n╔══════════════════════════════════════╗"))
        self.stdout.write(self.style.WARNING("║   SEED DEMO — Farmacia Dr. Nahum     ║"))
        self.stdout.write(self.style.WARNING("╚══════════════════════════════════════╝\n"))

        if options["clear"]:
            self._limpiar_datos_demo()

        with transaction.atomic():
            proveedores = self._crear_proveedores()
            self._crear_usuarios()
            medicamentos = self._crear_medicamentos(proveedores)
            clientes = self._crear_clientes()
            self._crear_ventas_historicas(medicamentos, clientes)

        self._mostrar_credenciales()

    # ──────────────────────────────────────────
    def _limpiar_datos_demo(self):
        self.stdout.write("  Limpiando datos demo anteriores...")
        User.objects.filter(username__endswith="_demo").delete()
        self.stdout.write(self.style.SUCCESS("  ✓ Usuarios demo eliminados"))

    # ──────────────────────────────────────────
    def _crear_usuarios(self):
        self.stdout.write("\n  Creando usuarios demo...")
        roles = [
            ("admin_demo",    "Admin",    "admin@farmaciadrnahum.cl",    "ADMIN"),
            ("vendedor_demo", "Vendedor", "vendedor@farmaciadrnahum.cl", "VENDEDOR"),
            ("gerente_demo",  "Gerente",  "gerente@farmaciadrnahum.cl",  "GERENTE"),
            ("contador_demo", "Contador", "contador@farmaciadrnahum.cl", "CONTADOR"),
        ]
        for username, nombre, email, rol in roles:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": nombre,
                    "last_name": "Demo",
                    "is_staff": rol == "ADMIN",
                    "is_superuser": rol == "ADMIN",
                },
            )
            if created:
                user.set_password(PASS_DEMO)
                user.save()
            RolPermiso.objects.get_or_create(
                user=user,
                defaults={"rol": rol, "estado_activo": True},
            )
            estado = "creado" if created else "ya existe"
            self.stdout.write(f"    ✓ {username} [{rol}] — {estado}")

    # ──────────────────────────────────────────
    def _crear_proveedores(self):
        self.stdout.write("\n  Creando proveedores...")
        result = []
        for p in PROVEEDORES:
            obj, created = Proveedor.objects.get_or_create(
                rut=p["rut"],
                defaults={
                    "nombre": p["nombre"],
                    "razon_social": p["razon_social"],
                    "email": p["email"],
                    "fono": p["fono"],
                    "direccion": p["direccion"],
                },
            )
            result.append(obj)
            self.stdout.write(f"    ✓ {obj.nombre}")
        return result

    # ──────────────────────────────────────────
    def _crear_medicamentos(self, proveedores):
        self.stdout.write("\n  Creando medicamentos y lotes...")
        result = []
        labs = {
            "Lab Chile": proveedores[0],
            "Recalcine": proveedores[1],
            "Mintlab": proveedores[2],
            "Andromaco": proveedores[3],
            "Abbott": proveedores[4],
        }
        hoy = date.today()

        for datos in MEDICAMENTOS:
            nombre, lab, principio, presentacion, dosis, tipo, precio, stock, sku = datos
            proveedor = labs.get(lab, proveedores[0])

            med, created = Medicamento.objects.get_or_create(
                sku=sku,
                defaults={
                    "nombre": nombre,
                    "laboratorio": lab,
                    "principio_activo": principio,
                    "presentacion": presentacion,
                    "dosis": dosis,
                    "tipo_venta": tipo,
                    "precio": Decimal(str(precio)),
                    "stock": stock,
                    "proveedor": proveedor,
                    "fecha_ingreso": hoy - timedelta(days=random.randint(30, 180)),
                    "fecha_vencimiento": hoy + timedelta(days=random.randint(180, 730)),
                },
            )

            # Crear lote si no existe
            LoteMedicamento.objects.get_or_create(
                medicamento=med,
                numero_lote=f"L{random.randint(10000, 99999)}",
                defaults={
                    "fecha_vencimiento": hoy + timedelta(days=random.randint(180, 730)),
                    "cantidad_ingresada": stock + random.randint(50, 200),
                    "cantidad_disponible": stock,
                    "proveedor": proveedor,
                    "precio_costo": Decimal(str(int(precio * 0.55))),
                },
            )

            result.append(med)
            if created:
                self.stdout.write(f"    ✓ {nombre} [stock:{stock}]")

        return result

    # ──────────────────────────────────────────
    def _crear_clientes(self):
        self.stdout.write("\n  Creando clientes...")
        result = []
        for rut, nombre, apellido, email, telefono in CLIENTES:
            cliente, created = Cliente.objects.get_or_create(
                rut_dni=rut,
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "email": email,
                    "telefono": telefono,
                    "cliente_vip": random.choice([True, False, False, False]),
                    "descuento_vip": Decimal("5.00") if random.random() > 0.7 else Decimal("0.00"),
                    "activo": True,
                },
            )
            result.append(cliente)
        self.stdout.write(f"    ✓ {len(result)} clientes creados/verificados")
        return result

    # ──────────────────────────────────────────
    def _crear_ventas_historicas(self, medicamentos, clientes):
        self.stdout.write("\n  Generando historial de ventas (90 días)...")

        vendedor = User.objects.filter(username="vendedor_demo").first()
        admin = User.objects.filter(username="admin_demo").first()
        if not vendedor:
            vendedor = User.objects.filter(is_staff=True).first()

        hoy = date.today()
        total_ventas = 0
        folio = Boleta.objects.count() + 1000

        # Distribución: más ventas los últimos 30 días
        for dias_atras in range(90, 0, -1):
            fecha_venta = hoy - timedelta(days=dias_atras)
            # Más ventas recientes (realismo)
            num_ventas_dia = random.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                weights=[5, 10, 15, 20, 20, 15, 10, 4, 1]
            )[0]
            if dias_atras > 60:
                num_ventas_dia = max(0, num_ventas_dia - 2)

            for _ in range(num_ventas_dia):
                try:
                    med = random.choice([m for m in medicamentos if m.tipo_venta == "libre" and m.stock > 2])
                    cantidad = random.randint(1, min(5, med.stock))
                    precio_total = med.precio * cantidad
                    metodo = random.choice(METODOS_PAGO)
                    cliente = random.choice(clientes) if random.random() > 0.4 else None

                    # Número de venta único
                    n = Venta.objects.count() + total_ventas + 1
                    numero_venta = f"VT-{fecha_venta.year}-{n:05d}"

                    if Venta.objects.filter(numero_venta=numero_venta).exists():
                        continue

                    # Crear carrito
                    carrito = CarritoVenta.objects.create(
                        vendedor=vendedor,
                        cliente=cliente,
                        estado="COMPLETADO",
                        subtotal=precio_total,
                        base_imponible=precio_total,
                        iva=precio_total * Decimal("0.19"),
                        total=precio_total * Decimal("1.19"),
                        fecha_completacion=timezone.make_aware(
                            datetime.combine(fecha_venta, datetime.min.time().replace(
                                hour=random.randint(9, 19),
                                minute=random.randint(0, 59)
                            ))
                        ),
                    )

                    CarritoItem.objects.create(
                        carrito=carrito,
                        medicamento=med,
                        cantidad=cantidad,
                        precio_unitario=med.precio,
                    )

                    # Boleta
                    folio += 1
                    numero_boleta = f"BV-{fecha_venta.year}-{folio:05d}"
                    boleta = Boleta.objects.create(
                        numero_boleta=numero_boleta,
                        folio=folio,
                        carrito=carrito,
                        rut_farmacia="12.345.678-9",
                        nombre_farmacia="FARMACIA DR. NAHUM",
                        direccion_farmacia="Av. Principal 1234, Santiago",
                        subtotal=precio_total,
                        base_imponible=precio_total,
                        iva=precio_total * Decimal("0.19"),
                        total=precio_total * Decimal("1.19"),
                        metodo_pago=metodo,
                        vendedor=vendedor,
                        estado="EMITIDA",
                        fecha_emision=carrito.fecha_completacion,
                        cliente_nombre=f"{cliente.nombre} {cliente.apellido}" if cliente else "Consumidor Final",
                        cliente_rut=cliente.rut_dni if cliente else None,
                    )

                    # Pago
                    monto_pagado = precio_total * Decimal("1.19")
                    Pago.objects.create(
                        carrito=carrito,
                        boleta=boleta,
                        metodo_pago=metodo,
                        monto=monto_pagado,
                        cambio=Decimal("0"),
                    )

                    # Venta
                    Venta.objects.create(
                        medicamento=med,
                        cantidad=cantidad,
                        precio=precio_total,
                        vendedor=vendedor,
                        cliente=cliente,
                        numero_venta=numero_venta,
                        estado="COMPLETADA",
                        boleta=boleta,
                        fecha=carrito.fecha_completacion,
                    )

                    # Historial stock (no restamos realmente para no agotar)
                    HistorialStock.objects.create(
                        medicamento=med,
                        tipo="VENTA",
                        cantidad=-cantidad,
                        stock_anterior=med.stock + cantidad,
                        stock_posterior=med.stock,
                        usuario=vendedor,
                        motivo=f"Venta {numero_venta}",
                    )

                    total_ventas += 1
                except Exception:
                    continue

        self.stdout.write(f"    ✓ {total_ventas} ventas históricas generadas")

    # ──────────────────────────────────────────
    def _mostrar_credenciales(self):
        self.stdout.write(self.style.SUCCESS("\n╔══════════════════════════════════════════════╗"))
        self.stdout.write(self.style.SUCCESS("║         DEMO LISTA — CREDENCIALES            ║"))
        self.stdout.write(self.style.SUCCESS("╠══════════════════════════════════════════════╣"))
        self.stdout.write(self.style.SUCCESS("║  admin_demo    / Demo2026!  → Admin total    ║"))
        self.stdout.write(self.style.SUCCESS("║  vendedor_demo / Demo2026!  → POS y ventas   ║"))
        self.stdout.write(self.style.SUCCESS("║  gerente_demo  / Demo2026!  → Reportes       ║"))
        self.stdout.write(self.style.SUCCESS("║  contador_demo / Demo2026!  → Finanzas       ║"))
        self.stdout.write(self.style.SUCCESS("╚══════════════════════════════════════════════╝\n"))
