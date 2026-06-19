import { useState } from "react";
import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Send,
  BookOpen,
  Award,
} from "lucide-react";

export default function Assignments() {
  const { isAuthenticated } = useAuth();
  const { data: myEnrollments } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const [selectedCourse, setSelectedCourse] = useState<number | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<number | null>(null);
  const [submissionContent, setSubmissionContent] = useState("");
  const utils = trpc.useUtils();

  const submitMutation = trpc.submission.create.useMutation({
    onSuccess: () => {
      utils.submission.mySubmissions.invalidate();
      utils.assignment.mySubmissions.invalidate({ courseId: selectedCourse! });
      setSubmissionContent("");
      setSelectedAssignment(null);
    },
  });

  // Get assignments for selected course
  const { data: courseAssignments } = trpc.assignment.listByCourse.useQuery(
    { courseId: selectedCourse! },
    { enabled: selectedCourse !== null }
  );

  // Get submissions for selected course
  const { data: assignmentSubs } = trpc.assignment.mySubmissions.useQuery(
    { courseId: selectedCourse! },
    { enabled: selectedCourse !== null && isAuthenticated }
  );

  if (!isAuthenticated) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <FileText className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
        <p className="text-[#6B6865] mb-4">Connectez-vous pour voir vos devoirs.</p>
        <Link to="/login" className="btn-gold">Se connecter</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="font-serif text-4xl md:text-5xl text-[#1A1A1A] mb-4">
          Mes devoirs
        </h1>
        <p className="text-[#6B6865]">
          Consultez et soumettez vos devoirs pour chaque cours.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Course Selector */}
        <div className="lg:col-span-1">
          <h2 className="font-serif text-xl text-[#1A1A1A] mb-4">Mes cours</h2>
          <div className="space-y-2">
            {myEnrollments?.filter((e) => e.status === "active").map((enrollment) => (
              <button
                key={enrollment.id}
                onClick={() => {
                  setSelectedCourse(enrollment.course?.id || null);
                  setSelectedAssignment(null);
                }}
                className={`w-full text-left p-4 rounded-[12px] transition-all duration-200 ${
                  selectedCourse === enrollment.course?.id
                    ? "bg-[#D4A853]/10 border border-[#D4A853]/30"
                    : "bg-[#F2EDE7] hover:bg-[#EDE8E2]"
                }`}
              >
                <h3 className="font-medium text-[#1A1A1A] text-sm">
                  {enrollment.course?.title}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <Progress value={enrollment.progress || 0} className="h-1.5 flex-1 bg-[#E0DCD7]" />
                  <span className="text-xs text-[#6B6865]">{Math.round(enrollment.progress || 0)}%</span>
                </div>
              </button>
            ))}

            {(!myEnrollments || myEnrollments.filter((e) => e.status === "active").length === 0) && (
              <div className="text-center py-8 bg-[#F2EDE7] rounded-[12px]">
                <BookOpen className="w-8 h-8 text-[#E0DCD7] mx-auto mb-2" />
                <p className="text-sm text-[#6B6865]">Vous n'êtes inscrit à aucun cours.</p>
                <Link to="/cours" className="text-[#D4A853] hover:underline text-sm mt-2 inline-block">
                  Parcourir les cours
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Assignments List */}
        <div className="lg:col-span-2">
          {selectedCourse ? (
            <>
              <h2 className="font-serif text-xl text-[#1A1A1A] mb-4">
                Devoirs
                {courseAssignments && (
                  <span className="text-base font-sans text-[#6B6865] ml-2">
                    ({courseAssignments.length})
                  </span>
                )}
              </h2>

              {selectedAssignment && courseAssignments ? (
                <div className="card-warm p-6">
                  {(() => {
                    const assignment = courseAssignments.find((a) => a.id === selectedAssignment);
                    if (!assignment) return null;
                    return (
                      <>
                        <h3 className="font-serif text-xl text-[#1A1A1A] mb-2">
                          {assignment.title}
                        </h3>
                        <p className="text-sm text-[#6B6865] mb-4">{assignment.description}</p>
                        <div className="flex items-center gap-4 mb-6">
                          <span className="text-xs text-[#6B6865]">
                            Note maximale : {assignment.maxScore}
                          </span>
                          {assignment.dueDate && (
                            <span className="flex items-center gap-1 text-xs text-[#D32F2F]">
                              <AlertCircle className="w-3.5 h-3.5" />
                              Date limite : {new Date(assignment.dueDate).toLocaleDateString("fr-FR")}
                            </span>
                          )}
                        </div>

                        <Textarea
                          placeholder="Rédigez votre réponse ici..."
                          value={submissionContent}
                          onChange={(e) => setSubmissionContent(e.target.value)}
                          className="mb-4 border-[#E0DCD7] resize-none min-h-[200px]"
                        />
                        <div className="flex gap-2">
                          <Button
                            onClick={() =>
                              submitMutation.mutate({
                                assignmentId: selectedAssignment,
                                content: submissionContent,
                              })
                            }
                            disabled={!submissionContent.trim()}
                            className="btn-gold"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Soumettre
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setSelectedAssignment(null)}
                            className="border-[#E0DCD7] text-[#6B6865]"
                          >
                            Annuler
                          </Button>
                        </div>
                      </>
                    );
                  })()}
                </div>
              ) : (
                <div className="space-y-3">
                  {courseAssignments?.map((assignment) => {
                    const sub = assignmentSubs?.find(
                      (s) => s.assignment.id === assignment.id
                    );
                    return (
                      <div key={assignment.id} className="card-warm p-5">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-medium text-[#1A1A1A] mb-1">
                              {assignment.title}
                            </h3>
                            <p className="text-sm text-[#6B6865] mb-2">
                              {assignment.description}
                            </p>
                            <div className="flex items-center gap-3">
                              <span className="text-xs text-[#6B6865]">
                                Note max : {assignment.maxScore}
                              </span>
                              {assignment.dueDate && (
                                <span className="flex items-center gap-1 text-xs text-[#D32F2F]">
                                  <Clock className="w-3 h-3" />
                                  {new Date(assignment.dueDate).toLocaleDateString("fr-FR")}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            {sub?.submission ? (
                              <div>
                                <span
                                  className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                                    sub.submission.status === "graded"
                                      ? "bg-[#2E7D6F]/10 text-[#2E7D6F]"
                                      : "bg-[#D4A853]/10 text-[#D4A853]"
                                  }`}
                                >
                                  {sub.submission.status === "graded" ? (
                                    <span className="flex items-center gap-1">
                                      <Award className="w-3 h-3" />
                                      Noté
                                    </span>
                                  ) : (
                                    <span className="flex items-center gap-1">
                                      <CheckCircle2 className="w-3 h-3" />
                                      Soumis
                                    </span>
                                  )}
                                </span>
                                {sub.submission.score !== null && sub.submission.score !== undefined && (
                                  <p className="text-sm text-[#1A1A1A] mt-2">
                                    <span className="font-semibold">{sub.submission.score}</span>
                                    <span className="text-[#6B6865]">/{assignment.maxScore}</span>
                                  </p>
                                )}
                              </div>
                            ) : (
                              <Button
                                size="sm"
                                onClick={() => setSelectedAssignment(assignment.id)}
                                className="btn-gold text-xs py-1.5 px-3"
                              >
                                Soumettre
                                <ArrowRight className="w-3 h-3 ml-1" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {(!courseAssignments || courseAssignments.length === 0) && (
                    <div className="text-center py-12 card-warm">
                      <FileText className="w-10 h-10 text-[#E0DCD7] mx-auto mb-3" />
                      <p className="text-[#6B6865]">Aucun devoir pour ce cours.</p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20 card-warm">
              <BookOpen className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
              <p className="text-[#6B6865] mb-2">Sélectionnez un cours pour voir les devoirs.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
