# Auditoría Técnica y Funcional Completa
## Sistema de Gestión Farmacéutica Dr. Nahum

---

**Versión:** 2.0  
**Fecha:** Mayo 2026  
**Tipo:** Auditoría técnica integral — sistema completo  
**Preparado por:** Arquitecto de Software Senior / Auditor Técnico  
**Stack:** Django 6.0 · PostgreSQL · Bootstrap 5 · Railway  
**Clasificación:** Confidencial — uso interno y técnico

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Inventario del Sistema](#2-inventario-del-sistema)
3. [Módulos — Análisis Funcional](#3-módulos--análisis-funcional)
4. [Arquitectura Técnica](#4-arquitectura-técnica)
5. [Base de Datos y Modelos](#5-base-de-datos-y-modelos)
6. [Seguridad — Auditoría Completa](#6-seguridad--auditoría-completa)
7. [UX/UI y Experiencia de Usuario](#7-uxui-y-experiencia-de-usuario)
8. [Rendimiento y Escalabilidad](#8-rendimiento-y-escalabilidad)
9. [Automatizaciones](#9-automatizaciones)
10. [Problemas Críticos Identificados](#10-problemas-críticos-identificados)
11. [Comparativa con Sistemas Modernos](#11-comparativa-con-sistemas-modernos)
12. [Roadmap de Evolución — 5 Fases](#12-roadmap-de-evolución--5-fases)
13. [Conclusiones y Recomendaciones](#13-conclusiones-y-recomendaciones)

---

## 1. Resumen Ejecutivo

### 1.1 Evaluación general

El Sistema de Gestión Farmacéutica Dr. Nahum es una aplicación web Django desplegada en Railway con base de datos PostgreSQL. El sistema cubre las operaciones core de una farmacia pequeña a mediana: punto de venta, inventario, control de recetas, proveedores y auditoría.

### 1.2 Scorecard del sistema

| Área | Puntuación | Estado |
|------|-----------|--------|
| Modelo de datos | 8/10 | Sólido con mejoras menores |
| Lógica de negocio | 7/10 | Correcta, algunos gaps |
| Seguridad | 7/10 | Base buena, reforzar |
| Rendimiento | 5/10 | Limitado, 1 worker |
| UX/UI | 6/10 | Funcional, mejorable |
| Cobertura funcional | 6/10 | Módulos core OK, faltan extras |
| Documentación | 7/10 | Bien documentado |
| Escalabilidad | 4/10 | Preparación inicial |
| Integraciones | 2/10 | Pendientes |
| **TOTAL** | **6.2/10** | **Sistema viable y en producción** |

### 1.3 Hallazgos principales

**Críticos (resolver urgente):**
- Modelo `Venta` guarda solo 1 medicamento (limita reportes)
- Email configurado en modo consola (no envía en producción)
- Sin exportación de reportes (solo pantalla)
- Sin facturación electrónica (SII Chile)

**Importantes (resolver en próximas versiones):**
- Dashboard con métricas limitadas
- POS requiere múltiples navegaciones para completar una venta
- Sin gestión de caja/turno
- Sin límite máximo de descuento por rol

**Oportunidades de mejora:**
- Integración WebPay/Mercado Pago
- WhatsApp para boletas y recordatorios
- CRM con seguimiento de clientes crónicos
- App móvil / PWA

---

## 2. Inventario del Sistema

### 2.1 Mapa completo de componentes

```
Sistema Farmacia Dr. Nahum
├── sistema_farmacia/               Configuración Django
│   ├── settings.py                 Desarrollo (SQLite + Redis)
│   ├── settings_prod.py            Producción (PostgreSQL + Railway)
│   ├── urls.py                     URLs raíz (admin + farmacia)
│   ├── wsgi.py                     WSGI + healthcheck bypass
│   └── asgi.py                     ASGI (no usado actualmente)
│
├── farmacia/                       App principal
│   ├── models.py                   18 modelos
│   ├── views.py                    20+ vistas generales
│   ├── views_pos_v2.py             13 vistas del POS
│   ├── urls.py                     40+ rutas URL
│   ├── forms.py                    12 formularios
│   ├── middleware.py               VerificacionRolMiddleware
│   ├── backends.py                 CustomUserBackend
│   ├── permissions.py              6 decoradores de permisos
│   ├── pdf_generator.py            Generador de PDF con ReportLab
│   ├── email_utils.py              Envío de emails
│   ├── email_sender.py             Adjunto PDF por email
│   ├── utils.py                    Funciones auxiliares
│   │
│   ├── templates/farmacia/         42 templates HTML
│   │   ├── base_generic.html       Template base (nav, sidebar)
│   │   ├── inicio_sesion.html      Login
│   │   ├── registro_usuario.html   Registro
│   │   ├── farmacia_main.html      Menú principal
│   │   ├── dashboard.html          Dashboard ventas
│   │   ├── dashboard_inventario.html Dashboard inventario
│   │   ├── [medicamento_*.html]    4 templates
│   │   ├── [proveedor_*.html]      4 templates
│   │   ├── [clientes_*.html]       2 templates
│   │   ├── [ventas_*.html]         2 templates
│   │   ├── [reporte_*.html]        3 templates
│   │   ├── [auditoria_*.html]      2 templates
│   │   ├── gestor_lotes.html       Gestión de lotes
│   │   ├── reporte_lotes.html      Reporte de vencimientos
│   │   ├── pos_v2/                 8 templates del POS
│   │   └── email/                  2 templates de email
│   │
│   ├── static/css/style.css        Estilos personalizados
│   ├── migrations/                 19 migraciones
│   └── tests/                      Suite de pruebas (factories)
│
├── static/                         Archivos estáticos globales
├── screenshots/                    32 capturas del sistema
├── docs/                           Documentación
└── scripts/                        Scripts utilitarios
```

### 2.2 Inventario de URLs (40 rutas)

| Grupo | Cantidad | Ejemplos |
|-------|---------|---------|
| Autenticación | 4 | login, registro, logout, accounts/ |
| Dashboard y reportes | 6 | dashboard, dashboard_inventario, reportes |
| POS v2 | 13 | terminal, agregar, pago, boleta, anular |
| Medicamentos CRUD | 5 | list, detail, create, update, delete |
| Proveedores CRUD | 5 | list, detail, create, update, delete |
| Clientes | 2 | list, detail |
| Inventario/Lotes | 3 | dashboard_inventario, gestor_lotes, reporte_lotes |
| Auditoría | 2 | auditoria, auditoria_usuario |
| Admin Django | 1 | gestion-interna-nahum/ (URL oculta) |

---

## 3. Módulos — Análisis Funcional

### 3.1 Módulo de Autenticación y Acceso

**Estado:** ✅ Operativo

```
Usuario accede al sistema
    │
    ├── Login (email o username, case-insensitive)
    │       CustomUserBackend: Q(username=x) | Q(email=x)
    │       Redirección → farmacia_main
    │
    ├── Registro (username, email único, celular)
    │       Auto-login después del registro
    │       Sin verificación de email (riesgo)
    │
    └── Logout → redirige a login
```

**Fortalezas:**
- Login con email O username (flexibilidad)
- Backend personalizado bien implementado
- URLs de auth de Django incluidas (`/accounts/`)

**Problemas:**
- Sin verificación de email al registrarse
- Registro público — cualquiera puede crear cuenta
- Sin límite de intentos de login (brute force)
- Sin 2FA (autenticación de dos factores)
- Sin recuperación de contraseña configurada

---

### 3.2 Módulo POS v2 — Punto de Venta

**Estado:** ✅ Operativo — Módulo más completo del sistema

```
VISTAS (13):                    TEMPLATES (8):
terminal_pos_v2                 terminal_pos_v2.html
pos_agregar_item                procesar_pago_v2.html
pos_agregar_por_codigo_barras   seleccionar_cliente_v2.html
pos_eliminar_item               aplicar_descuento.html
pos_vaciar_carrito              boleta.html
pos_aplicar_descuento           anular_venta.html
pos_seleccionar_cliente         procesar_devolucion.html
pos_procesar_pago               historial_ventas.html
pos_mostrar_boleta
pos_anular_venta
pos_procesar_devolucion
pos_historial_ventas
```

**Flujo de venta completo:**

```
[1] Terminal POS
     ↓ Buscar / Escanear código
[2] Validación backend (stock + receta)
     ↓ OK
[3] Carrito (agregar, modificar, eliminar)
     ↓ (página separada) Cliente opcional
     ↓ (página separada) Descuento opcional
[4] Proceso de pago
     ↓ Transacción atómica
[5] Boleta emitida → Email + impresión
```

**Funcionalidades implementadas:**

| Funcionalidad | Estado |
|--------------|--------|
| Búsqueda por nombre/SKU | ✅ |
| Búsqueda por código de barras | ✅ |
| Carrito persistente (BD) | ✅ |
| Validación stock en tiempo real | ✅ |
| Control de recetas (4 tipos) | ✅ |
| Descuento por % o monto | ✅ |
| Selección de cliente | ✅ |
| Pago efectivo/débito/crédito/transferencia | ✅ |
| Cálculo de vuelto | ✅ |
| Generación de boleta PDF | ✅ |
| Envío boleta por email | ✅ (consola) |
| Anulación de venta | ✅ (solo staff) |
| Devolución parcial | ✅ |
| Historial con filtros | ✅ |
| Nota de crédito automática | ✅ |

**Problemas del POS:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Flujo multi-página (cliente, descuento en páginas separadas) | Alto |
| 2 | Sin botones +/- para cantidad (solo input manual) | Medio |
| 3 | Sin total por ítem visible en el carrito | Medio |
| 4 | Sin confirmación visual antes de cobrar | Medio |
| 5 | Sin gestión de turno/caja | Alto |
| 6 | Sin descuento máximo configurable por rol | Alto |
| 7 | Email no funciona en producción (backend consola) | Crítico |

---

### 3.3 Módulo de Inventario y Medicamentos

**Estado:** ✅ Operativo

```
Medicamento
├── CRUD completo (crear, ver, editar, eliminar)
├── Clasificación: libre / receta_simple / receta_retenida / controlado
├── Niveles de stock: Bajo (<100) / Medio (100-700) / Alto (>700)
├── Validación fecha_vencimiento > fecha_ingreso
└── Vinculación a proveedor (PROTECT — no elimina si tiene meds)

LoteMedicamento (Trazabilidad)
├── Por lote con fecha vencimiento
├── FIFO: ordenados por fecha_vencimiento ASC
├── Alertas: vencido / próximo a vencer (configurable, default 30 días)
└── Vinculación a venta (trazabilidad legal)

HistorialStock (Auditoría)
├── Tipo: VENTA / AJUSTE / INGRESO / DEVOLUCION
├── Cantidad (puede ser negativa para egresos)
├── Stock anterior y posterior (snapshot)
└── Usuario responsable + timestamp
```

**Vistas de inventario:**

| Vista | Función |
|-------|---------|
| `MedicamentoListView` | Lista con filtros por tipo_venta, KPIs |
| `MedicamentoDetailView` | Detalle con lotes y historial |
| `MedicamentoCreateView` | Alta con validaciones |
| `MedicamentoUpdateView` | Edición |
| `MedicamentoDeleteView` | Eliminación con confirmación |
| `dashboard_inventario` | Alertas: vencimientos (<7 días), agotados |
| `gestor_lotes` | Vista visual de lotes activos |
| `reporte_lotes` | Reporte completo por estado de lote |

**Problemas del inventario:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Nivel de stock hardcodeado (<100 "Bajo", >700 "Alto") | Medio |
| 2 | Sin ajuste masivo de precios | Medio |
| 3 | Sin carga masiva de medicamentos (Excel/CSV) | Alto |
| 4 | Sin historial de precio (¿cuánto costaba hace 6 meses?) | Bajo |
| 5 | Sin alertas automáticas por email cuando stock bajo | Alto |
| 6 | `nivel_stock` calculado al guardar, pero el campo en BD puede desincronizarse | Medio |

---

### 3.4 Módulo de Proveedores

**Estado:** ✅ Operativo básico

```
Proveedor
├── CRUD completo
├── Validación RUT chileno (formato XX.XXX.XXX-X)
├── Email único por proveedor
└── Vinculado a Medicamento (PROTECT)
```

**Problemas:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Sin historial de compras por proveedor | Alto |
| 2 | Sin módulo de órdenes de compra | Alto |
| 3 | Sin comparativo de precios entre proveedores | Medio |
| 4 | Campo `productos` es TextField libre (sin estructura) | Bajo |

---

### 3.5 Módulo de Clientes

**Estado:** ⚠️ Parcialmente implementado

**Modelos:**
- `Cliente` con campos médicos (alergias, medicamentos_contraindicados)
- `cliente_vip` con `descuento_vip`
- Historial de compras calculado dinámicamente

**Vistas disponibles:** solo `clientes_list` y `cliente_detail`

**Problemas:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Sin CRUD completo (no se puede crear/editar desde la web) | Alto |
| 2 | Sin búsqueda avanzada de clientes | Medio |
| 3 | Sin historial de compras en la vista de detalle | Alto |
| 4 | Descuento VIP existe en el modelo pero no se aplica automáticamente en el POS | Alto |
| 5 | Sin comunicaciones al cliente (email, WhatsApp) | Medio |

---

### 3.6 Módulo de Reportes

**Estado:** ⚠️ Básico, sin exportación

**Templates disponibles:**
- `dashboard.html` — ventas del día/semana/mes/año
- `dashboard_inventario.html` — alertas de vencimiento
- `reporte_global.html` — vista general
- `reporte_finanzas.html` — datos financieros
- `reporte_personal.html` — por vendedor
- `reporte_lotes.html` — estado de lotes
- `historial_ventas.html` — historial del POS

**Dashboard de ventas (caché 1 hora):**
```python
# Métricas calculadas:
- stock_vendido: suma cantidad vendida
- total_ventas: conteo de ventas
- monto_total: suma de precios
- ventas_semana: ventas últimos 7 días
- ventas_mes: ventas últimos 30 días
- ventas_año: ventas últimos 365 días
```

**Problemas:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Sin exportación a Excel | Crítico |
| 2 | Sin exportación a PDF de reportes | Alto |
| 3 | Dashboard no muestra gráficos (solo números) | Alto |
| 4 | Sin ranking de productos más vendidos | Medio |
| 5 | Sin reporte de rentabilidad (precio venta vs costo lote) | Alto |
| 6 | Sin reporte de flujo de caja diario | Alto |
| 7 | Filtros de reporte limitados | Medio |

---

### 3.7 Módulo de Auditoría

**Estado:** ✅ Bien implementado

```
AuditoriaLog
├── Acciones: CREAR, EDITAR, ELIMINAR, VER, EXPORTAR
│             INTENTOFALLIDO, ACCESODENEGADO
├── IP del usuario registrada
├── Resultado (éxito/fallo)
└── Timestamp inmutable

AuditoriaReceta (ISP)
├── Eventos específicos de recetas
├── Inmutable (sin edición permitida)
└── Cumplimiento normativa controlados

VerificacionRolMiddleware
└── Protege rutas admin automáticamente
    → 403 si rol incorrecto
    → 401 si no autenticado
    → Log automático en AuditoriaLog
```

**Fortalezas:**
- Cobertura completa de acciones sensibles
- IP registrada para trazabilidad
- Log de recetas separado (cumplimiento ISP)

**Mejoras:**
- Sin retención automática de logs por X días
- Sin exportación del log de auditoría
- Sin alertas ante patrones sospechosos

---

### 3.8 Módulo de Usuarios y Roles

**Estado:** ✅ Operativo

```
Roles disponibles:
├── ADMIN — Acceso total
├── GERENTE — Reportes globales, aprueba devoluciones
├── CONTADOR — Solo lectura financiera
└── VENDEDOR — POS + historial propio

Decoradores de permisos:
├── @requiere_rol(rol)
├── @requiere_vendedor_o_admin()
├── @solo_admin()
├── @puede_editar_venta()
├── @requiere_gerente_o_admin()
└── @requiere_contador_o_admin()
```

**Problemas:**

| # | Problema | Impacto |
|---|---------|---------|
| 1 | Registro público sin aprobación de admin | Alto (seguridad) |
| 2 | Sin gestión de usuarios desde interfaz web (solo Django admin) | Alto |
| 3 | Sin asignación masiva de roles | Bajo |
| 4 | Sin 2FA para administradores | Alto (seguridad) |

---

### 3.9 Módulo de Recetas Médicas

**Estado:** ✅ Bien implementado (cumplimiento ISP)

```
Tipos:
├── simple          → Receta sin retención
├── retenida        → Receta retenida físicamente
└── controlada      → Retención + archivo digital obligatorio

Validaciones:
├── Vigencia: 30 días por defecto
├── Backend bloqueante (no se puede saltar)
└── AuditoriaReceta inmutable por cada evento

Eventos auditados:
├── RECETA_REGISTRADA
├── RECETA_VERIFICADA
├── VENTA_BLOQUEADA (intento sin receta)
├── VENTA_CON_RECETA
└── RECETA_RETENIDA
```

**Problemas:**
- Sin vista dedicada para gestionar recetas fuera del POS
- Sin alerta cuando una receta está próxima a vencer
- Sin reporte mensual de recetas para ISP

---

## 4. Arquitectura Técnica

### 4.1 Arquitectura actual

```
Internet
    │ HTTPS
    ▼
Railway Edge (CDN + proxy)
    │ HTTP
    ▼
WSGI Handler (wsgi.py)
├── Bypass healthcheck → 200 OK (sin pasar por Django)
└── Resto → Django application
    │
    ▼
Django Middleware Stack:
1. SecurityMiddleware
2. WhiteNoiseMiddleware       ← Archivos estáticos
3. LocaleMiddleware           ← i18n español
4. SessionMiddleware
5. CommonMiddleware
6. CsrfViewMiddleware
7. AuthenticationMiddleware
8. MessageMiddleware
9. XFrameOptionsMiddleware
10. VerificacionRolMiddleware  ← Custom: protege rutas admin
    │
    ▼
Django Views
├── views.py              (funciones + class-based)
├── views_pos_v2.py       (funciones POS)
└── sistema_farmacia/     (admin Django)
    │
    ▼
Django ORM
    │
    ▼
PostgreSQL (Railway managed)
├── 18+ tablas
├── Índices optimizados
└── Backups automáticos Railway
```

### 4.2 Flujo de una request completa

```
1. Browser envía POST /pos/pago/
2. Railway termina TLS, reenvía HTTP
3. wsgi.py: no es healthcheck → pasa a Django
4. SecurityMiddleware: headers de seguridad
5. WhiteNoise: no es estático → siguiente
6. SessionMiddleware: carga sesión
7. CsrfViewMiddleware: valida token
8. AuthenticationMiddleware: carga usuario
9. VerificacionRolMiddleware: ¿ruta protegida? no → siguiente
10. Django URL router: → pos_procesar_pago view
11. @login_required: ¿autenticado? sí → continúa
12. View: valida stock (re-check), procesa pago
13. @transaction.atomic: BD operations
14. ORM → PostgreSQL: INSERT/UPDATE múltiples tablas
15. Response: redirect a boleta
```

### 4.3 Patrones de código detectados

| Patrón | Uso | Evaluación |
|--------|-----|-----------|
| Class-Based Views | CRUD Medicamento, Proveedor | ✅ Bien usado |
| Function-Based Views | POS, dashboard, reportes | ✅ Correcto para lógica compleja |
| `@transaction.atomic` | Proceso de pago | ✅ Correcto |
| `@cache_page(3600)` | Dashboard | ✅ Reduce carga BD |
| `LoginRequiredMixin` | Todas las vistas de datos | ✅ |
| Custom decorators | Permisos por rol | ✅ Bien diseñado |
| ORM annotations | Cálculos en QuerySet | ⚠️ Algunos en Python (más lento) |
| `F()` expressions | Algunas consultas | ⚠️ No usado en stock deduction |
| `select_related` | No detectado | ❌ Riesgo N+1 queries |
| `prefetch_related` | No detectado | ❌ Riesgo N+1 queries |

### 4.4 Problemas técnicos detectados

```python
# PROBLEMA 1: N+1 queries en historial de ventas
# Cada venta → query separada para medicamento, vendedor, cliente
ventas = Venta.objects.filter(...)  # sin select_related

# FIX:
ventas = Venta.objects.filter(...).select_related(
    'medicamento', 'vendedor', 'cliente', 'boleta'
)

# PROBLEMA 2: Stock deduction sin SELECT FOR UPDATE
# (race condition con ventas simultáneas)
medicamento.stock -= cantidad
medicamento.save()

# FIX:
from django.db import F
Medicamento.objects.filter(id=medicamento.id, stock__gte=cantidad).update(
    stock=F('stock') - cantidad
)

# PROBLEMA 3: Caché de dashboard con datos obsoletos
@cache_page(3600)  # 1 hora — puede mostrar datos viejos
def dashboard(request):
    ...

# FIX: Caché por clave dinámica con invalidación en ventas
cache.set(f'dashboard_{fecha_hoy}', data, 300)  # 5 min
```

---

## 5. Base de Datos y Modelos

### 5.1 Diagrama ERD completo

```
auth_User (Django built-in)
    │ 1:1
    ├──→ RolPermiso (rol, estado_activo)
    │
    │ 1:N
    ├──→ CarritoVenta ←──────────── Cliente (rut_dni, vip, descuento_vip)
    │       │                           │
    │       │ 1:N                       │ 1:N
    │       ├──→ CarritoItem            └──→ Venta
    │       │       │ N:1
    │       │       └──→ Medicamento ←──── Proveedor
    │       │               │ 1:N
    │       │               └──→ LoteMedicamento
    │       │               │ 1:N
    │       │               └──→ HistorialStock
    │       │
    │       │ 1:1
    │       ├──→ Boleta
    │       │       │ 1:N
    │       │       └──→ NotaCredito
    │       │
    │       │ 1:1
    │       └──→ Pago
    │
    │ 1:N
    ├──→ Venta ──→ Medicamento, Lote, Cliente, Boleta, Receta
    │
    │ 1:N
    └──→ AuditoriaLog

Receta (tipo, estado, rut_medico, rut_paciente)
    │ 1:N
    └──→ AuditoriaReceta (eventos ISP)
    │ 1:1
    ├──→ Venta
    └──→ CarritoItem

Devolucion → Venta, Medicamento, Lote
```

### 5.2 Inventario de modelos (18 modelos)

| Modelo | Tabla | Propósito | Estado |
|--------|-------|-----------|--------|
| Medicamento | farmacia_medicamento | Catálogo de productos | ✅ |
| Proveedor | farmacia_proveedor | Proveedores | ✅ |
| LoteMedicamento | farmacia_lotemedicamento | Lotes FIFO | ✅ |
| HistorialStock | farmacia_historialstock | Trazabilidad stock | ✅ |
| Cliente | farmacia_cliente | Clientes | ✅ |
| Devolucion | farmacia_devolucion | Devoluciones | ✅ |
| CarritoVenta | farmacia_carritoventa | Carrito POS | ✅ |
| CarritoItem | farmacia_carritoitem | Ítems carrito | ✅ |
| Boleta | farmacia_boleta | Documento fiscal | ✅ |
| Pago | farmacia_pago | Registro de pago | ✅ |
| NotaCredito | farmacia_notacredito | Anulaciones/devoluciones | ✅ |
| Venta | farmacia_venta | Venta completada | ⚠️ Ver nota |
| DetalleVenta | farmacia_detalleventa | Líneas de venta | ⚠️ Subutilizado |
| RolPermiso | farmacia_rolpermiso | Roles por usuario | ✅ |
| AuditoriaLog | farmacia_auditorialog | Log general | ✅ |
| Receta | farmacia_receta | Recetas médicas | ✅ |
| AuditoriaReceta | farmacia_auditoriareceta | Log ISP | ✅ |
| ConfiguracionFarmacia | farmacia_configuracion | Datos farmacia | ✅ |

**Nota sobre Venta:** El modelo `Venta` está diseñado para UN medicamento por registro. El carrito maneja múltiples productos, pero `Venta` solo registra el primero. `DetalleVenta` existe para múltiples líneas pero no se usa en el POS v2.

### 5.3 Índices PostgreSQL existentes y recomendados

```sql
-- EXISTENTES (bien configurados)
farmacia_venta: numero_venta, (vendedor_id, fecha), estado, fecha
farmacia_boleta: numero_boleta, folio, (vendedor_id, fecha_emision), estado
farmacia_historialstock: fecha_creacion, (med_id, fecha), (user_id, fecha), tipo
farmacia_auditorialog: timestamp, (usuario_id, timestamp), (accion, timestamp)
farmacia_lotemedicamento: fecha_vencimiento
farmacia_cliente: rut_dni, email
farmacia_receta: (tipo, estado), rut_paciente, fecha_emision

-- RECOMENDADOS (agregar)
-- Para búsqueda en POS
CREATE INDEX CONCURRENTLY idx_med_nombre ON farmacia_medicamento 
    USING gin(to_tsvector('spanish', nombre));

-- Para reportes de ventas por período
CREATE INDEX CONCURRENTLY idx_venta_fecha_vendedor ON farmacia_venta 
    (fecha DESC, vendedor_id) WHERE estado = 'COMPLETADA';

-- Para carrito activo
CREATE INDEX CONCURRENTLY idx_carrito_activo ON farmacia_carritoventa 
    (vendedor_id) WHERE estado = 'EN_CONSTRUCCION';
```

### 5.4 Problemas estructurales

| # | Problema | Tabla | Solución |
|---|---------|-------|---------|
| 1 | `Venta` = 1 medicamento | farmacia_venta | Usar VentaCabecera + VentaDetalle |
| 2 | `precio` en Venta = total (no unitario) | farmacia_venta | Renombrar + agregar precio_unitario |
| 3 | `ConfiguracionFarmacia` tiene datos hardcodeados en views | views_pos_v2.py | Leer siempre de BD |
| 4 | `nivel_stock` en Medicamento puede desincronizarse | farmacia_medicamento | Calcularlo siempre con property |
| 5 | Dos tablas de email (emails/ y email/) | templates | Consolidar en una |
| 6 | Sin tabla de `TurnoCaja` / `AperturaConteo` | — | Agregar para control de caja |

---

## 6. Seguridad — Auditoría Completa

### 6.1 Protecciones activas

| Vulnerabilidad | Estado | Implementación |
|---------------|--------|---------------|
| SQL Injection | ✅ Protegido | ORM Django (no raw SQL) |
| XSS | ✅ Protegido | Auto-escape en templates |
| CSRF | ✅ Protegido | Middleware CSRF + tokens |
| Clickjacking | ✅ Protegido | XFrameOptionsMiddleware |
| Session hijacking | ✅ Protegido | SESSION_COOKIE_SECURE=True en prod |
| HTTPS forzado | ✅ | Railway edge + SECURE_PROXY_SSL_HEADER |
| Secretos expuestos | ✅ | Variables de entorno (.env no en git) |
| Admin URL oculta | ✅ | URL configurable por variable de entorno |
| Permisos por rol | ✅ | RolPermiso + decoradores |
| Auditoría de accesos | ✅ | AuditoriaLog completo |
| Log de recetas ISP | ✅ | AuditoriaReceta inmutable |

### 6.2 Vulnerabilidades identificadas

#### ALTA PRIORIDAD

```
[VULN-001] Registro público sin restricción
Descripción: Cualquier persona puede registrarse en el sistema
Riesgo: Un atacante puede crear cuentas falsas
Solución: Deshabilitar registro público o requerir invitación de admin

[VULN-002] Sin rate limiting en login
Descripción: Intentos de login ilimitados
Riesgo: Ataques de fuerza bruta
Solución: 
    from django.core.cache import cache
    def login_rate_limit(request):
        ip = get_client_ip(request)
        key = f"login_attempts_{ip}"
        attempts = cache.get(key, 0)
        if attempts >= 5:
            return HttpResponse("Demasiados intentos", status=429)
        cache.set(key, attempts + 1, 300)  # 5 min

[VULN-003] Race condition en stock
Descripción: Dos ventas simultáneas pueden dejar stock negativo
Riesgo: Inconsistencia de datos bajo carga
Solución: SELECT FOR UPDATE en transacción atómica
    with transaction.atomic():
        med = Medicamento.objects.select_for_update().get(id=med_id)
        if med.stock < cantidad:
            raise ValidationError("Stock insuficiente")
        med.stock -= cantidad
        med.save()

[VULN-004] Sin límite de descuento
Descripción: Un vendedor puede aplicar 100% de descuento
Riesgo: Fraude interno / pérdida económica
Solución: Configurar límite por rol en RolPermiso
```

#### MEDIA PRIORIDAD

```
[VULN-005] Sin 2FA para administradores
Solución: django-otp o django-two-factor-auth

[VULN-006] Sin expiración de sesión
Solución: SESSION_COOKIE_AGE = 28800  # 8 horas

[VULN-007] Sin verificación de email en registro
Solución: Agregar token de verificación por email

[VULN-008] Archivos de receta sin validación de tipo
Descripción: FileField no valida que sea imagen/PDF
Solución: Validar extensión y magic bytes en clean()
```

### 6.3 Hardening recomendado

```python
# En settings_prod.py — agregar:

# Sesión
SESSION_COOKIE_AGE = 28800        # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# HSTS
SECURE_HSTS_SECONDS = 31536000    # ya configurado ✅
SECURE_HSTS_PRELOAD = True        # agregar

# Content Security Policy
CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "cdn.jsdelivr.net"],
    'style-src': ["'self'", "cdn.jsdelivr.net"],
}

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions Policy
PERMISSIONS_POLICY = {
    'camera': [],
    'microphone': [],
    'geolocation': [],
}
```

---

## 7. UX/UI y Experiencia de Usuario

### 7.1 Inventario de templates (42 archivos)

| Sección | Templates | Estado UX |
|---------|-----------|-----------|
| Auth | 2 | ✅ Moderno (split-screen) |
| Base | 2 | ✅ Responsive, drawer móvil |
| Dashboard | 2 | ⚠️ Sin gráficos |
| Medicamentos | 4 | ✅ Funcional |
| Proveedores | 4 | ✅ Funcional |
| POS v2 | 8 | ⚠️ Multi-pantalla |
| Reportes | 5 | ⚠️ Sin export |
| Inventario/Lotes | 2 | ✅ Claro |
| Clientes | 2 | ⚠️ Solo lectura |
| Auditoría | 2 | ✅ Funcional |
| Email | 2 | ✅ Bien diseñado |
| Ventas | 2 | ⚠️ Básico |

### 7.2 Problemas UX identificados

| # | Pantalla | Problema | Impacto |
|---|---------|---------|---------|
| 1 | POS Terminal | Cliente y descuento en páginas separadas | Alto |
| 2 | POS Terminal | Sin botones +/− cantidad | Medio |
| 3 | POS Historial | Sin búsqueda por número de venta | Alto |
| 4 | Dashboard | Solo texto, sin gráficos visuales | Alto |
| 5 | Medicamentos | Sin búsqueda en tiempo real | Medio |
| 6 | General | Menú principal demasiado plano | Bajo |
| 7 | Boleta | Sin opción directa a WhatsApp | Medio |
| 8 | Clientes | Sin poder crear/editar desde web | Alto |

### 7.3 POS mejorado — propuesta de diseño

```
┌──────────────────────────────────────────────────────────────────────────┐
│  FARMACIA DR. NAHUM — POS v3                    👤 vendedor  🚪 Salir    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────┐  ┌─────────────────────────────────┐│
│  │  🔍 Buscar medicamento...      │  │  CARRITO                         ││
│  │  [Nombre / SKU / Lab      ]    │  │  ─────────────────────────────  ││
│  │  [📷 Escanear código]          │  │  Amoxicilina 500mg              ││
│  │                                │  │  − 2 +    $3.500/u   $7.000  ✕  ││
│  │  RESULTADOS:                   │  │  Paracetamol 1g                 ││
│  │  ─────────────────────────     │  │  − 1 +    $890/u      $890   ✕  ││
│  │  Amoxicilina 500mg             │  │  ─────────────────────────────  ││
│  │  Laboratorio: Chile            │  │                                  ││
│  │  Stock: 45u   $3.500/u  [+]    │  │  Cliente: [🔍 RUT o nombre...]  ││
│  │                                │  │                                  ││
│  │  Paracetamol 1g                │  │  Descuento: [  0  ] %  o  [$  ] ││
│  │  Stock: 120u  $890/u    [+]    │  │                                  ││
│  │                                │  │  Subtotal:            $7.890     ││
│  │  Ibuprofeno 400mg              │  │  IVA 19%:             $1.499     ││
│  │  Stock: 8u    $1.200/u  [+]    │  │  TOTAL:               $9.389     ││
│  │  ⚠️ Stock bajo                 │  │                                  ││
│  │                                │  │  Pago: [Efectivo ▼]              ││
│  │                                │  │  Monto: [$___________]           ││
│  │                                │  │  Vuelto: $611                    ││
│  │                                │  │                                  ││
│  │                                │  │  [        💰 COBRAR        ]     ││
│  └────────────────────────────────┘  └─────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Dashboard mejorado — propuesta

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DASHBOARD — Hoy: 16 Mayo 2026                    ← Semana  Mes  Año →  │
├─────────────┬─────────────┬──────────────┬───────────────────────────────┤
│ Ventas Hoy  │ Total $      │ Unidades     │ Boletas emitidas              │
│   $125.890  │  $2.156.000 │   847 uds    │    156                        │
│  ↑ 12% ayer │ ↑ 8% mes    │              │                               │
├─────────────┴─────────────┴──────────────┴───────────────────────────────┤
│                        VENTAS ÚLTIMOS 7 DÍAS                             │
│  █████▄▃▅▇█▆                                                             │
│  L  M  X  J  V  S  D                                                     │
├──────────────────────────────┬───────────────────────────────────────────┤
│  TOP 5 PRODUCTOS HOY         │  ALERTAS                                  │
│  1. Paracetamol 500mg  x145  │  ⚠️ 3 medicamentos con stock bajo         │
│  2. Amoxicilina 500mg   x89  │  🔴 2 lotes vencen en 5 días              │
│  3. Ibuprofeno 400mg    x67  │  📧 12 boletas pendientes de email         │
│  4. Loratadina 10mg     x45  │                                           │
│  5. Omeprazol 20mg      x38  │                                           │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 8. Rendimiento y Escalabilidad

### 8.1 Configuración actual

| Parámetro | Valor actual | Recomendado |
|-----------|-------------|------------|
| Gunicorn workers | 1 | CPU_COUNT × 2 + 1 |
| Worker timeout | 120s | 30s |
| Database connections | conn_max_age=600 | Mantener |
| Caché | LocMemCache | Redis |
| Sesiones | Base de datos | Redis |
| Archivos estáticos | WhiteNoise | CDN en producción |

### 8.2 Cuellos de botella identificados

```
PROBLEMA: 1 solo worker Gunicorn
IMPACTO: Con más de 1 usuario simultáneo, las requests hacen cola
SOLUCIÓN:
    # railway.toml
    startCommand = "... gunicorn ... --workers 3 --timeout 30"

PROBLEMA: Caché en memoria (LocMemCache)
IMPACTO: Se pierde al reiniciar el server; no compartida entre workers
SOLUCIÓN: 
    # requirements.txt: django-redis
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL', 'redis://...'),
        }
    }

PROBLEMA: N+1 queries probables en historial de ventas
IMPACTO: 100 ventas = 100+ queries a BD
SOLUCIÓN:
    Venta.objects.all().select_related('medicamento', 'vendedor', 'cliente')

PROBLEMA: Sin paginación en catálogo de medicamentos
IMPACTO: Con 500+ medicamentos, carga lenta
SOLUCIÓN: Paginator(queryset, 25) o infinite scroll con AJAX
```

### 8.3 Estimación de capacidad actual

| Escenario | Capacidad estimada |
|-----------|-------------------|
| Usuarios concurrentes | 2-3 (1 worker) |
| Ventas por hora | 50-100 |
| Medicamentos en catálogo | Sin límite práctico |
| Historial de ventas | Sin límite (paginado) |
| Tamaño de BD estimado a 1 año | 50-200 MB |

### 8.4 Plan de escalabilidad

```
CORTO PLAZO (sin cambiar infraestructura):
├── 3 workers Gunicorn
├── select_related en queries clave
└── Redis para caché + sesiones

MEDIANO PLAZO:
├── CDN para archivos estáticos (Cloudflare free)
├── PostgreSQL connection pooling (PgBouncer)
└── Búsqueda full-text con índice GIN

LARGO PLAZO:
├── Celery + Redis para tasks asíncronas (email, reportes)
├── Read replica PostgreSQL
└── Multi-tenant para multi-sucursal
```

---

## 9. Automatizaciones

### 9.1 Oportunidades detectadas

| Automatización | Valor | Complejidad |
|---------------|-------|------------|
| Email de boleta (ya existe, no funciona) | Alto | Baja |
| Alerta email stock bajo | Alto | Baja |
| Alerta email medicamentos próximos a vencer | Alto | Baja |
| Reporte diario automático al dueño | Medio | Media |
| WhatsApp boleta al cliente | Alto | Media |
| Recordatorio medicamentos crónicos | Medio | Media |
| Backup automático de datos | Alto | Baja |
| Facturación electrónica SII | Crítico | Alta |

### 9.2 Implementación de alertas automáticas

```python
# Con Celery (recomendado) o con management commands:

# management/commands/alertas_stock.py
from django.core.management.base import BaseCommand
from farmacia.models import Medicamento
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Envía alertas de stock bajo'

    def handle(self, *args, **options):
        bajos = Medicamento.objects.filter(stock__lt=100, stock__gt=0)
        agotados = Medicamento.objects.filter(stock=0)
        
        if bajos.exists() or agotados.exists():
            mensaje = self.construir_mensaje(bajos, agotados)
            send_mail(
                'Alerta de Stock — Farmacia Dr. Nahum',
                mensaje,
                'sistema@farmaciadrnahum.cl',
                ['admin@farmaciadrnahum.cl'],
            )
```

```python
# Scheduled en Railway (via cron):
# O con Celery beat:
from celery import shared_task
from celery.schedules import crontab

@shared_task
def alerta_stock_diaria():
    # ejecutar todos los días a las 08:00
    pass

CELERY_BEAT_SCHEDULE = {
    'alerta-stock-diaria': {
        'task': 'farmacia.tasks.alerta_stock_diaria',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

### 9.3 WhatsApp para boletas

```python
# Con Twilio WhatsApp API:
from twilio.rest import Client

def enviar_boleta_whatsapp(boleta, numero_cliente):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=f'Hola {boleta.cliente_nombre}, '
             f'su compra en Farmacia Dr. Nahum: '
             f'${int(boleta.total):,}. '
             f'Boleta {boleta.numero_boleta}',
        to=f'whatsapp:{numero_cliente}'
    )
```

---

## 10. Problemas Críticos Identificados

### 10.1 Resumen priorizado

| Prioridad | # | Problema | Área |
|-----------|---|---------|------|
| 🔴 CRÍTICO | 1 | Email no funciona en producción | Config |
| 🔴 CRÍTICO | 2 | Modelo Venta = 1 medicamento | BD |
| 🔴 CRÍTICO | 3 | Sin exportación de reportes | Funcional |
| 🔴 CRÍTICO | 4 | Sin facturación electrónica SII | Legal |
| 🟠 ALTO | 5 | Race condition en stock | Técnico |
| 🟠 ALTO | 6 | Sin límite de descuento por rol | Seguridad |
| 🟠 ALTO | 7 | Registro público sin restricción | Seguridad |
| 🟠 ALTO | 8 | POS multi-pantalla (UX) | UX |
| 🟠 ALTO | 9 | Sin gestión de caja/turno | Funcional |
| 🟠 ALTO | 10 | Sin CRUD de clientes en web | Funcional |
| 🟡 MEDIO | 11 | 1 worker Gunicorn | Rendimiento |
| 🟡 MEDIO | 12 | Sin gráficos en dashboard | UX |
| 🟡 MEDIO | 13 | Sin brute force protection | Seguridad |
| 🟡 MEDIO | 14 | N+1 queries en historial | Rendimiento |
| 🟡 MEDIO | 15 | Sin nivel de stock configurable | Config |
| 🟢 BAJO | 16 | Dos carpetas de templates email | Deuda técnica |
| 🟢 BAJO | 17 | Campo `productos` en Proveedor sin estructura | BD |
| 🟢 BAJO | 18 | Sin historial de precios en Medicamento | Funcional |

---

## 11. Comparativa con Sistemas Modernos

### 11.1 vs POS modernos chilenos (SimplePOS, Bsale, Defontana)

| Funcionalidad | Sistemas modernos | Este sistema |
|--------------|------------------|-------------|
| Facturación electrónica DTE | ✅ Nativa | ❌ Pendiente |
| Integración SII | ✅ | ❌ |
| WebPay integrado | ✅ | ❌ |
| App móvil | ✅ | ❌ |
| Multi-sucursal | ✅ | ❌ |
| Gestión de caja/turno | ✅ | ❌ |
| Reportes exportables | ✅ | ❌ |
| Dashboard con gráficos | ✅ | ⚠️ |
| WhatsApp integrado | ✅ | ❌ |
| Control de recetas ISP | Parcial | ✅ Completo |
| Auditoría inmutable | ⚠️ | ✅ Completa |
| Código abierto/personalizable | ❌ SaaS cerrado | ✅ |
| Costo mensual | $50.000-$200.000/mes | Sin licencia |

### 11.2 vs ERP modernos (SAP Business One, Odoo)

| Aspecto | ERP moderno | Este sistema |
|---------|------------|-------------|
| Módulos integrados | 20+ módulos | 8 módulos |
| API REST nativa | ✅ | ❌ |
| Multi-empresa | ✅ | ❌ |
| BI integrado | ✅ | ❌ |
| Workflow/Aprobaciones | ✅ | Parcial |
| Complejidad de uso | Alta | Baja ✅ |
| Costo de implementación | $5M-$50M | Mínimo |
| Personalización | Alta | Alta ✅ |

### 11.3 Ventajas competitivas de este sistema

1. **Control de recetas ISP superior** — Más completo que la mayoría de POS del mercado
2. **Sin costo de licencia mensual** — Propiedad del dueño
3. **Totalmente personalizable** — Código fuente disponible
4. **Auditoría inmutable de recetas** — Cumplimiento legal robusto
5. **Deploy en la nube** — Acceso desde cualquier lugar
6. **Modelo FIFO nativo** — Correcto para farmacias

---

## 12. Roadmap de Evolución — 5 Fases

### Fase 1 — Correcciones Críticas
**Duración: 3-4 semanas | Prioridad: URGENTE**

| Tarea | Complejidad | Riesgo | Dependencia |
|-------|------------|--------|-------------|
| Configurar SMTP real (email) | Baja | Baja | Variables de entorno |
| Fix race condition stock | Media | Alta | Requiere testing |
| Exportación Excel ventas | Media | Baja | `openpyxl` |
| Exportación PDF reportes | Media | Baja | ReportLab instalado |
| Límite descuento por rol | Baja | Baja | RolPermiso existente |
| CRUD completo de clientes | Media | Baja | Formularios nuevos |
| Brute force protection | Baja | Baja | Cache Django |
| 3 workers Gunicorn | Baja | Baja | railway.toml |

**Entregables:**
- Email funcionando en producción
- Reportes exportables
- CRUD clientes completo
- Sistema más seguro

---

### Fase 2 — Optimización
**Duración: 4-6 semanas | Prioridad: ALTA**

| Tarea | Complejidad | Riesgo | Dependencia |
|-------|------------|--------|-------------|
| Refactorizar modelo Venta | Alta | Alta | Migraciones BD |
| select_related en queries | Baja | Baja | Ninguna |
| Redis para caché + sesiones | Media | Media | Redis en Railway |
| Dashboard con Chart.js | Media | Baja | Ninguna |
| Gestión de caja/turno | Alta | Media | Modelo nuevo |
| Celery para tasks async | Alta | Media | Redis |
| Alertas automáticas stock | Media | Baja | Celery |

**Entregables:**
- Base de datos optimizada
- Dashboard visual con gráficos
- Gestión de turnos operativa
- Alertas automáticas funcionando

---

### Fase 3 — Modernización Visual
**Duración: 4-6 semanas | Prioridad: MEDIA-ALTA**

| Tarea | Complejidad | Riesgo | Dependencia |
|-------|------------|--------|-------------|
| POS en una sola pantalla | Alta | Media | Fase 1 |
| HTMX para actualizaciones parciales | Media | Baja | Ninguna |
| Búsqueda en tiempo real | Media | Baja | HTMX o AJAX |
| Dashboard inteligente | Media | Baja | Fase 2 |
| Modo oscuro | Baja | Baja | CSS variables |
| PWA básica (offline capable) | Alta | Alta | Service Worker |
| Responsive POS para tablet | Media | Baja | CSS |

**Entregables:**
- POS moderno y rápido (una pantalla)
- Búsqueda instantánea
- Sistema usable en tablet

---

### Fase 4 — Automatizaciones e Integraciones
**Duración: 6-8 semanas | Prioridad: MEDIA**

| Tarea | Complejidad | Riesgo | Dependencia |
|-------|------------|--------|-------------|
| Facturación electrónica SII | Muy Alta | Alta | Certificado SII |
| WebPay Plus (Transbank) | Alta | Media | Cuenta comercial |
| WhatsApp Business API | Media | Baja | Cuenta Meta |
| Reporte automático diario | Baja | Baja | Celery (Fase 2) |
| CRM básico (citas, crónicos) | Alta | Baja | Fase 1 |
| API REST (DRF) | Alta | Baja | Ninguna |
| Importación masiva Excel | Media | Media | `openpyxl` |

**Entregables:**
- DTE emitidos legalmente (SII)
- Pago electrónico integrado
- CRM básico operativo
- API para futuras integraciones

---

### Fase 5 — Escalabilidad Empresarial
**Duración: 8-12 semanas | Prioridad: BAJA (futuro)**

| Tarea | Complejidad | Riesgo | Dependencia |
|-------|------------|--------|-------------|
| Multi-sucursal | Muy Alta | Muy Alta | Refactor global |
| App móvil (React Native / Flutter) | Muy Alta | Media | API REST |
| BI avanzado (integración Power BI) | Media | Baja | PostgreSQL acceso |
| Metas de venta por vendedor | Media | Baja | Fase 2 |
| Gestión de compras a proveedores | Alta | Media | Nuevo módulo |
| Sistema de fidelización de clientes | Alta | Baja | CRM Fase 4 |
| Inteligencia artificial básica | Muy Alta | Alta | Datos históricos |

**Entregables:**
- Sistema empresarial completo
- App móvil para vendedores
- Multi-sucursal operativo

---

### Resumen visual del Roadmap

```
2026
│
├── Mayo─Junio     ██ FASE 1: Correcciones críticas
│                     Email · Exportación · CRUD clientes · Seguridad
│
├── Junio─Agosto   ████ FASE 2: Optimización
│                     BD · Caja · Redis · Dashboard · Celery
│
├── Agosto─Sept    ████ FASE 3: Modernización visual
│                     POS único · HTMX · PWA · Tablet
│
├── Sept─Nov       ██████ FASE 4: Automatizaciones
│                     SII · WebPay · WhatsApp · CRM · API
│
└── 2027           ████████ FASE 5: Escalabilidad
                      Multi-sucursal · App móvil · BI
```

---

## 13. Conclusiones y Recomendaciones

### 13.1 Lo que funciona bien (mantener)

1. **Carrito persistente en BD** — Superior a soluciones basadas en sesión
2. **Control de recetas completo** — Cumple normativa ISP mejor que competidores
3. **Auditoría inmutable** — Trazabilidad legal robusta
4. **Transacciones atómicas** — Integridad de datos garantizada
5. **Modelo de roles** — Bien diseñado y extensible
6. **Trazabilidad de lotes FIFO** — Correcto para farmacias

### 13.2 Prioridades absolutas para el corto plazo

```
ESTA SEMANA:
├── 1. Configurar SMTP real → email funcional en producción
└── 2. 3 workers en railway.toml → mejor rendimiento

PRÓXIMAS 2 SEMANAS:
├── 3. Exportación Excel de ventas
├── 4. CRUD completo de clientes
└── 5. Protección brute force en login

PRÓXIMO MES:
├── 6. Refactorizar modelo Venta (VentaDetalle)
├── 7. Dashboard con gráficos Chart.js
└── 8. Gestión de caja/turno
```

### 13.3 Posicionamiento del sistema

**Hoy:** Sistema POS farmacia pequeña, funcional y en producción.

**Con Fase 1-2:** Sistema competitivo con Bsale y SimplePOS, con la ventaja de ser propio y sin costo de licencia.

**Con Fase 3-4:** Sistema ERP farmacéutico completo, con facturación electrónica y pagos integrados.

**Con Fase 5:** Plataforma SaaS farmacéutica para múltiples sucursales y revendible a otras farmacias.

### 13.4 Valoración del código

El código es **limpio, organizado y bien estructurado** para el tamaño del equipo y el tiempo de desarrollo. Las decisiones técnicas son correctas en general. Los problemas identificados son típicos de un MVP que creció hacia producción y que ahora necesita madurar hacia un producto empresarial.

**Deuda técnica estimada:** 3-4 semanas de trabajo de un desarrollador senior para resolver Fase 1 y 2 completamente.

**Recomendación final:** El sistema tiene una base excelente. Vale la pena invertir en las correcciones críticas antes de agregar nuevas funcionalidades.

---

*Sistema Farmacia Dr. Nahum — Auditoría Técnica Completa — Mayo 2026*  
*Documento preparado como auditoría empresarial profesional*  
*Confidencial — uso interno*
