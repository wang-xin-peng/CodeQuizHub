import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Col, Row, Spin, Statistic, Table, Tag, Typography, message, Progress } from 'antd';
import * as gradesApi from '../../api/grades';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

const difficultyConfig: Record<string, { color: string; label: string }> = {
  easy: { color: 'success', label: '简单' },
  medium: { color: 'warning', label: '中等' },
  hard: { color: 'error', label: '困难' },
};

const statusConfig: Record<string, { color: string; label: string }> = {
  accepted: { color: 'success', label: 'AC' },
  wrong_answer: { color: 'error', label: 'WA' },
  time_limit_exceeded: { color: 'warning', label: 'TLE' },
  memory_limit_exceeded: { color: 'warning', label: 'MLE' },
  runtime_error: { color: 'error', label: 'RE' },
  compilation_error: { color: 'error', label: 'CE' },
  pending: { color: 'default', label: 'Pending' },
  judging: { color: 'processing', label: 'Judging' },
  none: { color: 'default', label: '未提交' },
};

const assignmentStatusConfig: Record<string, { color: string; label: string }> = {
  draft: { color: 'default', label: '草稿' },
  published: { color: 'processing', label: '进行中' },
  closed: { color: 'default', label: '已结束' },
};

function getDifficultyConfig(difficulty: string) {
  return difficultyConfig[difficulty] || { color: 'default', label: difficulty };
}

function getStatusConfig(status: string) {
  return statusConfig[status] || { color: 'default', label: status };
}

function getAssignmentStatusConfig(status: string) {
  return assignmentStatusConfig[status] || { color: 'default', label: status };
}

export default function StudentGradeDetail() {
  const { courseId, studentId } = useParams<{ courseId: string; studentId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!courseId || !studentId) return;
    gradesApi
      .getStudentGradeDetail(courseId, studentId)
      .then((res) => setData(res.data))
      .catch((err) => message.error(err?.message || '加载失败'))
      .finally(() => setLoading(false));
  }, [courseId, studentId]);

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }
  if (!data) {
    return <div className="empty-state">无数据</div>;
  }

  const problemColumns = [
    {
      title: '题目',
      dataIndex: 'title',
      key: 'title',
      width: 200,
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 100,
      render: (difficulty: string) => {
        const cfg = getDifficultyConfig(difficulty);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const cfg = getStatusConfig(status);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '得分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      render: (score: number, record: any) => (
        <span>
          {score != null ? `${score} / ${record.max_score}` : '-'}
        </span>
      ),
    },
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      width: 180,
      render: (val: string | null) =>
        val ? new Date(val).toLocaleString() : '-',
    },
  ];

  const totalPercent =
    data.max_total_score > 0
      ? Math.round((data.total_score / data.max_total_score) * 100)
      : 0;

  return (
    <div>
      <BackButton path={`/grades/${courseId}`} />

      <div className="page-header">
        <Title level={4} style={{ margin: 0 }}>
          学生成绩详情
        </Title>
      </div>

      {/* Student Info Card */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={24} align="middle">
          <Col xs={24} sm={8}>
            <Statistic title="姓名" value={data.nickname || data.username} />
          </Col>
          <Col xs={12} sm={8}>
            <Statistic title="学号" value={data.username} />
          </Col>
          <Col xs={12} sm={8}>
            <Statistic
              title="课程"
              value={data.course_name}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
        </Row>
      </Card>

      {/* Total Score Card */}
      <Card style={{ marginBottom: 24 }}>
        <Statistic
          title="总成绩"
          value={data.total_score}
          suffix={`/ ${data.max_total_score}`}
          valueStyle={{ fontSize: 32, fontWeight: 700 }}
        />
        <Progress
          percent={totalPercent}
          status={totalPercent >= 60 ? 'success' : 'exception'}
          strokeColor={totalPercent >= 90 ? '#52c41a' : totalPercent >= 60 ? '#1890ff' : '#ff4d4f'}
          style={{ maxWidth: 400, marginTop: 8 }}
        />
      </Card>

      {/* Assignment Cards */}
      {data.assignments.map((assignment: any) => {
        const assignmentPercent =
          assignment.max_score > 0
            ? Math.round((assignment.score / assignment.max_score) * 100)
            : 0;

        return (
          <Card
            key={assignment.assignment_id}
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <Text strong style={{ fontSize: 16 }}>
                  {assignment.title}
                </Text>
                <Tag color={getAssignmentStatusConfig(assignment.status).color}>
                  {getAssignmentStatusConfig(assignment.status).label}
                </Tag>
              </div>
            }
            style={{ marginBottom: 16 }}
            extra={
              <Text>
                得分：<Text strong style={{ fontSize: 16, color: '#1890ff' }}>{assignment.score}</Text>
                {' / '}{assignment.max_score}
              </Text>
            }
          >
            <Progress
              percent={assignmentPercent}
              status={assignmentPercent >= 60 ? 'success' : 'exception'}
              strokeColor={assignmentPercent >= 90 ? '#52c41a' : assignmentPercent >= 60 ? '#1890ff' : '#ff4d4f'}
              style={{ maxWidth: 400, marginBottom: 16 }}
            />
            <Table
              dataSource={assignment.problems}
              columns={problemColumns}
              rowKey="problem_id"
              pagination={false}
              size="small"
            />
          </Card>
        );
      })}
    </div>
  );
}
