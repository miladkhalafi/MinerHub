import { Routes, Route, Link } from "react-router-dom";
import Farms from "./pages/Farms";
import FarmDetail from "./pages/FarmDetail";

const API = "";  // Same origin when proxied

export { API };

export default function App() {
  return (
    <div style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto" }}>
      <nav style={{ marginBottom: "1.5rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
        <Link to="/" style={{ fontSize: "1.25rem", fontWeight: 600 }}>
          Miner Agent Dashboard
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Farms />} />
        <Route path="/farms/:id" element={<FarmDetail />} />
      </Routes>
    </div>
  );
}
