import { getUsers } from "@/lib/api";
import { UsersTable } from "./UsersTable";

export const dynamic = "force-dynamic";

export default async function UsersPage() {
  const users = await getUsers();
  return (
    <div className="max-w-[1100px]">
      <div className="text-[13px] text-[#667085] mb-[16px]">
        Directory of people who can be assigned as named approvers when building an Approval Flow. No login/passwords —
        this is a lightweight directory, not an authentication system.
      </div>
      <UsersTable initialUsers={users} />
    </div>
  );
}
