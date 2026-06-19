import { useParams, Link, useNavigate } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock,
  BookOpen,
  Play,
} from "lucide-react";

export default function Lesson() {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const cid = Number(courseId);
  const lid = Number(lessonId);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const utils = trpc.useUtils();

  const { data: course } = trpc.course.getById.useQuery({ id: cid });
  const { data: lesson } = trpc.lesson.getById.useQuery({ id: lid });
  const { data: lessonProgressData } = trpc.lesson.getProgress.useQuery(
    { courseId: cid },
    { enabled: isAuthenticated }
  );
  const { data: myEnrollments } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const updateProgressMutation = trpc.enrollment.updateProgress.useMutation({
    onSuccess: () => {
      utils.enrollment.myEnrollments.invalidate();
    },
  });

  const markCompleteMutation = trpc.lesson.markComplete.useMutation({
    onSuccess: () => {
      utils.lesson.getProgress.invalidate({ courseId: cid });
      updateProgressMutation.mutate({ courseId: cid });
    },
  });

  const isEnrolled = myEnrollments?.some((e) => e.course?.id === cid);
  const isCompleted = lessonProgressData?.some((p) => p.lessonId === lid && p.isCompleted);

  // Find all lessons in order
  const allLessons: { id: number; title: string; moduleTitle: string; order: number }[] = [];
  course?.modules?.forEach((mod) => {
    mod.lessons?.forEach((l) => {
      allLessons.push({
        id: l.id,
        title: l.title,
        moduleTitle: mod.title,
        order: (mod.order || 0) * 100 + (l.order || 0),
      });
    });
  });
  allLessons.sort((a, b) => a.order - b.order);

  const currentIndex = allLessons.findIndex((l) => l.id === lid);
  const prevLesson = currentIndex > 0 ? allLessons[currentIndex - 1] : null;
  const nextLesson = currentIndex < allLessons.length - 1 ? allLessons[currentIndex + 1] : null;

  if (!course || !lesson) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <p className="text-[#6B6865]">Leçon non trouvée.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          to={`/cours/${cid}`}
          className="inline-flex items-center gap-1 text-sm text-[#D4A853] hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour au cours
        </Link>
      </div>

      {/* Lesson Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <span className="px-2.5 py-1 bg-[#F2EDE7] rounded-lg text-xs font-dm text-[#6B6865]">
            Leçon {currentIndex + 1} / {allLessons.length}
          </span>
          {lesson.duration && (
            <span className="flex items-center gap-1 text-xs text-[#6B6865]">
              <Clock className="w-3.5 h-3.5" />
              {lesson.duration} min
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 text-xs text-[#2E7D6F]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Complété
            </span>
          )}
        </div>
        <h1 className="font-serif text-3xl md:text-4xl text-[#1A1A1A] mb-2">
          {lesson.title}
        </h1>
        <p className="text-[#6B6865]">{allLessons[currentIndex]?.moduleTitle || course.title}</p>
      </div>

      {/* Video Placeholder or Content */}
      {lesson.videoUrl ? (
        <div className="aspect-video bg-[#1A1A1A] rounded-[20px] mb-8 flex items-center justify-center overflow-hidden">
          <div className="text-center">
            <Play className="w-16 h-16 text-white/30 mx-auto mb-4" />
            <p className="text-white/50 text-sm">Lecture vidéo</p>
          </div>
        </div>
      ) : (
        <div className="aspect-video bg-[#F2EDE7] rounded-[20px] mb-8 flex items-center justify-center">
          <div className="text-center">
            <BookOpen className="w-16 h-16 text-[#E0DCD7] mx-auto mb-4" />
            <p className="text-[#6B6865] text-sm">Leçon textuelle</p>
          </div>
        </div>
      )}

      {/* Lesson Content */}
      <div className="card-warm p-8 mb-8">
        <h2 className="font-serif text-xl text-[#1A1A1A] mb-4">Contenu de la leçon</h2>
        <div className="prose prose-sm max-w-none text-[#1A1A1A] leading-relaxed whitespace-pre-wrap">
          {lesson.content || "Aucun contenu disponible pour cette leçon."}
        </div>
      </div>

      {/* Lesson Navigation */}
      <div className="flex items-center justify-between">
        {prevLesson ? (
          <Button
            variant="outline"
            onClick={() => navigate(`/cours/${cid}/lecon/${prevLesson.id}`)}
            className="border-[#E0DCD7] text-[#1A1A1A] hover:bg-[#F2EDE7]"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Précédent
          </Button>
        ) : (
          <div />
        )}

        {isAuthenticated && isEnrolled && !isCompleted && (
          <Button
            onClick={() => markCompleteMutation.mutate({ lessonId: lid })}
            className="btn-gold"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Marquer comme terminé
          </Button>
        )}

        {isCompleted && (
          <div className="flex items-center gap-2 px-4 py-2 bg-[#2E7D6F]/10 rounded-xl">
            <CheckCircle2 className="w-5 h-5 text-[#2E7D6F]" />
            <span className="text-[#2E7D6F] font-medium">Leçon complétée</span>
          </div>
        )}

        {nextLesson ? (
          <Button
            onClick={() => navigate(`/cours/${cid}/lecon/${nextLesson.id}`)}
            className="btn-gold"
          >
            Suivant
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        ) : (
          <div />
        )}
      </div>
    </div>
  );
}
