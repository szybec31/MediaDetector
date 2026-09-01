import { useLanguage } from "../i18n";

interface SidebarProps {
  onNewProject: () => void;
  onNewPerson: () => void;
  onProfanityDictionary: () => void;
}

function Sidebar({
  onNewProject,
  onNewPerson,
  onProfanityDictionary,
}: SidebarProps) {
  const { t } = useLanguage();

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h2>{t.sidebar.actions}</h2>

        <button
          className="action-button"
          onClick={onNewProject}
        >
          <span>+</span>
          {t.sidebar.newProject}
        </button>

        <button
          className="action-button"
          onClick={onNewPerson}
        >
          <span>+</span>
          {t.sidebar.newPerson}
        </button>

        <button
          className="action-button"
          onClick={onProfanityDictionary}
        >
          <span>+</span>
          {t.sidebar.profanityDictionary}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;