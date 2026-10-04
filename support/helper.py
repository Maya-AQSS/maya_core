import logging
_logger = logging.getLogger(__name__)


from odoo.exceptions import UserError
import pandas as pd
import math

def get_mail_server(self, alias: str):
    """
    Busca y devuelve el mail.server del alias indicado (o lanza UserError).

    :alias alias del correo a enviar la notificación
    """
    
    if alias.upper() == 'CENTRO': 
      param='maya_core.alias_mail_center'
    elif alias.upper() == 'MAYA': 
      param='maya_core.alias_maya_mail'
    else:
      raise UserError(f'El alias {alias} no existe como servidor de correo .')
       
    mail_alias = self.env['ir.config_parameter'].get_param(param)
    if not mail_alias:
        raise UserError(f'No se ha definido el servidor de correo de {alias} (param: {param}).')
    mail_server = self.env['ir.mail_server'].search([('name', '=', mail_alias)], limit=1)
    if not mail_server:
        raise UserError(f"No se encontró el servidor de correo '{mail_alias}' en ir.mail_server.")
    
    return mail_server

def read_csv(filename: str) -> tuple[pd.DataFrame, pd.Series]:
  """
  Lee el fichero CSV  y devuelve el DataFrame original y su versión aplanada.

  :param filename: Ruta completa al fichero CSV.
  :return: Una tupla (df, df_aplanado) donde:
            - df: DataFrame original leído del CSV
            - df_aplanado: Serie con todos los valores del DataFrame aplanados
  :raises UserError: Si el fichero no existe o no se puede leer.
  """
  try:
    df = pd.read_csv(filename)
  except FileNotFoundError:
    raise Exception(f"¡Operación cancelada!. No se pudo encontrar el fichero de datos de alumnos de Itaca en {filename}.")
  except pd.errors.ParserError as e:
    raise Exception(f"Error al leer el fichero CSV {filename}: {str(e)}")

  df_aplanado = df.stack()

  return df, df_aplanado


def clean_str(val) -> str:
  """
  Limpia y formatea una cadena vacia de texto proveniente de pandas.
  Pandas asigna por defectyo Nan a una cadena vacía
  """
  if val is None or (isinstance(val, float) and math.isnan(val)):
      return ''
  return str(val).strip()