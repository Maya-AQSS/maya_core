# -*- coding: utf-8 -*-

# contextos posibles para las tareas automatizadas
CRON_CONTEXTS = [
    'FPC', # General para todos los ciclos (todos los estudiantes) : convalidaciones o renuncias, etc
    'FPD', # General para todos los departamentos (todos los profesores) :explicación de procedimientos, cumplimentación de formularios, etc
    'FPE', # General para todos los empleados (todo el claustro de FP) 
    'DEP', # Asociada a un departamento: mensajes de bienvenida, explicación de procedimientos, etc
    'COUR',  # Asociada a un Ciclo: mensaje de bienvenida, convocatoria de reuniones, apertura o fin de plazos
    'SUBJ' # Asociada a un Módulo
]