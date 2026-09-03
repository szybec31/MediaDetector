import { useLanguage } from "../i18n";

interface ProjectSidebarProps {
  onBack: () => void;
  onDeleteProject: () => void;
  onDownloadAll: () => void;
}

function ProjectSidebar({
  onBack,
  onDeleteProject,
  onDownloadAll,
}: ProjectSidebarProps) {
  const { t } = useLanguage();

  return (
    <aside className="project-sidebar">
      <div className="project-sidebar-section">
        <h2>{t.projectDetails.project}</h2>

        <button
          className="project-sidebar-button"
          onClick={onBack}
        >
          <span>←</span>
          {t.projectDetails.back}
        </button>

        <button
          className="project-sidebar-button"
          onClick={onDownloadAll}
        >
          <span>↓</span>
          {t.projectDetails.downloadAll}
        </button>

        <button
          className="project-sidebar-button danger"
          onClick={onDeleteProject}
        >
          <span>×</span>
          {t.projectDetails.deleteProject}
        </button>
      </div>
    </aside>
  );
}

export default ProjectSidebar;