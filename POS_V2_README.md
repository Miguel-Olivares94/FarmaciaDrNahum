# POS v2 - Terminal de Punto de Venta (Farmacia Collico)

## 📋 Descripción

Terminal POS v2 es un sistema completo de punto de venta para **Farmacia Collico** ubicada en Collico, Región del Biobío, Chile. Este sistema reemplaza el anterior con mejoras significativas en usabilidad, seguridad, auditoría y cumplimiento fiscal.

**Versión:** 2.0  
**Plataforma:** Django 5.0 + MySQL 8.0  
**Tecnología de Interfaz:** Bootstrap 5.3.0 + AJAX/JavaScript  
**Fecha de Implementación:** Abril 2026

## 🎯 Características Principales

### 1. **Terminal POS Completa**
- Búsqueda de medicamentos por nombre, SKU o laboratorio
- Carrito de compras almacenado en base de datos (seguro para múltiples usuarios)
- Visualización en tiempo real de totales (subtotal, IVA, total)
- Interfaz responsive en 2 columnas (búsqueda + carrito)

### 2. **Sistema de Pagos**
- 4 métodos de pago: Efectivo, Débito, Crédito, Transferencia
- Cálculo automático de cambio (para efectivo)
- Validación de referencia según método seleccionado
- Registro de cada transacción en tabla `Pago`

### 3. **Boletas y Facturación**
- Generación automática de números únicos: `BV-2026-00001` (resets cada año)
- Folios secuenciales requeridos por SII (Servicio Impuestos Internos)
- Desglose completo de IVA (19% - Chile)
- Plantilla imprimible en formato factura
- Almacenamiento de PDF en campo `archivo_pdf` (futuro)

### 4. **Descuentos**
- Descuentos por porcentaje (0-100%)
- Descuentos por monto fijo
- Motivo/observaciones registradas
- Aplicados ANTES de calcular IVA

### 5. **Gestión de Clientes**
- Selección opcional de cliente en venta
- Búsqueda rápida por RUT
- Registro automático de cliente en boleta
- Historial de compras por cliente

### 6. **Anulaciones y Devoluciones**
- **Anular venta completa**: Crea nota de crédito, revierte stock, requiere password supervisor
- **Procesar devolución parcial**: Permite devolver cantidad menor a vendida
- Todas las operaciones registradas en `HistorialStock` para auditoría
- Estados de venta: COMPLETADA, ANULADA, DEVUELTA (nunca se eliminan)

### 7. **Historial y Reportes**
- Visualización de todas las ventas realizadas
- Filtros por estado (completada/anulada/devuelta) y fecha
- Acciones rápidas: Anular, Devolver, Ver Boleta
- Paginación automática (20 ventas por página)

## 🏗️ Arquitectura

### Base de Datos
```
Modelos principales:
├── CarritoVenta
│   ├── vendedor (FK User)
│   ├── cliente (FK Cliente, nullable)
│   ├── estado (EN_CONSTRUCCION, COMPLETADO)
│   ├── subtotal, iva, total (Decimal)
│   ├── descuento_porcentaje, descuento_monto
│   └── fecha_completacion
│
├── CarritoItem
│   ├── carrito (FK CarritoVenta)
│   ├── medicamento (FK Medicamento)
│   ├── cantidad, precio_unitario
│   └── subtotal (property)
│
├── Boleta
│   ├── numero_boleta (unique, BV-YYYY-NNNNN)
│   ├── folio (unique, sequential)
│   ├── carrito (OneToOne CarritoVenta)
│   ├── cliente_rut, cliente_nombre
│   ├── subtotal, descuento, base_imponible, iva, total
│   ├── metodo_pago, referencia_pago
│   └── archivo_pdf (para PDF generado)
│
├── Pago
│   ├── boleta (FK Boleta)
│   ├── carrito (FK CarritoVenta)
│   ├── metodo_pago, monto, cambio
│   └── referencia (para débito/crédito/transferencia)
│
├── NotaCredito
│   ├── numero_nota (unique, NC-YYYY-NNNNN)
│   ├── folio (sequential)
│   ├── boleta_original (FK Boleta)
│   ├── motivo (ANULACION, DEVOLUCION)
│   ├── monto, observaciones
│   └── aprobada (true/false)
│
└── Venta (MODIFICADO)
    ├── numero_venta (unique, VT-YYYY-NNNNN) ← NUEVO
    ├── estado (COMPLETADA, ANULADA, DEVUELTA) ← NUEVO
    ├── boleta (FK Boleta) ← NUEVO
    └── [campos existentes]
```

