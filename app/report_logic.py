import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from sqlalchemy.orm import Session
from . import models, crud

def calculate_interval_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> float:
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start >= overlap_end:
        return 0.0

    delta = overlap_end - overlap_start
    seconds = delta.total_seconds()
    return seconds

def calculate_store_metrics(db: Session, store_id: str, max_timestamp: datetime) -> dict:
    last_week_start = max_timestamp - timedelta(weeks=1)
    timezone_entry = db.query(models.StoreTimezone).filter(models.StoreTimezone.store_id == store_id).first()
    store_timezone_str = timezone_entry.timezone_str if timezone_entry else "America/Chicago"
    store_timezone = pytz.timezone(store_timezone_str)
    business_hours_entries = db.query(models.BusinessHours).filter(models.BusinessHours.store_id == store_id).all()
    polls = db.query(models.StoreStatus)\
        .filter(models.StoreStatus.store_id == store_id, 
                models.StoreStatus.timestamp_utc >= last_week_start - timedelta(hours=1))\
        .order_by(models.StoreStatus.timestamp_utc.asc())\
        .all()
    utc_business_intervals = []
    if not business_hours_entries:
        utc_business_intervals.append((last_week_start, max_timestamp))
    else:
        hours_by_day = {h.day_of_week: (h.start_time_local, h.end_time_local) for h in business_hours_entries}
        current_day_utc = last_week_start
        while current_day_utc.date() <= max_timestamp.date():
            current_day_local = current_day_utc.astimezone(store_timezone)
            day_of_week = current_day_local.weekday()
            if day_of_week in hours_by_day:
                start_local_time, end_local_time = hours_by_day[day_of_week]
                if start_local_time is None or end_local_time is None:
                    current_day_utc += timedelta(days=1)
                    continue
                start_naive = datetime.combine(current_day_local.date(), start_local_time)
                end_naive = datetime.combine(current_day_local.date(), end_local_time)
                if end_local_time < start_local_time:
                    end_naive += timedelta(days=1)
                start_aware = store_timezone.localize(start_naive)
                end_aware = store_timezone.localize(end_naive)
                utc_business_intervals.append((start_aware.astimezone(pytz.utc), end_aware.astimezone(pytz.utc)))
            current_day_utc += timedelta(days=1)
    if not polls:
        return {
            "store_id": store_id, "uptime_last_hour": 0, "uptime_last_day": 0, "uptime_last_week": 0,
            "downtime_last_hour": 0, "downtime_last_day": 0, "downtime_last_week": 0
        }
    uptime_last_hour_secs, downtime_last_hour_secs = 0, 0
    uptime_last_day_secs, downtime_last_day_secs = 0, 0
    uptime_last_week_secs, downtime_last_week_secs = 0, 0
    for i in range(len(polls)):
        poll_start_time = polls[i].timestamp_utc.replace(tzinfo=pytz.UTC)
        status = polls[i].status
        if i + 1 < len(polls):
            poll_end_time = polls[i+1].timestamp_utc.replace(tzinfo=pytz.UTC)
        else:
            poll_end_time = max_timestamp
        for biz_start_utc, biz_end_utc in utc_business_intervals:
            overlap = calculate_interval_overlap(poll_start_time, poll_end_time, max(biz_start_utc, max_timestamp - timedelta(hours=1)), min(biz_end_utc, max_timestamp))
            if status == 'active': uptime_last_hour_secs += overlap
            else: downtime_last_hour_secs += overlap
            overlap = calculate_interval_overlap(poll_start_time, poll_end_time, max(biz_start_utc, max_timestamp - timedelta(days=1)), min(biz_end_utc, max_timestamp))
            if status == 'active': uptime_last_day_secs += overlap
            else: downtime_last_day_secs += overlap
            overlap = calculate_interval_overlap(poll_start_time, poll_end_time, max(biz_start_utc, max_timestamp - timedelta(weeks=1)), min(biz_end_utc, max_timestamp))
            if status == 'active': uptime_last_week_secs += overlap
            else: downtime_last_week_secs += overlap
    return {
        "store_id": store_id,
        "uptime_last_hour": round(uptime_last_hour_secs / 60),
        "uptime_last_day": round(uptime_last_day_secs / 3600),
        "uptime_last_week": round(uptime_last_week_secs / 3600),
        "downtime_last_hour": round(downtime_last_hour_secs / 60),
        "downtime_last_day": round(downtime_last_day_secs / 3600),
        "downtime_last_week": round(downtime_last_week_secs / 3600),
    }

def generate_full_report(db: Session, report_id: str):
    print(f"[{report_id}] Starting full report generation...")

    store_ids = crud.list_store_ids(db)
    latest_ts = crud.latest_timestamp(db)

    if not latest_ts:
        print("No data in store_status table. Aborting report.")
        return

    latest_ts = latest_ts.replace(tzinfo=pytz.UTC)

    results = []
    for idx, store_id in enumerate(store_ids, start=1):
        print(f"[{report_id}] Processing store {idx}/{len(store_ids)}: {store_id}")
        try:
            metrics = calculate_store_metrics(db, store_id, latest_ts)
            results.append(metrics)
        except Exception as err:
            print(f"[{report_id}] ERROR: Failed to process store {store_id}. Reason: {err}")

    df = pd.DataFrame(results)

    if df.empty:
        print(f"[{report_id}] No data processed. Report generation finished with empty results.")
        crud.set_report_status(db, report_id, models.ReportStatus.COMPLETE)
        return

    out_file = f"generated_reports/{report_id}.csv"
    df.to_csv(out_file, index=False)

    print(f"[{report_id}] Report saved to {out_file}")
    crud.set_report_status(db, report_id, models.ReportStatus.COMPLETE, out_file)
    print(f"[{report_id}] Database status updated to Complete.")