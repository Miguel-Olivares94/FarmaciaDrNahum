# farmacia/views.py
from .forms import CaseInsensitiveAuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Medicamento, Proveedor, Venta, DetalleVenta
from .forms import MedicamentoForm, ProveedorForm, VentaForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db import models
from django.db import transaction
from .permissions import puede_editar_venta, registrar_auditoria, get_client_ip



############################################ VISTAS ###############################################################################


######   Se define una clase basada en View para manejar el registro de usuarios ####


class RegistroUsuarioView(View):
    
    # Se especifica la plantilla que se utilizará para renderizar la página de registro
    template_name = 'farmacia/registro_usuario.html'

    # Método para manejar las solicitudes GET (al cargar la página)
    def get(self, request):
        # Crear una instancia del formulario de creación de usuarios
        form = UserCreationForm()
        # Renderizar la página de registro con el formulario
        return render(request, self.template_name, {'form': form})

    # Método para manejar las solicitudes POST (al enviar el formulario)
    def post(self, request):
        # Crear una instancia del formulario de creación de usuarios con los datos del POST
        form = UserCreationForm(request.POST)
        
        # Verificar si el formulario es válido
        if form.is_valid():
            # Guardar el usuario en la base de datos
            user = form.save()
            # Obtener el nombre de usuario y contraseña limpios del formulario
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            
            # Autenticar al usuario recién creado
            user = authenticate(username=username, password=password)

            # Verificar si la autenticación fue exitosa
            if user is not None:
                # Iniciar sesión para el usuario autenticado
                login(request, user)
                # Mostrar un mensaje de éxito
                messages.success(request, '¡Registro exitoso!')
                # Redirigir al usuario a una URL específica (en este caso, 'farmacia_main')
                return redirect(reverse_lazy('farmacia_main'))
            else:
                # Si la autenticación falla, mostrar un mensaje de error
                messages.error(request, 'Error en el registro. Por favor, inténtalo de nuevo.')

        # Si el formulario no es válido, volver a renderizar el formulario con errores
        return render(request, self.template_name, {'form': form})
    
    
    


########### Se define una clase basada en View para manejar la vista de inicio de sesión##########

class InicioSesionView(View):
    template_name = 'farmacia/inicio_sesion.html'
    authentication_form = CaseInsensitiveAuthenticationForm

    def get(self, request):
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Aquí es donde usamos tu formulario de registro con el campo de email
            email = form.cleaned_data.get('email')

            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect(reverse_lazy('farmacia_main'))

        return render(request, self.template_name, {'form': form})
    
    
    
############## Se define una clase basada en View para manejar la vista de cierre de sesión ############################

class CerrarSesionView(View):
    
    # Método para manejar las solicitudes GET (al cargar la página)
    def get(self, request):
        # Cerrar la sesión del usuario actual
        logout(request)
        # Redirigir al usuario a la página de inicio de sesión ('inicio_sesion')
        return redirect('inicio_sesion')





# vista del menú principal de la farmacia 



############# Se define una clase basada en View para manejar la vista principal de la farmacia ########

class FarmaciaMainView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    # Se especifica la plantilla que se utilizará para renderizar la página principal
    template_name = 'farmacia/farmacia_main.html'

    # Método para manejar las solicitudes GET (al cargar la página)
    def get(self, request):
        # Obtener el total de medicamentos en la base de datos
        total_medicamentos = Medicamento.objects.count()
        # Obtener la cantidad de medicamentos con stock agotado
        medicamentos_agotados = Medicamento.objects.filter(stock=0).count()

        # Crear un diccionario de contexto con la información obtenida
        context = {
            'total_medicamentos': total_medicamentos,
            'medicamentos_agotados': medicamentos_agotados,
        }

        # Renderizar la página principal con el contexto proporcionado
        return render(request, self.template_name, context)



####################################### Vistas de medicametos #################################################




###### Vista de inventario medicamento ######


