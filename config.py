import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Segurança da Aplicação
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-secreta-padrao-dev')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secreta-padrao-dev')
    
    # Captura as credenciais do banco individualmente
    DB_USER = os.environ.get('POSTGRES_USER', 'postgres')
    DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    DB_HOST = os.environ.get('POSTGRES_HOST', 'db')
    DB_PORT = os.environ.get('POSTGRES_PORT', '5432')
    DB_NAME = os.environ.get('POSTGRES_DB', 'agendamento_uemg')
    
    # Monta a URL de conexão nativamente no Python (Garante 100% de funcionamento)
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Desativa o rastreamento de modificações para economizar memória
    SQLALCHEMY_TRACK_MODIFICATIONS = False