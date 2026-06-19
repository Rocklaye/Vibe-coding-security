import { z } from "zod";
import { createRouter, authedQuery, publicQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { certificates, courses, users } from "@db/schema";
import { eq, and } from "drizzle-orm";

export const certificateRouter = createRouter({
  myCertificates: authedQuery.query(async ({ ctx }) => {
    const db = getDb();
    return db
      .select({
        id: certificates.id,
        certificateNumber: certificates.certificateNumber,
        finalScore: certificates.finalScore,
        issuedAt: certificates.issuedAt,
        course: {
          id: courses.id,
          title: courses.title,
        },
      })
      .from(certificates)
      .leftJoin(courses, eq(certificates.courseId, courses.id))
      .where(eq(certificates.userId, ctx.user.id));
  }),

  generate: authedQuery
    .input(z.object({ courseId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      const db = getDb();

      // Check if certificate already exists
      const existing = await db
        .select()
        .from(certificates)
        .where(
          and(
            eq(certificates.userId, ctx.user.id),
            eq(certificates.courseId, input.courseId)
          )
        );

      if (existing.length > 0) {
        return { success: true, certificate: existing[0], alreadyExists: true };
      }

      // Generate certificate number
      const certNumber = `AURA-${Date.now()}-${ctx.user.id}-${input.courseId}`;

      const [certificate] = await db.insert(certificates).values({
        userId: ctx.user.id,
        courseId: input.courseId,
        certificateNumber: certNumber,
      });

      return { success: true, certificate: { insertId: certificate.insertId, certificateNumber: certNumber }, alreadyExists: false };
    }),

  verify: publicQuery
    .input(z.object({ certificateNumber: z.string() }))
    .query(async ({ input }) => {
      const db = getDb();
      const [cert] = await db
        .select({
          id: certificates.id,
          certificateNumber: certificates.certificateNumber,
          finalScore: certificates.finalScore,
          issuedAt: certificates.issuedAt,
          course: {
            id: courses.id,
            title: courses.title,
          },
          user: {
            id: users.id,
            name: users.name,
          },
        })
        .from(certificates)
        .leftJoin(courses, eq(certificates.courseId, courses.id))
        .leftJoin(users, eq(certificates.userId, users.id))
        .where(eq(certificates.certificateNumber, input.certificateNumber));

      return cert || null;
    }),
});
