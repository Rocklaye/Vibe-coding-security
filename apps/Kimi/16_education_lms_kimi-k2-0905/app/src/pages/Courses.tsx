import { useState } from "react";
import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  BookOpen,
  Clock,
  Search,
  ChevronRight,
  SlidersHorizontal,
  GraduationCap,
  CheckCircle2,
} from "lucide-react";

export default function Courses() {
  const { isAuthenticated } = useAuth();
  const { data: courses } = trpc.course.list.useQuery();
  const { data: myEnrollments } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: isAuthenticated,
  });
  const utils = trpc.useUtils();
  const enrollMutation = trpc.enrollment.enroll.useMutation({
    onSuccess: () => {
      utils.enrollment.myEnrollments.invalidate();
    },
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);

  const categories = [...new Set(courses?.map((c) => c.category).filter(Boolean))];
  const levels = ["debutant", "intermediaire", "avance"];

  const filteredCourses = courses?.filter((course) => {
    const matchesSearch = !searchQuery ||
      course.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || course.category === selectedCategory;
    const matchesLevel = !selectedLevel || course.level === selectedLevel;
    return matchesSearch && matchesCategory && matchesLevel;
  });

  const isEnrolled = (courseId: number) => {
    return myEnrollments?.some((e) => e.course?.id === courseId);
  };

  const levelLabels: Record<string, string> = {
    debutant: "Débutant",
    intermediaire: "Intermédiaire",
    avance: "Avancé",
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="font-serif text-4xl md:text-5xl text-[#1A1A1A] mb-4">
          Bibliothèque de cours
        </h1>
        <p className="text-[#6B6865] max-w-2xl">
          Explorez notre catalogue de formations et trouvez le cours qui correspond à vos objectifs.
        </p>
      </div>

      {/* Search & Filters */}
      <div className="mb-8 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B6865]" />
          <Input
            placeholder="Rechercher un cours..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white border-[#E0DCD7] rounded-xl h-12 text-[#1A1A1A] placeholder:text-[#6B6865]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <SlidersHorizontal className="w-4 h-4 text-[#6B6865]" />
          <span className="text-sm text-[#6B6865]">Filtres :</span>

          {/* Category filters */}
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(null)}
            className={`rounded-lg text-xs ${
              selectedCategory === null
                ? "bg-[#D4A853] text-white hover:bg-[#c49a4a]"
                : "border-[#E0DCD7] text-[#6B6865] hover:bg-[#F2EDE7]"
            }`}
          >
            Toutes les catégories
          </Button>
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
              className={`rounded-lg text-xs ${
                selectedCategory === cat
                  ? "bg-[#D4A853] text-white hover:bg-[#c49a4a]"
                  : "border-[#E0DCD7] text-[#6B6865] hover:bg-[#F2EDE7]"
              }`}
            >
              {cat}
            </Button>
          ))}

          <div className="w-px h-6 bg-[#E0DCD7]" />

          {/* Level filters */}
          {levels.map((level) => (
            <Button
              key={level}
              variant={selectedLevel === level ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedLevel(level === selectedLevel ? null : level)}
              className={`rounded-lg text-xs ${
                selectedLevel === level
                  ? "bg-[#D4A853] text-white hover:bg-[#c49a4a]"
                  : "border-[#E0DCD7] text-[#6B6865] hover:bg-[#F2EDE7]"
              }`}
            >
              {levelLabels[level]}
            </Button>
          ))}
        </div>
      </div>

      {/* Course Grid */}
      {filteredCourses && filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <div key={course.id} className="card-warm overflow-hidden group">
              <div className="relative h-44 overflow-hidden">
                <img
                  src={course.image || "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=800&q=80"}
                  alt={course.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-lg">
                  <span className="text-xs font-dm font-semibold text-[#D4A853] uppercase">
                    {course.level}
                  </span>
                </div>
                {isAuthenticated && isEnrolled(course.id) && (
                  <div className="absolute top-3 left-3 bg-[#2E7D6F]/90 backdrop-blur-sm px-2.5 py-1 rounded-lg flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                    <span className="text-xs font-dm font-semibold text-white">
                      Inscrit
                    </span>
                  </div>
                )}
              </div>
              <div className="p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-dm text-[#6B6865] bg-[#F2EDE7] px-2 py-0.5 rounded">
                    {course.category}
                  </span>
                  <span className="text-xs text-[#6B6865] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {course.duration}
                  </span>
                </div>
                <h3 className="font-serif text-lg text-[#1A1A1A] mb-2 group-hover:text-[#D4A853] transition-colors">
                  {course.title}
                </h3>
                <p className="text-sm text-[#6B6865] line-clamp-2 mb-4">
                  {course.description}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-[#6B6865]" />
                    <span className="text-sm text-[#6B6865]">
                      {course.instructor?.name || "Instructeur"}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {isAuthenticated && !isEnrolled(course.id) && (
                      <Button
                        size="sm"
                        onClick={() => enrollMutation.mutate({ courseId: course.id })}
                        className="btn-gold text-xs py-1.5 px-3"
                      >
                        S'inscrire
                      </Button>
                    )}
                    <Link
                      to={`/cours/${course.id}`}
                      className="flex items-center gap-1 text-sm text-[#D4A853] font-medium hover:underline"
                    >
                      Voir
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <BookOpen className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
          <p className="text-[#6B6865]">Aucun cours ne correspond à vos critères.</p>
        </div>
      )}
    </div>
  );
}
