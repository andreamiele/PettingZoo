from __future__ import annotations

from typing import Any
from warnings import warn


class AgentSelector:
    """Outputs an agent in the given order whenever agent_select is called.

    Can reinitialize to a new order.

    Example:
        >>> from pettingzoo.utils import AgentSelector
        >>> agent_selector = AgentSelector(agent_order=["player1", "player2"])
        >>> agent_selector.reset()
        'player1'
        >>> agent_selector.next()
        'player2'
        >>> agent_selector.is_last()
        True
        >>> agent_selector.reinit(agent_order=["player2", "player1"])
        >>> agent_selector.next()
        'player2'
        >>> agent_selector.is_last()
        False
    """

    def __init__(self, agent_order: list[Any]):
        self.reinit(agent_order)

    def reinit(self, agent_order: list[Any]) -> None:
        """Reinitialize to a new order."""
        self.agent_order = agent_order
        self._current_agent = 0
        self.selected_agent = 0

    def reset(self) -> Any:
        """Reset to the original order."""
        self.reinit(self.agent_order)
        return self.next()

    def next(self) -> Any:
        """Get the next agent."""
        self._current_agent = (self._current_agent + 1) % len(self.agent_order)
        self.selected_agent = self.agent_order[self._current_agent - 1]
        return self.selected_agent

    def is_last(self) -> bool:
        """Check if the current agent is the last agent in the cycle."""
        return self.selected_agent == self.agent_order[-1]

    def is_first(self) -> bool:
        """Check if the current agent is the first agent in the cycle."""
        return self.selected_agent == self.agent_order[0]

    def __eq__(self, other: AgentSelector) -> bool:
        if not isinstance(other, AgentSelector):
            return NotImplemented

        return (
            self.agent_order == other.agent_order
            and self._current_agent == other._current_agent
            and self.selected_agent == other.selected_agent
        )


class agent_selector(AgentSelector):
    """Deprecated version of AgentSelector. Use that instead."""

    def __init__(self, *args, **kwargs):
        warn(
            "agent_selector is deprecated, please use AgentSelector",
            DeprecationWarning,
        )
        super().__init__(*args, **kwargs)


class AgentSelector2:
    """Selects the next agent based on manager_act and coordination_act flags.

    Can dynamically switch between the manager and all workstations + coordination.

    Example:
        >>> agent_selector = AgentSelector(agent_order=["manager", "workstation_0", "workstation_1", "coordination"])
        >>> agent_selector.reset()
        'manager'
        >>> agent_selector.next(manager_act=True)
        'workstation_0'
        >>> agent_selector.next(manager_act=False, coordination_act=True)
        'coordination'
    """

    def __init__(self, agent_order: list[str]):
        self.agent_order = agent_order
        self.manager_index = agent_order.index("manager")  # Fixed index for manager
        self.workstation_indices = [
            i for i, agent in enumerate(agent_order) if agent.startswith("workstation")
        ]
        self.coordination_index = agent_order.index(
            "coordination"
        )  # Fixed index for coordination
        self._current_index = 0
        self.selected_agent = None

    def reset(self) -> str:
        """Reset to the initial state with the manager acting first."""
        self._current_index = 0
        return self.agent_order[self.manager_index]  # Always start with manager

    def next(self, manager_act, coordination_act, active_agents):
        """Get the next agent based on manager_act and coordination_act flags."""
        if manager_act and "manager" in active_agents:
            # Manager acts and cycle resets
            self.selected_agent = self.agent_order[self.manager_index]
            self._current_index = 0  # Reset cycle
        else:
            # Cycle through workstations and coordination agent indefinitely
            total_agents_in_cycle = (
                len(self.workstation_indices) + 1
            )  # Workstations + coordination
            cycle_index = self._current_index % total_agents_in_cycle

            if cycle_index < len(self.workstation_indices):
                # Select next workstation
                workstation_idx = self.workstation_indices[cycle_index]
                self.selected_agent = self.agent_order[workstation_idx]
            else:
                # Select coordination agent
                self.selected_agent = self.agent_order[self.coordination_index]

            self._current_index += 1  # Move to next agent in cycle

        return self.selected_agent

    def is_last(self) -> bool:
        """Check if the current agent is the last in the coordination phase (coordination agent)."""
        return self.selected_agent == self.agent_order[self.coordination_index]

    def is_first(self) -> bool:
        """Check if the current agent is the first agent in the cycle (manager)."""
        return self.selected_agent == self.agent_order[self.manager_index]

    def reinit(self, agent_order: list[str]) -> None:
        """Reinitialize to a new order."""
        self.agent_order = agent_order
        self.manager_index = agent_order.index("manager")
        self.workstation_indices = [
            i for i, agent in enumerate(agent_order) if agent.startswith("workstation")
        ]
        self.coordination_index = agent_order.index("coordination")
        self._current_index = 0
        self.selected_agent = None

    def __eq__(self, other: "AgentSelector2") -> bool:
        if not isinstance(other, AgentSelector2):
            return NotImplemented

        return (
            self.agent_order == other.agent_order
            and self._current_index == other._current_index
            and self.selected_agent == other.selected_agent
        )


