export interface Coordinates {
  lat: number
  lng: number
}

export interface RouteRequest {
  origin: Coordinates
  destination: Coordinates
  vehicle: VehicleType
  mode: RoutingMode
  depart_at?: string
  waypoints?: Coordinates[]
}

export interface RouteResponse {
  route_id: string
  algorithm: string
  distance_km: number
  eta_min: number
  risk_score: number
  reliability_score: number
  segments: RouteSegment[]
  explanation: string[]
  data_quality: DataQuality
}

export interface RouteSegment {
  edge_id: string
  coords: Coordinates[]
  distance_m: number
  travel_time_min: number
  congestion: number
  risk: number
  road_class: string
}

export interface DataQuality {
  traffic: 'live' | 'simulated' | 'historical' | 'predicted'
  weather: 'live' | 'simulated' | 'historical'
  incidents: 'live' | 'simulated' | 'historical'
}

export type VehicleType = 'car' | 'delivery_van' | 'ambulance' | 'truck'

export type RoutingMode = 'fastest' | 'safest' | 'balanced' | 'emergency'

export interface VehicleConstraints {
  max_height_m?: number
  max_weight_kg?: number
  max_width_m?: number
  allowed_road_classes: string[]
  forbidden_road_classes: string[]
  emergency_override: boolean
}

export interface WeatherData {
  temperature_c: number
  precipitation_mm: number
  wind_speed_kmh: number
  weather_code: number
}

export interface Incident {
  id: string
  edge_id: string
  type: 'road_blockage' | 'accident' | 'construction' | 'flooding' | 'other'
  severity: number
  active: boolean
  started_at: string
  expires_at?: string
}

export interface TrafficData {
  edge_id: string
  current_speed_kmh: number
  predicted_speed_kmh: number
  congestion: number
  confidence: number
}

export interface RiskFactors {
  congestion: number
  weather: number
  incident_severity: number
  road_class: number
  vehicle_compatibility: number
  historical_reliability: number
}

export interface RouteExplanation {
  summary: string
  factors: ExplanationFactor[]
  comparison?: RouteComparison
}

export interface ExplanationFactor {
  name: string
  impact: number
  description: string
}

export interface RouteComparison {
  recommended: RouteSummary
  fastest: RouteSummary
  safest: RouteSummary
}

export interface RouteSummary {
  label: string
  eta_min: number
  distance_km: number
  risk_level: 'very_low' | 'low' | 'medium' | 'high' | 'very_high'
  reliability: number
}

export interface MapBounds {
  north: number
  south: number
  east: number
  west: number
  center_lat: number
  center_lon: number
}

export interface AlgorithmMetrics {
  nodes_expanded: number
  execution_time_ms: number
  path_cost: number
  success: boolean
}