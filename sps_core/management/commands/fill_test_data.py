from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from sps_lines.models import Line, Node, Sensor
from sps_parts.models import (
    PartCategory, Part, PartInstallation,
    Warehouse, SparePartStock, PartOrder
)


class Command(BaseCommand):
    help = 'Наполняет базу тестовыми данными для SPS'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Начинаем наполнение базы тестовыми данными...')

        # Очищаем старые данные (опционально)
        self.stdout.write('🧹 Очистка старых данных...')
        PartOrder.objects.all().delete()
        SparePartStock.objects.all().delete()
        PartInstallation.objects.all().delete()
        Part.objects.all().delete()
        PartCategory.objects.all().delete()
        Sensor.objects.all().delete()
        Node.objects.all().delete()
        Line.objects.all().delete()
        Warehouse.objects.all().delete()

        # ==================== ЛИНИИ ====================
        self.stdout.write('🏭 Создаём производственные линии...')

        line1 = Line.objects.create(
            name='Линия розлива №1',
            inventory_number='L-2023-001',
            performance=1200,
            is_active=True,
            description='Основная линия розлива напитков'
        )

        line2 = Line.objects.create(
            name='Линия упаковки №2',
            inventory_number='L-2023-002',
            performance=800,
            is_active=True,
            description='Линия вторичной упаковки'
        )

        line3 = Line.objects.create(
            name='Линия этикетки №3',
            inventory_number='L-2023-003',
            performance=1000,
            is_active=True,
            description='Линия нанесения этикетки'
        )

        self.stdout.write(f'   ✅ Создано {Line.objects.count()} линий')

        # ==================== УЗЛЫ ====================
        self.stdout.write('🔧 Создаём узлы...')

        # Узлы для линии 1
        nodes_l1 = [
            ('Конвейер подачи', 'conveyor', 10, 50),
            ('Насосный агрегат', 'motor', 30, 50),
            ('Блок розлива', 'actuator', 50, 50),
            ('Контроллер PLC', 'controller', 70, 50),
            ('Конвейер отвода', 'conveyor', 90, 50),
        ]

        # Узлы для линии 2
        nodes_l2 = [
            ('Конвейер упаковки', 'conveyor', 15, 30),
            ('Термоусадочная печь', 'motor', 40, 30),
            ('Датчик контроля', 'sensor_block', 60, 30),
            ('Робот-упаковщик', 'actuator', 80, 30),
        ]

        # Узлы для линии 3
        nodes_l3 = [
            ('Подача бутылок', 'conveyor', 20, 70),
            ('Этикетировочный модуль', 'actuator', 50, 70),
            ('Сушильный туннель', 'motor', 75, 70),
            ('Контроль качества', 'sensor_block', 90, 70),
        ]

        created_nodes = []

        for name, node_type, pos_x, pos_y in nodes_l1:
            node = Node.objects.create(
                line=line1,
                name=name,
                node_type=node_type,
                is_active=True,
                position_x=pos_x,
                position_y=pos_y,
                service_interval_hours=500
            )
            created_nodes.append(node)

        for name, node_type, pos_x, pos_y in nodes_l2:
            node = Node.objects.create(
                line=line2,
                name=name,
                node_type=node_type,
                is_active=True,
                position_x=pos_x,
                position_y=pos_y,
                service_interval_hours=400
            )
            created_nodes.append(node)

            # Один узел сделаем неактивным для теста
            if name == 'Термоусадочная печь':
                node.is_active = False
                node.save()

        for name, node_type, pos_x, pos_y in nodes_l3:
            node = Node.objects.create(
                line=line3,
                name=name,
                node_type=node_type,
                is_active=True,
                position_x=pos_x,
                position_y=pos_y,
                service_interval_hours=450
            )
            created_nodes.append(node)

        self.stdout.write(f'   ✅ Создано {Node.objects.count()} узлов')

        # ==================== ДАТЧИКИ ====================
        self.stdout.write('📡 Создаём датчики...')

        sensor_types = [
            ('temperature', 'Температура', '°C', 20, 80),
            ('vibration', 'Вибрация', 'мм/с', 0, 10),
            ('current', 'Ток', 'А', 0, 50),
            ('pressure', 'Давление', 'бар', 1, 10),
            ('proximity', 'Приближение', '', 0, 1),
        ]

        for node in Node.objects.all():
            # Каждый узел получает 2-3 датчика
            for i, (stype, sname, unit, min_val, max_val) in enumerate(sensor_types[:3]):
                # Один датчик сделаем с проблемой (выход за пределы)
                if node.name == 'Насосный агрегат' and stype == 'vibration':
                    current = 12.5  # Выше нормы (max 10)
                elif node.name == 'Термоусадочная печь' and stype == 'temperature':
                    current = 95.0  # Выше нормы (max 80)
                else:
                    current = (min_val + max_val) / 2  # Среднее значение

                Sensor.objects.create(
                    node=node,
                    name=f'{sname} {node.name}',
                    sensor_type=stype,
                    code=f'{node.line.inventory_number}_{node.id}_{i}',
                    unit_of_measurement=unit,
                    min_value=min_val,
                    max_value=max_val,
                    current_value=current,
                    is_active=True
                )

        self.stdout.write(f'   ✅ Создано {Sensor.objects.count()} датчиков')

        # ==================== КАТЕГОРИИ ЗАПЧАСТЕЙ ====================
        self.stdout.write('📦 Создаём категории запчастей...')

        categories = [
            ('Подшипники', 'BRG'),
            ('Ремни', 'BLT'),
            ('Фильтры', 'FLT'),
            ('Датчики', 'SNS'),
            ('Уплотнения', 'SEL'),
        ]

        for name, code in categories:
            PartCategory.objects.create(name=name, code=code)

        self.stdout.write(f'   ✅ Создано {PartCategory.objects.count()} категорий')

        # ==================== ЗАПЧАСТИ ====================
        self.stdout.write('🔩 Создаём запчасти...')

        parts_data = [
            ('Подшипник SKF 6205', 'BRG-001', 'Подшипники', 10000, ['Насосный агрегат']),
            ('Подшипник SKF 6305', 'BRG-002', 'Подшипники', 8000, ['Конвейер подачи']),
            ('Ремень зубчатый HTD 500', 'BLT-001', 'Ремни', 5000, ['Конвейер отвода']),
            ('Фильтр масляный', 'FLT-001', 'Фильтры', 2000, ['Насосный агрегат']),
            ('Датчик температуры PT100', 'SNS-001', 'Датчики', 50000, ['Термоусадочная печь']),
            ('Уплотнение Viton 50мм', 'SEL-001', 'Уплотнения', 3000, ['Блок розлива']),
        ]

        created_parts = []

        for name, article, cat_name, lifetime, compat_nodes in parts_data:
            category = PartCategory.objects.get(name=cat_name)
            part = Part.objects.create(
                name=name,
                article=article,
                category=category,
                expected_lifetime_hours=lifetime,
                manufacturer='SKF' if 'Подшипник' in name else 'Generic'
            )

            # Привязываем к совместимым узлам
            for node_name in compat_nodes:
                try:
                    node = Node.objects.get(name=node_name)
                    part.compatible_nodes.add(node)
                except Node.DoesNotExist:
                    pass

            created_parts.append(part)

        self.stdout.write(f'   ✅ Создано {Part.objects.count()} запчастей')

        # ==================== СКЛАД ====================
        self.stdout.write('🏪 Создаём склад...')

        warehouse = Warehouse.objects.create(
            name='Основной склад',
            code='WH-001',
            location='Цех №1, сектор А',
            is_active=True
        )

        self.stdout.write(f'   ✅ Создано {Warehouse.objects.count()} складов')

        # ==================== ОСТАТКИ НА СКЛАДЕ ====================
        self.stdout.write('📊 Создаём остатки на складе...')

        stock_data = [
            ('BRG-001', 5, 2),  # Норма
            ('BRG-002', 1, 2),  # Низкий остаток (алерт!)
            ('BLT-001', 3, 2),  # Норма
            ('FLT-001', 0, 3),  # Нет в наличии (алерт!)
            ('SNS-001', 10, 2),  # Много
            ('SEL-001', 2, 2),  # На минимуме
        ]

        for article, qty, min_level in stock_data:
            try:
                part = Part.objects.get(article=article)
                SparePartStock.objects.create(
                    part=part,
                    warehouse=warehouse,
                    quantity=qty,
                    min_stock_level=min_level,
                    location=f'A-{Part.objects.get(article=article).id:03d}'
                )
            except Part.DoesNotExist:
                pass

        self.stdout.write(f'   ✅ Создано {SparePartStock.objects.count()} остатков')

        # ==================== УСТАНОВКИ ЗАПЧАСТЕЙ ====================
        self.stdout.write('🔧 Создаём истории установок запчастей...')

        installation_data = [
            ('BRG-001', 'Насосный агрегат', 8500, True),  # 85% ресурса (скоро замена!)
            ('BRG-002', 'Конвейер подачи', 2000, True),  # 25% ресурса (норма)
            ('BLT-001', 'Конвейер отвода', 4800, True),  # 96% ресурса (критично!)
            ('FLT-001', 'Насосный агрегат', 1800, True),  # 90% ресурса (внимание)
            ('SNS-001', 'Термоусадочная печь', 10000, True),  # 20% ресурса (норма)
            ('SEL-001', 'Блок розлива', 3200, False),  # Демонтирована
        ]

        for article, node_name, hours, is_installed in installation_data:
            try:
                part = Part.objects.get(article=article)
                node = Node.objects.get(name=node_name)

                installation = PartInstallation.objects.create(
                    part=part,
                    node=node,
                    serial_number=f'SN-{part.id}-{node.id}',
                    installation_hours=0,
                    current_hours=hours,
                    installed_by='Иванов И.И.',
                    notes='Плановая замена'
                )

                if not is_installed:
                    installation.removed_at = timezone.now() - timedelta(days=30)
                    installation.save()

            except (Part.DoesNotExist, Node.DoesNotExist):
                pass

        self.stdout.write(f'   ✅ Создано {PartInstallation.objects.count()} установок')

        # ==================== ЗАКАЗЫ В ПУТИ ====================
        self.stdout.write('🚚 Создаём заказы в пути...')

        orders_data = [
            ('BRG-002', 5, 'shipped', 5),  # В пути, 5 дней
            ('FLT-001', 10, 'in_transit', 3),  # В пути, 3 дня
            ('SEL-001', 5, 'ordered', 14),  # Заказан, 14 дней
        ]

        for article, qty, status, days in orders_data:
            try:
                part = Part.objects.get(article=article)
                PartOrder.objects.create(
                    part=part,
                    quantity=qty,
                    supplier='ООО "ПромСнаб"',
                    order_number=f'PO-2024-{PartOrder.objects.count() + 1:04d}',
                    expected_delivery_date=timezone.now().date() + timedelta(days=days),
                    status=status,
                    price=1500.00,
                    currency='RUB',
                    tracking_number=f'TRK-{PartOrder.objects.count() + 1:06d}'
                )
            except Part.DoesNotExist:
                pass

        self.stdout.write(f'   ✅ Создано {PartOrder.objects.count()} заказов')

        # ==================== ИТОГИ ====================
        self.stdout.write(self.style.SUCCESS('\n✅ Наполнение завершено!'))
        self.stdout.write(self.style.SUCCESS('\n📊 Итоги:'))
        self.stdout.write(f'   🏭 Линий: {Line.objects.count()}')
        self.stdout.write(f'   🔧 Узлов: {Node.objects.count()}')
        self.stdout.write(f'   📡 Датчиков: {Sensor.objects.count()}')
        self.stdout.write(f'   🔩 Запчастей: {Part.objects.count()}')
        self.stdout.write(f'   🔧 Установок: {PartInstallation.objects.count()}')
        self.stdout.write(f'   📦 Остатков: {SparePartStock.objects.count()}')
        self.stdout.write(f'   🚚 Заказов: {PartOrder.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n🌐 Откройте http://localhost:8080/ для просмотра дашборда!'))