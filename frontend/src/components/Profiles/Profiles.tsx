import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../../i18n";
import "./Profiles.css";

import Header from "../Homepage/Header";
import Footer from "../Footer";
import InfoOverlay from "../InfoOverlay";


type ProfilePhoto = {
  id: number;
  filename: string;
  uploaded_at: string | null;
  embedding_status?: string | null;
};

type PersonProfile = {
  id: number;
  name: string;
  safe_name?: string;
  created_at: string | null;
  photos: ProfilePhoto[];
};

function createId(): string {
  return crypto.randomUUID();
}

function ProfilePage() {
const { t } = useLanguage();
const [profiles, setProfiles] = useState<PersonProfile[]>([]);
const [profileName, setProfileName] = useState("");
const [showCreateForm, setShowCreateForm] = useState(false);
const [showInfo, setShowInfo] = useState(false);
const [error, setError] = useState("");
const [isLoading, setIsLoading] = useState(true);
const [activePhoto, setActivePhoto] = useState<{
  profileName: string;
  photos: ProfilePhoto[];
  index: number;
} | null>(null);

const loadProfiles = async () => {
setError("");

try {
    const response = await fetch("http://localhost:8000/api/profiles");

    if (!response.ok) {
    throw new Error("Nie udało się pobrać profili.");
    }

    const data = await response.json();
    setProfiles(data.profiles);
} catch (err) {
    setError(
    err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas pobierania profili."
    );
} finally {
    setIsLoading(false);
}
};

useEffect(() => {
void loadProfiles();
}, []);


const handleCreateProfile = async (name: string) => {
  setError("");

  try {
    const response = await fetch("http://localhost:8000/api/profiles", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Nie udało się utworzyć profilu.");
    }

    setProfiles((current) => [...current, data]);
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas tworzenia profilu."
    );
  }
};


const handleRenameProfile = async (
  profileId: number,
  name: string
) => {
  setError("");

  try {
    const response = await fetch(`http://localhost:8000/api/profiles/${profileId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Nie udało się zmienić nazwy.");
    }

    setProfiles((current) =>
      current.map((profile) =>
        profile.id === profileId ? data : profile
      )
    );
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas zmiany nazwy."
    );
  }
};

const handleDeleteProfile = async (profileId: number) => {
  setError("");

  try {
    const response = await fetch(`http://localhost:8000/api/profiles/${profileId}`, {
      method: "DELETE",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Nie udało się usunąć profilu.");
    }

    setProfiles((current) =>
      current.filter((profile) => profile.id !== profileId)
    );
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas usuwania profilu."
    );
  }
};


const handleAddPhotos = async (
  profileId: number,
  files: FileList | File[]
) => {
  if (files.length === 0) return;

  const formData = new FormData();

  Array.from(files).forEach((file) => {
    formData.append("files", file);
  });

  setError("");

  try {
    const response = await fetch(
      `http://localhost:8000/api/profiles/${profileId}/photos`,
      {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Nie udało się dodać zdjęć.");
    }

    await loadProfiles();
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas dodawania zdjęć."
    );
  }
};

const handleDeletePhoto = async (
  profileId: number,
  photoId: number
) => {
  setError("");

  try {
    const response = await fetch(
      `http://localhost:8000/api/profiles/${profileId}/photos/${photoId}`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Nie udało się usunąć zdjęcia.");
    }

    setProfiles((current) =>
      current.map((profile) =>
        profile.id === profileId
          ? {
              ...profile,
              photos: profile.photos.filter(
                (photo) => photo.id !== photoId
              ),
            }
          : profile
      )
    );
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Wystąpił błąd podczas usuwania zdjęcia."
    );
  }
};

