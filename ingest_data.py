import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, StoreStatus, BusinessHours, StoreTimezone
from datetime import datetime
import time


def parse_time(time_str):
    if pd.isnull(time_str):
        return None
    try:
        return datetime.strptime(str(time_str), "%H:%M:%S").time()
    except ValueError:
        return None


def ingest_all_data():
    print("Setting up database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

    session: Session = SessionLocal()
    start = time.time()

    try:
        print("Loading store status data...")
        status_df = pd.read_csv("data/store_status.csv")
        status_df["timestamp_utc"] = pd.to_datetime(
            status_df["timestamp_utc"].str.replace(" UTC", "", regex=False)
        )
        status_records = status_df.to_dict(orient="records")
        session.bulk_insert_mappings(StoreStatus, status_records)
        session.commit()
        print(f"{len(status_records)} status rows ingested.")

        print("Loading business hours...")
        hours_df = pd.read_csv("data/menu_hours.csv")
        for _, row in hours_df.iterrows():
            entry = BusinessHours(
                store_id=row["store_id"],
                day_of_week=row["dayOfWeek"],
                start_time_local=parse_time(row["start_time_local"]),
                end_time_local=parse_time(row["end_time_local"]),
            )
            session.add(entry)
        session.commit()
        print(f"{len(hours_df)} business hours rows ingested.")

        print("Loading store timezones...")
        tz_df = pd.read_csv("data/timezones.csv")
        tz_records = tz_df.to_dict(orient="records")
        session.bulk_insert_mappings(StoreTimezone, tz_records)
        session.commit()
        print(f"{len(tz_records)} timezone rows ingested.")

    except Exception as err:
        print(f"Ingestion failed: {err}")
        session.rollback()
    finally:
        session.close()
        end = time.time()
        print(f"Total ingestion took {end - start:.2f} seconds.")


if __name__ == "__main__":
    ingest_all_data()