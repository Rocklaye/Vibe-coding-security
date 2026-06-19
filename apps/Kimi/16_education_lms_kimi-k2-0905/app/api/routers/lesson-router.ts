import { z } from "zod";
import { createRouter, publicQuery, authedQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { lessons, lessonProgress } from "@db/schema";
import { eq, and } from "drizzle-orm";

export const lessonRouter = createRouter({
  getById: publicQuery
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const [lesson] = await db
        .select()
        .from(lessons)
        .where(eq(lessons.id, input.id));
      return lesson || null;
    }),

  listByModule: publicQuery
    .input(z.object({ moduleId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      return db
        .select()
        .from(lessons)
        .where(eq(lessons.moduleId, input.moduleId))
        .orderBy(lessons.order);
    }),

  create: adminQuery
    .input(
      z.object({
        moduleId: z.number(),
        title: z.string().min(1),
        content: z.string().optional(),
        videoUrl: z.string().optional(),
        duration: z.number().optional(),
        order: z.number().default(0),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const [lesson] = await db.insert(lessons).values(input);
      return lesson;
    }),

  update: adminQuery
    .input(
      z.object({
        id: z.number(),
        title: z.string().min(1).optional(),
        content: z.string().optional(),
        videoUrl: z.string().optional(),
        duration: z.number().optional(),
        order: z.number().optional(),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const { id, ...data } = input;
      await db.update(lessons).set(data).where(eq(lessons.id, id));
      return { success: true };
    }),

  delete: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(lessons).where(eq(lessons.id, input.id));
      return { success: true };
    }),

  markComplete: authedQuery
    .input(z.object({ lessonId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      const existing = await db
        .select()
        .from(lessonProgress)
        .where(
          and(
            eq(lessonProgress.userId, ctx.user.id),
            eq(lessonProgress.lessonId, input.lessonId)
          )
        );

      if (existing.length > 0) {
        await db
          .update(lessonProgress)
          .set({ isCompleted: true, completedAt: new Date() })
          .where(eq(lessonProgress.id, existing[0].id));
      } else {
        await db.insert(lessonProgress).values({
          userId: ctx.user.id,
          lessonId: input.lessonId,
          isCompleted: true,
          completedAt: new Date(),
        });
      }

      return { success: true };
    }),

  getProgress: authedQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ ctx }) => {
      const db = getDb();
      const progress = await db
        .select()
        .from(lessonProgress)
        .where(eq(lessonProgress.userId, ctx.user.id));
      return progress;
    }),
});
