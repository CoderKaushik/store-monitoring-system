import uuid
import os
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import models, crud, report_logic
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Store Monitoring API",
    description="An API to trigger and retrieve reports on store uptime and downtime."
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_report_generation(report_id: str):
    session = SessionLocal()
    try:
        report_logic.generate_full_report(session, report_id)
    finally:
        session.close()


@app.post("/trigger_report", status_code=202, tags=["Reports"])
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    crud.insert_report(db, report_id=new_id)
    background_tasks.add_task(run_report_generation, new_id)
    return {"report_id": new_id}


@app.get("/get_report/{report_id}", tags=["Reports"])
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = crud.fetch_report(db, report_id=report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Please check the ID.")

    if report.status == models.ReportStatus.RUNNING:
        return {"status": report.status.value}

    if report.status == models.ReportStatus.COMPLETE:
        path_to_file = report.file_path
        if not os.path.exists(path_to_file):
            raise HTTPException(status_code=404, detail="Report file not found on server.")
        return FileResponse(
            path=path_to_file,
            media_type="text/csv",
            filename=f"report_{report_id}.csv"
        )