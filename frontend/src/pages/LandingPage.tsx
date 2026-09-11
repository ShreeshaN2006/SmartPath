import { Link } from 'react-router-dom'
import { ArrowRight, Navigation, Shield, Zap, BrainCircuit, Truck, Clock, MapPin, CheckCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { cn } from '../lib/utils'

const features = [
  {
    icon: BrainCircuit,
    title: 'Predictive Traffic',
    description: 'Forecast road speed before congestion reaches your route using DCRNN models trained on historical and real-time data.',
  },
  {
    icon: Zap,
    title: 'Dynamic Replanning',
    description: 'Recalculate routes in milliseconds when road conditions change using D* Lite incremental search.',
  },
  {
    icon: Truck,
    title: 'Vehicle Aware',
    description: 'Avoid incompatible roads based on vehicle constraints — height, weight, width, and road class restrictions.',
  },
  {
    icon: Shield,
    title: 'Risk Aware',
    description: 'Balance travel time against disruption risk with configurable cost functions and explainable decisions.',
  },
]

const metrics = [
  { value: '18.2 min', label: 'Predicted ETA' },
  { value: '0.21', label: 'Risk Score' },
  { value: '91%', label: 'Route Reliability' },
  { value: '84 ms', label: 'Replanning Time' },
]

const useCases = [
  {
    icon: Truck,
    title: 'Last-Mile Delivery',
    description: 'Optimize delivery routes with vehicle constraints, time windows, and dynamic traffic.',
  },
  {
    icon: MapPin,
    title: 'Emergency Response',
    description: 'Rapid replanning for ambulances with emergency overrides and incident awareness.',
  },
  {
    icon: Clock,
    title: 'Fleet Management',
    description: 'Compare route options, track reliability metrics, and analyze operational efficiency.',
  },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center">
              <Navigation className="w-6 h-6 text-white" />
            </div>
            <span className="text-heading-m font-bold bg-gradient-to-r from-brand-primary to-brand-secondary bg-clip-text text-transparent">
              SmartPath
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-neutral-600 hover:text-brand-primary">
            <Link to="#features" className="transition-colors">Product</Link>
            <Link to="#intelligence" className="transition-colors">Intelligence</Link>
            <Link to="#use-cases" className="transition-colors">Use Cases</Link>
            <Link to="#research" className="transition-colors">Research</Link>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/planner" className="hidden md:block text-sm font-medium text-brand-primary hover:text-brand-secondary transition-colors">
              Plan a Route
            </Link>
            <Link to="/planner">
              <Button size="lg" className="hidden sm:block">
                Plan a Route
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-20">
        <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-primary/5 via-white to-brand-secondary/5" />
          <div className="max-w-7xl mx-auto px-6 py-20 relative z-10 text-center">
            <span className="inline-block px-4 py-1.5 rounded-pill bg-brand-primary/10 text-brand-primary text-sm font-semibold mb-6">
              PREDICTIVE ROUTE INTELLIGENCE
            </span>
            <h1 className="text-display-l font-bold text-neutral-900 max-w-3xl mx-auto mb-6 leading-tight">
              The route that thinks ahead.
            </h1>
            <p className="text-body-l text-neutral-600 max-w-2xl mx-auto mb-10 leading-relaxed">
              SmartPath predicts traffic, evaluates risk and dynamically replans routes as urban conditions change.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/planner">
                <Button size="lg" className="w-full sm:w-auto gap-2">
                  Plan a Route
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link to="#how-it-works">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  See How It Works
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="py-20 bg-neutral-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-heading-xl font-bold text-neutral-900 mb-4">How It Works</h2>
              <p className="text-body-l text-neutral-600 max-w-2xl mx-auto">
                Four steps from request to explainable, adaptive route
              </p>
            </div>
            <div className="grid md:grid-cols-4 gap-6">
              {[
                { step: '01', title: 'Request', desc: 'Origin, destination, vehicle type, and routing objective' },
                { step: '02', title: 'Predict', desc: 'DCRNN forecasts traffic, weather, and incident impacts' },
                { step: '03', title: 'Optimize', desc: 'Risk-aware edge costs feed D* Lite for adaptive routing' },
                { step: '04', title: 'Explain', desc: 'Human-readable justification with factor breakdown' },
              ].map((item) => (
                <Card key={item.step} variant="elevated" padding="lg" className="text-center">
                  <span className="text-caption font-bold text-brand-primary tracking-wider">{item.step}</span>
                  <h3 className="text-heading-m font-bold mt-2 mb-2">{item.title}</h3>
                  <p className="text-neutral-600">{item.desc}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="features" className="py-20">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-heading-xl font-bold text-neutral-900 mb-4">Intelligence Features</h2>
              <p className="text-body-l text-neutral-600 max-w-2xl mx-auto">
                Core capabilities that make routing predictive and adaptive
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature) => (
                <Card key={feature.title} variant="outlined" padding="lg" className="h-full transition-shadow hover:shadow-xl">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-xl bg-brand-primary/10 flex items-center justify-center mb-4">
                      <feature.icon className="w-6 h-6 text-brand-primary" />
                    </div>
                    <CardTitle className="text-heading-s">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-neutral-600">{feature.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="metrics" className="py-20 bg-neutral-900">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <h2 className="text-heading-xl font-bold text-white mb-4">Measured Performance</h2>
            <p className="text-neutral-400 max-w-2xl mx-auto mb-16">Demo values from Bangalore test network — not production guarantees</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {metrics.map((metric) => (
                <div key={metric.label}>
                  <div className="text-4xl md:text-5xl font-bold text-white font-mono mb-2">{metric.value}</div>
                  <div className="text-neutral-400 text-sm">{metric.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="use-cases" className="py-20">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-heading-xl font-bold text-neutral-900 mb-4">Use Cases</h2>
              <p className="text-body-l text-neutral-600 max-w-2xl mx-auto">
                Built for real operational scenarios
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {useCases.map((useCase) => (
                <Card key={useCase.title} variant="elevated" padding="lg" className="h-full">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-xl bg-brand-secondary/10 flex items-center justify-center mb-4">
                      <useCase.icon className="w-6 h-6 text-brand-secondary" />
                    </div>
                    <CardTitle className="text-heading-s">{useCase.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-neutral-600">{useCase.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="research" className="py-20 bg-neutral-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-heading-xl font-bold text-neutral-900 mb-4">Research & Analytics</h2>
              <p className="text-body-l text-neutral-600 max-w-2xl mx-auto">
                Reproducible experiments with algorithm comparison and ML benchmarking
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              <Card variant="outlined" padding="lg">
                <CardHeader>
                  <CardTitle className="text-heading-s">Routing Benchmarks</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {['A* vs BFS node expansion', 'D* Lite replanning time', 'Hybrid A*/DFS recovery rate', 'Vehicle constraint feasibility'].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
                      <span className="text-neutral-600">{item}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card variant="outlined" padding="lg">
                <CardHeader>
                  <CardTitle className="text-heading-s">Traffic Prediction</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {['DCRNN vs LSTM vs XGBoost', 'MAE / RMSE / MAPE metrics', 'Weather feature ablation', 'Inference latency profiling'].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
                      <span className="text-neutral-600">{item}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card variant="outlined" padding="lg">
                <CardHeader>
                  <CardTitle className="text-heading-s">Resilience Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {['Route availability under incidents', 'Recovery time distribution', 'Reachability analysis', 'Historical reliability scoring'].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
                      <span className="text-neutral-600">{item}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="py-20 bg-brand-primary">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <h2 className="text-heading-xl font-bold text-white mb-4">Ready to optimize your routes?</h2>
            <p className="text-brand-primary/80 max-w-2xl mx-auto mb-8">Start planning with predictive, risk-aware intelligence today.</p>
            <Link to="/planner">
              <Button variant="secondary" size="lg" className="gap-2">
                Get Started
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-neutral-900 text-neutral-400 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center">
                  <Navigation className="w-6 h-6 text-white" />
                </div>
                <span className="text-heading-m font-bold text-white">SmartPath</span>
              </div>
              <p className="text-sm max-w-xs">Predictive & risk-aware dynamic route optimization for urban logistics and emergency response.</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/planner" className="hover:text-white transition-colors">Route Planner</a></li>
                <li><a href="#intelligence" className="hover:text-white transition-colors">Intelligence</a></li>
                <li><a href="#research" className="hover:text-white transition-colors">Research Mode</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="https://github.com/ShreeshaN2006/SmartPath" className="hover:text-white transition-colors" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                <li><a href="#docs" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#api" className="hover:text-white transition-colors">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#privacy" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#terms" className="hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-neutral-800 pt-8 text-center text-sm">
            <p>© 2026 SmartPath. Open source under MIT license.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}



