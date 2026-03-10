from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

###CONFIGURAÇÕES DE SEGURANÇA PARA AUTENTICAÇÃO E GERENCIAMENTO DE USUÁRIOS
SECRET_KEY = "minha_chave_super_secreta_123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

###CRIPTOGRAFIA DE SENHAS COM BCRYPT
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


###CRIA HASH DA SENHA
def hash_password(password: str):
    return pwd_context.hash(password)

###VERIFICA SENHA PLANA COM HASH
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

###CRIA TOKEN DE ACESSO COM EXPIRAÇÃO
def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt