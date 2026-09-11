import { AlertTriangle, Shield, Clock, Zap, MapPin, CheckCircle, XCircle, Info } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { cn, formatDuration, formatDistance, formatRiskScore, getRiskColor } from '../../lib/utils'
import type { RouteResponse, RouteExplanation } from '../../types'

interface RouteResultCardProps {
  route: RouteResponse | null
  explanation?: RouteExplanation
  onUseRoute: () => void
  onViewAlternatives: () => void
  isLoading?: boolean
}

export function RouteResultCard({ route, explanation, onUseRoute, onViewAlternatives, isLoading }: RouteResultCardProps) {
  if (!route) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full min-h-[200px]">
          <div className="text-center text-neutral-500">
            <Info className="w-12 h-12 mx-auto mb-4 text-neutral-300" />
            <p className="text-body-m">Select origin and destination to calculate a route</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const { level: riskLevel, color: riskColor } = formatRiskScore(route.risk_score)
  const riskBg = getRiskColor(route.risk_score)

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-heading-m">Recommended Route</CardTitle>
          <Badge variant={riskLevel.toLowerCase() === 'very low' || riskLevel.toLowerCase() === 'low' ? 'success' : riskLevel.toLowerCase() === 'medium' ? 'warning' : 'danger'}>
            {riskLevel} Risk
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <p className="text-caption text-neutral-500 uppercase tracking-wider">Distance</p>
            <p className="text-heading-s font-bold text-brand-primary">{formatDistance(route.distance_km)}</p>
          </div>
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <p className="text-caption text-neutral-500 uppercase tracking-wider">ETA</p>
            <p className="text-heading-s font-bold text-brand-secondary">{formatDuration(route.eta_min)}</p>
          </div>
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <p className="text-caption text-neutral-500 uppercase tracking-wider">Reliability</p>
            <p className="text-heading-s font-bold text-success">{Math.round(route.reliability_score * 100)}%</p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="font-medium text-neutral-700">Risk Score</span>
              <span className="font-mono text-brand-primary">{route.risk_score.toFixed(2)}</span>
            </div>
            <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all duration-500', riskBg)}
                style={{ width: `${route.risk_score * 100}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2 p-2 bg-neutral-50 rounded-lg">
              <Clock className="w-4 h-4 text-neutral-500" />
              <span className="text-neutral-600">Algorithm: <span className="font-mono text-brand-primary capitalize">{route.algorithm.replace('_', ' ')}</span></span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-neutral-50 rounded-lg">
              <Shield className="w-4 h-4 text-neutral-500" />
              <span className="text-neutral-600">Data: <span className="font-mono text-brand-primary capitalize">{route.data_quality.traffic}</span> traffic</span>
            </div>
          </div>
        </div>

        {explanation && (
          <div className="border-t border-neutral-200 pt-4 space-y-2">
            <h4 className="font-semibold text-neutral-900">Why this route?</h4>
            <ul className="space-y-1.5">
              {explanation.factors.map((factor, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-neutral-600">
                  <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                  <span>{factor.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex gap-2 pt-2 border-t border-neutral-200">
          <Button onClick={onUseRoute} className="flex-1" size="lg">
            Use This Route
          </Button>
          <Button variant="outline" onClick={onViewAlternatives} className="flex-1" size="lg">
            View Alternatives
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface RouteComparisonProps {
  comparison: RouteExplanation['comparison']
  onSelectRoute: (type: 'recommended' | 'fastest' | 'safest') => void
}

export function RouteComparison({ comparison, onSelectRoute }: RouteComparisonProps) {
  if (!comparison) return null

  const routes = [
    { key: 'recommended', ...comparison.recommended, label: 'Recommended' },
    { key: 'fastest', ...comparison.fastest, label: 'Fastest' },
    { key: 'safest', ...comparison.safest, label: 'Safest' },
  ]

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-heading-m">Route Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-neutral-500 text-caption uppercase tracking-wider border-b border-neutral-200">
                <th className="pb-2">Route</th>
                <th className="pb-2 text-right">ETA</th>
                <th className="pb-2 text-right">Distance</th>
                <th className="pb-2 text-right">Risk</th>
                <th className="pb-2 text-right">Reliability</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {routes.map((r) => (
                <tr key={r.key} className={cn(r.key === 'recommended' && 'bg-brand-primary/5')}>
                  <td className="py-3 font-medium text-neutral-900">{r.label}</td>
                  <td className="py-3 text-right font-mono text-brand-primary">{formatDuration(r.eta_min)}</td>
                  <td className="py-3 text-right font-mono text-brand-secondary">{formatDistance(r.distance_km)}</td>
                  <td className="py-3 text-right">
                    <Badge variant={r.risk_level.includes('low') ? 'success' : r.risk_level === 'medium' ? 'warning' : 'danger'} size="sm">
                      {r.risk_level.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="py-3 text-right font-mono text-success">{Math.round(r.reliability * 100)}%</td>
                  <td className="py-3 text-right">
                    <Button variant="ghost" size="sm" onClick={() => onSelectRoute(r.key as 'recommended' | 'fastest' | 'safest')}>
                      Select
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}



