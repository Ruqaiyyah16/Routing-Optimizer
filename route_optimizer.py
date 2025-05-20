import requests
import folium
import pandas as pd
import polyline
from plyer import notification

# TomTom API Key
HERE_API = "0FKiA4FiUL0QqYRWD_xhlg_JVxKSzUv7hHDOnUtdWmo"  # Replace with your actual  API key
TOMTOM_API_KEY = "IsUik9Qm9wvuBJKLpDEFje3vTPggai29" 
def get_routes(start_lat, start_lon, end_lat, end_lon):
    """Fetch multiple route options from TomTom API and return details."""
    route_types = ["fastest", "shortest", "eco", "thrilling"]
    routes = []
    colors = ["blue", "red", "orange", "purple"]
    route_summaries = []
    
    for route_type, color in zip(route_types, colors):
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json?key={TOMTOM_API_KEY}&routeType={route_type}&traffic=true" 
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "routes" in data:
                route = data["routes"][0]
                route_points = route["legs"][0]["points"]
                route_coords = [(point["latitude"], point["longitude"]) for point in route_points]
                distance = route["summary"]["lengthInMeters"] / 1000  # Convert to km
                duration = route["summary"]["travelTimeInSeconds"] / 60  # Convert to minutes
                traffic_delay = route["summary"]["trafficDelayInSeconds"] / 60  # Convert to minutes
                
                routes.append((route_coords, color))
                route_summaries.append({
                    "type": route_type,
                    "distance_km": round(distance, 2),
                    "duration_min": round(duration, 2),
                    "traffic_delay_min": round(traffic_delay, 2)
                })
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {route_type} route: {e}")
    
    return routes, route_summaries
    
    
# User input for start and destination
start_location = input("Enter start location: ")
destination_location = input("Enter destination location: ")

# Fetch latitude and longitude using HERE API
def get_lat_long(address):
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&apiKey=0FKiA4FiUL0QqYRWD_xhlg_JVxKSzUv7hHDOnUtdWmo"
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

start_lat, start_lon = get_lat_long(start_location)
dest_lat, dest_lon = get_lat_long(destination_location)

if start_lat and dest_lat:
    routes, route_summaries = get_routes(start_lat, start_lon, dest_lat, dest_lon)
    
    # Select best route based on minimal duration including traffic delay
    best_route_index = min(range(len(route_summaries)), key=lambda i: route_summaries[i]["duration_min"] + route_summaries[i]["traffic_delay_min"])
    
    # Initialize map centered at start location
    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    
    # Add start and destination markers
    folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color="green")).add_to(route_map)
    folium.Marker([dest_lat, dest_lon], popup="Destination", icon=folium.Icon(color="red")).add_to(route_map)
    
    # Plot routes on map
    for i, (route, color) in enumerate(routes):
        if i == best_route_index:
            color = "blue"  # Best route in blue
        folium.PolyLine(route, color=color, weight=5, opacity=0.7).add_to(route_map)
    
    # Display route summaries
    print("\nRoute Options:")
    for i, summary in enumerate(route_summaries):
        label = "(Best Route)" if i == best_route_index else ""
        print(f"{summary['type'].capitalize()} - Distance: {summary['distance_km']} km, Duration: {summary['duration_min']} min, Traffic Delay: {summary['traffic_delay_min']} min {label}")
    
    # Save the map
    route_map.save("optimized_routes_map.html")
    print("Map with multiple routes saved as optimized_routes_map.html. Open it in a browser to view.")
else:
    print("Failed to fetch coordinates for the given locations.")