import { useState, useEffect, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { apiFetch } from "../utils/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { ArrowLeft, Copy, Plus, RefreshCw, Edit2, Power, PowerOff, ExternalLink, Trash2 } from "lucide-react";

function MinerEditForm({ miner, onSave, onCancel }) {
  const [worker1, setWorker1] = useState(miner.worker1 || "");
  const [worker2, setWorker2] = useState(miner.worker2 || "");
  const [worker3, setWorker3] = useState(miner.worker3 || "");
  const [password, setPassword] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSave({ worker1, worker2, worker3, password: password || undefined });
      }}
      className="space-y-4 max-w-md"
    >
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">Worker 1</label>
          <Input value={worker1} onChange={(e) => setWorker1(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">Worker 2</label>
          <Input value={worker2} onChange={(e) => setWorker2(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">Worker 3</label>
          <Input value={worker3} onChange={(e) => setWorker3(e.target.value)} />
        </div>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-400">Password (leave blank to keep)</label>
        <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
      </div>
      <div className="flex gap-2">
        <Button type="submit">Save</Button>
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}

export default function FarmDetail() {
  const { id: farmId } = useParams();
  const navigate = useNavigate();
  const [farm, setFarm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [discovered, setDiscovered] = useState([]);
  const [editingMiner, setEditingMiner] = useState(null);
  const [editingFarm, setEditingFarm] = useState(false);
  const [farmName, setFarmName] = useState("");
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(() => {
    setError(null);
    apiFetch(`/farms/${farmId}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "Farm not found" : `Failed to load: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setFarm(data);
        setError(null);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setFarm(null);
      })
      .finally(() => setLoading(false));
  }, [farmId]);

  useEffect(() => {
    load();
  }, [load]);

  const addAgent = async () => {
    try {
      const r = await apiFetch(`/farms/${farmId}/agents`, { method: "POST" });
      const data = await r.json();
      load();
      if (data.token) {
        navigator.clipboard?.writeText(data.install_script);
        alert("Install script copied to clipboard:\n" + data.install_script);
      }
    } catch (e) {
      console.error(e);
      alert("Failed to add agent");
    }
  };

  const scanForMiners = async () => {
    if (!farm?.agent?.id || scanning) return;
    setScanning(true);
    try {
      const r = await apiFetch(`/agents/${farm.agent.id}/scan`, { method: "POST" });
      const data = await r.json();
      setDiscovered(data.discovered || []);
      if (data.status === "queued") {
        alert("Agent offline - scan queued. Run again when agent is connected.");
      }
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setScanning(false);
    }
  };

  const registerMiner = async (m) => {
    try {
      await apiFetch(`/agents/${farm.agent.id}/miners/register`, {
        method: "POST",
        body: JSON.stringify({ miners: [{ mac: m.mac, ip: m.ip, model: m.model }] }),
      });
      setDiscovered((d) => d.filter((x) => x.mac !== m.mac));
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const restartMiner = async (minerId) => {
    try {
      await apiFetch(`/miners/${minerId}/restart`, { method: "POST" });
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const powerOffMiner = async (minerId) => {
    try {
      await apiFetch(`/miners/${minerId}/power_off`, { method: "POST" });
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const updateMiner = async (minerId, data) => {
    try {
      await apiFetch(`/miners/${minerId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      setEditingMiner(null);
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const startEditFarm = () => {
    setFarmName(farm.name);
    setEditingFarm(true);
  };

  const cancelEditFarm = () => {
    setEditingFarm(false);
    setFarmName("");
  };

  const saveFarm = async (e) => {
    e.preventDefault();
    if (!farmName.trim()) return;
    try {
      const r = await apiFetch(`/farms/${farmId}`, {
        method: "PATCH",
        body: JSON.stringify({ name: farmName.trim() }),
      });
      const data = await r.json();
      setFarm((prev) => ({ ...prev, ...data }));
      cancelEditFarm();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteFarm = async () => {
    if (!window.confirm(`Delete farm "${farm.name}"? This will remove all agents and miners.`)) return;
    setDeleting(true);
    try {
      await apiFetch(`/farms/${farmId}`, { method: "DELETE" });
      navigate("/");
    } catch (e) {
      console.error(e);
    } finally {
      setDeleting(false);
    }
  };

  const copyInstall = () => {
    if (farm?.agent?.install_script) {
      navigator.clipboard?.writeText(farm.agent.install_script);
      alert("Copied to clipboard");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-500">Loading...</div>
      </div>
    );
  }
  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-red-400">{error}</p>
          <Link to="/" className="inline-flex items-center gap-2 mt-4 text-sky-400 hover:text-sky-300">
            <ArrowLeft className="h-4 w-4" />
            Back to Farms
          </Link>
        </CardContent>
      </Card>
    );
  }
  if (!farm) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Farms
        </Link>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        {editingFarm ? (
          <form onSubmit={saveFarm} className="flex gap-2 items-center">
            <Input
              value={farmName}
              onChange={(e) => setFarmName(e.target.value)}
              placeholder="Farm name"
              className="max-w-xs"
              autoFocus
            />
            <Button type="submit" size="sm">Save</Button>
            <Button type="button" variant="outline" size="sm" onClick={cancelEditFarm}>Cancel</Button>
          </form>
        ) : (
          <>
            <h1 className="text-2xl font-semibold text-slate-100">{farm.name}</h1>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={startEditFarm} className="gap-1.5">
                <Edit2 className="h-3.5 w-3.5" />
                Edit Farm
              </Button>
              <Button variant="destructive" size="sm" onClick={deleteFarm} disabled={deleting} className="gap-1.5">
                <Trash2 className="h-3.5 w-3.5" />
                {deleting ? "Deleting..." : "Delete Farm"}
              </Button>
            </div>
          </>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Agent</CardTitle>
        </CardHeader>
        <CardContent>
          {!farm.agent ? (
            <div className="space-y-4">
              <p className="text-slate-400">No agent registered.</p>
              <Button onClick={addAgent} className="gap-2">
                <Plus className="h-4 w-4" />
                Add Agent
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Status: {farm.agent.last_seen ? "Last seen " + new Date(farm.agent.last_seen).toLocaleString() : "Unknown"}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <code className="flex-1 min-w-0 text-xs text-slate-500 bg-slate-900/50 px-2 py-1.5 rounded truncate">
                  {farm.agent.install_script || "curl ..."}
                </code>
                <Button variant="outline" size="sm" onClick={copyInstall} className="gap-1.5 shrink-0">
                  <Copy className="h-4 w-4" />
                  Copy
                </Button>
              </div>
              <Button onClick={scanForMiners} disabled={scanning} className="gap-2">
                <RefreshCw className={`h-4 w-4 ${scanning ? "animate-spin" : ""}`} />
                {scanning ? "Scanning..." : "Scan for new miners"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {discovered.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Discovered Miners</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">MAC</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">IP</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Model</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {discovered.map((m) => (
                    <tr key={m.mac} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                      <td className="py-3 px-4 text-slate-200">{m.mac}</td>
                      <td className="py-3 px-4 text-slate-200">{m.ip}</td>
                      <td className="py-3 px-4 text-slate-400">{m.model || "-"}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          {m.ip && (
                            <a
                              href={`http://${m.ip}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sky-400 hover:text-sky-300 text-sm"
                            >
                              Web UI
                            </a>
                          )}
                          <Button size="sm" onClick={() => registerMiner(m)}>
                            Register
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
      )}

      <Card>
        <CardHeader>
          <CardTitle>Miners</CardTitle>
        </CardHeader>
        <CardContent>
          {!farm.agent?.miners?.length ? (
            <p className="text-slate-500 py-4">No miners. Scan for new miners above.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">MAC</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">IP</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Model</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Web UI</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {farm.agent.miners.map((m) => (
                      <tr key={m.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                        <td className="py-3 px-4 text-slate-200">{m.mac}</td>
                        <td className="py-3 px-4 text-slate-200">{m.ip}</td>
                        <td className="py-3 px-4 text-slate-400">{m.model || "-"}</td>
                        <td className="py-3 px-4">
                          {m.ip ? (
                            <a
                              href={`http://${m.ip}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300 text-sm"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                              Open
                            </a>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-2 flex-wrap">
                            <Button variant="outline" size="sm" onClick={() => setEditingMiner(m)} className="gap-1">
                              <Edit2 className="h-3.5 w-3.5" />
                              Edit
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => restartMiner(m.id)} className="gap-1">
                              <RefreshCw className="h-3.5 w-3.5" />
                              Restart
                            </Button>
                            <Button variant="destructive" size="sm" onClick={() => powerOffMiner(m.id)} className="gap-1">
                              <PowerOff className="h-3.5 w-3.5" />
                              Power Off
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {editingMiner && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle>Edit Miner {editingMiner.mac}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MinerEditForm
                      miner={editingMiner}
                      onSave={(data) => updateMiner(editingMiner.id, data)}
                      onCancel={() => setEditingMiner(null)}
                    />
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
