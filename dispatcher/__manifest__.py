# -*- coding: utf-8 -*-
{
    'name': 'Dispatcher',
    'sequence': 3 ,
    'version': '1.0',
    'category': 'Logistics',
    'depends': ['base','web','sale','stock'],  
    'data': [
        'security/ir.model.access.csv',
        # 'views/delivery_load_views.xml',
        'views/delivery_route_views.xml',
        # 'security/dispatcher_security.xml',
        'views/views.xml',
        # 'views/assets.xml',  
        'reports/dispatcher_report.xml'
    ],
     'installable': True,
     'application': True,
    'description': 'Despacho de Cargas',
    'author': 'Joel S. Martinez Espinal',
    'license': 'LGPL-3',
    'demo':[
        'data/data.xml'
    ]
}
