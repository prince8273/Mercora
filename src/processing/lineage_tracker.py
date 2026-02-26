"""Data lineage tracking system"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4, UUID
from enum import Enum


class TransformationType(str, Enum):
    """Types of data transformations"""
    VALIDATION = "validation"
    NORMALIZATION = "normalization"
    DEDUPLICATION = "deduplication"
    SPAM_FILTERING = "spam_filtering"
    MISSING_DATA_HANDLING = "missing_data_handling"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"


class LineageNode:
    """Represents a node in the data lineage graph"""
    
    def __init__(
        self,
        node_id: str,
        data_type: str,
        source: str,
        timestamp: datetime,
        record_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.data_type = data_type
        self.source = source
        self.timestamp = timestamp
        self.record_count = record_count
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'node_id': self.node_id,
            'data_type': self.data_type,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'record_count': self.record_count,
            'metadata': self.metadata
        }


class LineageEdge:
    """Represents a transformation edge in the lineage graph"""
    
    def __init__(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        transformation_type: TransformationType,
        timestamp: datetime,
        records_in: int,
        records_out: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.edge_id = edge_id
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.transformation_type = transformation_type
        self.timestamp = timestamp
        self.records_in = records_in
        self.records_out = records_out
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'edge_id': self.edge_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'transformation_type': self.transformation_type.value,
            'timestamp': self.timestamp.isoformat(),
            'records_in': self.records_in,
            'records_out': self.records_out,
            'metadata': self.metadata
        }


class LineageTracker:
    """
    Tracks data lineage through the processing pipeline.
    
    Maintains a directed acyclic graph (DAG) of data transformations,
    allowing traceability from raw data to final processed records.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize lineage tracker.
        
        Args:
            tenant_id: Tenant UUID
        """
        self.tenant_id = tenant_id
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: Dict[str, LineageEdge] = {}
        self.current_pipeline_id = None
    
    def start_pipeline(self, pipeline_name: str) -> str:
        """
        Start tracking a new pipeline execution.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline execution ID
        """
        self.current_pipeline_id = str(uuid4())
        return self.current_pipeline_id
    
    def track_ingestion(
        self,
        source: str,
        data_type: str,
        record_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track data ingestion (creates a source node).
        
        Args:
            source: Data source name
            data_type: Type of data (product, review, etc.)
            record_count: Number of records ingested
            metadata: Additional metadata
            
        Returns:
            Node ID
        """
        node_id = f"ingestion_{str(uuid4())[:8]}"
        
        node = LineageNode(
            node_id=node_id,
            data_type=data_type,
            source=source,
            timestamp=datetime.utcnow(),
            record_count=record_count,
            metadata={
                **(metadata or {}),
                'pipeline_id': self.current_pipeline_id,
                'stage': 'ingestion'
            }
        )
        
        self.nodes[node_id] = node
        return node_id
    
    def track_transformation(
        self,
        source_node_id: str,
        transformation_type: TransformationType,
        records_in: int,
        records_out: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a data transformation.
        
        Args:
            source_node_id: ID of source node
            transformation_type: Type of transformation
            records_in: Number of input records
            records_out: Number of output records
            metadata: Additional metadata (e.g., validation errors, dedup stats)
            
        Returns:
            Target node ID
        """
        if source_node_id not in self.nodes:
            raise ValueError(f"Source node {source_node_id} not found")
        
        source_node = self.nodes[source_node_id]
        
        # Create target node
        target_node_id = f"{transformation_type.value}_{str(uuid4())[:8]}"
        target_node = LineageNode(
            node_id=target_node_id,
            data_type=source_node.data_type,
            source=source_node.source,
            timestamp=datetime.utcnow(),
            record_count=records_out,
            metadata={
                **(metadata or {}),
                'pipeline_id': self.current_pipeline_id,
                'stage': transformation_type.value
            }
        )
        self.nodes[target_node_id] = target_node
        
        # Create edge
        edge_id = f"edge_{str(uuid4())[:8]}"
        edge = LineageEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            transformation_type=transformation_type,
            timestamp=datetime.utcnow(),
            records_in=records_in,
            records_out=records_out,
            metadata=metadata or {}
        )
        self.edges[edge_id] = edge
        
        return target_node_id
    
    def get_lineage_for_node(self, node_id: str) -> Dict[str, Any]:
        """
        Get complete lineage for a specific node.
        
        Args:
            node_id: Node ID to trace
            
        Returns:
            Lineage information including ancestors and transformations
        """
        if node_id not in self.nodes:
            return {'error': f'Node {node_id} not found'}
        
        # Find all ancestor nodes
        ancestors = self._find_ancestors(node_id)
        
        # Find all edges in the lineage path
        lineage_edges = [
            edge for edge in self.edges.values()
            if edge.target_node_id in ancestors or edge.target_node_id == node_id
        ]
        
        return {
            'node': self.nodes[node_id].to_dict(),
            'ancestors': [self.nodes[nid].to_dict() for nid in ancestors],
            'transformations': [edge.to_dict() for edge in lineage_edges],
            'total_transformations': len(lineage_edges)
        }
    
    def get_pipeline_lineage(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get complete lineage for a pipeline execution.
        
        Args:
            pipeline_id: Pipeline execution ID
            
        Returns:
            Complete pipeline lineage
        """
        # Find all nodes in this pipeline
        pipeline_nodes = [
            node for node in self.nodes.values()
            if node.metadata.get('pipeline_id') == pipeline_id
        ]
        
        # Find all edges in this pipeline
        pipeline_node_ids = {node.node_id for node in pipeline_nodes}
        pipeline_edges = [
            edge for edge in self.edges.values()
            if edge.source_node_id in pipeline_node_ids
        ]
        
        # Calculate statistics
        total_records_in = sum(
            node.record_count for node in pipeline_nodes
            if node.metadata.get('stage') == 'ingestion'
        )
        
        final_nodes = [
            node for node in pipeline_nodes
            if not any(edge.source_node_id == node.node_id for edge in pipeline_edges)
        ]
        total_records_out = sum(node.record_count for node in final_nodes)
        
        return {
            'pipeline_id': pipeline_id,
            'nodes': [node.to_dict() for node in pipeline_nodes],
            'edges': [edge.to_dict() for edge in pipeline_edges],
            'statistics': {
                'total_nodes': len(pipeline_nodes),
                'total_transformations': len(pipeline_edges),
                'records_in': total_records_in,
                'records_out': total_records_out,
                'data_loss': total_records_in - total_records_out,
                'retention_rate': (
                    total_records_out / total_records_in
                    if total_records_in > 0 else 0.0
                )
            }
        }
    
    def get_all_pipelines(self) -> List[Dict[str, Any]]:
        """
        Get summary of all tracked pipelines.
        
        Returns:
            List of pipeline summaries
        """
        pipeline_ids = set(
            node.metadata.get('pipeline_id')
            for node in self.nodes.values()
            if node.metadata.get('pipeline_id')
        )
        
        summaries = []
        for pipeline_id in pipeline_ids:
            lineage = self.get_pipeline_lineage(pipeline_id)
            summaries.append({
                'pipeline_id': pipeline_id,
                'node_count': lineage['statistics']['total_nodes'],
                'transformation_count': lineage['statistics']['total_transformations'],
                'records_in': lineage['statistics']['records_in'],
                'records_out': lineage['statistics']['records_out'],
                'retention_rate': lineage['statistics']['retention_rate']
            })
        
        return summaries
    
    def _find_ancestors(self, node_id: str) -> List[str]:
        """
        Find all ancestor nodes for a given node.
        
        Args:
            node_id: Node ID
            
        Returns:
            List of ancestor node IDs
        """
        ancestors = []
        to_visit = [node_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Find edges pointing to current node
            parent_edges = [
                edge for edge in self.edges.values()
                if edge.target_node_id == current
            ]
            
            for edge in parent_edges:
                if edge.source_node_id not in visited:
                    ancestors.append(edge.source_node_id)
                    to_visit.append(edge.source_node_id)
        
        return ancestors
    
    def export_lineage_graph(self) -> Dict[str, Any]:
        """
        Export complete lineage graph for visualization.
        
        Returns:
            Graph data in format suitable for visualization
        """
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'metadata': {
                'tenant_id': str(self.tenant_id),
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'export_timestamp': datetime.utcnow().isoformat()
            }
        }
