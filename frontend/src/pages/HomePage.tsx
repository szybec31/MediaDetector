import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import ProjectCard from "../components/ProjectCard";
import Footer from "../components/Footer";
import InfoOverlay from "../components/InfoOverlay";

import { useLanguage } from "../i18n";

interface Project {
  name: string;
  created_at: string;
}

function HomePage() {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showInfo, setShowInfo] = useState(false);

  const loadProjects = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/projects"
      );

      if (!response.ok) {
        throw new Error("Failed to load projects.");
      }

      const data: Project[] =
        await response.json();

      data.sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime()
      );

      setProjects(data);
    } catch (error) {
      console.error(error);
      setError(t.projects.error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleNewProject = () => {
    navigate("/projects/new");
    console.log("New project");
  };

  const handleNewPerson = () => {
    console.log("New person");
  };

  const handleProfanityDictionary = () => {
    navigate("/profanity-dictionary");
    console.log("Profanity dictionary");
  };

  const handleProjectClick = (
    project: Project
  ) => {
    console.log(
      "Open project:",
      project.name
    );
  };

  return (
    <div className="app">
      <Header
        onInfo={() => setShowInfo(true)}
      />

      <div className="app-body">
        <Sidebar
          onNewProject={handleNewProject}
          onNewPerson={handleNewPerson}
          onProfanityDictionary={
            handleProfanityDictionary
          }
        />

        <main className="content">
          <div className="content-header">
            <h1>{t.projects.title}</h1>
          </div>

          {loading && (
            <div className="status-message">
              {t.projects.loading}
            </div>
          )}

          {error && (
            <div className="status-message error">
              {error}
            </div>
          )}

          {!loading &&
            !error &&
            projects.length === 0 && (
              <div className="status-message">
                {t.projects.empty}
              </div>
            )}

          {!loading &&
            !error &&
            projects.length > 0 && (
              <div className="projects-scroll">
                <div className="projects-grid">
                  {projects.map((project) => (
                    <ProjectCard
                      key={project.name}
                      project={project}
                      onClick={() =>
                        handleProjectClick(
                          project
                        )
                      }
                    />
                  ))}
                </div>
              </div>
            )}
        </main>
      </div>

      <Footer />

      {showInfo && (
        <InfoOverlay
          onClose={() => setShowInfo(false)}
        />
      )}
    </div>
  );
}

export default HomePage;