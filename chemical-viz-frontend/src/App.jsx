import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import axios from 'axios';
import { LogIn, Upload, History, FileText, BarChart, PieChart, Loader2, ServerOff, CheckCircle } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

// --- Configuration ---
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// --- Utility Components ---

/** A simple component to display error or status messages. */
const Message = ({ type, children }) => {
  const bgColor = type === 'error' ? 'bg-red-500' : type === 'success' ? 'bg-green-500' : 'bg-blue-500';
  const Icon = type === 'success' ? CheckCircle : type === 'error' ? ServerOff : Loader2;
  // Determine animation class based on type
  const animationClass = type === 'info' ? 'animate-pulse' : ''; 
  
  return (
    <div className={`p-3 rounded-lg shadow-md flex items-center space-x-3 ${bgColor} text-white`}>
      <Icon className={`w-5 h-5 ${animationClass}`} />
      <p className="font-medium text-sm">{children}</p>
    </div>
  );
};

/**
 * Main application component.
 * Manages authentication, state, and rendering of all sub-sections.
 */
const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authHeader, setAuthHeader] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  const [history, setHistory] = useState([]);
  const [currentSummary, setCurrentSummary] = useState(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);

  const [uploadFile, setUploadFile] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);

  // --- Authentication Handler ---

  const handleLogin = async (e) => {
    e.preventDefault();
    setStatusMessage(null);
    setIsLoading(true);

    try {
      const authString = btoa(`${username}:${password}`);
      const headers = {
        Authorization: `Basic ${authString}`,
      };
      
      // Attempt to access a protected endpoint (history) to verify credentials
      await axios.get(`${API_BASE_URL}/history/`, { headers });

      // If successful:
      setAuthHeader(`Basic ${authString}`);
      setIsLoggedIn(true);
      setStatusMessage({ type: 'success', text: 'Login successful! Welcome.' });
      
    } catch (error) {
      console.error('Login failed:', error);
      setStatusMessage({ type: 'error', text: 'Login failed. Check username and password.' });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLogout = () => {
    setIsLoggedIn(false);
    setAuthHeader('');
    setUsername('');
    setPassword('');
    setHistory([]);
    setCurrentSummary(null);
    setSelectedDatasetId(null);
    setStatusMessage(null);
  };

  // --- API Handlers (Protected) ---

  const fetchHistory = useCallback(async () => {
    if (!authHeader) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/history/`, {
        headers: { Authorization: authHeader }
      });
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
      setStatusMessage({ type: 'error', text: 'Failed to load history data.' });
    }
  }, [authHeader]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setStatusMessage({ type: 'error', text: 'Please select a file first.' });
      return;
    }
    
    setStatusMessage({ type: 'info', text: 'Uploading and analyzing data...' });
    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
        headers: { 
          Authorization: authHeader,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setStatusMessage({ type: 'success', text: `Upload success: ${response.data.name}. Processing complete.` });
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      
      // Auto-refresh history and load new summary
      await fetchHistory();
      setSelectedDatasetId(response.data.id);
      fetchSummary(response.data.id);
      
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error.response?.data?.error || 'An unexpected error occurred during upload.';
      setStatusMessage({ type: 'error', text: `Upload failed: ${errorMessage}` });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSummary = async (id) => {
    if (!authHeader) return;
    setStatusMessage(null);
    setIsLoading(true);
    setSelectedDatasetId(id);
    setCurrentSummary(null); // Clear old data

    try {
      const response = await axios.get(`${API_BASE_URL}/summary/${id}/`, {
        headers: { Authorization: authHeader }
      });
      setCurrentSummary(response.data);
      setStatusMessage({ type: 'success', text: `Loaded summary for dataset ID ${id}.` });
    } catch (error) {
      console.error('Failed to fetch summary:', error);
      setStatusMessage({ type: 'error', text: 'Failed to retrieve dataset summary.' });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDownloadPDF = async (id) => {
    if (!authHeader) return;
    setStatusMessage({ type: 'info', text: 'Generating PDF report...' });

    try {
      const response = await axios.get(`${API_BASE_URL}/report/${id}/`, {
        headers: { Authorization: authHeader },
        responseType: 'blob', // Important for file downloads
      });

      // Create a link element to trigger the download
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'report.pdf';
      if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/);
          if (filenameMatch.length === 2) {
              filename = filenameMatch[1];
          }
      }

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setStatusMessage({ type: 'success', text: `PDF Report downloaded successfully as ${filename}.` });

    } catch (error) {
      console.error('PDF Download error:', error);
      setStatusMessage({ type: 'error', text: 'Failed to generate or download PDF report.' });
    }
  };

  // --- Effects ---

  useEffect(() => {
    if (isLoggedIn) {
      fetchHistory();
      // Auto-load the newest summary on login/refresh
      if (history.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(history[0].id);
        fetchSummary(history[0].id);
      }
    }
  }, [isLoggedIn, fetchHistory]);
  
  // --- Memoized Chart Data ---
  
  const chartData = useMemo(() => {
    if (!currentSummary) return { type: {}, averages: {} };
    
    // 1. Type Distribution Data (Bar Chart)
    const typeDistribution = currentSummary.type_distribution || {};
    const typeLabels = Object.keys(typeDistribution);
    const typeCounts = Object.values(typeDistribution);
    
    // Random color generation for chart segments
    const generateColors = (count) => {
      const colors = ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#a8dadc', '#457b9d', '#1d3557', '#e63946'];
      return typeLabels.map((_, index) => colors[index % colors.length]);
    };
    
    const typeDistributionData = {
      labels: typeLabels,
      datasets: [{
        label: 'Count',
        data: typeCounts,
        backgroundColor: generateColors(typeLabels.length),
        borderColor: '#1f2937',
        borderWidth: 1,
      }]
    };
    
    // 2. Averages Data (Doughnut Chart)
    const averages = currentSummary.averages || {};
    const avgLabels = ['Flowrate', 'Pressure', 'Temperature'];
    const avgValues = [averages.flowrate, averages.pressure, averages.temperature].map(v => parseFloat(v).toFixed(2));
    
    const averagesData = {
      labels: avgLabels,
      datasets: [{
        label: 'Average Value',
        data: avgValues,
        backgroundColor: ['#f87171', '#34d399', '#60a5fa'], // Red, Green, Blue tones
        borderColor: '#1f2937',
        borderWidth: 1,
      }]
    };
    
    return {
      type: typeDistributionData,
      averages: averagesData
    };
  }, [currentSummary]);

  // --- Rendering ---
  
  // Renders the Login View
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
        <form onSubmit={handleLogin} className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-700">
          <div className="flex items-center space-x-3 mb-8">
            <LogIn className="w-8 h-8 text-indigo-400" />
            <h1 className="text-3xl font-extrabold text-indigo-300">API Login</h1>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-1" htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-white"
              required
              disabled={isLoading}
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-400 mb-1" htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-white"
              required
              disabled={isLoading}
            />
          </div>
          
          <button
            type="submit"
            className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-semibold transition-colors duration-200 flex items-center justify-center disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <LogIn className="w-5 h-5 mr-2" />}
            {isLoading ? 'Authenticating...' : 'Log In'}
          </button>
          
          {statusMessage && <div className="mt-6"><Message type={statusMessage.type}>{statusMessage.text}</Message></div>}
          
          <p className="mt-8 text-xs text-gray-500 text-center">Uses Basic Authentication against the Django API.</p>
        </form>
      </div>
    );
  }

  // Renders the Main Application View
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 p-4 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-xl md:text-2xl font-bold text-indigo-400">
            Chemical Parameter Visualizer
          </h1>
          <button
            onClick={handleLogout}
            className="text-sm px-3 py-1 bg-red-600 hover:bg-red-700 rounded-lg transition-colors duration-200 flex items-center"
          >
            <LogIn className="w-4 h-4 mr-1" /> Logout
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-4 md:p-8 grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Sidebar: Upload & History */}
        <aside className="lg:col-span-1 space-y-8">
            
          {/* Status Message */}
          {statusMessage && <Message type={statusMessage.type}>{statusMessage.text}</Message>}
            
          {/* File Upload Form */}
          <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
            <h2 className="text-lg font-semibold mb-4 flex items-center text-indigo-300">
              <Upload className="w-5 h-5 mr-2" /> Upload New Dataset
            </h2>
            <form onSubmit={handleFileUpload} className="space-y-4">
              <input
                type="file"
                ref={fileInputRef}
                accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-500 file:text-white hover:file:bg-indigo-600"
                required
                disabled={isLoading}
              />
              <button
                type="submit"
                className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-semibold transition-colors duration-200 flex items-center justify-center disabled:opacity-50"
                disabled={isLoading || !uploadFile}
              >
                {isLoading ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <Upload className="w-5 h-5 mr-2" />}
                {isLoading ? 'Analyzing...' : 'Upload & Analyze'}
              </button>
            </form>
          </section>

          {/* History List */}
          <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
            <h2 className="text-lg font-semibold mb-4 flex items-center text-indigo-300">
              <History className="w-5 h-5 mr-2" /> History (Last 5)
            </h2>
            {history.length === 0 ? (
              <p className="text-gray-400">No upload history found.</p>
            ) : (
              <ul className="space-y-2">
                {history.map((dataset) => (
                  <li 
                    key={dataset.id}
                    onClick={() => fetchSummary(dataset.id)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors duration-150 ${
                      dataset.id === selectedDatasetId 
                        ? 'bg-indigo-600 text-white shadow-md' 
                        : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                    }`}
                  >
                    <p className="font-medium text-sm truncate">{dataset.name}</p>
                    <p className="text-xs opacity-80">{new Date(dataset.timestamp).toLocaleString()}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>

        </aside>

        {/* Main Content: Summary & Visualization */}
        <main className="lg:col-span-3 space-y-8">
          
          {currentSummary ? (
            <>
              <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 flex justify-between items-center flex-wrap">
                <h2 className="text-2xl font-bold text-gray-100">
                  Visualization Summary: {history.find(h => h.id === selectedDatasetId)?.name || '...'}
                </h2>
                <button
                  onClick={() => handleDownloadPDF(selectedDatasetId)}
                  className="mt-4 sm:mt-0 py-2 px-4 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-semibold flex items-center transition-colors duration-200 disabled:opacity-50"
                  disabled={isLoading}
                >
                  <FileText className="w-5 h-5 mr-2" /> Download PDF Report
                </button>
              </div>

              {/* Statistical Averages Table */}
              <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
                <h3 className="text-xl font-semibold mb-4 text-indigo-300">Parameter Averages</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(currentSummary.averages || {}).map(([key, value]) => (
                    <div key={key} className="p-4 bg-gray-700 rounded-lg text-center shadow">
                      <p className="text-sm text-gray-400 uppercase">{key}</p>
                      <p className="text-3xl font-bold text-green-400 mt-1">
                        {parseFloat(value).toFixed(2)}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                
                {/* 1. Equipment Type Distribution Bar Chart */}
                <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
                  <h3 className="text-xl font-semibold mb-4 flex items-center text-indigo-300">
                    <BarChart className="w-5 h-5 mr-2" /> Equipment Type Distribution
                  </h3>
                  <div className="h-80">
                    <Bar
                      data={chartData.type}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                          title: { display: false },
                        },
                        scales: {
                          y: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#ccc' } },
                          x: { grid: { display: false }, ticks: { color: '#ccc' } }
                        }
                      }}
                    />
                  </div>
                </section>
                
                {/* 2. Parameter Averages Doughnut Chart */}
                <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
                  <h3 className="text-xl font-semibold mb-4 flex items-center text-indigo-300">
                    <PieChart className="w-5 h-5 mr-2" /> Relative Parameter Magnitudes
                  </h3>
                  <div className="h-80 flex items-center justify-center">
                    <div className="w-full max-w-xs">
                      <Doughnut 
                        data={chartData.averages}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { position: 'right', labels: { color: '#ccc' } },
                            title: { display: false },
                          },
                        }}
                      />
                    </div>
                  </div>
                </section>
                
              </div>
              
              {/* Data Preview Table */}
              <section className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 overflow-x-auto">
                <h3 className="text-xl font-semibold mb-4 text-indigo-300">Data Preview (First 5 Rows)</h3>
                <table className="min-w-full divide-y divide-gray-700">
                  <thead>
                    <tr className="text-xs font-medium tracking-wider text-gray-400 uppercase">
                      <th className="px-6 py-3 text-left">Equipment Name</th>
                      <th className="px-6 py-3 text-left">Type</th>
                      <th className="px-6 py-3 text-right">Flowrate</th>
                      <th className="px-6 py-3 text-right">Pressure</th>
                      <th className="px-6 py-3 text-right">Temperature</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {(currentSummary.data_preview || []).map((row, index) => (
                      <tr key={index} className="hover:bg-gray-700 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{row['Equipment Name']}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{row['Type']}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono text-cyan-400">{row['Flowrate'].toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono text-yellow-400">{row['Pressure'].toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono text-orange-400">{row['Temperature'].toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

            </>
          ) : (
            <div className="min-h-[60vh] flex items-center justify-center">
              <p className="text-gray-400 text-center text-xl p-8 bg-gray-800 rounded-xl border border-gray-700">
                <span className="font-bold text-indigo-400">Upload a CSV/Excel file</span> or select a dataset from the history to view the analysis and visualization.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;