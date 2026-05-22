from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

# modelos pydantic, definem o json que a api devolve e valida tipos

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int


# uma paragem no mapa ou na lista
class StopOut(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: Optional[str] = None


# lista paginada de paragens com meta page limit total
class StopsPageOut(BaseModel):
    meta: PaginationMeta
    items: list[StopOut]


# linha de metro ou autocarro, cores para o frontend
class RouteOut(BaseModel):
    route_id: str
    route_short_name: str
    route_long_name: Optional[str] = None
    route_color: Optional[str] = None
    route_text_color: Optional[str] = None


class RoutesPageOut(BaseModel):
    meta: PaginationMeta
    items: list[RouteOut]


# proxima chegada com eta em minutos
class NextArrivalOut(BaseModel):
    route_id: str
    route_short_name: str
    trip_id: str
    destination: Optional[str] = None
    departure_time: str
    eta_minutes: int = Field(ge=0)


# horario de uma linha numa paragem, varias partidas no mesmo grupo
class StopScheduleGroupOut(BaseModel):
    route_id: str
    route_short_name: str
    direction_id: Optional[int] = None
    destination: Optional[str] = None
    departures: list[str]


# posicao estimada entre duas paragens, percentagem 0 a 100
class VehiclePositionOut(BaseModel):
    route_id: str
    trip_id: str
    last_stop_id: Optional[str] = None
    last_stop_name: Optional[str] = None
    next_stop_id: Optional[str] = None
    next_stop_name: Optional[str] = None
    progress_percent: float = Field(ge=0, le=100)


# preco entre duas zonas tarifarias
class FareOut(BaseModel):
    fare_id: str
    origin_zone: Optional[str] = None
    destination_zone: Optional[str] = None
    price: Decimal
    currency_type: str


class StopOnLineOut(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: Optional[str] = None
    stop_sequence: int


class LineStopsOut(BaseModel):
    route_id: str
    route_short_name: str
    direction_id: int
    destination: Optional[str] = None
    stops: list[StopOnLineOut]


class NearbyStopOut(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: Optional[str] = None
    distance_m: int = Field(ge=0)


class BoardDepartureOut(BaseModel):
    route_id: str
    route_short_name: str
    route_color: Optional[str] = None
    destination: Optional[str] = None
    departure_time: str
    eta_minutes: int = Field(ge=0)


class DepartureBoardOut(BaseModel):
    stop_id: str
    stop_name: str
    departures: list[BoardDepartureOut]


class JourneyLegOut(BaseModel):
    route_id: str
    route_short_name: str
    from_stop_id: str
    from_stop_name: str
    to_stop_id: str
    to_stop_name: str
    departure_time: str
    arrival_time: str
    stops_between: int


class JourneyOut(BaseModel):
    from_stop_id: str
    to_stop_id: str
    direct: bool
    legs: list[JourneyLegOut]