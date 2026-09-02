import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../i18n";
import "./ProfanityDictionaryPage.css";

interface ProfanityDictionary {
  pl: string[];
  en: string[];
}

type DictionaryLanguage = "pl" | "en";

function ProfanityDictionaryPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [dictionary, setDictionary] =
    useState<ProfanityDictionary>({
      pl: [],
      en: [],
    });

  const [newWord, setNewWord] = useState({
    pl: "",
    en: "",
  });

  const [editing, setEditing] = useState<{
    language: DictionaryLanguage;
    index: number;
    value: string;
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDictionary = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/profanity-dictionary"
        );

        if (!response.ok) {
          throw new Error(
            t.profanityDictionary.loadError
          );
        }

        const data: ProfanityDictionary =
          await response.json();

        setDictionary(data);
      } catch (error) {
        console.error(error);

        setError(
          error instanceof Error
            ? error.message
            : t.profanityDictionary.loadError
        );
      } finally {
        setLoading(false);
      }
    };

    loadDictionary();
  }, [t]);

  const addWord = (language: DictionaryLanguage) => {
    const word = newWord[language].trim();

    if (!word) {
      return;
    }

    const exists = dictionary[language].some(
      (existingWord) =>
        existingWord.toLowerCase() ===
        word.toLowerCase()
    );

    if (exists) {
      return;
    }

    setDictionary((current) => ({
      ...current,
      [language]: [
        ...current[language],
        word,
      ],
    }));

    setNewWord((current) => ({
      ...current,
      [language]: "",
    }));
  };

  const removeWord = (
    language: DictionaryLanguage,
    index: number
  ) => {
    setDictionary((current) => ({
      ...current,
      [language]: current[language].filter(
        (_, wordIndex) => wordIndex !== index
      ),
    }));
  };

  const startEditing = (
    language: DictionaryLanguage,
    index: number
  ) => {
    setEditing({
      language,
      index,
      value: dictionary[language][index],
    });
  };

  const cancelEditing = () => {
    setEditing(null);
  };

  const saveEditing = () => {
    if (!editing) {
      return;
    }

    const word = editing.value.trim();

    if (!word) {
      return;
    }

    setDictionary((current) => ({
      ...current,
      [editing.language]: current[
        editing.language
      ].map((existingWord, index) =>
        index === editing.index
          ? word
          : existingWord
      ),
    }));

    setEditing(null);
  };

  const saveDictionary = async () => {
    try {
      setSaving(true);
      setError("");

      const response = await fetch(
        "http://localhost:8000/api/profanity-dictionary",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(dictionary),
        }
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.detail ||
            t.profanityDictionary.saveError
        );
      }
    } catch (error) {
      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : t.profanityDictionary.saveError
      );
    } finally {
      setSaving(false);
    }
  };

  const renderDictionaryColumn = (
    language: DictionaryLanguage
  ) => {
    return (
      <section className="dictionary-column">
        <h2>
          {language === "pl"
            ? "Polski"
            : "English"}
        </h2>

        <div className="dictionary-list">
          {dictionary[language].map(
            (word, index) => {
              const isEditing =
                editing?.language === language &&
                editing.index === index;

              return (
                <div
                  className="dictionary-word"
                  key={`${language}-${index}`}
                >
                  {isEditing ? (
                    <>
                      <input
                        type="text"
                        value={editing.value}
                        onChange={(event) =>
                          setEditing({
                            ...editing,
                            value:
                              event.target.value,
                          })
                        }
                        autoFocus
                      />

                      <div className="dictionary-word-actions">
                        <button
                          type="button"
                          onClick={
                            saveEditing
                          }
                        >
                          {t.profanityDictionary.save}
                        </button>

                        <button
                          type="button"
                          onClick={
                            cancelEditing
                          }
                        >
                          {
                            t.profanityDictionary
                              .cancel
                          }
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <span>{word}</span>

                      <div className="dictionary-word-actions">
                        <button
                          type="button"
                          onClick={() =>
                            startEditing(
                              language,
                              index
                            )
                          }
                        >
                          {
                            t.profanityDictionary
                              .edit
                          }
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            removeWord(
                              language,
                              index
                            )
                          }
                        >
                          {
                            t.profanityDictionary
                              .delete
                          }
                        </button>
                      </div>
                    </>
                  )}
                </div>
              );
            }
          )}
        </div>

        <div className="dictionary-add">
          <input
            type="text"
            value={newWord[language]}
            onChange={(event) =>
              setNewWord((current) => ({
                ...current,
                [language]:
                  event.target.value,
              }))
            }
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                addWord(language);
              }
            }}
            placeholder={
              t.profanityDictionary.placeholder
            }
          />

          <button
            type="button"
            onClick={() =>
              addWord(language)
            }
          >
            {t.profanityDictionary.add}
          </button>
        </div>
      </section>
    );
  };

  if (loading) {
    return (
      <div className="dictionary-page">
        <div className="dictionary-container">
          <p>
            {t.profanityDictionary.loading}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="dictionary-page">
      <div className="dictionary-container">
        <div className="dictionary-header">
          <div>
            <h1>
              {t.profanityDictionary.title}
            </h1>

            <p>
              {
                t.profanityDictionary
                  .description
              }
            </p>
          </div>

          <button
            type="button"
            className="dictionary-back-button"
            onClick={() => navigate("/")}
          >
            {t.profanityDictionary.back}
          </button>
        </div>

        <div className="dictionary-columns">
          {renderDictionaryColumn("pl")}
          {renderDictionaryColumn("en")}
        </div>

        {error && (
          <div className="dictionary-error">
            {error}
          </div>
        )}

        <div className="dictionary-footer">
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/")}
            disabled={saving}
          >
            {t.profanityDictionary.cancel}
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={saveDictionary}
            disabled={saving}
          >
            {saving
              ? t.profanityDictionary.saving
              : t.profanityDictionary
                  .saveDictionary}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfanityDictionaryPage;