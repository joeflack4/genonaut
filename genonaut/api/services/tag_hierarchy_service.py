"""Service for tag hierarchy operations."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from genonaut.api.models.responses import TagHierarchyResponse, TagHierarchyNode, TagHierarchyMetadata


class TagHierarchyService:
    """Service for managing tag hierarchy operations."""

    def __init__(self):
        """Initialize the tag hierarchy service."""
        # Path to the hierarchy JSON file
        self._hierarchy_path = Path(__file__).parent.parent.parent / "ontologies" / "tags" / "data" / "hierarchy.json"
        self._cached_hierarchy: Optional[TagHierarchyResponse] = None
        self._cache_timestamp: Optional[datetime] = None

    def get_hierarchy(self, use_cache: bool = True) -> TagHierarchyResponse:
        """Get the complete tag hierarchy.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            TagHierarchyResponse with complete hierarchy data

        Raises:
            FileNotFoundError: If hierarchy file doesn't exist
            ValueError: If hierarchy file is invalid JSON
        """
        # Check if cache is valid
        if use_cache and self._is_cache_valid():
            return self._cached_hierarchy

        # Load from file
        hierarchy_data = self._load_hierarchy_file()

        # Parse and validate
        hierarchy_response = self._parse_hierarchy_data(hierarchy_data)

        # Update cache
        self._cached_hierarchy = hierarchy_response
        self._cache_timestamp = datetime.now(timezone.utc)

        return hierarchy_response

    def get_node_by_id(self, node_id: str) -> Optional[TagHierarchyNode]:
        """Get a specific node by its ID.

        Args:
            node_id: The node identifier

        Returns:
            TagHierarchyNode if found, None otherwise
        """
        hierarchy = self.get_hierarchy()

        for node in hierarchy.nodes:
            if node.id == node_id:
                return node

        return None

    def get_children(self, parent_id: str) -> List[TagHierarchyNode]:
        """Get all direct children of a parent node.

        Args:
            parent_id: The parent node identifier

        Returns:
            List of child nodes
        """
        hierarchy = self.get_hierarchy()

        children = []
        for node in hierarchy.nodes:
            if node.parent == parent_id:
                children.append(node)

        return children

    def get_root_nodes(self) -> List[TagHierarchyNode]:
        """Get all root nodes (nodes without parents).

        Returns:
            List of root nodes
        """
        hierarchy = self.get_hierarchy()

        roots = []
        for node in hierarchy.nodes:
            if node.parent is None:
                roots.append(node)

        return roots

    def get_path_to_root(self, node_id: str) -> List[TagHierarchyNode]:
        """Get the path from a node to its root.

        Args:
            node_id: The starting node identifier

        Returns:
            List of nodes from the given node to root (inclusive)
        """
        hierarchy = self.get_hierarchy()
        path = []

        current_id = node_id
        visited = set()  # Prevent infinite loops

        while current_id is not None and current_id not in visited:
            visited.add(current_id)

            # Find current node
            current_node = None
            for node in hierarchy.nodes:
                if node.id == current_id:
                    current_node = node
                    break

            if current_node is None:
                break  # Node not found

            path.append(current_node)
            current_id = current_node.parent

        return path

    def invalidate_cache(self) -> None:
        """Invalidate the cached hierarchy data."""
        self._cached_hierarchy = None
        self._cache_timestamp = None

    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid.

        Returns:
            True if cache is valid, False otherwise
        """
        if self._cached_hierarchy is None or self._cache_timestamp is None:
            return False

        # Check if file has been modified since cache
        try:
            file_mtime = datetime.fromtimestamp(
                self._hierarchy_path.stat().st_mtime,
                tz=timezone.utc
            )
            return file_mtime <= self._cache_timestamp
        except OSError:
            # File doesn't exist or can't be accessed
            return False

    def _load_hierarchy_file(self) -> Dict:
        """Load hierarchy data from JSON file.

        Returns:
            Dictionary with hierarchy data

        Raises:
            FileNotFoundError: If hierarchy file doesn't exist
            ValueError: If JSON is invalid
        """
        if not self._hierarchy_path.exists():
            raise FileNotFoundError(f"Hierarchy file not found: {self._hierarchy_path}")

        try:
            with open(self._hierarchy_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in hierarchy file: {e}")

    def _parse_hierarchy_data(self, data: Dict) -> TagHierarchyResponse:
        """Parse raw hierarchy data into response model.

        Args:
            data: Raw hierarchy dictionary

        Returns:
            TagHierarchyResponse instance

        Raises:
            ValueError: If data structure is invalid
        """
        if "nodes" not in data or "metadata" not in data:
            raise ValueError("Invalid hierarchy data: missing 'nodes' or 'metadata'")

        # Parse nodes
        nodes = []
        for node_data in data["nodes"]:
            if not isinstance(node_data, dict):
                continue

            try:
                node = TagHierarchyNode(
                    id=node_data["id"],
                    name=node_data["name"],
                    parent=node_data.get("parent")
                )
                nodes.append(node)
            except (KeyError, TypeError) as e:
                # Skip invalid nodes but continue processing
                continue

        # Parse metadata
        metadata_dict = data["metadata"]
        try:
            # Convert ISO timestamp to datetime
            last_updated_str = metadata_dict.get("lastUpdated", metadata_dict.get("last_updated"))
            if isinstance(last_updated_str, str):
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            else:
                last_updated = datetime.now(timezone.utc)

            metadata = TagHierarchyMetadata(
                totalNodes=metadata_dict.get("totalNodes", len(nodes)),
                totalRelationships=metadata_dict.get("totalRelationships", 0),
                rootCategories=metadata_dict.get("rootCategories", 0),
                lastUpdated=last_updated,
                format=metadata_dict.get("format", "flat_array"),
                version=metadata_dict.get("version", "1.0")
            )
        except (KeyError, TypeError, ValueError) as e:
            # Create default metadata if parsing fails
            metadata = TagHierarchyMetadata(
                totalNodes=len(nodes),
                totalRelationships=len([n for n in nodes if n.parent is not None]),
                rootCategories=len([n for n in nodes if n.parent is None]),
                lastUpdated=datetime.now(timezone.utc),
                format="flat_array",
                version="1.0"
            )

        return TagHierarchyResponse(
            nodes=nodes,
            metadata=metadata
        )