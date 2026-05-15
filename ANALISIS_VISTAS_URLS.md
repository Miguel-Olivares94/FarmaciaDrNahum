# 📋 ANÁLISIS COMPLETO DE VISTAS Y URLs DEL SISTEMA DE FARMACIA

**Fecha de generación:** Mayo 2026  
**Archivo analizado:** farmacia/views.py, farmacia/views_pos_v2.py, farmacia/urls.py

---

## 📑 TABLA DE CONTENIDOS

1. [Vistas en farmacia/views.py](#vistas-en-farmaciaviespy)
2. [Vistas en farmacia/views_pos_v2.py](#vistas-en-farmaciavews_pos_v2py)
3. [URLs en farmacia/urls.py](#urls-en-farmaciaurlspy)
4. [Resumen de estadísticas](#resumen-de-estadísticas)

---

## 🔷 VISTAS EN farmacia/views.py

### 1. **RegistroUsuarioView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 26
- **Herencia:** `View`
- **Propósito:** Permite el registro de nuevos usuarios en el sistema
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Muestra formulario de registro vacío
  - `post(request)` - Procesa el registro y autentica al usuario
- **URL asociada:** `registro/` → `registro_usuario`
- **Template:** `farmacia/registro_usuario.html`
- **Lógica:**
  - Recibe formulario `UserCreationForm`
  - Valida contraseña (validación integrada de Django)
  - Autentica al usuario tras crear la cuenta
  - Redirige a `farmacia_main` al registro exitoso

---

### 2. **InicioSesionView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 65
- **Herencia:** `View`
- **Propósito:** Maneja el inicio de sesión de usuarios
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Muestra formulario de autenticación
  - `post(request)` - Procesa autenticación con username/password
- **URL asociada:** `` (raíz) → `inicio_sesion`
- **Template:** `farmacia/inicio_sesion.html`
- **Autenticación:** Usa `AuthenticationForm` personalizado (`CaseInsensitiveAuthenticationForm`)
- **Lógica:**
  - Extrae username y password
  - Autentica usuario (sin distinción de mayúsculas)
  - Inicia sesión si es válido
  - Redirige a `farmacia_main`

---

### 3. **CerrarSesionView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 104
- **Herencia:** `View`
- **Propósito:** Cierra la sesión del usuario actual
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Ejecuta logout y redirige
- **URL asociada:** `cerrar_sesion/` → `cerrar_sesion`
- **Lógica:**
  - Llama a `logout(request)` de Django
  - Redirige a página de inicio de sesión

---

### 4. **FarmaciaMainView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 120
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Página principal/dashboard de la farmacia
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Muestra estadísticas principales
- **URL asociada:** `farmacia_main/` → `farmacia_main`
- **Template:** `farmacia/farmacia_main.html`
- **Login requerido:** Sí (redirige a `inicio_sesion`)
- **Contexto (datos mostrados):**
  - `total_medicamentos` - Count de medicamentos
  - `medicamentos_agotados` - Count de medicamentos con stock=0
- **KPIs calculados:**
  - Total de medicamentos en inventario
  - Medicamentos con stock agotado

---

### 5. **MedicamentoListView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 151
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Lista todos los medicamentos con filtros por tipo de venta
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Obtiene medicamentos y aplica filtros
- **URL asociada:** `medicamentos/` → `medicamento_list`
- **Template:** `farmacia/medicamento_list.html`
- **Login requerido:** Sí
- **Filtros disponibles (GET params):**
  - `filtro=todos` - Todos los medicamentos
  - `filtro=receta` - Medicamentos que requieren receta
  - `filtro=receta_simple` - Receta simple
  - `filtro=receta_retenida` - Receta retenida
  - `filtro=controlado` - Medicamentos controlados
  - `filtro=libre` - Venta libre
- **KPIs calculados:**
  - `stock_total` - Suma total de stock disponible
  - `bajo_stock` - Count de medicamentos con 0 < stock < 100
  - `agotados` - Count de medicamentos con stock=0
  - `titulo_filtro` - Título según filtro activo
  - `filtro_activo` - Identificador del filtro

---

### 6. **MedicamentoDetailView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 202
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Muestra detalles de un medicamento específico
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request, pk)` - Obtiene medicamento por ID
- **URL asociada:** `medicamentos/<int:pk>/` → `medicamento_detail`
- **Template:** `farmacia/medicamento_detail.html`
- **Login requerido:** Sí
- **Parámetros URL:** `pk` (ID del medicamento)
- **Contexto:** Objeto medicamento completo

---

### 7. **MedicamentoCreateView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 216
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Permite crear nuevos medicamentos
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request)` - Muestra formulario vacío
  - `post(request)` - Procesa creación y guarda en BD
- **URL asociada:** `medicamentos/nuevo/` → `medicamento_create`
- **Template:** `farmacia/medicamento_form.html`
- **Login requerido:** Sí
- **Form utilizado:** `MedicamentoForm`
- **Lógica:**
  - Valida formulario
  - Guarda medicamento en BD
  - Redirige a lista de medicamentos

---

### 8. **MedicamentoUpdateView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 250
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Permite editar medicamentos existentes
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request, pk)` - Muestra formulario con datos actuales
  - `post(request, pk)` - Procesa actualización
- **URL asociada:** `medicamentos/<int:pk>/editar/` → `medicamento_update`
- **Template:** `farmacia/medicamento_form.html`
- **Login requerido:** Sí
- **Parámetros URL:** `pk` (ID del medicamento)
- **Form utilizado:** `MedicamentoForm`

---

### 9. **MedicamentoDeleteView**
- **Tipo:** Class-Based View (CBV)
- **Línea:** 274
- **Herencia:** `LoginRequiredMixin`, `View`
- **Propósito:** Permite eliminar medicamentos
- **Docstring:** No tiene
- **Métodos principales:**
  - `get(request, pk)` - Muestra página de confirmación
  - `post(request, pk)` - Ejecuta eliminación
- **URL asociada:** `medicamentos/<int:pk>/eliminar/` → `medicamento_delete`
- **Template:** `farmacia/medicamento_confirm_delete.html`
- **Login requerido:** Sí
- **Parámetros URL:** `pk` (ID del medicamento)

---

### 10. **ProveedorListView**
- **Tipo:** Class-Based View (CBV) - Generic ListView
- **Línea:** 307
- **Herencia:** `LoginRequiredMixin`, `ListView`
- **Propósito:** Lista todos los proveedores
- **Docstring:** No tiene
- **Propiedades:**
  - `model` = `Proveedor`
  - `template_name` = `farmacia/proveedor_list.html`
  - `context_object_name` = `proveedores`
- **URL asociada:** `proveedores/` → `proveedor_list`
- **Login requerido:** Sí

---

### 11. **ProveedorDetailView**
- **Tipo:** Class-Based View (CBV) - Generic DetailView
- **Línea:** 318
- **Herencia:** `LoginRequiredMixin`, `DetailView`
- **Propósito:** Muestra detalles de un proveedor
- **Docstring:** No tiene
- **Propiedades:**
  - `model` = `Proveedor`
  - `template_name` = `farmacia/proveedor_detail.html`
  - `context_object_name` = `proveedor`
- **URL asociada:** `proveedores/<int:pk>/` → `proveedor_detail`
- **Login requerido:** Sí

---

### 12. **ProveedorCreateView**
- **Tipo:** Class-Based View (CBV) - Generic CreateView
- **Línea:** 330
- **Herencia:** `LoginRequiredMixin`, `CreateView`
- **Propósito:** Crea nuevos proveedores
- **Docstring:** No tiene
- **Propiedades:**
  - `model` = `Proveedor`
  - `template_name` = `farmacia/proveedor_form.html`
  - `form_class` = `ProveedorForm`
- **URL asociada:** `proveedores/nuevo/` → `proveedor_create`
- **Login requerido:** Sí
- **Método especial:** `get_success_url()` redirige a detalle del proveedor creado

---

### 13. **ProveedorUpdateView**
- **Tipo:** Class-Based View (CBV) - Generic UpdateView
- **Línea:** 343
- **Herencia:** `LoginRequiredMixin`, `UpdateView`
- **Propósito:** Edita proveedores existentes
- **Docstring:** No tiene
- **Propiedades:**
  - `model` = `Proveedor`
  - `template_name` = `farmacia/proveedor_form.html`
  - `form_class` = `ProveedorForm`
- **URL asociada:** `proveedores/editar/<int:pk>/` → `proveedor_update`
- **Login requerido:** Sí

---

### 14. **ProveedorDeleteView**
- **Tipo:** Class-Based View (CBV) - Generic DeleteView
- **Línea:** 353
- **Herencia:** `LoginRequiredMixin`, `DeleteView`
- **Propósito:** Elimina proveedores
- **Docstring:** No tiene
- **Propiedades:**
  - `model` = `Proveedor`
  - `template_name` = `farmacia/proveedor_confirm_delete.html`
  - `success_url` = `reverse_lazy('proveedor_list')`
- **URL asociada:** `proveedores/eliminar/<int:pk>/` → `proveedor_delete`
- **Login requerido:** Sí

---

### 15. **dashboard**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 367
- **Decoradores:**
  - `@login_required(login_url='inicio_sesion')` - Requiere autenticación
  - `@cache_page(60 * 60)` - Cache de 1 hora
- **Propósito:** Dashboard con estadísticas de ventas y stock
- **Docstring:** Sí
  - "Dashboard con estadísticas de ventas y stock. Resultado cacheado por 1 hora para mejorar performance."
- **URL asociada:** `dashboard/` → `dashboard`
- **Template:** `dashboard.html`
- **Caché:** Sí (1 hora) con key `dashboard_data`
- **Contexto calculado:**
  - `medicamentos` - Todos los medicamentos con `nivel_stock`
  - `stock_vendido` - Total de cantidad vendida
  - `total_ventas` - Conteo de ventas
  - `monto_total_vendido` - Suma de precios vendidos
  - `medicamentos_vendidos` - Lista de nombres de medicamentos vendidos
  - `ventas_semanales` - Agrupar por semana con suma de precios
  - `ventas_mensuales` - Agrupar por mes con suma de precios
  - `ventas_anuales` - Agrupar por año con suma de precios

---

### 16. **dashboard_inventario**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 431
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Dashboard con alertas de vencimiento y estado del inventario
- **Docstring:** Sí
  - "Dashboard con alertas de vencimiento y estado del inventario. Muestra medicamentos próximos a vencer (<7 días)."
- **URL asociada:** `inventario/dashboard/` → `dashboard_inventario`
- **Template:** `farmacia/dashboard_inventario.html`
- **Contexto calculado:**
  - `medicamentos_alerta` - Medicamentos próximos a vencer (< 7 días)
  - `lotes_vencidos` - Lotes con fecha_vencimiento < hoy
  - `lotes_criticos` - Lotes con vencimiento entre hoy y hoy+7 días
  - `total_medicamentos` - Count total
  - `medicamentos_agotados` - Count con stock=0
  - `cantidad_alertas` - Count de medicamentos con alerta
  - `cantidad_vencidos` - Count de lotes vencidos

---

### 17. **gestor_lotes**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 469
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Gestor visual de lotes de medicamentos
- **Docstring:** Sí
  - "Gestor visual de lotes de medicamentos. Permite ver stock por lote, vencimientos, y gestionar devoluciones."
- **URL asociada:** `inventario/lotes/` → `gestor_lotes`
- **Template:** `farmacia/gestor_lotes.html`
- **GET params:**
  - `medicamento` (id) - Filtrar por medicamento específico
- **Lógica:**
  - Si hay medicamento_id: muestra lotes ordenados por vencimiento
  - Si no: muestra lotes próximos a vencer (< 30 días), máx 50
- **Contexto:**
  - `lotes` - Lista de lotes filtrados
  - `medicamento_seleccionado` - Medicamento actual o None
  - `medicamentos` - Todos los medicamentos (para selector)

---

### 18. **reporte_lotes**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 507
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Reporte completo de lotes
- **Docstring:** Sí
  - "Reporte completo de lotes. Muestra stock por lote, vencimientos próximos, y lotes vencidos."
- **URL asociada:** `inventario/reporte-lotes/` → `reporte_lotes`
- **Template:** `farmacia/reporte_lotes.html`
- **Contexto calculado:**
  - `lotes_vigentes` - Lotes con fecha_vencimiento >= hoy y cantidad > 0
  - `lotes_criticos` - Lotes con vencimiento en próximos 7 días
  - `lotes_vencidos` - Lotes con fecha_vencimiento < hoy y cantidad > 0
  - `total_stock_vigente` - Suma de cantidad en lotes vigentes
  - `total_stock_critico` - Suma de cantidad en lotes críticos
  - `total_stock_vencido` - Suma de cantidad en lotes vencidos
  - `fecha_hoy` - Fecha actual

---

## 🔶 VISTAS EN farmacia/views_pos_v2.py

### 1. **terminal_pos_v2**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 50
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Terminal POS v2 - Vista principal de punto de venta
- **Docstring:** Sí
  - "Terminal POS v2 - Vista principal. Muestra búsqueda de medicamentos y carrito actualizado."
  - "GET: Mostrar búsqueda + carrito"
  - "POST: Buscar medicamento (vía AJAX)"
- **URL asociada:** `pos/` → `terminal_pos_v2`
- **Template:** `farmacia/pos_v2/terminal_pos_v2.html`
- **GET params:**
  - `busqueda` (str) - Búsqueda por nombre, SKU o laboratorio
- **Contexto:**
  - `carrito` - Carrito del vendedor actual
  - `items` - Items del carrito
  - `medicamentos` - Medicamentos encontrados en búsqueda
  - `busqueda` - Término de búsqueda
  - `cantidad_items` - Count de items en carrito
  - `total_carrito` - Total a pagar
- **Lógica:**
  - Obtiene o crea carrito en estado 'EN_CONSTRUCCION'
  - Busca medicamentos con stock > 0
  - Recalcula totales del carrito

---

### 2. **pos_agregar_item**
- **Tipo:** Función-Based View (FBV) - AJAX
- **Línea:** 87
- **Decoradores:**
  - `@login_required(login_url='inicio_sesion')`
  - `@require_http_methods(["POST"])`
- **Propósito:** AJAX - Agrega medicamento al carrito
- **POST params:**
  - `cantidad` (int) - Cantidad a agregar
  - `receta_id` (int, optional) - ID de receta si requiere
- **Returns:** JSON
- **Validaciones:**
  - Cantidad > 0
  - Cantidad <= stock disponible
  - Si requiere receta: debe proporcionarse receta válida
- **Lógica:**
  - Obtiene o crea CarritoItem
  - Si ya existe: incrementa cantidad
  - Calcula totales
  - Retorna JSON con estado

---

### 3. **pos_agregar_por_codigo_barras**
- **Tipo:** Función-Based View (FBV) - AJAX
- **Línea:** 143
- **Decoradores:**
  - `@login_required(login_url='inicio_sesion')`
  - `@require_http_methods(["POST"])`
- **Propósito:** AJAX - Busca por código de barras (SKU) y agrega al carrito
- **POST params:**
  - `codigo_barras` (str) - SKU del medicamento
  - `cantidad` (int, default=1) - Cantidad
  - `receta_id` (int, optional) - ID de receta si requiere
- **Returns:** JSON
- **Búsqueda:**
  - Por SKU exacto
  - Por nombre (icontains)
- **Validaciones:** Iguales a `pos_agregar_item`

---

### 4. **pos_eliminar_item**
- **Tipo:** Función-Based View (FBV) - AJAX
- **Línea:** 219
- **Decoradores:**
  - `@login_required(login_url='inicio_sesion')`
  - `@require_http_methods(["POST"])`
- **Propósito:** AJAX - Elimina medicamento del carrito
- **URL params:** `medicamento_id` (int)
- **Returns:** JSON
- **Contexto:** Carrito actualizado

---

### 5. **pos_vaciar_carrito**
- **Tipo:** Función-Based View (FBV) - AJAX
- **Línea:** 245
- **Decoradores:**
  - `@login_required(login_url='inicio_sesion')`
  - `@require_http_methods(["POST"])`
- **Propósito:** AJAX - Limpia carrito completo
- **Returns:** JSON con carrito vacío

---

### 6. **pos_aplicar_descuento**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 274
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Aplica descuento al carrito
- **GET:** Muestra formulario
- **POST:** Procesa descuento
- **URL asociada:** `pos/descuento/` → `pos_aplicar_descuento`
- **Template:** `farmacia/pos_v2/aplicar_descuento.html`
- **Form utilizado:** `AplicarDescuentoForm`
- **Contexto:**
  - `form` - Formulario de descuento
  - `carrito` - Carrito actual
- **Lógica:**
  - Obtiene tipo de descuento (PORCENTAJE o MONTO)
  - Aplica descuento al carrito
  - Redirige a procesar_pago

---

### 7. **pos_seleccionar_cliente**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 312
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Selecciona cliente para la venta (opcional)
- **GET:** Muestra formulario
- **POST:** Guarda cliente en carrito
- **URL asociada:** `pos/cliente/` → `pos_seleccionar_cliente`
- **Template:** `farmacia/pos_v2/seleccionar_cliente_v2.html`
- **Form utilizado:** `SeleccionarClienteV2Form`
- **Contexto:**
  - `form` - Formulario de cliente
  - `carrito` - Carrito actual
- **Lógica:**
  - Si selecciona cliente: guarda en carrito
  - Si no: marca como venta sin cliente
  - Redirige a procesar_pago

---

### 8. **pos_procesar_pago**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 353
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Procesa el pago y completa la venta
- **GET:** Muestra formulario de pago
- **POST:** Procesa pago en transacción atómica
- **URL asociada:** `pos/pago/` → `pos_procesar_pago`
- **Template:** `farmacia/pos_v2/procesar_pago_v2.html`
- **Form utilizado:** `ProcesarPagoV2Form`
- **Validaciones previas:**
  - Carrito no vacío
  - Stock suficiente para todos items
  - Recetas requeridas validadas
- **En transacción atómica (@transaction.atomic()):**
  1. Genera número de venta, boleta, folio
  2. Crea objeto Boleta
  3. Crea objeto Pago
  4. Crea objeto Venta principal
  5. Registra auditoría de recetas
  6. Descuenta stock y registra en HistorialStock
  7. Marca carrito como COMPLETADO
  8. Guarda IDs en sesión
  9. Envía boleta por email si existe
- **Contexto:**
  - `form` - Formulario de pago
  - `carrito` - Carrito actual
  - `total_a_pagar` - Total final

---

### 9. **pos_mostrar_boleta**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 454
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Muestra la boleta de la última venta
- **URL asociada:** 
  - `pos/boleta/` → `pos_mostrar_boleta`
  - `pos/boleta/<int:boleta_id>/` → `pos_mostrar_boleta_id`
- **URL params:** `boleta_id` (int, opcional)
- **Template:** `farmacia/pos_v2/boleta.html`
- **Lógica:**
  - Si no hay boleta_id: obtiene de sesión ('ultima_boleta_id')
  - Si no hay en sesión: redirige a terminal_pos_v2
  - Muestra boleta con todos los detalles
- **Contexto:**
  - `boleta` - Objeto Boleta
  - `carrito` - Carrito asociado
  - `items` - Items del carrito
  - `pago` - Objeto Pago

---

### 10. **pos_anular_venta**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 487
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Anula una venta completada (requiere staff)
- **POST:** Procesa anulación
- **URL asociada:** `pos/anular/<str:numero_venta>/` → `pos_anular_venta`
- **URL params:** `numero_venta` (str)
- **Template:** `farmacia/pos_v2/anular_venta.html`
- **Restricción:** Solo usuarios staff
- **Form utilizado:** `AnularVentaForm`
- **En transacción atómica:**
  1. Cambia estado venta a 'ANULADA'
  2. Genera NotaCredito
  3. Revierte stock del medicamento
  4. Registra en HistorialStock como ANULACION
- **Contexto:**
  - `form` - Formulario de anulación
  - `venta` - Objeto Venta a anular

---

### 11. **pos_procesar_devolucion**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 541
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Procesa devolución de medicamento
- **POST:** Procesa devolvución
- **URL asociada:** `pos/devolver/<str:numero_venta>/` → `pos_procesar_devolucion`
- **URL params:** `numero_venta` (str)
- **Template:** `farmacia/pos_v2/procesar_devolucion.html`
- **Form utilizado:** `ProcesarDevolucionForm`
- **En transacción atómica:**
  1. Obtiene cantidad a devolver
  2. Genera NotaCredito (requiere aprobación si cantidad > venta/2)
  3. Revierte stock
  4. Registra en HistorialStock como DEVOLUCION
- **Contexto:**
  - `form` - Formulario de devolución
  - `venta` - Objeto Venta

---

### 12. **pos_historial_ventas**
- **Tipo:** Función-Based View (FBV)
- **Línea:** 596
- **Decorador:** `@login_required(login_url='inicio_sesion')`
- **Propósito:** Muestra historial de ventas con opciones para anular/devolver
- **URL asociada:** `pos/historial/` → `pos_historial_ventas`
- **Template:** `farmacia/pos_v2/historial_ventas.html`
- **GET params:**
  - `estado` (str) - Filtrar por estado (COMPLETADA, ANULADA, etc.)
  - `fecha_desde` (date) - Filtrar ventas desde esta fecha
  - `page` (int) - Página (20 por página)
- **Lógica:**
  - Si usuario es staff: muestra todas las ventas
  - Si no: muestra solo ventas del usuario (vendedor)
  - Aplica filtros
  - Ordena por fecha descendente
- **Contexto:**
  - `ventas` - Lista de ventas filtradas
  - `filtro_estado` - Estado actual
  - `filtro_fecha_desde` - Fecha desde actual

---

## 🔵 URLs EN farmacia/urls.py

### GRUPO: Autenticación y Sesión

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `accounts/` | (incluida) | `django.contrib.auth.urls` | GET, POST | URLs de autenticación de Django |
| `` | `inicio_sesion` | `InicioSesionView` | GET, POST | Página de inicio de sesión |
| `registro/` | `registro_usuario` | `RegistroUsuarioView` | GET, POST | Página de registro de usuarios |
| `cerrar_sesion/` | `cerrar_sesion` | `CerrarSesionView` | GET | Cierra sesión del usuario |

---

### GRUPO: Página Principal

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `farmacia_main/` | `farmacia_main` | `FarmaciaMainView` | GET | Dashboard principal de la farmacia |
| `dashboard/` | `dashboard` | `dashboard` (FBV) | GET | Dashboard con estadísticas de ventas |

---

### GRUPO: Terminal POS v2 (Unificada - INTERFAZ ÚNICA DE VENTAS)

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `pos/` | `terminal_pos_v2` | `terminal_pos_v2` (FBV) | GET | Terminal POS v2 - busqueda + carrito |
| `pos/agregar/<int:medicamento_id>/` | `pos_agregar_item` | `pos_agregar_item` (FBV) | POST | AJAX - agrega medicamento al carrito |
| `pos/codigo_barras/` | `pos_agregar_codigo_barras` | `pos_agregar_por_codigo_barras` (FBV) | POST | AJAX - agrega por código de barras |
| `pos/eliminar/<int:medicamento_id>/` | `pos_eliminar_item` | `pos_eliminar_item` (FBV) | POST | AJAX - elimina del carrito |
| `pos/vaciar/` | `pos_vaciar_carrito` | `pos_vaciar_carrito` (FBV) | POST | AJAX - limpia carrito |
| `pos/descuento/` | `pos_aplicar_descuento` | `pos_aplicar_descuento` (FBV) | GET, POST | Aplicar descuento |
| `pos/cliente/` | `pos_seleccionar_cliente` | `pos_seleccionar_cliente` (FBV) | GET, POST | Seleccionar cliente |
| `pos/pago/` | `pos_procesar_pago` | `pos_procesar_pago` (FBV) | GET, POST | Procesar pago |
| `pos/boleta/` | `pos_mostrar_boleta` | `pos_mostrar_boleta` (FBV) | GET | Mostrar última boleta |
| `pos/boleta/<int:boleta_id>/` | `pos_mostrar_boleta_id` | `pos_mostrar_boleta` (FBV) | GET | Mostrar boleta específica |
| `pos/anular/<str:numero_venta>/` | `pos_anular_venta` | `pos_anular_venta` (FBV) | GET, POST | Anular venta |
| `pos/devolver/<str:numero_venta>/` | `pos_procesar_devolucion` | `pos_procesar_devolucion` (FBV) | GET, POST | Procesar devolución |
| `pos/historial/` | `pos_historial_ventas` | `pos_historial_ventas` (FBV) | GET | Historial de ventas |

---

### GRUPO: Inventario

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `inventario/dashboard/` | `dashboard_inventario` | `dashboard_inventario` (FBV) | GET | Dashboard de inventario con alertas |
| `inventario/lotes/` | `gestor_lotes` | `gestor_lotes` (FBV) | GET | Gestor visual de lotes |
| `inventario/reporte-lotes/` | `reporte_lotes` | `reporte_lotes` (FBV) | GET | Reporte completo de lotes |

---

### GRUPO: Medicamentos (CRUD)

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `medicamentos/` | `medicamento_list` | `MedicamentoListView` | GET | Lista todos los medicamentos |
| `medicamentos/<int:pk>/` | `medicamento_detail` | `MedicamentoDetailView` | GET | Detalle de medicamento |
| `medicamentos/nuevo/` | `medicamento_create` | `MedicamentoCreateView` | GET, POST | Crear nuevo medicamento |
| `medicamentos/<int:pk>/editar/` | `medicamento_update` | `MedicamentoUpdateView` | GET, POST | Editar medicamento |
| `medicamentos/<int:pk>/eliminar/` | `medicamento_delete` | `MedicamentoDeleteView` | GET, POST | Eliminar medicamento |

---

### GRUPO: Proveedores (CRUD)

| Ruta | Nombre | Vista | Método HTTP | Descripción |
|------|--------|-------|-------------|-------------|
| `proveedores/` | `proveedor_list` | `ProveedorListView` | GET | Lista todos los proveedores |
| `proveedores/<int:pk>/` | `proveedor_detail` | `ProveedorDetailView` | GET | Detalle de proveedor |
| `proveedores/nuevo/` | `proveedor_create` | `ProveedorCreateView` | GET, POST | Crear nuevo proveedor |
| `proveedores/editar/<int:pk>/` | `proveedor_update` | `ProveedorUpdateView` | GET, POST | Editar proveedor |
| `proveedores/eliminar/<int:pk>/` | `proveedor_delete` | `ProveedorDeleteView` | GET, POST | Eliminar proveedor |

---

## 📊 RESUMEN DE ESTADÍSTICAS

### Vistas por tipo:

| Tipo | Cantidad | Ubicación |
|------|----------|-----------|
| **Class-Based Views (CBV)** | 14 | `views.py` |
| **Function-Based Views (FBV)** | 12 | `views.py` + `views_pos_v2.py` |
| **Generic Views (CreateView, UpdateView, DeleteView, ListView, DetailView)** | 10 | `views.py` |
| **TOTAL VISTAS** | **26** | - |

### Vistas por módulo:

| Módulo | Cantidad | Categoría |
|--------|----------|-----------|
| `views.py` | 18 | Gestión general, inventario, dashboard |
| `views_pos_v2.py` | 12 | Terminal POS, pagos, devoluciones |

### Estadísticas de URLs:

| Categoría | Cantidad |
|-----------|----------|
| URLs de autenticación | 4 |
| URLs de POS v2 | 13 |
| URLs de inventario | 3 |
| URLs de medicamentos (CRUD) | 5 |
| URLs de proveedores (CRUD) | 5 |
| URLs principales | 2 |
| **TOTAL URLs** | **32** |

### Decoradores más usados:

| Decorador | Frecuencia | Propósito |
|-----------|-----------|----------|
| `@login_required` | 12 | Requiere autenticación |
| `@require_http_methods` | 5 | Restringe métodos HTTP |
| `@cache_page` | 1 | Cachea vista por tiempo |
| `LoginRequiredMixin` | 13 | Mixin de autenticación |

### Modelos relacionados principales:

| Modelo | Vistas que usa | Descripción |
|--------|---|---|
| `Medicamento` | 6 | Medicamentos del inventario |
| `Proveedor` | 5 | Proveedores de medicamentos |
| `CarritoVenta` | 9 | Carrito de compra (POS v2) |
| `Boleta` | 3 | Documento de venta |
| `Venta` | 4 | Registro de venta |
| `Cliente` | 3 | Información de clientes |
| `Receta` | 2 | Recetas médicas |
| `LoteMedicamento` | 3 | Lotes de medicamentos |

### Features especiales por vista:

| Vista | Features |
|-------|----------|
| `dashboard` | ⏱️ Caché de 1 hora, Estadísticas semanales/mensuales/anuales |
| `pos_procesar_pago` | 🔄 Transacción atómica, Auditoría de recetas, Email |
| `MedicamentoListView` | 🔍 6 filtros por tipo de venta |
| `gestor_lotes` | 📦 Filtro por medicamento, alertas de vencimiento |
| `pos_historial_ventas` | 📊 Filtros por estado y fecha, Paginación |
| `pos_anular_venta` | 🔐 Solo staff, Generación NotaCredito |

---

## 🔗 RELACIONES DE NAVEGACIÓN

```
inicio_sesion (/) 
    ↓
farmacia_main → dashboard
                  ↓
              medicamentos/ → medicamento_detail → medicamento_update/delete
                                               → medicamento_create
              
              proveedores/ → proveedor_detail → proveedor_update/delete
                                             → proveedor_create

              inventario/ → dashboard_inventario
                         → gestor_lotes
                         → reporte_lotes

              pos/ → pos_agregar_item/codigo_barras
                  → pos_descuento
                  → pos_cliente
                  → pos_pago → pos_boleta
                            → pos_historial_ventas → pos_anular_venta
                                                   → pos_devolver
```

---

## 📝 NOTAS IMPORTANTES

1. **Terminal POS v2 es la INTERFAZ ÚNICA de ventas** - Todas las operaciones de venta se realizan a través de esta interfaz
2. **Transacciones atómicas** en operaciones críticas (pago, anulación, devolución)
3. **Validaciones de receta obligatorias** en backend antes de agregar medicamentos
4. **Caché de 1 hora** en dashboard para optimizar performance
5. **Modelo de permisos** basado en `LoginRequiredMixin` y `@login_required`
6. **Sistema de auditoría** en operaciones de recetas y stock

---

**Generado:** Mayo 2026  
**Sistema:** Sistema de Farmacia - Collico  
**Versión:** Fase 3 (POS v2 implementado)
