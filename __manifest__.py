
{
    'name': 'Temporizador de Tareas',
    'version': '16.0.1.0.0',
    'summary': 'Agrega un temporizador para tareas del proyecto',
    'category': 'Project',
    'author': 'William Sosa',
    'depends': ['project', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/temporizador_tareas_views.xml',
    ],
    'installable': True,
    'application': False,
}
