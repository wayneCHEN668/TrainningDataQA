import { Routes, Route } from "react-router-dom";
import { ChatInterface } from "./components/ai/ChatInterface";
import { LoginPage } from "./components/auth/LoginPage";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<ChatInterface />} />
      </Route>
    </Routes>
  );
}

export default App;
