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
  source?: string;
}

interface ProjectDetails {
  id: number;
  name: string;
  created_at: string;
  files: ProjectFile[];
}
const isTextFile = (file: ProjectFile) => {
  const textExtensions = [
    ".txt",
    ".json",
    ".srt",
    ".vtt",
    ".csv",
    ".md",
    ".log",
  ];

  return textExtensions.some((extension) =>
    file.name.toLowerCase().endsWith(extension)
  );
};

type ModuleKind = "audio" | "video";

interface ProjectModule {
  id: string;
  label: string;
  kind: ModuleKind;
  path: string;
}

type JsonTableRow = {
  id: number | string;
  start?: number | string;
  end?: number | string;
  text?: string;
  word?: string;
  normalized_word?: string;
  duration?: number | string;
};

const getJsonTableRows = (
  content: string
): JsonTableRow[] | null => {
  try {
    const parsed = JSON.parse(content);

    if (Array.isArray(parsed.segments)) {
      return parsed.segments.map(
        (item: any, index: number) => ({
          id: item.id ?? index,
          start: item.start,
          end: item.end,
          text: item.text,
        })
      );
    }

    if (Array.isArray(parsed.matches)) {
      return parsed.matches.map(
        (item: any, index: number) => ({
          id: index,
          start: item.start,
          end: item.end,
          word: item.word,
          normalized_word: item.normalized_word,
          duration: item.duration,
        })
      );
    }

    return null;
  } catch {
    return null;
  }
};

