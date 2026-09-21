from __future__ import annotations

import time
import traceback
from datetime import datetime

from app.database.connection import SessionLocal
from app.university_ai.services.portal_integration import (
    get_due_sync_schedules,
    create_sync_job_from_schedule,
    mark_schedule_run,
    get_retryable_sync_jobs,
    retry_sync_job,
)


WORKER_INTERVAL_SECONDS = 30


def process_schedules():
    db = SessionLocal()

    try:
        # Check all universities with due schedules
        # Current implementation starts with the known university scope.
        for university_id in range(1, 10000):
            schedules = get_due_sync_schedules(db, university_id)

            if not schedules:
                continue

            for schedule in schedules:
                try:
                    job = create_sync_job_from_schedule(
                        db=db,
                        university_id=university_id,
                        schedule_id=schedule.id,
                    )

                    mark_schedule_run(
                        db=db,
                        university_id=university_id,
                        schedule_id=schedule.id,
                        status="started",
                    )

                    print(
                        f"[WORKER] Schedule {schedule.id} "
                        f"created sync job {job.id}"
                    )

                except Exception as exc:
                    print(
                        f"[WORKER] Schedule {schedule.id} failed: {exc}"
                    )

    finally:
        db.close()


def process_retries():
    db = SessionLocal()

    try:
        for university_id in range(1, 10000):
            jobs = get_retryable_sync_jobs(db, university_id)

            for job in jobs:
                try:
                    retried = retry_sync_job(
                        db=db,
                        university_id=university_id,
                        sync_id=job.id,
                    )

                    print(
                        f"[WORKER] Retry job {job.id}: "
                        f"{retried.status}"
                    )

                except Exception as exc:
                    print(
                        f"[WORKER] Retry job {job.id} failed: {exc}"
                    )

    finally:
        db.close()


def worker_loop():
    print("ALOKO UNIVERSITY PORTAL WORKER: STARTED")
    print(f"WORKER INTERVAL: {WORKER_INTERVAL_SECONDS}s")

    while True:
        try:
            process_schedules()
            process_retries()

        except Exception:
            print("[WORKER] Unexpected error:")
            traceback.print_exc()

        time.sleep(WORKER_INTERVAL_SECONDS)


if __name__ == "__main__":
    worker_loop()