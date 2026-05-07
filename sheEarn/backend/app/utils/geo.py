"""Geo utilities — Haversine distance calculation"""
import math


EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in kilometres.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def filter_by_radius(services_with_profiles, user_lat: float, user_lon: float, radius_km: float):
    """
    Filter a list of (service, profile) tuples by distance radius.
    Returns list of (service, profile, distance_km) sorted nearest-first.
    """
    results = []
    for service, profile in services_with_profiles:
        if profile and profile.latitude and profile.longitude:
            dist = haversine_distance(user_lat, user_lon, profile.latitude, profile.longitude)
            if dist <= radius_km:
                results.append((service, profile, dist))
    results.sort(key=lambda x: x[2])
    return results
