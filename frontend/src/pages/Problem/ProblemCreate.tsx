import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Form, Input, InputNumber, Select, Tabs, Typography, message, Space, Switch } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import * as problemsApi from '../../api/problems';

const { Title } = Typography;
const { TextArea } = Input;

export default function ProblemCreate() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const payload = {
        title: values.title,
        description: values.description,
        difficulty: values.difficulty,
        time_limit: values.time_limit,
        memory_limit: values.memory_limit,
        tags: values.tags || [],
        compare_mode: values.compare_mode,
        signatures: values.signatures.map((sig: any) => ({
          language: sig.language,
          function_name: sig.function_name,
          parameters: sig.parameters || [],
          return_type: sig.return_type,
          code_template: sig.code_template,
          prelude_code: sig.prelude_code || '',
          driver_template: sig.driver_template || '',
        })),
        test_cases: values.test_cases.map((tc: any) => ({
          input_params: JSON.parse(tc.input_params),
          expected_output: JSON.parse(tc.expected_output),
          is_public: tc.is_public || false,
          description: tc.description || '',
        })),
      };
      await problemsApi.createProblem(payload);
      message.success('题目创建成功');
      navigate('/problems');
    } catch (err: any) {
      message.error(err?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={4}>创建题目</Title>
      <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ difficulty: 'medium', time_limit: 1000, memory_limit: 256, compare_mode: 'exact' }}>
        <Card title="基本信息" style={{ marginBottom: 16 }}>
          <Form.Item name="title" label="题目标题" rules={[{ required: true }]}>
            <Input placeholder="如: 两数之和" />
          </Form.Item>
          <Form.Item name="description" label="题目描述 (Markdown)" rules={[{ required: true }]}>
            <TextArea rows={8} placeholder="支持 Markdown 格式" />
          </Form.Item>
          <Space>
            <Form.Item name="difficulty" label="难度">
              <Select style={{ width: 120 }} options={[{ label: '简单', value: 'easy' }, { label: '中等', value: 'medium' }, { label: '困难', value: 'hard' }]} />
            </Form.Item>
            <Form.Item name="time_limit" label="时间限制(ms)">
              <InputNumber min={100} max={30000} />
            </Form.Item>
            <Form.Item name="memory_limit" label="内存限制(MB)">
              <InputNumber min={16} max={1024} />
            </Form.Item>
            <Form.Item name="compare_mode" label="比对模式">
              <Select style={{ width: 120 }} options={[{ label: '精确', value: 'exact' }, { label: '无序', value: 'unordered' }, { label: '浮点', value: 'float' }]} />
            </Form.Item>
          </Space>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
        </Card>

        <Card title="函数签名" style={{ marginBottom: 16 }}>
          <Form.List name="signatures" initialValue={[{ language: 'python' }]}>
            {(fields, { add, remove }) => (
              <>
                <Tabs
                  type="editable-card"
                  onEdit={(_, action) => { if (action === 'add') add({ language: 'python' }); }}
                  items={fields.map((field, idx) => ({
                    key: String(idx),
                    label: form.getFieldValue(['signatures', field.name, 'language']) || `签名${idx + 1}`,
                    closable: fields.length > 1,
                    children: (
                      <div>
                        <Space style={{ marginBottom: 8 }}>
                          <Form.Item name={[field.name, 'language']} rules={[{ required: true }]} noStyle>
                            <Select style={{ width: 100 }} options={[{ label: 'Python', value: 'python' }, { label: 'Java', value: 'java' }, { label: 'C', value: 'c' }, { label: 'C++', value: 'cpp' }]} />
                          </Form.Item>
                          <Form.Item name={[field.name, 'function_name']} rules={[{ required: true }]} noStyle>
                            <Input placeholder="函数名" style={{ width: 150 }} />
                          </Form.Item>
                          <Form.Item name={[field.name, 'return_type']} rules={[{ required: true }]} noStyle>
                            <Input placeholder="返回类型" style={{ width: 150 }} />
                          </Form.Item>
                          {fields.length > 1 && <MinusCircleOutlined onClick={() => remove(field.name)} />}
                        </Space>
                        <Form.Item name={[field.name, 'code_template']} label="代码模板" rules={[{ required: true }]}>
                          <TextArea rows={6} placeholder="学生看到的初始代码" />
                        </Form.Item>
                        <Form.Item name={[field.name, 'prelude_code']} label="Prelude 代码">
                          <TextArea rows={3} placeholder="预置代码（数据结构等）" />
                        </Form.Item>
                        <Form.Item name={[field.name, 'driver_template']} label="Driver 模板">
                          <TextArea rows={4} placeholder="驱动代码模板" />
                        </Form.Item>
                        <Form.List name={[field.name, 'parameters']}>
                          {(paramFields, { add: addParam, remove: removeParam }) => (
                            <>
                              <Typography.Text strong>参数列表:</Typography.Text>
                              {paramFields.map((pf) => (
                                <Space key={pf.key} style={{ display: 'flex', marginTop: 4 }}>
                                  <Form.Item name={[pf.name, 'name']} noStyle rules={[{ required: true }]}>
                                    <Input placeholder="参数名" style={{ width: 100 }} />
                                  </Form.Item>
                                  <Form.Item name={[pf.name, 'type']} noStyle rules={[{ required: true }]}>
                                    <Input placeholder="类型" style={{ width: 120 }} />
                                  </Form.Item>
                                  <Form.Item name={[pf.name, 'description']} noStyle>
                                    <Input placeholder="说明" style={{ width: 150 }} />
                                  </Form.Item>
                                  <MinusCircleOutlined onClick={() => removeParam(pf.name)} />
                                </Space>
                              ))}
                              <Button type="dashed" onClick={() => addParam()} icon={<PlusOutlined />} style={{ marginTop: 8 }}>
                                添加参数
                              </Button>
                            </>
                          )}
                        </Form.List>
                      </div>
                    ),
                  }))}
                />
              </>
            )}
          </Form.List>
        </Card>

        <Card title="测试用例" style={{ marginBottom: 16 }}>
          <Form.List name="test_cases" initialValue={[{ is_public: true }]}>
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, idx) => (
                  <Card key={field.key} size="small" title={`用例 ${idx + 1}`} style={{ marginBottom: 8 }}
                    extra={fields.length > 1 && <MinusCircleOutlined onClick={() => remove(field.name)} />}
                  >
                    <Form.Item name={[field.name, 'input_params']} label="输入 (JSON)" rules={[{ required: true }]}>
                      <TextArea rows={2} placeholder='{"nums": [2, 7, 11, 15], "target": 9}' />
                    </Form.Item>
                    <Form.Item name={[field.name, 'expected_output']} label="期望输出 (JSON)" rules={[{ required: true }]}>
                      <TextArea rows={2} placeholder='[0, 1]' />
                    </Form.Item>
                    <Space>
                      <Form.Item name={[field.name, 'is_public']} valuePropName="checked" label="公开">
                        <Switch />
                      </Form.Item>
                      <Form.Item name={[field.name, 'description']} label="说明">
                        <Input placeholder="用例说明" />
                      </Form.Item>
                    </Space>
                  </Card>
                ))}
                <Button type="dashed" onClick={() => add({ is_public: false })} icon={<PlusOutlined />} block>
                  添加测试用例
                </Button>
              </>
            )}
          </Form.List>
        </Card>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>创建题目</Button>
            <Button onClick={() => navigate('/problems')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
}
