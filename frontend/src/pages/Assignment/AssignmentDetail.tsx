import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Descriptions, List, Space, Spin, Tag, Typography, message } from 'antd';
import { useAuthStore } from '../../store/authStore';
import * as assignmentsApi from '../../api/assignments';
import * as problemsApi from '../../api/problems';
import type { Assignment, Problem } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function AssignmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    assignmentsApi.getAssignment(id)
      .then(async (res) => {
        const a = res.data;
        setAssignment(a);
        if (a.problems) {
          const probs = await Promise.all(
            a.problems.map((ap) => problemsApi.getProblem(ap.problem_id).then((r) => r.data))
          );
          setProblems(probs);
        }
      })
      .catch((err) => message.error(err?.message || '加载失败'))
      .finally(() => setLoading(false));
  }, [id]);

  const handlePublish = async () => {
    if (!id) return;
    try {
      await assignmentsApi.updateAssignment(id, { status: 'published' });
      message.success('作业已发布，学生现在可以查看');
      setAssignment((prev) => prev ? { ...prev, status: 'published' } : null);
    } catch (err: any) {
      message.error(err?.message || '发布失败');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!assignment) return <div className="empty-state">作业不存在</div>;

  const statusMap: Record<string, { color: string; label: string }> = {
    draft: { color: 'default', label: '草稿' },
    published: { color: 'success', label: '进行中' },
    closed: { color: 'error', label: '已关闭' },
  };

  const difficultyColors: Record<string, string> = { easy: 'green', medium: 'warning', hard: 'red' };

  return (
    <div>
      <BackButton path={assignment ? `/courses/${assignment.course_id}` : '/courses'} />
      <Title level={4} style={{ marginBottom: 24 }}>{assignment.title}</Title>

      <Card style={{ marginBottom: 24 }}
        extra={
          user?.role === 'teacher' && assignment.status === 'draft'
            ? <Button type="primary" onClick={handlePublish}>发布作业</Button>
            : null
        }
      >
        <Descriptions column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[assignment.status]?.color}>
              {statusMap[assignment.status]?.label}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {new Date(assignment.start_time).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="截止时间">
            {new Date(assignment.end_time).toLocaleString()}
          </Descriptions.Item>
          {assignment.description && (
            <Descriptions.Item label="说明">{assignment.description}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Title level={5} style={{ marginBottom: 16 }}>题目列表</Title>
      <List
        dataSource={problems}
        renderItem={(problem, idx) => (
          <List.Item
            actions={
              user?.role === 'student' && assignment.status === 'published'
                ? [
                    <Button type="primary" onClick={() => navigate(`/solve/${id}/${problem.id}`)}>
                      做题
                    </Button>,
                    <Button onClick={() => navigate(`/submissions/${id}/${problem.id}`)}>
                      提交历史
                    </Button>,
                  ]
                : []
            }
          >
            <List.Item.Meta
              title={
                <span>
                  {idx + 1}. {problem.title}{' '}
                  <Tag color={difficultyColors[problem.difficulty]}>{problem.difficulty}</Tag>
                </span>
              }
              description={
                <span>
                  <Text type="secondary">
                    时间限制: {problem.time_limit}ms | 内存限制: {problem.memory_limit}MB
                  </Text>
                  {problem.tags?.map((t) => <Tag key={t} style={{ marginLeft: 4 }}>{t}</Tag>)}
                </span>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );
}
