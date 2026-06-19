import { z } from "zod";
import { createRouter, publicQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { modules, lessons } from "@db/schema";
import { eq, asc } from "drizzle-orm";

export const moduleRouter = createRouter({
  listByCourse: publicQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const courseModules = await db
        .select()
        .from(modules)
        .where(eq(modules.courseId, input.courseId))
        .orderBy(asc(modules.order));

      const modulesWithLessons = await Promise.all(
        courseModules.map(async (mod) => {
          const modLessons = await db
            .select()
            .from(lessons)
            .where(eq(lessons.moduleId, mod.id))
            .orderBy(asc(lessons.order));
          return { ...mod, lessons: modLessons };
        })
      );

      return modulesWithLessons;
    }),

  create: adminQuery
    .input(
      z.object({
        courseId: z.number(),
        title: z.string().min(1),
        description: z.string().optional(),
        order: z.number().default(0),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const [module] = await db.insert(modules).values(input);
      return module;
    }),

  update: adminQuery
    .input(
      z.object({
        id: z.number(),
        title: z.string().min(1).optional(),
        description: z.string().optional(),
        order: z.number().optional(),
      })
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const { id, ...data } = input;
      await db.update(modules).set(data).where(eq(modules.id, id));
      return { success: true };
    }),

  delete: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(modules).where(eq(modules.id, input.id));
      return { success: true };
    }),
});
