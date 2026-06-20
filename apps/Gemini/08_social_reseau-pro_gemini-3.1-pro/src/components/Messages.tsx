import { useState, useEffect, useRef } from 'react';
import { Connection, Message } from '../types';
import { Send } from 'lucide-react';

export function Messages({ token, currentUser }: { token: string, currentUser: any }) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [activeChat, setActiveChat] = useState<Connection | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchConnections = async () => {
      const res = await fetch('/api/connections', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setConnections(data.filter((c: Connection) => c.status === 'accepted'));
      }
    };
    fetchConnections();
  }, [token]);

  useEffect(() => {
    let interval: any;
    const fetchMessages = async () => {
      if (!activeChat) return;
      const res = await fetch(`/api/messages/${activeChat.id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setMessages(await res.json());
    };

    if (activeChat) {
      fetchMessages();
      interval = setInterval(fetchMessages, 3000); // Poll for new messages
    }
    return () => clearInterval(interval);
  }, [activeChat, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeChat) return;

    await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ receiverId: activeChat.id, content: newMessage })
    });
    
    setNewMessage('');
    // Optimistic UI update could be done here instead of waiting for poll
    const res = await fetch(`/api/messages/${activeChat.id}`, { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) setMessages(await res.json());
  };

  return (
    <div className="max-w-6xl mx-auto py-8 h-[calc(100vh-64px)]">
      <div className="bg-white rounded-lg shadow h-full flex overflow-hidden">
        
        {/* Liste des contacts */}
        <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h2 className="font-semibold text-gray-900">Messagerie</h2>
          </div>
          <ul className="divide-y divide-gray-100">
            {connections.length === 0 ? (
               <div className="p-8 text-center text-sm text-gray-500">
                  Connectez-vous à d'autres professionnels pour commencer à échanger.
               </div>
            ) : (
                connections.map(conn => (
                  <li key={conn.id}>
                    <button 
                      onClick={() => setActiveChat(conn)}
                      className={`w-full text-left p-4 flex items-center hover:bg-gray-50 transition-colors ${activeChat?.id === conn.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''}`}
                    >
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold mr-3 flex-shrink-0">
                        {conn.name.charAt(0)}
                      </div>
                      <div className="overflow-hidden">
                        <h4 className="font-medium text-gray-900 truncate">{conn.name}</h4>
                        <p className="text-xs text-gray-500 truncate">{conn.jobTitle}</p>
                      </div>
                    </button>
                  </li>
                ))
            )}
          </ul>
        </div>

        {/* Zone de chat */}
        <div className="w-2/3 flex flex-col bg-gray-50/50">
          {activeChat ? (
            <>
              {/* Entête du chat */}
              <div className="p-4 border-b border-gray-200 bg-white flex items-center shadow-sm z-10">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold mr-3">
                  {activeChat.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{activeChat.name}</h3>
                  <p className="text-xs text-gray-500">{activeChat.jobTitle}</p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                   <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                      Envoyez le premier message à {activeChat.name}.
                   </div>
                ) : (
                    messages.map((msg) => {
                      const isMine = msg.sender_id === currentUser.id;
                      return (
                        <div key={msg.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[70%] rounded-2xl px-4 py-2 ${isMine ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'}`}>
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <span className={`text-[10px] mt-1 block ${isMine ? 'text-blue-100 text-right' : 'text-gray-400'}`}>
                              {new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          </div>
                        </div>
                      );
                    })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 bg-white border-t border-gray-200">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={e => setNewMessage(e.target.value)}
                    placeholder="Écrivez un message..."
                    className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <button type="submit" disabled={!newMessage.trim()} className="bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors">
                    <Send size={18} />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-gray-500 px-8 text-center">
               <MessageSquare size={48} className="text-gray-300 mb-4" />
               <p className="text-lg font-medium text-gray-700">Sélectionnez une conversation</p>
               <p className="text-sm mt-2">Choisissez un contact dans le menu de gauche pour démarrer ou reprendre vos échanges professionnels.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
