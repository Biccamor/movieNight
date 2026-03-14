from sqlmodel import SQLModel
from database.main_db import engine, create_tables

def reset_db():
    print("Niszczenie starych tabel...")
    SQLModel.metadata.drop_all(engine)
    
    print("Tworzenie nowych tabel...")
    create_tables()

if __name__ == "__main__":
    reset_db()