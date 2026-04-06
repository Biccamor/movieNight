from sqlmodel import SQLModel, Session, text
import scripts.dependencies as d
from database.main_db import create_tables

def reset():
    print("Usuwanie starej tabeli użytkowników...")
    with Session(d.engine) as session:
        # Usuwamy tabelę app_user (i przy okazji room_session bo mogą mieć zależności)
        session.exec(text("DROP TABLE IF EXISTS app_user CASCADE"))
        session.commit()
    
    print("Tworzenie tabel od nowa...")
    create_tables()
    print("Gotowe! Możesz teraz spróbować się zalogować/zarejestrować.")

if __name__ == "__main__":
    reset()
