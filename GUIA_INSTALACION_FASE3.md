# FASE 3 - GUÍA DE INSTALACIÓN Y CONFIGURACIÓN

## 📋 Requisitos Previos

- Django 5.0.0
- Python 3.10+
- MySQL 8.0
- pip (gestor de paquetes)

---

## 1️⃣ INSTALAR DEPENDENCIAS

### Paso 1: Actualizar requirements.txt

Ya están incluidos en el archivo:
```
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
reportlab==4.0.7
Pillow==10.1.0
```

### Paso 2: Instalar paquetes

```bash
# Navegar al directorio del proyecto
cd c:\Users\HP SERIES TOUCH\Sistema_FarmaciaC-master

# Instalar todas las dependencias
pip install -r requirements.txt
```

**Output esperado:**
```
Successfully installed pytest-7.4.3 pytest-django-4.7.0 pytest-cov-4.1.0
factory-boy-3.3.0 reportlab-4.0.7 Pillow-10.1.0
```

---

## 2️⃣ EJECUTAR TESTS

### Paso 1: Ejecutar todos los tests

```bash
# Desde el directorio del proyecto
pytest farmacia/tests/ -v --cov=farmacia
```

**Output esperado:**
```
test_utils.py::TestGenerarNumeros::test_generar_numero_venta_formato PASSED
test_utils.py::TestGenerarNumeros::test_generar_numero_venta_incremental PASSED
test_forms.py::TestProcesarPagoV2Form::test_formulario_valido_efectivo PASSED
...
====== 78 passed in 5.23s ======
```

### Paso 2: Generar reporte de coverage

```bash
pytest farmacia/tests/ --cov=farmacia --cov-report=html
```

Esto genera carpeta `htmlcov/` con reporte HTML.

**Para ver el reporte:**
```bash
# Windows
start htmlcov/index.html

# Mac
open htmlcov/index.html

# Linux
firefox htmlcov/index.html
```

### Paso 3: Ejecutar tests específicos (opcional)

```bash
# Solo tests de utils
pytest farmacia/tests/test_utils.py -v

# Solo tests de forms
pytest farmacia/tests/test_forms.py -v

# Solo tests de models
pytest farmacia/tests/test_models.py -v

# Solo tests de views
pytest farmacia/tests/test_views.py -v

# Un test específico
pytest farmacia/tests/test_utils.py::TestGenerarNumeros::test_generar_numero_venta_formato -v
```

---

## 3️⃣ CONFIGURAR PDF GENERATION

### Paso 1: Verificar modelo Boleta

Abrir `farmacia/models.py` y asegurar que Boleta tiene:

```python
class Boleta(models.Model):
    # ... campos existentes ...
    
    # NUEVOS (agregar si no existen):
    archivo_pdf = FileField(
        upload_to='boletas/',
        null=True,
        blank=True,
        help_text='PDF de la boleta generado automáticamente'
    )
    email_enviado = BooleanField(default=False)
    email_destinatario = EmailField(null=True, blank=True)
```

### Paso 2: Crear/Ejecutar migración

```bash
# Si agregaste campos nuevos:
python manage.py makemigrations farmacia

# Aplicar migración
python manage.py migrate farmacia
```

### Paso 3: Probar generación de PDF (en Django shell)

```bash
# Entrar en shell de Django
python manage.py shell

# Dentro del shell:
from farmacia.pdf_generator import generar_pdf_boleta
from farmacia.models import Boleta

# Obtener una boleta existente
boleta = Boleta.objects.first()

# Generar PDF
pdf_buffer = generar_pdf_boleta(boleta)

# Guardar a archivo temporal (para verificar)
with open('boleta_test.pdf', 'wb') as f:
    f.write(pdf_buffer.getvalue())

print("✅ PDF generado: boleta_test.pdf")
```

---

## 4️⃣ CONFIGURAR EMAIL

### Paso 1: Actualizar settings.py

Abrir `collico_sw/settings.py` y agregar:

```python
# ========== EMAIL CONFIGURATION ==========
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Opción 1: Gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Usar variable de entorno
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Opción 2: Office 365 (comentado)
# EMAIL_HOST = 'smtp.office365.com'
# EMAIL_PORT = 587

# Opción 3: Servidor custom
# EMAIL_HOST = os.getenv('EMAIL_HOST')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))

DEFAULT_FROM_EMAIL = 'farmacia@collico.cl'
SERVER_EMAIL = 'noreply@collico.cl'
```