########### Se define una clase basada en View para manejar la vista de lista de medicamentos #############
class MedicamentoListView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    # Se especifica la plantilla que se utilizará para renderizar la lista de medicamentos
    template_name = 'farmacia/medicamento_list.html'

    # Método para manejar las solicitudes GET (al cargar la página)
    def get(self, request):
        
        # Obtener todos los medicamentos de la base de datos
        medicamentos = Medicamento.objects.all()
        
        # Filtro por tipo de venta (receta)
        filtro = request.GET.get('filtro', 'todos')
        titulo_filtro = 'Todos los Medicamentos'
        
        if filtro == 'receta':
            # Mostrar solo medicamentos que requieren receta
            medicamentos = [m for m in medicamentos if m.requiere_receta()]
            titulo_filtro = 'Medicamentos que Requieren Receta'
        elif filtro == 'receta_simple':
            medicamentos = [m for m in medicamentos if m.tipo_venta == 'receta_simple']
            titulo_filtro = 'Medicamentos - Receta Simple'
        elif filtro == 'receta_retenida':
            medicamentos = [m for m in medicamentos if m.tipo_venta == 'receta_retenida']
            titulo_filtro = 'Medicamentos - Receta Retenida'
        elif filtro == 'controlado':
            medicamentos = [m for m in medicamentos if m.tipo_venta == 'controlado']
            titulo_filtro = 'Medicamentos - Controlados'
        elif filtro == 'libre':
            medicamentos = [m for m in medicamentos if m.tipo_venta == 'libre']
            titulo_filtro = 'Medicamentos - Venta Libre'

        # KPI calculados en la vista
        stock_total = sum(m.stock for m in medicamentos)
        bajo_stock = sum(1 for m in medicamentos if m.stock > 0 and m.stock < 100)
        agotados = sum(1 for m in medicamentos if m.stock == 0)
        
        context = {
            'medicamentos': medicamentos,
            'stock_total': stock_total,
            'bajo_stock': bajo_stock,
            'agotados': agotados,
            'titulo_filtro': titulo_filtro,
            'filtro_activo': filtro,
        }
        
        return render(request, self.template_name, context)




###### Vista de Detalles de medicamento ######


class MedicamentoDetailView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    template_name = 'farmacia/medicamento_detail.html'

    def get(self, request, pk):
        medicamento = get_object_or_404(Medicamento, pk=pk)
        return render(request, self.template_name, {'medicamento': medicamento})
    
    


###### Vista de Detalles de medicamento ###### 



############### Se define una clase basada en View para manejar la vista de creación de medicamentos###############

class MedicamentoCreateView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    # Se especifica la plantilla que se utilizará para renderizar el formulario de creación
    template_name = 'farmacia/medicamento_form.html'

    # Método para manejar las solicitudes GET (al cargar la página)
    def get(self, request):
        # Crear una instancia del formulario de creación de medicamentos
        form = MedicamentoForm()
        # Renderizar la página de creación de medicamentos con el formulario vacío
        return render(request, self.template_name, {'form': form})

    # Método para manejar las solicitudes POST (al enviar el formulario)
    def post(self, request):
        # Crear una instancia del formulario de creación de medicamentos con los datos del POST
        form = MedicamentoForm(request.POST)
        
        # Verificar si el formulario es válido
        if form.is_valid():
            # Guardar el nuevo medicamento en la base de datos
            form.save()
            print("Medicamento guardado con éxito")
            # Redirigir a la lista de medicamentos
            return HttpResponseRedirect(reverse('medicamento_list'))
        else:
            # Si el formulario no es válido, imprimir errores en la consola
            print("Formulario no válido. Errores:")
            print(form.errors)
        
        # Si el formulario no es válido, volver a renderizar la página con errores
        return render(request, self.template_name, {'form': form})

    
    


###### Vista para Actualizar medicamento ###### 


class MedicamentoUpdateView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    template_name = 'farmacia/medicamento_form.html'

    def get(self, request, pk):
        medicamento = get_object_or_404(Medicamento, pk=pk)
        form = MedicamentoForm(instance=medicamento)
        return render(request, self.template_name, {'form': form, 'medicamento': medicamento})

    def post(self, request, pk):
        medicamento = get_object_or_404(Medicamento, pk=pk)
        form = MedicamentoForm(request.POST, instance=medicamento)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('medicamento_list'))
        return render(request, self.template_name, {'form': form, 'medicamento': medicamento})
    
    
    

