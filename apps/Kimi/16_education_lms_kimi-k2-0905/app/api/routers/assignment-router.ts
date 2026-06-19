import { z } from "zod";
import { createRouter, publicQuery, authedQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { assignments, submissions, users } from "@db/schema";
import { eq, and } from "drizzle-orm";

export const assignmentRouter = createRouter({
  listByCourse: publicQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      return db
        .select()
        .from(assignments)
        .where(eq(assignments.courseId, input.courseId));
    }),

  getById: publicQuery
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const [assignment] = await db
        .select()
        .from(assignments)
        .where(eq(assignments.id, input.id));
      return assignment || null;
    }),

  create: adminQuery
    .input(
      z.object({
        courseId: z.number(),
        moduleId: z.number().optional(),
        title: z.string().min(1),
        description: z.string().optional(),
        dueDate: z.string().optional(),
        maxScore: z.number().default(100),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const dueDate = input.dueDate ? new Date(input.dueDate) : null;
      const [assignment] = await db.insert(assignments).values({
        ...input,
        dueDate,
      });
      return assignment;
    }),

  delete: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(assignments).where(eq(assignments.id, input.id));
      return { success: true };
    }),

  // Get my submissions for assignments in a course
  mySubmissions: authedQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ input, ctx }) => {
      const db = getDb();
      const courseAssignments = await db
        .select()
        .from(assignments)
        .where(eq(assignments.courseId, input.courseId));

      const submissionsList = await Promise.all(
        courseAssignments.map(async (assignment) => {
          const [submission] = await db
            .select()
            .from(submissions)
            .where(
              and(
                eq(submissions.assignmentId, assignment.id),
                eq(submissions.userId, ctx.user.id)
              )
            );
          return { assignment, submission: submission || null };
        })
      );

      return submissionsList;
    }),

  // Grade a submission (teacher/admin)
  gradeSubmission: adminQuery
    .input(
      z.object({
        submissionId: z.number(),
        score: z.number().min(0).max(100),
        feedback: z.string().optional(),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      await db
        .update(submissions)
        .set({
          score: input.score,
          feedback: input.feedback,
          status: "graded",
          gradedAt: new Date(),
        })
        .where(eq(submissions.id, input.submissionId));
      return { success: true };
    }),

  // Get all submissions for an assignment (teacher/admin)
  submissions: adminQuery
    .input(z.object({ assignmentId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      return db
        .select({
          id: submissions.id,
          content: submissions.content,
          fileUrl: submissions.fileUrl,
          score: submissions.score,
          feedback: submissions.feedback,
          status: submissions.status,
          submittedAt: submissions.submittedAt,
          gradedAt: submissions.gradedAt,
          user: {
            id: users.id,
            name: users.name,
            email: users.email,
          },
        })
        .from(submissions)
        .leftJoin(users, eq(submissions.userId, users.id))
        .where(eq(submissions.assignmentId, input.assignmentId));
    }),
});
