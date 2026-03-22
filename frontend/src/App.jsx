import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Radio,
  SendHorizonal,
  ServerCog,
  WifiOff,
} from 'lucide-react';
import AgentGraph from './components/AgentGraph';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const navItems = [
  { label: 'Orchestrator', icon: Bot, active: true },
  { label: 'Worker Nodes', icon: Cpu, active: false },
  { label: 'Market Analysis', icon: BrainCircuit, active: false },
];

const initialSnapshot = {
  rabbitmq_connection: { online: false, endpoint: 'unknown' },
  active_tasks: [],
  recent_tasks: [],
  node_status: {
    orchestrator: 'online',
    csharp_worker: 'idle',
    python_inference: 'idle',
  },
  metrics: {
    active_count: 0,
    recent_count: 0,
  },
};

function toWsUrl(apiBase) {
  const parsed = new URL(apiBase);
  parsed.protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
  parsed.pathname = '/ws/status';
  return parsed.toString();
}

function shortTaskId(taskId) {
  if (!taskId) return 'unknown';
  if (taskId.length <= 18) return taskId;
  return `${taskId.slice(0, 10)}...${taskId.slice(-8)}`;
}

export default function App() {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [taskRequest, setTaskRequest] = useState('Run stock backtest for AAPL');
  const [taskType, setTaskType] = useState('backtest');
  const [dispatchError, setDispatchError] = useState('');
  const [dispatching, setDispatching] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const wsUrl = useMemo(() => toWsUrl(API_BASE), []);

  useEffect(() => {
    let mounted = true;
    let socket;
    let reconnectTimer;

    const loadInitial = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (!response.ok) return;
        const payload = await response.json();
        if (mounted) setSnapshot(payload);
      } catch {
        // WebSocket reconnect path covers transient startup failures.
      }
    };

    const connect = () => {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        if (mounted) setWsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (mounted) setSnapshot(payload);
        } catch {
          // Ignore malformed frames.
        }
      };

      socket.onclose = () => {
        if (!mounted) return;
        setWsConnected(false);
        reconnectTimer = setTimeout(connect, 2000);
      };

      socket.onerror = () => {
        socket.close();
      };
    };

    loadInitial();
    connect();

    return () => {
      mounted = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, [wsUrl]);

  async function submitTask(event) {
    event.preventDefault();
    setDispatching(true);
    setDispatchError('');

    try {
      const response = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request: taskRequest,
          task_type: taskType,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Task dispatch failed');
      }

      setTaskRequest('');
    } catch (error) {
      setDispatchError(error instanceof Error ? error.message : 'Task dispatch failed');
    } finally {
      setDispatching(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(6,182,212,0.12),transparent_34%),radial-gradient(circle_at_100%_100%,rgba(16,185,129,0.08),transparent_30%)]" />

      <div className="relative grid min-h-screen grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_360px]">
        <aside className="border-b border-zinc-800/90 bg-zinc-900/90 p-5 backdrop-blur lg:border-b-0 lg:border-r">
          <div className="mb-8">
            <p className="text-xs font-semibold tracking-[0.22em] text-cyan-300">NEXUSMESH-AI</p>
            <h1 className="mt-2 text-xl font-semibold text-zinc-100">Command Center</h1>
            <p className="mt-2 text-sm text-zinc-400">Distributed Multi-Agent Control Plane</p>
          </div>

          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  type="button"
                  className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                    item.active
                      ? 'border-cyan-400/70 bg-cyan-500/10 text-cyan-200 shadow-[0_0_18px_rgba(34,211,238,0.17)]'
                      : 'border-zinc-800 bg-zinc-900/70 text-zinc-300 hover:border-zinc-600 hover:bg-zinc-800/70'
                  }`}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="border-b border-zinc-800/90 p-4 lg:border-b-0 lg:p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-zinc-400">NETWORK TOPOLOGY</p>
              <h2 className="mt-1 text-lg font-semibold text-zinc-100">Agent Mesh Visualization</h2>
            </div>

            <div
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
                wsConnected
                  ? 'border-emerald-400/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-rose-400/40 bg-rose-500/10 text-rose-300'
              }`}
            >
              {wsConnected ? <Activity size={14} /> : <WifiOff size={14} />}
              {wsConnected ? 'WebSocket Live' : 'WebSocket Reconnecting'}
            </div>
          </div>

          <div className="h-[420px] md:h-[560px] lg:h-[calc(100vh-3rem)]">
            <AgentGraph nodeStatus={snapshot.node_status} />
          </div>
        </main>

        <section className="bg-zinc-900/90 p-5 backdrop-blur lg:border-l lg:border-zinc-800/90">
          <h3 className="text-xs font-semibold tracking-[0.2em] text-zinc-400">STATUS PANEL</h3>

          <form onSubmit={submitTask} className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
            <p className="text-sm text-zinc-300">Dispatch Task</p>
            <div className="mt-3 grid grid-cols-1 gap-2">
              <select
                value={taskType}
                onChange={(event) => setTaskType(event.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-cyan-400"
              >
                <option value="backtest">backtest</option>
                <option value="signal_generation">signal_generation</option>
                <option value="risk_evaluation">risk_evaluation</option>
              </select>
              <input
                value={taskRequest}
                onChange={(event) => setTaskRequest(event.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-cyan-400"
                placeholder="Task request"
                required
              />
              <button
                type="submit"
                disabled={dispatching}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-400/60 bg-cyan-500/10 px-3 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <SendHorizonal size={14} />
                {dispatching ? 'Dispatching...' : 'Dispatch'}
              </button>
              {dispatchError ? <p className="text-xs text-rose-300">{dispatchError}</p> : null}
            </div>
          </form>

          <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
            <p className="text-sm text-zinc-300">RabbitMQ Connection</p>
            <div
              className={`mt-2 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
                snapshot.rabbitmq_connection.online
                  ? 'border-emerald-400/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-rose-400/40 bg-rose-500/10 text-rose-300'
              }`}
            >
              <CheckCircle2 size={14} />
              {snapshot.rabbitmq_connection.online ? 'Online' : 'Offline'}
            </div>
            <p className="mt-3 text-xs text-zinc-500">Broker: {snapshot.rabbitmq_connection.endpoint}</p>
          </div>

          <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm text-zinc-300">Active Tasks</p>
              <div className="inline-flex items-center gap-1 text-xs text-cyan-300">
                <Radio size={12} />
                {snapshot.metrics.active_count} live
              </div>
            </div>

            <div className="space-y-2">
              {snapshot.active_tasks.length === 0 ? (
                <p className="rounded-xl border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-xs text-zinc-500">
                  No active tasks right now.
                </p>
              ) : (
                snapshot.active_tasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="rounded-xl border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-xs"
                  >
                    <div className="flex items-start gap-2">
                      <p
                        className="min-w-0 flex-1 truncate font-mono font-semibold text-zinc-200"
                        title={task.task_id}
                      >
                        {shortTaskId(task.task_id)}
                      </p>
                      <span className="shrink-0 rounded-full border border-cyan-400/30 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                        {task.status}
                      </span>
                    </div>
                    <p className="mt-1 break-all text-zinc-500" title={task.task_id}>
                      id: {task.task_id}
                    </p>
                    <p className="mt-1 text-zinc-400">type: {task.task_type}</p>
                    <p className="mt-1 break-words text-zinc-500">{task.request}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 text-xs text-zinc-400">
            <p className="mb-1 inline-flex items-center gap-2 text-zinc-300">
              <ServerCog size={14} />
              Runtime Snapshot
            </p>
            <p>Orchestrator: {snapshot.node_status.orchestrator}</p>
            <p>C# Worker Nodes: {snapshot.node_status.csharp_worker}</p>
            <p>Python Inference Nodes: {snapshot.node_status.python_inference}</p>
            <p>Recent Tasks: {snapshot.metrics.recent_count}</p>
          </div>
        </section>
      </div>
    </div>
  );
}
