import { useEffect, useRef, useCallback } from "react";
import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  BookOpen,
  Clock,
  Users,
  ChevronRight,
  ArrowRight,
  Award,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

gsap.registerPlugin(ScrollTrigger);

// ─── Hero Rolling Text ───
function HeroRollingText() {
  const containerRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const texts = ["Découvrir.", "Apprendre.", "Analyser.", "Comprendre.", "Réussir."];
  const currentTextRef = useRef(texts[0]);
  const hoverTlRef = useRef<gsap.core.Timeline | null>(null);
  const leaveTlRef = useRef<gsap.core.Timeline | null>(null);
  const isHoveringRef = useRef(false);

  const cycle = useCallback((nextText: string) => {
    if (!titleRef.current) return;
    gsap.to(titleRef.current, {
      duration: 0.4,
      opacity: 0,
      y: -10,
      onComplete: () => {
        if (titleRef.current) {
          titleRef.current.textContent = nextText;
          currentTextRef.current = nextText;
          gsap.fromTo(titleRef.current, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3 });
        }
      },
    });
  }, []);

  const handleMouseEnter = useCallback(() => {
    isHoveringRef.current = true;
    if (leaveTlRef.current?.isActive()) leaveTlRef.current.kill();
    if (hoverTlRef.current?.isActive()) return;

    hoverTlRef.current = gsap.timeline();
    texts.forEach((text) => {
      if (text !== currentTextRef.current) {
        hoverTlRef.current!.add(() => cycle(text), "+=0.4");
      }
    });
  }, [cycle]);

  const handleMouseLeave = useCallback(() => {
    isHoveringRef.current = false;
    if (hoverTlRef.current?.isActive()) hoverTlRef.current.kill();
    if (leaveTlRef.current?.isActive()) return;

    leaveTlRef.current = gsap.timeline();
    if (currentTextRef.current !== texts[0]) {
      leaveTlRef.current.add(() => cycle(texts[0]));
    }
  }, [cycle]);

  return (
    <div
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="relative flex items-center justify-center min-h-[60vh] py-20"
    >
      <h1
        ref={titleRef}
        className="font-serif text-[#1A1A1A] text-center leading-none select-none"
        style={{ fontSize: "clamp(3rem, 10vw, 8rem)" }}
      >
        {texts[0]}
      </h1>
      <div className="absolute bottom-8 right-8 glass-badge hidden sm:block">
        +120 formations en ligne
      </div>
    </div>
  );
}

// ─── Parallax Gallery ───
const galleryImages = [
  {
    src: "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=800&q=80",
    caption: "Bibliothèque d'étude",
    position: "left" as const,
  },
  {
    src: "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=600&q=80",
    caption: "Apprentissage collaboratif",
    position: "right" as const,
  },
  {
    src: "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=700&q=80",
    caption: "Concentration et savoir",
    position: "center" as const,
  },
  {
    src: "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=80",
    caption: "Recherche académique",
    position: "left" as const,
  },
];

