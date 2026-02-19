import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";

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
      style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 400 }}
    >
      <div>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>Worker 1</label>
        <input value={worker1} onChange={(e) => setWorker1(e.target.value)} style={{ width: "100%" }} />
      </div>
      <div>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>Worker 2</label>
        <input value={worker2} onChange={(e) => setWorker2(e.target.value)} style={{ width: "100%" }} />
      </div>
      <div>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>Worker 3</label>
        <input value={worker3} onChange={(e) => setWorker3(e.target.value)} style={{ width: "100%" }} />
      </div>
      <div>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>Password (leave blank to keep)</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" style={{ width: "100%" }} />
      </div>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button type="submit" className="primary">Save</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

export default function FarmDetail() {
  const { id: farmId } = useParams();
  const [farm, setFarm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [discovered, setDiscovered] = useState([]);
  const [editingMiner, setEditingMiner] = useState(null);

  const load = () => {
    fetch(`${API}/farms/${farmId}`)
      .then((r) => r.json())
      .then(setFarm)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [farmId]);

  const addAgent = async () => {
    try {
      const r = await fetch(`${API}/farms/${farmId}/agents`, { method: "POST" });
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
      const r = await fetch(`${API}/agents/${farm.agent.id}/scan`, { method: "POST" });
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
      await fetch(`${API}/agents/${farm.agent.id}/miners/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      await fetch(`${API}/miners/${minerId}/restart`, { method: "POST" });
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const powerOffMiner = async (minerId) => {
    try {
      await fetch(`${API}/miners/${minerId}/power_off`, { method: "POST" });
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const updateMiner = async (minerId, data) => {
    try {
      await fetch(`${API}/miners/${minerId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      setEditingMiner(null);
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const copyInstall = () => {
    if (farm?.agent?.install_script) {
      navigator.clipboard?.writeText(farm.agent.install_script);
      alert("Copied to clipboard");
    }
  };

  if (loading || !farm) return <div>Loading...</div>;

  return (
    <div>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/">← Back to Farms</Link>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{farm.name}</h2>

        {!farm.agent ? (
          <div>
            <p>No agent registered.</p>
            <button onClick={addAgent} className="primary">
              Add Agent
            </button>
          </div>
        ) : (
          <div>
            <h3>Agent</h3>
            <p>Status: {farm.agent.last_seen ? "Last seen " + new Date(farm.agent.last_seen).toLocaleString() : "Unknown"}</p>
            <div style={{ marginBottom: "1rem" }}>
              <strong>Install:</strong>{" "}
              <code style={{ fontSize: "0.75rem", wordBreak: "break-all" }}>{farm.agent.install_script || "curl ..."}</code>
              <button onClick={copyInstall} style={{ marginLeft: "0.5rem" }}>
                Copy
              </button>
            </div>
            <button onClick={scanForMiners} className="primary" disabled={scanning}>
              {scanning ? "Scanning..." : "Scan for new miners"}
            </button>
          </div>
        )}
      </div>

      {discovered.length > 0 && (
        <div className="card">
          <h3>Discovered Miners</h3>
          <table>
            <thead>
              <tr>
                <th>MAC</th>
                <th>IP</th>
                <th>Model</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {discovered.map((m) => (
                <tr key={m.mac}>
                  <td>{m.mac}</td>
                  <td>{m.ip}</td>
                  <td>{m.model || "-"}</td>
                  <td>
                    {m.ip && (
                      <a href={`http://${m.ip}`} target="_blank" rel="noreferrer" style={{ marginRight: "0.5rem" }}>
                        Web UI
                      </a>
                    )}
                    <button onClick={() => registerMiner(m)} className="primary">
                      Register
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card">
        <h3>Miners</h3>
        {!farm.agent?.miners?.length ? (
          <p>No miners. Scan for new miners above.</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>MAC</th>
                  <th>IP</th>
                  <th>Model</th>
                  <th>Web UI</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {farm.agent.miners.map((m) => (
                  <tr key={m.id}>
                    <td>{m.mac}</td>
                    <td>{m.ip}</td>
                    <td>{m.model || "-"}</td>
                    <td>
                      {m.ip ? (
                        <a href={`http://${m.ip}`} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      ) : "-"}
                    </td>
                    <td>
                      <button onClick={() => setEditingMiner(m)} style={{ marginRight: "0.5rem" }}>
                        Edit
                      </button>
                      <button onClick={() => restartMiner(m.id)} style={{ marginRight: "0.5rem" }}>
                        Restart
                      </button>
                      <button onClick={() => powerOffMiner(m.id)} className="danger" style={{ marginRight: "0.5rem" }}>
                        Power Off
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {editingMiner && (
              <div className="card" style={{ marginTop: "1rem" }}>
                <h4>Edit Miner {editingMiner.mac}</h4>
                <MinerEditForm
                  miner={editingMiner}
                  onSave={(data) => updateMiner(editingMiner.id, data)}
                  onCancel={() => setEditingMiner(null)}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
