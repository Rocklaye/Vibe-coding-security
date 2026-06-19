import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import {
  Award,
  CheckCircle2,
  GraduationCap,
  ExternalLink,
} from "lucide-react";

export default function Certificates() {
  const { isAuthenticated } = useAuth();
  const { data: certificates, isLoading } = trpc.certificate.myCertificates.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <Award className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
        <p className="text-[#6B6865] mb-4">Connectez-vous pour voir vos certificats.</p>
        <Link to="/login" className="btn-gold">Se connecter</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="font-serif text-4xl md:text-5xl text-[#1A1A1A] mb-4">
          Mes certificats
        </h1>
        <p className="text-[#6B6865]">
          Tous vos certificats de réussite obtenus sur la plateforme.
        </p>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-pulse text-[#6B6865]">Chargement...</div>
        </div>
      ) : certificates && certificates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {certificates.map((cert) => (
            <div key={cert.id} className="card-warm overflow-hidden">
              {/* Certificate visual */}
              <div className="bg-gradient-to-br from-[#1A1A1A] to-[#2d2d2d] p-6 text-center">
                <GraduationCap className="w-12 h-12 text-[#D4A853] mx-auto mb-3" />
                <h3 className="font-serif text-lg text-white mb-1">
                  Certificat de réussite
                </h3>
                <p className="text-sm text-white/60">Aura Espace Formation</p>
              </div>

              <div className="p-6">
                <h4 className="font-serif text-lg text-[#1A1A1A] mb-2">
                  {cert.course?.title}
                </h4>
                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[#6B6865]">Numéro</span>
                    <span className="text-xs font-mono text-[#1A1A1A] bg-[#F2EDE7] px-2 py-0.5 rounded">
                      {cert.certificateNumber?.slice(0, 20)}...
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[#6B6865]">Date d'émission</span>
                    <span className="text-xs text-[#1A1A1A]">
                      {new Date(cert.issuedAt).toLocaleDateString("fr-FR")}
                    </span>
                  </div>
                  {cert.finalScore !== null && cert.finalScore !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#6B6865]">Score final</span>
                      <span className="text-xs font-semibold text-[#2E7D6F]">
                        {cert.finalScore}/100
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-[#2E7D6F]">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-xs font-medium">Vérifié</span>
                  </div>
                  <Link
                    to={`/cours/${cert.course?.id}`}
                    className="flex items-center gap-1 text-sm text-[#D4A853] hover:underline"
                  >
                    Voir le cours
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 card-warm">
          <Award className="w-12 h-12 text-[#E0DCD7] mx-auto mb-4" />
          <h3 className="font-serif text-xl text-[#1A1A1A] mb-2">
            Aucun certificat pour le moment
          </h3>
          <p className="text-[#6B6865] mb-6 max-w-md mx-auto">
            Complétez un cours pour obtenir votre premier certificat de réussite.
          </p>
          <Link to="/cours" className="btn-gold">
            Explorer les cours
          </Link>
        </div>
      )}
    </div>
  );
}
