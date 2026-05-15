import { useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Descriptions } from 'antd';
import { useAuthStore } from '../../store/authStore';
import * as authApi from '../../api/auth';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function Profile() {
  const { user, setUser } = useAuthStore();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleEdit = () => {
    form.setFieldsValue({
      nickname: user?.nickname || '',
      avatar_url: user?.avatar_url || '',
    });
    setEditing(true);
  };

  const handleSave = async (values: { nickname: string; avatar_url: string }) => {
    setLoading(true);
    try {
      const res = await authApi.updateProfile({
        nickname: values.nickname || undefined,
        avatar_url: values.avatar_url || undefined,
      });
      setUser(res.data);
      message.success('个人信息更新成功');
      setEditing(false);
    } catch (err: any) {
      message.error(err?.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <Title level={4} style={{ marginBottom: 24 }}>个人信息</Title>
      <BackButton path="/" />
      <Card>
        {!editing ? (
          <>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="用户名">
                <Text>{user?.username}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="邮箱">
                <Text>{user?.email}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="角色">
                <Text>
                  {user?.role === 'admin'
                    ? '管理员'
                    : user?.role === 'teacher'
                      ? '教师'
                      : '学生'}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="昵称">
                <Text>{user?.nickname || <Text type="secondary">未设置</Text>}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="头像链接">
                <Text>{user?.avatar_url || <Text type="secondary">未设置</Text>}</Text>
              </Descriptions.Item>
            </Descriptions>
            <div style={{ marginTop: 16 }}>
              <Button type="primary" onClick={handleEdit}>编辑信息</Button>
            </div>
          </>
        ) : (
          <Form form={form} layout="vertical" onFinish={handleSave}>
            <Form.Item label="昵称" name="nickname">
              <Input placeholder="输入昵称" maxLength={100} />
            </Form.Item>
            <Form.Item label="头像链接" name="avatar_url">
              <Input placeholder="输入头像 URL" maxLength={500} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} style={{ marginRight: 8 }}>
                保存
              </Button>
              <Button onClick={() => setEditing(false)}>取消</Button>
            </Form.Item>
          </Form>
        )}
      </Card>
    </div>
  );
}
