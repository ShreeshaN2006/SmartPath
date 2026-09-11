import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { cn } from '../../lib/utils'
import type { Coordinates, RouteResponse, RouteSegment } from '../../types'

// Fix Leaflet default marker icons
const DefaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

L.Marker.prototype.options.icon = DefaultIcon

interface RouteLayerProps {
  coords: Coordinates[]
  color: string
  weight?: number
  opacity?: number
  dashArray?: string
  layerId?: string
}

function RouteLayer({ coords, color, weight = 5, opacity = 0.9, dashArray, layerId }: RouteLayerProps) {
  const map = useMapEvents({})
  const layerRef = useRef<L.Polyline | null>(null)

  useEffect(() => {
    if (coords.length < 2) return

    const latLngs = coords.map((c) => [c.lat, c.lng] as L.LatLngExpression)

    layerRef.current = L.polyline(latLngs, {
      color,
      weight,
      opacity,
      dashArray,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(map)

    return () => {
      if (layerRef.current) map.removeLayer(layerRef.current)
    }
  }, [coords, color, weight, opacity, dashArray, map])

  useEffect(() => {
    if (layerId && coords.length > 0) {
      const latLngs = coords.map((c) => [c.lat, c.lng] as L.LatLngExpression)
      map.fitBounds(L.polyline(latLngs).getBounds().pad(0.15), {
        animate: true,
        duration: 1,
      })
    }
  }, [coords, layerId, map])

  return null
}

interface MarkerProps {
  position: Coordinates
  icon: L.DivIcon
  popup?: string
  zIndexOffset?: number
}

function MapMarker({ position, icon, popup, zIndexOffset = 0 }: MarkerProps) {
  return (
    <Marker position={[position.lat, position.lng]} icon={icon} zIndexOffset={zIndexOffset}>
      {popup && <Popup>{popup}</Popup>}
    </Marker>
  )
}

function DeliveryAnimation({ coords }: { coords: Coordinates[] }) {
  const map = useMapEvents({})
  const markerRef = useRef<L.Marker | null>(null)

  useEffect(() => {
    if (coords.length < 2) return

    const deliveryIcon = L.divIcon({
      className: 'delivery-marker-container',
      html: '<div class="delivery-marker"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    })

    markerRef.current = L.marker([coords[0].lat, coords[0].lng], {
      icon: deliveryIcon,
      zIndexOffset: 1000,
    }).addTo(map)

    let currentIndex = 0
    const speed = Math.max(30, Math.min(100, 3000 / coords.length))

    const interval = setInterval(() => {
      currentIndex++
      if (currentIndex >= coords.length) {
        clearInterval(interval)
        if (markerRef.current) map.removeLayer(markerRef.current)
        return
      }
      markerRef.current?.setLatLng([coords[currentIndex].lat, coords[currentIndex].lng])
    }, speed)

    return () => {
      clearInterval(interval)
      if (markerRef.current) map.removeLayer(markerRef.current)
    }
  }, [coords, map])

  return null
}

interface BlockageMarkerProps {
  position: Coordinates
}

function BlockageMarker({ position }: BlockageMarkerProps) {
  return (
    <CircleMarker
      center={[position.lat, position.lng]}
      radius={10}
      pathOptions={{
        color: '#f43f5e',
        fillColor: '#f43f5e',
        fillOpacity: 0.5,
        weight: 3,
      }}
    >
      <Popup>
        <strong>⚠️ Blockage Detected</strong><br />
        Route recalculated
      </Popup>
    </CircleMarker>
  )
}

function createIcon(color: string, symbol: string) {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 28px; height: 28px;
        background: ${color};
        border-radius: 50%;
        border: 3px solid white;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; font-weight: bold;
        box-shadow: 0 2px 12px ${color}88;
        color: white;
      ">${symbol}</div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

const sourceIcon = createIcon('#22c55e', 'S')
const destIcon = createIcon('#ef4444', 'D')
const waypointIcon = (num: number) => L.divIcon({
  className: 'custom-marker',
  html: `<div class="waypoint-badge">${num}</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

interface MapViewProps {
  center: Coordinates
  zoom: number
  source?: Coordinates
  destination?: Coordinates
  waypoints?: Coordinates[]
  route?: RouteResponse | null
  showAstar?: boolean
  showDfs?: boolean
  showMerged?: boolean
  showBfs?: boolean
  blockedCoords?: Coordinates[]
  onMapClick: (lat: number, lng: number) => void
  onBoundsChange: (bounds: { north: number; south: number; east: number; west: number; center_lat: number; center_lon: number }) => void
}

export function MapView({
  center,
  zoom,
  source,
  destination,
  waypoints = [],
  route,
  showAstar = true,
  showDfs = true,
  showMerged = true,
  showBfs = false,
  blockedCoords = [],
  onMapClick,
  onBoundsChange,
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null)

  // Handle map click
  const ClickHandler = () => {
    useMapEvents({
      click(e: any) {
        onMapClick(e.latlng.lat, e.latlng.lng)
      },
    })
    return null
  }

  // Handle bounds change
  const BoundsHandler = () => {
    useMapEvents({
      moveend() {
        if (mapRef.current) {
          const bounds = mapRef.current.getBounds()
          const center = mapRef.current.getCenter()
          onBoundsChange({
            north: bounds.getNorth(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            west: bounds.getWest(),
            center_lat: center.lat,
            center_lon: center.lng,
          })
        }
      },
    })
    return null
  }

  return (
    <MapContainer
      ref={mapRef}
      center={[center.lat, center.lng]}
      zoom={zoom}
      scrollWheelZoom={true}
      className="w-full h-full"
      attributionControl={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors | SmartPath'
        maxZoom={19}
      />

      <ClickHandler />
      <BoundsHandler />

      {source && <MapMarker position={source} icon={sourceIcon} popup="<strong>📍 Source</strong><br/>Start location" />}
      {destination && <MapMarker position={destination} icon={destIcon} popup="<strong>🎯 Destination</strong><br/>End location" />}
      {waypoints.map((wp, i) => (
        <MapMarker key={i} position={wp} icon={waypointIcon(i + 1)} popup={`<strong>🟣 Waypoint #${i + 1}</strong><br/>Delivery stop`} />
      ))}

      {blockedCoords.map((coord, i) => (
        <MapMarker
          key={i}
          position={coord}
          icon={L.divIcon({
            className: 'custom-marker',
            html: `<div style="width: 28px; height: 28px; background: #f43f5e; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; box-shadow: 0 2px 12px #f43f5e88; color: white;">✕</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          })}
          popup="<strong>⛔ Blocked Node</strong><br/>Road blockage"
        />
      ))}

      {route && showAstar && route.segments.length > 0 && (
        <RouteLayer
          coords={route.segments.flatMap((s) => s.coords)}
          color="#38bdf8"
          weight={4}
          opacity={0.6}
          dashArray="8, 8"
        />
      )}

      {route && showDfs && route.segments.length > 0 && (
        <RouteLayer
          coords={route.segments.flatMap((s) => s.coords)}
          color="#fb923c"
          weight={5}
          opacity={0.8}
          dashArray="5, 10"
        />
      )}

      {route && showMerged && route.segments.length > 0 && (
        <RouteLayer
          coords={route.segments.flatMap((s) => s.coords)}
          color="#a78bfa"
          weight={5}
          opacity={0.9}
          layerId="merged"
        />
      )}

      {route && showBfs && route.segments.length > 0 && (
        <RouteLayer
          coords={route.segments.flatMap((s) => s.coords)}
          color="#34d399"
          weight={4}
          opacity={0.7}
          dashArray="12, 6"
        />
      )}

      {route && route.segments.length > 0 && (
        <DeliveryAnimation coords={route.segments.flatMap((s) => s.coords)} />
      )}

      {route && route.segments.some((s) => s.risk > 0.7) && (
        <BlockageMarker position={route.segments[0].coords[0]} />
      )}
    </MapContainer>
  )
}