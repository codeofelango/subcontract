import { getUsers, getWorkflow } from "@/lib/api";
import { CanvasEditor } from "./CanvasEditor";

export const dynamic = "force-dynamic";

export default async function ApprovalFlowCanvasPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [workflow, users] = await Promise.all([getWorkflow(Number(id)), getUsers()]);
  return <CanvasEditor workflow={workflow} users={users} />;
}
