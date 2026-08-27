from sqlalchemy.orm import Session
from app.db.models.decision import Decision
from app.db.models.audit_log import AuditLog
from app.db.models.application import Application
import uuid


def persist_pipeline_result(
    db: Session,
    application_id: str,
    result: dict,
) -> None:


   
    decision = Decision(
        application_id=uuid.UUID(application_id),
        score=result.get("credit_score", 0.0),
        recommendation=result.get("final_decision", "Decline"),
        approved_amount=result.get("approved_amount_nrs", 0.0),
        top_factors=result.get("top_shap_factors", []),
        nepali_explanation=result.get("nepali_explanation", ""),
        conditions=result.get("conditions", []),
        action_items=result.get("action_items", []),
    )
    db.add(decision)

    agent_names = ["DVA", "IIA", "CSA", "CA", "OA"]
    audit_trail = result.get("audit_trail", [])

    agent_logs = {name: [] for name in agent_names}
    for line in audit_trail:
        for name in agent_names:
            if line.startswith(f"{name}:"):
                agent_logs[name].append(line)

    for agent_name in agent_names:
        log = AuditLog(
            application_id=uuid.UUID(application_id),
            agent_name=agent_name,
            input_snapshot={},
            output_snapshot={
                k: v for k, v in result.items()
                if not k.startswith("_")
            },
            notes="\n".join(agent_logs[agent_name]),
        )
        db.add(log)

    application = db.query(Application).filter(
        Application.id == uuid.UUID(application_id)
    ).first()
    if application:
        application.status = "completed"
        application.lalpurja_data = result.get("lalpurja_fields", {})

    db.commit()