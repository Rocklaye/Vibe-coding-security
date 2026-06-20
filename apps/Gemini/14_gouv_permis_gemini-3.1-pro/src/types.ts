export interface User {
  id: number;
  email: string;
  role: 'citoyen' | 'agent';
}

export interface Permit {
  id: number;
  user_id: number;
  type_travaux: string | null;
  surface_plancher: number | null;
  adresse: string | null;
  status: 'brouillon' | 'soumis' | 'en_cours' | 'valide' | 'refuse';
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  permit_id: number;
  type_document: string;
  file_path: string;
  original_name: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}
