import React, { useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  Layout,
  Card,
  Typography,
  Timeline,
  Badge,
  Spin,
  Alert,
  Progress,
  Tag,
  Space,
} from "antd";
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from "@ant-design/icons";

import { useChat } from "./useChat";
import {
  selectMessages,
  selectExpertPanels,
  selectFinalSummary,
  selectErrors,
  selectActiveExperts,
  selectCompletedExperts,
  selectProcessingExperts,
  selectTotalRecords,
  selectProcessedRecords,
  selectRecordSummaries,
  selectAnalysisDone,
  resetConversation,
} from "./chatSlice";
import { DEFAULT_EXPERT_CONFIGS, ExpertPanelState } from "../../types";
import InputBar from "../../ui/InputBar";
import Md from "../../ui/Md";

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

interface ExpertPanelProps {
  expertPanel: ExpertPanelState;
}

const ExpertPanel: React.FC<ExpertPanelProps> = ({ expertPanel }) => {
  const config = DEFAULT_EXPERT_CONFIGS.find(
    (c) => c.type === expertPanel.expert_type,
  ) || {
    id: expertPanel.expert_id,
    type: expertPanel.expert_type,
    name: expertPanel.expert_type,
    description: "Expert analysis",
    color: "#666666",
    icon: "🔧",
  };

  const getStatusIcon = () => {
    switch (expertPanel.status) {
      case "processing":
        return <LoadingOutlined spin style={{ color: "#1890ff" }} />;
      case "completed":
        return <CheckCircleOutlined style={{ color: "#52c41a" }} />;
      case "error":
        return <ExclamationCircleOutlined style={{ color: "#f5222d" }} />;
      default:
        return <ClockCircleOutlined style={{ color: "#d9d9d9" }} />;
    }
  };

  const getStatusColor = () => {
    switch (expertPanel.status) {
      case "processing":
        return "processing";
      case "completed":
        return "success";
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  return (
    <Card
      size="small"
      className={`expert-panel expert-panel-${expertPanel.status}`}
      title={
        <Space>
          <span style={{ fontSize: "18px" }}>{config.icon}</span>
          <span>{config.name}</span>
          <Badge status={getStatusColor()} />
        </Space>
      }
      extra={getStatusIcon()}
      style={{
        marginBottom: 16,
        borderColor:
          expertPanel.status === "completed" ? config.color : undefined,
      }}
    >
      <div style={{ minHeight: 120 }}>
        {expertPanel.status === "processing" && (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <Spin size="small" />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Analyzing...</Text>
            </div>
          </div>
        )}

        {expertPanel.chunks.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            {expertPanel.chunks.map((chunk, index) => (
              <div key={index} style={{ margin: "4px 0" }}>
                <Md>{chunk}</Md>
              </div>
            ))}
          </div>
        )}

        {expertPanel.final_summary && (
          <div>
            <div>
              <Md>{expertPanel.final_summary}</Md>
            </div>

            {expertPanel.status === "completed" && (
              <div
                style={{
                  marginTop: 12,
                  paddingTop: 8,
                  borderTop: "1px solid #f0f0f0",
                }}
              >
                <Space size="middle">
                  {expertPanel.confidence && (
                    <Tag color={config.color}>
                      Confidence: {(expertPanel.confidence * 100).toFixed(0)}%
                    </Tag>
                  )}
                  {expertPanel.processing_time_ms && (
                    <Tag>
                      <ClockCircleOutlined /> {expertPanel.processing_time_ms}ms
                    </Tag>
                  )}
                </Space>
              </div>
            )}
          </div>
        )}

        {expertPanel.error_message && (
          <Alert
            message="Analysis Error"
            description={expertPanel.error_message}
            type="error"
          />
        )}
      </div>
    </Card>
  );
};

export const ChatWindow: React.FC = () => {
  const dispatch = useDispatch();
  const { sendMessage, isStreaming, hasError } = useChat();
  const messages = useSelector(selectMessages);
  const expertPanels = useSelector(selectExpertPanels);
  const finalSummary = useSelector(selectFinalSummary);
  const errors = useSelector(selectErrors);
  const activeExperts = useSelector(selectActiveExperts);
  const completedExperts = useSelector(selectCompletedExperts);
  const processingExperts = useSelector(selectProcessingExperts);
  const totalRecords = useSelector(selectTotalRecords);
  const processedRecords = useSelector(selectProcessedRecords);
  const recordSummaries = useSelector(selectRecordSummaries);
  const analysisDone = useSelector(selectAnalysisDone);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, expertPanels, finalSummary]);

  const getOverallProgress = () => {
    if (!totalRecords || totalRecords === 0) return 0;
    return (processedRecords / totalRecords) * 100;
  };

  const handleClearConversation = () => {
    dispatch(resetConversation());
  };

  return (
    <Layout>
      <Content
        style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}
      >
        <div style={{ marginBottom: "24px" }}>
          <Title level={2}>🔍 LangGraph Expert Orchestrator</Title>
          <Paragraph type="secondary">
            Get comprehensive security insights from Generative AI in-depth data
            analysis. Ask about hosts and certificates, and more.
          </Paragraph>
        </div>

        {/* Input Section */}
        <InputBar
          onSendMessage={sendMessage}
          onClear={handleClearConversation}
          isStreaming={isStreaming}
        />

        {/* Conversation Messages */}
        {messages.length > 0 && (
          <Card title="Conversation" style={{ marginBottom: 24 }}>
            <Timeline mode="left">
              {messages.map((message) => (
                <Timeline.Item
                  key={message.id}
                  dot={
                    message.type === "user" ? (
                      <Badge status="processing" />
                    ) : message.type === "final" ? (
                      <CheckCircleOutlined style={{ color: "#52c41a" }} />
                    ) : (
                      <ClockCircleOutlined />
                    )
                  }
                >
                  <div
                    style={{ wordBreak: "break-word", whiteSpace: "pre-wrap" }}
                  >
                    <Text
                      type="secondary"
                      style={{ fontSize: 12, marginRight: 8 }}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Text>
                    <Text strong>
                      {message.type === "user"
                        ? "You"
                        : message.type === "final"
                          ? "Final Summary"
                          : message.expert_type
                            ? `${message.expert_type.toUpperCase()} Expert`
                            : "System"}
                      :
                    </Text>
                    <div style={{ marginTop: 4 }}>
                      <Md>{message.content}</Md>
                    </div>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}

        {/* Progress Indicator */}
        {isStreaming && totalRecords !== null && (
          <Card title="Analysis Progress" style={{ marginBottom: 24 }}>
            <Progress
              percent={totalRecords ? Math.round(getOverallProgress()) : 0}
              status={
                hasError ? "exception" : isStreaming ? "active" : "success"
              }
              format={() =>
                `${processedRecords}/${totalRecords || 0} records processed`
              }
            />
            <div style={{ marginTop: 12 }}>
              <Space wrap>
                {processingExperts.map((expert) => (
                  <Tag key={expert.expert_id} color="blue">
                    <LoadingOutlined spin /> {expert.expert_type}
                  </Tag>
                ))}
                {completedExperts.map((expert) => (
                  <Tag key={expert.expert_id} color="green">
                    <CheckCircleOutlined /> {expert.expert_type}
                  </Tag>
                ))}
              </Space>
            </div>
          </Card>
        )}

        {/* Per-Record Summaries */}
        {Object.keys(recordSummaries).length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <Title level={3}>Individual Record Analysis</Title>
            {Object.entries(recordSummaries).map(([id, rec]) => (
              <Card size="small" key={id} style={{ marginBottom: 8 }}>
                <Text strong>
                  {rec.kind === "host" ? "🖥️ Host" : "🔐 Cert"} — {id}
                </Text>
                <div style={{ marginTop: 8 }}>
                  <Md>{rec.summary}</Md>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Expert Panels */}
        {!analysisDone && activeExperts.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <Title level={3}>Expert Analysis</Title>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "16px" }}
            >
              {Object.values(expertPanels).map((panel) => (
                <ExpertPanel key={panel.expert_id} expertPanel={panel} />
              ))}
            </div>
          </div>
        )}

        {/* Final Summary */}
        {finalSummary && (
          <Card
            title={
              <Space>
                <CheckCircleOutlined style={{ color: "#52c41a" }} />
                <span>Comprehensive Analysis Summary</span>
              </Space>
            }
            style={{ marginBottom: 24 }}
          >
            <div>
              <Md>{finalSummary}</Md>
            </div>
          </Card>
        )}

        {/* Errors */}
        {errors.length > 0 && (
          <Alert
            message="Analysis Errors"
            description={
              <ul>
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            }
            type="error"
            closable
            style={{ marginBottom: 24 }}
          />
        )}

        <div ref={messagesEndRef} />
      </Content>
    </Layout>
  );
};

export default ChatWindow;
