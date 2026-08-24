import os

class Config:  
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta_aqui'
    DATABASE = 'pacientes.db'

