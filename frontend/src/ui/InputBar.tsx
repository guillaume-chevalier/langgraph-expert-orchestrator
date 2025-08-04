import React, { useState, useCallback, KeyboardEvent } from "react";
import { Input, Button, Space, Card, Form, message } from "antd";
import { SendOutlined, ClearOutlined } from "@ant-design/icons";

interface InputBarProps {
  onSendMessage: (message: string) => void;
  onClear?: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

const { TextArea } = Input;

export const InputBar: React.FC<InputBarProps> = ({
  onSendMessage,
  onClear,
  isStreaming,
  disabled = false,
}) => {
  const [messageText, setMessageText] = useState("");

  const handleSend = useCallback(() => {
    if (!messageText.trim()) {
      message.warning("Please enter a message");
      return;
    }

    // Send message - backend will load the full dataset automatically
    onSendMessage(messageText);
  }, [messageText, onSendMessage]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!isStreaming) {
          handleSend();
        }
      }
    },
    [handleSend, isStreaming],
  );

  const handleClear = useCallback(() => {
    setMessageText("");
    onClear?.();
  }, [onClear]);

  return (
    <Card size="small" style={{ margin: "16px 0" }}>
      <Form layout="vertical">
        {/* Message Input */}
        <Form.Item label="Your Question" style={{ marginBottom: 12 }}>
          <TextArea
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about security analysis, vulnerabilities, certificates, or geographic information..."
            rows={3}
            disabled={disabled || isStreaming}
            style={{ resize: "none" }}
          />
        </Form.Item>

        {/* Action Buttons */}
        <Form.Item style={{ marginBottom: 0 }}>
          <Space style={{ width: "100%", justifyContent: "space-between" }}>
            <Space>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                disabled={disabled || isStreaming || !messageText.trim()}
                loading={isStreaming}
              >
                {isStreaming ? "Analyzing..." : "Send"}
              </Button>
            </Space>

            <Button
              type="text"
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={disabled || isStreaming}
            >
              Clear
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default InputBar;
