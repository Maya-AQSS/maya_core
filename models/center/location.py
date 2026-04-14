# -*- coding: utf-8 -*-

from odoo import models, api, fields, _

class Location(models.Model):
    """
    Define las ubicaciones
    """

    _name = 'maya_core.location'
    _description = 'Ubicaciones'

    name = fields.Char(_('Nombre'), required = True, translate = True)
    description = fields.Text(_('Descripción'), translate=True, help=_('Usos permitidos, normas de acceso y cualquier información relevante.'))

    # Añadidos campos que faltaban por definir de dirección y teléfono móvil
    address = fields.Char(string=_('Dirección'), required = True, help=_('Dirección de la ubicación física.'))
    phone_number = fields.Char(string=_('Teléfono'), required = False, help=_('Número de teléfono del departamento docente.'))


    image = fields.Image(
    string = _('Fotografía'),
    max_width = 1920,
    max_height = 1080,
    attachment=True
    )

    floor_plan = fields.Image(
    string = _('Plano'),
    max_width = 3508,
    max_height = 2480,
    attachment=True
    )  # va al filestore

    map_url = fields.Char(string = _('Enlace Google Maps'), help = _('URL de Google Maps'))

    session_ids = fields.Many2many('maya_core.session_schedule', string=_('Sesiones Asignadas'))

    opening_hours = fields.Text(string='Horario de Apertura', compute='_compute_opening_hours')

    @api.depends('session_ids.start_time', 'session_ids.end_time', 'session_ids.week_day', 'session_ids.active')
    def _compute_opening_hours(self):
        # pasar de 9.5 a "09:30"
        def format_float_time(value):
            hours, mins = divmod(round(value * 60), 60)
            return "%02d:%02d" % (hours, mins)

        for record in self:
            # Extraer y formatear el horario de cada día
            schedules_by_day = []
            days_info = [('L', 'Lunes'), ('M', 'Martes'), ('X', 'Miércoles'), ('J', 'Jueves'), ('V', 'Viernes')]
            
            for code, name in days_info:
                # Filtrar sesiones de este día y ordenarlas
                sessions = record.session_ids.filtered(lambda s: s.active and s.week_day == code).sorted('start_time')
                
                if not sessions:
                    schedules_by_day.append({'name': name, 'text': 'Cerrado'})
                    continue

                # Fusionar intervalos (9-10 y 10-11 -> 9-11)
                merged = []
                for s in sessions:
                    if not merged or s.start_time > merged[-1][1]:
                        merged.append([s.start_time, s.end_time])
                    else:
                        merged[-1][1] = max(merged[-1][1], s.end_time)
                
                # Crear el texto del día (ej: "09:00 - 13:00 / 16:00 - 20:00")
                day_text = " / ".join(["%s - %s" % (format_float_time(m[0]), format_float_time(m[1])) for m in merged])
                schedules_by_day.append({'name': name, 'text': day_text})

            # Agrupar días consecutivos con el mismo horario
            final_groups = []
            if schedules_by_day:
                current_group = {'start_day': schedules_by_day[0]['name'], 'last_day': schedules_by_day[0]['name'], 'text': schedules_by_day[0]['text']}
                
                for i in range(1, len(schedules_by_day)):
                    day = schedules_by_day[i]
                    if day['text'] == current_group['text']:
                        current_group['last_day'] = day['name']
                    else:
                        final_groups.append(current_group)
                        current_group = {'start_day': day['name'], 'last_day': day['name'], 'text': day['text']}
                final_groups.append(current_group)

            # Construir el string final
            lines = []
            for g in final_groups:
                if g['text'] == 'Cerrado': continue # no mostrar días cerrados
                
                label = g['start_day'] if g['start_day'] == g['last_day'] else "De %s a %s" % (g['start_day'], g['last_day'])
                lines.append("%s: %s" % (label, g['text']))
            
            record.opening_hours = "\n".join(lines) if lines else "Sin horario definido"