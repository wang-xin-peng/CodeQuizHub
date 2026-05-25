import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Descriptions, Space, Table, Tabs, Tag, Typography, message, Popconfirm } from 'antd';
import { useAuthStore } from '../../store/authStore';
import * as coursesApi from '../../api/courses';
import * as assignmentsApi from '../../api/assignments';
import type { Assignment, Course } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function CourseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [course, setCourse] = useState<Course | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin';

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      coursesApi.getCourse(id),
      assignmentsApi.getCourseAssignments(id),
      isTeacher ? coursesApi.getCourseStudents(id) : Promise.resolve(null),
    ])
      .then(([courseRes, assignRes, studentsRes]) => {
        setCourse(courseRes.data);
        setAssignments(assignRes.data.items);
        if (studentsRes) setStudents(studentsRes.data.items);
      })
      .catch((err) => message.error(err?.message || '加载失败'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRemoveStudent = async (studentId: string) => {
    if (!id) return;
    try {
      await coursesApi.removeStudent(id, studentId);
      message.success('已移除学生');
      const res = await coursesApi.getCourseStudents(id);
      setStudents(res.data.items);
    } catch (err: any) {
      message.error(err?.message || '操作失败');
    }
  };

  const handleCloseCourse = async () => {
    if (!id) return;
    try {
      await coursesApi.updateCourse(id, { status: 'archived' });
      message.success('课程已关闭');
      // Refresh course data
      const res = await coursesApi.getCourse(id);
      setCourse(res.data);
    } catch (err: any) {
      message.error(err?.message || '关闭失败');
    }
  };

  const handleDeleteCourse = async () => {
    if (!id) return;
    try {
      await coursesApi.deleteCourse(id);
      message.success('课程已删除');
      navigate('/courses');
    } catch (err: any) {
      message.error(err?.message || '删除失败');
    }
  };

  const handlePublish = async (assignmentId: string) => {
    try {
      const res = await assignmentsApi.updateAssignment(assignmentId, { status: 'published' });
      message.success('作业已发布');
      setAssignments((prev) =>
        prev.map((a) => (a.id === assignmentId ? { ...a, status: res.data.status } : a))
      );
    } catch (err: any) {
      message.error(err?.message || '发布失败');
    }
  };

  const handleDeleteAssignment = async (assignmentId: string) => {
    try {
      await assignmentsApi.deleteAssignment(assignmentId);
      message.success('作业已删除');
      setAssignments((prev) => prev.filter((a) => a.id !== assignmentId));
    } catch (err: any) {
      message.error(err?.message || '删除失败');
    }
  };

  if (!course) return null;

  const assignmentColumns = [
    { title: '作业名称', dataIndex: 'title', key: 'title' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = { draft: 'default', not_started: 'processing', ongoing: 'success', closed: 'error' };
        const labels: Record<string, string> = { draft: '草稿', not_started: '未开始', ongoing: '进行中', closed: '已关闭' };
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>;
      },
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '截止时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Assignment) => (
        <span>
          <Button type="link" onClick={() => navigate(`/assignments/${record.id}`)}>查看</Button>
          {isTeacher && (
            <Button type="link" onClick={() => navigate(`/assignments/${record.id}/edit`)}>编辑</Button>
          )}
          {isTeacher && record.status === 'draft' && (
            <Button type="link" style={{ color: 'green' }} onClick={() => handlePublish(record.id)}>发布</Button>
          )}
          {isTeacher && (
            <Popconfirm title="确定删除此作业？此操作不可恢复。" onConfirm={() => handleDeleteAssignment(record.id)}>
              <Button type="link" danger>删除</Button>
            </Popconfirm>
          )}
        </span>
      ),
    },
  ];

  const studentColumns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '昵称', dataIndex: 'nickname', key: 'nickname' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Popconfirm title="确认移除?" onConfirm={() => handleRemoveStudent(record.id)}>
          <Button type="link" danger>移除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <BackButton path="/courses" />
      <Title level={4} style={{ marginBottom: 24 }}>{course.name}</Title>

      <Card
        style={{ marginBottom: 24 }}
        extra={isTeacher && (
          <Space>
            {course.status === 'active' && (
              <Popconfirm title="关闭后学生将无法加入，确定关闭？" onConfirm={handleCloseCourse}>
                <Button danger>关闭课程</Button>
              </Popconfirm>
            )}
            <Popconfirm title="确定删除课程？此操作不可恢复，所有关联数据将被清空。" onConfirm={handleDeleteCourse}>
              <Button type="primary" danger>删除课程</Button>
            </Popconfirm>
          </Space>
        )}
      >
        <Descriptions column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="描述">
            {course.description || <Text type="secondary">无</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="语言">
            {course.languages.map((l) => <Tag key={l}>{l}</Tag>)}
          </Descriptions.Item>
          <Descriptions.Item label="邀请码">
            <code>{course.invite_code}</code>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={course.status === 'active' ? 'success' : 'warning'}>
              {course.status === 'active' ? '进行中' : '已关闭'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建老师">
            {course.teacher_name || <Text type="secondary">未知</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs
        items={[
          {
            key: 'assignments',
            label: '作业列表',
            children: (
              <>
                {isTeacher && (
                  <Button
                    type="primary"
                    style={{ marginBottom: 16 }}
                    onClick={() => navigate(`/assignments/create?courseId=${id}`)}
                  >
                    发布作业
                  </Button>
                )}
                <Table dataSource={assignments} columns={assignmentColumns} rowKey="id" loading={loading} />
              </>
            ),
          },
          ...(isTeacher
            ? [
                {
                  key: 'students',
                  label: `学生列表 (${students.length})`,
                  children: <Table dataSource={students} columns={studentColumns} rowKey="id" />,
                },
                {
                  key: 'grades',
                  label: '成绩总览',
                  children: (
                    <Button type="primary" onClick={() => navigate(`/grades/${id}`)}>
                      查看成绩
                    </Button>
                  ),
                },
              ]
            : []),
        ]}
      />
    </div>
  );
}
