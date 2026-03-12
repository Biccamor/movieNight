from sqlmodel import SQLModel
from main import engine
def reset_db():
    print("Niszczenie starych tabel...")
    SQLModel.metadata.drop_all(engine)
    
    print("Tworzenie nowych tabel...")
    SQLModel.metadata.create_all(engine)
    print("Baza danych jest czysta i gotowa!")

if __name__ == "__main__":
    reset_db()