###### Vista para Eliminar medicamento ###### 


class MedicamentoDeleteView(LoginRequiredMixin, View):
    login_url = 'inicio_sesion'
    template_name = 'farmacia/medicamento_confirm_delete.html'

    def get(self, request, pk):
        medicamento = get_object_or_404(Medicamento, pk=pk)
        return render(request, self.template_name, {'medicamento': medicamento})

    def post(self, request, pk):
        medicamento = get_object_or_404(Medicamento, pk=pk)
        medicamento.delete()
        return HttpResponseRedirect(reverse('medicamento_list'))
    
    
    
    
    
    

####################################### Vistas de medicametos #################################################



###### Vista del inventario de proveedores ###### 



class ProveedorListView(LoginRequiredMixin, ListView):
    login_url = 'inicio_sesion'
    model = Proveedor
    template_name = 'farmacia/proveedor_list.html'
    context_object_name = 'proveedores'


###### Vista del Detalle de Proveedor ###### 


class ProveedorDetailView(LoginRequiredMixin, DetailView):
    login_url = 'inicio_sesion'
    model = Proveedor
    template_name = 'farmacia/proveedor_detail.html'
    context_object_name = 'proveedor'



###### Vista para crear/guardar el proveedor ###### 


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    login_url = 'inicio_sesion'
    model = Proveedor
    template_name = 'farmacia/proveedor_form.html'
    form_class = ProveedorForm
    def get_success_url(self):
        return reverse('proveedor_detail', args=[str(self.object.id)])
    

###### Vista para actualizar de proveedor ###### 

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'inicio_sesion'
    model = Proveedor
    template_name = 'farmacia/proveedor_form.html'
    form_class = ProveedorForm
    
###### Vista para eliminar el proveedor ###### 

class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'inicio_sesion'
    model = Proveedor
    template_name = 'farmacia/proveedor_confirm_delete.html'
    success_url = reverse_lazy('proveedor_list')
    


####################################### Vistas de Dashboard #################################################
    


import json
from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear, TruncDate
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import Medicamento, Venta, Boleta, CarritoVenta

