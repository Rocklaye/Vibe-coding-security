import { z } from "zod";
import { createRouter, publicQuery, authedQuery, adminQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { forumTopics, forumReplies, users } from "@db/schema";
import { eq, desc } from "drizzle-orm";

export const forumRouter = createRouter({
  listTopics: publicQuery
    .input(z.object({ courseId: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const topics = await db
        .select({
          id: forumTopics.id,
          title: forumTopics.title,
          content: forumTopics.content,
          isPinned: forumTopics.isPinned,
          createdAt: forumTopics.createdAt,
          user: {
            id: users.id,
            name: users.name,
            avatar: users.avatar,
          },
        })
        .from(forumTopics)
        .leftJoin(users, eq(forumTopics.userId, users.id))
        .where(eq(forumTopics.courseId, input.courseId))
        .orderBy(desc(forumTopics.isPinned), desc(forumTopics.createdAt));

      return topics;
    }),

  getTopic: publicQuery
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const db = getDb();
      const [topic] = await db
        .select({
          id: forumTopics.id,
          title: forumTopics.title,
          content: forumTopics.content,
          isPinned: forumTopics.isPinned,
          createdAt: forumTopics.createdAt,
          user: {
            id: users.id,
            name: users.name,
            avatar: users.avatar,
          },
        })
        .from(forumTopics)
        .leftJoin(users, eq(forumTopics.userId, users.id))
        .where(eq(forumTopics.id, input.id));

      if (!topic) return null;

      const replies = await db
        .select({
          id: forumReplies.id,
          content: forumReplies.content,
          createdAt: forumReplies.createdAt,
          user: {
            id: users.id,
            name: users.name,
            avatar: users.avatar,
          },
        })
        .from(forumReplies)
        .leftJoin(users, eq(forumReplies.userId, users.id))
        .where(eq(forumReplies.topicId, input.id))
        .orderBy(forumReplies.createdAt);

      return { ...topic, replies };
    }),

  createTopic: authedQuery
    .input(
      z.object({
        courseId: z.number(),
        title: z.string().min(1),
        content: z.string().optional(),
      })
    )
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      const [topic] = await db.insert(forumTopics).values({
        courseId: input.courseId,
        userId: ctx.user.id,
        title: input.title,
        content: input.content,
      });
      return { success: true, id: topic.insertId };
    }),

  createReply: authedQuery
    .input(
      z.object({
        topicId: z.number(),
        content: z.string().min(1),
      })
    )
    .mutation(async ({ input, ctx }) => {
      const db = getDb();
      const [reply] = await db.insert(forumReplies).values({
        topicId: input.topicId,
        userId: ctx.user.id,
        content: input.content,
      });
      return { success: true, id: reply.insertId };
    }),

  pinTopic: adminQuery
    .input(z.object({ id: z.number(), isPinned: z.boolean() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db
        .update(forumTopics)
        .set({ isPinned: input.isPinned })
        .where(eq(forumTopics.id, input.id));
      return { success: true };
    }),

  deleteTopic: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(forumReplies).where(eq(forumReplies.topicId, input.id));
      await db.delete(forumTopics).where(eq(forumTopics.id, input.id));
      return { success: true };
    }),

  deleteReply: adminQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const db = getDb();
      await db.delete(forumReplies).where(eq(forumReplies.id, input.id));
      return { success: true };
    }),
});
