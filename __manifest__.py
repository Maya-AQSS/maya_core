{
    'name': "Maya | Core",
    'version': '19.0.1.0',

    'summary': "Módulo (Core) para la gestión interna del CEED",

    'description': """
        Módulo central de Odoo del sistema Maya AQSS. Se encarga de simplificar y automatizar el trabajo de un centron de educación a distancia.

        Implementa la funcionalidad básica que será utilizada por otras extensiones como:
         - Maya | Valid: gestión de las convalidaciones,
         - Maya | Report: generación de informes
         - Maya | Students: gestión de tareas relativas a estudiantes: anulaciones...
         - Maya | Bookings: gestión de reservas: espacios, material personal de apoyo...

        Este módulo permite entre otras cosas
         - Control de profesores y sus roles
         - Control de enseñanzas: módulos y asignaturas
         - Generación automática de calendiario escolar y horario
         - Gestión de las aulas virtuales
         - Gestión de las tareas automatizadas (CronJobs)
         - Gestión de las notificaciones (envío  de mails) al profesorado
    """,

    'website': "https://portal.edu.gva.es/ceedcv/",
    'author': 'Alfredo Oltra',
    'maintainer': 'Alfredo Oltra <alfredo.ptcf@gmail.com>',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Productivity',

    'license': 'AGPL-3',
    'price': 0,

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        # seguridad
        'security/core_access.xml',
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # datos de modelos
        'data/companies.xml', # Los tipos de estudios impartidos en el centro
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
}

