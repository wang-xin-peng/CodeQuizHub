import { createBrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import AppLayout from '../components/Layout/AppLayout';
import Login from '../pages/Auth/Login';
import Register from '../pages/Auth/Register';
import Dashboard from '../pages/Dashboard/Dashboard';
import CourseList from '../pages/Course/CourseList';
import CourseDetail from '../pages/Course/CourseDetail';
import CourseCreate from '../pages/Course/CourseCreate';
import ProblemList from '../pages/Problem/ProblemList';
import ProblemCreate from '../pages/Problem/ProblemCreate';
import ProblemSolve from '../pages/Problem/ProblemSolve';
import AssignmentDetail from '../pages/Assignment/AssignmentDetail';
import AssignmentCreate from '../pages/Assignment/AssignmentCreate';
import GradeOverview from '../pages/Grade/GradeOverview';
import AdminUsers from '../pages/Admin/AdminUsers';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <Dashboard /> },
          { path: '/dashboard', element: <Dashboard /> },
          { path: '/courses', element: <CourseList /> },
          { path: '/courses/create', element: <CourseCreate /> },
          { path: '/courses/:id', element: <CourseDetail /> },
          { path: '/problems', element: <ProblemList /> },
          { path: '/problems/create', element: <ProblemCreate /> },
          { path: '/assignments/create', element: <AssignmentCreate /> },
          { path: '/assignments/:id', element: <AssignmentDetail /> },
          { path: '/grades/:courseId', element: <GradeOverview /> },
        ],
      },
      {
        // Full-page layout for problem solving (no sidebar)
        path: '/solve/:assignmentId/:problemId',
        element: <ProblemSolve />,
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={['admin']} />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/admin/users', element: <AdminUsers /> },
        ],
      },
    ],
  },
]);
