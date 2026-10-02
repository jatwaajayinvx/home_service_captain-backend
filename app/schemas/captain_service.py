from pydantic import BaseModel


class CaptainServiceRequest(BaseModel):
    service_id: int
    experience_years: int = 0


class CaptainServiceResponse(BaseModel):
    id: int
    captain_id: int
    service_id: int
    experience_years: int

    class Config:
        from_attributes = True