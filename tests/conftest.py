from typing import List

import faker
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import Participant, Player, Tournament
from app.settings import settings

from .utils import participant_create_data, player_create_data, tournament_create_data


if settings.test_database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(settings.test_database_url, connect_args=connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

Base.metadata.create_all(bind=engine)

fake = faker.Faker()


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db_players(db_session) -> List[Player]:
    players = [Player(**player_create_data().dict()) for _ in range(3)]
    db_session.add_all(players)
    db_session.commit()

    for player in players:
        db_session.refresh(player)

    yield players

    for player in players:
        for participant in player.history:
            db_session.delete(participant)
        db_session.delete(player)

    db_session.commit()


@pytest.fixture
def db_tournaments(db_session) -> List[Tournament]:
    tournaments = [Tournament(**tournament_create_data().dict()) for _ in range(3)]
    db_session.add_all(tournaments)
    db_session.commit()

    for tournament in tournaments:
        db_session.refresh(tournament)

    yield tournaments

    for tournament in tournaments:
        for participant in tournament.participants:
            db_session.delete(participant)
        db_session.delete(tournament)

    db_session.commit()


@pytest.fixture
def db_participants(db_session, db_players, db_tournaments) -> List[Participant]:
    participants = [
        Participant(**participant_create_data(player.id, tournament.id).dict())
        for player in db_players
        for tournament in db_tournaments
    ]
    db_session.add_all(participants)
    db_session.commit()

    for participant in participants:
        db_session.refresh(participant)

    yield participants


@pytest.fixture
def players_url() -> str:
    return "/api/v1/players"


@pytest.fixture
def tournaments_url() -> str:
    return "/api/v1/tournaments"


@pytest.fixture
def participants_url() -> str:
    return "/api/v1/participants"