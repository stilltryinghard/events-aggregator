import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CancelTicketUsecaseDep, CreateTicketUsecaseDep
from app.api.schemas import TicketCancelled, TicketCreate, TicketCreated
from app.clients.events_provider import SeatUnavailable
from app.usecases.errors import AppError, EventNotFound, TicketNotFound

router = APIRouter(prefix="/api")


@router.post(
    "/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketCreated
)
async def create_ticket(body: TicketCreate, usecase: CreateTicketUsecaseDep):
    try:
        ticket_id = await usecase.do(
            body.event_id, body.first_name, body.last_name, body.email, body.seat
        )
    except EventNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.detail) from None
    except AppError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.detail) from None
    except SeatUnavailable:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Seat is already taken"
        ) from None
    return TicketCreated(ticket_id=ticket_id)


@router.delete("/tickets/{ticket_id}", response_model=TicketCancelled)
async def cancel_ticket(ticket_id: uuid.UUID, usecase: CancelTicketUsecaseDep):
    try:
        await usecase.do(ticket_id)
    except (TicketNotFound, EventNotFound) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.detail) from None
    except AppError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.detail) from None
    return TicketCancelled(success=True)
