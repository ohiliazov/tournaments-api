from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..crud import delete_instance, insert_instance, select_instances, update_instance
from ..dependencies import get_session
from ..models import Participant, Player, Scoring, Tournament
from ..schemas import ParticipantCreate, ParticipantRead, ParticipantUpdate


router = APIRouter(tags=["participants"])


@router.get("/participants", response_model=list[ParticipantRead])
async def read_participants(
    tournament_id: int = None,
    player_id: int = None,
    session: Session = Depends(get_session),
):
    if not tournament_id and not player_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Please provide tournament_id or player_id"
        )
    filters = []
    if tournament_id:
        filters.append(Participant.tournament_id == tournament_id)
    if player_id:
        filters.append(Participant.player_id == player_id)

    participants = select_instances(session, Participant, filters=filters)
    return participants


@router.post("/participants", response_model=ParticipantRead)
def create_participant(
    data: ParticipantCreate,
    session: Session = Depends(get_session),
):
    tournament = session.get(Tournament, data.tournament_id)

    if not tournament:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tournament not found")

    player = session.get(Player, data.player_id)
    if not player:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")

    participant = Participant.from_orm(data)

    for round_number in range(tournament.number_of_rounds):
        if round_number in data.rounds:
            scoring = Scoring.from_orm(data.rounds[round_number])
        else:
            scoring = Scoring(round_number=round_number)
        participant.rounds.append(scoring)

    insert_instance(session, participant)
    return participant


@router.get("/participants/{participant_id}", response_model=ParticipantRead)
async def read_participant(
    participant_id: int, session: Session = Depends(get_session)
):
    if participant := session.get(Participant, participant_id):
        return participant
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.put("/participants/{participant_id}", response_model=ParticipantRead)
async def update_participant(
    participant_id: int,
    data: ParticipantUpdate,
    session: Session = Depends(get_session),
):
    if participant := update_instance(session, Participant, participant_id, data):
        return participant
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.delete("/participants/{participant_id}", response_model=ParticipantRead)
async def delete_participant(
    participant_id: int, session: Session = Depends(get_session)
):
    if participant := delete_instance(session, Participant, participant_id):
        return participant
    raise HTTPException(status.HTTP_404_NOT_FOUND)
