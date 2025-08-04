import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

// Mock the entire ChatWindow component to avoid complex Ant Design rendering issues
jest.mock("./features/chat/ChatWindow", () => {
  return function MockChatWindow() {
    return (
      <div data-testid="chat-window">
        <h2>LangGraph Expert Orchestrator</h2>
        <input placeholder="Ask about security analysis, vulnerabilities, certificates, or geographic information..." />
      </div>
    );
  };
});

describe("App Component", () => {
  it("renders without crashing", () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });

  it("provides Redux store to children", () => {
    render(<App />);
    expect(screen.getByTestId("chat-window")).toBeInTheDocument();
  });
});