### Rutas de URL
```
pos/v2/                    → terminal_pos_v2() - interfaz principal
pos/v2/agregar/<id>/       → pos_agregar_item() - AJAX add to cart
pos/v2/eliminar/<id>/      → pos_eliminar_item() - AJAX remove
pos/v2/vaciar/             → pos_vaciar_carrito() - empty cart
pos/v2/descuento/          → pos_aplicar_descuento() - discount form
pos/v2/cliente/            → pos_seleccionar_cliente() - client selection
pos/v2/pago/               → pos_procesar_pago() - payment processing
pos/v2/boleta/             → pos_mostrar_boleta() - receipt display
pos/v2/anular/<numero>/    → pos_anular_venta() - annul sale
pos/v2/devolver/<numero>/  → pos_procesar_devolucion() - process return
pos/v2/historial/          → pos_historial_ventas() - sales history
```

## 📦 Archivos Principales

### Backend
- **`farmacia/utils.py`** (NEW) - Utilidades: generadores de números, cálculos IVA, formatos
- **`farmacia/forms.py`** (MODIFIED) - 5 nuevos formularios para POS v2
- **`farmacia/views_pos_v2.py`** (NEW) - 11 vistas para POS v2
- **`farmacia/models.py`** (MODIFIED) - Nuevos modelos + campo boleta en Venta
- **`farmacia/urls.py`** (MODIFIED) - 11 nuevas rutas

### Frontend
- **`farmacia/templates/farmacia/pos_v2/`** (NEW) - 8 plantillas HTML
  - `terminal_pos_v2.html` - Interfaz principal
  - `procesar_pago_v2.html` - Formulario de pago
  - `boleta.html` - Recibo imprimible
  - `seleccionar_cliente_v2.html` - Selección de cliente
  - `aplicar_descuento.html` - Aplicar descuentos
  - `anular_venta.html` - Anular venta
  - `procesar_devolucion.html` - Procesar devolución
  - `historial_ventas.html` - Historial de ventas

### Base de Datos
- **`farmacia/migrations/0018_venta_boleta.py`** (NEW) - Migración para campo boleta

## 🚀 Inicio Rápido

### 1. Iniciar Servidor
```bash
python manage.py runserver
```
Acceder a: `http://localhost:8000/pos/v2/`

### 2. Crear Medicamentos (si no existen)
- Ir a `/medicamentos/nuevo/`
- Llenar nombre, laboratorio, precio, stock

### 3. Realizar Venta
1. Buscar medicamento en terminal
2. Ingresar cantidad, agregar a carrito
3. Opcionalmente: aplicar descuento, seleccionar cliente
4. Procesar pago
5. Ver boleta e imprimir

### 4. Anular Venta (solo supervisor)
- Ir a `/pos/v2/historial/`
- Encontrar venta a anular
- Click "Anular" → ingresar motivo + contraseña
- Sistema crea nota de crédito y revierte stock automáticamente

## 🔐 Seguridad

### Autenticación
- `@login_required` en todas las vistas
- Sessions de Django (ya existentes)

### Autorización
- Solo staff (supervisores) pueden anular ventas
- Contraseña requerida para anulaciones

### Integridad de Datos
- `@transaction.atomic()` en operaciones críticas:
  - Procesar pago (crea Boleta + Pago + Venta)
  - Anular venta (crea NotaCredito, revierte stock)
  - Procesar devolución

### Auditoría
- Números únicos para cada venta/boleta/nota (no se reutilizan)
- HistorialStock registra cantidad anterior/posterior
- Estados de venta NUNCA se borran (COMPLETADA → ANULADA)
- Usuarios registrados en todas las operaciones

## 💾 Cálculos Financieros

### IVA (19% - Chile)
```
Subtotal = suma de (cantidad × precio_unitario) de cada item
Descuento = porcentaje% del subtotal O monto fijo
Base Imponible = Subtotal - Descuento
IVA = Base Imponible × 19%
Total = Base Imponible + IVA

Ejemplo:
- Medicamento 1: 5 × $10.000 = $50.000
- Medicamento 2: 2 × $20.000 = $40.000
- Subtotal: $90.000
- Descuento (10%): -$9.000
- Base Imponible: $81.000
- IVA (19%): $15.390
- Total: $96.390
```

