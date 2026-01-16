/**
 * Graph Types
 * ============
 * 
 * TypeScript interfaces for entity graph visualization, representing
 * relationships between wallets, agents, timelines, evidence, sabotage events,
 * and paradoxes.
 */

/**
 * Graph Node Type
 * 
 * Types of nodes that can appear in the entity graph.
 */
export type GraphNodeType =
  | 'wallet'
  | 'agent'
  | 'timeline'
  | 'evidence'
  | 'sabotage'
  | 'paradox';

/**
 * Graph Edge Relation
 * 
 * Types of relationships between graph nodes.
 */
export type GraphEdgeRelation =
  | 'holds_position'
  | 'placed_wing_flap'
  | 'founded'
  | 'benefited'
  | 'triggered'
  | 'contradicted'
  | 'linked';

/**
 * GraphNode
 * 
 * Represents a node in the entity graph.
 */
export interface GraphNode {
  /** Unique node identifier */
  id: string;
  
  /** Type of node */
  type: GraphNodeType;
  
  /** Human-readable label for the node */
  label: string;
  
  /** Additional metadata (optional) */
  meta?: Record<string, any>;
}

/**
 * GraphEdge
 * 
 * Represents an edge (relationship) between two nodes in the graph.
 */
export interface GraphEdge {
  /** Unique edge identifier */
  id: string;
  
  /** Source node ID */
  from: string;
  
  /** Target node ID */
  to: string;
  
  /** Type of relationship */
  relation: GraphEdgeRelation;
  
  /** Edge weight (optional, for visualization) */
  weight?: number;
}

/**
 * EntityGraph
 * 
 * Complete entity graph containing nodes and edges.
 */
export interface EntityGraph {
  /** Array of graph nodes */
  nodes: GraphNode[];
  
  /** Array of graph edges */
  edges: GraphEdge[];
}
