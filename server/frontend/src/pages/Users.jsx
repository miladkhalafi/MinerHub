import { useState, useEffect } from "react";
import { apiFetch } from "../utils/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Plus, Pencil, Trash2 } from "lucide-react";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ email: "", password: "", role: "user" });

  const load = () => {
    apiFetch("/users")
      .then((r) => r.json())
      .then(setUsers)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.email.trim() || !form.password || creating) return;
    setCreating(true);
    try {
      const r = await apiFetch("/users", {
        method: "POST",
        body: JSON.stringify({
          email: form.email.trim(),
          password: form.password,
          role: form.role,
        }),
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to create user");
      }
      setForm({ email: "", password: "", role: "user" });
      load();
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editing || !form.email.trim()) return;
    try {
      const body = { email: form.email.trim(), role: form.role };
      if (form.password && form.password.trim()) body.password = form.password;
      const r = await apiFetch(`/users/${editing.id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to update user");
      }
      setEditing(null);
      setForm({ email: "", password: "", role: "user" });
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (user) => {
    if (!confirm(`Delete user ${user.email}?`)) return;
    try {
      const r = await apiFetch(`/users/${user.id}`, { method: "DELETE" });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to delete user");
      }
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  const startEdit = (u) => {
    setEditing(u);
    setForm({ email: u.email, password: "", role: u.role });
  };

  const cancelEdit = () => {
    setEditing(null);
    setForm({ email: "", password: "", role: "user" });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-500">Loading users...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Users</h1>
        <p className="mt-1 text-sm text-slate-500">Manage dashboard users and roles</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{editing ? "Edit User" : "Add User"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={editing ? handleUpdate : handleCreate}
            className="flex flex-wrap gap-4 items-end"
          >
            <div className="min-w-[200px] space-y-2">
              <label className="text-sm font-medium text-slate-400">Email</label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="user@example.com"
                required
              />
            </div>
            <div className="min-w-[140px] space-y-2">
              <label className="text-sm font-medium text-slate-400">
                Password {editing && "(leave blank to keep)"}
              </label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="••••••••"
                required={!editing}
              />
            </div>
            <div className="min-w-[100px] space-y-2">
              <label className="text-sm font-medium text-slate-400">Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
                className="flex h-10 w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={creating} className="gap-1.5">
                {editing ? (
                  <>
                    <Pencil className="h-4 w-4" />
                    Update
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    Add User
                  </>
                )}
              </Button>
              {editing && (
                <Button type="button" variant="outline" onClick={cancelEdit}>
                  Cancel
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Email</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                    <td className="py-3 px-4 text-slate-200">{u.email}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-slate-700/50 text-slate-300">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => startEdit(u)} className="gap-1">
                          <Pencil className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button variant="destructive" size="sm" onClick={() => handleDelete(u)} className="gap-1">
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
