
from models.schemas import RoutingMode
from pydantic import BaseModel


class RoutingWeights(BaseModel):
    time: float = 1.0
    congestion: float = 1.0
    risk: float = 1.0
    vehicle: float = 1.0
    resilience: float = 0.5


DEFAULT_WEIGHTS: dict[RoutingMode, RoutingWeights] = {
    RoutingMode.FASTEST: RoutingWeights(time=2.0, congestion=0.5, risk=0.2, vehicle=0.1, resilience=0.1),
    RoutingMode.SAFEST: RoutingWeights(time=0.5, congestion=0.5, risk=2.0, vehicle=0.5, resilience=0.5),
    RoutingMode.BALANCED: RoutingWeights(time=1.0, congestion=1.0, risk=1.0, vehicle=1.0, resilience=0.5),
    RoutingMode.EMERGENCY: RoutingWeights(time=1.5, congestion=0.3, risk=0.5, vehicle=2.0, resilience=0.3),
}


def get_weights(mode: RoutingMode) -> RoutingWeights:
    return DEFAULT_WEIGHTS.get(mode, DEFAULT_WEIGHTS[RoutingMode.BALANCED])
