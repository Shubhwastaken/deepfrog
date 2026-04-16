import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Results from "./pages/Results";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/dashboard"
          element={(
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/upload"
          element={(
            <ProtectedRoute>
              <Upload />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/results/:jobId"
          element={(
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          )}
        />
      </Routes>
    </Router>
  );
}
