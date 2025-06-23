from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True, nullable=False)
    original_file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tables")
