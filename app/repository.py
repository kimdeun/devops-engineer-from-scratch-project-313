from typing import Optional
from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
from app.models import Link, LinkCreate, LinkResponse
from app.database import engine


def link_to_response(link: Link) -> LinkResponse:
    return LinkResponse(
        id=link.id,
        original_url=link.original_url,
        short_name=link.short_name,
        short_url=link.short_url,
        created_at=link.created_at
    )


class LinkRepository:
    @staticmethod
    def get_total_count() -> int:
        with Session(engine) as session:
            return session.exec(select(func.count(Link.id))).one()

    @staticmethod
    def get_all(offset: Optional[int] = None, limit: Optional[int] = None) -> list[Link]:
        with Session(engine) as session:
            query = select(Link)
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return session.exec(query).all()

    @staticmethod
    def get_by_id(link_id: int) -> Optional[Link]:
        with Session(engine) as session:
            return session.get(Link, link_id)

    @staticmethod
    def get_by_short_name(short_name: str) -> Optional[Link]:
        with Session(engine) as session:
            return session.exec(
                select(Link).where(Link.short_name == short_name)
            ).first()

    @staticmethod
    def create(link_data: LinkCreate) -> Link:
        with Session(engine) as session:
            link = Link(
                original_url=link_data.original_url,
                short_name=link_data.short_name
            )
            session.add(link)
            try:
                session.commit()
                session.refresh(link)
                return link
            except IntegrityError:
                session.rollback()
                raise

    @staticmethod
    def update(link_id: int, link_data: LinkCreate) -> Optional[Link]:
        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return None

            link.original_url = link_data.original_url
            link.short_name = link_data.short_name
            session.add(link)
            try:
                session.commit()
                session.refresh(link)
                return link
            except IntegrityError:
                session.rollback()
                raise

    @staticmethod
    def delete(link_id: int) -> bool:
        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return False
            session.delete(link)
            session.commit()
            return True
