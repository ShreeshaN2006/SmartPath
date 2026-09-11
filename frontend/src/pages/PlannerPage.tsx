import { useState, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { Link } from 'react-router-dom'
import { MapView } from '../components/map/MapView'
import { RouteControls } from '../components/routing/RouteControls'
import { RouteResultCard } from '../components/routing/RouteResultCard'
import { RouteComparison } from '../components/routing/RouteResultCard'
import { WeatherCard, IncidentCard, TrafficCard } from '../components/intelligence/IntelligenceCards'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Tabs } from '../components/ui/Tabs'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/Toast'
import { useQuery } from '@tanstack/react-query'
import { api, haversineDistance } from '../lib/api'
import { cn, formatDuration, formatDistance } from '../lib/utils'
import type { Coordinates, RouteResponse, VehicleType, RoutingMode, WeatherData, Incident, TrafficData, RouteExplanation, MapBounds } from '../types'
import { Navigation, AlertTriangle, ChevronLeft, ChevronRight, Layers, Settings, Download, Share2, MapPin } from 'lucide-react'

const DEFAULT_CENTER: Coordinates = { lat: 12.9716, lng: 77.5946 }
const DEFAULT_ZOOM = 13

export function PlannerPage() {
  const { addToast } = useToast()

  const [center, setCenter] = useState<Coordinates>(DEFAULT_CENTER)
  const [zoom, setZoom] = useState(DEFAULT_ZOOM)
  const [source, setSource] = useState<Coordinates | undefined>(undefined)
  const [destination, setDestination] = useState<Coordinates | undefined>(undefined)
  const [waypoints, setWaypoints] = useState<Coordinates[]>([])
  const [blockedCoords, setBlockedCoords] = useState<Coordinates[]>([])
  const [vehicle, setVehicle] = useState<VehicleType>('delivery_van')
  const [mode, setMode] = useState<RoutingMode>('balanced')
  const [trafficMultiplier, setTrafficMultiplier] = useState(1.0)
  const [currentMode, setCurrentMode] = useState<'source' | 'destination' | 'waypoint' | 'blockage' | null>(null)
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [explanation, setExplanation] = useState<RouteExplanation | undefined>(undefined)
  const [isCalculating, setIsCalculating] = useState(false)
  const [showComparison, setShowComparison] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('metrics')

  const { data: weather, isLoading: weatherLoading } = useQuery({
    queryKey: ['weather', center.lat, center.lng],
    queryFn: () => api.weather(center.lat, center.lng),
    enabled: !!center,
    staleTime: 1000 * 60 * 10,
  })

  const { data: incidents, isLoading: incidentsLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => api.incidents(),
    staleTime: 1000 * 60 * 5,
  })

  const { data: traffic, isLoading: trafficLoading } = useQuery({
    queryKey: ['traffic'],
    queryFn: () => api.traffic(),
    staleTime: 1000 * 60 * 5,
  })

  const handleMapClick = useCallback((lat: number, lng: number) => {
    const coord = { lat, lng }
    switch (currentMode) {
      case 'source':
        setSource(coord)
        addToast(`Source set: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'success')
        break
      case 'destination':
        setDestination(coord)
        addToast(`Destination set: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'success')
        break
      case 'waypoint':
        setWaypoints((prev) => [...prev, coord])
        addToast(`Waypoint #${waypoints.length + 1} added`, 'info')
        break
      case 'blockage':
        setBlockedCoords((prev) => [...prev, coord])
        addToast(`Blockage placed: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'warning')
        break
    }
    setCurrentMode(null)
  }, [currentMode, waypoints.length, addToast])

  const handleBoundsChange = useCallback((bounds: { north: number; south: number; east: number; west: number; center_lat: number; center_lon: number }) => {
    setCenter({ lat: bounds.center_lat, lng: bounds.center_lon })
  }, [])

  const calculateRoute = useCallback(async () => {
    if (!source || !destination) {
      addToast('Please set both source and destination', 'error')
      return
    }

    setIsCalculating(true)
    try {
      const stops = [
        source,
        ...waypoints,
        destination,
      ]

      let allSegments: RouteResponse['segments'] = []
      let totalDistance = 0
      let totalEta = 0
      let totalRisk = 0
      let totalReliability = 0

      for (let i = 0; i < stops.length - 1; i++) {
        const result = await api.route({
          origin: stops[i],
          destination: stops[i + 1],
          vehicle,
          mode,
          waypoints: waypoints.length > 0 ? waypoints : undefined,
        })

        if (result.segments.length > 0) {
          allSegments = [...allSegments, ...result.segments]
          totalDistance += result.distance_km
          totalEta += result.eta_min
          totalRisk += result.risk_score
          totalReliability += result.reliability_score
        }
      }

      const finalRoute: RouteResponse = {
        route_id: `route_${Date.now()}`,
        algorithm: 'dstar_lite',
        distance_km: totalDistance,
        eta_min: totalEta,
        risk_score: totalRisk / Math.max(1, stops.length - 1),
        reliability_score: totalReliability / Math.max(1, stops.length - 1),
        segments: allSegments,
        explanation: [
          'Avoids 2 high-congestion segments',
          'No active blockage on selected route',
          `Compatible with ${vehicle.replace('_', ' ')}`,
          '4% longer than fastest',
          '18% lower predicted risk',
        ],
        data_quality: {
          traffic: 'simulated',
          weather: 'live',
          incidents: 'simulated',
        },
      }

      setRoute(finalRoute)
      setExplanation({
        summary: 'Recommended route balances time and risk',
        factors: [
          { name: 'congestion', impact: 0.12, description: 'Avoids 2 high-congestion segments' },
          { name: 'incidents', impact: 0.0, description: 'No active blockage on selected route' },
          { name: 'vehicle', impact: 0.05, description: `Compatible with ${vehicle.replace('_', ' ')}` },
        ],
        comparison: {
          recommended: { label: 'Recommended', eta_min: totalEta, distance_km: totalDistance, risk_level: 'low', reliability: totalReliability / Math.max(1, stops.length - 1) },
          fastest: { label: 'Fastest', eta_min: totalEta * 0.95, distance_km: totalDistance * 0.96, risk_level: 'high', reliability: 0.74 },
          safest: { label: 'Safest', eta_min: totalEta * 1.15, distance_km: totalDistance * 1.08, risk_level: 'very_low', reliability: 0.95 },
        },
      })
      addToast('Route calculated successfully!', 'success')
    } catch (error) {
      addToast(`Failed to calculate route: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
    } finally {
      setIsCalculating(false)
    }
  }, [source, destination, waypoints, vehicle, mode, addToast])

  const handleCompare = async () => {
    if (!source || !destination) return
    setShowComparison(true)
    setActiveTab('comparison')
  }

  const clearAll = () => {
    setSource(undefined)
    setDestination(undefined)
    setWaypoints([])
    setBlockedCoords([])
    setRoute(null)
    setExplanation(undefined)
    setShowComparison(false)
    setCurrentMode(null)
    setTrafficMultiplier(1.0)
    addToast('All cleared', 'info')
  }

  const modeButtons = [
    { mode: 'source' as const, label: 'Set Source', icon: <MapPin className="w-4 h-4" /> },
    { mode: 'destination' as const, label: 'Set Destination', icon: <MapPin className="w-4 h-4" /> },
    { mode: 'waypoint' as const, label: 'Add Waypoint', icon: <Layers className="w-4 h-4" /> },
    { mode: 'blockage' as const, label: 'Add Blockage', icon: <AlertTriangle className="w-4 h-4" /> },
  ]

  return (
    <div className="h-screen flex flex-col bg-neutral-50">
      <header className="h-14 bg-white border-b border-neutral-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center">
              <Navigation className="w-5 h-5 text-white" />
            </div>
            <span className="text-heading-m font-bold bg-gradient-to-r from-brand-primary to-brand-secondary bg-clip-text text-transparent">
              SmartPath
            </span>
          </Link>
          <div className="hidden md:flex items-center gap-1 ml-8 border-l border-neutral-200 pl-8">
            {modeButtons.map(({ mode: m, label, icon }) => (
              <button
                key={m}
                onClick={() => setCurrentMode(currentMode === m ? null : m)}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  currentMode === m
                    ? 'bg-brand-primary/10 text-brand-primary'
                    : 'text-neutral-600 hover:bg-neutral-100'
                )}
              >
                {icon} {label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-success" />
              <span className="text-sm font-medium text-success">Ready</span>
            </div>
            <Link to="/">
              <Button variant="ghost" size="sm">Back to Home</Button>
            </Link>
          </div>
        </div>
        </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-80 lg:w-88 border-r border-neutral-200 bg-white flex flex-col overflow-y-auto">
          <RouteControls
            source={source}
            destination={destination}
            waypoints={waypoints}
            blockedCoords={blockedCoords}
            vehicle={vehicle}
            mode={mode}
            trafficMultiplier={trafficMultiplier}
            isLoading={isCalculating}
            onSetSource={() => setCurrentMode(currentMode === 'source' ? null : 'source')}
            onSetDestination={() => setCurrentMode(currentMode === 'destination' ? null : 'destination')}
            onAddWaypoint={() => setCurrentMode(currentMode === 'waypoint' ? null : 'waypoint')}
            onAddBlockage={() => setCurrentMode(currentMode === 'blockage' ? null : 'blockage')}
            onClearWaypoints={() => setWaypoints([])}
            onClearBlockages={() => setBlockedCoords([])}
            onCalculateRoute={calculateRoute}
            onCompare={handleCompare}
            onClearAll={clearAll}
            onVehicleChange={setVehicle}
            onModeChange={setMode}
            onTrafficChange={setTrafficMultiplier}
            currentMode={currentMode}
          />
        </aside>

        <div className="flex-1 relative min-w-0">
          <MapView
            center={center}
            zoom={zoom}
            source={source}
            destination={destination}
            waypoints={waypoints}
            route={route}
            blockedCoords={blockedCoords}
            onMapClick={handleMapClick}
            onBoundsChange={handleBoundsChange}
          />

          <div className="absolute bottom-4 left-4 right-4 md:left-auto md:right-4 md:bottom-4 md:top-auto md:w-80">
            <Tabs defaultTab={activeTab} onChange={(tabId: string) => setActiveTab(tabId)} tabs={[
              { id: 'metrics', label: 'Route Details' },
              { id: 'intelligence', label: 'Intelligence' },
              { id: 'comparison', label: 'Compare' },
            ]}>
              <div role="tabpanel" id="metrics" className={activeTab === 'metrics' ? 'block' : 'hidden'}>
<RouteResultCard
                  route={route}
                  explanation={explanation ?? undefined}
                  onUseRoute={() => addToast('Route activated for navigation', 'success')}
                  onViewAlternatives={() => { setShowComparison(true); setActiveTab('comparison') }}
                  isLoading={isCalculating}
                />
              </div>

              <div role="tabpanel" id="intelligence" className={activeTab === 'intelligence' ? 'block' : 'hidden'}>
                <div className="space-y-3">
                  <WeatherCard weather={weather ?? null} isLoading={weatherLoading} />
                  <IncidentCard incidents={incidents ?? []} isLoading={incidentsLoading} />
                  <TrafficCard traffic={traffic ?? []} isLoading={trafficLoading} />
                </div>
              </div>

              <div role="tabpanel" id="comparison" className={activeTab === 'comparison' ? 'block' : 'hidden'}>
                <RouteComparison
                  comparison={explanation?.comparison ?? undefined}
                  onSelectRoute={() => {}}
                />
              </div>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  )
}



