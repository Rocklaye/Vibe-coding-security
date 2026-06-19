import { z } from "zod";
import { createRouter, publicQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { courses, modules, lessons, enrollments, users } from "@db/schema";
import { eq, desc, like, and, sql } from "drizzle-orm";

export const courseRouter = createRouter({
  list: publicQuery.query(async () => {
    const db = getDb();
    const allCourses = await db
      .select({
        id: courses.id,
        title: courses.title,
        description: courses.description,
        image: courses.image,
        category: courses.category,
        level: courses.level,
        duration: courses.duration,
        isPublished: courses.isPublished,
        createdAt: courses.createdAt,
        instructor: {
          id: users.id,
          name: users.name,
        },
      })
      .from(courses)
      .leftJoin(users, eq(courses.instructorId, users.id))
      .where(eq(courses.isPublished, true))
      .orderBy(desc(courses.createdAt));

    // Get enrollment counts
    const counts = await db
      .select({
        courseId: enrollments.courseId,
        count: sql<number>`count(*)`,
      })
      .from(enrollments)
      .groupBy(enrollments.courseId);

    const countMap = new Map(counts.map((c) => [c.courseId, c.count]));

    return allCourses.map((c) => ({
      ...c,
      enrollmentCount: countMap.get(c.id) || 0,
    }));
  }),

  search: publicQuery
    .input(z.object({ query: z.string().optional(), category: z.string().optional() }))
    .query(async ({ input }) => {
      const db = getDb();
      const conditions = [eq(courses.isPublished, true)];
      if (input.query) {
        conditions.push(like(courses.title, `%${input.query}%`));
      }
      if (input.category) {
        conditions.push(eq(courses.category, input.category));
      }
      return db
        .select({
          id: courses.id,
          title: courses.title,
          description: courses.description,
          image: courses.image,
          category: courses.category,
          level: courses.level,
          duration: courses.duration,
          createdAt: courses.createdAt,
          instructor: {
            id: users.id,
            name: users.name,
          },
        })
        .from(courses)
        .leftJoin(users, eq(courses.instructorId, users.id))
        .where(and(...conditions))
        .orderBy(desc(courses.createdAt));
    }),

  getById: publicQuery
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const [course] = await db
        .select()
        .from(courses)
        .where(eq(courses.id, input.id));
      if (!course) return null;

      const instructor = await db
        .select()
        .from(users)
        .where(eq(users.id, course.instructorId));

      const courseModules = await db
        .select()
        .from(modules)
        .where(eq(modules.courseId, input.id))
        .orderBy(modules.order);

      const moduleLessons = await Promise.all(
        courseModules.map(async (mod) => {
          const modLessons = await db
            .select()
            .from(lessons)
            .where(eq(lessons.moduleId, mod.id))
            .orderBy(lessons.order);
          return { ...mod, lessons: modLessons };
        })
      );

      const enrollmentCount = await db
        .select({ count: sql<number>`count(*)` })
        .from(enrollments)
        .where(eq(enrollments.courseId, input.id));

      return {
        ...course,
        instructor: instructor[0] || null,
        modules: moduleLessons,
        enrollmentCount: enrollmentCount[0]?.count || 0,
      };
    }),

  create: adminQuery
    .input(
      z.object({
        title: z.string().min(1),
        description: z.string().optional(),
        image: z.string().optional(),
        category: z.string().optional(),
        level: z.enum(["debutant", "intermediaire", "avance"]).default("debutant"),
        duration: z.string().optional(),
      })
    )
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      const [course] = await db.insert(courses).values({
        ...input,
        instructorId: ctx.user.id,
        isPublished: true,
      });
      return course;
    }),

  update: adminQuery
    .input(
      z.object({
        id: z.number(),
        title: z.string().min(1).optional(),
        description: z.string().optional(),
        image: z.string().optional(),
        category: z.string().optional(),
        level: z.enum(["debutant", "intermediaire", "avance"]).optional(),
        duration: z.string().optional(),
        isPublished: z.boolean().optional(),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const { id, ...data } = input;
      await db.update(courses).set(data).where(eq(courses.id, id));
      return { success: true };
    }),

  delete: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(courses).where(eq(courses.id, input.id));
      return { success: true };
    }),
});
