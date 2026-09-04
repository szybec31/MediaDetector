import "./App.css";
import {BrowserRouter,Routes,Route,} from "react-router-dom";

import HomePage from "./components/Homepage/HomePage";
import NewProjectPage from "./components/NewProject/NewProjectPage";
import ProfanityDictionaryPage from "./components/ProfanityDictionary/ProfanityDictionaryPage";
import ProjectDetailsPage from "./components/ProjectDetails/ProjectDetailsPage";

import AddSourceFile from "./components/Modules/AddSourceFile/AddSourceFile";

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
        <Route
          path="/projects/:projectId/modules/add-source-files"
          element={<AddSourceFile />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;

/*

*/