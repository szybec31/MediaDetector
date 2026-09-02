import {useState,type FormEvent,} from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../i18n";
import "./NewProjectPage.css";

function NewProjectPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    const trimmedName = name.trim();

    if (!trimmedName) {
      setError(t.newProject.required);
      return;
    }

    try {
      setSaving(true);
      setError("");

      const response = await fetch(
        "http://localhost:8000/api/projects",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: trimmedName,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.detail || t.newProject.failed
        );
      }

      navigate("/");
    } catch (error) {
      console.error(error);

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(t.newProject.failed);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate("/");
  };

  return (
    <div className="app">
      <main className="form-page">
        <div className="form-container">
          <div className="form-header">
            <h1>{t.newProject.title}</h1>

            <p>
              {t.newProject.description}
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="project-name">
                {t.newProject.name}
              </label>

              <input
                id="project-name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder={
                  t.newProject.placeholder
                }
                disabled={saving}
                autoFocus
              />
            </div>

            {error && (
              <div className="form-error">
                {error}
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={handleCancel}
                disabled={saving}
              >
                {t.newProject.cancel}
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={saving}
              >
                {saving
                  ? t.newProject.creating
                  : t.newProject.create}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default NewProjectPage;