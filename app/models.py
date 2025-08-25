import enum
from sqlalchemy import Column, Integer, String, DateTime, Time, Enum as SQLAlchemyEnum
from .database import Base

class ReportStatus(str, enum.Enum):
    RUNNING = "Running"
    COMPLETE = "Complete"

class StoreStatus(Base):
    __tablename__ = 'store_status'
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    timestamp_utc = Column(DateTime, index=True)
    status = Column(String)

class BusinessHours(Base):
    __tablename__ = 'business_hours'
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    day_of_week = Column(Integer)
    start_time_local = Column(Time)
    end_time_local = Column(Time)

class StoreTimezone(Base):
    __tablename__ = 'store_timezones'
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, unique=True, index=True)
    timezone_str = Column(String)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    report_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(SQLAlchemyEnum(ReportStatus), default=ReportStatus.RUNNING)
    file_path = Column(String, nullable=True)