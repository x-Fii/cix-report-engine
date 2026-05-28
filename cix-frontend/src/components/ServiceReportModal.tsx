import React, { useState } from 'react';
import apiClient from '../api/client';

interface ServiceReportModalProps {
  ticketId: number;
  ticketNo: string;
  maxisCentreId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const ServiceReportModal: React.FC<ServiceReportModalProps> = ({
  ticketId,
  ticketNo,
  maxisCentreId,
  onClose,
  onSuccess,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mutable form states tied to active interactive input fields
  const [srNo, setSrNo] = useState(`SR-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`);
  const [doNo, setDoNo] = useState(`DO-${ticketNo}`);
  const [storeName, setStoreName] = useState('1Borneo');
  const [picName, setPicName] = useState('');
  const [picTel, setPicTel] = useState('');
  const [itemCode, setItemCode] = useState('MHD-MP');

  // Hardened local constants to satisfy strict compilation rules
  const companyName = 'Maxis Broadband Sdn Bhd';
  const address = 'G-304, Ground Floor, 1Borneo Hypermall, Jalan Sulaman, Kota Kinabalu';
  const operatorEmail = 'fii_ops@clickix.com';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Structural model mapping aligned directly with Pydantic expectations
    const payload = {
      sr_no: srNo,
      do_id: 1,
      do_no: doNo,
      ticket_id: ticketId,
      client: {
        company: companyName,
        company_address: [address],
        store_type: 'MC',
        store_name: storeName,
        pic_name: picName || 'Manager On Duty',
        pic_tel: picTel || '60120000000',
      },
      before_photos_json: ['uploads/2026/05/before1.jpg'],
      after_photos_json: ['uploads/2026/05/after1.jpg'],
      acknowledgement: {
        signed_by: picName || 'Manager On Duty',
        signature_png_upload_id: 1,
        signed_at: new Date().toISOString().split('.')[0],
        operator_email: operatorEmail,
      },
      hardware_swaps: [
        {
          direction: 'installed',
          sku_id: 1,
          item_code: itemCode,
        },
      ],
    };

    try {
      const response = await apiClient.post('/operations/service-reports', payload);
      if (response.data.status === 'Success') {
        alert(`Operational success: ${response.data.message}`);
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      console.error('Submission rejection:', err);
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || err.message || 'Verification failure.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        <header className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-900/50">
          <div>
            <h2 className="text-xl font-bold text-white">Resolve Ticket {ticketNo}</h2>
            <p className="text-xs text-slate-400 mt-0.5">Filing closed-loop service report for Maxis Centre #{maxisCentreId}</p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white text-lg">✕</button>
        </header>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {error && <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl">{error}</div>}

          {/* Document Reference Block */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Report Number</label>
              <input type="text" value={srNo} onChange={e => setSrNo(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500 font-mono" required />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Delivery Order Reference</label>
              <input type="text" value={doNo} onChange={e => setDoNo(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500 font-mono" required />
            </div>
          </div>

          {/* Store Contacts Block */}
          <div className="space-y-4 border-t border-slate-700/50 pt-4">
            <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Store & Client Records</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Store Name</label>
                <input type="text" value={storeName} onChange={e => setStoreName(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none" required />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">On-Site PIC Name</label>
                <input type="text" value={picName} onChange={e => setPicName(e.target.value)} placeholder="e.g. Awang Kimaruddin" className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none" required />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">PIC Contact Number</label>
                <input type="text" value={picTel} onChange={e => setPicTel(e.target.value)} placeholder="e.g. 60127233420" className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none" required />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Hardware Item Code Swap</label>
                <input type="text" value={itemCode} onChange={e => setItemCode(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none font-mono" required />
              </div>
            </div>
          </div>
        </form>

        <footer className="p-4 border-t border-slate-700 bg-slate-900/30 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 font-medium transition-colors">Cancel</button>
          <button type="button" onClick={handleSubmit} disabled={submitting} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:text-indigo-300 rounded-lg text-white font-medium shadow-lg shadow-indigo-600/20 transition-colors">
            {submitting ? 'Synchronizing State...' : 'Submit Deployment Report'}
          </button>
        </footer>
      </div>
    </div>
  );
};
