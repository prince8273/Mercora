"""Tests for lineage tracker"""
import pytest
from uuid import uuid4
from src.processing.lineage_tracker import (
    LineageTracker,
    TransformationType,
    LineageNode,
    LineageEdge
)


def test_lineage_tracker_initialization():
    """Test lineage tracker initialization"""
    tenant_id = uuid4()
    tracker = LineageTracker(tenant_id)
    
    assert tracker.tenant_id == tenant_id
    assert len(tracker.nodes) == 0
    assert len(tracker.edges) == 0


def test_start_pipeline():
    """Test starting a pipeline"""
    tracker = LineageTracker(uuid4())
    
    pipeline_id = tracker.start_pipeline("test_pipeline")
    
    assert pipeline_id is not None
    assert tracker.current_pipeline_id == pipeline_id


def test_track_ingestion():
    """Test tracking data ingestion"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    node_id = tracker.track_ingestion(
        source="test_source",
        data_type="product",
        record_count=100,
        metadata={'test': 'data'}
    )
    
    assert node_id in tracker.nodes
    node = tracker.nodes[node_id]
    assert node.data_type == "product"
    assert node.record_count == 100
    assert node.source == "test_source"


def test_track_transformation():
    """Test tracking a transformation"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    # Create source node
    source_id = tracker.track_ingestion(
        source="test_source",
        data_type="product",
        record_count=100
    )
    
    # Track transformation
    target_id = tracker.track_transformation(
        source_node_id=source_id,
        transformation_type=TransformationType.VALIDATION,
        records_in=100,
        records_out=90,
        metadata={'rejected': 10}
    )
    
    assert target_id in tracker.nodes
    assert len(tracker.edges) == 1
    
    # Check edge
    edge = list(tracker.edges.values())[0]
    assert edge.source_node_id == source_id
    assert edge.target_node_id == target_id
    assert edge.transformation_type == TransformationType.VALIDATION
    assert edge.records_in == 100
    assert edge.records_out == 90


def test_track_multiple_transformations():
    """Test tracking multiple transformations in sequence"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    # Ingestion
    node1 = tracker.track_ingestion("source", "product", 100)
    
    # Validation
    node2 = tracker.track_transformation(
        node1, TransformationType.VALIDATION, 100, 90
    )
    
    # Normalization
    node3 = tracker.track_transformation(
        node2, TransformationType.NORMALIZATION, 90, 90
    )
    
    # Deduplication
    node4 = tracker.track_transformation(
        node3, TransformationType.DEDUPLICATION, 90, 85
    )
    
    assert len(tracker.nodes) == 4
    assert len(tracker.edges) == 3


def test_get_lineage_for_node():
    """Test getting lineage for a specific node"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    node1 = tracker.track_ingestion("source", "product", 100)
    node2 = tracker.track_transformation(
        node1, TransformationType.VALIDATION, 100, 90
    )
    node3 = tracker.track_transformation(
        node2, TransformationType.NORMALIZATION, 90, 90
    )
    
    lineage = tracker.get_lineage_for_node(node3)
    
    assert 'node' in lineage
    assert 'ancestors' in lineage
    assert 'transformations' in lineage
    assert len(lineage['ancestors']) == 2  # node1 and node2


def test_get_pipeline_lineage():
    """Test getting complete pipeline lineage"""
    tracker = LineageTracker(uuid4())
    pipeline_id = tracker.start_pipeline("test_pipeline")
    
    node1 = tracker.track_ingestion("source", "product", 100)
    node2 = tracker.track_transformation(
        node1, TransformationType.VALIDATION, 100, 90
    )
    
    lineage = tracker.get_pipeline_lineage(pipeline_id)
    
    assert lineage['pipeline_id'] == pipeline_id
    assert len(lineage['nodes']) == 2
    assert len(lineage['edges']) == 1
    assert 'statistics' in lineage
    assert lineage['statistics']['records_in'] == 100
    assert lineage['statistics']['records_out'] == 90


def test_get_all_pipelines():
    """Test getting all pipeline summaries"""
    tracker = LineageTracker(uuid4())
    
    # Pipeline 1
    pipeline1 = tracker.start_pipeline("pipeline1")
    node1 = tracker.track_ingestion("source1", "product", 100)
    tracker.track_transformation(
        node1, TransformationType.VALIDATION, 100, 90
    )
    
    # Pipeline 2
    pipeline2 = tracker.start_pipeline("pipeline2")
    node2 = tracker.track_ingestion("source2", "review", 50)
    tracker.track_transformation(
        node2, TransformationType.SPAM_FILTERING, 50, 45
    )
    
    summaries = tracker.get_all_pipelines()
    
    assert len(summaries) == 2
    assert all('pipeline_id' in s for s in summaries)
    assert all('retention_rate' in s for s in summaries)


def test_export_lineage_graph():
    """Test exporting lineage graph"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    node1 = tracker.track_ingestion("source", "product", 100)
    node2 = tracker.track_transformation(
        node1, TransformationType.VALIDATION, 100, 90
    )
    
    graph = tracker.export_lineage_graph()
    
    assert 'nodes' in graph
    assert 'edges' in graph
    assert 'metadata' in graph
    assert len(graph['nodes']) == 2
    assert len(graph['edges']) == 1


def test_transformation_invalid_source():
    """Test transformation with invalid source node"""
    tracker = LineageTracker(uuid4())
    tracker.start_pipeline("test_pipeline")
    
    with pytest.raises(ValueError):
        tracker.track_transformation(
            "invalid_node_id",
            TransformationType.VALIDATION,
            100,
            90
        )


def test_lineage_node_to_dict():
    """Test LineageNode to_dict conversion"""
    from datetime import datetime
    
    node = LineageNode(
        node_id="test_node",
        data_type="product",
        source="test_source",
        timestamp=datetime.utcnow(),
        record_count=100,
        metadata={'key': 'value'}
    )
    
    node_dict = node.to_dict()
    
    assert node_dict['node_id'] == "test_node"
    assert node_dict['data_type'] == "product"
    assert node_dict['record_count'] == 100
    assert 'timestamp' in node_dict


def test_lineage_edge_to_dict():
    """Test LineageEdge to_dict conversion"""
    from datetime import datetime
    
    edge = LineageEdge(
        edge_id="test_edge",
        source_node_id="node1",
        target_node_id="node2",
        transformation_type=TransformationType.VALIDATION,
        timestamp=datetime.utcnow(),
        records_in=100,
        records_out=90,
        metadata={'rejected': 10}
    )
    
    edge_dict = edge.to_dict()
    
    assert edge_dict['edge_id'] == "test_edge"
    assert edge_dict['source_node_id'] == "node1"
    assert edge_dict['target_node_id'] == "node2"
    assert edge_dict['transformation_type'] == "validation"
    assert edge_dict['records_in'] == 100
    assert edge_dict['records_out'] == 90


def test_pipeline_statistics():
    """Test pipeline statistics calculation"""
    tracker = LineageTracker(uuid4())
    pipeline_id = tracker.start_pipeline("test_pipeline")
    
    # Simulate data loss through transformations
    node1 = tracker.track_ingestion("source", "product", 1000)
    node2 = tracker.track_transformation(
        node1, TransformationType.VALIDATION, 1000, 900
    )
    node3 = tracker.track_transformation(
        node2, TransformationType.DEDUPLICATION, 900, 850
    )
    
    lineage = tracker.get_pipeline_lineage(pipeline_id)
    stats = lineage['statistics']
    
    assert stats['records_in'] == 1000
    assert stats['records_out'] == 850
    assert stats['data_loss'] == 150
    assert stats['retention_rate'] == 0.85
