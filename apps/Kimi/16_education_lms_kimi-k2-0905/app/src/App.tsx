import { Routes, Route } from 'react-router'
import { Layout } from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Courses from './pages/Courses'
import CourseDetail from './pages/CourseDetail'
import Lesson from './pages/Lesson'
import Assignments from './pages/Assignments'
import Certificates from './pages/Certificates'
import Admin from './pages/Admin'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/cours" element={<Courses />} />
        <Route path="/cours/:id" element={<CourseDetail />} />
        <Route path="/cours/:courseId/lecon/:lessonId" element={<Lesson />} />
        <Route path="/devoirs" element={<Assignments />} />
        <Route path="/certificats" element={<Certificates />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  )
}
