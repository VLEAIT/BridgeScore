from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.application import Application
from app.models.decision import Decision
from app.schemas.application import ApplicationCreate,ApplicationOut,ApplicationUpdate
from app.schemas.common import APIResponse,ApplicationStatus
import uuid
from typing import Annotated

DatabaseSession=Annotated[Session,Depends(get_db)]
router=APIRouter(prefix="/applications",tags=["Applications"])

@router.post("/",response_model=APIResponse[ApplicationOut],status_code=status.HTTP_201_CREATED,summary="Submit a new loan application",description="Accepts farmer data,validates consent,writes to DB.Triggers agent pipline")
def create_application(payload:ApplicationCreate,db:DatabaseSession)->APIResponse[ApplicationOut]:
    existing=db.query(Application).filter(
        Application.citizenship_number == payload.citizenship_number,
        Application.status.in_([ApplicationStatus.pending.value, ApplicationStatus.processing.value]),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active application already exits for citizenship number {payload.citizenship_number}"
        )
    application=Application(**payload.model_dump(mode="json"))   
    db.add(application)
    db.commit()
    db.refresh(application)

    return APIResponse(success=True,data=ApplicationOut.model_validate(application))

@router.get("/",response_model=APIResponse[list[ApplicationOut]],status_code=status.HTTP_200_OK,summary="list all applications",description="Returns paginated list of all applications ")
def list_applications(db:DatabaseSession,skip:int=0,limit:int=20)->APIResponse[list[ApplicationOut]]:
    applications=db.query(Application).order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    return APIResponse(success=True,data=[ApplicationOut.model_validate(a) for a in applications])

@router.get("/{application_id}",response_model=APIResponse[ApplicationOut],status_code=status.HTTP_200_OK,summary="Get application by ID ",description="Returns application with nested decision if agents")
def get_application(application_id:uuid.UUID,db:DatabaseSession)->APIResponse[ApplicationOut]:
    application=db.query(Application).filter(Application.id==application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )

    return APIResponse(
        success=True,
        data=ApplicationOut.model_validate(application)
        )

@router.patch("/{application_id}/status",response_model=APIResponse[ApplicationOut],status_code=status.HTTP_200_OK,summary="Update application status",description="Internal endpoint")
def update_status(application_id:uuid.UUID,new_status:ApplicationStatus,db:DatabaseSession)->APIResponse[ApplicationOut]:
    application=db.query(Application).filter(Application.id==application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicatoin {application_id} not found"
        )
    application.status=new_status.value
    db.commit()
    db.refresh(application)
    return APIResponse(
        success=True,
        data=ApplicationOut.model_validate(application))    
        
@router.post("/{application_id}/reapply",response_model=APIResponse[ApplicationOut],status_code=status.HTTP_201_CREATED)
def reapply(application_id:uuid.UUID,payload:ApplicationUpdate,db:DatabaseSession)->APIResponse[ApplicationOut]:
    original=db.query(Application).filter(Application.id==application_id).first()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Application not found")
    if original.status != ApplicationStatus.failed.value:
        raise HTTPException(
            status_code=400,
            detail="Only declined application can be reapplied"
        )
    original_data={
        "farmer_name":original.farmer_name,
        "district":original.district,
        "citizenship_number":original.citizenship_number,
        "phone_number":original.phone_number,
        "land_area_hectares":original.land_area_hectares,
        "land_type":original.land_type,
        "land_grade":original.land_grade,
        "coop_income_monthly":original.coop_income_monthly,
        "remittance_monthly":original.remittance_monthly,
        "remittance_channel":original.remittance_channel,
        "requested_amount":original.requested_amount,
        "consent_given":original.consent_given,
    }    

    updated_fields=payload.model_dump(exclude_unset=True,mode="json")
    original_data.update(updated_fields)

    new_application=Application(**original_data)
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return APIResponse(
        success=True,
        data=ApplicationOut.model_validate(new_application)
    )


@router.patch("/{application_id}/update",response_model=APIResponse[ApplicationOut],status_code=status.HTTP_200_OK,summary="Update application status",description="Internal endpoint -called by agent pipeline")
def update_application(application_id:uuid.UUID,payload:ApplicationUpdate,db:DatabaseSession,)->APIResponse[ApplicationOut]:
     application=db.query(Application).filter(Application.id==application_id).first()
     if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Application not found")
     updated_fields=payload.model_dump(exclude_unset=True,mode="json")
     for field,value in updated_fields.items():
        setattr(application,field,value)
     application.status=ApplicationStatus.pending.value
     db.commit()
     db.refresh(application)

     return APIResponse(
        success=True,
        data=ApplicationOut.model_validate(application)
     )     










  

        





        