useEffect(() => {
  if (!activePhoto) return;

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      setActivePhoto(null);
    }

    if (event.key === "ArrowLeft") {
      setActivePhoto((current) => {
        if (!current || current.photos.length < 2) return current;

        return {
          ...current,
          index:
            (current.index - 1 + current.photos.length) %
            current.photos.length,
        };
      });
    }

    if (event.key === "ArrowRight") {
      setActivePhoto((current) => {
        if (!current || current.photos.length < 2) return current;

        return {
          ...current,
          index: (current.index + 1) % current.photos.length,
        };
      });
    }
  };

  window.addEventListener("keydown", handleKeyDown);

  return () => {
    window.removeEventListener("keydown", handleKeyDown);
  };
}, [activePhoto]);

  return (
    <div className="app">
      <Header
        onInfo={() => setShowInfo(true)}
      />

      <main className="profiles-page">
               <header className="profiles-header">
          <div>
            <span className="profiles-eyebrow">
              BIBLIOTEKA OSÓB
            </span>

            <h1>Profile</h1>

            <p>
              Twórz profile osób i dodawaj zdjęcia, które
              będą wykorzystywane do rozpoznawania osób
              na nagraniach.
            </p>
          </div>

          <button
            type="button"
            className="profiles-primary-button"
            onClick={() => {
              setShowCreateForm((current) => !current);
              setError("");
            }}
          >
            <span aria-hidden="true">＋</span>
            Dodaj profil
          </button>
        </header>

        {showCreateForm && (
          <section className="profiles-create-panel">
            <h2>Nowy profil</h2>

            <label htmlFor="new-profile-name">
              Nazwa osoby
            </label>

            <div className="profiles-create-row">
              <input
                id="new-profile-name"
                type="text"
                value={profileName}
                placeholder="Wpisz nazwę profilu"
                maxLength={100}
                onChange={(event) =>
                  setProfileName(event.target.value)
                }
                onKeyDown={(event) => {
                if (event.key === "Enter") {
                    void handleCreateProfile(profileName);
                }
                }}
              />

              <button
                type="button"
                className="profiles-primary-button"
                onClick={() => void handleCreateProfile(profileName)}
              >
                Utwórz profil
              </button>

              <button
                type="button"
                className="profiles-secondary-button"
                onClick={() => {
                  setShowCreateForm(false);
                  setProfileName("");
                  setError("");
                }}
              >
                Anuluj
              </button>
            </div>
          </section>
        )}

        {error && (
          <div className="profiles-error" role="alert">
            {error}
          </div>
        )}

        <section className="profiles-content">
          <div className="profiles-section-heading">
            <div>
              <h2>Twoje profile</h2>
              <p>
                {profiles.length === 1
                  ? "1 profil"
                  : `${profiles.length} profili`}
              </p>
            </div>
          </div>

          {profiles.length === 0 ? (
            <div className="profiles-empty">
              <div className="profiles-empty-icon">
                <span aria-hidden="true">♙</span>
              </div>

              <h3>Nie masz jeszcze żadnych profili</h3>

              <p>
                Dodaj profil osoby, a następnie przypisz do
                niego zdjęcia referencyjne.
              </p>

              <button
                type="button"
                className="profiles-primary-button"
                onClick={() => setShowCreateForm(true)}
              >
                Dodaj pierwszy profil
              </button>
            </div>
          ) : (
            <div className="profiles-grid">
              {profiles.map((profile) => (
                <article
                  className="profile-card"
                  key={profile.id}
                >
                  <div className="profile-card-header">
                    <div className="profile-avatar">
                      <span aria-hidden="true">♙</span>
                    </div>

                    <div className="profile-card-title">
                      <h3>{profile.name}</h3>
                      <span>
                        {profile.photos.length === 1
                          ? "1 zdjęcie"
                          : `${profile.photos.length} zdjęć`}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="profile-delete-button"
                      title="Usuń profil"
                      aria-label={`Usuń profil ${profile.name}`}
                      onClick={() => void handleDeleteProfile(profile.id)
                      }
                    >
                      Usuń
                    </button>
                  </div>

                 <div className="profile-photos">
                  {profile.photos.length === 0 ? (
                    <div className="profile-no-photos">
                      <span aria-hidden="true">▧</span>
                      <p>Brak zdjęć</p>
                      <small>Dodaj zdjęcia tej osoby</small>
                    </div>
                  ) : (
                    profile.photos.map((photo, index) => (
                      <div
                        className="profile-photo"
                        key={photo.id}
                      >
                        <div
                          className="profile-photo-preview"
                          role="button"
                          tabIndex={0}
                          onClick={() =>
                            setActivePhoto({
                              profileName: profile.name,
                              photos: profile.photos,
                              index,
                            })
                          }
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              setActivePhoto({
                                profileName: profile.name,
                                photos: profile.photos,
                                index,
                              });
                            }
                          }}
                          aria-label={`Otwórz zdjęcie ${index + 1} profilu ${profile.name}`}
                        >
                          <img
                            src={`http://localhost:8000/api/profiles/photos/${encodeURIComponent(photo.filename)}`}
                            alt={`Zdjęcie profilu ${profile.name}`}
                            loading="lazy"
                            onError={(event) => {
                              event.currentTarget.alt = "Nie udało się załadować zdjęcia";
                              event.currentTarget.classList.add("profile-photo-broken");
                            }}
                          />
                        </div>

                        <button
                          type="button"
                          className="profile-photo-remove"
                          title="Usuń zdjęcie"
                          aria-label="Usuń zdjęcie"
                          onClick={() =>
                            void handleDeletePhoto(profile.id, photo.id)
                          }
                        >
                          ×
                        </button>
                      </div>
                    ))
                  )}
                </div>

                  <label className="profile-add-photos">
                    <span aria-hidden="true">＋</span>
                    Dodaj zdjęcia

                 <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(event) => {
                        const files = event.target.files;

                        if (files && files.length > 0) {
                        void handleAddPhotos(profile.id, files);
                        }

                        event.target.value = "";
                    }}
                    />
                  </label>

                  <p className="profile-photo-hint">
                    Możesz zaznaczyć kilka zdjęć naraz.
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>


   {activePhoto && (
        <div
          className="profile-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={`Zdjęcia profilu ${activePhoto.profileName}`}
          onClick={() => setActivePhoto(null)}
        >
          <div
            className="profile-lightbox-content"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="profile-lightbox-close"
              aria-label="Zamknij podgląd zdjęcia"
              onClick={() => setActivePhoto(null)}
            >
              ×
            </button>

            <div className="profile-lightbox-heading">
              {activePhoto.profileName} · {activePhoto.index + 1} / {activePhoto.photos.length}
            </div>

            <img
              className="profile-lightbox-image"
              src={`http://localhost:8000/api/profiles/photos/${encodeURIComponent(activePhoto.photos[activePhoto.index].filename)}`}
              alt={`Zdjęcie ${activePhoto.index + 1} profilu ${activePhoto.profileName}`}
            />

            {activePhoto.photos.length > 1 && (
              <div className="profile-lightbox-navigation">
                <button
                  type="button"
                  aria-label="Poprzednie zdjęcie"
                  onClick={() =>
                    setActivePhoto((current) =>
                      current
                        ? {
                            ...current,
                            index: (current.index - 1 + current.photos.length) % current.photos.length,
                          }
                        : current
                    )
                  }
                >
                  ←
                </button>
                <button
                  type="button"
                  aria-label="Następne zdjęcie"
                  onClick={() =>
                    setActivePhoto((current) =>
                      current
                        ? {
                            ...current,
                            index: (current.index + 1) % current.photos.length,
                          }
                        : current
                    )
                  }
                >
                  →
                </button>
              </div>
            )}
          </div>
        </div>
      )}


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

export default ProfilePage;