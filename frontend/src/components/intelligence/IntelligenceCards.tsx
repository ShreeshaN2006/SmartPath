import { AlertTriangle, CloudRain, Wind, Thermometer, Activity, Truck, Car, Ambulance } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { cn } from '../../lib/utils'
import type { WeatherData, Incident, TrafficData } from '../../types'

interface WeatherCardProps {
  weather: WeatherData | null
  isLoading?: boolean
}

const weatherCodeMap: Record<number, { label: string; icon: React.ReactNode }> = {
  0: { label: 'Clear sky', icon: <Activity className="w-5 h-5 text-yellow-500" /> },
  1: { label: 'Mainly clear', icon: <Activity className="w-5 h-5 text-yellow-500" /> },
  2: { label: 'Partly cloudy', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  3: { label: 'Overcast', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  45: { label: 'Fog', icon: <CloudRain className="w-5 h-5 text-neutral-500" /> },
  48: { label: 'Depositing rime fog', icon: <CloudRain className="w-5 h-5 text-neutral-500" /> },
  51: { label: 'Light drizzle', icon: <CloudRain className="w-5 h-5 text-blue-400" /> },
  53: { label: 'Moderate drizzle', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  55: { label: 'Dense drizzle', icon: <CloudRain className="w-5 h-5 text-blue-600" /> },
  61: { label: 'Slight rain', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  63: { label: 'Moderate rain', icon: <CloudRain className="w-5 h-5 text-blue-600" /> },
  65: { label: 'Heavy rain', icon: <CloudRain className="w-5 h-5 text-blue-700" /> },
  71: { label: 'Slight snow', icon: <CloudRain className="w-5 h-5 text-blue-300" /> },
  73: { label: 'Moderate snow', icon: <CloudRain className="w-5 h-5 text-blue-400" /> },
  75: { label: 'Heavy snow', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  80: { label: 'Slight rain showers', icon: <CloudRain className="w-5 h-5 text-blue-400" /> },
  81: { label: 'Moderate rain showers', icon: <CloudRain className="w-5 h-5 text-blue-500" /> },
  82: { label: 'Violent rain showers', icon: <CloudRain className="w-5 h-5 text-blue-700" /> },
  95: { label: 'Thunderstorm', icon: <Activity className="w-5 h-5 text-yellow-600" /> },
  96: { label: 'Thunderstorm with hail', icon: <Activity className="w-5 h-5 text-yellow-700" /> },
  99: { label: 'Thunderstorm with heavy hail', icon: <Activity className="w-5 h-5 text-yellow-800" /> },
}

export function WeatherCard({ weather, isLoading }: WeatherCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary" />
        </CardContent>
      </Card>
    )
  }

  if (!weather) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-neutral-500">
          Weather data unavailable
        </CardContent>
      </Card>
    )
  }

  const condition = weatherCodeMap[weather.weather_code] || { label: 'Unknown', icon: <Activity className="w-5 h-5" /> }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-heading-s flex items-center gap-2">
          <CloudRain className="w-5 h-5 text-brand-primary" />
          Current Weather
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="text-4xl">{condition.icon}</div>
          <div>
            <p className="text-heading-m font-bold text-neutral-900">{condition.label}</p>
            <p className="text-sm text-neutral-500">Code: {weather.weather_code}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
              <Thermometer className="w-4 h-4" />
              Temperature
            </div>
            <p className="text-heading-s font-bold text-brand-primary">{weather.temperature_c.toFixed(1)}°C</p>
          </div>
          <div className="p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
              <CloudRain className="w-4 h-4" />
              Precipitation
            </div>
            <p className="text-heading-s font-bold text-info">{weather.precipitation_mm.toFixed(1)} mm</p>
          </div>
          <div className="p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
              <Wind className="w-4 h-4" />
              Wind Speed
            </div>
            <p className="text-heading-s font-bold text-brand-secondary">{weather.wind_speed_kmh.toFixed(1)} km/h</p>
          </div>
          <div className="p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
              <AlertTriangle className="w-4 h-4" />
              Risk Impact
            </div>
            <p className="text-heading-s font-bold text-warning">Moderate</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface IncidentCardProps {
  incidents: Incident[]
  isLoading?: boolean
}

export function IncidentCard({ incidents, isLoading }: IncidentCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary" />
        </CardContent>
      </Card>
    )
  }

  if (incidents.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-neutral-500">
          No active incidents
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-heading-s flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-warning" />
          Active Incidents ({incidents.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-60 overflow-y-auto">
          {incidents.map((incident) => (
            <div key={incident.id} className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className="font-medium text-neutral-900 capitalize">{incident.type.replace('_', ' ')}</p>
                  <p className="text-sm text-neutral-500">Edge: {incident.edge_id}</p>
                </div>
                <Badge variant={incident.severity > 0.7 ? 'danger' : incident.severity > 0.4 ? 'warning' : 'info'} size="sm">
                  Severity: {(incident.severity * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="mt-2 flex items-center gap-4 text-xs text-neutral-500">
                <span>Started: {new Date(incident.started_at).toLocaleTimeString()}</span>
                {incident.expires_at && <span>Expires: {new Date(incident.expires_at).toLocaleTimeString()}</span>}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface TrafficCardProps {
  traffic: TrafficData[]
  isLoading?: boolean
}

export function TrafficCard({ traffic, isLoading }: TrafficCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary" />
        </CardContent>
      </Card>
    )
  }

  if (traffic.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-neutral-500">
          No traffic data available
        </CardContent>
      </Card>
    )
  }

  const avgCongestion = traffic.reduce((sum, t) => sum + t.congestion, 0) / traffic.length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-heading-s flex items-center gap-2">
          <Activity className="w-5 h-5 text-brand-primary" />
          Traffic Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="font-medium text-neutral-700">Average Congestion</span>
            <span className="font-mono text-brand-primary">{(avgCongestion * 100).toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
            <div
              className={cn('h-full transition-all duration-500', avgCongestion > 0.7 ? 'bg-danger' : avgCongestion > 0.4 ? 'bg-warning' : 'bg-success')}
              style={{ width: `${avgCongestion * 100}%` }}
            />
          </div>
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {traffic.slice(0, 10).map((t) => (
            <div key={t.edge_id} className="flex items-center justify-between text-sm p-2 bg-neutral-50 rounded">
              <span className="font-mono text-neutral-600">{t.edge_id.slice(0, 20)}...</span>
              <div className="flex items-center gap-2">
                <span className={cn('font-mono', t.congestion > 0.7 ? 'text-danger' : t.congestion > 0.4 ? 'text-warning' : 'text-success')}>
                  {(t.congestion * 100).toFixed(0)}%
                </span>
                <span className="text-neutral-500">{t.current_speed_kmh.toFixed(0)} km/h</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}



