from sqlmodel import SQLModel, select, Session, func
from database.main_db import create_tables
from database.database_setup import Movie
import scripts.dependencies as d 
def reset_db():
    print("Niszczenie starych tabel...")
    SQLModel.metadata.drop_all(d.engine)
   
    print("Tworzenie nowych tabel...")
    create_tables()

def check_if_empty():
    with Session(d.engine) as session:
        # Liczymy rekordy w tabeli Movie
        count = session.exec(select(func.count()).select_from(Movie)).one()
        if count == 0:
            print("0 rekordów")
        else:
            print(f" {count} filmów")
    return count == 0

if __name__ == "__main__":
    check_if_empty()
#    check_if_empty()