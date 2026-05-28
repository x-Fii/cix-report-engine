import React, { useEffect, useState } from 'react';
import apiClient from './api/client';
import type { Ticket } from './types/operations';
import './App.css';

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  let styles = 'bg-gray-500 text-gray-100';
  if (priority === 'Critical') styles = 'bg-red-500/20 text-red-400 border border-red-500/30';
  else if (priority === 'High') styles = 'bg-orange-500/20 text-orange-400 border border-orange-500/30';
  else if (priority === 'Medium') styles = 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
  else if (priority === 'Low') styles = 'bg-blue-500/20 text-blue-400 border border-blue-500/30';

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide uppercase ${styles}`}>
      {priority}
    </span>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  let styles = 'bg-gray-500 text-gray-100';
  if (status === 'open') styles = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
  else if (status === 'assigned') styles = 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30';
  else if (status === 'in_progress') styles = 'bg-sky-500/20 text-sky-400 border border-sky-500/30';
  else if (status === 'resolved') styles = 'bg-gray-500/20 text-gray-400 border border-gray-500/30 line-through';
  else if (status === 'closed') styles = 'bg-zinc-800 text-zinc-500 border border-zinc-700';

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide uppercase ${styles}`}>
      {status.replace('_', ' ')}
    </span>
  );
};

const App: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        // Assuming your FastAPI ticket route doesn't strictly need JWT if we are testing,
        // or we mock it if it fails. The instructions say to trigger apiClient.get('/tickets')
        const response = await apiClient.get('/tickets');
        setTickets(response.data);
        setError(null);
      } catch (err: any) {
        console.error("Error fetching tickets:", err);
        setError(err.response?.data?.detail || err.message || "Failed to load tickets.");
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="w-8 h-8 rounded bg-indigo-500 flex items-center justify-center text-sm shadow-lg shadow-indigo-500/20">
              ⚡
            </span>
            Click-iX Operations Console
          </h1>
          <p className="text-slate-400 mt-2 text-sm">Real-time Service Desk Monitoring</p>
        </header>

        <main>
          {loading ? (
            <div className="flex items-center justify-center h-64 border border-slate-800 rounded-xl bg-slate-800/30 backdrop-blur">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-start gap-3">
              <span>⚠️</span>
              <div>
                <h3 className="font-semibold text-sm">Connection Error</h3>
                <p className="text-sm opacity-80 mt-1">{error}</p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl shadow-xl overflow-hidden backdrop-blur-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                    <tr>
                      <th className="px-6 py-4 font-semibold">Ticket ID</th>
                      <th className="px-6 py-4 font-semibold">Category</th>
                      <th className="px-6 py-4 font-semibold">Location Ref</th>
                      <th className="px-6 py-4 font-semibold">Description</th>
                      <th className="px-6 py-4 font-semibold text-center">Priority</th>
                      <th className="px-6 py-4 font-semibold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {tickets.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                          No active tickets found in the queue.
                        </td>
                      </tr>
                    ) : (
                      tickets.map((ticket) => (
                        <tr key={ticket.id} className="hover:bg-slate-700/30 transition-colors duration-200">
                          <td className="px-6 py-4 font-medium text-slate-300">
                            {ticket.ticket_no}
                          </td>
                          <td className="px-6 py-4 text-slate-300">
                            {ticket.category}
                          </td>
                          <td className="px-6 py-4 text-slate-400 font-mono text-xs">
                            MC-{ticket.maxis_centre_id}
                          </td>
                          <td className="px-6 py-4 text-slate-400 truncate max-w-xs">
                            {ticket.description || "No description provided."}
                          </td>
                          <td className="px-6 py-4 text-center">
                            <PriorityBadge priority={ticket.priority} />
                          </td>
                          <td className="px-6 py-4 text-center">
                            <StatusBadge status={ticket.status} />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
