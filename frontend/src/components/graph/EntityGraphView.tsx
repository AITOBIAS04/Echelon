import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ExternalLink, ArrowRight, ArrowLeft } from 'lucide-react';
import { getEntityGraph } from '../../api/graph';
import type { GraphNode, GraphEdge, GraphNodeType } from '../../types/graph';
import { useQuery } from '@tanstack/react-query';

/**
 * EntityGraphView Component
 * 
 * Graph explorer for visualizing entity relationships without external graph libraries.
 * Three-column layout: node list, node detail, edge list.
 */
export function EntityGraphView() {
  const navigate = useNavigate();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibleTypes, setVisibleTypes] = useState<Set<GraphNodeType>>(
    new Set(['wallet', 'agent', 'timeline', 'evidence', 'sabotage', 'paradox'])
  );

  // Fetch graph data
  const { data: graph, isLoading, error } = useQuery({
    queryKey: ['entityGraph', 'my'],
    queryFn: () => getEntityGraph('my'),
    staleTime: 30000, // 30 seconds
  });

  // Filter nodes by search and visible types
  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    
    return graph.nodes.filter((node) => {
      const matchesType = visibleTypes.has(node.type);
      const matchesSearch = searchQuery === '' || 
        node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [graph, visibleTypes, searchQuery]);

  // Group nodes by type
  const nodesByType = useMemo(() => {
    const grouped: Record<GraphNodeType, GraphNode[]> = {
      wallet: [],
      agent: [],
      timeline: [],
      evidence: [],
      sabotage: [],
      paradox: [],
    };

    filteredNodes.forEach((node) => {
      grouped[node.type].push(node);
    });

    return grouped;
  }, [filteredNodes]);

  // Get selected node
  const selectedNode = useMemo(() => {
    if (!graph || !selectedNodeId) return null;
    return graph.nodes.find((node) => node.id === selectedNodeId) || null;
  }, [graph, selectedNodeId]);

  // Get edges for selected node
  const nodeEdges = useMemo(() => {
    if (!graph || !selectedNodeId) return { incoming: [], outgoing: [] };

    const incoming: GraphEdge[] = [];
    const outgoing: GraphEdge[] = [];

    graph.edges.forEach((edge) => {
      if (edge.to === selectedNodeId) {
        incoming.push(edge);
      }
      if (edge.from === selectedNodeId) {
        outgoing.push(edge);
      }
    });

    return { incoming, outgoing };
  }, [graph, selectedNodeId]);

  // Get nodes connected to selected node
  const connectedNodes = useMemo(() => {
    if (!graph || !selectedNodeId) return new Map<string, GraphNode>();

    const connected = new Map<string, GraphNode>();
    
    nodeEdges.incoming.forEach((edge) => {
      const node = graph.nodes.find((n) => n.id === edge.from);
      if (node) connected.set(node.id, node);
    });
    
    nodeEdges.outgoing.forEach((edge) => {
      const node = graph.nodes.find((n) => n.id === edge.to);
      if (node) connected.set(node.id, node);
    });

    return connected;
  }, [graph, selectedNodeId, nodeEdges]);

  const toggleType = (type: GraphNodeType) => {
    setVisibleTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const getTypeColor = (type: GraphNodeType): string => {
    switch (type) {
      case 'wallet':
        return '#22D3EE'; // cyan
      case 'agent':
        return '#9932CC'; // purple
      case 'timeline':
        return '#00FF41'; // green
      case 'evidence':
        return '#FF9500'; // amber
      case 'sabotage':
        return '#FF3B3B'; // red
      case 'paradox':
        return '#FF6B00'; // orange
    }
  };

  const getRelationColor = (relation: GraphEdge['relation']): string => {
    switch (relation) {
      case 'holds_position':
      case 'placed_wing_flap':
        return '#22D3EE'; // cyan
      case 'founded':
        return '#00FF41'; // green
      case 'benefited':
        return '#FF9500'; // amber
      case 'triggered':
        return '#FF3B3B'; // red
      case 'contradicted':
        return '#FF6B00'; // orange
      case 'linked':
        return '#666666'; // grey
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-text-muted">Loading graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-500">Error loading graph: {error instanceof Error ? error.message : 'Unknown error'}</div>
      </div>
    );
  }

  if (!graph) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-text-muted">No graph data available</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 gap-4 bg-terminal-bg">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-terminal-text uppercase tracking-wide">
          Entity Graph Explorer
        </h1>
        <div className="text-xs text-terminal-text-muted">
          {graph.nodes.length} nodes • {graph.edges.length} edges
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Search */}
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-terminal-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search nodes..."
            className="w-full pl-8 pr-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
          />
        </div>

        {/* Type Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          {(['wallet', 'agent', 'timeline', 'evidence', 'sabotage', 'paradox'] as GraphNodeType[]).map((type) => {
            const isVisible = visibleTypes.has(type);
            const color = getTypeColor(type);
            const count = nodesByType[type].length;

            return (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className="flex items-center gap-1.5 px-2 py-1 text-xs rounded transition"
                style={{
                  backgroundColor: isVisible ? `${color}20` : 'transparent',
                  border: `1px solid ${isVisible ? color : '#333'}`,
                  color: isVisible ? color : '#666',
                }}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                <span className="capitalize">{type}</span>
                <span className="text-[10px]">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content: Three Columns */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[300px_1fr_300px] gap-4">
        {/* Left: Node List */}
        <div className="bg-terminal-panel rounded-lg border border-terminal-border p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-3">
            Nodes
          </h3>
          <div className="space-y-4">
            {(['wallet', 'agent', 'timeline', 'evidence', 'sabotage', 'paradox'] as GraphNodeType[]).map((type) => {
              const nodes = nodesByType[type];
              if (nodes.length === 0) return null;

              const color = getTypeColor(type);

              return (
                <div key={type}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-xs font-semibold text-terminal-text uppercase">
                      {type} ({nodes.length})
                    </span>
                  </div>
                  <div className="space-y-1 ml-4">
                    {nodes.map((node) => (
                      <button
                        key={node.id}
                        onClick={() => setSelectedNodeId(node.id)}
                        className={`
                          w-full text-left px-2 py-1.5 rounded text-xs transition
                          ${selectedNodeId === node.id
                            ? 'bg-terminal-panel border border-echelon-cyan text-terminal-text'
                            : 'text-terminal-text-muted hover:text-terminal-text hover:bg-terminal-panel/50'
                          }
                        `}
                      >
                        <div className="truncate">{node.label}</div>
                        <div className="text-[10px] font-mono text-terminal-text-muted truncate">
                          {node.id}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Centre: Selected Node Detail */}
        <div className="bg-terminal-panel rounded-lg border border-terminal-border p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {selectedNode ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getTypeColor(selectedNode.type) }}
                  />
                  <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
                    {selectedNode.label}
                  </h3>
                </div>
                {selectedNode.type === 'timeline' && (
                  <button
                    onClick={() => navigate(`/timeline/${selectedNode.id}`)}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-echelon-cyan/20 border border-echelon-cyan rounded text-echelon-cyan hover:bg-echelon-cyan/30 transition"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Open Timeline
                  </button>
                )}
              </div>

              {/* Node ID */}
              <div className="mb-4 pb-4 border-b border-terminal-border">
                <div className="text-xs text-terminal-text-muted mb-1">Node ID</div>
                <div className="text-xs font-mono text-terminal-text">{selectedNode.id}</div>
              </div>

              {/* Metadata */}
              {selectedNode.meta && Object.keys(selectedNode.meta).length > 0 && (
                <div className="mb-4 pb-4 border-b border-terminal-border">
                  <h4 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                    Metadata
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(selectedNode.meta).map(([key, value]) => (
                      <div key={key} className="text-xs">
                        <span className="text-terminal-text-muted">{key}:</span>{' '}
                        <span className="text-terminal-text font-mono">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Connections Summary */}
              <div className="mb-4 pb-4 border-b border-terminal-border">
                <h4 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                  Connections
                </h4>
                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-terminal-text-muted">Incoming:</span>{' '}
                    <span className="text-terminal-text font-semibold">
                      {nodeEdges.incoming.length}
                    </span>
                  </div>
                  <div>
                    <span className="text-terminal-text-muted">Outgoing:</span>{' '}
                    <span className="text-terminal-text font-semibold">
                      {nodeEdges.outgoing.length}
                    </span>
                  </div>
                  <div>
                    <span className="text-terminal-text-muted">Connected Nodes:</span>{' '}
                    <span className="text-terminal-text font-semibold">
                      {connectedNodes.size}
                    </span>
                  </div>
                </div>
              </div>

              {/* Connected Nodes List */}
              {connectedNodes.size > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                    Connected Nodes
                  </h4>
                  <div className="space-y-1">
                    {Array.from(connectedNodes.values()).map((node) => {
                      const color = getTypeColor(node.type);
                      return (
                        <button
                          key={node.id}
                          onClick={() => setSelectedNodeId(node.id)}
                          className="w-full text-left px-2 py-1 rounded text-xs bg-terminal-panel border border-terminal-border hover:border-echelon-cyan transition"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-terminal-text">{node.label}</span>
                            <span className="text-[10px] text-terminal-text-muted font-mono ml-auto">
                              {node.type}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-terminal-text-muted">
              <div className="text-4xl mb-4 opacity-50">⊚</div>
              <p className="text-sm">Select a node to view details</p>
            </div>
          )}
        </div>

        {/* Right: Edge List */}
        <div className="bg-terminal-panel rounded-lg border border-terminal-border p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-3">
            Edges
            {selectedNode && (
              <span className="ml-2 text-terminal-text">
                ({nodeEdges.incoming.length + nodeEdges.outgoing.length})
              </span>
            )}
          </h3>

          {!selectedNode ? (
            <div className="text-xs text-terminal-text-muted text-center py-8">
              Select a node to view edges
            </div>
          ) : (
            <div className="space-y-3">
              {/* Incoming Edges */}
              {nodeEdges.incoming.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-terminal-text-muted uppercase mb-2 flex items-center gap-1">
                    <ArrowRight className="w-3 h-3" />
                    Incoming ({nodeEdges.incoming.length})
                  </div>
                  <div className="space-y-1 ml-4">
                    {nodeEdges.incoming.map((edge) => {
                      const fromNode = graph.nodes.find((n) => n.id === edge.from);
                      const color = getRelationColor(edge.relation);
                      
                      return (
                        <div
                          key={edge.id}
                          className="px-2 py-1.5 rounded bg-terminal-panel border border-terminal-border text-xs"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-terminal-text-muted">{fromNode?.label || edge.from}</span>
                            <ArrowRight className="w-3 h-3 text-terminal-text-muted" />
                            <span className="text-terminal-text">{selectedNode.label}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase"
                              style={{
                                backgroundColor: `${color}20`,
                                color: color,
                              }}
                            >
                              {edge.relation.replace('_', ' ')}
                            </span>
                            {edge.weight !== undefined && (
                              <span className="text-[10px] text-terminal-text-muted">
                                weight: {edge.weight.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Outgoing Edges */}
              {nodeEdges.outgoing.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-terminal-text-muted uppercase mb-2 flex items-center gap-1">
                    <ArrowLeft className="w-3 h-3" />
                    Outgoing ({nodeEdges.outgoing.length})
                  </div>
                  <div className="space-y-1 ml-4">
                    {nodeEdges.outgoing.map((edge) => {
                      const toNode = graph.nodes.find((n) => n.id === edge.to);
                      const color = getRelationColor(edge.relation);
                      
                      return (
                        <div
                          key={edge.id}
                          className="px-2 py-1.5 rounded bg-terminal-panel border border-terminal-border text-xs"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-terminal-text">{selectedNode.label}</span>
                            <ArrowRight className="w-3 h-3 text-terminal-text-muted" />
                            <span className="text-terminal-text-muted">{toNode?.label || edge.to}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase"
                              style={{
                                backgroundColor: `${color}20`,
                                color: color,
                              }}
                            >
                              {edge.relation.replace('_', ' ')}
                            </span>
                            {edge.weight !== undefined && (
                              <span className="text-[10px] text-terminal-text-muted">
                                weight: {edge.weight.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {nodeEdges.incoming.length === 0 && nodeEdges.outgoing.length === 0 && (
                <div className="text-xs text-terminal-text-muted text-center py-8">
                  No edges connected to this node
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
