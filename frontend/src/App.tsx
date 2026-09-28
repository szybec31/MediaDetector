import "./App.css";
import {BrowserRouter,Routes,Route,} from "react-router-dom";

import HomePage from "./components/Homepage/HomePage";
import NewProjectPage from "./components/NewProject/NewProjectPage";
import ProfanityDictionaryPage from "./components/ProfanityDictionary/ProfanityDictionaryPage";
import ProjectDetailsPage from "./components/ProjectDetails/ProjectDetailsPage";

import AddSourceFile from "./components/Modules/AddSourceFile/AddSourceFile";
import ModulePage from "./components/Modules/ModulePage";
import ProfilePage from "./components/Profiles/Profiles";

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
          path="/profiles"
          element={<ProfilePage />}
        />

        <Route
          path="/projects/:projectId"
          element={<ProjectDetailsPage />}
        />
        <Route
          path="/projects/:projectId/modules/add-source-files"
          element={<AddSourceFile />}
        />

        <Route
          path="/projects/:projectId/modules/:moduleId"
          element={<ModulePage />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;

/*

*/