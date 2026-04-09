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

    opening_hours = fields.Text(
        string=_('Horario de Apertura'), 
        compute='_compute_opening_hours', 
        store=False,
        help=_("Horario calculado automáticamente en función de las sesiones.")
    )

    @api.depends('session_ids.start_time', 'session_ids.end_time', 'session_ids.week_day')
    def _compute_opening_hours(self):
        """
        Calcula el horario de apertura agrupando por día y fusionando los rangos contiguos.
        """
        # Función para convertir float
        def format_time(t):
            hours = int(t)
            minutes = int(round((t - hours) * 60))
            if minutes == 60:
                hours += 1
                minutes = 0
            return f"{hours:02d}:{minutes:02d}"

        week_order = ['L', 'M', 'X', 'J', 'V']
        
        day_dict = dict(self.env['maya_core.session_schedule']._fields['week_day'].selection)

        for location in self:
            if not location.session_ids:
                location.opening_hours = _("Sin horario asignado")
                continue

            # se agrupa sesiones por día
            sessions_by_day = {day: [] for day in week_order}
            for session in location.session_ids.filtered(lambda s: s.active):
                sessions_by_day[session.week_day].append((session.start_time, session.end_time))

            schedule_lines = []

            for day in week_order:
                intervals = sessions_by_day[day]
                if not intervals:
                    continue

                # intervalos por la hora de inicio
                intervals.sort(key=lambda x: x[0])

                merged = []
                current_start, current_end = intervals[0]

                for start, end in intervals[1:]:
                    if start <= current_end:
                        current_end = max(current_end, end)
                    else:
                        merged.append((current_start, current_end))
                        current_start, current_end = start, end
                
                # Se guarda el último bloque que quede pendiente
                merged.append((current_start, current_end))

                #Formatear a String  09:00 - 11:00 / 15:00 - 17:00)
                formatted_intervals = " / ".join([f"{format_time(s)} - {format_time(e)}" for s, e in merged])
                
                day_name = day_dict.get(day, day)
                schedule_lines.append(f"{day_name}: {formatted_intervals}")

            # Se une con saltos de línea para que quede estético en la vista form
            location.opening_hours = "\n".join(schedule_lines)
