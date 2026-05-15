from django.urls import path, include
from .views import CerrarSesionView
from .views import dashboard
from . import views
from . import views_pos_v2 

from .views import (
    FarmaciaMainView,
    MedicamentoListView,
    MedicamentoDetailView,
    MedicamentoCreateView,
    MedicamentoUpdateView,
    MedicamentoDeleteView,
    ProveedorListView,
    ProveedorDetailView,
    ProveedorCreateView,
    ProveedorUpdateView,
    ProveedorDeleteView,
    RegistroUsuarioView,
    InicioSesionView,
)


urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', dashboard, name='dashboard'),
    path('farmacia_main/', FarmaciaMainView.as_view(), name='farmacia_main'),
    
    path('registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('', InicioSesionView.as_view(), name='inicio_sesion'),
    path('cerrar_sesion/', CerrarSesionView.as_view(), name='cerrar_sesion'),
    
    # =====================================================================
    # RUTAS UNIFICADAS: TERMINAL POS v2 (ÚNICA INTERFAZ DE VENTAS)
    # =====================================================================
    path('pos/', views_pos_v2.terminal_pos_v2, name='terminal_pos_v2'),
    path('pos/agregar/<int:medicamento_id>/', views_pos_v2.pos_agregar_item, name='pos_agregar_item'),
    path('pos/codigo_barras/', views_pos_v2.pos_agregar_por_codigo_barras, name='pos_agregar_codigo_barras'),
    path('pos/eliminar/<int:medicamento_id>/', views_pos_v2.pos_eliminar_item, name='pos_eliminar_item'),
    path('pos/vaciar/', views_pos_v2.pos_vaciar_carrito, name='pos_vaciar_carrito'),
    path('pos/descuento/', views_pos_v2.pos_aplicar_descuento, name='pos_aplicar_descuento'),
    path('pos/cliente/', views_pos_v2.pos_seleccionar_cliente, name='pos_seleccionar_cliente'),
    path('pos/pago/', views_pos_v2.pos_procesar_pago, name='pos_procesar_pago'),
    path('pos/boleta/', views_pos_v2.pos_mostrar_boleta, name='pos_mostrar_boleta'),
    path('pos/boleta/<int:boleta_id>/', views_pos_v2.pos_mostrar_boleta, name='pos_mostrar_boleta_id'),
    path('pos/anular/<str:numero_venta>/', views_pos_v2.pos_anular_venta, name='pos_anular_venta'),
    path('pos/devolver/<str:numero_venta>/', views_pos_v2.pos_procesar_devolucion, name='pos_procesar_devolucion'),
    path('pos/historial/', views_pos_v2.pos_historial_ventas, name='pos_historial_ventas'),
    
    # =====================================================================
    # RUTAS DE INVENTARIO
    # =====================================================================
    path('inventario/dashboard/', views.dashboard_inventario, name='dashboard_inventario'),
    path('inventario/lotes/', views.gestor_lotes, name='gestor_lotes'),
    path('inventario/reporte-lotes/', views.reporte_lotes, name='reporte_lotes'),
    
    # =====================================================================
    # RUTAS DE MEDICAMENTOS
    # =====================================================================
    path('medicamentos/', MedicamentoListView.as_view(), name='medicamento_list'),
    path('medicamentos/<int:pk>/', MedicamentoDetailView.as_view(), name='medicamento_detail'),
    path('medicamentos/nuevo/', MedicamentoCreateView.as_view(), name='medicamento_create'),
    path('medicamentos/<int:pk>/editar/', MedicamentoUpdateView.as_view(), name='medicamento_update'),
    path('medicamentos/<int:pk>/eliminar/', MedicamentoDeleteView.as_view(), name='medicamento_delete'),
    
    # =====================================================================
    # RUTAS DE PROVEEDORES
    # =====================================================================
    path('proveedores/', ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/<int:pk>/', ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/nuevo/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/editar/<int:pk>/', ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/eliminar/<int:pk>/', ProveedorDeleteView.as_view(), name='proveedor_delete'),
]

