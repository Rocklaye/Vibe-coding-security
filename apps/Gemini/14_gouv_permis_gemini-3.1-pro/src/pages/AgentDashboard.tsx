import { useEffect, useState } from 'react';
import { useAuth } from '../components/AuthProvider';
import { FileText, LogOut, CheckSquare, Clock } from 'lucide-react';
import { Permit } from '../types';

export default function AgentDashboard() {
  const { user, logout } = useAuth();
  const [permits, setPermits] = useState<(Permit & { citoyen_email: string })[]>([]);
  const [selectedPermit, setSelectedPermit] = useState<(Permit & { citoyen_email: string, documents?: any[] }) | null>(null);

  const fetchPermits = () => {
    fetch('/api/admin/permits')
      .then(r => r.json())
      .then(setPermits);
  };

  useEffect(() => {
    fetchPermits();
  }, []);

  const openPermit = async (id: number) => {
    const res = await fetch(`/api/admin/permits/${id}`);
    const data = await res.json();
    setSelectedPermit(data);
  };

  const updateStatus = async (status: string) => {
    if (!selectedPermit) return;
    await fetch(`/api/admin/permits/${selectedPermit.id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    fetchPermits();
    setSelectedPermit({ ...selectedPermit, status: status as any });
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-slate-900 border-b border-slate-800 text-white">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <CheckSquare className="text-blue-400" />
            <h1 className="text-xl font-semibold">Portail Agent Instructeur</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-300">{user?.email}</span>
            <button onClick={logout} className="text-slate-400 hover:text-red-400 flex items-center gap-1 text-sm transition-colors">
              <LogOut size={16} /> Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Permit List */}
        <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col max-h-[80vh]">
          <div className="p-4 border-b border-gray-100 bg-gray-50">
            <h2 className="font-semibold text-gray-900">Dossiers à traiter</h2>
          </div>
          <div className="overflow-y-auto flex-1">
            {permits.length === 0 ? (
               <div className="p-8 text-center text-sm text-gray-500">Aucun dossier en attente.</div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {permits.map(permit => (
                  <li 
                    key={permit.id} 
                    onClick={() => openPermit(permit.id)}
                    className={`p-4 cursor-pointer transition-colors ${selectedPermit?.id === permit.id ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50 border-l-4 border-transparent'}`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-mono text-xs font-bold text-gray-500">#{permit.id.toString().padStart(4, '0')}</span>
                      <span className={`text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full ${
                        permit.status === 'soumis' ? 'bg-blue-100 text-blue-700' :
                        permit.status === 'en_cours' ? 'bg-yellow-100 text-yellow-700' :
                        permit.status === 'valide' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {permit.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="font-medium text-sm text-gray-900 truncate">{permit.type_travaux}</p>
                    <p className="text-xs text-gray-500 truncate mt-1">Par: {permit.citoyen_email}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right Col: Permit Details */}
        <div className="lg:col-span-2">
          {selectedPermit ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">Dossier #{selectedPermit.id.toString().padStart(4, '0')}</h2>
                  <p className="text-gray-500 text-sm">Déposé le {new Date(selectedPermit.created_at).toLocaleDateString()} par {selectedPermit.citoyen_email}</p>
                </div>
                {selectedPermit.status === 'soumis' && (
                  <button onClick={() => updateStatus('en_cours')} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-2">
                    <Clock size={16} /> Commencer l'instruction
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-6 mb-8">
                <div>
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Type de travaux</h3>
                  <p className="text-gray-900 font-medium">{selectedPermit.type_travaux}</p>
                </div>
                <div>
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Surface Plancher</h3>
                  <p className="text-gray-900 font-medium">{selectedPermit.surface_plancher} m²</p>
                </div>
                <div className="col-span-2">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Adresse du projet</h3>
                  <p className="text-gray-900 font-medium">{selectedPermit.adresse}</p>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Pièces jointes</h3>
              {selectedPermit.documents && selectedPermit.documents.length > 0 ? (
                <ul className="space-y-2 mb-8">
                  {selectedPermit.documents.map((doc: any) => (
                    <li key={doc.id} className="flex justify-between items-center p-3 bg-gray-50 border border-gray-100 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="text-gray-400" size={18} />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{doc.original_name}</p>
                          <p className="text-xs text-gray-500 uppercase">{doc.type_document}</p>
                        </div>
                      </div>
                      <a href={`/api/uploads/${doc.file_path}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-sm font-medium hover:underline">
                        Visualiser
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 mb-8 italic">Aucune pièce jointe.</p>
              )}

              <div className="border-t border-gray-200 pt-6 mt-8 flex justify-end gap-4">
                <button 
                  onClick={() => updateStatus('refuse')}
                  disabled={selectedPermit.status === 'refuse' || selectedPermit.status === 'valide'}
                  className="px-6 py-2 rounded-lg font-medium text-red-700 bg-red-50 hover:bg-red-100 disabled:opacity-50 transition-colors"
                >
                  Refuser le permis
                </button>
                <button 
                  onClick={() => updateStatus('valide')}
                  disabled={selectedPermit.status === 'valide' || selectedPermit.status === 'refuse'}
                  className="px-6 py-2 rounded-lg font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  Valider le permis
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 bg-white rounded-xl shadow-sm border border-gray-200 border-dashed p-12">
              <CheckSquare size={48} className="mb-4 text-gray-300" />
              <p>Sélectionnez un dossier pour visualiser les détails</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
