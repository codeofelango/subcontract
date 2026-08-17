"use client";

import "@xyflow/react/dist/style.css";
import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  Handle,
  Position,
  type Node,
  type NodeChange,
  type NodeProps,
} from "@xyflow/react";
import { ArrowLeft, Plus, Rocket, Save, X } from "lucide-react";
import { activateWorkflow, saveWorkflow } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import type { AppUser, WorkflowDetail, WorkflowEdge, WorkflowNode, WorkflowNodeData } from "@/lib/types";

const X_GAP = 240;
const NODE_WIDTH = 220;
const NODE_HEIGHT = 62;
const inputCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[10px] py-[7px] text-[12.5px] focus:outline-none focus:border-[#3a5bd9]";

let idSeq = 1000;
function newNodeId(): string {
  return `n${idSeq++}`;
}

function layoutChain(nodes: WorkflowNode[], edges: WorkflowEdge[]): WorkflowNode[] {
  const nextOf = new Map(edges.map((e) => [e.source, e.target]));
  const hasIncoming = new Set(edges.map((e) => e.target));
  const start = nodes.find((n) => !hasIncoming.has(n.id));
  if (!start) return nodes;

  const order: string[] = [start.id];
  while (nextOf.has(order[order.length - 1])) order.push(nextOf.get(order[order.length - 1])!);
  const xById = new Map(order.map((id, i) => [id, 60 + i * X_GAP]));

  return nodes.map((n) => (xById.has(n.id) ? { ...n, position: { x: xById.get(n.id)!, y: n.position.y } } : n));
}

type StepNodeRenderData = WorkflowNodeData &
  Record<string, unknown> & {
    userName: string;
    isSelected: boolean;
    canDelete: boolean;
    onSelect: () => void;
    onAddAfter: () => void;
    onDelete: () => void;
  };

function StepNode({ data }: NodeProps<Node<StepNodeRenderData>>) {
  return (
    <div
      onClick={data.onSelect}
      className="relative rounded-[10px] px-[14px] py-[10px] min-w-[170px] cursor-pointer bg-white"
      style={{
        border: `2px solid ${data.isSelected ? "#3a5bd9" : "#e6e8ec"}`,
        boxShadow: data.isSelected ? "0 0 0 3px rgba(58,91,217,.12)" : "0 1px 2px rgba(16,24,40,.04)",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: "#98a2b3", width: 7, height: 7 }} />
      <div className="font-semibold text-[13px] text-[#101828] pr-[8px]">{data.label || "Untitled step"}</div>
      <div className="text-[11px] text-[#667085] mt-[2px]">{data.userName || "Unassigned"}</div>
      {data.canDelete && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            data.onDelete();
          }}
          className="absolute -top-[8px] -right-[8px] w-[18px] h-[18px] rounded-full bg-white border border-[#e6e8ec] text-[#98a2b3] hover:text-[#c0362c] flex items-center justify-center"
        >
          <X size={11} strokeWidth={2.5} />
        </button>
      )}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          data.onAddAfter();
        }}
        className="absolute top-1/2 -right-[13px] -translate-y-1/2 w-[24px] h-[24px] rounded-full bg-[#3a5bd9] text-white flex items-center justify-center hover:brightness-110 z-10"
        title="Insert step after"
      >
        <Plus size={14} strokeWidth={2.5} />
      </button>
      <Handle type="source" position={Position.Right} style={{ background: "#98a2b3", width: 7, height: 7 }} />
    </div>
  );
}

const NODE_TYPES = { step: StepNode };

