"""Tag hierarchy API routes."""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Optional, List

from genonaut.api.models.responses import TagHierarchyResponse, TagHierarchyNode
from genonaut.api.services.tag_hierarchy_service import TagHierarchyService

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])

# Initialize service
tag_hierarchy_service = TagHierarchyService()


@router.get("/hierarchy", response_model=TagHierarchyResponse)
async def get_tag_hierarchy(
    format: str = Query("json", description="Response format (json, tsv)"),
    no_cache: bool = Query(False, description="Skip cache and reload from file")
):
    """Get the complete tag hierarchy.

    Returns the tag ontology in a structured format optimized for tree view components.
    Uses flat array format for optimal performance with frontend tree libraries.

    Args:
        format: Response format (currently only 'json' supported)
        no_cache: Whether to bypass cache and reload from file

    Returns:
        TagHierarchyResponse: Complete hierarchy with nodes and metadata

    Raises:
        HTTPException: If hierarchy data cannot be loaded or is invalid
    """
    if format not in ["json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}. Supported formats: json"
        )

    try:
        hierarchy = tag_hierarchy_service.get_hierarchy(use_cache=not no_cache)
        return hierarchy

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag hierarchy data not found. Please ensure the ontology has been generated."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid hierarchy data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tag hierarchy: {str(e)}"
        )


@router.get("/hierarchy/nodes/{node_id}", response_model=TagHierarchyNode)
async def get_tag_node(node_id: str):
    """Get a specific tag node by ID.

    Args:
        node_id: The tag identifier

    Returns:
        TagHierarchyNode: The requested node

    Raises:
        HTTPException: If node is not found
    """
    try:
        node = tag_hierarchy_service.get_node_by_id(node_id)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag node not found: {node_id}"
            )
        return node

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag node: {str(e)}"
        )


@router.get("/hierarchy/children/{parent_id}", response_model=List[TagHierarchyNode])
async def get_tag_children(parent_id: str):
    """Get all direct children of a parent tag.

    Args:
        parent_id: The parent tag identifier

    Returns:
        List[TagHierarchyNode]: List of child nodes

    Raises:
        HTTPException: If parent node is not found
    """
    try:
        # Verify parent exists
        parent = tag_hierarchy_service.get_node_by_id(parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent tag not found: {parent_id}"
            )

        children = tag_hierarchy_service.get_children(parent_id)
        return children

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag children: {str(e)}"
        )


@router.get("/hierarchy/roots", response_model=List[TagHierarchyNode])
async def get_root_tags():
    """Get all root tags (tags without parents).

    Returns:
        List[TagHierarchyNode]: List of root nodes
    """
    try:
        roots = tag_hierarchy_service.get_root_nodes()
        return roots

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get root tags: {str(e)}"
        )


@router.get("/hierarchy/path/{node_id}", response_model=List[TagHierarchyNode])
async def get_tag_path(node_id: str):
    """Get the path from a tag to its root.

    Args:
        node_id: The tag identifier

    Returns:
        List[TagHierarchyNode]: Path from node to root (node first, root last)

    Raises:
        HTTPException: If node is not found
    """
    try:
        # Verify node exists
        node = tag_hierarchy_service.get_node_by_id(node_id)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag node not found: {node_id}"
            )

        path = tag_hierarchy_service.get_path_to_root(node_id)
        return path

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag path: {str(e)}"
        )


@router.post("/hierarchy/refresh")
async def refresh_tag_hierarchy():
    """Refresh tag hierarchy cache.

    Forces a reload of the hierarchy data from the file system.
    Useful after updating the ontology.

    Returns:
        dict: Success message with updated metadata
    """
    try:
        # Invalidate cache
        tag_hierarchy_service.invalidate_cache()

        # Reload hierarchy
        hierarchy = tag_hierarchy_service.get_hierarchy(use_cache=False)

        return {
            "message": "Tag hierarchy cache refreshed successfully",
            "metadata": hierarchy.metadata
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tag hierarchy: {str(e)}"
        )