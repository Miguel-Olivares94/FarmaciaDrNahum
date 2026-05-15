
from django.contrib import admin
from .models import (
    Medicamento, Proveedor, Venta, DetalleVenta,
    HistorialStock, Cliente, LoteMedicamento, Devolucion,
    Receta, AuditoriaReceta,
)

# Medicamento Admin
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'tipo_venta', 'stock', 'precio', 'nivel_stock', 'fecha_vencimiento')
    list_filter = ('tipo_venta', 'nivel_stock', 'laboratorio', 'fecha_vencimiento')
    search_fields = ('nombre', 'sku')
    readonly_fields = ('fecha_ingreso', 'nivel_stock')

# Venta Admin
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicamento', 'cantidad', 'precio', 'vendedor', 'fecha')
    list_filter = ('fecha', 'vendedor')
    search_fields = ('medicamento__nombre', 'vendedor__username')
    readonly_fields = ('fecha',)

# HistorialStock Admin
class HistorialStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicamento', 'tipo', 'cantidad', 'usuario', 'fecha_creacion')
    list_filter = ('tipo', 'fecha_creacion', 'medicamento')
    search_fields = ('medicamento__nombre', 'usuario__username')
    readonly_fields = ('fecha_creacion', 'stock_anterior', 'stock_posterior')
    date_hierarchy = 'fecha_creacion'

# Cliente Admin
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'rut_dni', 'email', 'cliente_vip', 'fecha_registro')
    list_filter = ('cliente_vip', 'activo', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'rut_dni', 'email')
    readonly_fields = ('fecha_registro',)
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'rut_dni', 'email', 'telefono', 'fecha_nacimiento')
        }),
        ('Salud', {
            'fields': ('alergias', 'medicamentos_contraindicados')
        }),
        ('Estado', {
            'fields': ('cliente_vip', 'descuento_vip', 'activo', 'fecha_registro')
        }),
    )

# LoteMedicamento Admin
class LoteMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('medicamento', 'numero_lote', 'fecha_vencimiento', 'cantidad_disponible', 'proveedor')
    list_filter = ('fecha_vencimiento', 'proveedor', 'medicamento')
    search_fields = ('medicamento__nombre', 'numero_lote')
    readonly_fields = ('fecha_ingreso',)
    fieldsets = (
        ('Información del Lote', {
            'fields': ('medicamento', 'numero_lote', 'proveedor', 'precio_costo')
        }),
        ('Stock', {
            'fields': ('cantidad_ingresada', 'cantidad_disponible')
        }),
        ('Fechas', {
            'fields': ('fecha_ingreso', 'fecha_vencimiento')
        }),
    )

# Devolucion Admin
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicamento', 'cantidad', 'motivo', 'estado', 'fecha_registro')
    list_filter = ('estado', 'motivo', 'fecha_registro')
    search_fields = ('medicamento__nombre', 'venta__id')
    readonly_fields = ('fecha_registro', 'fecha_aprobacion')
    actions = ['aprobar_devoluciones']
    
    def aprobar_devoluciones(self, request, queryset):
        from datetime import datetime
        updated = queryset.filter(estado='registrada').update(
            estado='aprobada',
            usuario_aprueba=request.user,
            fecha_aprobacion=datetime.now()
        )
        self.message_user(request, f'{updated} devoluciones aprobadas')
    aprobar_devoluciones.short_description = "Aprobar devoluciones seleccionadas"

# Registrar modelos
admin.site.register(Medicamento, MedicamentoAdmin)
admin.site.register(Proveedor)
admin.site.register(Venta, VentaAdmin)
admin.site.register(DetalleVenta)
admin.site.register(HistorialStock, HistorialStockAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(LoteMedicamento, LoteMedicamentoAdmin)
admin.site.register(Devolucion, DevolucionAdmin)


# =====================================================================
# ADMIN: RECETAS Y AUDITORÍA
# =====================================================================

class RecetaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tipo', 'estado', 'nombre_paciente', 'rut_paciente',
        'nombre_medico', 'fecha_emision', 'registrada_por', 'fecha_registro',
    )
    list_filter = ('tipo', 'estado', 'fecha_emision')
    search_fields = ('nombre_paciente', 'rut_paciente', 'nombre_medico', 'numero_receta')
    readonly_fields = ('fecha_registro', 'registrada_por', 'verificada_por', 'fecha_verificacion')
    date_hierarchy = 'fecha_emision'
    fieldsets = (
        ('Tipo y Estado', {
            'fields': ('tipo', 'estado', 'motivo_rechazo')
        }),
        ('Datos del Médico', {
            'fields': ('nombre_medico', 'rut_medico', 'especialidad', 'codigo_prestador')
        }),
        ('Datos del Paciente', {
            'fields': ('nombre_paciente', 'rut_paciente')
        }),
        ('Datos de la Receta', {
            'fields': ('numero_receta', 'fecha_emision', 'fecha_vencimiento_receta', 'archivo_receta')
        }),
        ('Auditoría', {
            'fields': ('registrada_por', 'verificada_por', 'fecha_verificacion', 'fecha_registro'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.registrada_por = request.user
        super().save_model(request, obj, form, change)


class AuditoriaRecetaAdmin(admin.ModelAdmin):
    list_display = ('id', 'evento', 'usuario', 'medicamento', 'receta', 'ip_address', 'timestamp')
    list_filter = ('evento', 'timestamp')
    search_fields = ('usuario__username', 'medicamento__nombre', 'detalle')
    readonly_fields = ('evento', 'usuario', 'receta', 'medicamento', 'detalle', 'ip_address', 'timestamp')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False  # Registro sólo automático

    def has_change_permission(self, request, obj=None):
        return False  # Inmutable


admin.site.register(Receta, RecetaAdmin)
admin.site.register(AuditoriaReceta, AuditoriaRecetaAdmin)