### Paso 2: Configurar variables de entorno

Crear o modificar archivo `.env` en raíz del proyecto:

```ini
# .env
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_o_app_password
```

**Para Gmail con 2FA activado:**
1. Ir a myaccount.google.com/security
2. Crear "Contraseña de aplicación"
3. Usar esa contraseña en EMAIL_HOST_PASSWORD

### Paso 3: Probar conexión email (en Django shell)

```bash
python manage.py shell

from farmacia.email_sender import test_email_connection
if test_email_connection():
    print("✅ Conexión email OK")
else:
    print("❌ Error en conexión email")
```

### Paso 4: Enviar email de prueba

```bash
python manage.py shell

from farmacia.email_sender import enviar_boleta_email
from farmacia.models import Boleta

boleta = Boleta.objects.first()
success = enviar_boleta_email(boleta, 'cliente@example.com')

if success:
    print("✅ Email enviado correctamente")
else:
    print("❌ Error al enviar email")
```

---

## 5️⃣ AGREGAR RUTAS AL PROYECTO

### Paso 1: Actualizar farmacia/urls.py

```python
# Agregar al final del archivo:

from .views_reportes import (
    dashboard_reportes,
    reporte_ventas_diarias,
    reporte_top_productos,
    reporte_vendedores,
    reporte_ingresos,
    descargar_reporte_pdf,
    anular_venta_desde_reporte,
)

urlpatterns = [
    # ... rutas existentes ...
    
    # Nuevas rutas - Dashboard y Reportes
    path('pos/v2/reportes/', dashboard_reportes, name='dashboard_reportes'),
    path('pos/v2/reportes/ventas-diarias/', reporte_ventas_diarias, name='reporte_ventas_diarias'),
    path('pos/v2/reportes/top-productos/', reporte_top_productos, name='reporte_top_productos'),
    path('pos/v2/reportes/vendedores/', reporte_vendedores, name='reporte_vendedores'),
    path('pos/v2/reportes/ingresos/', reporte_ingresos, name='reporte_ingresos'),
    path('pos/v2/reportes/descargar-pdf/', descargar_reporte_pdf, name='descargar_reporte_pdf'),
    path('pos/v2/reportes/anular/<str:numero_venta>/', anular_venta_desde_reporte, name='anular_venta_reporte'),
]
```

### Paso 2: Verificar rutas

```bash
python manage.py show_urls | grep reportes
```

---

## 6️⃣ INTEGRAR PDF EN VISTAS EXISTENTES

### Paso 1: Actualizar vista pos_procesar_pago

En `farmacia/views_pos_v2.py`, agregar en función `pos_procesar_pago()`:

```python
from farmacia.pdf_generator import guardar_pdf_boleta
from farmacia.email_sender import enviar_boleta_email

@transaction.atomic
def pos_procesar_pago(request):
    # ... código existente ...
    
    # Crear boleta
    boleta = Boleta.objects.create(
        carrito=carrito,
        numero_boleta=generar_numero_boleta(),
        folio=generar_folio_boleta(),
        # ... otros campos ...
    )
    
    # ✅ NUEVO: Generar PDF automáticamente
    guardar_pdf_boleta(boleta)
    
    # ✅ OPCIONAL: Enviar email si cliente solicita
    if request.POST.get('enviar_email_boleta') and cliente and cliente.email:
        enviar_boleta_email(boleta, cliente.email)
    
    return redirect('pos_mostrar_boleta', numero_boleta=boleta.numero_boleta)
```

### Paso 2: Actualizar template boleta HTML

En `farmacia/templates/farmacia/base_boleta.html`, agregar botones:

