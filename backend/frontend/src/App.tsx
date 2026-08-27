import { NavLink, Route, Routes } from "react-router-dom";
import { CaseProvider, useCase } from "./lib/CaseContext";
import { DocumentsPage } from "./pages/DocumentsPage";
import { RunsPage } from "./pages/RunsPage";
import { FindingsPage } from "./pages/FindingsPage";
import { ReportPage } from "./pages/ReportPage";

function CasePicker() {
  const { caseId, setCaseId } = useCase();

  return (
    <div className="case-picker">
      <label htmlFor="case-id">Active case</label>
      <input
        id="case-id"
        type="text"
        placeholder="CASE-ACME-001"
        value={caseId}
        onChange={(event) => setCaseId(event.target.value)}
      />
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">Docsnary</span>
        <span className="brand-sub">Evidence-Backed Review</span>
      </div>

      <nav className="nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Documents
        </NavLink>
        <NavLink
          to="/runs"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Runs
        </NavLink>
        <NavLink
          to="/findings"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Findings Review
        </NavLink>
        <NavLink
          to="/report"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Case Report
        </NavLink>
      </nav>

      <CasePicker />
    </aside>
  );
}

export default function App() {
  return (
    <CaseProvider>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<DocumentsPage />} />
            <Route path="/runs" element={<RunsPage />} />
            <Route path="/findings" element={<FindingsPage />} />
            <Route path="/report" element={<ReportPage />} />
          </Routes>
        </main>
      </div>
    </CaseProvider>
  );
}
