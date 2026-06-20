import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../components/AuthProvider';
import { ArrowLeft, ArrowRight, Upload, Check, File } from 'lucide-react';
import { Permit } from '../types';

export default function PermitForm() {
  const [searchParams] = useSearchParams();
  const permitId = searchParams.get('id');
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [step, setStep] = useState(1);
  const [currentId, setCurrentId] = useState<number | null>(permitId ? parseInt(permitId) : null);
  
  const [formData, setFormData] = useState({
    type_travaux: '',
    surface_plancher: '',
    adresse: ''
  });
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (currentId) {
      fetch(`/api/permits/${currentId}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            setFormData({
              type_travaux: data.type_travaux || '',
              surface_plancher: data.surface_plancher ? data.surface_plancher.toString() : '',
              adresse: data.adresse || ''
            });
            if (data.documents) setDocuments(data.documents);
          }
        });
    }
  }, [currentId]);

  const saveDraft = async (goToNext = false) => {
    try {
      let id = currentId;
      if (!id) {
        const res = await fetch('/api/permits', { method: 'POST' });
        const data = await res.json();
        id = data.id;
        setCurrentId(id);
      }
      
      if (id) {
        await fetch(`/api/permits/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...formData,
            surface_plancher: parseInt(formData.surface_plancher) || 0,
            status: 'brouillon'
          })
        });
        if (goToNext) setStep(step + 1);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitPermit = async () => {
    if (!currentId) return;
    await fetch(`/api/permits/${currentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...formData,
        surface_plancher: parseInt(formData.surface_plancher) || 0,
        status: 'soumis' // Submit for review
      })
    });
    navigate('/dashboard');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: string) => {
    if (!e.target.files?.[0] || !currentId) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', e.target.files[0]);
    fd.append('type_document', type);

    const res = await fetch(`/api/permits/${currentId}/upload`, {
      method: 'POST',
      body: fd
    });
    
    if (res.ok) {
      // Refresh documents
      const permitRes = await fetch(`/api/permits/${currentId}`);
      const permitData = await permitRes.json();
      setDocuments(permitData.documents || []);
    }
    setUploading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button onClick={() => navigate('/dashboard')} className="flex items-center text-gray-600 hover:text-gray-900">
            <ArrowLeft size={18} className="mr-2" /> Retour au tableau de bord
          </button>
          <div className="text-sm text-gray-500 font-medium">Étape {step} / 3</div>
        </div>
      </header>

      <main className="flex-1 flex flex-col justify-center max-w-3xl mx-auto w-full px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          
          {/* Progress Bar */}
          <div className="flex gap-2 mb-8">
             {[1, 2, 3].map(i => (
               <div key={i} className={`flex-1 h-2 rounded-full ${i <= step ? 'bg-blue-600' : 'bg-gray-100'}`} />
             ))}
          </div>

          {step === 1 && (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
              <h2 className="text-2xl font-bold text-gray-900">Informations Generales</h2>
              <p className="text-gray-500 text-sm">Décrivez la nature de vos travaux.</p>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nature des travaux</label>
                <select 
                  value={formData.type_travaux}
                  onChange={e => setFormData({...formData, type_travaux: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">Sélectionnez...</option>
                  <option value="construction_neuve">Construction Neuve</option>
                  <option value="agrandissement">Agrandissement</option>
                  <option value="modification_facade">Modification de façade</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Surface de plancher (m²)</label>
                <input 
                  type="number"
                  value={formData.surface_plancher}
                  onChange={e => setFormData({...formData, surface_plancher: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Ex: 120"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Adresse complète du projet</label>
                <textarea 
                  value={formData.adresse}
                  onChange={e => setFormData({...formData, adresse: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                  placeholder="Numéro, voie, code postal, ville"
                />
              </div>

              <div className="pt-4 flex justify-end">
                <button 
                  onClick={() => saveDraft(true)}
                  disabled={!formData.type_travaux || !formData.surface_plancher || !formData.adresse}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  Suivant <ArrowRight size={18} />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
              <h2 className="text-2xl font-bold text-gray-900">Pièces Jointes</h2>
              <p className="text-gray-500 text-sm">Veuillez fournir les plans et documents nécessaires. Ces documents sont obligatoires pour l'instruction.</p>
              
              <div className="space-y-4 pt-4">
                {[
                  { id: 'plan_masse', label: 'Plan de masse des constructions' },
                  { id: 'plan_facades', label: 'Plan des façades et toitures' },
                  { id: 'document_graphique', label: 'Document graphique 3D' }
                ].map(docType => {
                  const uploaded = documents.find(d => d.type_document === docType.id);
                  return (
                    <div key={docType.id} className="p-4 border border-gray-200 rounded-xl flex items-center justify-between bg-gray-50/50">
                      <div>
                        <h3 className="font-medium text-gray-900">{docType.label}</h3>
                        {uploaded && <p className="text-xs text-green-600 flex items-center gap-1 mt-1"><Check size={12}/> Fichier importé : {uploaded.original_name}</p>}
                      </div>
                      <div>
                        <input 
                          type="file" 
                          id={`file-${docType.id}`} 
                          className="hidden" 
                          onChange={(e) => handleFileUpload(e, docType.id)}
                        />
                        <label htmlFor={`file-${docType.id}`} className="cursor-pointer bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                          <Upload size={16} /> 
                          {uploaded ? 'Remplacer' : 'Uploader'}
                        </label>
                      </div>
                    </div>
                  )
                })}
              </div>
              
              <div className="pt-6 flex justify-between">
                <button onClick={() => setStep(1)} className="text-gray-600 hover:text-gray-900 font-medium">Retour</button>
                <button onClick={() => setStep(3)} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50" disabled={uploading}>
                  Suivant <ArrowRight size={18} />
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
              <h2 className="text-2xl font-bold text-gray-900">Récapitulatif</h2>
              <p className="text-gray-500 text-sm">Vérifiez les informations avant de soumettre définitivement votre dossier.</p>
              
              <div className="bg-gray-50 rounded-xl p-6 space-y-4 text-sm border border-gray-100">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-gray-500">Nature des travaux</div>
                  <div className="col-span-2 font-medium text-gray-900">{formData.type_travaux}</div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-gray-500">Surface plancher</div>
                  <div className="col-span-2 font-medium text-gray-900">{formData.surface_plancher} m²</div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-gray-500">Adresse</div>
                  <div className="col-span-2 font-medium text-gray-900">{formData.adresse}</div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-gray-500">Pièces jointes</div>
                  <div className="col-span-2 font-medium text-gray-900 flex flex-col gap-1">
                    {documents.map(d => (
                       <span key={d.id} className="flex items-center gap-1 text-blue-600"><File size={14}/> {d.original_name}</span>
                    ))}
                    {documents.length === 0 && <span className="text-red-500">Aucun document joint</span>}
                  </div>
                </div>
              </div>
              
              <div className="pt-6 flex justify-between">
                <button onClick={() => setStep(2)} className="text-gray-600 hover:text-gray-900 font-medium">Retour</button>
                <button onClick={submitPermit} className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-lg transition-colors flex items-center gap-2">
                  <Check size={18} /> Soumettre ma demande
                </button>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
