from datetime import datetime, timedelta, timezone

import pytest

from api.v1.services.upload_service import UploadService
from api.v1.schemas.upload import UploadCreate
from api.v1.models.upload import ImageUpload, ProcessingLog, UploadStatus


def test_create_and_get_upload(db_session):
    svc = UploadService(db_session)
    data = UploadCreate(original_filename="file.jpg", file_size=1234, mime_type="image/jpeg")
    upload = svc.create_upload(data, original_url="http://example.com/file.jpg")

    assert upload is not None
    assert upload.id is not None
    assert upload.status == UploadStatus.PENDING

    fetched = svc.get_upload(upload.id)
    assert fetched is not None
    assert fetched.id == upload.id


def test_get_upload_missing(db_session):
    svc = UploadService(db_session)
    assert svc.get_upload("non-existent-id") is None


def test_update_upload_status_transitions(db_session):
    svc = UploadService(db_session)
    data = UploadCreate(original_filename="file2.jpg")
    upload = svc.create_upload(data, original_url="http://example.com/2.jpg")

    # Move to processing
    updated = svc.update_upload_status(upload.id, UploadStatus.PROCESSING)
    assert updated is not None
    assert updated.status == UploadStatus.PROCESSING
    assert updated.processing_started_at is not None

    # Move to completed
    updated = svc.update_upload_status(upload.id, UploadStatus.COMPLETED)
    assert updated.status == UploadStatus.COMPLETED
    assert updated.processing_completed_at is not None

    # Non-existent
    assert svc.update_upload_status("nope", UploadStatus.FAILED) is None


def test_update_processed_urls(db_session):
    svc = UploadService(db_session)
    data = UploadCreate(original_filename="file3.jpg")
    upload = svc.create_upload(data, original_url="http://example.com/3.jpg")

    svc.update_processed_urls(upload.id, thumbnail_url="http://cdn/thumb.jpg")
    refreshed = svc.get_upload(upload.id)
    assert refreshed.thumbnail_url == "http://cdn/thumb.jpg"

    svc.update_processed_urls(upload.id, resized_url="http://cdn/resized.jpg", compressed_url="http://cdn/compressed.jpg")
    refreshed = svc.get_upload(upload.id)
    assert refreshed.resized_url == "http://cdn/resized.jpg"
    assert refreshed.compressed_url == "http://cdn/compressed.jpg"


def test_add_processing_log(db_session):
    svc = UploadService(db_session)
    data = UploadCreate(original_filename="file4.jpg")
    upload = svc.create_upload(data, original_url="http://example.com/4.jpg")

    log = svc.add_processing_log(upload.id, step="download", status="started", message="ok", duration_ms=123)
    assert isinstance(log, ProcessingLog)
    assert log.upload_id == upload.id
    assert log.step == "download"
    assert log.status == "started"

    # ensure it's persisted
    logs = db_session.query(ProcessingLog).filter(ProcessingLog.upload_id == upload.id).all()
    assert len(logs) == 1


def test_cleanup_failed_uploads(db_session):
    svc = UploadService(db_session)
    data = UploadCreate(original_filename="old.jpg")
    old = svc.create_upload(data, original_url="http://example.com/old.jpg")

    # mark as failed and set created_at to old
    old.status = UploadStatus.FAILED
    old.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db_session.commit()

    cleaned = svc.cleanup_failed_uploads(hours_old=24)
    assert cleaned >= 1
    assert svc.get_upload(old.id) is None
