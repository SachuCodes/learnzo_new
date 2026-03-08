# app/api/alerts.py

from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.services.logging_service import ensure_learner_exists

router = APIRouter(prefix="/alerts", tags=["alerts"])


# --------------------------------------------------
# 1️⃣ FETCH ALERTS (Parent / Teacher)
# --------------------------------------------------
@router.get("/{learner_id}", dependencies=[Depends(require_role("parent", "teacher", "admin"))])
def fetch_alerts(learner_id: str):
    ensure_learner_exists(learner_id)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            topic,
            alert_type,
            severity,
            message,
            created_at,
            acknowledged_at
        FROM alerts
        WHERE learner_id = %s
        ORDER BY created_at DESC
        """,
        (learner_id,)
    )

    alerts = cursor.fetchall()
    cursor.close()
    db.close()

    return {
        "learner_id": learner_id,
        "alerts": alerts
    }


# --------------------------------------------------
# 2️⃣ ACKNOWLEDGE ALERT (Teacher/Admin)
# --------------------------------------------------
@router.post("/{alert_id}/acknowledge", dependencies=[Depends(require_role("teacher", "admin"))])
def acknowledge_alert(alert_id: int, user=Depends(get_current_user)):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE alerts
        SET acknowledged_at = NOW(),
            acknowledged_by = %s
        WHERE id = %s AND acknowledged_at IS NULL
        """,
        (user["id"], alert_id)
    )

    if cursor.rowcount == 0:
        cursor.close()
        db.close()
        raise HTTPException(404, "Alert not found or already acknowledged")

    db.commit()
    cursor.close()
    db.close()

    return {"status": "acknowledged"}
