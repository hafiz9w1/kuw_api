{
    'name': 'Sharing API Framework',
    'version': '15.0.0.0.1',
    'author': 'Hafiz Abbas',
    'email': 'hafizabbas9w1@gmail.com',
    'sequence': 2,
    'category': 'Technical',
    'Summary': 'API integration',
    'description': """
    """,
    'depends': [
        'base',
        'mail',
        'point_of_sale',
        'stock',
    ],
    'external_dependencies': {
        'python': [
            'schema',
            'pypeg2',
        ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/pcv_api_data.xml',
        'views/pcv_api_handler_views.xml',
        'views/pcv_api_logs_views.xml',
        'views/api_handler_menuitem.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
