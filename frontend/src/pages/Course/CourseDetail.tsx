import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Descriptions, Table, Tabs, Tag, Typography, message, Popconfirm } from 'antd';
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

  const handlePublish = async (assignmentId: string) => {
    try {
      await assignmentsApi.updateAssignment(assignmentId, { status: 'published' });
      message.success('作业已发布');
      setAssignments((prev) =>
        prev.map((a) => (a.id === assignmentId ? { ...a, status: 'published' } : a))
      );
    } catch (err: any) {
      message.error(err?.message || '发布失败');
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
        const colors: Record<string, string> = { draft: 'default', published: 'success', closed: 'error' };
        const labels: Record<string, string> = { draft: '草稿', published: '进行中', closed: '已关闭' };
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
          {isTeacher && record.status === 'draft' && (
            <Button type="link" style={{ color: 'green' }} onClick={() => handlePublish(record.id)}>发布</Button>
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

      <Card style={{ marginBottom: 24 }}>
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
            <Tag color={course.status === 'active' ? 'success' : 'default'}>
              {course.status === 'active' ? '进行中' : '已归档'}
            </Tag>
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
