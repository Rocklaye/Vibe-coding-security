import { useState } from "react";
import { useParams, Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  BookOpen,
  Clock,
  GraduationCap,
  ChevronRight,
  ChevronDown,
  Play,
  CheckCircle2,
  Circle,
  FileText,
  MessageSquare,
  ArrowLeft,
  Award,
  Lock,
  Users,
} from "lucide-react";

export default function CourseDetail() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);
  const { isAuthenticated } = useAuth();
  const utils = trpc.useUtils();

  const { data: course, isLoading } = trpc.course.getById.useQuery({ id: courseId });
  const { data: myEnrollments } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: isAuthenticated,
  });
  const { data: assignmentSubmissions } = trpc.assignment.mySubmissions.useQuery(
    { courseId },
    { enabled: isAuthenticated }
  );
  const { data: forumTopicsList } = trpc.forum.listTopics.useQuery({ courseId });
  const { data: myCertificates } = trpc.certificate.myCertificates.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const enrollMutation = trpc.enrollment.enroll.useMutation({
    onSuccess: () => {
      utils.enrollment.myEnrollments.invalidate();
    },
  });
  const generateCertMutation = trpc.certificate.generate.useMutation({
    onSuccess: () => {
      utils.certificate.myCertificates.invalidate();
    },
  });

  const [expandedModule, setExpandedModule] = useState<number | null>(0);
  const [activeTab, setActiveTab] = useState("content");

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <div className="animate-pulse">Chargement du cours...</div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <p className="text-[#6B6865]">Cours non trouvé.</p>
        <Link to="/cours" className="text-[#D4A853] hover:underline mt-4 inline-block">
          Retour aux cours
        </Link>
      </div>
    );
  }

  const enrollment = myEnrollments?.find((e) => e.course?.id === courseId);
  const isEnrolled = !!enrollment;
  const hasCertificate = myCertificates?.some((c) => c.course?.id === courseId);
  const isCourseCompleted = enrollment?.status === "completed";
  const totalLessons = course.modules?.reduce((acc, m) => acc + (m.lessons?.length || 0), 0) || 0;

  return (
    <div>
      {/* Hero */}
      <div className="relative h-[40vh] min-h-[300px] overflow-hidden">
        <img
          src={course.image || "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=1200&q=80"}
          alt={course.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10">
          <div className="max-w-5xl mx-auto">
            <Link
              to="/cours"
              className="inline-flex items-center gap-1 text-white/80 hover:text-white text-sm mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour aux cours
            </Link>
            <h1 className="font-serif text-3xl md:text-5xl text-white mb-3">
              {course.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-white/80">
              <span className="flex items-center gap-1 text-sm">
                <GraduationCap className="w-4 h-4" />
                {course.instructor?.name || "Instructeur"}
              </span>
              <span className="flex items-center gap-1 text-sm">
                <Clock className="w-4 h-4" />
                {course.duration}
              </span>
              <span className="px-2.5 py-0.5 bg-white/20 backdrop-blur-sm rounded-lg text-xs font-dm font-semibold uppercase">
                {course.level}
              </span>
              <span className="px-2.5 py-0.5 bg-[#D4A853]/80 rounded-lg text-xs font-dm font-semibold">
                {course.category}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Enrollment bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8 p-4 bg-[#F2EDE7] rounded-[16px]">
          <div className="flex items-center gap-4">
            {isEnrolled ? (
              <>
                <div className="flex-1 min-w-[200px]">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-[#1A1A1A]">Progression</span>
                    <span className="text-sm text-[#6B6865]">{Math.round(enrollment?.progress || 0)}%</span>
                  </div>
                  <Progress value={enrollment?.progress || 0} className="h-2.5 bg-[#E0DCD7]" />
                </div>
                {isCourseCompleted && (
                  <div className="flex items-center gap-1 text-[#2E7D6F]">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="text-sm font-medium">Terminé</span>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-[#6B6865]">
                Inscrivez-vous pour accéder au contenu complet et suivre votre progression.
              </p>
            )}
          </div>
          <div className="flex gap-3">
            {isAuthenticated && isCourseCompleted && !hasCertificate && (
              <Button
                onClick={() => generateCertMutation.mutate({ courseId })}
                className="bg-[#2E7D6F] hover:bg-[#266b5f] text-white rounded-xl"
              >
                <Award className="w-4 h-4 mr-2" />
                Générer le certificat
              </Button>
            )}
            {hasCertificate && (
              <div className="flex items-center gap-2 px-4 py-2 bg-[#2E7D6F]/10 rounded-xl">
                <Award className="w-4 h-4 text-[#2E7D6F]" />
                <span className="text-sm text-[#2E7D6F] font-medium">Certifié</span>
              </div>
            )}
            {!isEnrolled && isAuthenticated && (
              <Button
                onClick={() => enrollMutation.mutate({ courseId })}
                className="btn-gold"
              >
                S'inscrire au cours
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-[#F2EDE7] rounded-xl mb-6">
            <TabsTrigger value="content" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-[#1A1A1A]">
              <BookOpen className="w-4 h-4 mr-2" />
              Contenu
            </TabsTrigger>
            <TabsTrigger value="assignments" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-[#1A1A1A]">
              <FileText className="w-4 h-4 mr-2" />
              Devoirs
            </TabsTrigger>
            <TabsTrigger value="forum" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-[#1A1A1A]">
              <MessageSquare className="w-4 h-4 mr-2" />
              Forum
            </TabsTrigger>
          </TabsList>

          {/* Content Tab */}
          <TabsContent value="content">
            <div className="mb-6">
              <h2 className="font-serif text-2xl text-[#1A1A1A] mb-2">Description</h2>
              <p className="text-[#6B6865] leading-relaxed">{course.description}</p>
            </div>

            {/* Modules & Lessons */}
            <div className="space-y-3">
              <h2 className="font-serif text-2xl text-[#1A1A1A] mb-4">
                Programme du cours
                <span className="text-base font-sans text-[#6B6865] ml-2">
                  ({course.modules?.length || 0} modules, {totalLessons} leçons)
                </span>
              </h2>

              {course.modules?.map((module, mi) => (
                <div key={module.id} className="border border-[#E0DCD7] rounded-[16px] overflow-hidden">
                  <button
                    onClick={() => setExpandedModule(expandedModule === mi ? null : mi)}
                    className="w-full flex items-center justify-between p-4 bg-[#F2EDE7] hover:bg-[#EDE8E2] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 bg-[#D4A853]/10 rounded-lg flex items-center justify-center text-sm font-dm font-semibold text-[#D4A853]">
                        {mi + 1}
                      </span>
                      <div className="text-left">
                        <h3 className="font-medium text-[#1A1A1A]">{module.title}</h3>
                        {module.description && (
                          <p className="text-sm text-[#6B6865]">{module.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[#6B6865]">
                        {module.lessons?.length || 0} leçons
                      </span>
                      <ChevronDown
                        className={`w-5 h-5 text-[#6B6865] transition-transform ${
                          expandedModule === mi ? "rotate-180" : ""
                        }`}
                      />
                    </div>
                  </button>

                  {expandedModule === mi && (
                    <div className="divide-y divide-[#E0DCD7]">
                      {module.lessons?.map((lesson) => (
                        <div
                          key={lesson.id}
                          className="flex items-center gap-3 p-4 hover:bg-[#F2EDE7]/50 transition-colors"
                        >
                          {isEnrolled ? (
                            <Circle className="w-4 h-4 text-[#E0DCD7]" />
                          ) : (
                            <Lock className="w-4 h-4 text-[#E0DCD7]" />
                          )}
                          <div className="flex-1">
                            <span className="text-sm text-[#1A1A1A]">{lesson.title}</span>
                            {lesson.duration && (
                              <span className="text-xs text-[#6B6865] ml-2">
                                ({lesson.duration} min)
                              </span>
                            )}
                          </div>
                          {isEnrolled && (
                            <Link
                              to={`/cours/${courseId}/lecon/${lesson.id}`}
                              className="flex items-center gap-1 text-sm text-[#D4A853] hover:underline"
                            >
                              <Play className="w-3.5 h-3.5" />
                              Commencer
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>

          {/* Assignments Tab */}
          <TabsContent value="assignments">
            <h2 className="font-serif text-2xl text-[#1A1A1A] mb-6">Devoirs et évaluations</h2>
            {assignmentSubmissions && assignmentSubmissions.length > 0 ? (
              <div className="space-y-4">
                {assignmentSubmissions.map(({ assignment, submission }) => (
                  <div key={assignment.id} className="card-warm p-6">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-[#1A1A1A] mb-1">{assignment.title}</h3>
                        <p className="text-sm text-[#6B6865] mb-3">{assignment.description}</p>
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-[#6B6865]">
                            Note maximale : {assignment.maxScore}
                          </span>
                          {assignment.dueDate && (
                            <span className="text-xs text-[#6B6865]">
                              Date limite : {new Date(assignment.dueDate).toLocaleDateString("fr-FR")}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        {submission ? (
                          <div>
                            <span
                              className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                                submission.status === "graded"
                                  ? "bg-[#2E7D6F]/10 text-[#2E7D6F]"
                                  : "bg-[#D4A853]/10 text-[#D4A853]"
                              }`}
                            >
                              {submission.status === "graded" ? "Noté" : "Soumis"}
                            </span>
                            {submission.score !== null && submission.score !== undefined && (
                              <p className="text-sm text-[#1A1A1A] mt-2">
                                Note : <span className="font-semibold">{submission.score}/{assignment.maxScore}</span>
                              </p>
                            )}
                          </div>
                        ) : (
                          <Link
                            to={`/cours/${courseId}/devoirs`}
                            className="text-sm text-[#D4A853] hover:underline"
                          >
                            Soumettre
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-10 h-10 text-[#E0DCD7] mx-auto mb-3" />
                <p className="text-[#6B6865]">Aucun devoir pour ce cours.</p>
              </div>
            )}
          </TabsContent>

          {/* Forum Tab */}
          <TabsContent value="forum">
            <ForumSection courseId={courseId} topics={forumTopicsList || []} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// ─── Forum Section ───
function ForumSection({ courseId, topics }: { courseId: number; topics: any[] }) {
  const { isAuthenticated } = useAuth();
  const utils = trpc.useUtils();
  const [newTopicTitle, setNewTopicTitle] = useState("");
  const [newTopicContent, setNewTopicContent] = useState("");
  const [showNewTopic, setShowNewTopic] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState("");

  const { data: topicDetail } = trpc.forum.getTopic.useQuery(
    { id: selectedTopic! },
    { enabled: selectedTopic !== null }
  );

  const createTopicMutation = trpc.forum.createTopic.useMutation({
    onSuccess: () => {
      utils.forum.listTopics.invalidate({ courseId });
      setNewTopicTitle("");
      setNewTopicContent("");
      setShowNewTopic(false);
    },
  });

  const createReplyMutation = trpc.forum.createReply.useMutation({
    onSuccess: () => {
      utils.forum.getTopic.invalidate({ id: selectedTopic! });
      setReplyContent("");
    },
  });

  if (selectedTopic && topicDetail) {
    return (
      <div>
        <button
          onClick={() => setSelectedTopic(null)}
          className="flex items-center gap-1 text-sm text-[#D4A853] hover:underline mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour au forum
        </button>

        <div className="card-warm p-6 mb-6">
          <h3 className="font-serif text-xl text-[#1A1A1A] mb-2">{topicDetail.title}</h3>
          <p className="text-sm text-[#6B6865] mb-3">{topicDetail.content}</p>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-[#D4A853]/20 flex items-center justify-center">
              <Users className="w-3 h-3 text-[#D4A853]" />
            </div>
            <span className="text-xs text-[#6B6865]">{topicDetail.user?.name}</span>
            <span className="text-xs text-[#6B6865]">
              {new Date(topicDetail.createdAt).toLocaleDateString("fr-FR")}
            </span>
          </div>
        </div>

        {/* Replies */}
        <div className="space-y-4 mb-6">
          <h4 className="font-medium text-[#1A1A1A]">
            {topicDetail.replies?.length || 0} réponse(s)
          </h4>
          {topicDetail.replies?.map((reply: any) => (
            <div key={reply.id} className="bg-white border border-[#E0DCD7] rounded-[12px] p-4">
              <p className="text-sm text-[#1A1A1A] mb-2">{reply.content}</p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#6B6865]">{reply.user?.name}</span>
                <span className="text-xs text-[#E0DCD7]">·</span>
                <span className="text-xs text-[#6B6865]">
                  {new Date(reply.createdAt).toLocaleDateString("fr-FR")}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Reply form */}
        {isAuthenticated && (
          <div className="bg-white border border-[#E0DCD7] rounded-[12px] p-4">
            <Textarea
              placeholder="Votre réponse..."
              value={replyContent}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setReplyContent(e.target.value)}
              className="mb-3 border-[#E0DCD7] resize-none"
              rows={3}
            />
            <Button
              onClick={() => createReplyMutation.mutate({ topicId: selectedTopic, content: replyContent })}
              disabled={!replyContent.trim()}
              className="btn-gold"
            >
              Répondre
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-serif text-2xl text-[#1A1A1A]">
          Forum de discussion
          <span className="text-base font-sans text-[#6B6865] ml-2">({topics.length} sujets)</span>
        </h2>
        {isAuthenticated && (
          <Button
            onClick={() => setShowNewTopic(!showNewTopic)}
            className="btn-gold text-sm"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Nouveau sujet
          </Button>
        )}
      </div>

      {showNewTopic && (
        <div className="card-warm p-6 mb-6">
          <h3 className="font-medium text-[#1A1A1A] mb-4">Créer un nouveau sujet</h3>
          <Input
            placeholder="Titre du sujet"
            value={newTopicTitle}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewTopicTitle(e.target.value)}
            className="mb-3 border-[#E0DCD7]"
          />
          <Textarea
            placeholder="Contenu de votre message..."
            value={newTopicContent}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewTopicContent(e.target.value)}
            className="mb-3 border-[#E0DCD7] resize-none"
            rows={4}
          />
          <div className="flex gap-2">
            <Button
              onClick={() =>
                createTopicMutation.mutate({
                  courseId,
                  title: newTopicTitle,
                  content: newTopicContent,
                })
              }
              disabled={!newTopicTitle.trim()}
              className="btn-gold"
            >
              Publier
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowNewTopic(false)}
              className="border-[#E0DCD7] text-[#6B6865]"
            >
              Annuler
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {topics.map((topic) => (
          <button
            key={topic.id}
            onClick={() => setSelectedTopic(topic.id)}
            className="w-full text-left card-warm p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-medium text-[#1A1A1A] mb-1 hover:text-[#D4A853] transition-colors">
                  {topic.title}
                </h3>
                <p className="text-sm text-[#6B6865] line-clamp-1 mb-2">{topic.content}</p>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#6B6865]">{topic.user?.name}</span>
                  <span className="text-xs text-[#E0DCD7]">·</span>
                  <span className="text-xs text-[#6B6865]">
                    {new Date(topic.createdAt).toLocaleDateString("fr-FR")}
                  </span>
                  {topic.isPinned && (
                    <span className="px-2 py-0.5 bg-[#D4A853]/10 text-[#D4A853] text-xs rounded-full font-medium">
                      Épinglé
                    </span>
                  )}
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#E0DCD7] shrink-0" />
            </div>
          </button>
        ))}

        {topics.length === 0 && (
          <div className="text-center py-12">
            <MessageSquare className="w-10 h-10 text-[#E0DCD7] mx-auto mb-3" />
            <p className="text-[#6B6865]">Aucun sujet de discussion pour ce cours.</p>
            {isAuthenticated && (
              <p className="text-sm text-[#6B6865] mt-1">
                Soyez le premier à créer un sujet !
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
