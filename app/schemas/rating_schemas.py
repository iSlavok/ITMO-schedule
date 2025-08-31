from pydantic import BaseModel


class LecturerDTO(BaseModel):
    name: str
    avg_rating: float
    reviews_count: int
    rank: int
