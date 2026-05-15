import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, List, Spin, Tag, Typography, message } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import * as coursesApi from '../../api/courses';
import { useAuthStore } from '../../store/authStore';
import type { Course } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function GradesList() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    coursesApi.getCourses({ page: 1, page_size: 100 })
      .then((res) => setCourses(res.data.items))
      .catch((err) => message.error(err?.message || '加载课程失败'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin';

  return (
    <div>
      <BackButton path="/" />
      <Title level={4} style={{ marginBottom: 24 }}>
        <BarChartOutlined /> 成绩管理
      </Title>

      {courses.length === 0 ? (
        <Card>
          <Text type="secondary">
            {isTeacher ? '你还没有创建课程，请先创建课程。' : '你还没有加入任何课程。'}
          </Text>
        </Card>
      ) : (
        <List
          dataSource={courses}
          renderItem={(course) => (
            <List.Item
              actions={[
                <Button
                  type="primary"
                  size="small"
                  icon={<BarChartOutlined />}
                  onClick={() => navigate(`/grades/${course.id}`)}
                >
                  查看成绩
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <span>
                    <Text strong>{course.name}</Text>
                    <Tag color={course.status === 'active' ? 'success' : 'default'} style={{ marginLeft: 8 }}>
                      {course.status === 'active' ? '进行中' : '已归档'}
                    </Tag>
                  </span>
                }
                description={course.description || '暂无描述'}
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
}
