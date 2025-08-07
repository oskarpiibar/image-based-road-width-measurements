import ac
import acsys


def get_lap_position(car_id=0):
    # Returns value between 0 and 1
    return ac.getCarState(car_id, acsys.CS.NormalizedSplinePosition)


def get_world_location(car_id=0):
    # Returns a tuple (x, y) from WorldPosition
    pos = ac.getCarState(car_id, acsys.CS.WorldPosition)
    y = pos[0]
    x = pos[2]
    coordinates = (x, y)
    return coordinates
