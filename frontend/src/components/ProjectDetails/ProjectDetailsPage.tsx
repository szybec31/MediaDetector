import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Header from "../Homepage/Header";
import ProjectSidebar  from "./ProjectSidebar";
import Footer from "../Footer";
import InfoOverlay from "../InfoOverlay";

import "./ProjectDetailsPage.css";
import { useLanguage } from "../../i18n";

interface ProjectFile {
  name: string;
  size: number;
  type: string;
}

interface ProjectDetails {
  id: number;
  name: string;
  created_at: string;
  files: ProjectFile[];
}

function ProjectDetailsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [project, setProject] =
    useState<ProjectDetails | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showInfo, setShowInfo] = useState(false);

      const loadProject = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `http://localhost:8000/api/projects/${projectId}`
        );

        if (!response.ok) {
          const data = await response.json();

          throw new Error(
            data.detail || t.projectDetails.loadError
          );
        }

        const data: ProjectDetails =
          await response.json();

        setProject(data);
      } catch (error) {
        console.error(error);

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError(
            t.projectDetails.loadError
          );
        }
      } finally {
        setLoading(false);
      }
    };

  useEffect(() => {

    loadProject();
  }, [projectId]);

  const handleBack = () => {
    navigate("/");
  };

  const handleDeleteProject = async () => {
    if (!project) {
      return;
    }

    const confirmed = window.confirm(
        t.projectDetails.deleteConfirmation.replace(
        "{name}",
        project.name
      )
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/projects/${project.id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.detail ||
            t.projectDetails.deleteError
        );
      }

      navigate("/");
    } catch (error) {
      console.error(error);

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          t.projectDetails.deleteError
        );
      }
    }
  };

  const handleDownloadAll = () => {
    console.log(
      "Pobieranie wszystkich plików:",
      project?.id
    );
  };

  const handleNewProject = () => {
    navigate("/projects/new");
  };

  const handleNewPerson = () => {
    console.log("Nowa osoba");
  };

  const handleProfanityDictionary = () => {
    navigate("/profanity-dictionary");
  };

  const handleDownloadFile = (filename: string) => {
  const encodedFilename = encodeURIComponent(filename);

  window.open(
    `http://localhost:8000/api/projects/${projectId}/files/download/${encodedFilename}`,
    "_blank"
  );
  };

  const handleDownloadAllFiles = () => {
  window.open(
    `http://localhost:8000/api/projects/${projectId}/files/download-all`,
    "_blank"
    );
  };  

  const handleDeleteFile = async (filename: string) => {
  const confirmed = window.confirm(
    `Czy na pewno chcesz usunąć plik "${filename}"?`
  );

  if (!confirmed) {
    return;
  }

  try {
    const encodedFilename = encodeURIComponent(filename);

    const response = await fetch(
      `http://localhost:8000/api/projects/${projectId}/files/${encodedFilename}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      const data = await response.json();

      throw new Error(
        data.detail || "Nie udało się usunąć pliku."
      );
    }

    await loadProject();
  } catch (error) {
    console.error(error);

    if (error instanceof Error) {
      setError(error.message);
    } else {
      setError("Nie udało się usunąć pliku.");
    }
  }
  };

  return (
    <div className="app">
      <Header
        onInfo={() => setShowInfo(true)}
      />

      <div className="app-body">
        <ProjectSidebar
        onDeleteProject={handleDeleteProject}
        onDownloadAll={handleDownloadAllFiles}
        fileCount={project?.files?.length ?? 0}
        
        />

        <main className="project-details-content">
          {loading && (
            <div className="status-message">
              {t.projectDetails.loading}
            </div>
          )}

          {!loading && error && (
            <div className="status-message error">
              {error}
            </div>
          )}

          {!loading && !error && project && (
            <>
              <div className="project-details-header">
                <div>
                  <h1>{project.name}</h1>

                  <div className="project-details-meta">
                    Projekt #{project.id}
                  </div>
                </div>
              </div>

              <section className="project-section">
                <div className="project-section-header">
                  <h2>{t.projectDetails.files}</h2>

                  <span>
                    {project.files.length} {t.projectDetails.fileCount}
                  </span>
                </div>

                {project.files.length === 0 ? (
                  <div className="project-empty">
                    {t.projectDetails.emptyFiles}
                  </div>
                ) : (
                  <div className="project-files">
                    {project.files.map((file) => (
                      <div
                        key={file.name}
                        className="project-file"
                      >
                        <div>
                          <div className="project-file-name">
                            {file.name}
                          </div>

                          <div className="project-file-meta">
                            {file.type} ·{" "}
                            {file.size} B
                          </div>
                        </div>

                        <div className="project-file-actions">
                          <button
                            type="button"
                            onClick={() =>
                              console.log("Odtwórz:", file.name)
                            }
                          >
                            {t.projectDetails.open}
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDownloadFile(file.name)
                            }
                            
                          >
                            {t.projectDetails.download}
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDeleteFile(file.name)
                            }
                          >
                            {t.projectDetails.delete}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="project-section">
                <div className="project-section-header">
                  <h2>{t.projectDetails.preview}</h2>
                </div>

                <div className="project-preview-empty">
                  {t.projectDetails.selectFile}
                </div>
              </section>

              <section className="project-section">
                <div className="project-section-header">
                  <h2>{t.projectDetails.modules}</h2>
                </div>

                <div className="project-modules">
                  <div className="project-module">

                    <button
                      type="button"
                      className="project-module-button"
                      onClick={() =>
                        navigate(
                          `/projects/${project.id}/modules/add-source-files`
                        )
                      }
                    >
                      Dodaj pliki źródłowe
                    </button>



                    
                  </div>
                </div>
              </section>
            </>
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

export default ProjectDetailsPage;