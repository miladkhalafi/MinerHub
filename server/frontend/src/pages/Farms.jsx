import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../utils/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Plus, ChevronRight, Edit2, Trash2 } from "lucide-react";

export default function Farms() {
  const [farms, setFarms] = useState([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    apiFetch("/farms")
      .then((r) => r.json())
      .then(setFarms)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const createFarm = async (e) => {
    e.preventDefault();
    if (!name.trim() || creating) return;
    setCreating(true);
    try {
      const r = await apiFetch("/farms", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      });
      const data = await r.json();
      setFarms((f) => [...f, data]);
      setName("");
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (farm) => {
    setEditingId(farm.id);
    setEditingName(farm.name);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingName("");
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    if (!editingName.trim() || !editingId) return;
    try {
      const r = await apiFetch(`/farms/${editingId}`, {
        method: "PATCH",
        body: JSON.stringify({ name: editingName.trim() }),
      });
      const data = await r.json();
      setFarms((f) => f.map((x) => (x.id === editingId ? data : x)));
      cancelEdit();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteFarm = async (farm) => {
    if (!window.confirm(`Delete farm "${farm.name}"? This will remove all agents and miners.`)) return;
    setDeletingId(farm.id);
    try {
      await apiFetch(`/farms/${farm.id}`, { method: "DELETE" });
      setFarms((f) => f.filter((x) => x.id !== farm.id));
    } catch (e) {
      console.error(e);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-500 dark:text-slate-500">Loading farms...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Farms</h1>
        <p className="mt-1 text-sm text-slate-500">Manage your mining farms and agents</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add Farm</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={createFarm} className="flex gap-3 flex-wrap items-end">
            <div className="flex-1 min-w-[200px] space-y-2">
              <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Farm name</label>
              <Input
                placeholder="e.g. North Warehouse"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={creating || !name.trim()} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Farm
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Farms</CardTitle>
        </CardHeader>
        <CardContent>
          {farms.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              No farms yet. Add one above to get started.
            </div>
          ) : (
            <div className="divide-y divide-slate-200 dark:divide-slate-700/50">
              {farms.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between gap-4 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/30 -mx-2 px-2 rounded-md transition-colors group"
                >
                  {editingId === f.id ? (
                    <form onSubmit={saveEdit} className="flex gap-2 flex-1">
                      <Input
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        placeholder="Farm name"
                        className="max-w-xs"
                        autoFocus
                      />
                      <Button type="submit" size="sm">Save</Button>
                      <Button type="button" variant="outline" size="sm" onClick={cancelEdit}>Cancel</Button>
                    </form>
                  ) : (
                    <>
                      <Link
                        to={`/farms/${f.id}`}
                        className="flex items-center gap-2 flex-1 min-w-0"
                      >
                        <span className="font-medium text-slate-800 dark:text-slate-200 group-hover:text-sky-500 dark:group-hover:text-sky-400 transition-colors truncate">{f.name}</span>
                        <ChevronRight className="h-5 w-5 text-slate-500 group-hover:text-sky-500 dark:group-hover:text-sky-400 transition-colors shrink-0" />
                      </Link>
                      <div className="flex gap-2 shrink-0" onClick={(e) => e.preventDefault()}>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEdit(f)}
                          className="gap-1.5 opacity-70 group-hover:opacity-100"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => deleteFarm(f)}
                          disabled={deletingId === f.id}
                          className="gap-1.5 opacity-70 group-hover:opacity-100"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          {deletingId === f.id ? "..." : "Delete"}
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
