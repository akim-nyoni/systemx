"""
Management command: python manage.py seed_rhapsodys
Seeds the database with Rhapsody's checklist data, roles, and users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role
from forms_builder.models import FormTemplate, FormSection, ChecklistItem

User = get_user_model()

# (name, code, parent_code_or_None, order)
DEPARTMENTS = [
    ('Director',        'director',        None,             1),
    ('General Manager', 'general_manager', None,             2),
    ('Front of House',  'front_of_house',  None,             3),
    ('Bar',             'bar',             'front_of_house', 4),
    ('Waiters',         'waiters',         'front_of_house', 5),
    ('Floor Manager',   'floor_manager',   'front_of_house', 6),
    ('Bar Manager',     'bar_manager',     'front_of_house', 7),
    ('Back of House',   'back_of_house',   None,             8),
    ('Kitchen Manager', 'kitchen_manager', 'back_of_house',  9),
    ('Stock Controller','stock_controller','back_of_house',  10),
    ('Head Chef',       'head_chef',       'back_of_house',  11),
    ('Coordinator',     'coordinator',     'back_of_house',  12),
    ('Red Section',     'red_section',     'back_of_house',  13),
    ('Yellow Section',  'yellow_section',  'back_of_house',  14),
    ('Green Section',   'green_section',   'back_of_house',  15),
    ('Blue Section',    'blue_section',    'back_of_house',  16),
    ('White Section',   'white_section',   'back_of_house',  17),
    ('Prep Section',    'prep_section',    'back_of_house',  18),
    ('Sushi Bar',       'sushi_bar',       'back_of_house',  19),
    ('Maintenance',     'maintenance',     None,             20),
    ('Cleaning',        'cleaning',        None,             21),
    ('Scullery / Porter','scullery',       'cleaning',       22),
    ('General Cleaner', 'general_cleaner', 'cleaning',       23),
    ('Marketing',       'marketing',       None,             24),
    ('Finance',         'finance',         None,             25),
]

CHECKLISTS = [
    {
        'name': "Management Opening Checklist",
        'category': 'opening',
        'description': 'Daily opening duties for the duty manager.',
        'sections': [
            {'title': 'Opening Duties', 'items': [
                ('Inspect outside the store right round', 'yes_no'),
                ('Unlock doors and check for break ins', 'yes_no'),
                ('Disable alarm', 'yes_no'),
                ('Switch on lights', 'yes_no'),
                ('Switch on TVs', 'yes_no'),
                ('Switch on music', 'yes_no'),
                ('Switch on air conditioning, fans & heaters', 'yes_no'),
                ('Check electricity amount', 'yes_no'),
                ('Check diary', 'yes_no'),
                ('Check all rostered staff if present & on time', 'yes_no'),
                ('Print stock count sheet and toilet check sheet', 'yes_no'),
                ('Do ordering', 'yes_no'),
            ]},
            {'title': 'Front Of House – Day', 'items': [
                ('Check toilets and check sheets', 'yes_no'),
                ('Allocate duties to staff members', 'yes_no'),
                ('Check out of stock and low stock', 'yes_no'),
                ('Enquire on must sell and daily promos', 'yes_no'),
                ('Check and allocate bookings', 'yes_no'),
                ('Allocate sections', 'yes_no'),
                ('Vibe meeting', 'yes_no'),
                ('Prepare breakfast set-up and issuing FOH', 'yes_no'),
                ('Conduct bar issuing', 'yes_no'),
                ('Conduct kitchen issuing', 'yes_no'),
                ('Check Front of House', 'yes_no'),
                ('Conduct bar meeting', 'yes_no'),
                ('Check Bar', 'yes_no'),
                ('Conduct green area meeting', 'yes_no'),
                ('Check Kitchen', 'yes_no'),
                ('Check staff toilet', 'yes_no'),
                ('Check ice and ice machine', 'yes_no'),
                ('Ensure store set-up and cleaning is complete', 'yes_no'),
            ]},
            {'title': 'Administration', 'items': [
                ('Office and front of house diary are checked for notes', 'yes_no'),
                ('Check all closing procedures were followed previous night', 'yes_no'),
                ('Daily orders are placed – bread / milk / cream', 'yes_no'),
                ('Do register and check everyone is present and on time', 'yes_no'),
                ('Issue sheets are filled out by management', 'yes_no'),
                ('Issues are done by 10h45', 'yes_no'),
                ('Daily recon completed', 'yes_no'),
                ("Previous night's dustbins are emptied and washed", 'yes_no'),
                ('All deliveries that are expected have arrived', 'yes_no'),
                ('Change room has been cleaned according to roster', 'yes_no'),
                ('Veg and juice order placed', 'yes_no'),
                ('Weekly glass order placed', 'yes_no'),
                ('Weekly top up kitchen order checked and placed', 'yes_no'),
                ('Extraction plates are taken out and cleaned', 'yes_no'),
            ]},
        ]
    },
    {
        'name': "Management Closing Checklist",
        'category': 'closing',
        'description': 'End-of-day closing procedures for the duty manager.',
        'sections': [
            {'title': 'Front Of House – Night', 'items': [
                ('Allocate duties to staff members', 'yes_no'),
                ('Check out of stock and low stock', 'yes_no'),
                ('Enquire on must sell and daily promos', 'yes_no'),
                ('Check and allocate bookings', 'yes_no'),
                ('Allocate sections', 'yes_no'),
                ('Vibe meeting', 'yes_no'),
                ('Prepare dinner set-up and issuing FOH', 'yes_no'),
                ('Conduct bar issuing', 'yes_no'),
                ('Conduct kitchen issuing', 'yes_no'),
                ('Check Front of House', 'yes_no'),
                ('Check Toilets', 'yes_no'),
                ('Conduct bar meeting', 'yes_no'),
                ('Check Bar', 'yes_no'),
                ('Conduct green meeting', 'yes_no'),
                ('Check Kitchen', 'yes_no'),
                ('Check staff toilet', 'yes_no'),
                ('Check ice and ice machine', 'yes_no'),
                ('Ensure store set-up and cleaning is complete', 'yes_no'),
            ]},
            {'title': 'Closing Procedure', 'items': [
                ('Equipment is switched off in stages', 'yes_no'),
                ('All equipment is moved away from walls and cleaned', 'yes_no'),
                ('Each section has counted their portions', 'yes_no'),
                ('Defrost for the next day must be taken out', 'yes_no'),
                ('Out of stock list has been communicated to management', 'yes_no'),
                ('Kitchen decks to be scrubbed', 'yes_no'),
                ('Sauces have been sealed in plastic wrap – with a hole', 'yes_no'),
                ('Sauces have been packed in the fridge – not on the floor', 'yes_no'),
                ('Mops have been washed and soaked', 'yes_no'),
                ('Veg and juice order has been done', 'yes_no'),
                ('WALK IN FRIDGE must BE clean and tidy', 'yes_no'),
                ('Grill is soaked overnight in correct cleaning agent', 'yes_no'),
                ('All electrical equipment is off', 'yes_no'),
                ('Scullery section is clean and tidy', 'yes_no'),
                ('Dishwashers are cleaned', 'yes_no'),
                ('All storerooms and back gates are locked', 'yes_no'),
                ('Clear bins', 'yes_no'),
                ('Do cash up', 'yes_no'),
                ('Write in diary', 'yes_no'),
                ('Lock BOH doors', 'yes_no'),
                ('Switch off all equipment', 'yes_no'),
                ('Switch off gas', 'yes_no'),
                ('Switch heaters off from the back', 'yes_no'),
                ('Check if everything is packed and clean', 'yes_no'),
                ('Check if all staff is out of the BOH', 'yes_no'),
                ('Switch off music', 'yes_no'),
                ('Switch off lights', 'yes_no'),
                ('Switch off TVs', 'yes_no'),
                ('Check the toilets', 'yes_no'),
                ('Ensure everyone is outside', 'yes_no'),
                ('Switch on alarms', 'yes_no'),
                ('Lock front entrances', 'yes_no'),
                ('Drive around store ensuring everything off & locked, vigilance of suspicious characters', 'yes_no'),
            ]},
        ]
    },
    {
        'name': "Cleaning & Maintenance Checklist",
        'category': 'cleaning',
        'description': 'Monthly deep cleaning checklist for all areas.',
        'sections': [
            {'title': 'Store Front – Outside Area', 'items': [
                ('Parking bays in front & around entrance', 'yes_no'),
                ('Outside walls', 'yes_no'),
                ('Branding outside', 'yes_no'),
                ('Plants watered and in good health', 'yes_no'),
                ('Mist machine clean and operational', 'yes_no'),
                ('Check & remove bird nests & droppings', 'yes_no'),
                ('Canvas clean and in good condition', 'yes_no'),
            ]},
            {'title': 'Smoking Area', 'items': [
                ("Clean TVs and make sure it's on & playing", 'yes_no'),
                ('Wipe all power points', 'yes_no'),
                ('Scrub floors', 'yes_no'),
                ('Scrub under flowerpots', 'yes_no'),
                ('Scrub under benches', 'yes_no'),
                ('Wipe all chair and table footings', 'yes_no'),
                ('Aluminum doors and frames', 'yes_no'),
                ('Wipe all silver steel pillars', 'yes_no'),
                ('Wipe lights and hanging light holders', 'yes_no'),
                ('Flowerpots', 'yes_no'),
                ('Change cushion covers', 'yes_no'),
                ('Wipe and dust all speakers', 'yes_no'),
                ('Clean hanging flowers and pots', 'yes_no'),
                ('Clean windows and rails', 'yes_no'),
                ('Wipe signage and banding', 'yes_no'),
                ('Clean walls', 'yes_no'),
                ('Check for spider webs', 'yes_no'),
                ('Clean fire extinguishers', 'yes_no'),
                ('Fix table alignment', 'yes_no'),
                ('Remove dead leaves from flower bed', 'yes_no'),
                ('Remove gum under chairs and tables', 'yes_no'),
                ('Table set-up done accordingly', 'yes_no'),
                ('Clean Heaters and check gas availability', 'yes_no'),
                ('Clean Fans', 'yes_no'),
            ]},
            {'title': 'Non-Smoking Area', 'items': [
                ('Curbs and footings', 'yes_no'),
                ('Plug points', 'yes_no'),
                ('Golden foot rails outside bar and sushi', 'yes_no'),
                ('Wipe all plants', 'yes_no'),
                ('TVs clean and working', 'yes_no'),
                ('Clean and fill salt and pepper', 'yes_no'),
                ('Clean and fill condiments', 'yes_no'),
                ('Clean and dust speakers and subwoofers', 'yes_no'),
                ('Clean and dust lights', 'yes_no'),
                ("Clean and scrub under waiter's stations", 'yes_no'),
                ('Remove bubblegum under chairs & tables', 'yes_no'),
                ('Clean and dust air-vents', 'yes_no'),
                ("Clean kiddies' chairs", 'yes_no'),
                ('2-3 printer rolls per waiter station', 'yes_no'),
                ('Scrub and mop floors', 'yes_no'),
                ('Wipe wall papers', 'yes_no'),
                ('Clean aluminum doors and windows', 'yes_no'),
                ('Clean and polish ice buckets', 'yes_no'),
                ('Check & remove spider webs', 'yes_no'),
                ('Polish all wood and leather', 'yes_no'),
                ('Fix table alignment', 'yes_no'),
                ('Wipe smoke sensors', 'yes_no'),
            ]},
            {'title': 'Waiter Stations', 'items': [
                ('Clean under and around POS', 'yes_no'),
                ('Clean Waiter stations', 'yes_no'),
                ('Clean bill folders', 'yes_no'),
                ('Clean Menus', 'yes_no'),
                ('Cutlery clean and polished', 'yes_no'),
                ('Outside lamps clean and filled', 'yes_no'),
                ('Linen clean and available', 'yes_no'),
                ('Sanitizer station', 'yes_no'),
                ('Fill toothpicks', 'yes_no'),
                ('Fill serviettes', 'yes_no'),
                ('Fill wet wipes', 'yes_no'),
            ]},
            {'title': 'Private Room / Upstairs', 'items': [
                ('Clean all table footings in the private room', 'yes_no'),
                ('Scrubbing and mopping floor', 'yes_no'),
                ('Clean all aluminum and windows', 'yes_no'),
                ('Check gum under tables and chairs', 'yes_no'),
                ('Clean and dust the shelves', 'yes_no'),
                ('Clean all chair footings', 'yes_no'),
                ('Clean ceiling of any stains', 'yes_no'),
                ('Clean and check décor lights', 'yes_no'),
                ('Clean wine cellar tops', 'yes_no'),
                ('Clean wines and decor', 'yes_no'),
                ('Clean display units', 'yes_no'),
            ]},
        ]
    },
    {
        'name': "Bar Daily Checklist",
        'category': 'bar',
        'description': 'Bar setup, equipment checks and glassware counts.',
        'sections': [
            {'title': 'Bar Setup & Equipment', 'items': [
                ('Check milk quantity and dates', 'yes_no'),
                ('Fill coffee beans', 'yes_no'),
                ('Fill salt & sugar', 'yes_no'),
                ('Check honey', 'yes_no'),
                ('Check coaster amount and condition', 'yes_no'),
                ('Check straws amount and condition', 'yes_no'),
                ('Check garnish quantity and freshness', 'yes_no'),
                ('Check speed pourer amount and condition', 'yes_no'),
                ('Check swizzle stick amount and condition', 'yes_no'),
                ('Check coffee & tea quantity and condition', 'yes_no'),
                ('Check muddle stick', 'yes_no'),
                ('Check strainer', 'yes_no'),
                ('Bottle cocks', 'yes_no'),
                ('Clean rimmer', 'yes_no'),
                ('Check shakers', 'yes_no'),
                ('Check spoon and knife', 'yes_no'),
                ('Check tot measurer', 'yes_no'),
                ('Check signage and branding', 'yes_no'),
                ('Check cutting board', 'yes_no'),
                ('Check sanitizer station', 'yes_no'),
            ]},
            {'title': 'Bar Cleaning', 'items': [
                ('Clean the bar fridge (in, out & under)', 'yes_no'),
                ('Clean draught machine', 'yes_no'),
                ('Clean bar counters', 'yes_no'),
                ('Clean coffee grinder', 'yes_no'),
                ('Clean coffee machine', 'yes_no'),
                ('Clean coffee disposal container', 'yes_no'),
                ('Check coffee temper', 'yes_no'),
                ('Clean POS', 'yes_no'),
                ('Check Till rolls – 2 minimum', 'yes_no'),
                ('Clean sink', 'yes_no'),
                ('Clean shelves', 'yes_no'),
                ('Polish glasses', 'yes_no'),
                ('Clean blender', 'yes_no'),
                ('Clean ice crusher', 'yes_no'),
                ('Remove broken and cracked equipment', 'yes_no'),
                ('Check bins if washed', 'yes_no'),
                ('Fill up sanitizer', 'yes_no'),
                ('Fill up soap', 'yes_no'),
                ('Fill toothpick', 'yes_no'),
            ]},
        ]
    },
    {
        'name': "Kitchen Daily Checklist",
        'category': 'kitchen',
        'description': 'Kitchen coordinator checks – hygiene, stock and preps.',
        'sections': [
            {'title': 'Kitchen Coordinator Checks', 'items': [
                ('Check dates and stock rotation', 'yes_no'),
                ('Cross contamination check', 'yes_no'),
                ('Inspect each section cleaning procedure', 'yes_no'),
                ('Out of stock check', 'yes_no'),
                ('Fridge temperature', 'yes_no'),
                ('Check for stock items that need to be prepped', 'yes_no'),
                ('All preps have been done', 'yes_no'),
                ('Cold-room temperature', 'yes_no'),
                ('All issues have been completed', 'yes_no'),
                ('Defrost all prep', 'yes_no'),
                ('Ensure personal hygiene checklist completed for staff', 'yes_no'),
                ('Ensure chest freezer is clean', 'yes_no'),
                ('Check all closing procedures were followed previous night', 'yes_no'),
                ('Check no fridges or freezers went off during the night', 'yes_no'),
                ('Do register and check everyone is present and on time', 'yes_no'),
                ('Ensure dry storeroom has had proper cleaning procedure', 'yes_no'),
                ('Cleaning procedure for all fridges have been followed', 'yes_no'),
                ('Ensure bain-marie was cleaned correctly', 'yes_no'),
                ('All out of stock reported and OOS board is updated', 'yes_no'),
                ('Monitoring of all staff hygiene procedures', 'yes_no'),
                ('All sanitising and cleaning equipment is in place', 'yes_no'),
                ('Hot pass was cleaned correctly', 'yes_no'),
                ('Monitor food orders to ensure expected quality', 'yes_no'),
                ('Monitor tickets for efficient timing', 'yes_no'),
                ('Check date and stock rotation of all products', 'yes_no'),
                ('All precooked items are covered, sealed & dated correctly', 'yes_no'),
                ('Following day preps to be taken out to defrost by 16h00', 'yes_no'),
                ('Ensure no cross contamination is occurring', 'yes_no'),
                ('Vegetable order done', 'yes_no'),
                ('All sections to have sanitizer station', 'yes_no'),
            ]},
            {'title': 'Grill Section', 'items': [
                ('Ensure grill was cleaned correctly', 'yes_no'),
                ('All preps have been completed', 'yes_no'),
                ('Oil in deep fryer has been filtered and changed regularly', 'yes_no'),
                ('Staff are following sanitizing and hygiene standards', 'yes_no'),
                ('Check date and stock rotation of meat', 'yes_no'),
                ('No cross contamination is occurring', 'yes_no'),
            ]},
            {'title': 'Sushi Bar', 'items': [
                ('Clean and scrub floor', 'yes_no'),
                ('Check all sushi equipment and tools are clean and covered', 'yes_no'),
                ('Clean gold glass rail on sushi bar', 'yes_no'),
                ('Ensure correct defrosting methods are in place', 'yes_no'),
                ('All preps have been completed', 'yes_no'),
                ('Ensure knifes are sanitary', 'yes_no'),
                ('Staff are following sanitizing and hygiene standards', 'yes_no'),
                ('Ensure no cross contamination is occurring', 'yes_no'),
                ('Check sushi rice', 'yes_no'),
                ('Ensure hand washing and sanitizer stations are full', 'yes_no'),
            ]},
        ]
    },
    {
        'name': "30-Minute Schedule Check",
        'category': 'foh',
        'description': 'Regular 30-minute interval checks throughout the shift.',
        'sections': [
            {'title': '30-Minute Checks', 'items': [
                ('Fridge temperature checked', 'yes_no'),
                ('Toilets checked and clean', 'yes_no'),
                ('All staff members have washed hands', 'yes_no'),
            ]},
        ]
    },
]


class Command(BaseCommand):
    help = "Seed Rhapsody's with roles, users, and checklist data."

    def add_arguments(self, parser):
        parser.add_argument('--no-user', action='store_true', help='Skip creating default users')
        parser.add_argument('--clear', action='store_true', help='Clear existing templates before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing templates...')
            FormTemplate.objects.all().delete()

        outlet_map = self._create_outlets()
        self._create_departments(outlet_map)
        roles = self._create_roles()

        if not options['no_user']:
            self._create_users(roles)

        self._seed_forms()

        self.stdout.write(self.style.SUCCESS('\n Rhapsody's seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('   Admin:      admin   / admin123'))
        self.stdout.write(self.style.SUCCESS('   Manager:    akim    / manager123'))
        self.stdout.write(self.style.SUCCESS('   Supervisor: super1  / super123'))
        self.stdout.write(self.style.SUCCESS('   Staff:      staff1  / staff123'))
        self.stdout.write(self.style.SUCCESS('   Viewer:     viewer1 / viewer123'))

        # Seed stock data
        try:
            seed_stock()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Stock seed skipped: {e}'))

    def _create_outlets(self):
        from accounts.models import Outlet
        self.stdout.write('\nCreating outlets...')
        outlets_data = [
            ("Rhapsody's Sibili",       'sibili',       1),
            ("Rhapsody's Phakalane",    'phakalane',    2),
            ("Rhapsody's Seventy Nine", 'seventy_nine', 3),
        ]
        outlet_map = {}
        for name, code, order in outlets_data:
            outlet, created = Outlet.objects.update_or_create(
                code=code, defaults={'name': name, 'order': order, 'is_active': True}
            )
            outlet_map[code] = outlet
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'   {action}: {name}')
        return outlet_map

    def _create_departments(self, outlet_map=None):
        from accounts.models import Department, Outlet
        self.stdout.write('\nCreating departments...')
        # Create departments for each outlet
        outlets = list(Outlet.objects.all()) if not outlet_map else list(outlet_map.values())
        if not outlets:
            outlets = [None]  # fallback if no outlets

        all_dept_maps = {}
        for outlet in outlets:
            dept_map = {}
            for name, code, parent_code, order in DEPARTMENTS:
                if outlet:
                    dept, created = Department.objects.update_or_create(
                        outlet=outlet, name=name,
                        defaults={'code': code, 'order': order, 'is_active': True}
                    )
                else:
                    dept, created = Department.objects.update_or_create(
                        name=name, defaults={'code': code, 'order': order, 'is_active': True}
                    )
                dept_map[code] = dept
                if created:
                    self.stdout.write(f'   Created: {name} ({outlet.name if outlet else "global"})')
            # Link parents within this outlet
            for name, code, parent_code, order in DEPARTMENTS:
                if parent_code and parent_code in dept_map:
                    dept = dept_map[code]
                    dept.parent = dept_map[parent_code]
                    dept.save(update_fields=['parent'])
            if outlet:
                all_dept_maps[outlet.code] = dept_map
        return all_dept_maps

    def _create_roles(self):
        self.stdout.write('\nCreating roles...')
        roles = {}

        role_defs = [
            {
                'name': 'Administrator',
                'description': 'Full system access. Can manage users, roles, forms, and all data.',
                'can_fill_forms': True, 'can_view_reports': True, 'can_view_all_reports': True,
                'can_manage_forms': True, 'can_manage_users': True, 'can_delete_submissions': True,
                'can_access_stock': True, 'can_manage_stock': True, 'is_system_admin': True,
            },
            {
                'name': 'Manager',
                'description': 'Can fill forms, view own and all team reports.',
                'can_fill_forms': True, 'can_view_reports': True, 'can_view_all_reports': True,
                'can_manage_forms': False, 'can_manage_users': False, 'can_delete_submissions': False,
                'is_system_admin': False,
            },
            {
                'name': 'Supervisor',
                'description': 'Can fill forms and view own reports only.',
                'can_fill_forms': True, 'can_view_reports': True, 'can_view_all_reports': False,
                'can_manage_forms': False, 'can_manage_users': False, 'can_delete_submissions': False,
                'is_system_admin': False,
            },
            {
                'name': 'Staff',
                'description': 'Can fill assigned forms. No report access.',
                'can_fill_forms': True, 'can_view_reports': False, 'can_view_all_reports': False,
                'can_manage_forms': False, 'can_manage_users': False, 'can_delete_submissions': False,
                'is_system_admin': False,
            },
            {
                'name': 'Viewer',
                'description': 'Read-only. Can view all reports but cannot fill forms.',
                'can_fill_forms': False, 'can_view_reports': True, 'can_view_all_reports': True,
                'can_manage_forms': False, 'can_manage_users': False, 'can_delete_submissions': False,
                'is_system_admin': False,
            },
        ]

        for rd in role_defs:
            role, created = Role.objects.update_or_create(
                name=rd['name'],
                defaults={k: v for k, v in rd.items() if k != 'name'}
            )
            roles[rd['name']] = role
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'   {action}: {role.name}')

        return roles

    def _create_users(self, roles):
        self.stdout.write('\nCreating users...')
        users = [
            ('admin',   'System', 'Administrator', 'admin@rhapsodys.co.bw',   'admin123',    'Administrator', True),
            ('akim',    'Akim',   '',               'akim@rhapsodys.co.bw',    'manager123',  'Manager',       False),
            ('super1',  'Sarah',  'Molefe',         'sarah@rhapsodys.co.bw',   'super123',    'Supervisor',    False),
            ('staff1',  'John',   'Doe',            'john@rhapsodys.co.bw',    'staff123',    'Staff',         False),
            ('viewer1', 'Report', 'Viewer',         'viewer@rhapsodys.co.bw',  'viewer123',   'Viewer',        False),
        ]
        for username, first, last, email, password, role_name, is_super in users:
            if not __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.filter(username=username).exists():
                from accounts.models import User as U
                u = U.objects.create_user(
                    username=username, email=email, password=password,
                    first_name=first, last_name=last,
                    custom_role=roles.get(role_name),
                    is_superuser=is_super, is_staff=is_super,
                )
                self.stdout.write(f'   Created: {username} ({role_name})')

    def _seed_forms(self):
        self.stdout.write('\nSeeding checklists...')
        for checklist_data in CHECKLISTS:
            tmpl, created = FormTemplate.objects.get_or_create(
                name=checklist_data['name'],
                defaults={
                    'category': checklist_data['category'],
                    'description': checklist_data['description'],
                    'is_active': True, 'all_managers_access': True,
                }
            )
            if not created:
                self.stdout.write(f'  ↳ Skipping "{tmpl.name}" (already exists)')
                continue
            self.stdout.write(f'   Created: {tmpl.name}')
            for s_idx, section_data in enumerate(checklist_data['sections']):
                section = FormSection.objects.create(form=tmpl, title=section_data['title'], order=s_idx)
                for i_idx, (label, resp_type) in enumerate(section_data['items']):
                    ChecklistItem.objects.create(
                        section=section, label=label, response_type=resp_type,
                        requires_comment_on_no=True, requires_image_on_no=True,
                        order=i_idx, is_active=True,
                    )


def seed_stock():
    """Seed stock categories and locations."""
    from stock.models import StockCategory, StockLocation
    from accounts.models import Department

    print('\nSeeding stock categories...')
    categories = [
        ('Beer',        'beer'),
        ('Spirits',     'spirits'),
        ('Wine',        'wine'),
        ('Soft Drinks', 'soft_drink'),
        ('Juice',       'juice'),
        ('Dairy',       'dairy'),
        ('Meat',        'meat'),
        ('Seafood',     'seafood'),
        ('Produce',     'produce'),
        ('Dry Goods',   'dry_goods'),
        ('Sauces',      'sauces'),
        ('Cleaning',    'cleaning'),
        ('Packaging',   'packaging'),
        ('Other',       'other'),
    ]
    for name, code in categories:
        obj, created = StockCategory.objects.get_or_create(code=code, defaults={'name': name})
        print(f"  {' Created' if created else '↳ Exists'}: {name}")

    print('\nSeeding stock locations per outlet...')
    from accounts.models import Outlet
    outlets = Outlet.objects.all()
    location_defs = [
        ('Main Bar',           'bar'),
        ('Cellar / Wine Room', 'bar'),
        ('Kitchen — Hot',      'back_of_house'),
        ('Kitchen — Cold',     'back_of_house'),
        ('Sushi Bar',          'sushi_bar'),
        ('Dry Store',          'back_of_house'),
        ('Walk-in Fridge',     'back_of_house'),
        ('Cleaning Store',     'cleaning'),
        ('General Store',      None),
    ]
    for outlet in outlets:
        for loc_name, dept_code in location_defs:
            dept = None
            if dept_code:
                try:
                    dept = Department.objects.get(code=dept_code, outlet=outlet)
                except Department.DoesNotExist:
                    pass
            obj, created = StockLocation.objects.get_or_create(
                name=loc_name, outlet=outlet,
                defaults={'department': dept, 'is_active': True}
            )
            if created:
                print(f"   Created: {loc_name} ({outlet.short_name})")


# Run stock seeding when called directly
if __name__ == '__main__':
    seed_stock()
