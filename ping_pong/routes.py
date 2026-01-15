import re
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Response
from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
from ping_pong import database
from ping_pong.models import Link, LinkCreate, LinkResponse


def get_engine():
    """Получает engine из database модуля"""
    return database.engine


router = APIRouter()


def link_to_response(link: Link) -> LinkResponse:
    """Преобразует Link в LinkResponse"""
    return LinkResponse(
        id=link.id,
        original_url=link.original_url,
        short_name=link.short_name,
        short_url=link.short_url,
        created_at=link.created_at
    )


@router.get("/api/links", response_model=list[LinkResponse])
def get_links(range_param: Optional[str] = Query(None, alias="range"), response: Response = None):
    """Возвращает список всех ссылок с поддержкой пагинации"""
    with Session(get_engine()) as session:
        total_count = session.exec(select(func.count(Link.id))).one()

        # Если range не указан, возвращаем все записи
        if range_param is None:
            links = session.exec(select(Link)).all()
            result = [link_to_response(link) for link in links]
            if response:
                response.headers["Content-Range"] = f"links 0-{len(result) - 1}/{total_count}"
            return result

        # Парсим range параметр в формате [start, end]
        range_match = re.match(r'\[(\d+),\s*(\d+)\]', range_param)
        if not range_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid range format. Expected format: [start, end]"
            )

        start = int(range_match.group(1))
        end = int(range_match.group(2))

        # Валидация диапазона
        if start < 0 or end < start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid range: start must be >= 0 and end must be >= start"
            )

        limit = end - start + 1
        offset = start

        links = session.exec(select(Link).offset(offset).limit(limit)).all()
        result = [link_to_response(link) for link in links]

        if len(result) > 0:
            actual_end = start + len(result) - 1
        else:
            # Для пустого результата: если start > 0, то end = start - 1, иначе 0
            actual_end = max(0, start - 1)

        if response:
            response.headers["Content-Range"] = f"links {start}-{actual_end}/{total_count}"

        return result


@router.post("/api/links", status_code=status.HTTP_201_CREATED, response_model=LinkResponse)
def create_link(link_data: LinkCreate):
    """Создает новую ссылку"""
    with Session(get_engine()) as session:
        # Проверяем уникальность short_name
        existing_link = session.exec(
            select(Link).where(Link.short_name == link_data.short_name)
        ).first()
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short name already exists"
            )

        link = Link(
            original_url=link_data.original_url,
            short_name=link_data.short_name
        )
        session.add(link)
        try:
            session.commit()
            session.refresh(link)
            return link_to_response(link)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short name already exists"
            )


@router.get("/api/links/{link_id}", response_model=LinkResponse)
def get_link(link_id: int):
    """Возвращает данные ссылки по идентификатору"""
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        return link_to_response(link)


@router.put("/api/links/{link_id}", response_model=LinkResponse)
def update_link(link_id: int, link_update: LinkCreate):
    """Обновляет существующую ссылку"""
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )

        # Проверяем уникальность short_name, если он меняется
        if link.short_name != link_update.short_name:
            existing_link = session.exec(
                select(Link).where(Link.short_name == link_update.short_name)
            ).first()
            if existing_link:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Short name already exists"
                )

        link.original_url = link_update.original_url
        link.short_name = link_update.short_name
        session.add(link)
        try:
            session.commit()
            session.refresh(link)
            return link_to_response(link)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short name already exists"
            )


@router.delete("/api/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(link_id: int):
    """Удаляет ссылку"""
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        session.delete(link)
        session.commit()
        return None
