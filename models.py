from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)

    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    position = Column(String)
    jersey = Column(String)
    height = Column(String)
    weight = Column(String)
    date_of_birth = Column(String)
    age = Column(Integer)
    college = Column(String)

    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="players")
