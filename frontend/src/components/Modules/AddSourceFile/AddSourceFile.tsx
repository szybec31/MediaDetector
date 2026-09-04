import {useRef,useState,type ChangeEvent,type DragEvent,} from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLanguage } from "../../../i18n";

import "./AddSourceFile.css";
import Header from "../../Header";
import Footer from "../../Footer";
import InfoOverlay from "../../InfoOverlay";

function AddSourceFile() {
  const { projectId } = useParams<{ projectId: string }>();

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFiles, setSelectedFiles] =
    useState<File[]>([]);

  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [showInfo, setShowInfo] = useState(false);

  const addFiles = (files: File[]) => {
    if (files.length === 0) {
      return;
    }

    setSelectedFiles((currentFiles) => {
      const existingFiles = new Set(
        currentFiles.map(
          (file) =>
            `${file.name}-${file.size}-${file.lastModified}`
        )
      );

      const newFiles = files.filter(
        (file) =>
          !existingFiles.has(
            `${file.name}-${file.size}-${file.lastModified}`
          )
      );

      return [...currentFiles, ...newFiles];
    });

    setError("");
    setSuccess("");
  };

  const handleFileChange = (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const files = Array.from(
      event.target.files || []
    );

    addFiles(files);

    // Pozwala ponownie wybrać ten sam plik.
    event.target.value = "";
  };

  const handleDragEnter = (
    event: DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (!uploading) {
      setDragActive(true);
    }
  };

  const handleDragOver = (
    event: DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (!uploading) {
      setDragActive(true);
    }
  };

  const handleDragLeave = (
    event: DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (
      event.currentTarget === event.target
    ) {
      setDragActive(false);
    }
  };

  const handleDrop = (
    event: DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(false);

    if (uploading) {
      return;
    }

    const files = Array.from(
      event.dataTransfer.files
    );

    addFiles(files);
  };

  const handleChooseFiles = () => {
    if (uploading) {
      return;
    }

    fileInputRef.current?.click();
  };

  const handleRemoveFile = (fileToRemove: File) => {
    setSelectedFiles((currentFiles) =>
      currentFiles.filter(
        (file) => file !== fileToRemove
      )
    );

    setError("");
    setSuccess("");
  };

  const formatFileSize = (size: number) => {
    if (size < 1024) {
      return `${size} B`;
    }

    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)} KB`;
    }

    if (size < 1024 * 1024 * 1024) {
      return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }

    return `${(
      size /
      (1024 * 1024 * 1024)
    ).toFixed(1)} GB`;
  };

  const handleUpload = async () => {
    if (!projectId) {
      setError("Nie znaleziono projektu.");
      return;
    }

    if (selectedFiles.length === 0) {
      setError("Wybierz przynajmniej jeden plik.");
      return;
    }

    const formData = new FormData();

    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      setUploading(true);
      setError("");
      setSuccess("");

      const response = await fetch(
        `http://localhost:8000/api/projects/${projectId}/files`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        let message =
          "Nie udało się dodać plików.";

        try {
          const data = await response.json();

          if (data.detail) {
            message = data.detail;
          }
        } catch {
          // API nie zwróciło poprawnego JSON-a.
        }

        throw new Error(message);
      }

      setSelectedFiles([]);
      setSuccess("Pliki zostały dodane.");
    } catch (error) {
      console.error(error);

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Nie udało się dodać plików."
        );
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app">
      <Header
        onInfo={() => setShowInfo(true)}
      />

      <main className="add-source-files-content">
        <section className="add-source-files">
          <div className="add-source-files-header">
            <h2>{t.addSourceFile.title}</h2>

            <p>
              {t.addSourceFile.description}
            </p>
          </div>

          <div className="add-source-files-form">
            <div
              className={`add-source-files-dropzone ${
                dragActive ? "drag-active" : ""
              } ${
                uploading ? "uploading" : ""
              }`}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleChooseFiles}
              role="button"
              tabIndex={uploading ? -1 : 0}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" ||
                  event.key === " "
                ) {
                  handleChooseFiles();
                }
              }}
            >
              <div className="add-source-files-dropzone-icon">
                ↑
              </div>

              <div className="add-source-files-dropzone-title">
                {dragActive
                  ? t.addSourceFile.dropzone.active
                  : t.addSourceFile.dropzone.title}
              </div>

              <div className="add-source-files-dropzone-description">
                {t.addSourceFile.dropzone.description}
              </div>

              <div className="add-source-files-dropzone-info">
                {t.addSourceFile.dropzone.supported}
              </div>

              <input
                ref={fileInputRef}
                id="source-files"
                type="file"
                multiple
                accept="audio/*,video/*"
                onChange={handleFileChange}
                disabled={uploading}
              />
            </div>

            {selectedFiles.length > 0 && (
              <div className="add-source-files-selected">
                <div className="add-source-files-selected-header">
                  <h3>
                    {t.addSourceFile.selectedFiles}
                  </h3>

                  <span>
                    {selectedFiles.length}
                  </span>
                </div>

                <div className="add-source-files-list">
                  {selectedFiles.map((file) => (
                    <div
                      className="add-source-file"
                      key={`${file.name}-${file.size}-${file.lastModified}`}
                    >
                      <div className="add-source-file-info">
                        <div className="add-source-file-name">
                          {file.name}
                        </div>

                        <div className="add-source-file-meta">
                          {formatFileSize(file.size)}
                        </div>
                      </div>

                      <button
                        type="button"
                        className="add-source-file-remove"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleRemoveFile(file);
                        }}
                        disabled={uploading}
                        aria-label={`${t.addSourceFile.removeFile}: ${file.name}`}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div
                className="add-source-files-message error"
                role="alert"
              >
                {error}
              </div>
            )}

            {success && (
              <div
                className="add-source-files-message success"
                role="status"
              >
                {success}
              </div>
            )}

            <button
              type="button"
              className="add-source-files-button"
              onClick={handleUpload}
              disabled={
                uploading ||
                selectedFiles.length === 0
              }
            >
              {uploading
                ? t.addSourceFile.uploading
                : `${t.addSourceFile.upload}${
                    selectedFiles.length > 0
                      ? ` (${selectedFiles.length})`
                      : ""
                  }`}
            </button>
          </div>
        </section>
      </main>

      <Footer />

      {showInfo && (
        <InfoOverlay
          onClose={() => setShowInfo(false)}
        />
      )}
    </div>
  );
}
export default AddSourceFile;
