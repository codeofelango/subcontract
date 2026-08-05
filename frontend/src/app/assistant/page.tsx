import { getActivity } from "@/lib/api";
import { AssistantChat } from "./AssistantChat";

export const dynamic = "force-dynamic";

export default async function AssistantPage() {
  const initialActivity = await getActivity(15);

  return <AssistantChat initialActivity={initialActivity} />;
}
