import hashlib
from typing import List
from collections import defaultdict


class LoadBalancer:
    """Load balancer for distributing requests across multiple backends"""

    def __init__(self):
        self.round_robin_index = defaultdict(int)
        self.connection_counts = defaultdict(int)

    def select_backend(
        self, backends: List[str], strategy: str = "round_robin", client_ip: str = None
    ) -> str:
        """
        Select a backend URL based on the load balancing strategy.

        Strategies:
        - round_robin: Distribute requests evenly across backends
        - least_connections: Send to backend with fewest active connections
        - ip_hash: Consistent hashing based on client IP
        """

        if not backends:
            raise ValueError("No backend URLs provided")

        if len(backends) == 1:
            return backends[0]

        if strategy == "round_robin":
            return self._round_robin(backends)
        elif strategy == "least_connections":
            return self._least_connections(backends)
        elif strategy == "ip_hash":
            if not client_ip:
                # Fall back to round robin if no IP provided
                return self._round_robin(backends)
            return self._ip_hash(backends, client_ip)
        else:
            # Default to round robin
            return self._round_robin(backends)

    def _round_robin(self, backends: List[str]) -> str:
        """Round-robin load balancing"""

        backends_key = "|".join(sorted(backends))
        index = self.round_robin_index[backends_key]
        selected = backends[index % len(backends)]

        # Increment for next request
        self.round_robin_index[backends_key] = (index + 1) % len(backends)

        return selected

    def _least_connections(self, backends: List[str]) -> str:
        """Least connections load balancing"""

        # Find backend with minimum connections
        min_connections = min(
            (self.connection_counts[backend], backend) for backend in backends
        )
        return min_connections[1]

    def _ip_hash(self, backends: List[str], client_ip: str) -> str:
        """IP hash load balancing (consistent hashing)"""

        # Hash the IP address
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)

        # Select backend based on hash
        index = hash_value % len(backends)
        return backends[index]

    def increment_connections(self, backend: str):
        """Increment connection count for a backend"""
        self.connection_counts[backend] += 1

    def decrement_connections(self, backend: str):
        """Decrement connection count for a backend"""
        if self.connection_counts[backend] > 0:
            self.connection_counts[backend] -= 1

    def reset_connections(self):
        """Reset all connection counts"""
        self.connection_counts.clear()
