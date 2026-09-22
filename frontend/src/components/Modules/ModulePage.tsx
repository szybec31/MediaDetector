import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Header from "../Header";
import Footer from "../Footer";
import InfoOverlay from "../InfoOverlay";

import { useLanguage } from "../../i18n";
import { moduleConfigs } from "./moduleConfigs";

import type {
  ModuleConfig,
  ModuleParameter,
  ModuleResult,
  ProjectFile,
} from "./moduleTypes";

import "./ModulePage.css";

const API_URL = "http://localhost:8000";

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function getDefaultParameterValues(
  parameters: ModuleParameter[] = []
): Record<string, unknown> {
  return parameters.reduce<Record<string, unknown>>((result, parameter) => {
    result[parameter.id] = parameter.defaultValue ?? "";
    return result;
  }, {});
}

function getParameterFiles(
  parameter: ModuleParameter,
  projectFiles: ProjectFile[]
): ProjectFile[] {
  if (parameter.type !== "file") {
    return [];
  }

  if (parameter.id === "detected_words_file") {
    return projectFiles.filter((file) => {
      const filename = file.name.toLowerCase();

      return (
        filename.endsWith(".json") &&
        filename.startsWith("detected_words_")
      );
    });
  }

  if (parameter.id === "transcription") {
    return projectFiles.filter((file) => {
      const filename = file.name.toLowerCase();

      return (
        filename.endsWith(".json") &&
        filename.startsWith("transcription_")
      );
    });
  }

  return projectFiles.filter((file) => 
    { const filename = file.name.toLowerCase();
      return filename.endsWith(".json") && filename !== "project_info.json"; 
    });
}

function isProjectFileAllowed(
  file: ProjectFile,
  config: ModuleConfig
): boolean {
  const filename = file.name.toLowerCase();
  const fileType = file.type.toLowerCase();

  if (config.acceptedFileTypes.includes("any")) {
    return true;
  }

  if (config.acceptedFileTypes.includes("audio-video")) {
    return fileType.startsWith("audio/") || fileType.startsWith("video/")
  }

  if (config.acceptedFileTypes.includes("audio")) {
    return fileType.startsWith("audio/");
  }

  if (config.acceptedFileTypes.includes("video")) {
    return fileType.startsWith("video/");
  }

  if (config.acceptedFileTypes.includes("transcription-json")) {
    const isJson =
      fileType === "application/json" || filename.endsWith(".json");

    if (!isJson) {
      return false;
    }

    if (config.requiredFilename) {
      return filename.includes(config.requiredFilename.toLowerCase());
    }

    return true;
  }

  return false;
}

function getFileTypeLabel(config: ModuleConfig): string {
  if (config.acceptedFileTypes.includes("audio")) {
    return "audio";
  }

  if (config.acceptedFileTypes.includes("video")) {
    return "video";
  }

  if (config.acceptedFileTypes.includes("transcription-json")) {
    return "JSON transkrypcji";
  }

  return "wszystkie pliki";
}

