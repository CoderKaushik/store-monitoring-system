from sqlalchemy.orm import Session
from . import models
from sqlalchemy import func

def fetch_report(db: Session, report_id: str):
    query = db.query(models.Report)
    report = query.filter(models.Report.report_id == report_id).first()
    return report

def insert_report(db: Session, report_id: str) -> models.Report:
    new_report = models.Report(
        report_id=report_id,
        status=models.ReportStatus.RUNNING
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return new_report

def set_report_status(db: Session, report_id: str, status: models.ReportStatus, file_path: str = None):
    rep = fetch_report(db, report_id)
    if rep:
        rep.status = status
        if file_path is not None:
            rep.file_path = file_path
        db.commit()

def list_store_ids(db: Session) -> list[str]:
    store_rows = db.query(models.StoreStatus.store_id).distinct().all()
    store_ids = [row[0] for row in store_rows]
    return store_ids


def latest_timestamp(db: Session):
    max_time = db.query(func.max(models.StoreStatus.timestamp_utc)).scalar()
    return max_time
