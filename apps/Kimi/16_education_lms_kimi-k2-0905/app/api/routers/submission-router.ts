import { z } from "zod";
import { createRouter, authedQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { submissions } from "@db/schema";
import { eq, and, desc } from "drizzle-orm";

export const submissionRouter = createRouter({
  create: authedQuery
    .input(
      z.object({
        assignmentId: z.number(),
        content: z.string().optional(),
        fileUrl: z.string().optional(),
      })
    )
    .mutation(async ({ input, ctx }) => {
      const db = getDb();

      // Check if already submitted
      const existing = await db
        .select()
        .from(submissions)
        .where(
          and(
            eq(submissions.assignmentId, input.assignmentId),
            eq(submissions.userId, ctx.user.id)
          )
        );

      if (existing.length > 0) {
        // Update existing submission
        await db
          .update(submissions)
          .set({
            content: input.content,
            fileUrl: input.fileUrl,
            status: "submitted",
            submittedAt: new Date(),
          })
          .where(eq(submissions.id, existing[0].id));
        return { success: true, id: existing[0].id };
      }

      const [submission] = await db.insert(submissions).values({
        assignmentId: input.assignmentId,
        userId: ctx.user.id,
        content: input.content,
        fileUrl: input.fileUrl,
        status: "submitted",
      });

      return { success: true, id: submission.insertId };
    }),

  mySubmissions: authedQuery.query(async ({ ctx }) => {
    const db = getDb();
    return db
      .select()
      .from(submissions)
      .where(eq(submissions.userId, ctx.user.id))
      .orderBy(desc(submissions.submittedAt));
  }),

  getByAssignment: authedQuery
    .input(z.object({ assignmentId: z.number() }))
    .query(async ({ input, ctx }) => {
      const db = getDb();
      const [submission] = await db
        .select()
        .from(submissions)
        .where(
          and(
            eq(submissions.assignmentId, input.assignmentId),
            eq(submissions.userId, ctx.user.id)
          )
        );
      return submission || null;
    }),
});