export default function ModulePage() {
  const { projectId, moduleId } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const config = moduleId ? moduleConfigs[moduleId] : undefined;

  const [showInfo, setShowInfo] = useState(false);

  const [projectFiles, setProjectFiles] = useState<ProjectFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<ProjectFile | null>(null);

  const [parameters, setParameters] = useState<Record<string, unknown>>({});
  const [result, setResult] = useState<ModuleResult | null>(null);

  const [loadingFiles, setLoadingFiles] = useState(true);
  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    if (!config) {
      return;
    }

    setParameters(getDefaultParameterValues(config.parameters));
  }, [config]);

  useEffect(() => {
    if (!projectId) {
      return;
    }

    const loadProjectFiles = async () => {
      setLoadingFiles(true);
      setError("");

      try {
        const response = await fetch(
          `${API_URL}/api/projects/${projectId}`
        );

        if (!response.ok) {
          throw new Error("Nie udało się pobrać plików projektu.");
        }

        const data = await response.json();

        setProjectFiles(data.files ?? []);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Nie udało się pobrać plików projektu."
        );
      } finally {
        setLoadingFiles(false);
      }
    };

    loadProjectFiles();
  }, [projectId]);

 
    useEffect(() => {
    if (!jobId || !config?.statusEndpoint) {
        return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;

    const pollStatus = async () => {
        try {
        const response = await fetch(
            `${API_URL}${config.statusEndpoint}/${jobId}`
        );

        if (!response.ok) {
            throw new Error("Nie udało się pobrać statusu zadania.");
        }

        const data = await response.json();

        if (cancelled) {
            return;
        }

        setResult({
            status: data.status,
            progress: Math.round((data.progress ?? 0) * 100),
            message: data.message ?? "",
            outputFiles: data.output_files ?? [],
        });

        if (data.status === "completed") {
            setLoading(false);
            return;
        }

        if (data.status === "failed") {
            setLoading(false);
            setError(data.error ?? "Moduł zakończył się błędem.");
            return;
        }

        timeoutId = window.setTimeout(pollStatus, 1000);
        } catch (pollError) {
        if (cancelled) {
            return;
        }

        setLoading(false);
        setError(
            pollError instanceof Error
            ? pollError.message
            : "Nie udało się pobrać statusu zadania."
        );
        }
    };

    pollStatus();

    return () => {
        cancelled = true;

        if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
        }
    };
    }, [jobId, config?.statusEndpoint]);


  const availableFiles =
    config && projectFiles.length > 0
      ? projectFiles.filter((file) => isProjectFileAllowed(file, config))
      : [];

  if (!config) {
    return (
      <>
        <Header onInfo={() => setShowInfo(true)} />

        <main className="module-page">
          <section className="module-section module-error-section">
            <h1>Nie znaleziono modułu</h1>

            <button
              type="button"
              className="module-secondary-button"
              onClick={() => navigate(-1)}
            >
              Wróć
            </button>
          </section>
        </main>

        <Footer />

        {showInfo && (
          <InfoOverlay onClose={() => setShowInfo(false)} />
        )}
      </>
    );
  }

  const handleParameterChange = (
    parameter: ModuleParameter,
    value: unknown
  ) => {
    setParameters((previous) => ({
      ...previous,
      [parameter.id]: value,
    }));
  };

  const handleSelectFile = (file: ProjectFile) => {
    setSelectedFile(file);
    setError("");
  };

  const handleRunModule = async () => {
    if (!selectedFile) {
      setError("Najpierw wybierz plik wejściowy.");
      return;
    }

    if (!projectId) {
      setError("Brak identyfikatora projektu.");
      return;
    }

    setError("");
    setLoading(true);

    setResult({
      status: "pending",
      progress: 0,
      message: "Przygotowywanie zadania...",
    });

    try {
      const response = await fetch(`${API_URL}${config.runEndpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: Number(projectId),
          filename: selectedFile.name,
          parameters,
        }),
      });

      if (!response.ok) {
        throw new Error("Nie udało się uruchomić modułu.");
      }

      const data = await response.json();

      setJobId(data.job_id);

      setResult({
        status: data.status ?? "running",
        progress: Math.round((data.progress ?? 0) * 100),
        message: data.message ?? "Moduł został uruchomiony.",
        outputFiles: data.output_files ?? [],
      });

    } catch (runError) {
      setLoading(false);

      setResult({
        status: "failed",
        progress: 0,
        message: "Wystąpił błąd podczas przetwarzania.",
      });

      setError(
        runError instanceof Error
          ? runError.message
          : "Nieznany błąd podczas uruchamiania modułu."
      );
    }
  };

  const renderParameter = (parameter: ModuleParameter) => {
    const value = parameters[parameter.id];

    switch (parameter.type) {
      case "text":
        if (parameter.id === "font_color") {
          return ( 
            <input 
              type="color"
              className="parameter-color-input" 
              value={String(value ?? "#FFFFFF")} 
              onChange={(event) => handleParameterChange( parameter, event.target.value ) } 
            /> 
          ); 
        }
        return (
          <input
            type="text"
            value={String(value ?? "")}
            required={parameter.required}
            onChange={(event) =>
              handleParameterChange(parameter, event.target.value)
            }
          />
        );

      case "number":
        return (
          <input
            type="number"
            value={Number(value ?? 0)}
            min={parameter.min}
            max={parameter.max}
            step={parameter.step ?? 1}
            required={parameter.required}
            onChange={(event) =>
              handleParameterChange(parameter, Number(event.target.value))
            }
          />
        );

      case "select":
        return (
          <select
            value={String(value ?? "")}
            required={parameter.required}
            onChange={(event) =>
              handleParameterChange(parameter, event.target.value)
            }
          >
            {parameter.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case "checkbox":
        return (
          <label className="module-checkbox">
            <input
              type="checkbox"
              checked={Boolean(value)}
              onChange={(event) =>
                handleParameterChange(parameter, event.target.checked)
              }
            />

            <span>{parameter.label}</span>
          </label>
        );

        case "file": {
        const parameterFiles = projectFiles.filter((file) => {
          const filename = file.name.toLowerCase();

          if (parameter.id === "detected_words_file") {
            return (
              filename.endsWith(".json") &&
              filename.startsWith("detected_words_")
            );
          }
          if (parameter.id === "transcription_file" || parameter.id === "censored_transcription") {
            return (
              filename.endsWith(".json") &&
              (filename.startsWith("transcription_") || filename.startsWith("censored_"))
            );
          }

          return false;
        });

        return (
          <select
            value={String(value ?? "")}
            required={parameter.required}
            onChange={(event) =>
              handleParameterChange(
                parameter,
                event.target.value
              )
            }
          >
            <option value="">Wybierz plik</option>

            {parameterFiles.map((file) => (
              <option key={file.name} value={file.name}>
                {file.name}
              </option>
            ))}
          </select>
        );
      }

      case "multiselect":
        return (
          <select
            multiple
            value={Array.isArray(value) ? value.map(String) : []}
            required={parameter.required}
            onChange={(event) => {
              const selectedValues = Array.from(
                event.target.selectedOptions
              ).map((option) => option.value);

              handleParameterChange(parameter, selectedValues);
            }}
          >
            {parameter.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Header onInfo={() => setShowInfo(true)} />

      <main className="module-page">
        <div className="module-page-header">


          <h1>{config.title}</h1>
        </div>

        {/* 2. Opis modułu */}
        <section className="module-section">
          <h2>Opis modułu</h2>
          <p className="module-description">
            {config.description}
          </p>
        </section>

        {/* 3. Lista plików projektu */}
        <section className="module-section">
          <div className="module-section-heading">
            <div>
              <h2>Plik wejściowy</h2>

              <p className="module-section-description">
                Dostępne pliki: {getFileTypeLabel(config)}
              </p>

              {config.requiredFilename && (
                <p className="module-section-description">
                  Nazwa pliku musi zawierać:{" "}
                  <strong>{config.requiredFilename}</strong>
                </p>
              )}
            </div>

            <span className="module-file-count">
              {availableFiles.length}
            </span>
          </div>

          {loadingFiles ? (
            <div className="module-empty-box">
              Ładowanie plików projektu...
            </div>
          ) : availableFiles.length === 0 ? (
            <div className="module-empty-box">
              Brak plików pasujących do wymagań tego modułu.
            </div>
          ) : (
            <div className="module-file-list">
              {availableFiles.map((file) => {
                const isSelected = selectedFile?.name === file.name;

                return (
                  <button
                    key={file.name}
                    type="button"
                    className={`module-file-item ${
                      isSelected ? "selected" : ""
                    }`}
                    onClick={() => handleSelectFile(file)}
                  >
                    <span className="module-file-item-main">
                      <strong>{file.name}</strong>

                      <span className="module-file-item-meta">
                        {file.type || "Nieznany typ"} ·{" "}
                        {formatFileSize(file.size)}
                      </span>
                    </span>

                    <span className="module-file-item-status">
                      {isSelected ? "Wybrany" : "Wybierz"}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {selectedFile && (
            <div className="module-selected-file">
              <span>Wybrany plik:</span>
              <strong>{selectedFile.name}</strong>
            </div>
          )}
        </section>

        {/* 4. Parametry */}
        {config.parameters && config.parameters.length > 0 && (
          <section className="module-section">
            <h2>Parametry modułu</h2>

            <div className="module-parameters">
              {config.parameters.map((parameter) => (
                <div
                  key={parameter.id}
                  className={`module-parameter module-parameter-${parameter.type}`}
                >
                  {parameter.type !== "checkbox" && (
                    <label htmlFor={parameter.id}>
                      {parameter.label}
                    </label>
                  )}

                  {parameter.description && (
                    <p className="module-parameter-description">
                      {parameter.description}
                    </p>
                  )}

                  <div id={parameter.id}>
                    {renderParameter(parameter)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="module-section module-run-section">
          <button
            type="button"
            className="module-primary-button"
            disabled={loading || !selectedFile}
            onClick={handleRunModule}
          >
            {loading ? "Przetwarzanie..." : "Uruchom moduł"}
          </button>

          {error && (
            <div className="module-error-message">
              {error}
            </div>
          )}
        </section>

        {/* 5. Pasek postępu */}
        <section className="module-section">
          <h2>Postęp przetwarzania</h2>

          <div className="module-progress-wrapper">
            <div className="module-progress-header">
              <span>
                {result?.message ??
                  "Moduł nie został jeszcze uruchomiony."}
              </span>

              <strong>{result?.progress ?? 0}%</strong>
            </div>

            <div className="module-progress-track">
              <div
                className="module-progress-bar"
                style={{
                  width: `${result?.progress ?? 0}%`,
                }}
              />
            </div>
          </div>
        </section>

        {/* 6. Wynik */}
        <section className="module-section">
          <h2>Wynik modułu</h2>

          {!result && (
            <p className="module-empty-result">
              Wynik pojawi się tutaj po uruchomieniu modułu.
            </p>
          )}

          {result?.status === "failed" && (
            <div className="module-result-error">
              Przetwarzanie zakończyło się błędem.
            </div>
          )}

          {result?.status === "completed" && (
            <div className="module-result">
              <p className="module-result-success">
                Przetwarzanie zakończone pomyślnie.
              </p>

              {!result.outputFiles ||
              result.outputFiles.length === 0 ? (
                <p className="module-empty-result">
                  Moduł nie zwrócił jeszcze plików wynikowych.
                </p>
              ) : (
                <div className="module-output-files">
                  {result.outputFiles.map((file,index) => (
                    <div
                      className="module-output-file"
                      key={`${file.name}-${file.type}-${index}`}
                    >
                      <div>
                        <strong>{file.name}</strong>
                        <span>{formatFileSize(file.size)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      <Footer />

      {showInfo && (
        <InfoOverlay onClose={() => setShowInfo(false)} />
      )}
    </>
  );
}