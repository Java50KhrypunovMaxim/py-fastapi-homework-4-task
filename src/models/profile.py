from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from src.database.models.base import Base


class ProfileModel(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    info = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    user = relationship("UserModel", back_populates="profile")
