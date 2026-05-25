import { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { Spin } from 'antd';
import { ProtectedRoute } from './ProtectedRoute';
import AppLayout from '../components/Layout/AppLayout';

// Code-split each page with React.lazy
const Login = lazy(() => import('../pages/Auth/Login'));
const Register = lazy(() => import('../pages/Auth/Register'));
const Dashboard = lazy(() => import('../pages/Dashboard/Dashboard'));
const CourseList = lazy(() => import('../pages/Course/CourseList'));
const CourseDetail = lazy(() => import('../pages/Course/CourseDetail'));
const CourseCreate = lazy(() => import('../pages/Course/CourseCreate'));
const ProblemList = lazy(() => import('../pages/Problem/ProblemList'));
const ProblemDetail = lazy(() => import('../pages/Problem/ProblemDetail'));
const ProblemCreate = lazy(() => import('../pages/Problem/ProblemCreate'));
const ProblemEdit = lazy(() => import('../pages/Problem/ProblemEdit'));
const ProblemSolve = lazy(() => import('../pages/Problem/ProblemSolve'));
const AssignmentDetail = lazy(() => import('../pages/Assignment/AssignmentDetail'));
const AssignmentCreate = lazy(() => import('../pages/Assignment/AssignmentCreate'));
const GradeOverview = lazy(() => import('../pages/Grade/GradeOverview'));
const GradesList = lazy(() => import('../pages/Grade/GradesList'));
const StudentGradeDetail = lazy(() => import('../pages/Grade/StudentGradeDetail'));
const AdminUsers = lazy(() => import('../pages/Admin/AdminUsers'));
const Profile = lazy(() => import('../pages/Profile/Profile'));
const ChangePassword = lazy(() => import('../pages/Profile/ChangePassword'));
const SubmissionHistory = lazy(() => import('../pages/Submission/SubmissionHistory'));
const SubmissionResult = lazy(() => import('../pages/Submission/SubmissionResult'));

const PageLoading = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
    <Spin size="large" />
  </div>
);

const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<PageLoading />}>{children}</Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <SuspenseWrapper><Login /></SuspenseWrapper>,
  },
  {
    path: '/register',
    element: <SuspenseWrapper><Register /></SuspenseWrapper>,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <SuspenseWrapper><Dashboard /></SuspenseWrapper> },
          { path: '/dashboard', element: <SuspenseWrapper><Dashboard /></SuspenseWrapper> },
          { path: '/profile', element: <SuspenseWrapper><Profile /></SuspenseWrapper> },
          { path: '/profile/password', element: <SuspenseWrapper><ChangePassword /></SuspenseWrapper> },
          { path: '/courses', element: <SuspenseWrapper><CourseList /></SuspenseWrapper> },
          { path: '/courses/create', element: <SuspenseWrapper><CourseCreate /></SuspenseWrapper> },
          { path: '/courses/:id', element: <SuspenseWrapper><CourseDetail /></SuspenseWrapper> },
          { path: '/problems', element: <SuspenseWrapper><ProblemList /></SuspenseWrapper> },
          { path: '/problems/create', element: <SuspenseWrapper><ProblemCreate /></SuspenseWrapper> },
          { path: '/problems/:id', element: <SuspenseWrapper><ProblemDetail /></SuspenseWrapper> },
          { path: '/problems/:id/edit', element: <SuspenseWrapper><ProblemEdit /></SuspenseWrapper> },
          { path: '/assignments/create', element: <SuspenseWrapper><AssignmentCreate /></SuspenseWrapper> },
          { path: '/assignments/:id/edit', element: <SuspenseWrapper><AssignmentCreate /></SuspenseWrapper> },
          { path: '/assignments/:id', element: <SuspenseWrapper><AssignmentDetail /></SuspenseWrapper> },
          { path: '/grades', element: <SuspenseWrapper><GradesList /></SuspenseWrapper> },
          { path: '/grades/:courseId', element: <SuspenseWrapper><GradeOverview /></SuspenseWrapper> },
          { path: '/grades/:courseId/students/:studentId', element: <SuspenseWrapper><StudentGradeDetail /></SuspenseWrapper> },
          { path: '/submissions/:assignmentId', element: <SuspenseWrapper><SubmissionHistory /></SuspenseWrapper> },
          { path: '/submissions/:assignmentId/:problemId', element: <SuspenseWrapper><SubmissionHistory /></SuspenseWrapper> },
        ],
      },
      {
        path: '/solve/:assignmentId/:problemId',
        element: <SuspenseWrapper><ProblemSolve /></SuspenseWrapper>,
      },
      {
        path: '/solve/:assignmentId/:problemId/submission/:submissionId',
        element: <SuspenseWrapper><SubmissionResult /></SuspenseWrapper>,
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={['admin']} />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/admin/users', element: <SuspenseWrapper><AdminUsers /></SuspenseWrapper> },
        ],
      },
    ],
  },
]);
