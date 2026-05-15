# Manuales del Sistema de Gestión Farmacéutico

## ✅ Manuales Generados

Se han creado **DOS MANUALES COMPLETOS** en formato Word para el Sistema de Gestión Farmacéutico:

### 1. **MANUAL_COMPLETO_FARMACIA.docx**
**Para:** Vendedores, Dispensadores y Operadores del Sistema

**Contenido:**
- ✓ Introducción al sistema
- ✓ Acceso y login
- ✓ Gestión de medicamentos (búsqueda, filtros, stock)
- ✓ Operaciones POS (crear venta, agregar productos, finalizar)
- ✓ Control de recetas médicas
  - Validación de receta simple
  - Medicamentos controlados
  - Retención de recetas
- ✓ Reportes de ventas, stock y recetas
- ✓ Referencia rápida (flujo diario, atajos, códigos de color)

**Características:**
- 📊 Instrucciones paso a paso (53 pasos distribuidos)
- 🎨 Colores corporativos (verde farmacia)
- ⚠️ Cajas de advertencia para información crítica
- 📋 Tabla de roles y permisos
- 💡 Emojis para fácil identificación

---

### 2. **MANUAL_DJANGO_ADMIN_FARMACIA.docx**
**Para:** Administradores del Sistema

**Contenido:**
- ✓ Acceso al panel de administración Django
- ✓ Gestión completa de usuarios
- ✓ Administración de medicamentos (CRUD completo)
- ✓ Gestión de proveedores y distribuidores
- ✓ Auditoría de ventas
- ✓ Control de medicamentos controlados
- ✓ Reportes analíticos (ventas, stock, ingresos)
- ✓ Configuración del sistema
- ✓ Sistema de auditoría y logs
- ✓ Checklist de tareas administrativas regulares

**Características:**
- 🔧 Instrucciones técnicas detalladas
- 📊 Tablas de referencia rápida
- ✅ Checklist de tareas diarias/semanales/mensuales
- 🔐 Información de seguridad y permisos
- 📧 Datos de soporte técnico

---

## 🛠️ Scripts Utilizados

### `generar_manual_completo.py`
Genera el manual completo de operador (MANUAL_COMPLETO_FARMACIA.docx)

**Uso:**
```bash
python generar_manual_completo.py
```

**Dependencia:** python-docx
```bash
pip install python-docx
```

---

### `generar_manual_django_admin.py`
Genera el manual de administración Django (MANUAL_DJANGO_ADMIN_FARMACIA.docx)

**Uso:**
```bash
python generar_manual_django_admin.py
```

**Dependencia:** python-docx

---

## 📝 Cómo Personalizar los Manuales

### Información de Empresa
En ambos scripts, busca y edita estas variables:

```python
# Contactos
"admin@collichico.cl"          # Email soporte
"+56 2 XXXX XXXX"              # Teléfono
"+56 9 XXXX XXXX"              # WhatsApp emergencias
"Farmacia Collichico S.A."     # Nombre empresa
```

### Colores Corporativos
```python
PHARMACY_COLOR = RGBColor(0, 102, 51)      # Verde farmacia
ADMIN_COLOR = RGBColor(192, 0, 0)          # Rojo para alertas
```

---

## 📸 Agregar Capturas de Pantalla

**Próximos pasos:**

1. **Tomar screenshots** de cada pantalla del sistema:
   - Login
   - Dashboard
   - Tabla de medicamentos
   - Crear venta
   - Validación receta
   - Reportes
   - Panel Django Admin
   - etc.

2. **Crear carpeta** para guardar screenshots:
   ```
   screenshots/
   ├── 01_login.jpg
   ├── 02_dashboard.jpg
   ├── 03_medicamentos.jpg
   └── ...
   ```

3. **Editar los scripts** para incluir imágenes:
   ```python
   # Agregar esta línea en cada sección
   add_screenshot(doc, "screenshots/01_login.jpg", "Figura 1: Pantalla de Login")
   ```

4. **Regenerar manuales** ejecutando los scripts nuevamente

---

## 📊 Estructura de Contenido