@login_required(login_url='inicio_sesion')
def dashboard(request):
    hoy = date.today()
    hace_7 = hoy - timedelta(days=6)
    hace_30 = hoy - timedelta(days=29)

    # ── KPIs principales ────────────────────────────────────────────
    ventas_hoy = Venta.objects.filter(
        fecha__date=hoy, estado='COMPLETADA'
    ).aggregate(total=Sum('precio'), count=Count('id'))

    ventas_mes = Venta.objects.filter(
        fecha__date__gte=hace_30, estado='COMPLETADA'
    ).aggregate(total=Sum('precio'), count=Count('id'))

    total_ventas_all = Venta.objects.filter(estado='COMPLETADA').aggregate(
        total=Sum('precio'), count=Count('id'), unidades=Sum('cantidad')
    )

    # ── Gráfico barras: ventas últimos 7 días ────────────────────────
    ventas_7dias = (
        Venta.objects
        .filter(fecha__date__gte=hace_7, estado='COMPLETADA')
        .annotate(dia=TruncDate('fecha'))
        .values('dia')
        .annotate(total=Sum('precio'), count=Count('id'))
        .order_by('dia')
    )
    labels_7dias = []
    data_montos = []
    data_count = []
    dias_map = {v['dia']: v for v in ventas_7dias}
    for i in range(7):
        d = hace_7 + timedelta(days=i)
        dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        labels_7dias.append(f"{dias_es[d.weekday()]} {d.day}/{d.month}")
        v = dias_map.get(d, {})
        data_montos.append(float(v.get('total') or 0))
        data_count.append(int(v.get('count') or 0))

    # ── Gráfico dona: métodos de pago ───────────────────────────────
    metodos = (
        Boleta.objects
        .filter(estado='EMITIDA')
        .values('metodo_pago')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    labels_metodos = [m['metodo_pago'] for m in metodos]
    data_metodos = [m['count'] for m in metodos]

    # ── Top 5 productos más vendidos ─────────────────────────────────
    top_productos = (
        Venta.objects
        .filter(estado='COMPLETADA')
        .values('medicamento__nombre')
        .annotate(total_uds=Sum('cantidad'), total_monto=Sum('precio'))
        .order_by('-total_uds')[:5]
    )

    # ── Alertas ──────────────────────────────────────────────────────
    stock_bajo = Medicamento.objects.filter(stock__lt=50, stock__gt=0).count()
    agotados = Medicamento.objects.filter(stock=0).count()
    vencen_pronto = Medicamento.objects.filter(
        fecha_vencimiento__lte=hoy + timedelta(days=30),
        fecha_vencimiento__gte=hoy
    ).count()

    # ── Medicamentos bajo stock (para tabla) ─────────────────────────
    meds_bajo_stock = Medicamento.objects.filter(stock__lt=100).order_by('stock')[:10]

    # ── Ventas semanales/mensuales/anuales (legacy) ──────────────────
    ventas_semanales = (
        Venta.objects.annotate(week=TruncWeek('fecha'))
        .values('week').annotate(total=Sum('precio')).order_by('-week')[:4]
    )
    ventas_mensuales = (
        Venta.objects.annotate(month=TruncMonth('fecha'))
        .values('month').annotate(total=Sum('precio')).order_by('-month')[:6]
    )
    ventas_anuales = (
        Venta.objects.annotate(year=TruncYear('fecha'))
        .values('year').annotate(total=Sum('precio')).order_by('-year')[:3]
    )

    es_demo = request.user.username.endswith('_demo')

    context = {
        # KPIs
        'ventas_hoy_monto': ventas_hoy.get('total') or 0,
        'ventas_hoy_count': ventas_hoy.get('count') or 0,
        'ventas_mes_monto': ventas_mes.get('total') or 0,
        'ventas_mes_count': ventas_mes.get('count') or 0,
        'monto_total_vendido': total_ventas_all.get('total') or 0,
        'total_ventas': total_ventas_all.get('count') or 0,
        'stock_vendido': total_ventas_all.get('unidades') or 0,
        # Alertas
        'stock_bajo': stock_bajo,
        'agotados': agotados,
        'vencen_pronto': vencen_pronto,
        # Tabla bajo stock
        'medicamentos': meds_bajo_stock,
        # Gráficos (JSON para Chart.js)
        'labels_7dias_json': json.dumps(labels_7dias),
        'data_montos_json': json.dumps(data_montos),
        'data_count_json': json.dumps(data_count),
        'labels_metodos_json': json.dumps(labels_metodos),
        'data_metodos_json': json.dumps(data_metodos),
        # Top productos
        'top_productos': top_productos,
        # Legacy
        'ventas_semanales': ventas_semanales,
        'ventas_mensuales': ventas_mensuales,
        'ventas_anuales': ventas_anuales,
        'es_demo': es_demo,
        'hoy': hoy,
    }
    return render(request, 'farmacia/dashboard.html', context)



   ############# Vista para realizar venta ############









class RegistroUsuarioView(View):
    template_name = 'farmacia/registro_usuario.html'

    def get(self, request):
        form = UserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, '¡Registro exitoso!')
                return redirect(reverse_lazy('farmacia_main'))  
            else:
                messages.error(request, 'Error en el registro. Por favor, inténtalo de nuevo.')

        # Si el formulario no es válido, vuelve a renderizar el formulario con errores
        return render(request, self.template_name, {'form': form})


# =====================================================================
# WEEK 3: VISTAS PARA STOCK TRANSACCIONAL CON FIFO
# =====================================================================


# =====================================================================
# WEEK 3: VISTAS PARA STOCK TRANSACCIONAL CON FIFO
# =====================================================================

@login_required(login_url='inicio_sesion')
def dashboard_inventario(request):
    """
    Dashboard con alertas de vencimiento y estado del inventario.
    Muestra medicamentos próximos a vencer (<7 días).
    """
    from .functions import obtener_medicamentos_con_alerta, obtener_lotes_vencidos
    from .models import Medicamento, LoteMedicamento
    
    # Medicamentos con alerta de vencimiento
    medicamentos_alerta = obtener_medicamentos_con_alerta()
    
    # Lotes vencidos
    lotes_vencidos = obtener_lotes_vencidos()
    
    # Estadísticas generales
    total_medicamentos = Medicamento.objects.count()
    medicamentos_agotados = Medicamento.objects.filter(stock=0).count()
    
    # Lotes próximos a vencer (<7 días)
    from datetime import date, timedelta
    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=7)
    
    lotes_criticos = LoteMedicamento.objects.filter(
        fecha_vencimiento__lte=fecha_alerta,
        fecha_vencimiento__gt=hoy,
        cantidad_disponible__gt=0
    ).order_by('fecha_vencimiento')[:10]
    
    context = {
        'medicamentos_alerta': medicamentos_alerta,
        'lotes_vencidos': lotes_vencidos,
        'lotes_criticos': lotes_criticos,
        'total_medicamentos': total_medicamentos,
        'medicamentos_agotados': medicamentos_agotados,
        'cantidad_alertas': medicamentos_alerta.count(),
        'cantidad_vencidos': lotes_vencidos.count()
    }
    
    return render(request, 'farmacia/dashboard_inventario.html', context)


@login_required(login_url='inicio_sesion')
def gestor_lotes(request):
    """
    Gestor visual de lotes de medicamentos.
    Permite ver stock por lote, vencimientos, y gestionar devoluciones.
    """
    from .models import LoteMedicamento, Medicamento
    from datetime import date, timedelta
    
    # Obtener medicamento filtrado (opcional)
    medicamento_id = request.GET.get('medicamento')
    
    if medicamento_id:
        medicamento = get_object_or_404(Medicamento, pk=medicamento_id)
        lotes = LoteMedicamento.objects.filter(medicamento=medicamento).order_by('fecha_vencimiento')
    else:
        medicamento = None
        # Mostrar lotes próximos a vencer
        hoy = date.today()
        fecha_alerta = hoy + timedelta(days=30)
        lotes = LoteMedicamento.objects.filter(
            fecha_vencimiento__lte=fecha_alerta,
            cantidad_disponible__gt=0
        ).order_by('fecha_vencimiento')[:50]
    
    medicamentos = Medicamento.objects.all()
    
    context = {
        'lotes': lotes,
        'medicamento_seleccionado': medicamento,
        'medicamentos': medicamentos
    }
    
    return render(request, 'farmacia/gestor_lotes.html', context)





@login_required(login_url='inicio_sesion')
def reporte_lotes(request):
    """
    Reporte completo de lotes.
    Muestra stock por lote, vencimientos próximos, y lotes vencidos.
    """
    from .models import LoteMedicamento, Medicamento
    from datetime import date, timedelta
    from django.db.models import Sum
    
    hoy = date.today()
    
    # Agrupar por estado
    lotes_vigentes = LoteMedicamento.objects.filter(
        fecha_vencimiento__gte=hoy,
        cantidad_disponible__gt=0
    ).order_by('fecha_vencimiento')
    
    lotes_criticos = lotes_vigentes.filter(
        fecha_vencimiento__lte=hoy + timedelta(days=7)
    )
    
    lotes_vencidos = LoteMedicamento.objects.filter(
        fecha_vencimiento__lt=hoy,
        cantidad_disponible__gt=0
    )
    
    # Totales
    total_stock_vigente = lotes_vigentes.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    total_stock_critico = lotes_criticos.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    total_stock_vencido = lotes_vencidos.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    
    context = {
        'lotes_vigentes': lotes_vigentes,
        'lotes_criticos': lotes_criticos,
        'lotes_vencidos': lotes_vencidos,
        'total_stock_vigente': total_stock_vigente,
        'total_stock_critico': total_stock_critico,
        'total_stock_vencido': total_stock_vencido,
        'fecha_hoy': hoy
    }
    
    return render(request, 'farmacia/reporte_lotes.html', context)



