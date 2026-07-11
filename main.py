from parser import Parser
from typing import List, Dict, Tuple, Optional
from metadata import ZoneType, Color
import sys

class Zone:
    def __init__(
        self,
        name: str,
        coordinates: Tuple[int, int],
        zone_type: ZoneType = "normal",
        color: Optional[str] = None,
        zone_capacity: Optional[int] = 1
    ) -> None:
        self.name : str = name
        self.coordinates :Tuple[int, int] = coordinates
        self.zone_type : ZoneType = zone_type
        self.color : Optional[str] = color
        self.zone_capacity : int = zone_capacity
        self.drones: list[int] = []  # IDs currently in this zone. ints
        self.neighbors: list[Connection] = [] # TODO list of Connection obj.
    
    def move_cost(self)-> int:
        """Return turn cost to ENTER this zone (1, 2, or invalid if blocked)."""
        ...

    def is_blocked(self)-> bool:
        ...

    def has_capacity(self)-> bool:
        """True if another drone can fit (respecting max_drones)."""
        ...

    def add_drone(self, drone_id: int) -> None:
        ...

    def remove_drone(self, drone_id: int)-> None:
        ...



class Drone:
    def __init__(self, drone_id: int):
        self.id : int = drone_id
        self.path : list[Zone] = []         # ordered Zones to follow
        self.position = None      # current Zone
        self.transit = None       # Connection if mid multi-turn move
        self.transit_left = 0     # turns remaining on that connection
        self.delivered = False


    def next_zone(self) -> Optional[Zone]:
        """The zone this drone wants to enter next, or None."""
        if self.position == None or self.delivered == True:
            return None
        for index, zone in enumerate(self.path):
            if zone == self.position:
                return self.path[index + 1]
            # if the zone == end? no need for the next_zone func in  the first place




class Connection:
    def __init__(
        self,
        zone_a : Zone,
        zone_b : Zone,
        max_link_capacity : int = 1
    )-> None:
        self.a : Zone = zone_a
        self.b : Zone = zone_b
        self.max_link_capacity : int = max_link_capacity
        self.in_transit: list[int] = []      # drones  IDs  currently traversing this conn this turn




    def other(self, zone: Zone) -> Zone:
        if zone == self.a:
            return self.b
        elif zone == self.b:
            return self.a
        """Given one endpoint, return the other."""
        ...

    def has_capacity(self)-> bool:
        return len(self.in_transit) < self.max_link_capacity 

class Graph:
    def __init__(self) -> None:
        self.zones : dict[str, Zone] = {}           # name -> Zone.obj
        self.connections : list[Connection] = []     # list of Connection.obj
        self.start : Zone = None         # Zone
        self.end : Zone = None           # Zone
        self.nb_drones: int = 0
    def add_zone(
        self,
        zone : Zone,
        is_start :bool=False,
        is_end :bool=False
    )-> None:
        self.zones[zone.name] =  zone
        if is_start:
            self.start = zone
        if is_end:
            self.end = zone

    def add_connection(
        self,
        name_a: str, # TODO: str?
        name_b: str, # TODO: str?
        max_link_capacity: int = 1
    )-> None:
        self.connections.append(
            Connection(
                self.zones[name_a],
                self.zones[name_b],
                max_link_capacity
            )
        )
        """Link two existing zones"""



    def make_graph(
            self,
            parser_info : Parser,
    )-> None:
        for config in parser_info.configs:
            match config.type_:
                case "nb_drones":
                    self.nb_drones = config.value
                case "hub" | "start_hub" | "end_hub":
                    zone_ = Zone(
                        config.value,
                        (config.x, config.y),
                        config.metadata["zone"],
                        config.metadata["color"],
                        config.metadata["max_drones"]
                    )
                    if config.type_ == "end_hub":
                         self.add_zone(zone_,is_end=True)
                    elif config.type_ == "start_hub":
                        self.add_zone(zone_,is_start=True)
                    elif config.type_ == "hub":
                        self.add_zone(zone_)
                
        for config in parser_info.configs:
            if config.type_ == "connection":
                n_zones = config.value.split("-") 
                self.add_connection(
                    n_zones[0],
                    n_zones[1],
                    config.metadata["max_link_capacity"]
                )
                    
    def neighbors(self, zone: Zone)-> list[Zone]:
        """Return zones reachable from `zone` (skipping blocked)."""
        list_neighbors : list[Zone] = []
        for connection in self.connections:
            if connection.a == zone or connection.b == zone:
                list_neighbors.append(connection.other(zone))
            continue
        return list_neighbors

    def ft_shortest_path(self)-> list[Zone]:
        pass



    def find_paths(self) -> list[list[Zone]]:
        """Return candidate paths start->end, weighted by move_cost,
        preferring priority zones. Disjoint or overlapping as needed."""
        ...

class Simulation:
    def __init__(self, graph):
        self.graph : Graph = graph
        self.drones : list[Drone] = []          # all Drone objects
        self.turn : int = 0
    




def main()-> None:
    try:
        if len(sys.argv) != 2:
            print(f"Usage: python3 {sys.argv[0]} config_file.txt")
            sys.exit(1)
        if not sys.argv[1].endswith(".txt"):
            raise ValueError(
                f" configfile's name should ends with .txt\n"
            )
        parser_info = Parser(sys.argv[1])
        parser_info.parse()
        drones_field = Graph()
        drones_field.make_graph(parser_info)
        # TODO: for max_link_capacity= 0 , nothing?
        # TODO: make the graph, from a to z.
        # make graph
        
        # print("=== ZONES ===")
        # for config in parser_info.configs:
        #     print(f"type: {config.type_}, value: {config.value}, x: {config.x}, y: {config.y}, metadata: {config.metadata}")
    except FileNotFoundError:
        print(f"Error The file {parser_info.file_name} not found")
        sys.exit(1)
    except PermissionError:
        print(
            f"no permission to read {parser_info.file_name}, "
            f"use the command: chmod +r map.txt"
        )
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", end="")
        sys.exit(1)

if __name__ == "__main__":
    main()