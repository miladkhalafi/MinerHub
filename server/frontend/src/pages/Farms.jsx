import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../utils/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Plus, ChevronRight } from "lucide-react";

export default function Farms() {
  const [farms, setFarms] = useState([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-500">Loading farms...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Farms</h1>
        <p className="mt-1 text-sm text-slate-500">Manage your mining farms and agents</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add Farm</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={createFarm} className="flex gap-3 flex-wrap items-end">
            <div className="flex-1 min-w-[200px] space-y-2">
              <label className="text-sm font-medium text-slate-400">Farm name</label>
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
            <div className="divide-y divide-slate-700/50">
              {farms.map((f) => (
                <Link
                  key={f.id}
                  to={`/farms/${f.id}`}
                  className="flex items-center justify-between py-4 hover:bg-slate-800/30 -mx-2 px-2 rounded-md transition-colors group"
                >
                  <span className="font-medium text-slate-200">{f.name}</span>
                  <ChevronRight className="h-5 w-5 text-slate-500 group-hover:text-sky-400 transition-colors" />
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
