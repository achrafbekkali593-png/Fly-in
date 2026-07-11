from typing import List, Union, Optional
from metadata import ZoneType, Color
import re


class Config:
    def __init__(
        self,
        type_: str,
        value: Union[str, int],
        x: Optional[int] = None,
        y: Optional[int] = None,
        metadata: Optional[dict[str, str]] = None
    ) -> None:
        self.type_ = type_
        self.value = value
        self.x = x
        self.y = y
        self.metadata = metadata


class Parser:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.lines: list[tuple[int, str]] = []
        self.configs: list[Config] = []
        self.seen_prefix: set[str] = set()
        self.list_zones: set[str] = set()
        self.connection_zones: set[tuple[str, str]] = set()
        self.list_coordinates: set[tuple[int, int]] = set()
        self.nb_drones : int = None

    def _read_file(self):
        with open(self.file_name, "r", encoding="utf-8") as file:  # TODO:utf-8 meaning
            for index, line in enumerate(file, start=1):
                if not line.strip() or line.strip().startswith("#"):
                    continue
                self.lines.append((index, line))

    def _parse_hub(self, line, index):
        parts = line.split(":")
        type_prefix = parts[0].strip()
        if len(parts) != 2 or type_prefix not in {"start_hub", "end_hub", "hub"}:
            raise ValueError(
                f"expected 'hub|start_hub|end_hub: <name> <x> <y>' at line {index}: '{line.strip()}'"
            )
        # start_hub and end_hub must be unique
        if type_prefix in {"start_hub", "end_hub"} and type_prefix in self.seen_prefix:
            raise ValueError(
                f"duplicate '{type_prefix}' at line {index}: only one start and end_hub are allowed"
            )
        self.seen_prefix.add(type_prefix)

        # example: "hub 0 0 [color=green]" -> ['hub', '0', '0', '[color=green]']
        hub_info = re.findall(r"\[[^\]]*\]\s*$|\S+", parts[1].strip())
        if len(hub_info) < 3 or len(hub_info) > 4:
            print(hub_info)
            raise ValueError(
                f"expected '<name> <x> <y> [metadata]', got {len(hub_info)} token(s) at line {index}: '{parts[1].strip()}'"
            )
        try:
            x: int = int(hub_info[1])
            y: int = int(hub_info[2])
        except ValueError:
            raise ValueError(
                f"x and y must be integers at line {index}: got '{hub_info[1]}' and '{hub_info[2]}'"
            )

        name_zone = hub_info[0]
        if "-" in name_zone:
            raise ValueError(
                f"zone name '{name_zone}' cannot contain '-' at line {index}"
            )
        if name_zone in self.list_zones:
            raise ValueError(
                f"duplicate zone name '{name_zone}' at line {index}"
            )
        if (x, y) in self.list_coordinates:
            raise ValueError(
                f"coordinates ({x}, {y}) already used by another hub at line {index}"
            )
        self.list_coordinates.add((x, y))
        self.list_zones.add(name_zone)  # TODO: use list zones

        metadata = hub_info[3] if len(hub_info) == 4 else None
        return Config(
            type_prefix,
            name_zone,
            x=x,
            y=y,
            metadata=self._parse_metadata(metadata, index, type_prefix)
        )

    # connection: tunnelB-goal
    def _parse_connection(self, line, index):
        parts = line.split(":")
        type_prefix = parts[0].strip()
        if len(parts) != 2 or type_prefix != "connection":
            raise ValueError(
                f"expected 'connection: <zone1>-<zone2> [metadata]' at line {index}: '{line.strip()}'"
            )
        connection_info = re.findall(r"\[[^]]\]\s*$|\S+", parts[1])
        if len(connection_info) < 1 or len(connection_info) > 2:
            raise ValueError(
                f"expected '<zone1>-<zone2>', got {len(connection_info)} token(s) at line {index}: '{parts[1].strip()}'"
            )
        link = connection_info[0]
        l_zones = link.split("-")
        if len(l_zones) != 2 or len(l_zones[0]) == 0 or len(l_zones[1]) == 0:
            raise ValueError(
                f"connection link must be '<zone1>-<zone2>' at line {index}: got '{link}'"
            )
        zone1, zone2 = l_zones[0], l_zones[1]
        # a-b and b-a are the same connection (sorted) -> reversed duplicate raises
        pair = tuple(sorted((zone1, zone2)))
        if pair in self.connection_zones:
            raise ValueError(
                f"duplicate connection '{zone1}-{zone2}' at line {index}"
            )
        self.connection_zones.add(pair)

        metadata = connection_info[1] if len(connection_info) == 2 else None
        return Config(
            type_prefix,
            link.strip(),
            metadata=self._parse_metadata(metadata, index, type_prefix)
        )

    def _parse_metadata(self, metadata, index, type_prefix) -> dict[str, str]:
        
        if metadata == None:
            match type_prefix:
                case "hub":
                    return {"zone": "normal", "color": None, "max_drones": 1}
                case "start_hub" | "end_hub":
                    if self.nb_drones == None:
                        raise ValueError(
                            "Please specify nb_drones in the first_line of the file"
                        )
                    return {"zone": "normal", "color": None, "max_drones": self.nb_drones}
                case "connection":
                    return {"max_link_capacity": 1}
        metadata = metadata.strip()
        if not (metadata.startswith("[") and metadata.endswith("]")):
            raise ValueError(
                f"metadata must be wrapped in [] at line {index}: got '{metadata}'"
            )

        if type_prefix in {"hub", "start_hub", "end_hub"}:
            allowed_hubkeys = {"zone", "color", "max_drones"}
            default_max = 1 if type_prefix == "hub" else self.nb_drones
            metadata_dict = {"zone": "normal", "color": None, "max_drones": default_max}

            items = re.findall(r"\S+", metadata.strip("[]"))
            if len(items) == 0 or len(items) > 3:  # edge case: [] -> error
                raise ValueError(
                    f"expected 1 to 3 key=value pairs in [] at line {index}: '{metadata}'"
                    f"with syntax : key=value"
                )
            for item in items:
                parts = item.split("=")
                if len(parts) != 2 or parts[1] == "":
                    raise ValueError(
                        f"invalid metadata item '{item}' at line {index}: expected 'key=value'"
                    )
                key = parts[0]
                value = parts[1]
                try:
                    allowed_hubkeys.remove(key)  # also rejects duplicated keys
                except KeyError:
                    raise ValueError(
                        f"unknown or duplicate metadata key '{key}' at line {index}: allowed keys are zone, color, max_drones"
                    )
                match key:
                    case "zone":
                        # TODO hub: any zone type, start/end hub: normal only
                        valid_zones = {c.value for c in ZoneType} if type_prefix == "hub" else {"normal", "priority"}
                        if value not in valid_zones:
                            raise ValueError(
                                f"invalid zone '{value}' for '{type_prefix}' at line {index}: valid ZoneTypes are {valid_zones}"
                            )
                    case "color":
                        valid_colors = {c.value for c in Color}
                        if value not in valid_colors:
                            value = None
                    case "max_drones":
                        try:
                            value = int(value)
                            if value <= 0:
                                raise ValueError(
                                f"max_drones must be a positive integer at line"
                                f" {index}: got '{value}'"
                            )
                            if type_prefix in {"start_hub", "end_hub"}:
                                
                                if value < default_max:
                                    raise ValueError(
                                        f"max_drones for start_hub/end_hub should be superior or equal to "
                                        f"nb_drones: {default_max}"
                                )
                        except ValueError as e:
                            raise ValueError(e)
                metadata_dict[key] = value
            return metadata_dict

        # connection
        metadata_dict = {"max_link_capacity": 1}
        items = re.findall(r"\S+", metadata.strip("[]"))
        if len(items) != 1:
            raise ValueError(
                f"connection metadata expects exactly 'max_link_capacity=<n>' at line {index}: '{metadata}'"
            )
        parts = items[0].split("=")
        if len(parts) != 2 or parts[0] != "max_link_capacity":
            raise ValueError(
                f"unknown connection metadata key '{parts[0]}' at line {index}: only 'max_link_capacity' is allowed"
            )
        try:
            metadata_dict["max_link_capacity"] = int(parts[1])
            if metadata_dict["max_link_capacity"] <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError(
                f"max_link_capacity must be a positive integer at line {index}: got '{parts[1]}'"
            )
        return metadata_dict

    def _parse_nbdrones(self, line, index):
        parts = line.split(":")
        if len(parts) != 2 or parts[0].strip() != "nb_drones":
            raise ValueError(
                f"expected 'nb_drones: <number>' at line {index}: '{line.strip()}'"
            )
        try:
            nb_drones = int(parts[1].strip())
            if nb_drones <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError(
                f"nb_drones must be a positive integer at line {index}: got '{parts[1].strip()}'"
            )
        self.nb_drones = nb_drones
        return Config(parts[0].strip(), nb_drones)

    def parse(self) -> None:
        self._read_file()
        first = False
        for index, line in self.lines:
            line_type = self._detect_line_type(line, index)
            match line_type:
                case "nb_drones":
                    self.configs.append(self._parse_nbdrones(line, index))
                    if first:
                        raise ValueError(f"duplicated nb_drone detected at line {index}")
                    first = True
                case "hub" | "start_hub" | "end_hub":
                    self.configs.append(self._parse_hub(line, index))
                case "connection":
                    self.configs.append(self._parse_connection(line, index))
        if "start_hub" not in self.seen_prefix or "end_hub" not in self.seen_prefix:
            raise ValueError(
                f"invalid config: start_hub and/or end_hub missing"
            )
        zones_connections = set()
        for zone1, zone2 in  self.connection_zones:
                zones_connections.add(zone1)
                zones_connections.add(zone2)
        if not zones_connections <= self.list_zones:
            raise ValueError(
                f"connections have zones that are not defined,"
                f" invalid connection_zone(s): {zones_connections - self.list_zones}"
            )
    def _detect_line_type(self, line, index) -> str:
        if line.startswith("nb_drones"):
            return "nb_drones"
        elif line.startswith("start_hub"):
            return "start_hub"
        elif line.startswith("end_hub"):
            return "end_hub"
        elif line.startswith("connection"):
            return "connection"
        elif line.startswith("hub"):
            return "hub"
        else:
            raise ValueError(f"invalid config at line {index} with content {line}\n")

    # nb_drones: 5
    # start_hub: hub 0 0 [color=green]
    # end_hub: goal 10 10 [color=yellow]
    # hub: roof1 3 4 [zone=restricted color=red]
    # hub: roof2 6 2 [zone=normal color=blue]
    # hub: corridorA 4 3 [zone=priority color=green max_drones=2]
    # hub: tunnelB 7 4 [zone=normal color=red]
    # hub: obstacleX 5 5 [zone=blocked color=gray]
    # connection: hub-roof1 [metadata]
    # connection: hub-corridorA
    # connection: roof1-roof2
    # connection: roof2-goal
    # connection: corridorA-tunnelB [max_link_capacity=2]
    # connection: tunnelB-goal
    # line start/end and normal hub