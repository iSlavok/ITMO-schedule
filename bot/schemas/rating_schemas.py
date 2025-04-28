from pydantic import BaseModel


class LecturerDTO(BaseModel):
    rank: int
    name: str
    avg_rating: float
    reviews_count: int
