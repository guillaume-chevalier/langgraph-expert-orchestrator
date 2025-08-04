import { configureStore } from "@reduxjs/toolkit";
import chatReducer from "../features/chat/chatSlice";

export const store = configureStore({
  reducer: {
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["chat/handleSseEvent"],
        ignoredPaths: ["chat.messages.timestamp"],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
