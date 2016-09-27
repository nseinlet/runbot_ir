# -*- coding: utf-8 -*-
{
    'name': "runbot_ir",

    'summary': """
        Runbot as information radiator""",

    'description': """
        Use the runbot as an information radiator
    """,

    'author': "Odoo s.a.",
    'website': "http://odoo.com",

    'category': 'Uncategorized',
    'version': '1.0',

    'depends': ['runbot', 'website'],

    'data': [
        'views/repo.xml',
        'views/templates.xml',
    ],
}
