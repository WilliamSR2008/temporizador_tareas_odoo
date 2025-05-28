from odoo import models, fields, api
from odoo.exceptions import UserError

class TemporizadorTarea(models.Model):
    _name = 'temporizador.tarea'
    _description = 'Temporizador de Tarea'

    usuario_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.uid)
    empleado_id = fields.Many2one('hr.employee', string='Empleado', compute='_calcular_empleado', store=True)
    tarea_id = fields.Many2one('project.task', string='Tarea')
    hora_inicio = fields.Datetime(string='Hora de inicio', default=fields.Datetime.now)
    hora_fin = fields.Datetime(string='Hora de fin')
    duracion = fields.Float(string='Duración (horas)', compute='_calcular_duracion', store=True)
    estado = fields.Selection([('activo', 'Activo'), ('detenido', 'Detenido')], default='activo')

    @api.depends('usuario_id')
    def _calcular_empleado(self):
        for registro in self:
            empleado = self.env['hr.employee'].search([('user_id', '=', registro.usuario_id.id)], limit=1)
            registro.empleado_id = empleado

    @api.depends('hora_inicio', 'hora_fin')
    def _calcular_duracion(self):
        for registro in self:
            if registro.hora_fin:
                delta = registro.hora_fin - registro.hora_inicio
                registro.duracion = round(delta.total_seconds() / 3600, 2)
            else:
                registro.duracion = 0.0

    def detener_temporizador(self):
        for registro in self:
            if registro.estado == 'detenido':
                raise UserError('El temporizador ya está detenido.')
            registro.hora_fin = fields.Datetime.now()
            registro.estado = 'detenido'
            registro._crear_hoja_tiempo()

    def _crear_hoja_tiempo(self):
        self.ensure_one()
        if not self.empleado_id:
            raise UserError('No se encontró un empleado vinculado al usuario.')
        self.env['account.analytic.line'].create({
            'name': f'Temporizador: {self.tarea_id.name}',
            'employee_id': self.empleado_id.id,
            'task_id': self.tarea_id.id,
            'project_id': self.tarea_id.project_id.id,
            'unit_amount': self.duracion,
            'date': fields.Date.today(),
        })

class TareaProyecto(models.Model):
    _inherit = 'project.task'

    temporizador_activo = fields.Boolean(
        string='Temporizador Activo',
        compute='_compute_temporizador_activo',
        store=False
    )

    @api.depends('temporizadores_ids.estado')
    def _compute_temporizador_activo(self):
        for task in self:
            # True si hay algún temporizador con estado 'activo'
            task.temporizador_activo = any(t.estado == 'activo' for t in task.temporizadores_ids)

    temporizadores_ids = fields.One2many('temporizador.tarea', 'tarea_id', string='Temporizadores')

    def iniciar_temporizador(self):
        temporizador_activo = self.env['temporizador.tarea'].search([
            ('usuario_id', '=', self.env.uid),
            ('estado', '=', 'activo')
        ])
        if temporizador_activo:
            raise UserError('Ya tienes un temporizador activo.')
        self.env['temporizador.tarea'].create({
            'tarea_id': self.id,
            'usuario_id': self.env.uid,
        })

    def detener_temporizador(self):
        temporizador_activo = self.env['temporizador.tarea'].search([
            ('usuario_id', '=', self.env.uid),
            ('tarea_id', '=', self.id),
            ('estado', '=', 'activo')
        ], limit=1)
        if not temporizador_activo:
            raise UserError('No hay un temporizador activo para esta tarea.')
        temporizador_activo.detener_temporizador()
