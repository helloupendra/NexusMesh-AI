import React, { memo, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

const ROLE_STYLES = {
  orchestrator: {
    border: '#22d3ee',
    glow: '0 0 0 1px rgba(34,211,238,0.45), 0 0 30px rgba(34,211,238,0.18)',
    badge: 'ORCHESTRATOR',
  },
  csharp: {
    border: '#10b981',
    glow: '0 0 0 1px rgba(16,185,129,0.45), 0 0 28px rgba(16,185,129,0.16)',
    badge: 'C# WORKER',
  },
  python: {
    border: '#38bdf8',
    glow: '0 0 0 1px rgba(56,189,248,0.45), 0 0 28px rgba(56,189,248,0.16)',
    badge: 'PYTHON AGENT',
  },
};

const NODE_STATUS_STYLE = {
  online: {
    text: 'text-emerald-300',
    chip: 'border-emerald-400/30 bg-emerald-500/10',
  },
  idle: {
    text: 'text-zinc-300',
    chip: 'border-zinc-500/30 bg-zinc-500/10',
  },
  offline: {
    text: 'text-rose-300',
    chip: 'border-rose-400/30 bg-rose-500/10',
  },
};

const handleStyle = {
  width: 8,
  height: 8,
  border: 'none',
  background: '#22d3ee',
};

const AgentNode = memo(({ data }) => {
  const roleStyle = ROLE_STYLES[data.role] ?? ROLE_STYLES.orchestrator;
  const statusStyle = NODE_STATUS_STYLE[data.status] ?? NODE_STATUS_STYLE.idle;

  return (
    <div
      className="min-w-[240px] rounded-xl border bg-zinc-900/95 px-4 py-3 text-zinc-100"
      style={{ borderColor: roleStyle.border, boxShadow: roleStyle.glow }}
    >
      <Handle type="target" position={Position.Left} style={handleStyle} />
      <Handle type="source" position={Position.Right} style={handleStyle} />

      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="inline-flex rounded-full border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] font-semibold tracking-[0.18em] text-cyan-300">
          {roleStyle.badge}
        </p>
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${statusStyle.chip} ${statusStyle.text}`}
        >
          {data.status}
        </span>
      </div>
      <h3 className="text-sm font-semibold text-zinc-100">{data.title}</h3>
      <p className="mt-1 text-xs text-zinc-400">{data.subtitle}</p>
    </div>
  );
});

AgentNode.displayName = 'AgentNode';

const nodeTypes = {
  agentNode: AgentNode,
};

export default function AgentGraph({ nodeStatus }) {
  const nodes = useMemo(
    () => [
      {
        id: 'node-orchestrator',
        type: 'agentNode',
        position: { x: 260, y: 160 },
        data: {
          title: 'Orchestrator',
          subtitle: 'Live API + Task Dispatch',
          role: 'orchestrator',
          status: nodeStatus?.orchestrator ?? 'idle',
        },
      },
      {
        id: 'node-csharp-worker',
        type: 'agentNode',
        position: { x: 20, y: 40 },
        data: {
          title: 'C# Data Worker',
          subtitle: '.NET 9 | task_queue consumer',
          role: 'csharp',
          status: nodeStatus?.csharp_worker ?? 'idle',
        },
      },
      {
        id: 'node-python-inference',
        type: 'agentNode',
        position: { x: 500, y: 300 },
        data: {
          title: 'Python Inference',
          subtitle: 'Model Analysis + Signal Logic',
          role: 'python',
          status: nodeStatus?.python_inference ?? 'idle',
        },
      },
    ],
    [nodeStatus]
  );

  const edges = useMemo(
    () => [
      {
        id: 'edge-orchestrator-csharp',
        source: 'node-orchestrator',
        target: 'node-csharp-worker',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#10b981', strokeWidth: 2 },
      },
      {
        id: 'edge-orchestrator-python',
        source: 'node-orchestrator',
        target: 'node-python-inference',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#38bdf8', strokeWidth: 2 },
      },
    ],
    []
  );

  return (
    <div className="h-full w-full rounded-2xl border border-zinc-800 bg-zinc-950/70">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
        proOptions={{ hideAttribution: true }}
      >
        <MiniMap
          pannable
          zoomable
          nodeColor={(node) => {
            if (node.id === 'node-csharp-worker') return '#10b981';
            if (node.id === 'node-python-inference') return '#38bdf8';
            return '#22d3ee';
          }}
          maskColor="rgba(24, 24, 27, 0.7)"
          className="rounded-lg border border-zinc-700 bg-zinc-900"
        />
        <Controls
          showInteractive={false}
          className="rounded-lg border border-zinc-700 bg-zinc-900 text-zinc-300"
        />
        <Background gap={24} size={1.1} color="#3f3f46" />
      </ReactFlow>
    </div>
  );
}
