"""
display.py
----------
Handles the simulation output as specified in VII.5.

Rules implemented:
- Each simulation turn is represented by a single line.
- A line lists every drone movement that occurs during that turn,
  space-separated.
- Movement format:
    * D<ID>-<zone>        when the drone enters a zone
    * D<ID>-<connection>  when the drone is still in flight toward a
                          restricted zone (occupying the connection)
- Drones that do not move in a given turn are excluded from the line.
- Delivered drones (those that have reached the end zone) are no longer
  tracked and should not appear in subsequent turns.
- The caller is responsible for stopping the simulation once every drone
  has been delivered. $TOUNDER
"""

from __future__ import annotations
from typing import Optional, Union

# Forward references to keep this module independent of the others.
# Replace these with real imports once the project is wired up:
#   from zone import Zone, Connection
#   from drone import Drone
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Zone, Connection, Drone


# A move is: (drone, destination), where destination is either a Zone
# (normal arrival) or a Connection (drone still in transit toward a
# restricted zone).
Move = tuple["Drone", Union["Zone", "Connection"]]


# ---------- ANSI colors (optional visual feedback) ----------------------

ANSI_COLORS: dict[str, str] = {
    "red":     "\033[31m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "cyan":    "\033[36m",
    "gray":    "\033[90m",
    "grey":    "\033[90m",
    "white":   "\033[37m",
}
ANSI_RESET: str = "\033[0m"


def _colorize(text: str, color: Optional[str], use_color: bool) -> str:
    """Wrap `text` with ANSI codes if a known color is requested."""
    if not use_color or color is None:
        return text
    code = ANSI_COLORS.get(color.lower())
    if code is None:
        return text
    return f"{code}{text}{ANSI_RESET}"


# ---------- Move formatting --------------------------------------------

def format_move(move: Move, use_color: bool = False) -> str:
    """
    Format a single move as 'D<ID>-<name>'.

    - If the destination is a Zone, <name> is the zone name.
    - If the destination is a Connection (drone in flight toward a
      restricted zone), <name> is built from the two endpoints
      as 'zoneA-zoneB'.
    """
    drone, destination = move

    # Zone arrival
    if hasattr(destination, "name"):
        label = f"D{drone.id}-{destination.name}"
        color = getattr(destination, "color", None)
        return _colorize(label, color, use_color)

    # Connection (in-flight toward a restricted zone)
    if hasattr(destination, "a") and hasattr(destination, "b"):
        conn_name = f"{destination.a.name}-{destination.b.name}"
        return f"D{drone.id}-{conn_name}"

    raise TypeError(
        f"Unknown move destination type: {type(destination).__name__}"
    )


def format_turn(moves: list[Move], use_color: bool = False) -> str:
    """
    Build the line for a single turn: space-separated moves.

    Drones that do not move this turn must NOT appear in `moves`,
    so they are naturally omitted from the output.
    Returns an empty string if no drone moved this turn.
    """
    return " ".join(format_move(m, use_color) for m in moves)


# ---------- Printing ----------------------------------------------------

def print_turn(moves: list[Move], use_color: bool = False) -> None:
    """
    Print one turn's worth of movements.

    Per VII.5, turns where no drone moves still belong to the simulation
    timeline; we print an empty line so each line == one turn.
    """
    print(format_turn(moves, use_color))


def print_simulation(
    turns: list[list[Move]],
    use_color: bool = False,
) -> None:
    """
    Print the full simulation: one line per turn, in order.

    `turns[i]` is the list of moves that happened during turn i.
    The simulation is expected to end on the turn where the last
    drone reaches the end zone.
    """
    for moves in turns:
        print_turn(moves, use_color)