class AgentSelector3:
    """Selects the next agent based on manager_act, coordination_act, and workstation_act flags.

    Can dynamically switch between the manager and all active workstations + coordination.

    Example:
        >>> agent_selector = AgentSelector2(agent_order=["manager", "workstation_0", "workstation_1", "coordination"])
        >>> agent_selector.reset()
        'manager'
        >>> agent_selector.next(manager_act=True, coordination_act=False, active_agents=["manager", "workstation_0", "workstation_1"], workstation_act=[1, 0])
        'manager'
        >>> agent_selector.next(manager_act=False, coordination_act=True, active_agents=["manager", "workstation_0", "workstation_1"], workstation_act=[1, 0])
        'workstation_0'
    """

    def __init__(self, agent_order: list[str]):
        self.agent_order = agent_order
        self.manager_index = agent_order.index("manager")  # Fixed index for manager
        self.workstation_indices = [
            i for i, agent in enumerate(agent_order) if agent.startswith("workstation")
        ]
        self.coordination_index = agent_order.index(
            "coordination"
        )  # Fixed index for coordination
        self._current_index = 0
        self.selected_agent = None
        self._previous_agents_in_cycle_indices = []

    def reset(self) -> str:
        """Reset to the initial state with the manager acting first."""
        self._current_index = 0
        self.selected_agent = self.agent_order[self.manager_index]
        self._previous_agents_in_cycle_indices = []
        return self.selected_agent  # Always start with manager

    def next(self, manager_act, workstation_act):
        """Get the next agent based on manager_act and workstation_act flags."""
        if manager_act:
            # Manager acts and cycle resets
            self.selected_agent = self.agent_order[self.manager_index]
            self._current_index = 0  # Reset cycle
            self._previous_agents_in_cycle_indices = []
        else:
            # Determine active workstations
            active_workstation_indices = [
                idx
                for i, idx in enumerate(self.workstation_indices)
                if workstation_act[i] == 1
            ]

            # Only add the coordination agent if there are active workstations
            if active_workstation_indices:
                agents_in_cycle_indices = active_workstation_indices + [
                    self.coordination_index
                ]
            else:
                agents_in_cycle_indices = (
                    self.workstation_indices
                    + [self.coordination_index]
                    + [self.manager_index]
                )

            if not agents_in_cycle_indices:
                # No agents to act
                self.selected_agent = None
                return None

            # Reset _current_index if the agents in cycle have changed
            if agents_in_cycle_indices != self._previous_agents_in_cycle_indices:
                self._current_index = 0
                self._previous_agents_in_cycle_indices = agents_in_cycle_indices.copy()

            # Cycle through the agents
            cycle_length = len(agents_in_cycle_indices)
            cycle_index = self._current_index % cycle_length
            selected_idx = agents_in_cycle_indices[cycle_index]
            self.selected_agent = self.agent_order[selected_idx]

            self._current_index += 1  # Move to next agent in cycle

        return self.selected_agent

    def is_last(self) -> bool:
        """Check if the current agent is the last in the coordination phase (coordination agent)."""
        return self.selected_agent == "coordination"

    def is_first(self) -> bool:
        """Check if the current agent is the first agent in the cycle (manager)."""
        return self.selected_agent == "manager"

    def reinit(self, agent_order: list[str]) -> None:
        """Reinitialize to a new order."""
        self.agent_order = agent_order
        self.manager_index = agent_order.index("manager")
        self.workstation_indices = [
            i for i, agent in enumerate(agent_order) if agent.startswith("workstation")
        ]
        self.coordination_index = agent_order.index("coordination")
        self._current_index = 0
        self.selected_agent = None
        self._previous_agents_in_cycle_indices = []

    def __eq__(self, other: "AgentSelector2") -> bool:
        if not isinstance(other, AgentSelector2):
            return NotImplemented

        return (
            self.agent_order == other.agent_order
            and self._current_index == other._current_index
            and self.selected_agent == other.selected_agent
        )