function ParallaxGallery() {
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;
    const items = gsap.utils.toArray<HTMLElement>(".parallax-item");
    const triggers: ScrollTrigger[] = [];

    items.forEach((section, index) => {
      const img = section.querySelector(".parallax-img");
      if (!img) return;

      const isEven = index % 2 === 0;
      const startX = isEven ? -120 : 120;

      const tween = gsap.fromTo(
        img,
        { x: startX, opacity: 0.7 },
        {
          x: 0,
          opacity: 1,
          scrollTrigger: {
            trigger: section,
            scrub: 0.8,
            start: "top bottom",
            end: "bottom top",
          },
        }
      );

      if (tween.scrollTrigger) triggers.push(tween.scrollTrigger);
    });

    return () => {
      triggers.forEach((t) => t.kill());
    };
  }, []);

  return (
    <section ref={sectionRef} className="py-20 px-4 overflow-hidden">
      <div className="max-w-5xl mx-auto mb-12 text-center">
        <h2 className="font-serif text-4xl md:text-5xl text-[#1A1A1A] mb-4">
          Une expérience immersive
        </h2>
        <p className="text-[#6B6865] max-w-2xl mx-auto">
          Plongez dans un environnement d'apprentissage conçu pour stimuler votre curiosité et structurer votre progression.
        </p>
      </div>
      <div className="space-y-12">
        {galleryImages.map((img, i) => (
          <div
            key={i}
            className={`parallax-item flex ${
              img.position === "left"
                ? "justify-start pl-[5vw] md:pl-[15vw]"
                : img.position === "right"
                ? "justify-end pr-[5vw] md:pr-[15vw]"
                : "justify-center"
            }`}
          >
            <div
              className={`parallax-img relative rounded-[20px] overflow-hidden shadow-[0_12px_32px_rgba(0,0,0,0.06)] ${
                i === 0 ? "w-[70vw] md:w-[50vw] h-[40vw]" : i === 1 ? "w-[50vw] md:w-[25vw] h-[50vw] md:h-[25vw]" : "w-[60vw] md:w-[35vw] h-[35vw] md:h-[25vw]"
              }`}
            >
              <img
                src={img.src}
                alt={img.caption}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm px-3 py-1.5 rounded-lg">
                <span className="text-sm font-dm font-medium text-[#1A1A1A]">
                  {img.caption}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── Featured Courses Section ───
function FeaturedCourses() {
  const { data: courses } = trpc.course.list.useQuery();
  const { isAuthenticated } = useAuth();
  const { data: myEnrollments } = trpc.enrollment.myEnrollments.useQuery(undefined, {
    enabled: isAuthenticated,
  });
  const utils = trpc.useUtils();
  const enrollMutation = trpc.enrollment.enroll.useMutation({
    onSuccess: () => {
      utils.enrollment.myEnrollments.invalidate();
    },
  });

  const isEnrolled = (courseId: number) => {
    return myEnrollments?.some((e) => e.course?.id === courseId);
  };

  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-12">
          <div>
            <h2 className="font-serif text-4xl md:text-5xl text-[#1A1A1A] mb-2">
              Formations en vedette
            </h2>
            <p className="text-[#6B6865]">
              Découvrez nos cours les plus populaires
            </p>
          </div>
          <Link
            to="/cours"
            className="hidden sm:flex items-center gap-2 text-[#D4A853] font-medium hover:underline"
          >
            Voir tous les cours
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {courses?.slice(0, 4).map((course) => (
            <div
              key={course.id}
              className="card-warm overflow-hidden group"
            >
              <div className="relative h-48 overflow-hidden">
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
              </div>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-dm text-[#6B6865] bg-[#F2EDE7] px-2 py-0.5 rounded">
                    {course.category}
                  </span>
                  <span className="text-xs text-[#6B6865] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {course.duration}
                  </span>
                </div>
                <h3 className="font-serif text-xl text-[#1A1A1A] mb-2 group-hover:text-[#D4A853] transition-colors">
                  {course.title}
                </h3>
                <p className="text-sm text-[#6B6865] line-clamp-2 mb-4">
                  {course.description}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-[#6B6865]" />
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
                      Détails
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Student Dashboard ───
function StudentDashboard() {
  const { data: enrollments } = trpc.enrollment.myEnrollments.useQuery();
  const { data: certificates } = trpc.certificate.myCertificates.useQuery();

  if (!enrollments || enrollments.length === 0) return null;

  const activeEnrollments = enrollments.filter((e) => e.status === "active");

  return (
    <section className="py-16 px-4 bg-[#F2EDE7]">
      <div className="max-w-6xl mx-auto">
        <h2 className="font-serif text-3xl md:text-4xl text-[#1A1A1A] mb-8">
          Mon tableau de bord
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Stats cards */}
          <div className="bg-white rounded-[20px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <BookOpen className="w-5 h-5 text-[#D4A853]" />
              <span className="text-sm text-[#6B6865]">Cours actifs</span>
            </div>
            <span className="text-3xl font-serif text-[#1A1A1A]">
              {activeEnrollments.length}
            </span>
          </div>
          <div className="bg-white rounded-[20px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <Award className="w-5 h-5 text-[#2E7D6F]" />
              <span className="text-sm text-[#6B6865]">Certificats</span>
            </div>
            <span className="text-3xl font-serif text-[#1A1A1A]">
              {certificates?.length || 0}
            </span>
          </div>
          <div className="bg-white rounded-[20px] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 className="w-5 h-5 text-[#D4A853]" />
              <span className="text-sm text-[#6B6865]">Progression moyenne</span>
            </div>
            <span className="text-3xl font-serif text-[#1A1A1A]">
              {Math.round(
                activeEnrollments.reduce((acc, e) => acc + (e.progress || 0), 0) /
                  (activeEnrollments.length || 1)
              )}%
            </span>
          </div>
        </div>

        {/* Active courses progress */}
        <div className="bg-white rounded-[20px] p-6 shadow-sm">
          <h3 className="font-serif text-xl mb-4">Progression des cours</h3>
          <div className="space-y-4">
            {activeEnrollments.slice(0, 4).map((enrollment) => (
              <div key={enrollment.id} className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-[#1A1A1A]">
                      {enrollment.course?.title}
                    </span>
                    <span className="text-sm text-[#6B6865]">
                      {Math.round(enrollment.progress || 0)}%
                    </span>
                  </div>
                  <Progress
                    value={enrollment.progress || 0}
                    className="h-2 bg-[#E0DCD7]"
                  />
                </div>
                <Link
                  to={`/cours/${enrollment.course?.id}`}
                  className="text-[#D4A853] hover:underline text-sm shrink-0"
                >
                  Reprendre
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Platform Overview ───
function PlatformOverview() {
  const features = [
    {
      icon: Sparkles,
      title: "Accompagnement personnalisé",
      description: "Chaque apprenant bénéficie d'un suivi individualisé pour maximiser ses résultats.",
    },
    {
      icon: BookOpen,
      title: "Contenus de qualité",
      description: "Des cours conçus par des experts dans leur domaine, avec des supports pédagogiques riches.",
    },
    {
      icon: Award,
      title: "Certifications reconnues",
      description: "Obtenez des certificats à la fin de chaque formation pour valoriser vos compétences.",
    },
    {
      icon: BarChart3,
      title: "Suivi de progression",
      description: "Visualisez votre avancement en temps réel et identifiez vos points d'amélioration.",
    },
  ];

  return (
    <section className="py-20 px-4">
      <div className="max-w-3xl mx-auto text-center mb-16">
        <h2 className="font-serif text-3xl md:text-4xl text-[#1A1A1A] mb-6">
          Aura, votre espace de formation
        </h2>
        <p className="text-lg text-[#6B6865] leading-relaxed">
          Aura est une plateforme LMS haut de gamme dédiée à la formation continue.
          Grâce à un accompagnement pédagogique personnalisé et des outils ergonomiques,
          elle rend le parcours de l'apprenant fluide et structuré.
        </p>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature, i) => {
          const Icon = feature.icon;
          return (
            <div key={i} className="card-warm p-6 text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-[#FDF5E6] rounded-xl flex items-center justify-center">
                <Icon className="w-6 h-6 text-[#D4A853]" />
              </div>
              <h3 className="font-serif text-lg text-[#1A1A1A] mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-[#6B6865]">{feature.description}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ─── Main Home Page ───
export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      {/* Hero */}
      <section className="relative px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <HeroRollingText />
        </div>
      </section>

      {/* Platform Overview */}
      <div className="border-t border-[#E0DCD7]">
        <PlatformOverview />
      </div>

      {/* Student Dashboard (if authenticated) */}
      {isAuthenticated && (
        <div className="border-t border-[#E0DCD7]">
          <StudentDashboard />
        </div>
      )}

      {/* Featured Courses */}
      <div className="border-t border-[#E0DCD7]">
        <FeaturedCourses />
      </div>

      {/* Parallax Gallery */}
      <div className="border-t border-[#E0DCD7]">
        <ParallaxGallery />
      </div>
    </div>
  );
}
