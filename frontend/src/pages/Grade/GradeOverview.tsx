import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Col, Row, Spin, Statistic, Table, Typography, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import * as gradesApi from '../../api/grades';
import BackButton from '../../components/BackButton/BackButton';

const { Title } = Typography;

const DISTRIBUTION_COLORS = ['#52c41a', '#73d13d', '#fadb14', '#fa8c16', '#ff4d4f'];
const PIE_COLORS = ['#52c41a', '#ff4d4f'];

export default function GradeOverview() {
  const { courseId } = useParams<{ courseId: string }>();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!courseId) return;
    gradesApi.getCourseGrades(courseId)
      .then((res) => setData(res.data))
      .catch((err) => message.error(err?.message || '加载失败'))
      .finally(() => setLoading(false));
  }, [courseId]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!data) return <div className="empty-state">无数据</div>;

  // ── Chart data preparation ──
  const assignmentPassRateData = (data.assignment_pass_rates || []).map((a: any) => ({
    name: a.assignment_title?.length > 10 ? a.assignment_title.slice(0, 10) + '..' : a.assignment_title || '未知',
    通过率: Math.round(a.pass_rate * 100) / 100,
    平均分: Math.round(a.avg_score * 100) / 100,
    fullTitle: a.assignment_title,
  }));

  const scoreDistribution = (() => {
    const buckets = [0, 0, 0, 0, 0];
    const labels = ['0-59', '60-69', '70-79', '80-89', '90-100'];
    (data.grades || []).forEach((g: any) => {
      const s = g.total_score || 0;
      if (s < 60) buckets[0]++;
      else if (s < 70) buckets[1]++;
      else if (s < 80) buckets[2]++;
      else if (s < 90) buckets[3]++;
      else buckets[4]++;
    });
    return labels.map((label, i) => ({ name: label, 人数: buckets[i] }));
  })();

  const passCount = (data.grades || []).filter((g: any) => (g.total_score || 0) >= 60).length;
  const failCount = (data.grades || []).length - passCount;
  const passFailPieData = [
    { name: '及格 (>=60)', value: passCount },
    { name: '不及格 (<60)', value: failCount },
  ].filter(d => d.value > 0);

  const handleExport = (format: 'xlsx' | 'csv') => {
    const token = localStorage.getItem('token');
    const url = gradesApi.getExportUrl(courseId!, format);
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.blob())
      .then((blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${data.course_name}_grades.${format}`;
        a.click();
      })
      .catch(() => message.error('导出失败'));
  };

  const assignmentKeys = data.grades.length > 0 ? Object.keys(data.grades[0].assignments) : [];
  const columns = [
    { title: '学号', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'nickname', key: 'nickname' },
    ...assignmentKeys.map((key) => ({
      title: data.grades[0]?.assignments[key]?.title || key,
      key,
      render: (_: any, record: any) => record.assignments[key]?.score ?? '-',
    })),
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      sorter: (a: any, b: any) => a.total_score - b.total_score,
    },
  ];

  return (
    <div>
      <BackButton path="/courses" />
      <div className="page-header">
        <Title level={4} style={{ margin: 0 }}>成绩总览 - {data.course_name}</Title>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport('xlsx')}>
          导出 Excel
        </Button>
      </div>

      {data.statistics && (
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="平均分" value={data.statistics.average} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="最高分" value={data.statistics.max} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="最低分" value={data.statistics.min} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="学生人数" value={data.statistics.student_count} />
            </Card>
          </Col>
        </Row>
      )}

      {/* ── Charts ── */}
      {(assignmentPassRateData.length > 0 || scoreDistribution.length > 0) && (
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          {assignmentPassRateData.length > 0 && (
            <Col xs={24} lg={14}>
              <Card title="作业通过率 & 平均分">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={assignmentPassRateData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(val: number) => `${val.toFixed(1)}`} />
                    <Legend />
                    <Bar dataKey="通过率" fill="#52c41a" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="平均分" fill="#1890ff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
          <Col xs={24} lg={assignmentPassRateData.length > 0 ? 10 : 24}>
            <Card title="成绩分布">
              <Row gutter={16}>
                <Col xs={24} md={scoreDistribution.some(d => d.人数 > 0) ? 14 : 24}>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={scoreDistribution}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" fontSize={12} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="人数" radius={[4, 4, 0, 0]}>
                        {scoreDistribution.map((_, idx) => (
                          <Cell key={idx} fill={DISTRIBUTION_COLORS[idx]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Col>
                {passFailPieData.length > 1 && (
                  <Col xs={24} md={10}>
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie data={passFailPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}人`}>
                          {passFailPieData.map((_, idx) => (
                            <Cell key={idx} fill={PIE_COLORS[idx]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </Col>
                )}
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      <Table dataSource={data.grades} columns={columns} rowKey="student_id" />
    </div>
  );
}
