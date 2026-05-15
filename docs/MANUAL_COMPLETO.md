# 📕 MANUAL COMPLETO DEL SISTEMA FARMACIA DR NAHÚM

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Framework:** Django 5.2.13  
**Base de Datos:** SQLite (Desarrollo) / MySQL (Producción)  
**Tecnología:** Python 3.13, Bootstrap 5.3.0

---

## 📑 TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Módulo de Autenticación](#módulo-de-autenticación)
4. [Módulo de Medicamentos](#módulo-de-medicamentos)
5. [Módulo Terminal POS v2](#módulo-terminal-pos-v2)
6. [Módulo de Inventario](#módulo-de-inventario)
7. [Módulo de Recetas](#módulo-de-recetas)
8. [Módulo de Proveedores](#módulo-de-proveedores)
9. [Dashboard y Reportes](#dashboard-y-reportes)
10. [Guía de Flujos Principales](#guía-de-flujos-principales)

---

## 🎯 INTRODUCCIÓN

El **Sistema de Gestión Farmacéutica Collico** es una aplicación web desarrollada con Django que permite gestionar de forma integral:

- **Inventario de medicamentos** (compra, venta, devoluciones)
- **Punto de venta (Terminal POS)** con procesamiento de pagos
- **Control de recetas** (simple, retenida, controlada)
- **Gestión de proveedores** y lotes
- **Reportes y dashboards** de ventas e inventario
- **Auditoría y seguridad** con control de permisos

### 🔐 Tipos de Usuarios

| Tipo | Permisos | Acceso |
|------|----------|--------|
| **Admin** | Acceso total al sistema, anulación de ventas, reportes financieros | Todas las funciones |
| **Gerente** | Gestión de inventario, reportes, no puede anular ventas | Inventario + Reportes |
| **Vendedor** | Solo venta de medicamentos | Terminal POS + Historial |
| **Contador** | Reportes financieros, auditoría | Reportes + Historial |

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Estructura de Carpetas

```
farmacia/
├── models.py              # Modelos de datos
├── views.py               # Vistas principales
├── views_pos_v2.py        # Vistas de Terminal POS v2
├── forms.py               # Formularios
├── urls.py                # Rutas y URLs
├── backends.py            # Autenticación personalizada
├── permissions.py         # Control de permisos
├── receta_control.py      # Lógica de recetas
├── email_utils.py         # Envío de correos
├── utils.py               # Funciones auxiliares
├── templates/
│   └── farmacia/
│       ├── inicio_sesion.html
│       ├── registro_usuario.html
│       ├── dashboard.html
│       ├── medicamento_list.html
│       ├── medicamento_form.html
│       ├── pos_v2/
│       │   ├── terminal_pos_v2.html
│       │   ├── procesar_pago_v2.html
│       │   ├── boleta.html
│       │   └── historial_ventas.html
│       └── ...otros templates
└── migrations/            # Migraciones de BD

```

### Modelos Principales

#### 📦 Medicamento
```python
- nombre (CharField)
- laboratorio (CharField)
- precio (DecimalField)
- stock (IntegerField)
- tipo_venta (CharField: 'libre', 'receta_simple', 'receta_retenida', 'controlado')
- requiere_receta (BooleanField)
- fecha_ingreso (DateTimeField)
```

#### 💊 LoteMedicamento
```python
- medicamento (FK)
- numero_lote (CharField, único)
- fecha_vencimiento (DateField)
- cantidad (IntegerField)
- proveedor (FK)
- fecha_ingreso (DateTimeField)
```

#### 🛒 CarritoVenta
```python
- vendedor (FK a User)
- estado (CharField: 'EN_CONSTRUCCION', 'COMPLETADO')
- cliente (FK, opcional)
- descuento (DecimalField)
- fecha_creacion (DateTimeField)
- fecha_completacion (DateTimeField)
```

#### 🧾 Boleta
```python
- numero_boleta (CharField)
- folio (CharField)
- carrito (FK)
- subtotal, iva, total (DecimalField)
- metodo_pago (CharField)
- vendedor (FK)
```

#### 💵 Pago
```python
- boleta (FK)
- carrito (FK)
- metodo_pago (CharField: EFECTIVO, DEBITO, CREDITO, TRANSFERENCIA)
- monto (DecimalField)
- cambio (DecimalField)
- referencia (CharField, opcional)
```

#### 📄 Venta
```python
- numero_venta (CharField)
- medicamento (FK)
- cantidad (IntegerField)
- precio (DecimalField)
- vendedor (FK a User)
- boleta (FK)
- receta_venta (FK a Receta, opcional)
- estado (CharField: COMPLETADA, ANULADA, DEVUELTA)
- fecha (DateTimeField)
```

#### 📋 Receta
```python
- tipo (CharField: SIMPLE, RETENIDA, CONTROLADA)
- estado (CharField: PENDIENTE, VERIFICADA, RECHAZADA)
- nombre_medico (CharField)
- rut_medico (CharField)
- especialidad (CharField)
- nombre_paciente (CharField)
- rut_paciente (CharField)
- numero_receta (CharField)
- fecha_emision (DateField)
- fecha_vencimiento_receta (DateField)
- archivo_receta (FileField)
- registrada_por (FK a User)
- verificada_por (FK a User, opcional)
- fecha_verificacion (DateTimeField)
```

---

## 🔐 MÓDULO DE AUTENTICACIÓN

### 1️⃣ Vista: Inicio de Sesión
**Clase:** `InicioSesionView`  
**Ruta:** `/farmacia/` y `/farmacia/inicio_sesion/`  
**Métodos:** GET, POST  
**Template:** `inicio_sesion.html`

#### Funcionalidad
- Formulario de autenticación con usuario/email y contraseña
- Autenticación case-insensitive (personalizada en `backends.py`)
- Mensajes de error si las credenciales son incorrectas
- Redirección automática a `farmacia_main` si la autenticación es exitosa

#### Proceso
1. Usuario ingresa usuario/email y contraseña
2. Sistema valida credenciales en BD
3. Si es correcto → crea sesión y redirige a inicio
4. Si es incorrecto → muestra mensaje de error

**Credenciales de Prueba:**
```
Usuario: admin / Contraseña: admin123
Usuario: vendedor1 / Contraseña: (establecer según necesidad)
```

---

### 2️⃣ Vista: Registro de Usuario
**Clase:** `RegistroUsuarioView`  
**Ruta:** `/farmacia/registro/`  
**Métodos:** GET, POST  
**Template:** `registro_usuario.html`

#### Funcionalidad
- Formulario de creación de nuevos usuarios
- Validación de contraseñas (mínimo 8 caracteres, no todas numéricas)
- Confirmación de contraseña
- Autenticación automática al registrarse

#### Campos
- Username (único)
- Contraseña
- Confirmar contraseña
- Email (opcional)

#### Validaciones
- Username no puede existir
- Contraseñas deben coincidir
- Contraseña debe cumplir requisitos de seguridad

**Nota:** Los permisos (is_staff, is_superuser) deben asignarse manualmente por admin

---

### 3️⃣ Vista: Cerrar Sesión
**Clase:** `CerrarSesionView`  
**Ruta:** `/farmacia/cerrar_sesion/`  
**Métodos:** GET

#### Funcionalidad
- Cierra la sesión actual
- Redirige a página de inicio de sesión
- Destruye las cookies de sesión

---

## 💊 MÓDULO DE MEDICAMENTOS

### 4️⃣ Vista: Listado de Medicamentos
**Clase:** `MedicamentoListView` (ListView)  
**Ruta:** `/farmacia/medicamentos/`  
**Métodos:** GET  
**Template:** `medicamento_list.html`

#### Funcionalidad
- Listado completo de medicamentos en stock
- Filtrado por tipo de venta (venta libre, receta simple, retenida, controlado)
- Búsqueda por nombre o laboratorio
- Paginación (10 medicamentos por página)
- Muestra: nombre, laboratorio, precio, stock, tipo

#### Botones de Acción
- **Ver Detalles:** Redirige a medicamento_detail
- **Editar:** Abre formulario de edición (solo admin)
- **Eliminar:** Marca como inactivo (soft delete)

#### Filtros Disponibles
- Todos (todos los medicamentos)
- Venta Libre (sin receta)
- Receta Simple (válida 10 días, uso común)
- Receta Retenida (se queda en farmacia, 5 días)
- Controlado (drogas psicoactivas)

---

### 5️⃣ Vista: Detalle de Medicamento
**Clase:** `MedicamentoDetailView` (DetailView)  
**Ruta:** `/farmacia/medicamentos/<id>/`  
**Métodos:** GET  
**Template:** `medicamento_detail.html`

#### Información Mostrada
- Nombre y laboratorio
- Descripción
- Precio (con cálculo de IVA)
- Stock disponible
- Tipo de venta
- Fecha de ingreso
- Historial de lotes
- Botones: Editar, Volver, Agregar al Carrito (en POS)

---

### 6️⃣ Vista: Crear/Editar Medicamento
**Clase:** `MedicamentoCreateView`, `MedicamentoUpdateView` (CreateView, UpdateView)  
**Rutas:** 
- Crear: `/farmacia/medicamentos/nuevo/`
- Editar: `/farmacia/medicamentos/<id>/editar/`

**Métodos:** GET, POST  
**Template:** `medicamento_form.html`

#### Campos del Formulario
- Nombre *
- Laboratorio *
- Precio *
- Stock inicial *
- Tipo de venta *
- Requiere receta (checkbox)
- Descripción (opcional)

#### Validaciones
- Nombre y laboratorio no pueden estar vacíos
- Precio debe ser positivo
- Stock debe ser entero no negativo

**Restricción:** Solo accesible para usuarios con `is_staff=True`

---

### 7️⃣ Vista: Eliminar Medicamento
**Clase:** `MedicamentoDeleteView` (DeleteView)  
**Ruta:** `/farmacia/medicamentos/<id>/eliminar/`  
**Métodos:** GET, POST  
**Template:** `medicamento_confirm_delete.html`

#### Funcionalidad
- Pide confirmación antes de eliminar
- Elimina el registro de la BD
- Redirige a listado de medicamentos

**Nota:** Mejor es hacer soft-delete (marcar como inactivo)

---

## 🏪 MÓDULO TERMINAL POS v2

Este es el **corazón del sistema** de ventas. Consolida todas las operaciones en una única interfaz.

### 8️⃣ Vista: Terminal POS Principal
**Función:** `terminal_pos_v2`  
**Ruta:** `/farmacia/pos/`  
**Métodos:** GET  
**Template:** `pos_v2/terminal_pos_v2.html`

#### Funcionalidad
- Búsqueda en tiempo real de medicamentos
- Carrito visual con cálculo automático de totales
- Soporte para escaneo de códigos de barras
- Interfaz de dos columnas (búsqueda | carrito)

#### Componentes

**Búsqueda de Medicamentos:**
1. Por nombre/SKU/laboratorio
2. Por código de barras (AJAX)

**Carrito de Compras:**
- Medicamento
- Cantidad (spinner +/-)
- Precio unitario
- Subtotal del item
- Botón Eliminar
- **Resumen:**
  - Subtotal
  - Base Imponible
  - IVA 19%
  - **TOTAL**

**Botones Principales:**
- 👤 **Seleccionar Cliente** (opcional)
- 🏷️ **Aplicar Descuento**
- 💳 **Procesar Pago**
- 🗑️ **Vaciar Carrito**

#### Validaciones
- Stock disponible antes de agregar
- Receta válida para medicamentos controlados
- Cantidad mínima = 1

---

### 9️⃣ Vista: Agregar Medicamento al Carrito
**Función:** `pos_agregar_item`  
**Ruta:** `/farmacia/pos/agregar/<medicamento_id>/`  
**Métodos:** POST (AJAX)  
**Respuesta:** JSON

#### Proceso
1. Valida que medicamento exista
2. Valida stock disponible
3. Si medicamento requiere receta:
   - Solicita seleccionar receta válida
4. Obtiene/crea carrito en estado EN_CONSTRUCCION
5. Crea CarritoItem
6. Recalcula totales
7. Devuelve JSON con carrito actualizado

#### Respuesta JSON
```json
{
  "success": true,
  "carrito_id": 1,
  "items_count": 2,
  "total": 10948,
  "items": [
    {
      "medicamento": "Loratadina 10mg",
      "cantidad": 1,
      "subtotal": 2618
    }
  ]
}
```

---

### 🔟 Vista: Eliminar del Carrito
**Función:** `pos_eliminar_item`  
**Ruta:** `/farmacia/pos/eliminar/<medicamento_id>/`  
**Métodos:** POST (AJAX)  
**Respuesta:** JSON

#### Funcionalidad
- Elimina el item del carrito
- Si es el último item, elimina el carrito
- Recalcula totales
- Actualiza UI automáticamente

---

### 1️⃣1️⃣ Vista: Vaciar Carrito
**Función:** `pos_vaciar_carrito`  
**Ruta:** `/farmacia/pos/vaciar/`  
**Métodos:** POST (AJAX)  
**Respuesta:** JSON

#### Funcionalidad
- Elimina todos los items del carrito
- Marca carrito como eliminado
- Redirija a Terminal POS

---

### 1️⃣2️⃣ Vista: Seleccionar Cliente
**Función:** `pos_seleccionar_cliente`  
**Ruta:** `/farmacia/pos/cliente/`  
**Métodos:** GET, POST  
**Template:** `pos_v2/seleccionar_cliente_v2.html`

#### Funcionalidad
- Listado de clientes existentes
- Búsqueda por nombre/email
- Opción de crear cliente nuevo
- Opción "CONSUMIDOR FINAL" (por defecto)

#### Campos para Nuevo Cliente
- Nombre completo
- Email
- Teléfono
- RUT (opcional)
- Dirección (opcional)

---

### 1️⃣3️⃣ Vista: Aplicar Descuento
**Función:** `pos_aplicar_descuento`  
**Ruta:** `/farmacia/pos/descuento/`  
**Métodos:** GET, POST  
**Template:** `pos_v2/aplicar_descuento_v2.html`

#### Tipos de Descuento
- **Por Porcentaje:** 5%, 10%, 15%
- **Descuento Fijo:** $ ingresados
- **Sin Descuento**

#### Cálculo
```
Descuento = (Subtotal × Porcentaje) / 100
o
Descuento = Monto Fijo

Base Imponible = Subtotal - Descuento
IVA = Base Imponible × 0.19
Total = Base Imponible + IVA
```

---

### 1️⃣4️⃣ Vista: Procesar Pago
**Función:** `pos_procesar_pago`  
**Ruta:** `/farmacia/pos/pago/`  
**Métodos:** GET, POST  
**Template:** `pos_v2/procesar_pago_v2.html`

#### Pantalla de Pago (GET)
Muestra:
- Resumen de compra (items, cantidades, precios)
- Total a pagar
- Formulario de pago

#### Procesar Pago (POST)

**Validaciones Previas:**
1. ✅ Carrito existe y tiene items
2. ✅ Stock disponible para todos los items
3. ✅ Todas las recetas requeridas son válidas y vigentes
4. ✅ Medicamentos retenidos no superan límite

**Proceso Transaccional (ATOMIC):**
```python
with transaction.atomic():
    1. Crear Boleta
    2. Crear Pago
    3. Crear Venta (para primer item)
    4. Decrementar stock de medicamentos
    5. Crear registros de HistorialStock
    6. Marcar carrito como COMPLETADO
    7. Guardar numero_boleta en sesión
```

**Métodos de Pago:**
- EFECTIVO (sin validación adicional)
- DEBITO (requiere número de comprobante)
- CREDITO (requiere número de comprobante)
- TRANSFERENCIA (requiere número de transferencia)

#### Respuesta
Si todo es válido → Redirige a `pos_mostrar_boleta`  
Si hay error → Vuelve a mostrar formulario con mensajes de error

---

### 1️⃣5️⃣ Vista: Mostrar Boleta
**Función:** `pos_mostrar_boleta`  
**Ruta:** `/farmacia/pos/boleta/` o `/farmacia/pos/boleta/<boleta_id>/`  
**Métodos:** GET  
**Template:** `pos_v2/boleta.html`

#### Información Mostrada
- **Encabezado:**
  - Logo y nombre de farmacia
  - Número de boleta y folio
  - Fecha y hora
  - Vendedor
  
- **Items:**
  - Medicamento
  - Cantidad
  - Precio unitario
  - Subtotal

- **Totales:**
  - Subtotal
  - Base Imponible
  - IVA 19%
  - **TOTAL**

- **Método de Pago**
- **Validación SII**
- **Pie de página:** "Gracias por su compra"

#### Botones
- 🖨️ **Imprimir** (abre diálogo de impresión)
- 📧 **Enviar por Email** (opcional)
- ➕ **Nueva Venta**
- 📜 **Ver Historial**

---

### 1️⃣6️⃣ Vista: Historial de Ventas
**Función:** `pos_historial_ventas`  
**Ruta:** `/farmacia/pos/historial/`  
**Métodos:** GET  
**Template:** `pos_v2/historial_ventas.html`

#### Funcionalidad
- Listado de todas las ventas completadas
- Filtrado por estado (Completada, Anulada, Devuelta)
- Filtrado por fecha (desde-hasta)
- Búsqueda por número de venta
- Paginación

#### Para Cada Venta Muestra
- Número de venta
- Medicamento y cantidad
- Total
- Fecha y hora
- Estado
- Vendedor

#### Botones por Venta
- **Ver Boleta** (si está disponible)
- **Anular** (solo admin)
- **Devolver** (solo admin)

---

### 1️⃣7️⃣ Vista: Anular Venta
**Función:** `pos_anular_venta`  
**Ruta:** `/farmacia/pos/anular/<numero_venta>/`  
**Métodos:** GET, POST  
**Template:** `pos_v2/anular_venta.html`

#### Validaciones
- ✅ Solo usuarios con `is_staff=True` (admin/gerente)
- ✅ Venta debe estar en estado COMPLETADA
- ✅ Stock se restaura al anular

#### Proceso Transaccional
```python
with transaction.atomic():
    1. Cambiar estado de Venta a ANULADA
    2. Crear NotaCredito
    3. Restaurar stock del medicamento
    4. Crear registro de HistorialStock (ENTRADA)
    5. Registrar en auditoría
```

#### Campos
- Razón de anulación (obligatorio)
- Notas adicionales (opcional)

---

### 1️⃣8️⃣ Vista: Procesar Devolución
**Función:** `pos_procesar_devolucion`  
**Ruta:** `/farmacia/pos/devolver/<numero_venta>/`  
**Métodos:** GET, POST  
**Template:** `pos_v2/procesar_devolucion.html`

#### Diferencia con Anular
- **Anular:** Transacción nunca ocurrió (admin error)
- **Devolver:** Cliente devuelve medicamento (después de venta)

#### Opciones
- Reembolso completo
- Cambio por otro medicamento
- Crédito en cuenta

#### Validaciones
- ✅ Medicamento debe estar en buenas condiciones
- ✅ Venta original debe existir
- ✅ Fecha de devolución (máximo 30 días)

---

## 📦 MÓDULO DE INVENTARIO

### 1️⃣9️⃣ Vista: Dashboard de Inventario
**Función:** `dashboard_inventario`  
**Ruta:** `/farmacia/inventario/dashboard/`  
**Métodos:** GET  
**Template:** `dashboard_inventario.html`

#### Información Mostrada
- **Estadísticas:**
  - Total de medicamentos
  - Total de medicamentos agotados
  - Total de medicamentos bajo stock
  - Valor total de inventario

- **Gráficos:**
  - Medicamentos por tipo de venta
  - Medicamentos por laboratorio
  - Stock disponible por medicamento

- **Alertas:**
  - Medicamentos a punto de vencer
  - Medicamentos con stock bajo

---

### 2️⃣0️⃣ Vista: Gestor de Lotes
**Función:** `gestor_lotes`  
**Ruta:** `/farmacia/inventario/lotes/`  
**Métodos:** GET, POST  
**Template:** `gestor_lotes.html`

#### Funcionalidad
- Listado de lotes activos (FIFO)
- Creación de nuevos lotes
- Actualización de información
- Validación de fechas de vencimiento

#### Campos de Lote
- Número de lote (único)
- Medicamento
- Cantidad
- Fecha de vencimiento
- Proveedor
- Fecha de ingreso

#### Proceso FIFO (First In First Out)
El sistema automáticamente:
1. Ordena lotes por fecha_vencimiento (más próxima primero)
2. Descuenta stock de lote más antiguo primero
3. Registra en HistorialStock

---

### 2️⃣1️⃣ Vista: Reporte de Lotes
**Función:** `reporte_lotes`  
**Ruta:** `/farmacia/inventario/reporte-lotes/`  
**Métodos:** GET  
**Template:** `reporte_lotes.html`

#### Funcionalidad
- Reporte completo de lotes
- Filtrado por medicamento, proveedor, fecha
- Exportación a CSV/Excel
- Alertas de vencimiento

#### Columnas
- Medicamento
- Número de lote
- Cantidad
- Fecha de vencimiento
- Estatus (Vigente, Próximo a vencer, Vencido)
- Proveedor
- Fecha de ingreso

---

## 📋 MÓDULO DE RECETAS

### 2️⃣2️⃣ Vista: Gestión de Recetas
**Función:** `gestionar_recetas` (si existe)  
**Ruta:** `/farmacia/recetas/`  

#### Tipos de Recetas

**RECETA SIMPLE:**
- Validez: 10 días
- Uso: Antibióticos, antihipertensivos
- Control: Básico
- Ejemplo: Enalapril 10mg

**RECETA RETENIDA:**
- Validez: 5 días
- Uso: Medicamentos psicoactivos, ansiolíticos
- Control: Se queda en farmacia
- Máximo: 3 usos
- Ejemplo: Alprazolam 1mg

**RECETA CONTROLADA:**
- Validez: 1-3 días
- Uso: Drogas de alto control (estupefacientes)
- Control: Máximo, requiere documento original
- Validación: Cheque receta digitalizado

#### Validación Automática
El sistema valida automáticamente:
- ✅ Fecha de emisión no mayor a fecha de validez
- ✅ Receta aún vigente
- ✅ Número de usos (para retenidas)
- ✅ Información del médico y paciente
- ✅ Archivo digital (para controladas)

---

## 👥 MÓDULO DE PROVEEDORES

### 2️⃣3️⃣ Vista: Listado de Proveedores
**Clase:** `ProveedorListView` (ListView)  
**Ruta:** `/farmacia/proveedores/`  
**Métodos:** GET  
**Template:** `proveedor_list.html`

#### Funcionalidad
- Listado de proveedores activos
- Búsqueda por nombre o RUT
- Información de contacto
- Paginación

#### Información por Proveedor
- Nombre
- RUT
- Teléfono
- Email
- Dirección
- Persona de contacto

---

### 2️⃣4️⃣ Vista: Crear/Editar Proveedor
**Clase:** `ProveedorCreateView`, `ProveedorUpdateView`  
**Rutas:**
- Crear: `/farmacia/proveedores/nuevo/`
- Editar: `/farmacia/proveedores/<id>/editar/`

**Métodos:** GET, POST  
**Template:** `proveedor_form.html`

#### Campos Obligatorios
- Nombre
- RUT
- Teléfono
- Email

#### Campos Opcionales
- Dirección
- Persona de contacto
- Notas

---

### 2️⃣5️⃣ Vista: Eliminar Proveedor
**Clase:** `ProveedorDeleteView`  
**Ruta:** `/farmacia/proveedores/<id>/eliminar/`  
**Métodos:** GET, POST  
**Template:** `proveedor_confirm_delete.html`

---

## 📊 DASHBOARD Y REPORTES

### 2️⃣6️⃣ Vista: Dashboard Principal
**Función:** `dashboard`  
**Ruta:** `/farmacia/dashboard/`  
**Métodos:** GET  
**Template:** `dashboard.html`

#### Contenido para Diferentes Usuarios

**Para Admin:**
- Estadísticas generales (total ventas, ingresos)
- Medicamentos agotados
- Accesos rápidos a funciones
- Gráficos de ventas

**Para Gerente:**
- Dashboard de inventario
- Reportes de ventas
- Alertas de stock bajo

**Para Vendedor:**
- Acceso a Terminal POS
- Historial personal de ventas
- Información de medicamentos

**Para Contador:**
- Reportes financieros
- Auditoría de transacciones
- Exportación de datos

#### Accesos Rápidos
- 🏪 Abrir Terminal POS
- 💊 Ver Inventario
- 📋 Historial de Ventas
- 📈 Dashboard de Lotes
- 👥 Gestionar Proveedores

---

### 2️⃣7️⃣ Vista: Página Principal (Farmacia Main)
**Clase:** `FarmaciaMainView`  
**Ruta:** `/farmacia/farmacia_main/`  
**Métodos:** GET  
**Template:** `farmacia_main.html`

#### Contenido
- Bienvenida personalizada
- Información general del sistema
- Galería de imágenes
- Redes sociales
- Información de contacto

---

## 🔄 GUÍA DE FLUJOS PRINCIPALES

### Flujo 1: Venta de Medicamento Sin Receta

```
1. Usuario accede a Terminal POS (/farmacia/pos/)
   ↓
2. Busca medicamento (Loratadina)
   ↓
3. Sistema muestra resultados
   ↓
4. Usuario hace clic en "Agregar"
   ↓
5. Sistema valida stock
   ↓
6. Agrega item a carrito
   ↓
7. Usuario puede:
   - Agregar más medicamentos
   - Aplicar descuento
   - Seleccionar cliente
   ↓
8. Usuario hace clic en "Procesar Pago"
   ↓
9. Pantalla de resumen de compra
   ↓
10. Usuario selecciona método de pago (EFECTIVO)
    ↓
11. Sistema crea:
    - Boleta
    - Pago
    - Venta
    - Decrementa stock
    - Crea HistorialStock
    ↓
12. Muestra boleta
    ↓
13. Usuario imprime boleta
    ↓
14. ✅ VENTA COMPLETADA
```

**Tiempo Estimado:** 2-3 minutos

---

### Flujo 2: Venta de Medicamento con Receta Simple

```
1. Usuario accede a Terminal POS
   ↓
2. Busca medicamento (Enalapril 10mg)
   ↓
3. Sistema muestra como "REQUIERE RECETA"
   ↓
4. Usuario hace clic en "Agregar"
   ↓
5. Sistema muestra modal:
   "Este medicamento requiere receta"
   ↓
6. Usuario selecciona receta válida:
   - Dr. Juan García
   - Paciente: Juan Pérez
   - Receta Simple, vigente 10 días
   ↓
7. Sistema valida:
   - ✅ Receta existe
   - ✅ Receta aún vigente
   - ✅ Tipo coincide (simple)
   ↓
8. Agrega item a carrito con receta asociada
   ↓
9. Procede normalmente con pago
   ↓
10. En la Venta se registra:
    - medicamento: Enalapril
    - receta_venta: ID receta simple
    - estado: COMPLETADA
    ↓
11. ✅ VENTA CON RECETA COMPLETADA
```

---

### Flujo 3: Venta de Medicamento con Receta Retenida

```
1-5. Igual al Flujo 2
   ↓
6. Usuario selecciona receta RETENIDA:
   - Dra. María López
   - Especialidad: Psiquiatría
   - Receta Retenida, vigente 5 días
   ↓
7. Sistema valida:
   - ✅ Receta existe
   - ✅ Receta aún vigente
   - ✅ Número de usos < 3
   ↓
8. Agrega item a carrito
   ↓
9. En pago, sistema registra que:
   - Receta se queda en farmacia
   - Se incrementa uso (1/3)
   ↓
10. ✅ VENTA COMPLETADA
    - Receta se archiva en BD
    - Próximas ventas validarán usos restantes
```

---

### Flujo 4: Anular Venta (Admin)

```
1. Admin accede a Historial de Ventas
   ↓
2. Busca venta a anular
   ↓
3. Hace clic en "Anular"
   ↓
4. Sistema valida:
   - ✅ Usuario es admin/staff
   - ✅ Venta está COMPLETADA
   ↓
5. Muestra formulario:
   - Razón de anulación (requerido)
   - Notas adicionales
   ↓
6. Admin ingresa razón y confirma
   ↓
7. Sistema realiza (ATOMIC):
   - Venta.estado = ANULADA
   - Crea NotaCredito
   - Restaura stock
   - Crea HistorialStock (ENTRADA)
   - Registra auditoria
   ↓
8. ✅ VENTA ANULADA
    - Stock disponible nuevamente
    - Cliente puede recibir reembolso
```

---

### Flujo 5: Devolución de Medicamento

```
1. Cliente llega a farmacia con medicamento
   ↓
2. Admin accede a Historial
   ↓
3. Busca venta original
   ↓
4. Hace clic en "Devolver"
   ↓
5. Sistema valida:
   - ✅ Venta existe
   - ✅ Está dentro de 30 días
   ↓
6. Muestra opciones:
   - Reembolso completo
   - Cambio por otro medicamento
   - Crédito en cuenta
   ↓
7. Admin selecciona opción:
   
   Si REEMBOLSO:
   - Crea NotaCredito
   - Restaura stock
   - Registra transacción
   
   Si CAMBIO:
   - Crea nueva venta
   - Restaura stock medicamento original
   - Descuenta stock nuevo medicamento
   
   Si CRÉDITO:
   - Crea registro de crédito
   - Vincula a cliente
   ↓
8. ✅ DEVOLUCIÓN PROCESADA
```

---

## 🔒 SEGURIDAD Y VALIDACIONES

### Decoradores de Autenticación
```python
@login_required(login_url='inicio_sesion')  # Requiere estar autenticado
@admin_required  # Solo superusers
@staff_required  # Solo is_staff=True
```

### Validaciones Transaccionales
Todas las operaciones críticas usan `transaction.atomic()`:
- Pagos
- Anulaciones
- Devoluciones
- Cambios de stock

### Control de Permisos
| Operación | Admin | Gerente | Vendedor | Contador |
|-----------|-------|---------|----------|----------|
| Vender | ✅ | ❌ | ✅ | ❌ |
| Ver historial | ✅ | ✅ | ✅ | ✅ |
| Anular venta | ✅ | ✅ | ❌ | ❌ |
| Editar medicamentos | ✅ | ✅ | ❌ | ❌ |
| Ver reportes financieros | ✅ | ✅ | ❌ | ✅ |

---

## 📱 INTERFACES Y RESPONSIVIDAD

Todos los templates usan **Bootstrap 5.3.0** y son:
- ✅ Responsive (mobile, tablet, desktop)
- ✅ Accesibles (WCAG 2.1)
- ✅ Rápidos (carga < 2s)
- ✅ Compatibles con navegadores modernos

---

## 🔗 MAPA COMPLETO DE URLs

| Ruta | Nombre | Vista | Métodos |
|------|--------|-------|---------|
| `/farmacia/` | `inicio_sesion` | InicioSesionView | GET, POST |
| `/farmacia/registro/` | `registro_usuario` | RegistroUsuarioView | GET, POST |
| `/farmacia/cerrar_sesion/` | `cerrar_sesion` | CerrarSesionView | GET |
| `/farmacia/dashboard/` | `dashboard` | dashboard | GET |
| `/farmacia/farmacia_main/` | `farmacia_main` | FarmaciaMainView | GET |
| `/farmacia/medicamentos/` | `medicamento_list` | MedicamentoListView | GET |
| `/farmacia/medicamentos/nuevo/` | `medicamento_create` | MedicamentoCreateView | GET, POST |
| `/farmacia/medicamentos/<id>/` | `medicamento_detail` | MedicamentoDetailView | GET |
| `/farmacia/medicamentos/<id>/editar/` | `medicamento_update` | MedicamentoUpdateView | GET, POST |
| `/farmacia/medicamentos/<id>/eliminar/` | `medicamento_delete` | MedicamentoDeleteView | GET, POST |
| `/farmacia/pos/` | `terminal_pos_v2` | terminal_pos_v2 | GET |
| `/farmacia/pos/agregar/<id>/` | `pos_agregar_item` | pos_agregar_item | POST |
| `/farmacia/pos/eliminar/<id>/` | `pos_eliminar_item` | pos_eliminar_item | POST |
| `/farmacia/pos/vaciar/` | `pos_vaciar_carrito` | pos_vaciar_carrito | POST |
| `/farmacia/pos/cliente/` | `pos_seleccionar_cliente` | pos_seleccionar_cliente | GET, POST |
| `/farmacia/pos/descuento/` | `pos_aplicar_descuento` | pos_aplicar_descuento | GET, POST |
| `/farmacia/pos/pago/` | `pos_procesar_pago` | pos_procesar_pago | GET, POST |
| `/farmacia/pos/boleta/` | `pos_mostrar_boleta` | pos_mostrar_boleta | GET |
| `/farmacia/pos/boleta/<id>/` | `pos_mostrar_boleta_id` | pos_mostrar_boleta | GET |
| `/farmacia/pos/historial/` | `pos_historial_ventas` | pos_historial_ventas | GET |
| `/farmacia/pos/anular/<numero>/` | `pos_anular_venta` | pos_anular_venta | GET, POST |
| `/farmacia/pos/devolver/<numero>/` | `pos_procesar_devolucion` | pos_procesar_devolucion | GET, POST |
| `/farmacia/inventario/dashboard/` | `dashboard_inventario` | dashboard_inventario | GET |
| `/farmacia/inventario/lotes/` | `gestor_lotes` | gestor_lotes | GET, POST |
| `/farmacia/inventario/reporte-lotes/` | `reporte_lotes` | reporte_lotes | GET |
| `/farmacia/proveedores/` | `proveedor_list` | ProveedorListView | GET |
| `/farmacia/proveedores/nuevo/` | `proveedor_create` | ProveedorCreateView | GET, POST |
| `/farmacia/proveedores/<id>/` | `proveedor_detail` | ProveedorDetailView | GET |
| `/farmacia/proveedores/<id>/editar/` | `proveedor_update` | ProveedorUpdateView | GET, POST |
| `/farmacia/proveedores/<id>/eliminar/` | `proveedor_delete` | ProveedorDeleteView | GET, POST |

---

## 📝 CHEAT SHEET DE OPERACIONES COMUNES

### Agregar Medicamento Nuevo
```
1. Inicio → Medicamentos
2. Botón "Nuevo Medicamento"
3. Llenar formulario
4. Guardar
```

### Crear Venta
```
1. Terminal POS
2. Buscar medicamento
3. Agregar al carrito
4. Procesar pago
5. Imprimir boleta
```

### Anular Venta (admin)
```
1. Historial de Ventas
2. Buscar venta
3. Botón "Anular"
4. Ingresar razón
5. Confirmar
```

### Ver Inventario Bajo
```
1. Dashboard de Lotes
2. Ver medicamentos con stock bajo
3. Hacer orden de compra al proveedor
```

---

## ❓ PREGUNTAS FRECUENTES

**P: ¿Cómo recupero una boleta perdida?**
A: Ve a Historial de Ventas → busca por número o fecha → Ver Boleta

**P: ¿Se puede anular una venta después de 24 horas?**
A: Sí, solo admin puede anular, sin límite de tiempo (mejor usar Devolución)

**P: ¿Qué pasa si se anula una venta?**
A: Se restaura el stock y se crea una Nota de Crédito para el cliente

**P: ¿Los medicamentos retenidos se pueden vender 3 veces?**
A: Sí, máximo 3 usos con la misma receta retenida

**P: ¿Cómo exporto un reporte?**
A: Dashboard de Lotes → botón "Exportar CSV"

---

## 🆘 SOPORTE TÉCNICO

**Problemas Comunes:**

| Problema | Solución |
|----------|----------|
| No puedo acceder al sistema | Verificar usuario/contraseña, contactar admin |
| No veo medicamentos en búsqueda | Asegúrate de escribir el nombre exacto |
| No puedo procesar pago | Verificar que haya seleccionado método de pago |
| Receta no válida | Verificar que la receta esté vigente |
| Stock negativo | Contactar admin inmediatamente |

---

## 📞 INFORMACIÓN DE CONTACTO

**Farmacia Dr Nahúm**
- 📍 Collico, Región del Biobío
- 📱 WhatsApp: +56 9 42652487
- 📧 Email: farmaciacollico@example.com
- 🕐 Horarios: Lunes-Sábado 8:00-20:00

---

## 📜 HISTORIAL DE VERSIONES

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Mayo 2026 | Versión inicial - Terminal POS v2 consolidada |

---

**Última actualización:** 3 de Mayo de 2026  
**Manual elaborado por:** Sistema de Documentación Automática  
**Licencia:** Farmacia Dr Nahúm © 2026

---

## 📎 APÉNDICES

### Apéndice A: Códigos de Error Comunes
- **400:** Solicitud inválida
- **403:** Acceso denegado (permisos insuficientes)
- **404:** Recurso no encontrado
- **500:** Error del servidor (contactar soporte)

### Apéndice B: Tabla de Medicamentos de Prueba

| Nombre | Tipo | Precio | Stock | Requiere Receta |
|--------|------|--------|-------|-----------------|
| Loratadina 10mg | Libre | $2,618 | 50 | No |
| Enalapril 10mg | Receta Simple | $4,165 | 30 | Sí |
| Alprazolam 1mg | Receta Retenida | $6,188 | 20 | Sí |

### Apéndice C: Estructuras de Datos JSON

**Carrito en JSON:**
```json
{
  "id": 1,
  "vendedor": "vendedor1",
  "items": [
    {
      "medicamento": "Loratadina 10mg",
      "cantidad": 2,
      "precio_unitario": 2618,
      "receta": null
    }
  ],
  "subtotal": 5236,
  "descuento": 0,
  "base_imponible": 5236,
  "iva": 994.84,
  "total": 6230.84
}
```

---

**FIN DEL MANUAL**
