from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.reports import build_pdf_report

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/pdf")
def download_report(db: Session = Depends(get_db)):
    pdf_bytes = build_pdf_report(db)
    filename = f"monitor-nasdaq-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
