import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API } from "../App";

export default function Farms() {
  const [farms, setFarms] = useState([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetch(`${API}/farms`)
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
      const r = await fetch(`${API}/farms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Farms</h2>
        <form onSubmit={createFarm} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <input
            placeholder="Farm name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ flex: 1, maxWidth: 300 }}
          />
          <button type="submit" className="primary" disabled={creating || !name.trim()}>
            Add Farm
          </button>
        </form>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {farms.map((f) => (
              <tr key={f.id}>
                <td>{f.name}</td>
                <td>
                  <Link to={`/farms/${f.id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