const formatTime = (value: number | string) => {
  const seconds = Number(value);

  if (!Number.isFinite(seconds)) {
    return String(value);
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return (
    `${String(minutes).padStart(2, "0")}:` +
    `${remainingSeconds.toFixed(3).padStart(6, "0")}`
  );
};

function ProjectDetailsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [project, setProject] = useState<ProjectDetails | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showInfo, setShowInfo] = useState(false);
  const [selectedFile, setSelectedFile] = useState<ProjectFile | null>(null);
  const [previewContent, setPreviewContent] = useState<string>("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [jsonTableRows, setJsonTableRows] =useState<JsonTableRow[] | null>(null);
  
  const projectModules: ProjectModule[] = [
  {
    id: "file-upload",
    label: t.ProjectDetailsModuleButtons.fileupload,
    kind: "video",
    path: `/projects/${projectId}/modules/add-source-files`,
  },
  {
    id: "transcription",
    label: t.ProjectDetailsModuleButtons.speachtotext,
    kind: "audio",
    path: `/projects/${projectId}/modules/transcription`,
  },
  {
    id: "filter-words",
    label: t.ProjectDetailsModuleButtons.worddetection,
    kind: "audio",
    path: `/projects/${projectId}/modules/filter-words`,
  },
  {
    id: "censor-transcription",
    label: t.ProjectDetailsModuleButtons.censor,
    kind: "audio",
    path: `/projects/${projectId}/modules/censor-transcription`,
  },
    {
    id: "mute-detected-words",
    label: t.ProjectDetailsModuleButtons.mute,
    kind: "audio",
    path: `/projects/${projectId}/modules/mute-detected-words`,
  },
  {
    id: "subtitles",
    label: t.ProjectDetailsModuleButtons.subtitles,
    kind: "video",
    path: `/projects/${projectId}/modules/subtitles`,
  },
  // In progress
  {
    id: "split-media",
    label: t.ProjectDetailsModuleButtons.split_media,
    kind: "video",
    path: `/projects/${projectId}/modules/split-media`,
  },
  {
    id: "video-only",
    label: t.ProjectDetailsModuleButtons.merge_media,
    kind: "video",
    path: `/projects/${projectId}/modules/merge-media`,
  },
  {
    id: "blurowanie-twarzy",
    label: t.ProjectDetailsModuleButtons.selectiveblur,
    kind: "video",
    path: `/projects/${projectId}/modules/blur`,
  },
];

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

 const handleOpenFile = async (file: ProjectFile) => {
  setSelectedFile(file);
  setPreviewContent("");
  setPreviewError("");

  if (!isTextFile(file)) {
    return;
  }

  try {
    setPreviewLoading(true);

    const encodedFilename = encodeURIComponent(file.name);

    const response = await fetch(
      `http://localhost:8000/api/projects/${projectId}/files/download/${encodedFilename}`
    );

    if (!response.ok) {
      const data = await response.json();

      throw new Error(
        data.detail || "Nie udało się odczytać pliku."
      );
    }

    const content = await response.text();

    setPreviewContent(content);

    // TYLKO dodatkowa obsługa JSON
    if (file.name.toLowerCase().endsWith(".json")) {
      setJsonTableRows(getJsonTableRows(content));
    } else {
      setJsonTableRows(null);
    }
  } catch (error) {
    console.error(error);

    if (error instanceof Error) {
      setPreviewError(error.message);
    } else {
      setPreviewError(
        "Nie udało się odczytać pliku."
      );
    }
  } finally {
    setPreviewLoading(false);
  }
};

  const getFileUrl = (filename: string) => {
    const encodedFilename = encodeURIComponent(filename);
    return `http://localhost:8000/api/projects/${projectId}/files/download/${encodedFilename}`;
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
                    {t.projectDetails.fileCount} {project.files.length}
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
                            onClick={() => handleOpenFile(file)}
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

              {!selectedFile ? (
                <div className="project-preview-empty">
                  {t.projectDetails.selectFile}
                </div>
              ) : (
                <div className="project-preview">
                  <div className="project-preview-title">
                    {selectedFile.name}
                  </div>

                  {selectedFile.type.startsWith("video/") && (
                    <video
                      className="project-preview-video"
                      controls
                      src={getFileUrl(selectedFile.name)}
                    >
                      Twoja przeglądarka nie obsługuje odtwarzania wideo.
                    </video>
                  )}

                  {selectedFile.type.startsWith("audio/") && (
                    <audio
                      className="project-preview-audio"
                      controls
                      src={getFileUrl(selectedFile.name)}
                    >
                      Twoja przeglądarka nie obsługuje odtwarzania audio.
                    </audio>
                  )}

                  {isTextFile(selectedFile) && (
                    <>
                      {previewLoading && (
                        <div className="project-preview-empty">
                          Ładowanie zawartości pliku...
                        </div>
                      )}

                      {previewError && (
                        <div className="project-preview-empty error">
                          {previewError}
                        </div>
                      )}
                      {!previewLoading && !previewError && (
                        jsonTableRows ? (
                          <div className="json-table-wrapper">
                            <table className="json-table">
                              <thead>
                                <tr>
                                  <th>ID</th>
                                  <th>Start</th>
                                  <th>End</th>

                                  {jsonTableRows.some(
                                    (row) => row.word !== undefined
                                  ) ? (
                                    <>
                                      <th>Słowo</th>
                                      <th>Normalizacja</th>
                                      <th>Czas trwania</th>
                                    </>
                                  ) : (
                                    <th>Tekst</th>
                                  )}
                                </tr>
                              </thead>

                              <tbody>
                                {jsonTableRows.map((row) => (
                                  <tr key={row.id}>
                                    <td>{row.id}</td>
                                    <td>{formatTime(row.start ?? "-")}</td>
                                    <td>{formatTime(row.end ?? "-")}</td>

                                    {row.word !== undefined ? (
                                      <>
                                        <td>{row.word}</td>
                                        <td>{row.normalized_word ?? "-"}</td>
                                        <td>{formatTime(row.duration ?? "-")}</td>
                                      </>
                                    ) : (
                                      <td>{row.text ?? "-"}</td>
                                    )}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <pre className="project-preview-text">
                            {previewContent}
                          </pre>
                        )
                      )}
                    </>
                  )}

                  {!selectedFile.type.startsWith("video/") &&
                    !selectedFile.type.startsWith("audio/") &&
                    !isTextFile(selectedFile) && (
                      <div className="project-preview-empty">
                        Podgląd tego typu pliku nie jest jeszcze obsługiwany.
                      </div>
                    )}

                  <button
                    type="button"
                    className="project-preview-close"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewContent("");
                      setPreviewError("");
                      setJsonTableRows(null)
                    }}
                  >
                    Zamknij podgląd
                  </button>
                </div>
              )}
            </section>

            <section className="project-section">
              <div className="project-section-header">
                <h2>{t.projectDetails.modules}</h2>
              </div>

              <div className="project-modules">
                {projectModules.map((module) => (
                  <button
                    key={module.id}
                    type="button"
                    className={`project-module-button project-module-button-${module.kind}`}
                    onClick={() => navigate(module.path)}
                  >
                    {module.label}
                  </button>
                ))}
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