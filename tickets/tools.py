from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    LOWEST = "Lowest"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    HIGHEST = "Highest"

@dataclass
class Ticket:
    labels: list[str]
    summary: str
    description: str
    priority: Priority
    location: str

    project_key: str = "DCM"
    issue_type: str = "Task"

