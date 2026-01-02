from sqlalchemy import create_engine, Column, Integer, String, Boolean # TAMBAHKAN Boolean DI SINI
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey 

SQLALCHEMY_DATABASE_URL = "sqlite:///./skripsi.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    credits = Column(Integer, default=0)
    created_at = Column(String, default="Now")  # Tambahkan field created_at

    # --- BARU: Kolom untuk membedakan Admin ---
    is_admin = Column(Boolean, default=False)

class TopUpRequest(Base):
    __tablename__ = "topup_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Siapa yang minta?
    amount = Column(Integer) # Berapa banyak kredit?
    method = Column(String) # Bank Transfer atau E-Wallet
    account_number = Column(String) # Nama file bukti transfer
    status = Column(String, default="Pending") # Pending, Approved, Rejected
    created_at = Column(String, default="Now") # Waktu request
    price = Column(Integer, default=0)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ini akan membuat ulang tabel jika struktur berubah (untuk dev)
Base.metadata.create_all(bind=engine)