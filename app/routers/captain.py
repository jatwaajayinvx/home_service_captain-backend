from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.captain import Captain
from app.models.captain_service import CaptainService
from app.models.commission_transaction import CommissionTransaction
from app.models.service import Service
from app.models.user import User
from app.models.user_address import UserAddress

from app.schemas.captain import (
    CaptainEarningResponse,
    CaptainEarningsSummary,
    CaptainJobDetailResponse,
    CaptainJobHistoryResponse,
    CaptainJobResponse,
    CaptainLocationRequest,
    CaptainProfileUpdateRequest,
    CaptainRegisterRequest,
    CaptainResponse,
    CaptainStatusRequest,
    NearbyCaptainResponse,
)

from app.schemas.captain_service import (
    CaptainServiceRequest,
    CaptainServiceResponse,
)


router = APIRouter(
    prefix="/api/captains",
    tags=["Captains"],
)


# =========================================================
# CAPTAIN REGISTRATION
# =========================================================

@router.post(
    "/register",
    response_model=CaptainResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_captain(
    request: CaptainRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if existing_captain:
        raise HTTPException(
            status_code=400,
            detail="Captain profile already exists",
        )

    captain = Captain(
        user_id=current_user.id,
        experience_years=request.experience_years,
        kyc_status="PENDING",
        availability_status="OFFLINE",
    )

    current_user.role = "CAPTAIN"

    db.add(captain)
    db.commit()
    db.refresh(captain)

    return captain


# =========================================================
# MY CAPTAIN PROFILE
# =========================================================

@router.get(
    "/me",
    response_model=CaptainResponse,
)
def get_my_captain_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    return captain


# =========================================================
# CAPTAIN SERVICES
# =========================================================

@router.post(
    "/services",
    response_model=CaptainServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_captain_service(
    request: CaptainServiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    service = (
        db.query(Service)
        .filter(
            Service.id == request.service_id,
            Service.is_active == True,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    existing = (
        db.query(CaptainService)
        .filter(
            CaptainService.captain_id == captain.id,
            CaptainService.service_id == request.service_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Service already added",
        )

    captain_service = CaptainService(
        captain_id=captain.id,
        service_id=request.service_id,
        experience_years=request.experience_years,
    )

    db.add(captain_service)
    db.commit()
    db.refresh(captain_service)

    return captain_service


@router.get(
    "/services",
    response_model=list[CaptainServiceResponse],
)
def get_my_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    return (
        db.query(CaptainService)
        .filter(
            CaptainService.captain_id == captain.id
        )
        .all()
    )


# =========================================================
# CAPTAIN ONLINE / OFFLINE STATUS
# =========================================================

@router.put(
    "/status",
    response_model=CaptainResponse,
)
def update_captain_status(
    request: CaptainStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.availability_status not in ["ONLINE", "OFFLINE"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be ONLINE or OFFLINE",
        )

    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    # Captain can go online only after KYC verification
    if (
        request.availability_status == "ONLINE"
        and captain.kyc_status != "VERIFIED"
    ):
        raise HTTPException(
            status_code=403,
            detail="KYC must be verified before going online",
        )

    # Do not allow BUSY captain to manually go offline
    if (
        request.availability_status == "OFFLINE"
        and captain.availability_status == "BUSY"
    ):
        raise HTTPException(
            status_code=400,
            detail="Complete the active job before going offline",
        )

    captain.availability_status = request.availability_status

    db.commit()
    db.refresh(captain)

    return captain


# =========================================================
# CAPTAIN LOCATION
# =========================================================

@router.put(
    "/location",
    response_model=CaptainResponse,
)
def update_captain_location(
    request: CaptainLocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not -90 <= request.latitude <= 90:
        raise HTTPException(
            status_code=400,
            detail="Invalid latitude",
        )

    if not -180 <= request.longitude <= 180:
        raise HTTPException(
            status_code=400,
            detail="Invalid longitude",
        )

    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    captain.current_latitude = request.latitude
    captain.current_longitude = request.longitude

    db.commit()
    db.refresh(captain)

    return captain


# =========================================================
# NEARBY CAPTAINS
# =========================================================

@router.get(
    "/nearby/{booking_id}",
    response_model=list[NearbyCaptainResponse],
)
def get_nearby_captains(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.booking import Booking

    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.customer_id == current_user.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    address = (
        db.query(UserAddress)
        .filter(UserAddress.id == booking.address_id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=404,
            detail="Booking address not found",
        )

    if (
        address.latitude is None
        or address.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Booking address does not have location coordinates",
        )

    query = text("""
        SELECT
            c.id AS captain_id,
            c.user_id AS user_id,
            u.name AS name,
            c.rating AS rating,
            c.experience_years AS experience_years,

            (
                6371 * ACOS(
                    COS(RADIANS(:lat))
                    * COS(RADIANS(c.current_latitude))
                    * COS(
                        RADIANS(c.current_longitude)
                        - RADIANS(:lon)
                    )
                    + SIN(RADIANS(:lat))
                    * SIN(RADIANS(c.current_latitude))
                )
            ) AS distance_km

        FROM captains c

        JOIN users u
            ON u.id = c.user_id

        JOIN captain_services cs
            ON cs.captain_id = c.id

        WHERE
            cs.service_id = :service_id
            AND c.availability_status = 'ONLINE'
            AND c.kyc_status = 'VERIFIED'
            AND c.current_latitude IS NOT NULL
            AND c.current_longitude IS NOT NULL
            AND u.is_active = 1

        HAVING distance_km <= 20

        ORDER BY distance_km ASC

        LIMIT 10
    """)

    result = db.execute(
        query,
        {
            "lat": float(address.latitude),
            "lon": float(address.longitude),
            "service_id": booking.service_id,
        },
    )

    return [
        {
            "captain_id": row.captain_id,
            "user_id": row.user_id,
            "name": row.name,
            "rating": float(row.rating or 0),
            "experience_years": row.experience_years,
            "distance_km": round(
                float(row.distance_km),
                2,
            ),
        }
        for row in result
    ]


# =========================================================
# EARNINGS
# =========================================================

@router.get(
    "/earnings",
    response_model=list[CaptainEarningResponse],
)
def get_captain_earnings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    return (
        db.query(CommissionTransaction)
        .filter(
            CommissionTransaction.captain_id == captain.id
        )
        .order_by(
            CommissionTransaction.id.desc()
        )
        .all()
    )


@router.get(
    "/earnings/summary",
    response_model=CaptainEarningsSummary,
)
def get_captain_earnings_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    result = (
        db.query(
            func.count(
                CommissionTransaction.id
            ).label("total_bookings"),

            func.coalesce(
                func.sum(
                    CommissionTransaction.booking_amount
                ),
                0,
            ).label("total_booking_amount"),

            func.coalesce(
                func.sum(
                    CommissionTransaction.commission_amount
                ),
                0,
            ).label("total_commission"),

            func.coalesce(
                func.sum(
                    CommissionTransaction.captain_amount
                ),
                0,
            ).label("total_earnings"),
        )
        .filter(
            CommissionTransaction.captain_id == captain.id
        )
        .first()
    )

    return {
        "total_bookings": result.total_bookings,
        "total_booking_amount": float(
            result.total_booking_amount
        ),
        "total_commission": float(
            result.total_commission
        ),
        "total_earnings": float(
            result.total_earnings
        ),
    }


# =========================================================
# AVAILABLE JOBS
# =========================================================

@router.get(
    "/jobs",
    response_model=list[CaptainJobResponse],
)
def get_captain_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    if captain.kyc_status != "VERIFIED":
        raise HTTPException(
            status_code=403,
            detail="Captain KYC is not verified",
        )

    if captain.availability_status != "ONLINE":
        return []

    query = text("""
        SELECT
            b.id AS booking_id,
            b.booking_number AS booking_number,
            s.name AS service_name,
            u.name AS customer_name,
            b.problem_description AS problem_description,
            a.address_line AS address_line,
            a.city AS city,
            b.scheduled_date AS scheduled_date,
            b.scheduled_time AS scheduled_time,
            b.estimated_amount AS estimated_amount,

            (
                6371 * ACOS(
                    COS(RADIANS(a.latitude))
                    * COS(RADIANS(c.current_latitude))
                    * COS(
                        RADIANS(c.current_longitude)
                        - RADIANS(a.longitude)
                    )
                    + SIN(RADIANS(a.latitude))
                    * SIN(RADIANS(c.current_latitude))
                )
            ) AS distance_km,

            b.status AS status

        FROM bookings b

        JOIN users u
            ON u.id = b.customer_id

        JOIN services s
            ON s.id = b.service_id

        JOIN user_addresses a
            ON a.id = b.address_id

        JOIN captain_services cs
            ON cs.service_id = b.service_id
            AND cs.captain_id = :captain_id

        JOIN captains c
            ON c.id = :captain_id

        WHERE
            b.status = 'SEARCHING'
            AND b.captain_id IS NULL
            AND s.is_active = 1
            AND u.is_active = 1
            AND a.latitude IS NOT NULL
            AND a.longitude IS NOT NULL
            AND c.current_latitude IS NOT NULL
            AND c.current_longitude IS NOT NULL

        HAVING distance_km <= 20

        ORDER BY distance_km ASC

        LIMIT 20
    """)

    result = db.execute(
        query,
        {
            "captain_id": captain.id,
        },
    )

    jobs = []

    for row in result:
        scheduled_time = row.scheduled_time

        if (
            scheduled_time is not None
            and isinstance(
                scheduled_time,
                timedelta,
            )
        ):
            scheduled_time = (
                datetime.min + scheduled_time
            ).time()

        jobs.append({
            "booking_id": row.booking_id,
            "booking_number": row.booking_number,
            "service_name": row.service_name,
            "customer_name": row.customer_name,
            "problem_description": row.problem_description,
            "address_line": row.address_line,
            "city": row.city,
            "scheduled_date": row.scheduled_date,
            "scheduled_time": scheduled_time,
            "estimated_amount": float(
                row.estimated_amount or 0
            ),
            "distance_km": round(
                float(row.distance_km),
                2,
            ),
            "status": row.status,
        })

    return jobs


# =========================================================
# JOB HISTORY
# IMPORTANT: Must come BEFORE /jobs/{booking_id}
# =========================================================

@router.get(
    "/jobs/history",
    response_model=list[CaptainJobHistoryResponse],
)
def get_captain_job_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    query = text("""
        SELECT
            b.id AS booking_id,
            b.booking_number AS booking_number,
            s.name AS service_name,
            u.name AS customer_name,
            b.problem_description AS problem_description,
            a.address_line AS address_line,
            a.city AS city,
            b.scheduled_date AS scheduled_date,
            b.scheduled_time AS scheduled_time,
            b.estimated_amount AS estimated_amount,
            b.final_amount AS final_amount,
            b.status AS status,
            b.updated_at AS completed_at

        FROM bookings b

        JOIN users u
            ON u.id = b.customer_id

        JOIN services s
            ON s.id = b.service_id

        JOIN user_addresses a
            ON a.id = b.address_id

        WHERE
            b.captain_id = :captain_id
            AND b.status = 'COMPLETED'

        ORDER BY
            b.updated_at DESC

        LIMIT 50
    """)

    result = db.execute(
        query,
        {
            "captain_id": captain.id,
        },
    )

    jobs = []

    for row in result:
        scheduled_time = row.scheduled_time

        if (
            scheduled_time is not None
            and isinstance(
                scheduled_time,
                timedelta,
            )
        ):
            scheduled_time = (
                datetime.min + scheduled_time
            ).time()

        jobs.append({
            "booking_id": row.booking_id,
            "booking_number": row.booking_number,
            "service_name": row.service_name,
            "customer_name": row.customer_name,
            "problem_description": row.problem_description,
            "address_line": row.address_line,
            "city": row.city,
            "scheduled_date": row.scheduled_date,
            "scheduled_time": scheduled_time,
            "estimated_amount": float(
                row.estimated_amount or 0
            ),
            "final_amount": (
                float(row.final_amount)
                if row.final_amount is not None
                else None
            ),
            "status": row.status,
            "completed_at": row.completed_at,
        })

    return jobs


# =========================================================
# JOB DETAIL
# IMPORTANT: Dynamic route comes AFTER /jobs/history
# =========================================================

@router.get(
    "/jobs/{booking_id}",
    response_model=CaptainJobDetailResponse,
)
def get_captain_job_detail(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    if captain.kyc_status != "VERIFIED":
        raise HTTPException(
            status_code=403,
            detail="Captain KYC is not verified",
        )

    if captain.availability_status != "ONLINE":
        raise HTTPException(
            status_code=400,
            detail="Captain is offline",
        )

    query = text("""
        SELECT
            b.id AS booking_id,
            b.booking_number AS booking_number,
            s.name AS service_name,
            u.name AS customer_name,
            u.mobile AS customer_mobile,
            b.problem_description AS problem_description,
            a.address_line AS address_line,
            a.landmark AS landmark,
            a.city AS city,
            a.state AS state,
            a.pincode AS pincode,
            b.scheduled_date AS scheduled_date,
            b.scheduled_time AS scheduled_time,
            b.estimated_amount AS estimated_amount,

            (
                6371 * ACOS(
                    COS(RADIANS(a.latitude))
                    * COS(RADIANS(c.current_latitude))
                    * COS(
                        RADIANS(c.current_longitude)
                        - RADIANS(a.longitude)
                    )
                    + SIN(RADIANS(a.latitude))
                    * SIN(RADIANS(c.current_latitude))
                )
            ) AS distance_km,

            b.status AS status

        FROM bookings b

        JOIN users u
            ON u.id = b.customer_id

        JOIN services s
            ON s.id = b.service_id

        JOIN user_addresses a
            ON a.id = b.address_id

        JOIN captain_services cs
            ON cs.service_id = b.service_id
            AND cs.captain_id = :captain_id

        JOIN captains c
            ON c.id = :captain_id

        WHERE
            b.id = :booking_id
            AND b.status = 'SEARCHING'
            AND b.captain_id IS NULL
            AND s.is_active = 1
            AND u.is_active = 1
            AND a.latitude IS NOT NULL
            AND a.longitude IS NOT NULL
            AND c.current_latitude IS NOT NULL
            AND c.current_longitude IS NOT NULL

        HAVING distance_km <= 20

        LIMIT 1
    """)

    row = db.execute(
        query,
        {
            "booking_id": booking_id,
            "captain_id": captain.id,
        },
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Job not available for this captain",
        )

    scheduled_time = row.scheduled_time

    if (
        scheduled_time is not None
        and isinstance(
            scheduled_time,
            timedelta,
        )
    ):
        scheduled_time = (
            datetime.min + scheduled_time
        ).time()

    return {
        "booking_id": row.booking_id,
        "booking_number": row.booking_number,
        "service_name": row.service_name,
        "customer_name": row.customer_name,
        "customer_mobile": row.customer_mobile,
        "problem_description": row.problem_description,
        "address_line": row.address_line,
        "landmark": row.landmark,
        "city": row.city,
        "state": row.state,
        "pincode": row.pincode,
        "scheduled_date": row.scheduled_date,
        "scheduled_time": scheduled_time,
        "estimated_amount": float(
            row.estimated_amount or 0
        ),
        "distance_km": round(
            float(row.distance_km),
            2,
        ),
        "status": row.status,
    }


# =========================================================
# ACTIVE JOB DETAIL
# =========================================================

@router.get(
    "/active-jobs/{booking_id}",
    response_model=CaptainJobDetailResponse,
)
def get_active_job_detail(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    query = text("""
        SELECT
            b.id AS booking_id,
            b.booking_number AS booking_number,
            s.name AS service_name,
            u.name AS customer_name,
            u.mobile AS customer_mobile,
            b.problem_description AS problem_description,
            a.address_line AS address_line,
            a.landmark AS landmark,
            a.city AS city,
            a.state AS state,
            a.pincode AS pincode,
            b.scheduled_date AS scheduled_date,
            b.scheduled_time AS scheduled_time,
            b.estimated_amount AS estimated_amount,

            (
                6371 * ACOS(
                    COS(RADIANS(a.latitude))
                    * COS(RADIANS(c.current_latitude))
                    * COS(
                        RADIANS(c.current_longitude)
                        - RADIANS(a.longitude)
                    )
                    + SIN(RADIANS(a.latitude))
                    * SIN(RADIANS(c.current_latitude))
                )
            ) AS distance_km,

            b.status AS status

        FROM bookings b

        JOIN users u
            ON u.id = b.customer_id

        JOIN services s
            ON s.id = b.service_id

        JOIN user_addresses a
            ON a.id = b.address_id

        JOIN captains c
            ON c.id = b.captain_id

        WHERE
            b.id = :booking_id
            AND b.captain_id = :captain_id
            AND b.status IN (
                'ACCEPTED',
                'ON_THE_WAY',
                'ARRIVED',
                'STARTED'
            )

        LIMIT 1
    """)

    row = db.execute(
        query,
        {
            "booking_id": booking_id,
            "captain_id": captain.id,
        },
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Active job not found",
        )

    scheduled_time = row.scheduled_time

    if (
        scheduled_time is not None
        and isinstance(
            scheduled_time,
            timedelta,
        )
    ):
        scheduled_time = (
            datetime.min + scheduled_time
        ).time()

    return {
        "booking_id": row.booking_id,
        "booking_number": row.booking_number,
        "service_name": row.service_name,
        "customer_name": row.customer_name,
        "customer_mobile": row.customer_mobile,
        "problem_description": row.problem_description,
        "address_line": row.address_line,
        "landmark": row.landmark,
        "city": row.city,
        "state": row.state,
        "pincode": row.pincode,
        "scheduled_date": row.scheduled_date,
        "scheduled_time": scheduled_time,
        "estimated_amount": float(
            row.estimated_amount or 0
        ),
        "distance_km": round(
            float(row.distance_km),
            2,
        ),
        "status": row.status,
    }
    
@router.put("/me")
def update_my_captain_profile(
    request: CaptainProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    # Name
    if request.name is not None:
        name = request.name.strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty",
            )

        if len(name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Name must be at least 2 characters",
            )

        current_user.name = name

    # Email
    if request.email is not None:
        email = request.email.strip()

        current_user.email = email or None

    # Experience
    if request.experience_years is not None:
        if request.experience_years < 0:
            raise HTTPException(
                status_code=400,
                detail="Experience cannot be negative",
            )

        if request.experience_years > 50:
            raise HTTPException(
                status_code=400,
                detail="Experience cannot be more than 50 years",
            )

        captain.experience_years = request.experience_years

    db.commit()

    db.refresh(current_user)
    db.refresh(captain)

    return {
        "message": "Profile updated successfully",
        "name": current_user.name,
        "mobile": current_user.mobile,
        "email": current_user.email,
        "experience_years": captain.experience_years,
    }
    
@router.put("/me")
def update_my_captain_profile(
    request: CaptainProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain profile not found",
        )

    if request.name is not None:
        name = request.name.strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty",
            )

        if len(name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Name must be at least 2 characters",
            )

        current_user.name = name

    if request.email is not None:
        email = request.email.strip()
        current_user.email = email or None

    if request.experience_years is not None:
        if request.experience_years < 0:
            raise HTTPException(
                status_code=400,
                detail="Experience cannot be negative",
            )

        if request.experience_years > 50:
            raise HTTPException(
                status_code=400,
                detail="Experience cannot be more than 50 years",
            )

        captain.experience_years = request.experience_years

    db.commit()

    db.refresh(current_user)
    db.refresh(captain)

    return {
        "message": "Profile updated successfully",
        "name": current_user.name,
        "mobile": current_user.mobile,
        "email": current_user.email,
        "experience_years": captain.experience_years,
    }