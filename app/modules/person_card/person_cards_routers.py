from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from ..auth.auth import validate_user
from app.db.config import get_db
from ..person_card.models.person_card import Person, PersonKinship
from ..person_card.entities.person_cards import (
    PersonCardBaseSchema,
    PersonCardCreateSchema,
    PersonCardUpdateSchema,
    PersonCardResponseSchema,
    PersonCardWithKinshipResponseSchema,
    KinshipCreateSchema,
    KinshipUpdateSchema
)
from .operators import person_card


router = APIRouter(prefix='/person_card', tags=['Person_cards'])


@router.get('/{person_id}')
def get_person_card(person_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = person_card.get_person_card(person_id, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.post('/')
def create_person_card(person_data: PersonCardCreateSchema, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = person_card.create_person_card(person_data, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.patch('/')
def update_person_card(person_data: PersonCardUpdateSchema, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = person_card.update_person_card(person_data, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.delete('/{person_id}/')
def delete_person_card(person_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = person_card.delete_person_card(person_id, db)
        if response.get('success'):
            return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=response
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )
