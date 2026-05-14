import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Descriptions, List, Spin, Tag, Typography, message } from 'antd';
import { useAuthStore } from '../../store/authStore';
import * as assignmentsApi from '../../api/assignments';
import * as problemsApi from '../../api/problems';
import type { Assignment, Problem } from '../../types';

const { Title } = Typography;

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
        // Load problem details
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

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!assignment) return <div>作业不存在</div>;

  const statusMap: Record<string, { color: string; label: string }> = {
    draft: { color: 'default', label: '草稿' },
    published: { color: 'green', label: '进行中' },
    closed: { color: 'red', label: '已关闭' },
  };

  const difficultyColors: Record<string, string> = { easy: 'green', medium: 'orange', hard: 'red' };

  return (
    <div>
      <Title level={4}>{assignment.title}</Title>
      <Card style={{ marginBottom: 16 }}>
        <Descriptions>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[assignment.status]?.color}>{statusMap[assignment.status]?.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">{new Date(assignment.start_time).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="截止时间">{new Date(assignment.end_time).toLocaleString()}</Descriptions.Item>
          {assignment.description && <Descriptions.Item label="说明">{assignment.description}</Descriptions.Item>}
        </Descriptions>
      </Card>

      <Title level={5}>题目列表</Title>
      <List
        dataSource={problems}
        renderItem={(problem, idx) => (
          <List.Item
            actions={[
              user?.role === 'student' && assignment.status === 'published' ? (
                <Button type="primary" onClick={() => navigate(`/solve/${id}/${problem.id}`)}>
                  做题
                </Button>
              ) : null,
            ].filter(Boolean)}
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
                  时间限制: {problem.time_limit}ms | 内存限制: {problem.memory_limit}MB
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
