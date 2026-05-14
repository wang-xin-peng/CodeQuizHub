import { useEffect, useState } from 'react';
import { Button, Select, Table, Tag, Typography, message, Popconfirm } from 'antd';
import client from '../../api/client';
import type { User } from '../../types';

const { Title } = Typography;

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res: any = await client.get('/users/admin/list', { params: { page, page_size: 20 } });
      setUsers(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      message.error(err?.message || '获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page]);

  const handleToggleStatus = async (userId: string, currentActive: boolean) => {
    try {
      await client.put(`/users/admin/${userId}/status`, null, { params: { is_active: !currentActive } });
      message.success('操作成功');
      fetchUsers();
    } catch (err: any) {
      message.error(err?.message || '操作失败');
    }
  };

  const handleRoleChange = async (userId: string, role: string) => {
    try {
      await client.put(`/users/admin/${userId}/role`, null, { params: { role } });
      message.success('角色变更成功');
      fetchUsers();
    } catch (err: any) {
      message.error(err?.message || '操作失败');
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string, record: User) => (
        <Select
          value={role}
          style={{ width: 100 }}
          onChange={(v) => handleRoleChange(record.id, v)}
          options={[
            { label: '学生', value: 'student' },
            { label: '教师', value: 'teacher' },
            { label: '管理员', value: 'admin' },
          ]}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? '正常' : '禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Popconfirm title={`确认${record.is_active ? '禁用' : '启用'}?`} onConfirm={() => handleToggleStatus(record.id, record.is_active)}>
          <Button type="link" danger={record.is_active}>
            {record.is_active ? '禁用' : '启用'}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>用户管理</Title>
      <Table
        dataSource={users}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />
    </div>
  );
}
