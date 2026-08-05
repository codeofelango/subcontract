"use client";

import { useState } from "react";
import { Plus, Trash2, X, Check, Pencil } from "lucide-react";
import { createUser, deleteUser, updateUser, type UserInput } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import type { AppUser } from "@/lib/types";

const inputCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[9px] py-[6px] text-[12.5px] focus:outline-none focus:border-[#3a5bd9]";

const DEPARTMENTS = ["Procurement", "HR", "Finance", "PMO", "Executive", "QAQC"];

const emptyDraft: UserInput = { name: "", email: "", department: DEPARTMENTS[0], title: "", active: true };

export function UsersTable({ initialUsers }: { initialUsers: AppUser[] }) {
  const [users, setUsers] = useState(initialUsers);
  const [newDraft, setNewDraft] = useState<UserInput>(emptyDraft);
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<UserInput>(emptyDraft);
  const [error, setError] = useState<string | null>(null);

  async function submitNew() {
    if (!newDraft.name.trim()) return;
    setAdding(true);
    setError(null);
    try {
      const created = await createUser(newDraft);
      setUsers((u) => [...u, created].sort((a, b) => a.name.localeCompare(b.name)));
      setNewDraft(emptyDraft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add user");
    } finally {
      setAdding(false);
    }
  }

  function startEdit(u: AppUser) {
    setEditingId(u.id);
    setEditDraft({ name: u.name, email: u.email, department: u.department, title: u.title, active: u.active });
  }

  async function submitEdit(id: number) {
    try {
      const updated = await updateUser(id, editDraft);
      setUsers((list) => list.map((u) => (u.id === id ? updated : u)));
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save user");
    }
  }

  async function remove(id: number) {
    try {
      await deleteUser(id);
      setUsers((list) => list.filter((u) => u.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete user");
    }
  }

  return (
    <Card padding="0" className="overflow-hidden">
      {error && <div className="px-[18px] py-[10px] text-[12px] text-[#c0362c] bg-[#fbeceb] border-b border-[#e6e8ec]">{error}</div>}
      <table className="w-full border-collapse text-[12.5px]">
        <thead>
          <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
            <th className="px-[16px] py-[10px] font-semibold">Name</th>
            <th className="px-[16px] py-[10px] font-semibold">Email</th>
            <th className="px-[16px] py-[10px] font-semibold">Department</th>
            <th className="px-[16px] py-[10px] font-semibold">Title</th>
            <th className="px-[16px] py-[10px] font-semibold">Status</th>
            <th className="px-[16px] py-[10px] font-semibold w-[80px]" />
          </tr>
        </thead>
        <tbody>
          {users.map((u) =>
            editingId === u.id ? (
              <tr key={u.id} className="border-t border-[#f0f1f4] bg-[#fafbfc]">
                <td className="px-[16px] py-[8px]">
                  <input className={inputCls} value={editDraft.name} onChange={(e) => setEditDraft((d) => ({ ...d, name: e.target.value }))} />
                </td>
                <td className="px-[16px] py-[8px]">
                  <input className={inputCls} value={editDraft.email} onChange={(e) => setEditDraft((d) => ({ ...d, email: e.target.value }))} />
                </td>
                <td className="px-[16px] py-[8px]">
                  <select className={inputCls} value={editDraft.department} onChange={(e) => setEditDraft((d) => ({ ...d, department: e.target.value }))}>
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-[16px] py-[8px]">
                  <input className={inputCls} value={editDraft.title} onChange={(e) => setEditDraft((d) => ({ ...d, title: e.target.value }))} />
                </td>
                <td className="px-[16px] py-[8px]">
                  <select
                    className={inputCls}
                    value={editDraft.active ? "active" : "inactive"}
                    onChange={(e) => setEditDraft((d) => ({ ...d, active: e.target.value === "active" }))}
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </td>
                <td className="px-[16px] py-[8px]">
                  <div className="flex gap-[8px] justify-end">
                    <button type="button" onClick={() => submitEdit(u.id)} className="text-[#12805c] hover:opacity-70">
                      <Check size={15} strokeWidth={2.3} />
                    </button>
                    <button type="button" onClick={() => setEditingId(null)} className="text-[#98a2b3] hover:opacity-70">
                      <X size={15} strokeWidth={2.3} />
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr key={u.id} className="border-t border-[#f0f1f4] hover:bg-[#fafbfc]">
                <td className="px-[16px] py-[11px] font-semibold">{u.name}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{u.email}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{u.department}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{u.title}</td>
                <td className="px-[16px] py-[11px]">
                  {u.active ? (
                    <Pill color="#12805c" bg="#e6f4ee">
                      Active
                    </Pill>
                  ) : (
                    <Pill color="#667085" bg="#f0f1f4">
                      Inactive
                    </Pill>
                  )}
                </td>
                <td className="px-[16px] py-[11px]">
                  <div className="flex gap-[10px] justify-end">
                    <button type="button" onClick={() => startEdit(u)} className="text-[#98a2b3] hover:text-[#3a5bd9]">
                      <Pencil size={14} strokeWidth={2} />
                    </button>
                    <button type="button" onClick={() => remove(u.id)} className="text-[#98a2b3] hover:text-[#c0362c]">
                      <Trash2 size={14} strokeWidth={2} />
                    </button>
                  </div>
                </td>
              </tr>
            )
          )}
          <tr className="border-t border-[#e6e8ec] bg-[#fafbfc]">
            <td className="px-[16px] py-[8px]">
              <input placeholder="Name" className={inputCls} value={newDraft.name} onChange={(e) => setNewDraft((d) => ({ ...d, name: e.target.value }))} />
            </td>
            <td className="px-[16px] py-[8px]">
              <input placeholder="Email" className={inputCls} value={newDraft.email} onChange={(e) => setNewDraft((d) => ({ ...d, email: e.target.value }))} />
            </td>
            <td className="px-[16px] py-[8px]">
              <select className={inputCls} value={newDraft.department} onChange={(e) => setNewDraft((d) => ({ ...d, department: e.target.value }))}>
                {DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </td>
            <td className="px-[16px] py-[8px]">
              <input placeholder="Title" className={inputCls} value={newDraft.title} onChange={(e) => setNewDraft((d) => ({ ...d, title: e.target.value }))} />
            </td>
            <td className="px-[16px] py-[8px] text-[#98a2b3] text-[11.5px]">Active</td>
            <td className="px-[16px] py-[8px]">
              <button
                type="button"
                onClick={submitNew}
                disabled={adding || !newDraft.name.trim()}
                className="flex items-center gap-[5px] ml-auto text-[12px] font-semibold text-[#3a5bd9] disabled:opacity-40"
              >
                <Plus size={14} strokeWidth={2.5} />
                Add
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </Card>
  );
}
