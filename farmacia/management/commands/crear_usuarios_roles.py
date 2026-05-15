# farmacia/management/commands/crear_usuarios_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from farmacia.models import RolPermiso


class Command(BaseCommand):
    help = 'Crea usuarios de prueba con diferentes roles y permisos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('Creando usuarios con roles...'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        
        usuarios_creados = []
        usuarios_existentes = []
        
        # ============================================
        # ADMIN - Administrador / Dueño
        # ============================================
        try:
            admin, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'first_name': 'Administrador',
                    'last_name': 'Sistema',
                    'email': 'admin@farmacia.cl',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            admin.set_password('Admin2026!')
            admin.save()
            
            rol_admin, _ = RolPermiso.objects.get_or_create(
                user=admin,
                defaults={'rol': 'ADMIN', 'estado_activo': True}
            )
            
            if created:
                usuarios_creados.append(('admin', 'ADMIN', 'Admin2026!'))
                self.stdout.write(
                    self.style.SUCCESS('✅ ADMIN creado: admin / Admin2026!')
                )
            else:
                usuarios_existentes.append('admin')
                self.stdout.write(
                    self.style.WARNING('⚠️  ADMIN ya existe: admin')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crear ADMIN: {str(e)}'))
        
        # ============================================
        # VENDEDOR 1 - Vendedor
        # ============================================
        try:
            vendedor1, created = User.objects.get_or_create(
                username='vendedor1',
                defaults={
                    'first_name': 'Juan',
                    'last_name': 'Pérez',
                    'email': 'juan@farmacia.cl',
                    'is_staff': False,
                }
            )
            vendedor1.set_password('Vendedor123!')
            vendedor1.save()
            
            rol_v1, _ = RolPermiso.objects.get_or_create(
                user=vendedor1,
                defaults={'rol': 'VENDEDOR', 'estado_activo': True}
            )
            
            if created:
                usuarios_creados.append(('vendedor1', 'VENDEDOR', 'Vendedor123!'))
                self.stdout.write(
                    self.style.SUCCESS('✅ VENDEDOR 1 creado: vendedor1 / Vendedor123!')
                )
            else:
                usuarios_existentes.append('vendedor1')
                self.stdout.write(
                    self.style.WARNING('⚠️  VENDEDOR 1 ya existe: vendedor1')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crear VENDEDOR 1: {str(e)}'))
        
        # ============================================
        # VENDEDOR 2 - Vendedor
        # ============================================
        try:
            vendedor2, created = User.objects.get_or_create(
                username='vendedor2',
                defaults={
                    'first_name': 'María',
                    'last_name': 'González',
                    'email': 'maria@farmacia.cl',
                    'is_staff': False,
                }
            )
            vendedor2.set_password('Vendedor123!')
            vendedor2.save()
            
            rol_v2, _ = RolPermiso.objects.get_or_create(
                user=vendedor2,
                defaults={'rol': 'VENDEDOR', 'estado_activo': True}
            )
            
            if created:
                usuarios_creados.append(('vendedor2', 'VENDEDOR', 'Vendedor123!'))
                self.stdout.write(
                    self.style.SUCCESS('✅ VENDEDOR 2 creado: vendedor2 / Vendedor123!')
                )
            else:
                usuarios_existentes.append('vendedor2')
                self.stdout.write(
                    self.style.WARNING('⚠️  VENDEDOR 2 ya existe: vendedor2')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crear VENDEDOR 2: {str(e)}'))
        
        # ============================================
        # GERENTE - Gerente de Tienda
        # ============================================
        try:
            gerente, created = User.objects.get_or_create(
                username='gerente',
                defaults={
                    'first_name': 'Carlos',
                    'last_name': 'López',
                    'email': 'gerente@farmacia.cl',
                    'is_staff': True,
                }
            )
            gerente.set_password('Gerente123!')
            gerente.save()
            
            rol_gerente, _ = RolPermiso.objects.get_or_create(
                user=gerente,
                defaults={'rol': 'GERENTE', 'estado_activo': True}
            )
            
            if created:
                usuarios_creados.append(('gerente', 'GERENTE', 'Gerente123!'))
                self.stdout.write(
                    self.style.SUCCESS('✅ GERENTE creado: gerente / Gerente123!')
                )
            else:
                usuarios_existentes.append('gerente')
                self.stdout.write(
                    self.style.WARNING('⚠️  GERENTE ya existe: gerente')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crear GERENTE: {str(e)}'))
        
        # ============================================
        # CONTADOR - Contador
        # ============================================
        try:
            contador, created = User.objects.get_or_create(
                username='contador',
                defaults={
                    'first_name': 'Patricia',
                    'last_name': 'Rodríguez',
                    'email': 'contador@farmacia.cl',
                    'is_staff': True,
                }
            )
            contador.set_password('Contador123!')
            contador.save()
            
            rol_contador, _ = RolPermiso.objects.get_or_create(
                user=contador,
                defaults={'rol': 'CONTADOR', 'estado_activo': True}
            )
            
            if created:
                usuarios_creados.append(('contador', 'CONTADOR', 'Contador123!'))
                self.stdout.write(
                    self.style.SUCCESS('✅ CONTADOR creado: contador / Contador123!')
                )
            else:
                usuarios_existentes.append('contador')
                self.stdout.write(
                    self.style.WARNING('⚠️  CONTADOR ya existe: contador')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crear CONTADOR: {str(e)}'))
        
        # ============================================
        # RESUMEN
        # ============================================
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        
        if usuarios_creados:
            self.stdout.write(self.style.SUCCESS(f'\n✅ {len(usuarios_creados)} usuarios creados:'))
            for username, rol, password in usuarios_creados:
                self.stdout.write(
                    self.style.SUCCESS(f'   • {username} ({rol}) - {password}')
                )
        
        if usuarios_existentes:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {len(usuarios_existentes)} usuarios ya existen:'))
            for username in usuarios_existentes:
                self.stdout.write(
                    self.style.WARNING(f'   • {username}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando completado exitosamente!'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
