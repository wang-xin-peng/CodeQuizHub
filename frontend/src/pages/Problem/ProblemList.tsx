import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Select, Space, Table, Tag, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import * as problemsApi from '../../api/problems';
import type { Problem } from '../../types';

const { Title } = Typography;

export default function ProblemList() {
  const navigate = useNavigate();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{ difficulty?: string; language?: string }>({});

  const fetchProblems = async (p = page) => {
    setLoading(true);
    try {
      const res = await problemsApi.getProblems({ page: p, page_size: 20, ...filters });
      setProblems(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      message.error(err?.message || '获取题目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [page, filters]);

  const difficultyColors: Record<string, string> = { easy: 'green', medium: 'warning', hard: 'red' };
  const difficultyLabels: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      render: (d: string) => <Tag color={difficultyColors[d]}>{difficultyLabels[d]}</Tag>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => tags?.map((t) => <Tag key={t}>{t}</Tag>),
    },
    {
      title: '时间限制',
      dataIndex: 'time_limit',
      key: 'time_limit',
      render: (v: number) => `${v}ms`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Problem) => (
        <Space>
          <Button type="link" onClick={() => navigate(`/problems/${record.id}`)}>详情</Button>
          <Button type="link" onClick={() => navigate(`/problems/${record.id}/edit`)}>编辑</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={4} style={{ margin: 0 }}>题目管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/problems/create')}>
          创建题目
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder="难度筛选"
          style={{ width: 120 }}
          onChange={(v) => setFilters((f) => ({ ...f, difficulty: v }))}
          options={[
            { label: '简单', value: 'easy' },
            { label: '中等', value: 'medium' },
            { label: '困难', value: 'hard' },
          ]}
        />
        <Select
          allowClear
          placeholder="语言筛选"
          style={{ width: 120 }}
          onChange={(v) => setFilters((f) => ({ ...f, language: v }))}
          options={[
            { label: 'Python', value: 'python' },
            { label: 'Java', value: 'java' },
            { label: 'C', value: 'c' },
            { label: 'C++', value: 'cpp' },
          ]}
        />
      </Space>

      <Table
        dataSource={problems}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />
    </div>
  );
}
