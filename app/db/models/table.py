from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db.base_class import Base


class UserTable(Base):
    __tablename__ = "user_tables"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    table_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    owner = relationship("User", back_populates="tables")
