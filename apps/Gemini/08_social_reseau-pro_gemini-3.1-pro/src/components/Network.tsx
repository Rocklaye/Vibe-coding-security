import { useState, useEffect } from 'react';
import { User, Connection } from '../types';
import { UserPlus, Check, X } from 'lucide-react';

export function Network({ token, currentUser }: { token: string, currentUser: any }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);

  const fetchConnections = async () => {
    const res = await fetch('/api/connections', { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) setConnections(await res.json());
  };

  useEffect(() => {
    fetchConnections();
  }, [token]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const res = await fetch(`/api/users?q=${encodeURIComponent(searchQuery)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      // On filtre l'utilisateur courant des résultats
      setSearchResults(data.filter((u: User) => u.id !== currentUser.id));
    }
  };

  const handleConnect = async (receiverId: number) => {
    await fetch('/api/connections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ receiverId })
    });
    fetchConnections();
  };

  const handleAccept = async (requesterId: number) => {
    await fetch(`/api/connections/${requesterId}/accept`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    fetchConnections();
  };

  const isConnectedOrPending = (userId: number) => {
    return connections.some(c => c.id === userId);
  };

  const pendingRequests = connections.filter(c => c.status === 'pending' && c.requesterId !== currentUser.id);
  const myConnections = connections.filter(c => c.status === 'accepted');

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Colonne de gauche: Recherche et résultats */}
        <div className="md:col-span-2">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Trouver des professionnels</h2>
            <form onSubmit={handleSearch} className="flex gap-2">
              <input 
                type="text" 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Recherche par nom, poste ou compétence..." 
                className="flex-grow border border-gray-300 rounded-lg p-2 focus:outline-none focus:border-blue-500"
              />
              <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Chercher</button>
            </form>
          </div>

          {searchResults.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="font-medium text-gray-900">Résultats de recherche</h3>
              </div>
              <ul className="divide-y divide-gray-100">
                {searchResults.map(user => (
                  <li key={user.id} className="p-6 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold mr-4 text-xl">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{user.name}</h4>
                        <p className="text-sm text-gray-500">{user.jobTitle} {user.company ? `chez ${user.company}` : ''}</p>
                        {user.skills && <p className="text-xs text-blue-600 mt-1">{user.skills}</p>}
                      </div>
                    </div>
                    {!isConnectedOrPending(user.id) ? (
                      <button onClick={() => handleConnect(user.id)} className="flex items-center text-blue-600 hover:text-blue-800 border border-blue-600 rounded-full px-4 py-1 text-sm font-medium hover:bg-blue-50 transition-colors">
                        <UserPlus size={16} className="mr-1" /> Se connecter
                      </button>
                    ) : (
                      <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                        {connections.find(c => c.id === user.id)?.status === 'accepted' ? 'Connecté' : 'En attente'}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Colonne de droite: Demandes et réseau actuel */}
        <div className="md:col-span-1 space-y-6">
          {pendingRequests.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100 border-l-4 border-l-yellow-400">
                <h3 className="font-medium text-gray-900">Invitations reçues</h3>
              </div>
              <ul className="divide-y divide-gray-100">
                {pendingRequests.map(req => (
                  <li key={req.id} className="p-4">
                    <div className="flex items-center mb-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold mr-3 flex-shrink-0">
                        {req.name.charAt(0)}
                      </div>
                      <div className="overflow-hidden">
                        <h4 className="font-semibold text-gray-900 truncate">{req.name}</h4>
                        <p className="text-xs text-gray-500 truncate">{req.jobTitle}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                       <button onClick={() => handleAccept(req.id)} className="flex-1 flex justify-center items-center py-1.5 border border-green-600 text-green-600 rounded hover:bg-green-50 text-sm font-medium">
                          <Check size={16} className="mr-1" /> Accepter
                       </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="font-medium text-gray-900">Vos relations ({myConnections.length})</h3>
            </div>
            {myConnections.length > 0 ? (
              <ul className="divide-y divide-gray-100">
                {myConnections.map(conn => (
                  <li key={conn.id} className="p-4 flex items-center">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold mr-3 flex-shrink-0">
                      {conn.name.charAt(0)}
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="font-medium text-sm text-gray-900 truncate">{conn.name}</h4>
                      <p className="text-xs text-gray-500 truncate">{conn.jobTitle}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-6 text-center text-sm text-gray-500">
                Vous n'avez pas encore de relations.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