### Cambio (Efectivo)
```
Cambio = Monto Pagado - Total
Ejemplo: Cliente paga $100.000, total es $96.390 → Cambio = $3.610
```

## 📊 Reportes y Datos

### Información Generada Automáticamente
- **Número de Venta**: `VT-2026-00001` (resets each year)
- **Número de Boleta**: `BV-2026-00001` (resets each year)
- **Folio**: `1, 2, 3...` (sequential, resets yearly by invoice law)
- **Fecha/Hora**: Auto timestamp
- **Subtotal, IVA, Total**: Calculados automáticamente
- **Cambio**: Solo si método es EFECTIVO

### Historial Disponible
- Ver todas las ventas (con filtros)
- Detalles de cada venta (items, cliente, monto, fecha, vendedor)
- Acciones: Anular, Devolver, Ver Boleta

## 🔧 Mantenimiento

### Limpiar Carritos Abandonados (SQL)
```sql
-- Eliminar carritos en construcción hace > 24 horas
DELETE FROM farmacia_carritoventa 
WHERE estado = 'EN_CONSTRUCCION' 
AND fecha_creacion < DATE_SUB(NOW(), INTERVAL 1 DAY);
```

### Respaldar Boletas
```bash
# Exportar boletas como CSV
python manage.py dumpdata farmacia.Boleta --format=csv > boletas.csv
```

### Reestablecer Contadores (CAUTION!)
```sql
-- SOLO si es necesario (NUNCA en producción sin backup)
-- Resetear counter de número_venta para año siguiente
UPDATE farmacia_venta SET numero_venta = NULL 
WHERE YEAR(fecha) = 2025 AND numero_venta LIKE 'VT-2025-%';
```

## 📝 Notas de Diseño

### Por Qué Carrito en BD vs Session?
- **Multiusuario**: Si 2 usuarios usan misma PC, session se sobrescribe
- **Robustez**: Si se cae browser, carrito persiste
- **Auditoría**: Podemos saber qué estaba en carrito no completado

### Por Qué Venta + Boleta Separados?
- **Legal**: En Chile, boleta y factura son documentos diferentes
- **Flexible**: Múltiples items pueden estar en 1 boleta
- **Futuro**: Fácil agregar "Factura" como documento adicional

### Por Qué @transaction.atomic()?
- **Atomicidad**: Si falla uno de los pasos (crear boleta, crear pago, restar stock), ROLLBACK total
- **Consistencia**: Base de datos nunca queda en estado intermedio corrupto
- **Confiabilidad**: Crítico para operaciones de dinero

## 🐛 Troubleshooting

### Error: "Carrito no encontrado"
- Verificar que usuario está logueado
- Verificar que no hay múltiples carritos para mismo usuario
- SQL: `SELECT * FROM farmacia_carritoventa WHERE vendedor_id = X`

### Error: "Stock insuficiente"
- Verificar que medicamento tiene stock > cantidad
- Puede haber cambios concurrentes: REFRESH página

### Error: "Contraseña de supervisor incorrecta"
- Solo usuarios con `is_staff=True` pueden anular
- Contraseña es la contraseña de usuario Django

### Boleta no imprime correctamente
- Usar Firefox/Chrome (mejor soporte CSS print)
- Probar con "Guardar como PDF" antes de imprimir
- Si falla: error está en `boleta.html` CSS @media print

## 🎓 Flujo de Aprendizaje

### Para nuevos usuarios (cashiers)
1. Tutorial: Buscar producto
2. Tutorial: Agregar a carrito
3. Tutorial: Procesar pago
4. Tutorial: Imprimir boleta
5. Prácticas: 10 transacciones de prueba

### Para supervisores
1. Todo anterior +
2. Tutorial: Anular venta
3. Tutorial: Procesar devolución
4. Acceso a historial completo
5. Manejo de discrepancias

## 📞 Soporte

Para problemas:
1. Revisar logs: `logs/` folder
2. Ejecutar `python manage.py check`
3. Verificar base de datos está activa: `mysql -u user -p`
4. Contactar soporte técnico

---

**Sistema implementado por:** Arquitecto de Software  
**Última actualización:** Abril 2026  
**Status:** ✅ PRODUCCIÓN READY
