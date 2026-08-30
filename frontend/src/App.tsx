import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

interface Project {
  name: string;
  created_at: string;
}

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectName, setProjectName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const loadProjects = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/projects");

      if (!response.ok) {
        throw new Error("Nie udało się pobrać projektów.");
      }

      const data = await response.json();
      setProjects(data);
    } catch (error) {
      setError("Nie udało się pobrać projektów.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const createProject = async (event: FormEvent) => {
    event.preventDefault();

    setError("");

    if (!projectName.trim()) {
      setError("Podaj nazwę projektu.");
      return;
    }

    setCreating(true);

    try {
      const response = await fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: projectName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Nie udało się utworzyć projektu.");
        return;
      }

      setProjectName("");

      await loadProjects();
    } catch (error) {
      setError("Nie udało się połączyć z backendem.");
      console.error(error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>MediaDetector</h1>
      </header>

      <main>
        <section>
          <h2>Nowy projekt</h2>

          <form onSubmit={createProject}>
            <input
              type="text"
              placeholder="Nazwa projektu"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              disabled={creating}
            />

            <button type="submit" disabled={creating}>
              {creating ? "Tworzenie..." : "Utwórz projekt"}
            </button>
          </form>

          {error && <p>{error}</p>}
        </section>

        <section>
          <h2>Projekty</h2>

          {loading ? (
            <p>Ładowanie...</p>
          ) : projects.length === 0 ? (
            <p>Brak projektów.</p>
          ) : (
            <div>
              {projects.map((project) => (
                <div key={project.name}>
                  <h3>{project.name}</h3>
                  <p>
                    Utworzono:{" "}
                    {new Date(project.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
