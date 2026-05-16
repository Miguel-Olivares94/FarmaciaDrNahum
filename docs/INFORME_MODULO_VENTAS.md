# Informe Técnico y Funcional — Módulo de Ventas
## Sistema de Gestión Farmacéutica Dr. Nahum

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Preparado por:** Análisis Funcional Senior / Arquitecto de Software  
**Tecnología:** Django · PostgreSQL · Bootstrap 5  
**Clasificación:** Documento interno — uso técnico y comercial

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Estado Actual del Sistema](#2-estado-actual-del-sistema)
3. [Análisis Funcional — Flujo de Ventas](#3-análisis-funcional--flujo-de-ventas)
4. [Roles y Permisos](#4-roles-y-permisos)
5. [Estructura de Datos](#5-estructura-de-datos)
6. [Análisis Técnico](#6-análisis-técnico)
7. [Seguridad](#7-seguridad)
8. [UX/UI — Experiencia de Usuario](#8-uxui--experiencia-de-usuario)
9. [Integraciones Futuras](#9-integraciones-futuras)
10. [Problemas Identificados y Mejoras](#10-problemas-identificados-y-mejoras)
11. [Roadmap de Desarrollo](#11-roadmap-de-desarrollo)
12. [Conclusiones](#12-conclusiones)

---

## 1. Resumen Ejecutivo

El Sistema de Gestión Farmacéutica Dr. Nahum cuenta con un módulo de ventas (POS v2) completamente funcional desarrollado en Django con PostgreSQL. El sistema implementa un flujo de punto de venta completo que incluye carrito de compras persistente, control de recetas médicas, emisión de boletas, devoluciones y auditoría.

### Fortalezas actuales

| Área | Evaluación |
|------|-----------|
| Modelo de datos | ⭐⭐⭐⭐⭐ Sólido y bien estructurado |
| Control de recetas | ⭐⭐⭐⭐⭐ Cumple normativa ISP |
| Transacciones atómicas | ⭐⭐⭐⭐⭐ Implementado correctamente |
| Auditoría | ⭐⭐⭐⭐ Completa en la mayoría de flujos |
| UX/UI | ⭐⭐⭐ Funcional pero mejorable |
| Reportes | ⭐⭐ Limitados |
| Integraciones | ⭐ Pendientes |

### Oportunidades de mejora prioritarias

1. Facturación electrónica (SII Chile)
2. Dashboard de ventas con métricas en tiempo real
3. Búsqueda y filtros avanzados en historial
4. Integración con medios de pago (WebPay, Mercado Pago)
5. Exportación de reportes en Excel/PDF

---

## 2. Estado Actual del Sistema

### 2.1 Módulos implementados

```
Sistema Farmacia Dr. Nahum
│
├── POS v2 (Punto de Venta)          ✅ Operativo
│   ├── Terminal de venta             ✅
│   ├── Carrito de compras            ✅ (persistente en BD)
│   ├── Control de stock              ✅ (atómico)
│   ├── Validación de recetas         ✅ (backend + frontend)
│   ├── Proceso de pago               ✅
│   ├── Emisión de boleta             ✅
│   ├── Envío email                   ✅
│   ├── Anulación de venta            ✅ (solo staff)
│   └── Devoluciones                  ✅
│
├── Inventario                        ✅ Operativo
│   ├── Medicamentos                  ✅
│   ├── Lotes (FIFO)                  ✅
│   ├── Alertas de stock              ✅
│   └── Historial de movimientos      ✅
│
├── Recetas Médicas                   ✅ Operativo
│   ├── Registro                      ✅
│   ├── Validación                    ✅
│   └── Auditoría inmutable           ✅
│
├── Reportes                          ⚠️ Básicos
│   ├── Historial de ventas           ✅
│   └── Exportación PDF/Excel         ❌ Pendiente
│
├── Administración                    ✅ Operativo
│   ├── Usuarios y roles              ✅
│   └── Auditoría general             ✅
│
└── Integraciones externas            ❌ Pendientes
    ├── SII / Facturación electrónica ❌
    ├── WebPay / Mercado Pago         ❌
    └── WhatsApp / CRM                ❌
```

### 2.2 Tecnologías actuales

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | Django | 6.0 |
| Base de datos | PostgreSQL | (Railway hosted) |
| Frontend | Bootstrap + JS vanilla | 5.3 |
| Servidor | Gunicorn | 26.0 |
| Deploy | Railway | - |
| Archivos estáticos | WhiteNoise | 6.x |

---

## 3. Análisis Funcional — Flujo de Ventas

### 3.1 Flujo completo de una venta

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO DE VENTA POS v2                       │
└─────────────────────────────────────────────────────────────────┘

  [1] INICIO DE SESIÓN
       │
       ▼
  [2] TERMINAL POS
       │  → Buscar medicamento por nombre / SKU / laboratorio
       │  → Escanear código de barras
       │
       ▼
  [3] VALIDACIÓN DE RECETA (backend)
       │  → ¿Requiere receta? → SÍ → Verificar receta válida
       │                        → NO → Continuar
       │  → Receta inválida → BLOQUEO + Log auditoría
       │
       ▼
  [4] CARRITO DE COMPRAS
       │  → Agregar ítems
       │  → Modificar cantidades
       │  → Eliminar ítems
       │  → Aplicar descuento (% o monto fijo)
       │  → Seleccionar cliente (opcional)
       │
       ▼
  [5] PROCESO DE PAGO
       │  → Seleccionar método: Efectivo / Débito / Crédito / Transferencia
       │  → Ingresar monto pagado
       │  → Calcular vuelto (si efectivo)
       │  → Validación final de stock y recetas
       │
       ▼
  [6] TRANSACCIÓN ATÓMICA
       │  → Generar número de boleta (BV-2026-XXXXX)
       │  → Crear Boleta fiscal
       │  → Crear registro de Pago
       │  → Crear Venta
       │  → Descontar stock
       │  → Registrar HistorialStock
       │  → Marcar carrito COMPLETADO
       │  → Enviar boleta por email (si hay cliente con email)
       │
       ▼
  [7] BOLETA EMITIDA
       │  → Mostrar en pantalla
       │  → Opción imprimir
       │  → Opción enviar por email
       │
       ▼
  [8] FIN — Nueva venta
```

### 3.2 Estados de una venta

```
                    ┌──────────────┐
                    │   CREADA     │  (CarritoVenta: EN_CONSTRUCCION)
                    └──────┬───────┘
                           │ Pago procesado
                           ▼
                    ┌──────────────┐
                    │  COMPLETADA  │  (Venta.estado = COMPLETADA)
                    └──────┬───────┘
              ┌────────────┴────────────┐
              │ Staff anula             │ Cliente devuelve
              ▼                         ▼
       ┌────────────┐          ┌──────────────────┐
       │  ANULADA   │          │    DEVUELTA       │
       └────────────┘          └──────────────────┘
       (NotaCredito:           (NotaCredito:
        ANULACION)              DEVOLUCION)
       Stock revertido          Stock revertido parcial
```

| Estado | Descripción | Quién puede aplicarlo |
|--------|-------------|----------------------|
| `EN_CONSTRUCCION` | Carrito activo, en proceso | Sistema automático |
| `COMPLETADA` | Venta finalizada y pagada | Sistema al procesar pago |
| `CANCELADA` | Carrito abandonado | Sistema / Vendedor |
| `ANULADA` | Venta revertida post-pago | Solo Staff/Admin |
| `DEVUELTA` | Devolución parcial o total | Solo Staff/Admin |

### 3.3 Validaciones en cada etapa

| Etapa | Validación | Tipo |
|-------|-----------|------|
| Agregar ítem | Cantidad > 0 | Frontend + Backend |
| Agregar ítem | Cantidad ≤ stock disponible | Backend |
| Agregar ítem | Receta válida (si aplica) | Backend |
| Aplicar descuento | Valor > 0 | Backend |
| Aplicar descuento | Solo un tipo (% o monto) | Backend |
| Procesar pago | Carrito no vacío | Backend |
| Procesar pago | Monto pagado ≥ total | Backend |
| Procesar pago | Stock suficiente (re-check final) | Backend atómico |
| Procesar pago | Recetas (re-check final) | Backend atómico |
| Anular venta | Usuario es staff | Backend |
| Anular venta | Venta no ya anulada | Backend |
| Devolver | Cantidad ≤ cantidad original | Backend |

### 3.4 Control de recetas médicas

```
Medicamento.tipo_venta
       │
       ├── "libre" ──────────────────→ Sin receta requerida
       │
       ├── "bajo_receta" ────────────→ Receta SIMPLE requerida
       │                               Tipo: sin retención
       │
       ├── "bajo_receta_retenida" ───→ Receta RETENIDA requerida
       │                               Se retiene la receta física
       │
       └── "controlada" ─────────────→ Receta CONTROLADA requerida
                                        Se retiene + debe subir archivo
                                        Log ISP inmutable obligatorio
```

**Vigencia de recetas:** 30 días por defecto, o hasta `fecha_vencimiento_receta` si se especifica.

---

## 4. Roles y Permisos

### 4.1 Matriz de permisos actual

| Acción | Admin | Gerente | Contador | Vendedor |
|--------|-------|---------|----------|---------|
| Ver terminal POS | ✅ | ✅ | ❌ | ✅ |
| Crear venta | ✅ | ✅ | ❌ | ✅ |
| Ver ventas propias | ✅ | ✅ | ✅ | ✅ |
| Ver ventas de todos | ✅ | ✅ | ✅ | ❌ |
| Editar venta propia (+24h) | ✅ | ✅ | ❌ | ❌ |
| Editar venta propia (-24h) | ✅ | ✅ | ❌ | ✅ |
| Anular venta | ✅ | ❌ | ❌ | ❌ |
| Procesar devolución | ✅ | ✅ | ❌ | ❌ |
| Aplicar descuento | ✅ | ✅ | ❌ | ✅ |
| Ver reportes globales | ✅ | ✅ | ✅ | ❌ |
| Gestionar usuarios | ✅ | ❌ | ❌ | ❌ |
| Ver auditoría | ✅ | ✅ | ✅ | ❌ |
| Gestionar stock | ✅ | ✅ | ❌ | ❌ |

### 4.2 Roles propuestos para expansión futura

```
ADMIN (Administrador del sistema)
├── Acceso total
├── Configura parámetros del sistema
├── Gestiona usuarios y roles
└── Ve todos los reportes y auditorías

DUEÑO / GERENTE
├── Ve todo el negocio
├── Aprueba devoluciones
├── Ve reportes financieros
└── Establece metas de venta

CONTADOR
├── Acceso de solo lectura a ventas
├── Exporta reportes contables
└── Ve flujo de caja

FARMACÉUTICO
├── Valida recetas
├── Controla medicamentos controlados
└── Registra devoluciones

VENDEDOR
├── Usa el POS
├── Ve su propio historial
└── Aplica descuentos (dentro de límite)

USUARIO BÁSICO (Consulta)
└── Solo puede ver catálogo de productos
```

---

## 5. Estructura de Datos

### 5.1 Diagrama ERD — Módulo de Ventas

```
USUARIO (auth.User)
    │
    │ 1:1
    ├──→ RolPermiso (rol, permisos, estado_activo)
    │
    │ 1:N
    ├──→ CarritoVenta ──────────────────────────────────────┐
    │       │                                               │
    │       │ 1:N                                          1:1
    │       ├──→ CarritoItem ──→ Medicamento         Boleta
    │       │                        │                  │
    │       │ 1:1                    │ 1:N             1:1
    │       ├──→ Boleta          LoteMedicamento      Pago
    │       │       │
    │       │       │ 1:N
    │       │       └──→ NotaCredito
    │       │
    │       │ 1:1
    │       └──→ Pago
    │
    │ 1:N
    ├──→ Venta ──→ Medicamento
    │              Lote
    │              Cliente
    │              Boleta
    │              Receta
    │
    │ 1:N
    └──→ AuditoriaLog

CLIENTE
    └──→ CarritoVenta (opcional)
    └──→ Venta (opcional)

MEDICAMENTO
    ├──→ LoteMedicamento (1:N, FIFO por vencimiento)
    └──→ HistorialStock (1:N, trazabilidad total)

RECETA
    ├──→ CarritoItem (1:N)
    ├──→ Venta (1:1, opcional)
    └──→ AuditoriaReceta (1:N, inmutable)
```

### 5.2 Tablas principales y campos clave

#### CarritoVenta
| Campo | Tipo | Descripción |
|-------|------|-------------|
| vendedor | FK User | Responsable de la venta |
| cliente | FK Cliente NULL | Cliente asociado (opcional) |
| estado | CharField | EN_CONSTRUCCION / COMPLETADO / CANCELADO |
| subtotal | Decimal(12,2) | Suma de ítems |
| descuento_monto | Decimal(12,2) | Descuento en pesos |
| descuento_porcentaje | Decimal(5,2) | Descuento en % |
| base_imponible | Decimal(12,2) | subtotal − descuento |
| iva | Decimal(12,2) | 19% de base_imponible |
| total | Decimal(12,2) | base_imponible + iva |

#### Boleta
| Campo | Tipo | Descripción |
|-------|------|-------------|
| numero_boleta | CharField(15) | BV-2026-00001 |
| folio | PositiveInt UNIQUE | Correlativo fiscal |
| metodo_pago | CharField | EFECTIVO/DEBITO/CREDITO/TRANSFERENCIA |
| estado | CharField | EMITIDA / ANULADA / IMPRESA |
| archivo_pdf | FileField | PDF generado |

#### Venta
| Campo | Tipo | Descripción |
|-------|------|-------------|
| numero_venta | CharField(15) | VT-2026-00001 |
| estado | CharField | COMPLETADA / ANULADA / DEVUELTA |
| medicamento | FK | Producto vendido |
| lote | FK NULL | Lote específico (trazabilidad) |
| cantidad | PositiveInt | Unidades vendidas |
| precio | Decimal(10,2) | Precio total (no unitario) |

### 5.3 Índices PostgreSQL recomendados

```sql
-- Índices actuales (ya implementados)
CREATE INDEX idx_venta_fecha ON farmacia_venta(fecha DESC);
CREATE INDEX idx_venta_vendedor_fecha ON farmacia_venta(vendedor_id, fecha);
CREATE INDEX idx_venta_estado ON farmacia_venta(estado);
CREATE INDEX idx_boleta_fecha ON farmacia_boleta(fecha_emision DESC);
CREATE INDEX idx_historialstock_fecha ON farmacia_historialstock(fecha_creacion);

-- Índices adicionales recomendados
CREATE INDEX idx_carrito_vendedor_estado ON farmacia_carritoventa(vendedor_id, estado);
CREATE INDEX idx_venta_numero ON farmacia_venta(numero_venta);
CREATE INDEX idx_cliente_rut ON farmacia_cliente(rut_dni);
CREATE INDEX idx_receta_paciente ON farmacia_receta(rut_paciente, tipo, estado);
```

---

## 6. Análisis Técnico

### 6.1 Arquitectura actual

```
┌─────────────────────────────────────────────────────┐
│                   CLIENTE (Browser)                  │
│          Bootstrap 5 · HTML · JS vanilla             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────┐
│              RAILWAY (Edge / Proxy)                  │
│              HTTPS termination                       │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP interno
                       ▼
┌─────────────────────────────────────────────────────┐
│                GUNICORN (WSGI)                       │
│                1 worker · sync                       │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│             DJANGO 6.0 (Backend)                     │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐│
│  │  Views   │  │  Models  │  │   Business Logic   ││
│  │  POS v2  │  │  ORM     │  │   Validaciones     ││
│  │  Reports │  │  Queries │  │   Transacciones    ││
│  └──────────┘  └──────────┘  └────────────────────┘│
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐│
│  │WhiteNoise│  │  Email   │  │   PDF Generator    ││
│  │(Statics) │  │(Console) │  │   (ReportLab)      ││
│  └──────────┘  └──────────┘  └────────────────────┘│
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           PostgreSQL (Railway managed)               │
│           Backups automáticos                        │
└─────────────────────────────────────────────────────┘
```

### 6.2 Arquitectura recomendada (próxima fase)

```
┌─────────────────────────────────────────────────────┐
│            FRONTEND (mejorado)                       │
│   Bootstrap 5 + Alpine.js (reactividad liviana)     │
│   HTMX (actualizaciones parciales sin SPA)          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              DJANGO REST API (DRF)                   │
│         Para integraciones y móvil                   │
└──────────────────────┬──────────────────────────────┘
                       │
             ┌─────────┴──────────┐
             ▼                    ▼
┌────────────────┐     ┌─────────────────────────────┐
│  PostgreSQL    │     │       REDIS (caché)          │
│  (Principal)   │     │  Sesiones · Rate limiting    │
└────────────────┘     └─────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│           SERVICIOS EXTERNOS                         │
│  SII (facturación) · WebPay · WhatsApp API          │
└─────────────────────────────────────────────────────┘
```

### 6.3 Modelos Django — evaluación y recomendaciones

**Lo que está bien:**
- Uso correcto de `@transaction.atomic` en el proceso de pago
- Validaciones en `clean()` de los modelos
- Relaciones `SET_NULL` vs `CASCADE` bien elegidas
- Índices en campos de búsqueda frecuente
- Separación clara entre CarritoVenta (proceso) y Boleta (documento fiscal)

**Lo que mejorar:**

```python
# ACTUAL — Venta solo guarda UN medicamento
class Venta(models.Model):
    medicamento = models.ForeignKey(Medicamento, ...)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(10, 2)  # precio TOTAL, no unitario

# RECOMENDADO — Separar en VentaCabecera + VentaDetalle
class VentaCabecera(models.Model):
    numero_venta = models.CharField(15, unique=True)
    carrito = models.OneToOneField(CarritoVenta, ...)
    total = models.DecimalField(12, 2)
    # ...

class VentaDetalle(models.Model):
    venta = models.ForeignKey(VentaCabecera, related_name='detalles', ...)
    medicamento = models.ForeignKey(Medicamento, ...)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(10, 2)
    # Esto ya existe en CarritoItem — se puede usar como base
```

---

## 7. Seguridad

### 7.1 Medidas actuales

| Medida | Estado | Descripción |
|--------|--------|-------------|
| Autenticación | ✅ | Django auth + backend personalizado |
| Control de roles | ✅ | RolPermiso por usuario |
| Transacciones atómicas | ✅ | `@transaction.atomic` en pago |
| Auditoría general | ✅ | AuditoriaLog todas las acciones |
| Auditoría recetas | ✅ | AuditoriaReceta inmutable |
| CSRF | ✅ | Django middleware activo |
| SQL Injection | ✅ | ORM Django (no SQL raw) |
| XSS | ✅ | Django templates auto-escape |
| HTTPS | ✅ | Railway edge termination |
| Secretos | ✅ | Variables de entorno (.env) |

### 7.2 Medidas recomendadas (pendientes)

```python
# 1. Rate limiting en login y POS
from django.core.cache import cache

def pos_agregar_item(request, medicamento_id):
    key = f"pos_rate_{request.user.id}"
    calls = cache.get(key, 0)
    if calls > 100:  # max 100 ítems por minuto
        return JsonResponse({'error': 'Demasiadas solicitudes'}, status=429)
    cache.set(key, calls + 1, 60)
    # ...

# 2. Validación de monto máximo por venta
MAX_MONTO_VENTA = 5_000_000  # 5 millones CLP

def pos_procesar_pago(request):
    if carrito.total > MAX_MONTO_VENTA:
        # Requiere aprobación de gerente
        pass

# 3. Doble verificación de stock (race condition)
from django.db import F
Medicamento.objects.filter(
    id=medicamento.id,
    stock__gte=cantidad  # verificar Y descontar en una sola query
).update(stock=F('stock') - cantidad)
```

### 7.3 Prevención de fraude

| Riesgo | Medida Actual | Mejora Recomendada |
|--------|---------------|-------------------|
| Venta sin stock | ✅ Validado | Re-validar con SELECT FOR UPDATE |
| Descuento excesivo | ⚠️ Sin límite | Límite configurable por rol |
| Anulación masiva | ⚠️ Sin alertas | Alerta si >3 anulaciones/día |
| Acceso fuera de horario | ❌ Sin restricción | Restringir horario por rol |
| Venta de controlados sin receta | ✅ Bloqueado | Mantener y reforzar |

---

## 8. UX/UI — Experiencia de Usuario

### 8.1 Flujo actual del POS

```
Terminal POS (búsqueda) → Agregar ítem → [Repetir]
                        → Seleccionar cliente (navegación separada)
                        → Aplicar descuento (navegación separada)
                        → Procesar pago (navegación separada)
                        → Ver boleta
```

**Problema:** Cada acción secundaria (cliente, descuento) requiere navegar a una página diferente, interrumpiendo el flujo.

### 8.2 Flujo propuesto (todo en pantalla)

```
┌─────────────────────────────────────────────────────────────────┐
│  TERMINAL POS v3 — Una sola pantalla                            │
├──────────────────────────┬──────────────────────────────────────┤
│  BÚSQUEDA                │  CARRITO                             │
│                          │                                      │
│  [Buscar medicamento...] │  Cliente: [Buscar por RUT...]        │
│                          │                                      │
│  Resultados:             │  ┌──────────────────────────────┐   │
│  □ Amoxicilina 500mg     │  │ Amoxicilina 500mg      x2    │   │
│    Stock: 45  $3.500/u   │  │ $7.000                  [−][+][✕]│
│                          │  ├──────────────────────────────┤   │
│  □ Paracetamol 500mg     │  │ Paracetamol 1g          x1   │   │
│    Stock: 120 $890/u     │  │ $890                    [−][+][✕]│
│                          │  └──────────────────────────────┘   │
│  [📷 Escanear código]    │                                      │
│                          │  Subtotal:           $7.890          │
│                          │  Descuento: [___]%  −$0              │
│                          │  IVA 19%:             $1.499         │
│                          │  TOTAL:               $9.389         │
│                          │                                      │
│                          │  Pago: [Efectivo▼]                   │
│                          │  Monto: [$__________]                │
│                          │  Vuelto: $0                          │
│                          │                                      │
│                          │  [       COBRAR       ]              │
└──────────────────────────┴──────────────────────────────────────┘
```

### 8.3 Mejoras visuales y funcionales propuestas

| Área | Problema actual | Mejora propuesta |
|------|----------------|-----------------|
| Búsqueda | Solo texto, requiere Enter | Autocompletado en tiempo real (AJAX) |
| Cantidad | Input manual | Botones +/− con máximo = stock |
| Cliente | Página separada | Panel lateral desplegable |
| Descuento | Página separada | Modal o campo inline |
| Precio | Solo total | Mostrar unitario y total por ítem |
| Stock | No visible en carrito | Mostrar stock restante al agregar |
| Receta | Error genérico | Modal guiado paso a paso |
| Pago en efectivo | Cálculo manual | Vuelto calculado automáticamente |
| Boleta | Solo ver | Opción imprimir / WhatsApp / email inline |

### 8.4 Optimización móvil (smartphone)

El sistema es responsivo, pero el POS no está optimizado para uso en tablet o smartphone como terminal principal. Se recomienda:

```
MODO TABLET/POS (pantalla táctil)
├── Botones grandes (mínimo 44px)
├── Teclado numérico grande para cantidades
├── Búsqueda por voz (Web Speech API)
├── Escáner de código QR (cámara del dispositivo)
└── Flujo vertical simplificado
```

---

## 9. Integraciones Futuras

### 9.1 Facturación electrónica — SII Chile

**Prioridad: ALTA**

El SII exige desde 2024 que farmacias con más de cierto monto anual emitan documentos tributarios electrónicos (DTE).

```
Flujo propuesto:
Boleta actual → API SII → DTE firmado → Folio legal SII
                              ↓
                    QR Code en boleta impresa
                    Verificable en sii.cl
```

**Bibliotecas compatibles:** `python-libredte` o API de terceros (Haulmer, TuDTE).

### 9.2 Medios de pago electrónico

| Integración | Descripción | Complejidad |
|-------------|-------------|-------------|
| WebPay Plus (Transbank) | Débito/crédito chileno estándar | Media |
| Mercado Pago | Tarjetas + QR | Media |
| Khipu | Transferencia bancaria en tiempo real | Baja |

```python
# Flujo WebPay propuesto
def pos_iniciar_pago_webpay(request, carrito_id):
    carrito = CarritoVenta.objects.get(id=carrito_id)
    tx = webpay.create_transaction(
        amount=int(carrito.total),
        session_id=str(carrito_id),
        return_url=f"{BASE_URL}/pos/webpay/respuesta/",
    )
    return redirect(tx.url + "?token_ws=" + tx.token)
```

### 9.3 WhatsApp Business API

**Caso de uso:** Enviar boleta + recordatorios de medicamentos crónicos.

```
Compra completada
        ↓
WhatsApp automático al cliente:
"Hola [nombre], su compra en Farmacia Dr. Nahum
está lista. Total: $9.390. Boleta adjunta en PDF.
Recuerde tomar [medicamento] según indicación médica."
```

**Proveedor recomendado:** Twilio, Meta Business API directa.

### 9.4 Sistema CRM básico

Aprovechar el modelo `Cliente` ya existente para agregar:

- Historial de compras por cliente
- Medicamentos crónicos (alertas de reposición)
- Descuentos por fidelidad / VIP (ya está `cliente_vip` en el modelo)
- Comunicaciones automáticas (cumpleaños, reposición)

### 9.5 Business Intelligence (Reportes avanzados)

| Reporte | Herramienta recomendada |
|---------|------------------------|
| Dashboard ejecutivo | Django + Chart.js (ya disponible) |
| Exportación Excel | `openpyxl` o `django-import-export` |
| Exportación PDF | ReportLab (ya instalado) |
| BI avanzado | Power BI conectado a PostgreSQL directamente |

---

## 10. Problemas Identificados y Mejoras

### 10.1 Problemas críticos

| # | Problema | Impacto | Solución |
|---|---------|---------|---------|
| 1 | `Venta` guarda solo 1 medicamento por venta | Alto — reportes incorrectos | Refactorizar a VentaCabecera/VentaDetalle |
| 2 | Sin facturación electrónica SII | Alto — cumplimiento legal | Integrar DTE |
| 3 | Sin exportación de reportes | Medio — gestión manual | Agregar Excel/PDF export |
| 4 | 1 solo worker Gunicorn | Medio — rendimiento bajo carga | Escalar workers o usar async |

### 10.2 Problemas de diseño

| # | Problema | Descripción |
|---|---------|-------------|
| 5 | `precio` en Venta = total | Campo confuso, debería ser `precio_unitario` |
| 6 | Flujo POS multi-pantalla | Interrumpe al vendedor, aumenta errores |
| 7 | Sin límite en descuentos | Vendedor puede poner 100% descuento |
| 8 | Sin búsqueda en historial | Solo filtro por estado y fecha, sin texto |
| 9 | Sin paginación en POS | Lista de medicamentos puede ser muy larga |
| 10 | Email con backend Console | En producción solo imprime, no envía |

### 10.3 Funcionalidades faltantes vs sistemas modernos

| Funcionalidad | Sistemas modernos | Este sistema |
|---------------|------------------|-------------|
| Dashboard con KPIs | ✅ | ⚠️ Básico |
| Facturación electrónica | ✅ | ❌ |
| Pago electrónico integrado | ✅ | ❌ |
| App móvil / PWA | ✅ | ❌ |
| Multi-sucursal | ✅ | ❌ |
| Gestión de turno/caja | ✅ | ❌ |
| Control de arqueo de caja | ✅ | ❌ |
| Alertas WhatsApp | ✅ | ❌ |
| Búsqueda avanzada + filtros | ✅ | ⚠️ Básico |
| Exportación Excel | ✅ | ❌ |
| Historial de precios | ✅ | ❌ |
| Metas de venta por vendedor | ✅ | ❌ |

### 10.4 Mejoras prioritarias (ordenadas por impacto)

```
PRIORIDAD ALTA (hacer primero)
├── 1. Corregir modelo Venta (VentaDetalle)
├── 2. Exportación Excel/PDF de reportes
├── 3. Dashboard con ventas del día + gráficos
├── 4. Límite máximo de descuento por rol
└── 5. Configurar email SMTP real en producción

PRIORIDAD MEDIA (próxima versión)
├── 6. POS en una sola pantalla (rediseño UX)
├── 7. Facturación electrónica SII
├── 8. Búsqueda avanzada en historial
├── 9. Gestión de caja/turno
└── 10. WhatsApp para boletas

PRIORIDAD BAJA (versiones futuras)
├── 11. Integración WebPay
├── 12. CRM con seguimiento de clientes crónicos
├── 13. Multi-sucursal
└── 14. App móvil PWA
```

---

## 11. Roadmap de Desarrollo

### Fase 1 — Estabilización y mejoras críticas
**Duración estimada: 4-6 semanas**

| Tarea | Esfuerzo | Riesgo | Dependencia |
|-------|---------|--------|-------------|
| Refactorizar modelo Venta | Alto | Alto | Migraciones BD |
| Email SMTP real | Bajo | Bajo | Variables de entorno |
| Exportación Excel reportes | Medio | Bajo | `openpyxl` |
| Exportación PDF reportes | Medio | Bajo | ReportLab (ya instalado) |
| Límite descuentos por rol | Bajo | Bajo | Ninguna |
| Dashboard básico con Chart.js | Medio | Bajo | Ninguna |

**Entregables Fase 1:**
- Modelo de ventas corregido
- Reportes exportables
- Dashboard operativo
- Email funcional en producción

---

### Fase 2 — Modernización y nuevas funcionalidades
**Duración estimada: 6-8 semanas**

| Tarea | Esfuerzo | Riesgo | Dependencia |
|-------|---------|--------|-------------|
| Rediseño UX del POS | Alto | Medio | Fase 1 completa |
| Autocompletado AJAX en POS | Medio | Bajo | Ninguna |
| Gestión de caja/turno | Alto | Medio | Refactorización Venta |
| Facturación electrónica SII | Muy Alto | Alto | Certificado SII |
| Búsqueda avanzada historial | Medio | Bajo | Ninguna |
| Multi-sucursal básico | Alto | Alto | Refactorización global |

**Entregables Fase 2:**
- POS modernizado y más rápido
- Gestión de turnos de caja
- DTE emitidos (si se obtiene certificado SII)

---

### Fase 3 — Escalabilidad e integraciones externas
**Duración estimada: 8-12 semanas**

| Tarea | Esfuerzo | Riesgo | Dependencia |
|-------|---------|--------|-------------|
| Integración WebPay | Alto | Medio | Cuenta Transbank |
| API REST (Django REST Framework) | Alto | Bajo | Fase 2 |
| WhatsApp Business API | Medio | Bajo | Cuenta Meta Business |
| CRM básico | Alto | Bajo | Modelo Cliente existente |
| PWA / App móvil | Muy Alto | Medio | API REST |
| Redis + caché | Medio | Bajo | Infraestructura Railway |

**Entregables Fase 3:**
- Sistema completamente integrado
- Pago electrónico funcional
- App móvil para vendedores
- CRM con seguimiento de clientes

---

### Resumen del Roadmap

```
2026
│
├── Q2 (Mayo–Junio) ── FASE 1: Estabilización
│   ├── Semana 1–2: Refactorizar modelo Venta
│   ├── Semana 3–4: Reportes exportables + Dashboard
│   └── Semana 5–6: Email + Descuentos + QA
│
├── Q3 (Julio–Agosto) ── FASE 2: Modernización
│   ├── Semana 1–3: Rediseño POS
│   ├── Semana 4–6: Caja/Turno + Facturación SII
│   └── Semana 7–8: Multi-sucursal + QA
│
└── Q4 (Septiembre–Diciembre) ── FASE 3: Integraciones
    ├── Semana 1–4: API REST + WebPay
    ├── Semana 5–8: WhatsApp + CRM
    └── Semana 9–12: PWA + Redis + QA final
```

---

## 12. Conclusiones

El Sistema de Gestión Farmacéutica Dr. Nahum tiene una **base técnica sólida** con un modelo de datos bien diseñado, transacciones atómicas correctas y un control de recetas que cumple la normativa ISP chilena.

### Puntos clave

**Lo que funciona bien y debe mantenerse:**
- Arquitectura de CarritoVenta persistente en BD (mejor que sesiones)
- Auditoría completa con AuditoriaLog y AuditoriaReceta
- Control de recetas médicas con bloqueo en backend
- Trazabilidad de lotes FIFO

**Lo que debe mejorar en el corto plazo:**
- Refactorizar el modelo `Venta` para soportar múltiples productos en un registro
- Exportación de reportes (crítico para la gestión del negocio)
- Email SMTP real en producción (actualmente solo imprime en consola)
- Dashboard con métricas del día

**Lo que posicionará al sistema en el futuro:**
- Facturación electrónica SII (obligatorio legalmente)
- Integración WebPay (aumenta ventas y reduce efectivo)
- API REST para expansión móvil
- CRM para fidelización de clientes

### Valoración final

El sistema está listo para operar en producción para una farmacia de tamaño pequeño a mediano. Con las mejoras de Fase 1 completadas, puede competir directamente con soluciones comerciales del mercado chileno como SimplePOS o Softland Retail, con la ventaja de ser completamente personalizable y sin costo de licencia mensual.

---

*Farmacia Dr. Nahum — Informe Módulo de Ventas — Mayo 2026*  
*Documento generado para uso interno, técnico y comercial*
