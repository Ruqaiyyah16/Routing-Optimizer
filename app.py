from flask import Flask, render_template, request, jsonify
import requests

# Initialize Flask app
app = Flask(__name__, template_folder="C:/Users/Afrose Shahul/Dissertation/routeopt")

# API Keys
TOMTOM_API_KEY = "IsUik9Qm9wvuBJKLpDEFje3vTPggai29"
HERE_API_KEY = "0FKiA4FiUL0QqYRWD_xhlg_JVxKSzUv7hHDOnUtdWmo"

@app.route("/")
def index():
    return render_template("index.html")

# Fetch latitude and longitude using HERE API
def get_lat_long(address):
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&apiKey={HERE_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            location = data["items"][0]["position"]
            return location["lat"], location["lng"]
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {address}: {e}")
    return None, None

# Fetch routes from TomTom API
def get_routes(start_lat, start_lon, end_lat, end_lon):
    route_types = ["fastest", "shortest", "eco", "thrilling"]
    routes = []
    route_summaries = []
    
    for route_type in route_types:
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json?key={TOMTOM_API_KEY}&routeType={route_type}&traffic=true"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "routes" in data:
                route = data["routes"][0]
                route_points = route["legs"][0]["points"]
                route_coords = [(point["latitude"], point["longitude"]) for point in route_points]
                distance = round(route["summary"]["lengthInMeters"] / 1000, 2)
                duration = round(route["summary"]["travelTimeInSeconds"] / 60, 2)
                traffic_delay = round(route["summary"]["trafficDelayInSeconds"] / 60, 2)
                
                routes.append(route_coords)
                route_summaries.append({
                    "type": route_type,
                    "distance_km": distance,
                    "duration_min": duration,
                    "traffic_delay_min": traffic_delay
                })
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {route_type} route: {e}")

    return routes, route_summaries

@app.route('/get_route', methods=['POST'])
def get_route():
    data = request.get_json()
    start_location = data.get('start')
    destination_location = data.get('destination')

    print(f"Received start: {start_location}, destination: {destination_location}")  

    start_lat, start_lon = get_lat_long(start_location)
    dest_lat, dest_lon = get_lat_long(destination_location)

    print(f"Coordinates - Start: ({start_lat}, {start_lon}), Destination: ({dest_lat}, {dest_lon})")  

    if not start_lat or not dest_lat:
        return jsonify({"error": "Invalid location"}), 400

    routes, route_summaries = get_routes(start_lat, start_lon, dest_lat, dest_lon)

    if not routes:
        return jsonify({"error": "No routes found"}), 400

    best_route_index = min(range(len(route_summaries)), key=lambda i: route_summaries[i]["duration_min"] + route_summaries[i]["traffic_delay_min"])

    return jsonify({
        "start_coordinates": [start_lat, start_lon],
        "destination_coordinates": [dest_lat, dest_lon],
        "routes": routes,
        "route_summaries": route_summaries,
        "best_route_index": best_route_index
    })

if __name__ == "__main__":
    app.run(debug=True)