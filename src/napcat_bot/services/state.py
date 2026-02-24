import asyncio
from dataclasses import dataclass, field


@dataclass
class RuntimeState:
    trigger_mode: str = "at"  # "at" or "all"
    group_locks: dict[int, asyncio.Lock] = field(default_factory=dict)

    def lock_for_group(self, group_id: int) -> asyncio.Lock:
        if group_id not in self.group_locks:
            self.group_locks[group_id] = asyncio.Lock()
        return self.group_locks[group_id]