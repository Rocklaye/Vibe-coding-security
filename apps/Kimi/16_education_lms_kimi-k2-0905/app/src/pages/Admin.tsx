import { useState } from "react";
import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Shield,
  BookOpen,
  Users,
  GraduationCap,
  Plus,
  Trash2,
  BarChart3,
  ChevronRight,
  Award,
} from "lucide-react";

export default function Admin() {
  const { user, isAuthenticated } = useAuth();
  const isAdmin = user?.role === "admin";

  // Redirect non-admin users
  if (isAuthenticated && !isAdmin) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <Shield className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
        <h1 className="font-serif text-2xl text-[#1A1A1A] mb-2">Accès réservé</h1>
        <p className="text-[#6B6865] mb-4">Cette page est réservée aux administrateurs.</p>
        <Link to="/" className="btn-gold">Retour à l'accueil</Link>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <Shield className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
        <p className="text-[#6B6865] mb-4">Connectez-vous pour accéder à l'administration.</p>
        <Link to="/login" className="btn-gold">Se connecter</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-8 h-8 text-[#D4A853]" />
          <h1 className="font-serif text-4xl text-[#1A1A1A]">Administration</h1>
        </div>
        <p className="text-[#6B6865]">
          Gérez les cours, les utilisateurs et suivez les statistiques de la plateforme.
        </p>
      </div>

      <Tabs defaultValue="courses">
        <TabsList className="bg-[#F2EDE7] rounded-xl mb-6">
          <TabsTrigger value="courses" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-[#1A1A1A]">
            <BookOpen className="w-4 h-4 mr-2" />
            Cours
          </TabsTrigger>
          <TabsTrigger value="stats" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-[#1A1A1A]">
            <BarChart3 className="w-4 h-4 mr-2" />
            Statistiques
          </TabsTrigger>
        </TabsList>

        <TabsContent value="courses">
          <AdminCourses />
        </TabsContent>

        <TabsContent value="stats">
          <AdminStats />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ─── Admin Courses ───
function AdminCourses() {
  const { data: courses } = trpc.course.list.useQuery();
  const utils = trpc.useUtils();
  const [showCreate, setShowCreate] = useState(false);
  const [newCourse, setNewCourse] = useState({
    title: "",
    description: "",
    category: "",
    level: "debutant" as const,
    duration: "",
    image: "",
  });

  const createMutation = trpc.course.create.useMutation({
    onSuccess: () => {
      utils.course.list.invalidate();
      setShowCreate(false);
      setNewCourse({ title: "", description: "", category: "", level: "debutant", duration: "", image: "" });
    },
  });

  const deleteMutation = trpc.course.delete.useMutation({
    onSuccess: () => {
      utils.course.list.invalidate();
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-serif text-2xl text-[#1A1A1A]">
          Gestion des cours
          <span className="text-base font-sans text-[#6B6865] ml-2">({courses?.length || 0})</span>
        </h2>
        <Button onClick={() => setShowCreate(!showCreate)} className="btn-gold">
          <Plus className="w-4 h-4 mr-2" />
          Nouveau cours
        </Button>
      </div>

      {showCreate && (
        <div className="card-warm p-6 mb-6">
          <h3 className="font-medium text-[#1A1A1A] mb-4">Créer un cours</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <Input
              placeholder="Titre du cours"
              value={newCourse.title}
              onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
              className="border-[#E0DCD7]"
            />
            <Input
              placeholder="Catégorie"
              value={newCourse.category}
              onChange={(e) => setNewCourse({ ...newCourse, category: e.target.value })}
              className="border-[#E0DCD7]"
            />
            <Input
              placeholder="Durée (ex: 8 semaines)"
              value={newCourse.duration}
              onChange={(e) => setNewCourse({ ...newCourse, duration: e.target.value })}
              className="border-[#E0DCD7]"
            />
            <select
              value={newCourse.level}
              onChange={(e) => setNewCourse({ ...newCourse, level: e.target.value as any })}
              className="h-10 rounded-md border border-[#E0DCD7] bg-white px-3 text-sm"
            >
              <option value="debutant">Débutant</option>
              <option value="intermediaire">Intermédiaire</option>
              <option value="avance">Avancé</option>
            </select>
            <Input
              placeholder="URL de l'image"
              value={newCourse.image}
              onChange={(e) => setNewCourse({ ...newCourse, image: e.target.value })}
              className="border-[#E0DCD7] md:col-span-2"
            />
          </div>
          <Textarea
            placeholder="Description du cours"
            value={newCourse.description}
            onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
            className="mb-4 border-[#E0DCD7] resize-none"
            rows={3}
          />
          <div className="flex gap-2">
            <Button
              onClick={() => createMutation.mutate(newCourse)}
              disabled={!newCourse.title.trim()}
              className="btn-gold"
            >
              Créer
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowCreate(false)}
              className="border-[#E0DCD7] text-[#6B6865]"
            >
              Annuler
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {courses?.map((course) => (
          <div key={course.id} className="card-warm p-5 flex items-center gap-4">
            <img
              src={course.image || "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=200&q=80"}
              alt={course.title}
              className="w-16 h-16 rounded-xl object-cover shrink-0"
            />
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-[#1A1A1A] truncate">{course.title}</h3>
              <p className="text-sm text-[#6B6865] truncate">{course.description}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-[#6B6865] bg-[#F2EDE7] px-2 py-0.5 rounded">
                  {course.category}
                </span>
                <span className="text-xs text-[#6B6865] capitalize">{course.level}</span>
                <span className="text-xs text-[#6B6865]">{course.duration}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                to={`/cours/${course.id}`}
                className="p-2 rounded-lg hover:bg-[#F2EDE7] transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-[#6B6865]" />
              </Link>
              <button
                onClick={() => {
                  if (confirm("Supprimer ce cours ?")) {
                    deleteMutation.mutate({ id: course.id });
                  }
                }}
                className="p-2 rounded-lg hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4 text-[#D32F2F]" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Admin Stats ───
function AdminStats() {
  const { data: courses } = trpc.course.list.useQuery();

  return (
    <div>
      <h2 className="font-serif text-2xl text-[#1A1A1A] mb-6">Statistiques de la plateforme</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-[20px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-[#D4A853]/10 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-[#D4A853]" />
            </div>
          </div>
          <span className="text-3xl font-serif text-[#1A1A1A]">{courses?.length || 0}</span>
          <p className="text-sm text-[#6B6865]">Cours publiés</p>
        </div>

        <div className="bg-white rounded-[20px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-[#2E7D6F]/10 rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-[#2E7D6F]" />
            </div>
          </div>
          <span className="text-3xl font-serif text-[#1A1A1A]">
            {courses?.reduce((acc, c) => acc + (c.enrollmentCount || 0), 0) || 0}
          </span>
          <p className="text-sm text-[#6B6865]">Inscriptions totales</p>
        </div>

        <div className="bg-white rounded-[20px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-[#D4A853]/10 rounded-xl flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-[#D4A853]" />
            </div>
          </div>
          <span className="text-3xl font-serif text-[#1A1A1A]">
            {[...new Set(courses?.map((c) => c.category))].filter(Boolean).length}
          </span>
          <p className="text-sm text-[#6B6865]">Catégories</p>
        </div>

        <div className="bg-white rounded-[20px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-[#2E7D6F]/10 rounded-xl flex items-center justify-center">
              <Award className="w-5 h-5 text-[#2E7D6F]" />
            </div>
          </div>
          <span className="text-3xl font-serif text-[#1A1A1A]">-</span>
          <p className="text-sm text-[#6B6865]">Certificats émis</p>
        </div>
      </div>

      {/* Courses table */}
      <div className="mt-8 bg-white rounded-[20px] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[#E0DCD7]">
          <h3 className="font-medium text-[#1A1A1A]">Détail des cours</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#E0DCD7]">
                <th className="text-left text-xs font-dm font-semibold text-[#6B6865] uppercase px-6 py-3">Cours</th>
                <th className="text-left text-xs font-dm font-semibold text-[#6B6865] uppercase px-6 py-3">Catégorie</th>
                <th className="text-left text-xs font-dm font-semibold text-[#6B6865] uppercase px-6 py-3">Niveau</th>
                <th className="text-left text-xs font-dm font-semibold text-[#6B6865] uppercase px-6 py-3">Durée</th>
              </tr>
            </thead>
            <tbody>
              {courses?.map((course) => (
                <tr key={course.id} className="border-b border-[#E0DCD7]/50 hover:bg-[#F2EDE7]/30">
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-[#1A1A1A]">{course.title}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs bg-[#F2EDE7] px-2 py-0.5 rounded">{course.category}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs text-[#6B6865] capitalize">{course.level}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs text-[#6B6865]">{course.duration}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
