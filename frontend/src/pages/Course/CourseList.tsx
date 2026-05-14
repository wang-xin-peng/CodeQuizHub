import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input, List, Modal, Space, Tag, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import * as coursesApi from '../../api/courses';
import type { Course } from '../../types';

const { Title } = Typography;

export default function CourseList() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [joinModalOpen, setJoinModalOpen] = useState(false);
  const [inviteCode, setInviteCode] = useState('');

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin';

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const res = await coursesApi.getCourses({ page: 1, page_size: 100 });
      setCourses(res.data.items);
    } catch (err: any) {
      message.error(err?.message || '获取课程失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleJoin = async () => {
    if (!inviteCode.trim()) return;
    try {
      const res = await coursesApi.joinCourse(inviteCode.trim());
      message.success(`成功加入课程: ${res.data.course_name}`);
      setJoinModalOpen(false);
      setInviteCode('');
      fetchCourses();
    } catch (err: any) {
      message.error(err?.message || '加入失败');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>课程列表</Title>
        <Space>
          {!isTeacher && (
            <Button onClick={() => setJoinModalOpen(true)}>加入课程</Button>
          )}
          {isTeacher && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/courses/create')}>
              创建课程
            </Button>
          )}
        </Space>
      </div>

      <List
        loading={loading}
        grid={{ gutter: 16, column: 3 }}
        dataSource={courses}
        renderItem={(course) => (
          <List.Item>
            <Card
              hoverable
              onClick={() => navigate(`/courses/${course.id}`)}
              title={course.name}
              extra={<Tag color={course.status === 'active' ? 'green' : 'default'}>{course.status === 'active' ? '进行中' : '已归档'}</Tag>}
            >
              <p>{course.description || '暂无描述'}</p>
              <Space>
                {course.languages.map((lang) => (
                  <Tag key={lang} color="blue">{lang}</Tag>
                ))}
              </Space>
              {isTeacher && (
                <p style={{ marginTop: 8, color: '#999' }}>邀请码: {course.invite_code}</p>
              )}
            </Card>
          </List.Item>
        )}
      />

      <Modal
        title="加入课程"
        open={joinModalOpen}
        onOk={handleJoin}
        onCancel={() => setJoinModalOpen(false)}
      >
        <Input
          placeholder="请输入邀请码"
          value={inviteCode}
          onChange={(e) => setInviteCode(e.target.value)}
          maxLength={8}
        />
      </Modal>
    </div>
  );
}
