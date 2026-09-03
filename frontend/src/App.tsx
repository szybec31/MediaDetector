import "./App.css";

import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import HomePage from "./pages/HomePage";
import NewProjectPage from "./pages/NewProjectPage";
import ProfanityDictionaryPage from "./pages/ProfanityDictionaryPage";
import ProjectDetailsPage from "./pages/ProjectDetailsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<HomePage />}
        />

        <Route
          path="/projects/new"
          element={<NewProjectPage />}
        />

        <Route
          path="/profanity-dictionary"
          element={<ProfanityDictionaryPage />}
        />

        <Route
          path="/projects/:projectId"
          element={<ProjectDetailsPage />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;