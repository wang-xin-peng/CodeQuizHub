import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, Form, Input, InputNumber, Select, Tabs, Typography, message, Space, Spin, Switch } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as problemsApi from '../../api/problems';
import BackButton from '../../components/BackButton/BackButton';
import InputParamsEditor from '../../components/InputParamsEditor/InputParamsEditor';

const { Title } = Typography;
const { TextArea } = Input;

export default function ProblemEdit() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const watchedDescription = Form.useWatch('description', form);
  const watchedSignatures = Form.useWatch('signatures', form);
  const sigParams = watchedSignatures?.[0]?.parameters;

  // Load existing problem data
  useEffect(() => {
    if (!id) return;
    setFetching(true);
    problemsApi.getProblem(id)
      .then((res) => {
        const p = res.data;
        // Map API response back to form values
        const formValues: Record<string, any> = {
          title: p.title,
          description: p.description,
          difficulty: p.difficulty,
          time_limit: p.time_limit,
          memory_limit: p.memory_limit,
          tags: p.tags || [],
          compare_mode: p.compare_mode,
          signatures: p.signatures?.map((sig) => ({
            id: sig.id,
            language: sig.language,
            function_name: sig.function_name,
            return_type: sig.return_type,
            code_template: sig.code_template,
            prelude_code: sig.prelude_code || '',
            // @ts-ignore driver_template may exist from API
            driver_template: (sig as any).driver_template || '',
            parameters: sig.parameters_json?.map((param) => ({
              name: param.name,
              type: param.type,
              description: param.description,
            })) || [],
          })) || [{ language: 'python' }],
          test_cases: p.test_cases?.map((tc) => ({
            id: tc.id,
            input_params: JSON.stringify(tc.input_params_json, null, 2),
            expected_output: JSON.stringify(tc.expected_output_json),
            is_public: tc.is_public,
            description: tc.description || '',
          })) || [],
        };
        form.setFieldsValue(formValues);
      })
      .catch((err) => {
        message.error(err?.message || '加载题目失败');
        navigate('/problems');
      })
      .finally(() => setFetching(false));
  }, [id]);

  const onFinish = async (values: any) => {
    if (!id) return;
    setLoading(true);
    try {
      const rawSignatures = Array.isArray(values.signatures) ? values.signatures : [];
      const signaturesSafe = rawSignatures.map((sig: any) => {
        const obj = (sig && typeof sig === 'object') ? sig : {};
        const entry: Record<string, any> = {
          language: String(obj.language || ''),
          function_name: String(obj.function_name || ''),
          parameters: Array.isArray(obj.parameters) ? obj.parameters : [],
          return_type: String(obj.return_type || ''),
          code_template: String(obj.code_template || ''),
          prelude_code: String(obj.prelude_code || ''),
          driver_template: String(obj.driver_template || ''),
        };
        if (obj.id) entry.id = obj.id;
        return entry;
      });

      // Validate each signature has a language before sending
      const emptyLangIdx = signaturesSafe.findIndex(s => !s.language);
      if (emptyLangIdx !== -1) {
        // eslint-disable-next-line no-console
        console.error('[ProblemEdit] Signature with empty language detected at index', emptyLangIdx);
        message.error(`签名 #${emptyLangIdx + 1} 的编程语言不能为空，请为每个签名选择语言`);
        setLoading(false);
        return;
      }

      const rawTestCases = Array.isArray(values.test_cases) ? values.test_cases : [];
      const testCasesSafe = rawTestCases.map((tc: any) => {
        const obj = (tc && typeof tc === 'object') ? tc : {};
        const entry: Record<string, any> = {
          input_params: (() => { try { return JSON.parse(String(obj.input_params || '{}')); } catch { return {}; } })(),
          expected_output: (() => { try { return JSON.parse(String(obj.expected_output || 'null')); } catch { return null; } })(),
          is_public: !!obj.is_public,
          description: String(obj.description || ''),
        };
        if (obj.id) entry.id = obj.id;
        return entry;
      });

      const payload = {
        title: values.title,
        description: values.description,
        difficulty: values.difficulty,
        time_limit: values.time_limit,
        memory_limit: values.memory_limit,
        tags: values.tags || [],
        compare_mode: values.compare_mode,
        signatures: signaturesSafe,
        test_cases: testCasesSafe,
      };
      // eslint-disable-next-line no-console
      console.log('[ProblemEdit] Sending payload:', JSON.stringify(payload, null, 2));
      await problemsApi.updateProblem(id, payload as any);
      message.success('题目更新成功');
      navigate('/problems');
    } catch (err: any) {
      // eslint-disable-next-line no-console
      console.error('[ProblemEdit] onFinish error:', err);
      if (err && typeof err === 'object' && err.stack) {
        // eslint-disable-next-line no-console
        console.error('[ProblemEdit] stack:', err.stack);
      }
      // Format user-friendly error message
      const serverMsg = err?.response?.data?.message || err?.message || '';
      if (serverMsg.includes('at least 1 character') || serverMsg.includes('language')) {
        message.error('保存失败：存在编程语言为空的签名，请为每个签名选择语言后再试');
      } else {
        message.error(serverMsg || '更新失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const onFinishFailed = (errorInfo: any) => {
    // eslint-disable-next-line no-console
    console.error('[ProblemEdit] Form validation failed:', errorInfo);
    const messages = errorInfo?.errorFields?.map((f: any) => f.errors?.join('; ')).filter(Boolean).join('\n');
    if (messages) {
      message.error(`表单验证失败:\n${messages}`);
    } else {
      message.error('表单验证失败，请检查填写内容');
    }
  };

  return (
    <div>
      <Title level={4}>编辑题目</Title>
      <BackButton path="/problems" />
      <Spin spinning={fetching}>
        <Form form={form} layout="vertical" onFinish={onFinish} onFinishFailed={onFinishFailed} style={{ width: '100%' }}>
        <Card title="基本信息" style={{ marginBottom: 16 }}>
          <Form.Item name="title" label="题目标题" rules={[{ required: true }]}>
            <Input placeholder="如: 两数之和" />
          </Form.Item>
          <Form.Item name="description" label="题目描述 (Markdown)" rules={[{ required: true }]}>
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <TextArea rows={8} placeholder="支持 Markdown 格式" />
              </div>
              <div style={{ flex: 1, border: '1px solid #d9d9d9', borderRadius: 6, padding: 12, minHeight: 200, overflow: 'auto' }}>
                <Typography.Text strong style={{ marginBottom: 8, display: 'block' }}>预览</Typography.Text>
                {watchedDescription ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{watchedDescription}</ReactMarkdown> : <span style={{ color: '#999' }}>输入 Markdown 后在此预览</span>}
              </div>
            </div>
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
          <Form.List name="signatures">
            {(fields, { add, remove }) => (
              <>
                <Tabs
                  type="editable-card"
                  onEdit={(targetKey, action) => {
                    if (action === 'add') add({ language: 'python' });
                    else if (action === 'remove') remove(Number(targetKey));
                  }}
                  items={fields.map((field, idx) => {
                    const sigData = form.getFieldValue(['signatures', field.name]);
                    const langMap: Record<string, string> = { python: 'Python', java: 'Java', c: 'C', cpp: 'C++' };
                    return {
                    key: String(field.name),
                    label: sigData?.language
                      ? `${langMap[sigData.language] || sigData.language}${sigData.function_name ? ` - ${sigData.function_name}` : ''}`
                      : `签名${idx + 1}`,
                    closable: fields.length > 1,
                    children: (
                      <div style={{ width: '100%', minWidth: 500 }}>
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
                          <TextArea rows={10} placeholder="学生看到的初始代码" style={{ width: '100%' }} />
                        </Form.Item>
                        <Form.Item name={[field.name, 'prelude_code']} label="Prelude 代码"
                          tooltip="定义题目需要但学生不应手写的数据结构（如 ListNode、TreeNode）。简单题目（如只涉及基本类型 List[int]、int）不需要填，系统会自动处理。"
                        >
                          <TextArea rows={6} placeholder="预置代码（数据结构等），简单题可留空" style={{ width: '100%' }} />
                        </Form.Item>
                        <Form.Item name={[field.name, 'driver_template']} label="Driver 模板"
                          tooltip="控制如何把 JSON 测试用例解包后调用学生函数并输出结果。对于 List[int]、int 等标准类型系统会自动生成，不需要填。只有当参数类型复杂（如嵌套 JSON、树结构）时才需要自定义。"
                        >
                          <TextArea rows={8} placeholder="驱动代码模板，标准类型可留空，系统自动生成" style={{ width: '100%' }} />
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
                  };
                })}
                />
              </>
            )}
          </Form.List>
        </Card>

        <Card title="测试用例" style={{ marginBottom: 16 }}>
          <Form.List name="test_cases">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, idx) => (
                  <Card key={field.key} size="small" title={`用例 ${idx + 1}`} style={{ marginBottom: 8 }}
                    extra={fields.length > 1 && <MinusCircleOutlined onClick={() => remove(field.name)} />}
                  >
                    <Form.Item name={[field.name, 'input_params']} label={sigParams?.length ? '输入参数' : '输入 (JSON)'} rules={[{ required: true }]}>
                      <InputParamsEditor parameters={sigParams} placeholder='{"nums": [2, 7, 11, 15], "target": 9}' />
                    </Form.Item>
                    <Form.Item name={[field.name, 'expected_output']} label="期望输出" rules={[{ required: true }]}>
                      <InputParamsEditor placeholder='[0, 1] 或 true 或 42 等' />
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
            <Button type="primary" htmlType="submit" loading={loading}>保存修改</Button>
            <Button onClick={() => navigate('/problems')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
      </Spin>
    </div>
  );
}
