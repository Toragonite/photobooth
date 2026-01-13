import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout/Layout";

// Pages
import { HomePage } from "./pages/HomePage";
import { CameraPage } from "./pages/CameraPage";
import { PreviewPage } from "./pages/PreviewPage";
import { PrintingPage } from "./pages/PrintingPage";
import { CompletePage } from "./pages/CompletePage";
import { ErrorPage } from "./pages/ErrorPage";
import { AdminLogin } from "./pages/AdminLogin";
import { AdminDashboard } from "./pages/AdminDashboard";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="camera" element={<CameraPage />} />
        <Route path="preview" element={<PreviewPage />} />
        <Route path="printing" element={<PrintingPage />} />
        <Route path="complete" element={<CompletePage />} />
        <Route path="error" element={<ErrorPage />} />
      </Route>
      <Route path="/admin" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
    </Routes>
  );
}

export default App;
