{
    'name': 'IX-Inversors Manager',
    'author': 'CyBerX ©',
    'category': 'Extra Tools',
    'sequence': 50,
    'summary': "Manage all IX-Inversors accounts",
    'website': 'https://www.wedoo.tech',
    'version': '13.0.1.0.3',
    'description': """
IX-Inversors Manager
===============================================================
This module Manage all IX-Inversors accounts.
    """,
    'depends': [
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_res_partner.xml',
        'views/ix_user.xml',
        'views/ix_plan.xml',
        'views/ix_inversion.xml',
        'views/ix_daily_payment.xml',
        'views/ix_crypto.xml',
        'wizards/config.xml',
        'data/data.xml',
        'data/data_crypto.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
}
