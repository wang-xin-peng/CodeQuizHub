import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, Spin, Statistic, Table, Typography, message, Row, Col } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import * as gradesApi from '../../api/grades';

const { Title } = Typography;

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
  if (!data) return <div>无数据</div>;

  const handleExport = (format: 'xlsx' | 'csv') => {
    const token = localStorage.getItem('token');
    const url = gradesApi.getExportUrl(courseId!, format);
    // Use fetch with auth header for download
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

  // Build columns dynamically from assignment data
  const assignmentKeys = data.grades.length > 0 ? Object.keys(data.grades[0].assignments) : [];
  const columns = [
    { title: '学号', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'nickname', key: 'nickname' },
    ...assignmentKeys.map((key) => ({
      title: data.grades[0]?.assignments[key]?.title || key,
      key,
      render: (_: any, record: any) => record.assignments[key]?.score ?? '-',
    })),
    { title: '总分', dataIndex: 'total_score', key: 'total_score', sorter: (a: any, b: any) => a.total_score - b.total_score },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>成绩总览 - {data.course_name}</Title>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport('xlsx')}>
          导出 Excel
        </Button>
      </div>

      {data.statistics && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}><Card><Statistic title="平均分" value={data.statistics.average} /></Card></Col>
          <Col span={6}><Card><Statistic title="最高分" value={data.statistics.max} /></Card></Col>
          <Col span={6}><Card><Statistic title="最低分" value={data.statistics.min} /></Card></Col>
          <Col span={6}><Card><Statistic title="学生人数" value={data.statistics.student_count} /></Card></Col>
        </Row>
      )}

      <Table dataSource={data.grades} columns={columns} rowKey="student_id" />
    </div>
  );
}
