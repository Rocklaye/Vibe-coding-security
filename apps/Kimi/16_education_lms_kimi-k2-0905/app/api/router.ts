import { authRouter } from "./auth-router";
import { createRouter, publicQuery } from "./middleware";
import { courseRouter } from "./routers/course-router";
import { moduleRouter } from "./routers/module-router";
import { lessonRouter } from "./routers/lesson-router";
import { enrollmentRouter } from "./routers/enrollment-router";
import { assignmentRouter } from "./routers/assignment-router";
import { submissionRouter } from "./routers/submission-router";
import { certificateRouter } from "./routers/certificate-router";
import { forumRouter } from "./routers/forum-router";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  auth: authRouter,
  course: courseRouter,
  module: moduleRouter,
  lesson: lessonRouter,
  enrollment: enrollmentRouter,
  assignment: assignmentRouter,
  submission: submissionRouter,
  certificate: certificateRouter,
  forum: forumRouter,
});

export type AppRouter = typeof appRouter;
