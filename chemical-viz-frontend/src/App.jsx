import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

import {
  UploadCloud,
  FileText,
  Trash2,
  Download,
  CheckCircle,
  BarChart3,
  Table,
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
);

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [alert, setAlert] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("charts");
  const [isRegistering, setIsRegistering] = useState(false);
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
  });

  useEffect(() => {
    if (authenticated) fetchHistory();
  }, [authenticated]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setAlert(null);

    try {
      const token = btoa(`${username}:${password}`);

      const res = await api.get("/api/history/", {
        headers: { Authorization: `Basic ${token}` },
      });

      setAuthenticated(true);
      setAlert({ type: "success", text: "Login successful" });
      setHistory(res.data || []);
    } catch (err) {
      setAlert({ type: "error", text: "Invalid credentials or server error" });
      console.error(err);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAlert(null);

    if (password.length < 6) {
      setAlert({ type: "error", text: "Password must be at least 6 characters long" });
      return;
    }

    try {
      const res = await api.post("/api/register/", {
        username,
        password,
        email,
      });

      setAlert({ type: "success", text: res.data.message || "Registration successful! Please login." });
      setTimeout(() => {
        setIsRegistering(false);
        setPassword("");
        setEmail("");
      }, 2000);
    } catch (err) {
      const errorMsg = err.response?.data?.error || "Registration failed";
      setAlert({ type: "error", text: errorMsg });
      console.error(err);
    }
  };
  const fetchHistory = async () => {
    try {
      const token = btoa(`${username}:${password}`);
      const res = await api.get("/api/history/", {
        headers: { Authorization: `Basic ${token}` },
      });

      setHistory(res.data || []);
    } catch (err) {
      setAlert({ type: "error", text: "Failed to load history" });
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      const token = btoa(`${username}:${password}`);

      const uploadResponse = await api.post("/api/upload/", form, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Basic ${token}`,
        },
      });

      setAlert({ type: "success", text: "File uploaded successfully" });
      await fetchHistory();
      
      const newDataset = uploadResponse.data;
      if (newDataset && newDataset.id) {
        setSelectedHistory(newDataset);
        await fetchSummary(newDataset.id);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || "Upload failed";
      setAlert({ type: "error", text: errorMsg });
      console.error("Upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  const onFileSelected = (e) => {
    handleFileUpload(e.target.files?.[0]);
    e.target.value = null;
  };

  const fetchSummary = async (id) => {
    if (!id) return;

    try {
      const token = btoa(`${username}:${password}`);
      const res = await api.get(`/api/summary/?id=${id}`, {
        headers: { Authorization: `Basic ${token}` },
      });

      setSummary(res.data);
    } catch (err) {
      setAlert({ type: "error", text: "Failed to fetch summary" });
    }
  };

  const handleDownloadPDF = async (id) => {
    try {
      const token = btoa(`${username}:${password}`);

      const res = await api.get(`/api/report/?id=${id}`, {
        headers: { Authorization: `Basic ${token}` },
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `report-${id}.pdf`;
      link.click();
      link.remove();
    } catch (err) {
      setAlert({ type: "error", text: "Failed to download PDF" });
    }
  };

  const buildBarData = (data) =>
    data
      ? {
          labels: data.labels || [],
          datasets: [
            {
              label: data.title || "Values",
              data: data.values || [],
              backgroundColor: "#6366f1",
              borderRadius: 6,
            },
          ],
        }
      : { labels: [], datasets: [] };

  const buildDoughnutData = (data) =>
    data
      ? {
          labels: data.categories || [],
          datasets: [
            {
              data: data.counts || [],
              backgroundColor: [
                "#6366f1",
                "#8b5cf6",
                "#ec4899",
                "#f59e0b",
                "#10b981",
              ],
            },
          ],
        }
      : { labels: [], datasets: [] };

  if (!authenticated) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-icon">
              <FileText color="white" size={32} />
            </div>
            <h1 className="login-title">{isRegistering ? "Create Account" : "Welcome Back"}</h1>
            <p className="login-subtitle">
              {isRegistering ? "Register for Chemical Data Visualizer" : "Sign in to Chemical Data Visualizer"}
            </p>
          </div>

          {alert && (
            <div className={`alert ${alert.type === "success" ? "alert-success" : "alert-error"}`}>
              {alert.text}
            </div>
          )}

          <form onSubmit={isRegistering ? handleRegister : handleLogin}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="form-input"
                required
              />
            </div>

            {isRegistering && (
              <div className="form-group">
                <label className="form-label">Email (Optional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="form-input"
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegistering ? "At least 6 characters" : "Enter your password"}
                className="form-input"
                required
              />
            </div>

            <button type="submit" className="btn-primary">
              {isRegistering ? "Create Account" : "Sign in"}
            </button>
          </form>

          <div className="auth-toggle">
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setAlert(null);
                setPassword("");
                setEmail("");
              }}
              className="btn-link"
            >
              {isRegistering ? "Already have an account? Sign in" : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <div className="header-icon">
            <FileText color="white" size={20} />
          </div>
          <div>
            <div className="header-title">Chemical Data Visualizer</div>
            <div className="header-subtitle">Upload, analyze, and visualize datasets</div>
          </div>
        </div>

        <button
          onClick={() => {
            setAuthenticated(false);
            setUsername("");
            setPassword("");
          }}
          className="btn-secondary"
        >
          Sign out
        </button>
      </header>

      <div className="main-layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h4 className="sidebar-title">Upload Files</h4>
            
            <div className="upload-card">
              <label>
                <input
                  ref={fileInputRef}
                  type="file"
                  style={{ display: "none" }}
                  onChange={onFileSelected}
                  accept=".csv,.json"
                />
                <div className="upload-content">
                  <div className="upload-icon">
                    <UploadCloud color="white" size={20} />
                  </div>
                  <div className="upload-text">
                    <div className="upload-title">Upload dataset</div>
                    <div className="upload-subtitle">CSV / JSON files</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-upload"
                >
                  <UploadCloud size={16} />
                  Choose File
                </button>
              </label>
            </div>
          </div>

          <div className="sidebar-section">
            <h4 className="sidebar-title">History</h4>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="empty-state">No uploads yet</div>
              ) : (
                history.map((h) => (
                  <div
                    key={h.id}
                    onClick={() => {
                      setSelectedHistory(h);
                      fetchSummary(h.id);
                    }}
                    className={`history-item ${selectedHistory?.id === h.id ? "selected" : ""}`}
                  >
                    <div className="history-content">
                      <div className="history-info">
                        <div className="history-name">
                          {h.name || `Upload #${h.id}`}
                        </div>
                        <div className="history-date">
                          {new Date(h.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="history-actions">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownloadPDF(h.id);
                          }}
                          className="btn-icon success"
                        >
                          <Download size={16} />
                        </button>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              const token = btoa(`${username}:${password}`);
                              await api.delete(`/api/history/${h.id}/`, {
                                headers: { Authorization: `Basic ${token}` },
                              });
                              fetchHistory();
                            } catch (err) {
                              setAlert({ type: "error", text: "Delete failed" });
                            }
                          }}
                          className="btn-icon error"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        <main className="content">
          <div className="summary-card">
            <div className="summary-header">
              <div>
                <div className="summary-title">Selected Dataset</div>
                <div className="summary-subtitle">
                  {selectedHistory?.name || "Select a file from history to view analytics"}
                </div>
              </div>
              {selectedHistory && (
                <button
                  onClick={() => handleDownloadPDF(selectedHistory.id)}
                  className="btn-download"
                >
                  <Download size={16} />
                  Download PDF
                </button>
              )}
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Records</div>
                <div className="stat-value success">
                  {summary?.records ?? "—"}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Unique Categories</div>
                <div className="stat-value accent">
                  {summary?.categories?.length ?? "—"}
                </div>
              </div>
            </div>
          </div>

          <div className="tab-navigation">
            <button
              onClick={() => setActiveTab("charts")}
              className={`tab-button ${activeTab === "charts" ? "active" : ""}`}
            >
              <BarChart3 size={16} />
              Charts & Analytics
            </button>
            <button
              onClick={() => setActiveTab("data")}
              className={`tab-button ${activeTab === "data" ? "active" : ""}`}
            >
              <Table size={16} />
              Data Table & Statistics
            </button>
          </div>

          {activeTab === "charts" && (
            <div className="charts-grid">
              <div className="chart-card">
                <div className="chart-title">Bar Chart Analysis</div>
                <div className="chart-container">
                  <Bar
                    data={buildBarData(summary?.bar)}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          backgroundColor: "#0f172a",
                          titleColor: "#ffffff",
                          bodyColor: "#ffffff",
                          borderColor: "#6366f1",
                          borderWidth: 1,
                          padding: 10,
                          cornerRadius: 6,
                        },
                      },
                      scales: {
                        x: {
                          ticks: { color: "#94a3b8", font: { size: 11 } },
                          grid: { color: "rgba(255, 255, 255, 0.05)" },
                        },
                        y: {
                          ticks: { color: "#94a3b8", font: { size: 11 } },
                          grid: { color: "rgba(255, 255, 255, 0.05)" },
                        },
                      },
                    }}
                  />
                </div>
              </div>

              <div className="chart-card">
                <div className="chart-title">Category Distribution</div>
                <div className="chart-container">
                  <Doughnut
                    data={buildDoughnutData(summary?.doughnut)}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: "bottom",
                          labels: {
                            color: "#ffffff",
                            padding: 12,
                            font: { size: 11 },
                          },
                        },
                        tooltip: {
                          backgroundColor: "#0f172a",
                          titleColor: "#ffffff",
                          bodyColor: "#ffffff",
                          borderColor: "#6366f1",
                          borderWidth: 1,
                          padding: 10,
                          cornerRadius: 6,
                        },
                      },
                    }}
                  />
                </div>
              </div>

              {summary?.averages && (
                <div className="chart-card full-width">
                  <div className="chart-title">Parameter Averages</div>
                  <div className="averages-grid">
                    <div className="average-item">
                      <div className="average-label">Flowrate</div>
                      <div className="average-value">{summary.averages.flowrate?.toFixed(2) || "0.00"}</div>
                      <div className="average-unit">L/min</div>
                    </div>
                    <div className="average-item">
                      <div className="average-label">Pressure</div>
                      <div className="average-value">{summary.averages.pressure?.toFixed(2) || "0.00"}</div>
                      <div className="average-unit">bar</div>
                    </div>
                    <div className="average-item">
                      <div className="average-label">Temperature</div>
                      <div className="average-value">{summary.averages.temperature?.toFixed(2) || "0.00"}</div>
                      <div className="average-unit">°C</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "data" && (
            <div className="data-section">
              {summary?.data_preview && summary.data_preview.length > 0 ? (
                <>
                  <div className="data-card">
                    <div className="data-title">Data Preview (First 5 Rows)</div>
                    <div className="table-container">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Equipment Name</th>
                            <th>Type</th>
                            <th>Flowrate (L/min)</th>
                            <th>Pressure (bar)</th>
                            <th>Temperature (°C)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {summary.data_preview.map((row, index) => (
                            <tr key={index}>
                              <td>{row["Equipment Name"] || "N/A"}</td>
                              <td>{row["Type"] || "N/A"}</td>
                              <td>{typeof row["Flowrate"] === 'number' ? row["Flowrate"].toFixed(2) : "N/A"}</td>
                              <td>{typeof row["Pressure"] === 'number' ? row["Pressure"].toFixed(2) : "N/A"}</td>
                              <td>{typeof row["Temperature"] === 'number' ? row["Temperature"].toFixed(2) : "N/A"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="statistics-grid">
                    <div className="stat-detail-card">
                      <div className="stat-detail-title">Dataset Statistics</div>
                      <div className="stat-detail-content">
                        <div className="stat-row">
                          <span className="stat-label">Total Records:</span>
                          <span className="stat-value">{summary.records || 0}</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Equipment Types:</span>
                          <span className="stat-value">{summary.categories?.length || 0}</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Avg Flowrate:</span>
                          <span className="stat-value">{summary.averages?.flowrate?.toFixed(2) || "0.00"} L/min</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Avg Pressure:</span>
                          <span className="stat-value">{summary.averages?.pressure?.toFixed(2) || "0.00"} bar</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Avg Temperature:</span>
                          <span className="stat-value">{summary.averages?.temperature?.toFixed(2) || "0.00"} °C</span>
                        </div>
                      </div>
                    </div>

                    <div className="stat-detail-card">
                      <div className="stat-detail-title">Equipment Type Distribution</div>
                      <div className="stat-detail-content">
                        {summary.bar?.labels?.map((label, index) => (
                          <div key={index} className="stat-row">
                            <span className="stat-label">{label}:</span>
                            <span className="stat-value">{summary.bar.values[index]} units</span>
                          </div>
                        )) || <div className="stat-row">No data available</div>}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-data-state">
                  <Table size={48} color="#6b7280" />
                  <div className="empty-data-title">No Data Available</div>
                  <div className="empty-data-subtitle">
                    Upload a CSV file to view data tables and statistics
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      <div className="status-badge">
        <CheckCircle color="#22c55e" size={16} />
        <span className="status-text">Connected</span>
      </div>
    </div>
  );
}