### Manual Completo (Operador)
```
PORTADA
│
ÍNDICE
│
1. INTRODUCCIÓN
   - Qué es el sistema
   - Roles de usuario
│
2. ACCESO AL SISTEMA
   - Login
   - Roles y Permisos (tabla)
│
3. PANEL PRINCIPAL
   - Dashboard
   - Elementos y acceso rápido
│
4. GESTIÓN DE MEDICAMENTOS
   - Ver listado
   - Buscar y filtrar
   - Control de stock
│
5. OPERACIONES POS
   - Crear venta
   - Agregar medicamentos
   - Validación recetas
   - Finalizar venta
│
6. CONTROL DE RECETAS
   - Validación receta simple
   - Medicamentos controlados
   - Retención de recetas
│
7. REPORTES
   - Reportes de ventas
   - Reporte de stock
   - Reporte de recetas
│
8. ADMINISTRACIÓN
   - Gestión de usuarios (admin)
   - Gestión de medicamentos (admin)
   - Gestión de proveedores
│
9. REFERENCIA RÁPIDA
   - Flujo diario
   - Atajos de teclado
   - Códigos de color
   - Errores comunes
   - Soporte
```

### Manual Django Admin
```
PORTADA
│
ÍNDICE
│
1. INTRODUCCIÓN
   - Funciones administrativas
│
2. ACCESO
   - Login admin
   - Cambiar contraseña
│
3. DASHBOARD
   - Estadísticas
   - Acceso rápido
   - Acciones recientes
│
4. GESTIÓN DE USUARIOS
   - Ver lista
   - Crear usuario
   - Editar usuario
   - Desactivar usuario
│
5. GESTIÓN DE MEDICAMENTOS
   - Ver catálogo
   - Crear medicamento
   - Editar medicamento
   - Alertas de stock
│
6. GESTIÓN DE PROVEEDORES
   - Ver lista
   - Crear proveedor
   - Editar proveedor
│
7. GESTIÓN DE VENTAS
   - Ver todas las ventas
   - Ver detalle de venta
│
8. GESTIÓN DE RECETAS
   - Ver recetas
   - Auditar controlados
   - Recetas retenidas
│
9. REPORTES
   - Reportes de ventas
   - Reportes de stock
   - Reportes de ingresos
│
10. CONFIGURACIÓN
    - Información empresa
    - Configuración operativa
    - Configuración seguridad
│
11. AUDITORÍA
    - Historial cambios
    - Auditar precios
    - Auditar controlados
│
12. REFERENCIA RÁPIDA
    - Acciones comunes
    - Roles y permisos
    - Atajos
    - Checklist tareas
    - Soporte técnico
```

---

## 🎯 Casos de Uso

### Para Vendedor/Dispensador
> **Leer:** MANUAL_COMPLETO_FARMACIA.docx
> - Aprender a vender medicamentos
> - Validar recetas correctamente
> - Manejar medicamentos controlados
> - Consultar referencia rápida durante trabajo

### Para Administrador
> **Leer:** MANUAL_DJANGO_ADMIN_FARMACIA.docx
> - Crear cuentas de usuario
> - Administrar precios y stock
> - Auditar operaciones
> - Generar reportes
> - Mantener sistema funcionando

### Para Supervisor
> **Leer:** Ambos manuales
> - Entender operaciones de vendedores
> - Revisar auditoría y reportes
> - Validar medicamentos controlados
> - Supervisar equipo

---

## 📋 Checklist: Antes de Distribuir

- [ ] Personalizar contactos de soporte (email, teléfono)
- [ ] Revisar nombre de empresa (Farmacia Collichico)
- [ ] Agregar screenshots reales del sistema
- [ ] Revisar instrucciones específicas de tu sistema
- [ ] Probar links a imágenes si existen
- [ ] Imprimir para verificar formato en papel
- [ ] Distribuir a usuarios según su rol
- [ ] Recolectar feedback de usuarios
- [ ] Actualizar versión del manual si hay cambios

---

## 🔄 Mantener Manuales Actualizados

Si el sistema cambia:

1. **Editar los scripts Python**
2. **Regenerar manuales** ejecutando scripts
3. **Agregar nuevas secciones** si hay nuevas funcionalidades
4. **Incrementar versión:** 1.0 → 1.1 → 2.0
5. **Distribuir actualización** a usuarios

---

## 📞 Información de Soporte

Para preguntas sobre los manuales:
- 📧 Email: admin@collichico.cl
- ☎️ Teléfono: +56 2 XXXX XXXX (cambiar en scripts)
- 💬 WhatsApp: +56 9 XXXX XXXX (cambiar en scripts)

---

## 📄 Licencia

© 2026 Farmacia Collichico S.A. Todos los derechos reservados.

---

## 🚀 Próximas Mejoras

Posibles mejoras futuras:

- [ ] Agregar video tutoriales en QR
- [ ] Crear versión digital interactiva (HTML)
- [ ] Agregar módulo de FAQs
- [ ] Traducción a inglés
- [ ] Versión para dispositivos móviles
- [ ] Sistema de feedback en línea
- [ ] Búsqueda full-text en manuales

---

**Última actualización:** Mayo 2026
**Versión:** 1.0
