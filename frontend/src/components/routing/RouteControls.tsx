import { MapPin, MapPinX, Plus, X, Truck, Car, Ambulance, Navigation } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { Badge } from '../../components/ui/Badge'
import { cn } from '../../lib/utils'
import type { Coordinates, VehicleType, RoutingMode } from '../../types'

interface RouteControlsProps {
  source?: Coordinates
  destination?: Coordinates
  waypoints: Coordinates[]
  blockedCoords: Coordinates[]
  vehicle: VehicleType
  mode: RoutingMode
  trafficMultiplier: number
  isLoading: boolean
  onSetSource: () => void
  onSetDestination: () => void
  onAddWaypoint: () => void
  onAddBlockage: () => void
  onClearWaypoints: () => void
  onClearBlockages: () => void
  onCalculateRoute: () => void
  onCompare: () => void
  onClearAll: () => void
  onVehicleChange: (vehicle: VehicleType) => void
  onModeChange: (mode: RoutingMode) => void
  onTrafficChange: (value: number) => void
  currentMode: 'source' | 'destination' | 'waypoint' | 'blockage' | null
}

const vehicleOptions = [
  { value: 'car', label: 'Car', icon: Car },
  { value: 'delivery_van', label: 'Delivery Van', icon: Truck },
  { value: 'ambulance', label: 'Ambulance', icon: Ambulance },
  { value: 'truck', label: 'Truck', icon: Truck },
] as const

const modeOptions = [
  { value: 'fastest', label: 'Fastest', description: 'Minimize travel time' },
  { value: 'safest', label: 'Safest', description: 'Minimize risk exposure' },
  { value: 'balanced', label: 'Balanced', description: 'Balance time and risk' },
  { value: 'emergency', label: 'Emergency', description: 'Priority routing with overrides' },
] as const

export function RouteControls({
  source,
  destination,
  waypoints,
  blockedCoords,
  vehicle,
  mode,
  trafficMultiplier,
  isLoading,
  onSetSource,
  onSetDestination,
  onAddWaypoint,
  onAddBlockage,
  onClearWaypoints,
  onClearBlockages,
  onCalculateRoute,
  onCompare,
  onClearAll,
  onVehicleChange,
  onModeChange,
  onTrafficChange,
  currentMode,
}: RouteControlsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  return (
    <div className="w-80 flex flex-col gap-4">
      <div className="flex items-center gap-2 px-2 py-1">
        <Navigation className="w-5 h-5 text-brand-primary" />
        <h2 className="text-heading-s font-bold text-neutral-900">Route Controls</h2>
      </div>

      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant={currentMode === 'source' ? 'primary' : 'outline'}
            size="sm"
            onClick={onSetSource}
            className="w-full"
            disabled={isLoading}
          >
            <MapPin className="w-4 h-4" />
            Source
          </Button>
          <Button
            variant={currentMode === 'destination' ? 'primary' : 'outline'}
            size="sm"
            onClick={onSetDestination}
            className="w-full"
            disabled={isLoading}
          >
            <MapPin className="w-4 h-4" />
            Destination
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Button
            variant={currentMode === 'waypoint' ? 'primary' : 'outline'}
            size="sm"
            onClick={onAddWaypoint}
            className="w-full"
            disabled={isLoading}
          >
            <Plus className="w-4 h-4" />
            Waypoint
          </Button>
          <Button
            variant={currentMode === 'blockage' ? 'danger' : 'outline'}
            size="sm"
            onClick={onAddBlockage}
            className="w-full"
            disabled={isLoading}
          >
            <MapPinX className="w-4 h-4" />
            Blockage
          </Button>
        </div>

        {(waypoints.length > 0 || blockedCoords.length > 0) && (
          <div className="grid grid-cols-2 gap-2">
            {waypoints.length > 0 && (
              <Button variant="ghost" size="sm" onClick={onClearWaypoints} className="w-full">
                <X className="w-4 h-4" />
                Clear Waypoints ({waypoints.length})
              </Button>
            )}
            {blockedCoords.length > 0 && (
              <Button variant="ghost" size="sm" onClick={onClearBlockages} className="w-full">
                <X className="w-4 h-4" />
                Clear Blockages ({blockedCoords.length})
              </Button>
            )}
          </div>
        )}

        <div className="pt-2 border-t border-neutral-200">
          <label className="block text-sm font-medium text-neutral-700 mb-2">Vehicle</label>
          <Select
            value={vehicle}
            onChange={(e) => onVehicleChange(e.target.value as VehicleType)}
            options={vehicleOptions.map((v) => ({ value: v.value, label: v.label }))}
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">Routing Mode</label>
          <Select
            value={mode}
            onChange={(e) => onModeChange(e.target.value as RoutingMode)}
            options={modeOptions.map((m) => ({ value: m.value, label: m.label }))}
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-neutral-500">
            {modeOptions.find((m) => m.value === mode)?.description}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            Traffic Congestion: {trafficMultiplier.toFixed(1)}×
          </label>
          <input
            type="range"
            min="1"
            max="5"
            step="0.5"
            value={trafficMultiplier}
            onChange={(e) => onTrafficChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-lg appearance-none cursor-pointer"
            disabled={isLoading}
          />
        </div>

        <Button
          onClick={onCalculateRoute}
          disabled={isLoading || !source || !destination}
          loading={isLoading}
          className="w-full"
          size="lg"
        >
          Calculate Route
        </Button>

        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={onCompare} disabled={isLoading || !source || !destination} className="w-full">
            Compare
          </Button>
          <Button variant="ghost" onClick={onClearAll} className="w-full">
            Clear All
          </Button>
        </div>
      </div>

      <Button variant="ghost" onClick={() => setShowAdvanced(!showAdvanced)} className="w-full justify-start text-sm">
        {showAdvanced ? 'Hide' : 'Show'} Advanced Options
      </Button>
    </div>
  )
}



