import React from "react";
import { Provider } from "react-redux";
import { ConfigProvider } from "antd";
import { store } from "./app/store";
import ChatWindow from "./features/chat/ChatWindow";
import "./App.css";

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "rgba(255, 173, 91, 1)", // Orange
          borderRadius: 12,
          colorBgContainer: "rgba(251, 250, 246, 1)", // almost white
          colorText: "rgba(30, 60, 65, 1)", // Teal
        },
        components: {
          Layout: {
            bodyBg: "transparent",
          },
          Card: {
            borderRadius: 16,
          },
          Button: {
            borderRadius: 44,
          },
          Input: {
            borderRadius: 12,
          },
        },
      }}
    >
      <Provider store={store}>
        <div className="App">
          <ChatWindow />
        </div>
      </Provider>
    </ConfigProvider>
  );
};

export default App;
