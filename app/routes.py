import re
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Response
from sqlalchemy.exc import IntegrityError
from app.models import LinkCreate, LinkResponse
from app.repository import LinkRepository, link_to_response

router = APIRouter()


@router.get("/api/links", response_model=list[LinkResponse])
def get_links(range_param: Optional[str] = Query(None, alias="range"), response: Response = None):
    total_count = LinkRepository.get_total_count()

    if range_param is None:
        links = LinkRepository.get_all()
        result = [link_to_response(link) for link in links]
        if response:
            response.headers["Content-Range"] = f"links 0-{len(result) - 1}/{total_count}"
        return result

    range_match = re.match(r'\[(\d+),\s*(\d+)\]', range_param)
    if not range_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid range format. Expected format: [start, end]"
        )

    start = int(range_match.group(1))
    end = int(range_match.group(2))

    if start < 0 or end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid range: start must be >= 0 and end must be >= start"
        )

    limit = end - start + 1
    offset = start

    links = LinkRepository.get_all(offset=offset, limit=limit)
    result = [link_to_response(link) for link in links]

    if len(result) > 0:
        actual_end = start + len(result) - 1
    else:
        actual_end = max(0, start - 1)

    if response:
        response.headers["Content-Range"] = f"links {start}-{actual_end}/{total_count}"

    return result


@router.post("/api/links", status_code=status.HTTP_201_CREATED, response_model=LinkResponse)
def create_link(link_data: LinkCreate):
    existing_link = LinkRepository.get_by_short_name(link_data.short_name)
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short name already exists"
        )

    try:
        link = LinkRepository.create(link_data)
        return link_to_response(link)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short name already exists"
        )


@router.get("/api/links/{link_id}", response_model=LinkResponse)
def get_link(link_id: int):
    link = LinkRepository.get_by_id(link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return link_to_response(link)


@router.put("/api/links/{link_id}", response_model=LinkResponse)
def update_link(link_id: int, link_update: LinkCreate):
    link = LinkRepository.get_by_id(link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    if link.short_name != link_update.short_name:
        existing_link = LinkRepository.get_by_short_name(link_update.short_name)
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short name already exists"
            )

    try:
        updated_link = LinkRepository.update(link_id, link_update)
        if not updated_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        return link_to_response(updated_link)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short name already exists"
        )


@router.delete("/api/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(link_id: int):
    deleted = LinkRepository.delete(link_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return None
