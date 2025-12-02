import os
from dotenv import load_dotenv
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA")

SIENGE_USERNAME = os.getenv("SIENGE_USERNAME")
SIENGE_PASSWORD = os.getenv("SIENGE_PASSWORD")