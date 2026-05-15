# farmacia/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Medicamento, Venta, Receta


class CaseInsensitiveAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación que permite login con username o email en minúsculas.
    """
    def clean_username(self):
        return self.cleaned_data['username'].lower()


class VentaForm(forms.ModelForm):
    """
    Formulario para crear una venta con validación de stock.
    Para medicamentos que requieren receta, proporciona campo receta_venta.
    """
    medicamento = forms.ModelChoiceField(
        queryset=Medicamento.objects.all(),
        label='Medicamento',
        empty_label='Seleccionar medicamento...'
    )
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=1000,
        label='Cantidad',
        error_messages={
            'min_value': 'La cantidad mínima es 1',
            'max_value': 'La cantidad máxima es 1000'
        }
    )
    receta_venta = forms.ModelChoiceField(
        queryset=Receta.objects.all(),
        label='Receta Médica (si requiere)',
        empty_label='Sin receta (medicamento libre)',
        required=False
    )
    
    class Meta:
        model = Venta
        fields = ['medicamento', 'cantidad', 'receta_venta']
    
    def clean(self):
        cleaned_data = super().clean()
        medicamento = cleaned_data.get('medicamento')
        cantidad = cleaned_data.get('cantidad')
        receta_venta = cleaned_data.get('receta_venta')
        
        if medicamento and cantidad:
            if medicamento.stock < cantidad:
                raise ValidationError(
                    f'Stock insuficiente. Disponible: {medicamento.stock}, Solicitado: {cantidad}'
                )
            
            # Validar que medicamentos que requieren receta tengan receta
            if medicamento.requiere_receta() and not receta_venta:
                raise ValidationError(
                    f'{medicamento.nombre} requiere RECETA MÉDICA. Por favor, proporcione una receta válida.'
                )
        return cleaned_data


class RegistrationForm(UserCreationForm):
    """
    Formulario de registro de usuario con validación de email único.
    """
    email = forms.EmailField(required=True)
    numero_celular = forms.CharField(max_length=15, required=False, label='Número Celular')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'numero_celular')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email


class MedicamentoForm(forms.ModelForm):
    """
    Formulario para crear/editar medicamentos con validación de fechas.
    """
    NIVEL_STOCK_CHOICES = [
        ('Alto', 'Alto'),
        ('Medio', 'Medio'),
        ('Bajo', 'Bajo'),
    ]
    
    nivel_stock = forms.ChoiceField(
        choices=NIVEL_STOCK_CHOICES,
        required=False,
        label='Nivel de Stock'
    )

    class Meta:
        model = Medicamento
        fields = '__all__'
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_ingreso = cleaned_data.get('fecha_ingreso')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        
        if fecha_ingreso and fecha_vencimiento:
            if fecha_vencimiento <= fecha_ingreso:
                raise ValidationError(
                    'La fecha de vencimiento debe ser posterior a la fecha de ingreso.'
                )
        
        return cleaned_data


class ProveedorForm(forms.ModelForm):
    """
    Formulario para crear/editar proveedores con validación de RUT chileno.
    """
    
    class Meta:
        from .models import Proveedor
        model = Proveedor
        fields = ['nombre', 'razon_social', 'rut', 'direccion', 'email', 'fono', 'productos']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre comercial',
                'class': 'form-control'
            }),
            'razon_social': forms.TextInput(attrs={
                'placeholder': 'Razón social',
                'class': 'form-control'
            }),
            'rut': forms.TextInput(attrs={
                'placeholder': 'Ej: 12.345.678-9',
                'class': 'form-control'
            }),
            'direccion': forms.TextInput(attrs={
                'placeholder': 'Dirección',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'email@proveedor.cl',
                'class': 'form-control'
            }),
            'fono': forms.TextInput(attrs={
                'placeholder': '+56 9 XXXX XXXX',
                'class': 'form-control'
            }),
            'productos': forms.Textarea(attrs={
                'placeholder': 'Descripción de productos disponibles',
                'rows': 4,
                'class': 'form-control'
            }),
        }
    
    def clean_rut(self):
        """Valida RUT chileno básico: formato XX.XXX.XXX-X"""
        rut = self.cleaned_data.get('rut').strip()
        
        # Eliminar puntos y guión
        rut_clean = rut.replace('.', '').replace('-', '')
        
        # Verificar formato básico
        if not rut or len(rut_clean) < 8:
            raise ValidationError('RUT inválido. Formato esperado: XX.XXX.XXX-X')
        
        # Validar que solo contenga números (excepto el último carácter que puede ser K)
        try:
            numeros = rut_clean[:-1]
            dv = rut_clean[-1].upper()
            int(numeros)
            
            if dv not in [str(i) for i in range(10)] and dv != 'K':
                raise ValidationError('RUT inválido. Dígito verificador no válido.')
        except ValueError:
            raise ValidationError('RUT inválido. Solo se aceptan números.')
        
        return rut
    
    def clean_email(self):
        """Valida que el email sea único entre proveedores"""
        from .models import Proveedor
        email = self.cleaned_data.get('email')
        
        # Si estamos editando, excluir el proveedor actual
        qs = Proveedor.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Este email ya está registrado para otro proveedor.')
        
        return email


# =====================================================================
# WEEK 2: FORMULARIOS PARA TERMINAL POS
# =====================================================================

class BuscarMedicamentoForm(forms.Form):
    """
    Formulario para búsqueda de medicamentos en terminal POS.
    Permite búsqueda por nombre, SKU o código de barras.
    """
    busqueda = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Buscar por nombre, SKU o código de barras...',
            'autofocus': True,
            'autocomplete': 'off'
        }),
        label='Búsqueda'
    )
    
    def clean_busqueda(self):
        """Limpia y normaliza el término de búsqueda"""
        busqueda = self.cleaned_data.get('busqueda', '').strip()
        return busqueda


class AgregarCarritoForm(forms.Form):
    """
    Formulario para agregar medicamentos al carrito en POS.
    """
    medicamento_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        label='ID Medicamento'
    )
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px',
            'value': 1
        }),
        label='Cantidad'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        medicamento_id = cleaned_data.get('medicamento_id')
        cantidad = cleaned_data.get('cantidad')
        
        if medicamento_id and cantidad:
            try:
                medicamento = Medicamento.objects.get(pk=medicamento_id)
                if medicamento.stock < cantidad:
                    raise ValidationError(
                        f'Stock insuficiente. Disponible: {medicamento.stock}'
                    )
            except Medicamento.DoesNotExist:
                raise ValidationError('Medicamento no encontrado.')
        
        return cleaned_data


class ProcesarPagoForm(forms.Form):
    """
    Formulario para procesar pagos en POS.
    Soporta múltiples métodos de pago.
    """
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Tarjeta Débito'),
        ('credito', 'Tarjeta Crédito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('otro', 'Otro Método'),
    ]
    
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Método de Pago'
    )
    
    monto_pagado = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '100',
            'placeholder': '0.00'
        }),
        label='Monto Pagado'
    )
    
    cliente_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
        label='Cliente (opcional)'
    )
    
    referencia_transaccion = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Referencia de transacción (opcional)'
        }),
        label='Referencia Transacción'
    )
    
    def clean_monto_pagado(self):
        """Valida que el monto pagado sea positivo"""
        monto = self.cleaned_data.get('monto_pagado')
        if monto and monto <= 0:
            raise ValidationError('El monto debe ser mayor a 0.')
        return monto


class SeleccionarClienteForm(forms.Form):
    """
    Formulario para seleccionar cliente en venta (opcional).
    """
    from .models import Cliente
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'cliente_select'
        }),
        label='Cliente (opcional)',
        empty_label='--- Sin cliente ---'
    )


# =====================================================================
# NUEVOS FORMULARIOS PARA POS v2 (FASE 1-2)
# =====================================================================

class ProcesarPagoV2Form(forms.Form):
    """
    Formulario mejorado para procesar pago en POS v2.
    Incluye validación de métodos de pago.
    """
    METODOS_PAGO = [
        ('EFECTIVO', '💵 Efectivo'),
        ('DEBITO', '🏧 Débito'),
        ('CREDITO', '💳 Crédito'),
        ('TRANSFERENCIA', '🏦 Transferencia'),
    ]
    
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label='Método de Pago'
    )
    
    monto_pagado = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '100',
            'placeholder': '0',
        }),
        label='Monto a Pagar ($)'
    )
    
    referencia_pago = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ref. transacción, últimos 4 dígitos, etc (opcional)',
        }),
        label='Referencia de Pago'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        metodo_pago = cleaned_data.get('metodo_pago')
        referencia = cleaned_data.get('referencia_pago')
        
        # Si es transferencia, débito o crédito, requiere referencia
        if metodo_pago in ['TRANSFERENCIA', 'DEBITO', 'CREDITO'] and not referencia:
            raise ValidationError(
                f'Debes ingresar referencia para pago con {metodo_pago}'
            )
        
        return cleaned_data


class AplicarDescuentoForm(forms.Form):
    """Formulario para aplicar descuentos al carrito"""
    TIPO_DESCUENTO = [
        ('PORCENTAJE', 'Porcentaje (%)'),
        ('MONTO', 'Monto fijo ($)'),
    ]
    
    tipo_descuento = forms.ChoiceField(
        choices=TIPO_DESCUENTO,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label='Tipo de Descuento'
    )
    
    valor = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.01',
        }),
        label='Valor del Descuento'
    )
    
    motivo = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Motivo del descuento (opcional)',
        }),
        label='Observaciones'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_descuento')
        valor = cleaned_data.get('valor')
        
        if valor and valor < 0:
            raise ValidationError('El descuento debe ser positivo')
        
        if tipo == 'PORCENTAJE' and valor and valor > 100:
            raise ValidationError('El porcentaje no puede ser mayor a 100%')
        
        return cleaned_data


class SeleccionarClienteV2Form(forms.Form):
    """
    Formulario mejorado para seleccionar cliente en POS v2.
    Permite búsqueda rápida por RUT o nombre.
    """
    from .models import Cliente
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-lg',
            'id': 'cliente_select_v2',
        }),
        label='Cliente (opcional)',
        empty_label='--- Venta anónima ---'
    )
    
    rut_busqueda = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por RUT...',
            'id': 'rut_busqueda',
        }),
        label='O buscar por RUT'
    )


class AnularVentaForm(forms.Form):
    """Formulario para anular una venta (crear nota de crédito)"""
    motivo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Motivo de anulación',
        }),
        label='Motivo'
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Detalles adicionales',
            'rows': 3,
        }),
        label='Observaciones'
    )
    
    contrasena_supervisor = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña del supervisor',
        }),
        label='Autorización (contraseña supervisor)'
    )


class ProcesarDevolucionForm(forms.Form):
    """Formulario para procesar devolución de medicamento"""
    MOTIVOS = [
        ('DEFECTO', 'Defecto del producto'),
        ('CAMBIO', 'Cambio de medicamento'),
        ('ALERGIA', 'Reacción alérgica'),
        ('VENCIDO', 'Medicamento vencido'),
        ('ERROR', 'Error de venta'),
        ('OTRO', 'Otro motivo'),
    ]
    
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
        }),
        label='Cantidad a devolver'
    )
    
    motivo = forms.ChoiceField(
        choices=MOTIVOS,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Motivo de devolución'
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Detalles adicionales',
        }),
        label='Observaciones'
    )