export function CanvasEditor({ workflow, users }: { workflow: WorkflowDetail; users: AppUser[] }) {
  const router = useRouter();
  const [name, setName] = useState(workflow.name);
  const [rawNodes, setRawNodes] = useState<WorkflowNode[]>(workflow.nodes);
  const [edges, setEdges] = useState<WorkflowEdge[]>(workflow.edges);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [isActive, setIsActive] = useState(workflow.isActive);
  const [error, setError] = useState<string | null>(null);

  const usersById = useMemo(() => new Map(users.map((u) => [u.id, u])), [users]);

  const mutate = useCallback((nodes: WorkflowNode[], edgeList: WorkflowEdge[]) => {
    setRawNodes(layoutChain(nodes, edgeList));
    setEdges(edgeList);
    setDirty(true);
  }, []);

  const addAfter = useCallback(
    (afterId: string) => {
      const outgoing = edges.find((e) => e.source === afterId);
      const afterNode = rawNodes.find((n) => n.id === afterId);
      if (!afterNode) return;
      const id = newNodeId();
      const newNode: WorkflowNode = { id, type: "step", position: { x: 0, y: afterNode.position.y }, data: { label: "New Step", userId: null } };
      const newEdges = edges.filter((e) => e.source !== afterId);
      newEdges.push({ id: `e-${afterId}-${id}`, source: afterId, target: id });
      if (outgoing) newEdges.push({ id: `e-${id}-${outgoing.target}`, source: id, target: outgoing.target });
      mutate([...rawNodes, newNode], newEdges);
      setSelectedId(id);
    },
    [rawNodes, edges, mutate]
  );

  const deleteNode = useCallback(
    (id: string) => {
      if (rawNodes.length <= 1) return;
      const incoming = edges.find((e) => e.target === id);
      const outgoing = edges.find((e) => e.source === id);
      const newEdges = edges.filter((e) => e.source !== id && e.target !== id);
      if (incoming && outgoing) newEdges.push({ id: `e-${incoming.source}-${outgoing.target}`, source: incoming.source, target: outgoing.target });
      mutate(
        rawNodes.filter((n) => n.id !== id),
        newEdges
      );
      setSelectedId((cur) => (cur === id ? null : cur));
    },
    [rawNodes, edges, mutate]
  );

  const updateSelected = useCallback(
    (patch: Partial<WorkflowNodeData>) => {
      if (!selectedId) return;
      setRawNodes((nodes) => nodes.map((n) => (n.id === selectedId ? { ...n, data: { ...n.data, ...patch } } : n)));
      setDirty(true);
    },
    [selectedId]
  );

  const displayNodes: Node<StepNodeRenderData>[] = useMemo(
    () =>
      rawNodes.map((n) => ({
        id: n.id,
        type: "step",
        position: n.position,
        // Fixed dimensions + static handle bounds instead of relying on ResizeObserver
        // measurement — avoids nodes/edges getting stuck unmeasured if that pass never settles.
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        handles: [
          { id: null, type: "target", position: Position.Left, x: 0, y: NODE_HEIGHT / 2, width: 1, height: 1 },
          { id: null, type: "source", position: Position.Right, x: NODE_WIDTH, y: NODE_HEIGHT / 2, width: 1, height: 1 },
        ],
        data: {
          label: n.data.label,
          userId: n.data.userId,
          userName: n.data.userId ? usersById.get(n.data.userId)?.name ?? "Unknown" : "",
          isSelected: n.id === selectedId,
          canDelete: rawNodes.length > 1,
          onSelect: () => setSelectedId(n.id),
          onAddAfter: () => addAfter(n.id),
          onDelete: () => deleteNode(n.id),
        },
      })),
    [rawNodes, usersById, selectedId, addAfter, deleteNode]
  );

  const displayEdges = useMemo(() => edges.map((e) => ({ ...e, type: "smoothstep" })), [edges]);

  const onNodesChange = useCallback((changes: NodeChange<Node<StepNodeRenderData>>[]) => {
    setRawNodes((nodes) => {
      const plain: Node[] = nodes.map((n) => ({ id: n.id, type: "step", position: n.position, data: {} }));
      const positioned = applyNodeChanges(changes as unknown as NodeChange<Node>[], plain);
      const byId = new Map(positioned.map((n) => [n.id, n.position]));
      return nodes.map((n) => (byId.has(n.id) ? { ...n, position: byId.get(n.id)! } : n));
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await saveWorkflow(workflow.id, name, rawNodes, edges);
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleActivate() {
    setActivating(true);
    setError(null);
    try {
      await saveWorkflow(workflow.id, name, rawNodes, edges);
      await activateWorkflow(workflow.id);
      setIsActive(true);
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to activate");
    } finally {
      setActivating(false);
    }
  }

  const selectedNode = rawNodes.find((n) => n.id === selectedId) ?? null;

  return (
    <div className="flex flex-col gap-[14px]" style={{ height: "calc(100vh - 160px)" }}>
      <div className="flex items-center gap-[12px]">
        <button
          type="button"
          onClick={() => router.push("/approval-flows")}
          aria-label="Back to Approval Flows"
          title="Back to Approval Flows"
          className="text-[#98a2b3] hover:text-[#475467]"
        >
          <ArrowLeft size={17} strokeWidth={2} />
        </button>
        <input
          className="text-[15px] font-semibold border-b border-transparent hover:border-[#e6e8ec] focus:border-[#3a5bd9] focus:outline-none px-[2px] py-[2px] bg-transparent"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setDirty(true);
          }}
        />
        {isActive && (
          <Pill color="#12805c" bg="#e6f4ee">
            Active
          </Pill>
        )}
        <div className="flex-1" />
        {error && <span className="text-[12px] text-[#c0362c]">{error}</span>}
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || !dirty}
          className="flex items-center gap-[6px] bg-white border border-[#e6e8ec] rounded-[8px] px-[13px] py-[8px] text-[12.5px] font-semibold text-[#475467] disabled:opacity-40"
        >
          <Save size={14} strokeWidth={2} />
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={handleActivate}
          disabled={activating}
          className="flex items-center gap-[6px] bg-[#3a5bd9] text-white rounded-[8px] px-[13px] py-[8px] text-[12.5px] font-semibold disabled:opacity-50 hover:brightness-[1.08]"
        >
          <Rocket size={14} strokeWidth={2} />
          {activating ? "Activating…" : isActive ? "Re-activate" : "Activate"}
        </button>
      </div>

      <div className="flex-1 grid grid-cols-[1fr_280px] gap-[14px] min-h-0">
        <div className="rounded-[10px] border border-[#e6e8ec] overflow-hidden bg-[#fafbfc]">
          <ReactFlowProvider>
            <ReactFlow
              nodes={displayNodes}
              edges={displayEdges}
              nodeTypes={NODE_TYPES}
              onNodesChange={onNodesChange}
              nodesConnectable={false}
              onPaneClick={() => setSelectedId(null)}
              fitView
            >
              <Background gap={18} size={1} color="#e0e3e8" />
              <Controls showInteractive={false} />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </ReactFlowProvider>
        </div>

        <Card>
          {selectedNode ? (
            <div className="flex flex-col gap-[14px]">
              <div className="font-semibold text-[13.5px]">Step Details</div>
              <div>
                <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Role</label>
                <input className={inputCls} value={selectedNode.data.label} onChange={(e) => updateSelected({ label: e.target.value })} />
              </div>
              <div>
                <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Assigned User</label>
                <select
                  className={inputCls}
                  value={selectedNode.data.userId ?? ""}
                  onChange={(e) => updateSelected({ userId: e.target.value ? Number(e.target.value) : null })}
                >
                  <option value="">Unassigned (defaults to raiser)</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} — {u.title}
                    </option>
                  ))}
                </select>
              </div>
              {rawNodes.length > 1 && (
                <button type="button" onClick={() => deleteNode(selectedNode.id)} className="text-[12px] font-semibold text-[#c0362c] text-left">
                  Delete this step
                </button>
              )}
            </div>
          ) : (
            <div className="text-[12.5px] text-[#98a2b3] leading-[1.5]">
              Click a step on the canvas to edit its role and assigned user, or click the <b>+</b> button on a step to
              insert the next one in the chain.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
