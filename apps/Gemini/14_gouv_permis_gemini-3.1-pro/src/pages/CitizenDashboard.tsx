import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/AuthProvider';
import { Plus, FileText, Clock, CheckCircle, XCircle, LogOut } from 'lucide-react';
import { Permit } from '../types';

export default function CitizenDashboard() {
  const { user, logout } = useAuth();
  const [permits, setPermits] = useState<Permit[]>([]);

  useEffect(() => {
    fetch('/api/permits')
      .then(r => r.json())
      .then(setPermits);
  }, []);

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'brouillon': return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">Brouillon</span>;
      case 'soumis': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium flex items-center gap-1"><Clock size={12}/> Soumis</span>;
      case 'en_cours': return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium flex items-center gap-1"><Clock size={12}/> En traitement</span>;
      case 'valide': return <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium flex items-center gap-1"><CheckCircle size={12}/> Validé</span>;
      case 'refuse': return <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium flex items-center gap-1"><XCircle size={12}/> Refusé</span>;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <FileText className="text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">Espace Citoyen</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button onClick={logout} className="text-gray-500 hover:text-red-600 flex items-center gap-1 text-sm">
              <LogOut size={16} /> Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Mes Demandes de Permis</h2>
          <Link to="/dashboard/new" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium transition-colors">
            <Plus size={18} /> Nouvelle Demande
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {permits.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Vous n'avez aucune demande de permis en cours.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-500">
                  <th className="p-4 w-24">N° Dossier</th>
                  <th className="p-4">Type de travaux</th>
                  <th className="p-4">Date de création</th>
                  <th className="p-4">Statut</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {permits.map(permit => (
                  <tr key={permit.id} className="hover:bg-gray-50 transition-colors text-sm text-gray-800">
                    <td className="p-4 font-mono text-gray-600">#{permit.id.toString().padStart(4, '0')}</td>
                    <td className="p-4">{permit.type_travaux || 'Non précisé'}</td>
                    <td className="p-4 text-gray-500">{new Date(permit.created_at).toLocaleDateString()}</td>
                    <td className="p-4">{getStatusBadge(permit.status)}</td>
                    <td className="p-4 text-right">
                      {permit.status === 'brouillon' ? (
                        <Link to={`/dashboard/new?id=${permit.id}`} className="text-blue-600 hover:underline font-medium">Reprendre</Link>
                      ) : (
                        <Link to={`/dashboard/view/${permit.id}`} className="text-gray-600 hover:underline font-medium">Détails</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
