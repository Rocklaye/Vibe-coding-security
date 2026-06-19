import { z } from "zod";
import { createRouter, authedQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { enrollments, courses, users, modules, lessons, lessonProgress } from "@db/schema";
import { eq, and } from "drizzle-orm";

export const enrollmentRouter = createRouter({
  myEnrollments: authedQuery.query(async ({ ctx }) => {
    const db = getDb();
    const myEnrollments = await db
      .select({
        id: enrollments.id,
        progress: enrollments.progress,
        status: enrollments.status,
        enrolledAt: enrollments.enrolledAt,
        completedAt: enrollments.completedAt,
        course: {
          id: courses.id,
          title: courses.title,
          description: courses.description,
          image: courses.image,
          category: courses.category,
          level: courses.level,
          duration: courses.duration,
        },
      })
      .from(enrollments)
      .leftJoin(courses, eq(enrollments.courseId, courses.id))
      .where(eq(enrollments.userId, ctx.user.id));

    return myEnrollments;
  }),

  enroll: authedQuery
    .input(z.object({ courseId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      const existing = await db
        .select()
        .from(enrollments)
        .where(
          and(
            eq(enrollments.userId, ctx.user.id),
            eq(enrollments.courseId, input.courseId)
          )
        );

      if (existing.length > 0) {
        return { success: true, alreadyEnrolled: true };
      }

      await db.insert(enrollments).values({
        userId: ctx.user.id,
        courseId: input.courseId,
        progress: 0,
        status: "active",
      });

      return { success: true, alreadyEnrolled: false };
    }),

  updateProgress: authedQuery
    .input(z.object({ courseId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      const db = getDb();

      // Count total lessons in course
      const courseModules = await db
        .select()
        .from(modules)
        .where(eq(modules.courseId, input.courseId));

      let totalLessons = 0;
      const moduleLessons: Record<number, number> = {};

      for (const mod of courseModules) {
        const lessonsList = await db
          .select()
          .from(lessons)
          .where(eq(lessons.moduleId, mod.id));
        totalLessons += lessonsList.length;
        moduleLessons[mod.id] = lessonsList.length;
      }

      // Count completed lessons
      const completedLessons = await db
        .select()
        .from(lessonProgress)
        .where(
          and(
            eq(lessonProgress.userId, ctx.user.id),
            eq(lessonProgress.isCompleted, true)
          )
        );

      // Filter completed lessons that belong to this course
      const courseLessonIds = new Set<number>();
      for (const mod of courseModules) {
        const lessonsList = await db
          .select({ id: lessons.id })
          .from(lessons)
          .where(eq(lessons.moduleId, mod.id));
        lessonsList.forEach((l) => courseLessonIds.add(l.id));
      }

      const courseCompleted = completedLessons.filter((cl) =>
        courseLessonIds.has(cl.lessonId)
      );

      const progress = totalLessons > 0
        ? Math.round((courseCompleted.length / totalLessons) * 100)
        : 0;

      const isCompleted = progress >= 100;

      await db
        .update(enrollments)
        .set({
          progress,
          status: isCompleted ? "completed" : "active",
          completedAt: isCompleted ? new Date() : undefined,
        })
        .where(
          and(
            eq(enrollments.userId, ctx.user.id),
            eq(enrollments.courseId, input.courseId)
          )
        );

      return { progress, isCompleted };
    }),

  drop: authedQuery
    .input(z.object({ courseId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      await db
        .update(enrollments)
        .set({ status: "dropped" })
        .where(
          and(
            eq(enrollments.userId, ctx.user.id),
            eq(enrollments.courseId, input.courseId)
          )
        );
      return { success: true };
    }),

  // Admin: list all enrollments for a course
  listByCourse: adminQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      return db
        .select({
          id: enrollments.id,
          progress: enrollments.progress,
          status: enrollments.status,
          enrolledAt: enrollments.enrolledAt,
          completedAt: enrollments.completedAt,
          user: {
            id: users.id,
            name: users.name,
            email: users.email,
          },
        })
        .from(enrollments)
        .leftJoin(users, eq(enrollments.userId, users.id))
        .where(eq(enrollments.courseId, input.courseId));
    }),
});
