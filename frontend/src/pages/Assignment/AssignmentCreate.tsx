import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { Button, Card, DatePicker, Form, Input, Select, Space, Tag, Typography, message } from 'antd';
import dayjs from 'dayjs';
import * as assignmentsApi from '../../api/assignments';
import * as coursesApi from '../../api/courses';
import * as problemsApi from '../../api/problems';
import type { Course, Problem } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

export default function AssignmentCreate() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [course, setCourse] = useState<Course | null>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseId = searchParams.get('courseId') || '';
  const [form] = Form.useForm();
  const isEdit = !!id;

  useEffect(() => {
    if (isEdit && id) {
      // Edit mode: load existing assignment
      assignmentsApi.getAssignment(id)
        .then(async (res) => {
          const a = res.data;
          // Fetch course
          const courseRes = await coursesApi.getCourse(a.course_id);
          setCourse(courseRes.data);
          // Fetch problems matching course languages
          const langs = courseRes.data.languages;
          const probRes = await problemsApi.getProblems({
            page: 1,
            page_size: 100,
            languages: langs.join(','),
          });
          setProblems(probRes.data.items);

          // Pre-fill form
          form.setFieldsValue({
            title: a.title,
            description: a.description,
            time_range: [dayjs(a.start_time), dayjs(a.end_time)],
            problem_ids: a.problems?.map((p) => p.problem_id) || [],
          });
        })
        .catch(() => message.error('获取作业信息失败'));
    } else if (courseId) {
      // Create mode: load course and problems
      coursesApi.getCourse(courseId)
        .then((res) => {
          setCourse(res.data);
          const langs = res.data.languages;
          return problemsApi.getProblems({
            page: 1,
            page_size: 100,
            languages: langs.join(','),
          });
        })
        .then((res) => setProblems(res.data.items))
        .catch(() => message.error('获取题目列表失败'));
    }
  }, [courseId, id]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const [start, end] = values.time_range;
      if (isEdit && id) {
        await assignmentsApi.updateAssignment(id, {
          title: values.title,
          description: values.description,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          problem_ids: values.problem_ids,
        });
        message.success('作业已更新');
        navigate(`/assignments/${id}`);
      } else {
        await assignmentsApi.createAssignment({
          course_id: courseId,
          title: values.title,
          description: values.description,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          problem_ids: values.problem_ids,
        });
        message.success('作业发布成功');
        navigate(`/courses/${courseId}`);
      }
    } catch (err: any) {
      message.error(err?.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const backPath = isEdit
    ? `/assignments/${id}`
    : courseId ? `/courses/${courseId}` : '/courses';

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>{isEdit ? '编辑作业' : '发布作业'}</Title>
      <BackButton path={backPath} />
      <Card style={{ maxWidth: 700 }}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="作业标题" rules={[{ required: true }]}>
            <Input placeholder="如: 第一次编程作业" />
          </Form.Item>
          <Form.Item name="description" label="作业说明">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="time_range" label="起止时间" rules={[{ required: true }]}>
            <RangePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          {course && (
            <div style={{ marginBottom: 8, fontSize: 13, color: '#595959' }}>
              课程语言: {course.languages.map((l) => <Tag key={l} style={{ marginRight: 4 }}>{l}</Tag>)}
              — 仅显示支持该语言的题目
            </div>
          )}
          <Form.Item name="problem_ids" label="选择题目" rules={[{ required: true, message: '至少选择一道题目' }]}>
            <Select
              mode="multiple"
              placeholder="选择题目"
              options={problems.map((p) => ({ label: `${p.title} (${p.difficulty})`, value: p.id }))}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {isEdit ? '保存' : '发布'}
              </Button>
              <Button onClick={() => navigate(backPath)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
