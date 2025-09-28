from pydantic import BaseModel


class LecturerDTO(BaseModel):
    name: str
    avg_rating: float
    ratings_count: int
    rank: int
