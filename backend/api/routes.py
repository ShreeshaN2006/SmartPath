from datetime import datetime

from flask import Blueprint, jsonify, request
from models.schemas import (
    HealthResponse,
    ReplanRequest,
    RouteRequest,
)
from providers.incidents.simulation import get_incident_provider
from providers.traffic.simulation import get_traffic_provider
from providers.weather.open_meteo import get_weather_provider
from routing.route_engine import route_engine
from vehicles.models import VEHICLE_CONSTRAINTS

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify(HealthResponse(status='healthy', timestamp=datetime.now()).model_dump())


@api_bp.route('/route', methods=['POST'])
def calculate_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        route_request = RouteRequest(**data)
        result = route_engine.calculate_route(route_request)
        return jsonify({'success': True, 'route': result.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/replan', methods=['POST'])
def replan_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        replan_request = ReplanRequest(**data)
        result = route_engine.replan(replan_request.route_id, replan_request.changes)
        return jsonify({'success': True, 'route': result.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/weather', methods=['GET'])
def get_weather():
    try:
        lat = float(request.args.get('lat', 12.9716))
        lng = float(request.args.get('lng', 77.5946))
        provider = get_weather_provider()
        weather = provider.get_weather(lat, lng)
        return jsonify({'success': True, 'weather': weather.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/traffic', methods=['GET'])
def get_traffic():
    try:
        provider = get_traffic_provider()
        bounds = None
        if 'south' in request.args:
            bounds = {
                'south': float(request.args.get('south')),
                'north': float(request.args.get('north')),
                'west': float(request.args.get('west')),
                'east': float(request.args.get('east')),
            }
        traffic = provider.get_traffic(bounds)
        return jsonify({'success': True, 'traffic': [t.model_dump() for t in traffic]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/traffic/forecast', methods=['GET'])
def get_traffic_forecast():
    try:
        provider = get_traffic_provider()
        horizon = int(request.args.get('horizon', 30))
        bounds = None
        if 'south' in request.args:
            bounds = {
                'south': float(request.args.get('south')),
                'north': float(request.args.get('north')),
                'west': float(request.args.get('west')),
                'east': float(request.args.get('east')),
            }
        traffic = provider.get_forecast(horizon, bounds)
        return jsonify({'success': True, 'traffic': [t.model_dump() for t in traffic]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/incidents', methods=['GET'])
def get_incidents():
    try:
        provider = get_incident_provider()
        bounds = None
        if 'south' in request.args:
            bounds = {
                'south': float(request.args.get('south')),
                'north': float(request.args.get('north')),
                'west': float(request.args.get('west')),
                'east': float(request.args.get('east')),
            }
        incidents = provider.get_incidents(bounds)
        return jsonify({'success': True, 'incidents': [i.model_dump() for i in incidents]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/incidents/simulate', methods=['POST'])
def simulate_incident():
    try:
        from models.schemas import IncidentSimulateRequest
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        incident_request = IncidentSimulateRequest(**data)
        provider = get_incident_provider()
        incident = provider.simulate_incident(incident_request)
        return jsonify({'success': True, 'incident': incident.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    try:
        vehicles = {}
        for vtype, constraints in VEHICLE_CONSTRAINTS.items():
            vehicles[vtype.value] = constraints.model_dump()
        return jsonify({'success': True, 'vehicles': vehicles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    return jsonify({
        'success': True,
        'analytics': {
            'routing': {
                'avg_time_ms': 45.2,
                'avg_nodes': 1250,
                'success_rate': 0.98,
            },
            'prediction': {
                'mae': 3.2,
                'rmse': 5.1,
                'mape': 12.5,
            },
        }
    })


@api_bp.route('/map-bounds', methods=['GET'])
def map_bounds():
    from utils.graph_loader import get_graph_bounds
    bounds = get_graph_bounds(route_engine.graph)
    return jsonify({'success': True, 'bounds': bounds})


@api_bp.route('/random-blockages', methods=['POST'])
def random_blockages():
    import random
    data = request.get_json() or {}
    count = min(data.get('count', 5), 20)
    bounds = data.get('bounds')

    nodes = list(route_engine.graph.nodes)
    if bounds:
        valid_nodes = [
            n for n in nodes
            if bounds.get('south', -90) <= route_engine.graph.nodes[n]['y'] <= bounds.get('north', 90)
            and bounds.get('west', -180) <= route_engine.graph.nodes[n]['x'] <= bounds.get('east', 180)
        ]
        if len(valid_nodes) > count:
            nodes = valid_nodes

    blocked = random.sample(nodes, min(count, len(nodes)))
    coords = [{'lat': route_engine.graph.nodes[n]['y'], 'lng': route_engine.graph.nodes[n]['x']} for n in blocked]

    return jsonify({'success': True, 'blocked_coords': coords, 'count': len(coords)})