```html
<!-- Botones de acción -->
<div class="botones-boleta">
    <a href="{% url 'descargar_boleta_pdf' numero_boleta=boleta.numero_boleta %}" class="btn btn-success">
        📥 Descargar PDF
    </a>
    
    <button onclick="enviarEmail()" class="btn btn-info">
        📧 Enviar por Email
    </button>
    
    <button onclick="window.print()" class="btn btn-secondary">
        🖨️ Imprimir
    </button>
</div>

<script>
function enviarEmail() {
    const email = prompt("Ingrese email del cliente:");
    if (email) {
        // Llamar a endpoint para enviar
        fetch(`/pos/v2/enviar-boleta/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                numero_boleta: '{{ boleta.numero_boleta }}',
                email: email
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert('✅ Boleta enviada!');
            } else {
                alert('❌ Error: ' + data.error);
            }
        });
    }
}
</script>
```

---

## 7️⃣ CREAR TABLA HISTORIAL STOCK (Si no existe)

```bash
# Verificar si tabla existe
python manage.py shell

from farmacia.models import HistorialStock
print(f"Tabla existe: {HistorialStock}")
```

Si no existe, crear migración:

```bash
python manage.py makemigrations farmacia
python manage.py migrate farmacia
```

---

## 8️⃣ CREAR DATOS DE PRUEBA

```bash
python manage.py shell

from farmacia.tests.factories import (
    UserFactory, MedicamentoFactory, ClienteFactory,
    CarritoVentaFactory, CarritoItemFactory, VentaFactory,
    BouletaFactory
)

# Crear usuario de prueba
usuario = UserFactory(username='supervisor', is_staff=True)
usuario.set_password('testpass123')
usuario.save()

# Crear medicamentos
med1 = MedicamentoFactory(nombre='Ibuprofeno 400mg', precio=5000, stock=100)
med2 = MedicamentoFactory(nombre='Paracetamol 500mg', precio=3000, stock=50)

# Crear cliente
cliente = ClienteFactory(nombre='Juan Pérez', rut='12.345.678-9')

# Crear venta de prueba
venta = VentaFactory(
    medicamento=med1,
    cantidad=2,
    precio=10000,
    vendedor=usuario,
    cliente=cliente
)

# Crear boleta
boleta = BouletaFactory(
    numero_boleta='BV-2026-00001',
    total=11900
)

print("✅ Datos de prueba creados")
```

---

## 9️⃣ INICIAR SERVIDOR Y PROBAR

```bash
# Iniciar servidor de desarrollo
python manage.py runserver

# Acceder a:
# - Terminal POS: http://localhost:8000/pos/v2/
# - Dashboard: http://localhost:8000/pos/v2/reportes/
# - Admin: http://localhost:8000/admin/
```

---

## 🔟 CHECKLIST DE VERIFICACIÓN

- [ ] Dependencias instaladas (pip install -r requirements.txt)
- [ ] Tests ejecutados (pytest farmacia/tests/ -v)
- [ ] Coverage verificado (>80%)
- [ ] Modelo Boleta tiene campos archivo_pdf, email_enviado
- [ ] Migraciones aplicadas (manage.py migrate)
- [ ] Settings.py configurado con EMAIL_*
- [ ] .env creado con credenciales email
- [ ] Conexión email probada
- [ ] Rutas agregadas a farmacia/urls.py
- [ ] Vista pos_procesar_pago integrada con PDF/Email
- [ ] Servidor iniciado sin errores
- [ ] Dashboard accesible en http://localhost:8000/pos/v2/reportes/

---

## ⚠️ TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-django pytest-cov
```

### Error: "No module named 'reportlab'"
```bash
pip install reportlab
```

### Error: "EmailMessage has no attribute 'html_message'"
```bash
# Actualizar Django a 5.0+
pip install --upgrade Django
```

### Tests fallan por BD
```bash
pytest farmacia/tests/ --create-db -v
```

### Email no se envía
```python
# En Django shell:
from farmacia.email_sender import test_email_connection
test_email_connection()  # Verificar resultado
```

### PDF vacío
```python
# Verificar boleta tiene carrito con items:
boleta.carrito.items.count()  # Debe ser > 0
```

---

## 📞 SOPORTE

Si tienes dudas:
1. Revisar documentación en `FASE3_COMPLETADA.md`
2. Ver arquitectura en `ARQUITECTURA_FASE3.md`
3. Ejecutar tests para validar instalación
4. Revisar logs del servidor: `python manage.py runserver`

---

**Status**: ✅ Guía completa - Listo para implementar
